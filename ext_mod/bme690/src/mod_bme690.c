// MicroPython C module for the Bosch BME690 gas/environmental sensor (I2C),
// driven through the closed-source BSEC 3.x algorithm library (libalgobsec.a)
// and the open-source bme69x sensor driver.
//
// The BSEC processing loop from Bosch's reference bsec_integration.c is
// reimplemented here as a single-step run() so control returns to Python after
// each processing cycle. State (IAQ calibration) is persisted to NVS.
//
// Python usage:
//   import bme690, time
//   s = bme690.BME690(scl=4, sda=3, addr=0x76, port=1, save_state=True)
//   s.init()
//   while True:
//       out = s.run()                 # dict when a new result is ready, else None
//       if out:
//           print(out["iaq"], out["iaq_accuracy"], out["co2_equivalent"],
//                 out["temperature"], out["humidity"])
//       time.sleep_ms(s.next_call_ms())

#include "py/obj.h"
#include "py/runtime.h"

#include "esp_timer.h"
#include "nvs_flash.h"
#include "nvs.h"

#include "bme69x.h"
#include "bsec_interface.h"
#include "bsec_datatypes.h"
#include "bme690_i2c_bridge.h"
#include "bme690_config.h"   // extern const uint8_t bsec_config_iaq[]

#include <string.h>

/* --- constants mirrored from Bosch bsec_integration.h ------------------- */
#define BME690_TOTAL_HEAT_DUR       UINT16_C(140)
#define BME690_TEMP_OFFSET_LP       (0.1495f)
#define BME690_TEMP_OFFSET_ULP      (0.466f)
#define BME690_NUM_OUTPUTS_MAX      UINT8_C(14)
#define BME690_NVS_NAMESPACE        "bme690"
#define BME690_NVS_KEY_STATE        "bsec_state"
#define BME690_SAVE_INTERVAL        100    // save state every N samples

#define BSEC_CHECK_INPUT(x, shift)  ((x) & (1 << ((shift) - 1)))

/* ----------------------------------------------------------------------- */

typedef struct _mp_bme690_obj_t {
    mp_obj_base_t base;

    // configuration
    int port, sda, scl, freq;
    uint8_t addr;
    float sample_rate;
    bool nvs_enabled;

    // hardware / driver state
    bme690_i2c_t i2c;
    struct bme69x_dev dev;
    struct bme69x_conf conf;
    struct bme69x_heatr_conf heatr;

    // BSEC instance (allocated to bsec_get_instance_size())
    uint8_t *bsec_inst;

    // pipeline state
    bsec_bme_settings_t settings;
    uint8_t last_op_mode;
    uint8_t op_mode;
    float temp_offset;
    uint8_t baseline_tracker;

    // parallel-mode field buffer
    struct bme69x_data data_fields[3];
    uint8_t n_fields, i_field;

    // state persistence
    uint32_t n_samples;

    bool initialized;
} mp_bme690_obj_t;

extern const mp_obj_type_t mp_bme690_type;

/* ----------------------------------------------------------------------- */
/* Helpers                                                                  */
/* ----------------------------------------------------------------------- */

static int64_t bme690_now_ns(void)
{
    return (int64_t)esp_timer_get_time() * INT64_C(1000);
}

static void bme690_raise(const char *what, int status)
{
    mp_raise_msg_varg(&mp_type_OSError, MP_ERROR_TEXT("%s failed (status %d)"), what, status);
}

// NVS: load previously saved BSEC state. Returns number of bytes loaded (0 if none).
static uint32_t bme690_state_load(uint8_t *buf, uint32_t buf_len)
{
    nvs_handle_t h;
    if (nvs_open(BME690_NVS_NAMESPACE, NVS_READONLY, &h) != ESP_OK) {
        return 0;
    }
    size_t len = buf_len;
    esp_err_t err = nvs_get_blob(h, BME690_NVS_KEY_STATE, buf, &len);
    nvs_close(h);
    return (err == ESP_OK) ? (uint32_t)len : 0;
}

static void bme690_state_save(const uint8_t *buf, uint32_t len)
{
    nvs_handle_t h;
    if (nvs_open(BME690_NVS_NAMESPACE, NVS_READWRITE, &h) != ESP_OK) {
        return;
    }
    if (nvs_set_blob(h, BME690_NVS_KEY_STATE, buf, len) == ESP_OK) {
        nvs_commit(h);
    }
    nvs_close(h);
}

/* --- BSEC subscription (IAQ output set) --------------------------------- */

static bsec_library_return_t bme690_update_subscription(mp_bme690_obj_t *self)
{
    bsec_sensor_configuration_t virt[BME690_NUM_OUTPUTS_MAX];
    bsec_sensor_configuration_t required[BSEC_MAX_PHYSICAL_SENSOR];
    uint8_t n_required = BSEC_MAX_PHYSICAL_SENSOR;
    float sr = self->sample_rate;
    uint8_t n = 0;

    virt[n].sensor_id = BSEC_OUTPUT_RAW_PRESSURE;    virt[n++].sample_rate = sr;
    virt[n].sensor_id = BSEC_OUTPUT_RAW_TEMPERATURE; virt[n++].sample_rate = sr;
    virt[n].sensor_id = BSEC_OUTPUT_RAW_HUMIDITY;    virt[n++].sample_rate = sr;
    virt[n].sensor_id = BSEC_OUTPUT_RAW_GAS;         virt[n++].sample_rate = sr;
    virt[n].sensor_id = BSEC_OUTPUT_IAQ;             virt[n++].sample_rate = sr;
    virt[n].sensor_id = BSEC_OUTPUT_SENSOR_HEAT_COMPENSATED_TEMPERATURE; virt[n++].sample_rate = sr;
    virt[n].sensor_id = BSEC_OUTPUT_SENSOR_HEAT_COMPENSATED_HUMIDITY;    virt[n++].sample_rate = sr;
    virt[n].sensor_id = BSEC_OUTPUT_STATIC_IAQ;      virt[n++].sample_rate = sr;
    virt[n].sensor_id = BSEC_OUTPUT_CO2_EQUIVALENT;  virt[n++].sample_rate = sr;
    virt[n].sensor_id = BSEC_OUTPUT_BREATH_VOC_EQUIVALENT; virt[n++].sample_rate = sr;
    virt[n].sensor_id = BSEC_OUTPUT_STABILIZATION_STATUS;  virt[n++].sample_rate = sr;
    virt[n].sensor_id = BSEC_OUTPUT_RUN_IN_STATUS;   virt[n++].sample_rate = sr;
    virt[n].sensor_id = BSEC_OUTPUT_GAS_PERCENTAGE;  virt[n++].sample_rate = sr;

    if (self->sample_rate == BSEC_SAMPLE_RATE_LP) {
        virt[n].sensor_id = BSEC_OUTPUT_TVOC_EQUIVALENT; virt[n++].sample_rate = sr;
    }

    return bsec_update_subscription(self->bsec_inst, virt, n, required, &n_required);
}

/* --- bme69x mode configuration (from bsec_integration.c) ---------------- */

static uint32_t bme690_meas_dur(mp_bme690_obj_t *self, uint8_t mode)
{
    if (mode == BME69X_SLEEP_MODE) {
        mode = self->last_op_mode;
    }
    return bme69x_get_meas_dur(mode, &self->conf, &self->dev);
}

static void bme690_set_forced(mp_bme690_obj_t *self, bsec_bme_settings_t *s)
{
    if (bme69x_set_op_mode(BME69X_SLEEP_MODE, &self->dev) != BME69X_OK) return;
    if (bme69x_get_conf(&self->conf, &self->dev) != BME69X_OK) return;

    self->conf.os_hum = s->humidity_oversampling;
    self->conf.os_temp = s->temperature_oversampling;
    self->conf.os_pres = s->pressure_oversampling;
    if (bme69x_set_conf(&self->conf, &self->dev) != BME69X_OK) return;

    self->heatr.enable = BME69X_ENABLE;
    self->heatr.heatr_temp = s->heater_temperature;
    self->heatr.heatr_dur = s->heater_duration;
    if (bme69x_set_heatr_conf(BME69X_FORCED_MODE, &self->heatr, &self->dev) != BME69X_OK) return;

    if (bme69x_set_op_mode(BME69X_FORCED_MODE, &self->dev) != BME69X_OK) return;

    self->last_op_mode = BME69X_FORCED_MODE;
    self->op_mode = BME69X_FORCED_MODE;
}

static void bme690_set_parallel(mp_bme690_obj_t *self, bsec_bme_settings_t *s)
{
    uint16_t shared;
    if (bme69x_get_conf(&self->conf, &self->dev) != BME69X_OK) return;

    self->conf.os_hum = s->humidity_oversampling;
    self->conf.os_temp = s->temperature_oversampling;
    self->conf.os_pres = s->pressure_oversampling;
    if (bme69x_set_conf(&self->conf, &self->dev) != BME69X_OK) return;

    shared = BME690_TOTAL_HEAT_DUR - (bme690_meas_dur(self, BME69X_PARALLEL_MODE) / INT64_C(1000));
    self->heatr.enable = BME69X_ENABLE;
    self->heatr.heatr_temp_prof = s->heater_temperature_profile;
    self->heatr.heatr_dur_prof = s->heater_duration_profile;
    self->heatr.shared_heatr_dur = shared;
    self->heatr.profile_len = s->heater_profile_len;
    if (bme69x_set_heatr_conf(BME69X_PARALLEL_MODE, &self->heatr, &self->dev) != BME69X_OK) return;

    if (bme69x_set_op_mode(BME69X_PARALLEL_MODE, &self->dev) != BME69X_OK) return;

    self->last_op_mode = BME69X_PARALLEL_MODE;
    self->op_mode = BME69X_PARALLEL_MODE;
}

// Pull one data field out of the field buffer (mirrors bsec_integration get_data).
static uint8_t bme690_take_field(mp_bme690_obj_t *self, struct bme69x_data *data)
{
    if (self->last_op_mode == BME69X_FORCED_MODE) {
        *data = self->data_fields[0];
        return 0;
    }
    if (self->n_fields) {
        *data = self->data_fields[self->i_field];
        self->i_field++;
        if (self->i_field >= self->n_fields) {
            self->i_field = self->n_fields - 1;
            return 0;
        }
        return self->n_fields - self->i_field;
    }
    return 0;
}

// Feed one BME690 measurement into BSEC and, if outputs are produced, fill dict.
// Returns mp_const_none if no outputs, or a newly created dict.
static mp_obj_t bme690_process(mp_bme690_obj_t *self, int64_t ts_ns,
                               struct bme69x_data *data, uint32_t process_data)
{
    bsec_input_t inputs[BSEC_MAX_PHYSICAL_SENSOR];
    uint8_t n_inputs = 0;

    if (BSEC_CHECK_INPUT(process_data, BSEC_INPUT_HEATSOURCE)) {
        inputs[n_inputs].sensor_id = BSEC_INPUT_HEATSOURCE;
        inputs[n_inputs].signal = self->temp_offset;
        inputs[n_inputs].time_stamp = ts_ns;
        n_inputs++;
    }
    if (BSEC_CHECK_INPUT(process_data, BSEC_INPUT_TEMPERATURE)) {
        inputs[n_inputs].sensor_id = BSEC_INPUT_TEMPERATURE;
        inputs[n_inputs].signal = data->temperature / 100.0f;   // integer driver: x100
        inputs[n_inputs].time_stamp = ts_ns;
        n_inputs++;
    }
    if (BSEC_CHECK_INPUT(process_data, BSEC_INPUT_HUMIDITY)) {
        inputs[n_inputs].sensor_id = BSEC_INPUT_HUMIDITY;
        inputs[n_inputs].signal = data->humidity / 1000.0f;     // integer driver: x1000
        inputs[n_inputs].time_stamp = ts_ns;
        n_inputs++;
    }
    if (BSEC_CHECK_INPUT(process_data, BSEC_INPUT_PRESSURE)) {
        inputs[n_inputs].sensor_id = BSEC_INPUT_PRESSURE;
        inputs[n_inputs].signal = data->pressure;
        inputs[n_inputs].time_stamp = ts_ns;
        n_inputs++;
    }
    if (BSEC_CHECK_INPUT(process_data, BSEC_INPUT_GASRESISTOR) &&
        (data->status & BME69X_GASM_VALID_MSK)) {
        inputs[n_inputs].sensor_id = BSEC_INPUT_GASRESISTOR;
        inputs[n_inputs].signal = data->gas_resistance;
        inputs[n_inputs].time_stamp = ts_ns;
        n_inputs++;
    }
    if (BSEC_CHECK_INPUT(process_data, BSEC_INPUT_PROFILE_PART) &&
        (data->status & BME69X_GASM_VALID_MSK)) {
        inputs[n_inputs].sensor_id = BSEC_INPUT_PROFILE_PART;
        inputs[n_inputs].signal = (self->op_mode == BME69X_FORCED_MODE) ? 0 : data->gas_index;
        inputs[n_inputs].time_stamp = ts_ns;
        n_inputs++;
    }
    if (self->sample_rate == BSEC_SAMPLE_RATE_LP) {
        inputs[n_inputs].sensor_id = BSEC_INPUT_DISABLE_BASELINE_TRACKER;
        inputs[n_inputs].signal = self->baseline_tracker;
        inputs[n_inputs].time_stamp = ts_ns;
        n_inputs++;
    }

    if (n_inputs == 0) {
        return mp_const_none;
    }

    bsec_output_t outputs[BSEC_NUMBER_OUTPUTS];
    uint8_t n_outputs = BSEC_NUMBER_OUTPUTS;
    bsec_library_return_t st = bsec_do_steps(self->bsec_inst, inputs, n_inputs, outputs, &n_outputs);
    if (st != BSEC_OK || n_outputs == 0) {
        return mp_const_none;
    }

    mp_obj_t dict = mp_obj_new_dict(16);
    #define STORE_F(key, val) \
        mp_obj_dict_store(dict, MP_ROM_QSTR(MP_QSTR_##key), mp_obj_new_float((mp_float_t)(val)))
    #define STORE_I(key, val) \
        mp_obj_dict_store(dict, MP_ROM_QSTR(MP_QSTR_##key), mp_obj_new_int(val))

    for (uint8_t i = 0; i < n_outputs; i++) {
        switch (outputs[i].sensor_id) {
            case BSEC_OUTPUT_IAQ:
                STORE_F(iaq, outputs[i].signal);
                STORE_I(iaq_accuracy, outputs[i].accuracy);
                break;
            case BSEC_OUTPUT_STATIC_IAQ:
                STORE_F(static_iaq, outputs[i].signal);
                break;
            case BSEC_OUTPUT_CO2_EQUIVALENT:
                STORE_F(co2_equivalent, outputs[i].signal);
                break;
            case BSEC_OUTPUT_BREATH_VOC_EQUIVALENT:
                STORE_F(breath_voc_equivalent, outputs[i].signal);
                break;
            case BSEC_OUTPUT_RAW_TEMPERATURE:
                STORE_F(raw_temperature, outputs[i].signal);
                break;
            case BSEC_OUTPUT_RAW_HUMIDITY:
                STORE_F(raw_humidity, outputs[i].signal);
                break;
            case BSEC_OUTPUT_RAW_PRESSURE:
                STORE_F(pressure, outputs[i].signal);
                break;
            case BSEC_OUTPUT_RAW_GAS:
                STORE_F(gas_resistance, outputs[i].signal);
                break;
            case BSEC_OUTPUT_SENSOR_HEAT_COMPENSATED_TEMPERATURE:
                STORE_F(temperature, outputs[i].signal);
                break;
            case BSEC_OUTPUT_SENSOR_HEAT_COMPENSATED_HUMIDITY:
                STORE_F(humidity, outputs[i].signal);
                break;
            case BSEC_OUTPUT_STABILIZATION_STATUS:
                STORE_F(stabilization_status, outputs[i].signal);
                break;
            case BSEC_OUTPUT_RUN_IN_STATUS:
                STORE_F(run_in_status, outputs[i].signal);
                break;
            case BSEC_OUTPUT_GAS_PERCENTAGE:
                STORE_F(gas_percentage, outputs[i].signal);
                break;
            case BSEC_OUTPUT_TVOC_EQUIVALENT:
                STORE_F(tvoc_equivalent, outputs[i].signal);
                break;
            default:
                break;
        }
    }
    #undef STORE_F
    #undef STORE_I
    return dict;
}

/* ----------------------------------------------------------------------- */
/* Constructor                                                              */
/* ----------------------------------------------------------------------- */

static mp_obj_t bme690_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw,
                                const mp_obj_t *all_args)
{
    enum { ARG_scl, ARG_sda, ARG_addr, ARG_port, ARG_freq, ARG_mode, ARG_save_state };
    const mp_arg_t allowed_args[] = {
        { MP_QSTR_scl,        MP_ARG_INT | MP_ARG_KW_ONLY | MP_ARG_REQUIRED },
        { MP_QSTR_sda,        MP_ARG_INT | MP_ARG_KW_ONLY | MP_ARG_REQUIRED },
        { MP_QSTR_addr,       MP_ARG_INT | MP_ARG_KW_ONLY, { .u_int = 0x76 } },
        { MP_QSTR_port,       MP_ARG_INT | MP_ARG_KW_ONLY, { .u_int = 1 } },
        { MP_QSTR_freq,       MP_ARG_INT | MP_ARG_KW_ONLY, { .u_int = 400000 } },
        { MP_QSTR_mode,       MP_ARG_OBJ | MP_ARG_KW_ONLY, { .u_obj = mp_const_none } },
        { MP_QSTR_save_state, MP_ARG_BOOL | MP_ARG_KW_ONLY, { .u_bool = true } },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all_kw_array(n_args, n_kw, all_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    // Map the mode string to a BSEC sample rate. Default: low power (3s).
    float sr = BSEC_SAMPLE_RATE_LP;
    if (args[ARG_mode].u_obj != mp_const_none) {
        const char *mode = mp_obj_str_get_str(args[ARG_mode].u_obj);
        if (strcmp(mode, "lp") == 0) {
            sr = BSEC_SAMPLE_RATE_LP;
        } else if (strcmp(mode, "ulp") == 0) {
            sr = BSEC_SAMPLE_RATE_ULP;
        } else if (strcmp(mode, "cont") == 0) {
            sr = BSEC_SAMPLE_RATE_CONT;
        } else {
            mp_raise_msg(&mp_type_ValueError, MP_ERROR_TEXT("mode must be 'lp', 'ulp' or 'cont'"));
        }
    }

    mp_bme690_obj_t *self = m_new_obj(mp_bme690_obj_t);
    memset(self, 0, sizeof(*self));
    self->base.type = &mp_bme690_type;
    self->scl = args[ARG_scl].u_int;
    self->sda = args[ARG_sda].u_int;
    self->addr = (uint8_t)args[ARG_addr].u_int;
    self->port = args[ARG_port].u_int;
    self->freq = args[ARG_freq].u_int;
    self->sample_rate = sr;
    self->nvs_enabled = args[ARG_save_state].u_bool;
    self->last_op_mode = BME69X_SLEEP_MODE;
    self->op_mode = BME69X_SLEEP_MODE;
    self->settings.next_call = 0;
    self->initialized = false;

    return MP_OBJ_FROM_PTR(self);
}

/* ----------------------------------------------------------------------- */
/* init(): bring up I2C, bme69x, and BSEC                                   */
/* ----------------------------------------------------------------------- */

static mp_obj_t bme690_init(mp_obj_t self_in)
{
    mp_bme690_obj_t *self = MP_OBJ_TO_PTR(self_in);
    if (self->initialized) {
        return mp_const_none;
    }

    // NVS flash (idempotent - MicroPython usually already initialised it).
    if (self->nvs_enabled) {
        esp_err_t nerr = nvs_flash_init();
        if (nerr == ESP_ERR_NVS_NO_FREE_PAGES || nerr == ESP_ERR_NVS_NEW_VERSION_FOUND) {
            nvs_flash_erase();
            nvs_flash_init();
        }
    }

    // I2C bus + device.
    esp_err_t err = bme690_i2c_init(&self->i2c, self->port, self->sda, self->scl,
                                    self->freq, self->addr);
    if (err != ESP_OK) {
        mp_raise_msg_varg(&mp_type_OSError, MP_ERROR_TEXT("i2c init failed %d"), (int)err);
    }

    // bme69x device struct.
    self->dev.intf = BME69X_I2C_INTF;
    self->dev.read = bme690_i2c_read;
    self->dev.write = bme690_i2c_write;
    self->dev.delay_us = bme690_delay_us;
    self->dev.intf_ptr = &self->i2c;
    self->dev.amb_temp = 25;

    int8_t bst = bme69x_init(&self->dev);
    if (bst != BME69X_OK) {
        bme690_i2c_deinit(&self->i2c);
        bme690_raise("bme69x_init", bst);
    }

    // BSEC instance.
    size_t inst_size = bsec_get_instance_size();
    self->bsec_inst = (uint8_t *)malloc(inst_size);
    if (self->bsec_inst == NULL) {
        bme690_i2c_deinit(&self->i2c);
        mp_raise_msg(&mp_type_MemoryError, MP_ERROR_TEXT("bsec instance alloc failed"));
    }

    bsec_library_return_t st = bsec_init(self->bsec_inst);
    if (st != BSEC_OK) {
        free(self->bsec_inst); self->bsec_inst = NULL;
        bme690_i2c_deinit(&self->i2c);
        bme690_raise("bsec_init", st);
    }

    // Apply the built-in configuration blob (33v / 3s LP / 4-day).
    uint8_t work_buffer[BSEC_MAX_WORKBUFFER_SIZE];
    st = bsec_set_configuration(self->bsec_inst, bsec_config_iaq, sizeof(bsec_config_iaq),
                                work_buffer, sizeof(work_buffer));
    if (st != BSEC_OK) {
        free(self->bsec_inst); self->bsec_inst = NULL;
        bme690_i2c_deinit(&self->i2c);
        bme690_raise("bsec_set_configuration", st);
    }

    // Restore calibration state from NVS if available.
    if (self->nvs_enabled) {
        uint8_t state[BSEC_MAX_STATE_BLOB_SIZE];
        uint32_t state_len = bme690_state_load(state, sizeof(state));
        if (state_len != 0) {
            bsec_set_state(self->bsec_inst, state, state_len, work_buffer, sizeof(work_buffer));
        }
    }

    // Temperature offset heuristic (per Bosch reference).
    self->temp_offset = (self->sample_rate == BSEC_SAMPLE_RATE_LP)  ? BME690_TEMP_OFFSET_LP :
                        (self->sample_rate == BSEC_SAMPLE_RATE_ULP) ? BME690_TEMP_OFFSET_ULP : 0.0f;
    self->baseline_tracker = 0;

    st = bme690_update_subscription(self);
    if (st != BSEC_OK) {
        free(self->bsec_inst); self->bsec_inst = NULL;
        bme690_i2c_deinit(&self->i2c);
        bme690_raise("bsec_update_subscription", st);
    }

    memset(&self->settings, 0, sizeof(self->settings));
    self->settings.next_call = 0;
    self->n_samples = 0;
    self->initialized = true;
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(bme690_init_obj, bme690_init);

/* ----------------------------------------------------------------------- */
/* run(): one BSEC processing step. Mirrors the bsec_integration.c loop body.*/
/* ----------------------------------------------------------------------- */

static mp_obj_t bme690_run(mp_obj_t self_in)
{
    mp_bme690_obj_t *self = MP_OBJ_TO_PTR(self_in);
    if (!self->initialized) {
        mp_raise_msg(&mp_type_OSError, MP_ERROR_TEXT("sensor not initialised"));
    }

    int64_t ts_ns = bme690_now_ns();
    if (ts_ns < self->settings.next_call) {
        return mp_const_none;  // not time for the next cycle yet
    }

    self->op_mode = self->settings.op_mode;

    bsec_library_return_t status = bsec_sensor_control(self->bsec_inst, ts_ns, &self->settings);
    if (status < BSEC_OK) {
        bme690_raise("bsec_sensor_control", status);
    }

    switch (self->settings.op_mode) {
        case BME69X_FORCED_MODE:
            bme690_set_forced(self, &self->settings);
            break;
        case BME69X_PARALLEL_MODE:
            if (self->op_mode != self->settings.op_mode) {
                bme690_set_parallel(self, &self->settings);
            }
            break;
        case BME69X_SLEEP_MODE:
            if (self->op_mode != self->settings.op_mode) {
                bme69x_set_op_mode(BME69X_SLEEP_MODE, &self->dev);
            }
            break;
        default:
            break;
    }

    mp_obj_t result = mp_const_none;

    if (self->settings.trigger_measurement && self->settings.op_mode != BME69X_SLEEP_MODE) {
        self->n_fields = 0;
        bme69x_get_data(self->last_op_mode, &self->data_fields[0], &self->n_fields, &self->dev);
        self->i_field = 0;

        if (self->n_fields) {
            uint8_t left;
            do {
                struct bme69x_data data = {0};
                left = bme690_take_field(self, &data);
                if (data.status & BME69X_GASM_VALID_MSK) {
                    mp_obj_t out = bme690_process(self, ts_ns, &data, self->settings.process_data);
                    if (out != mp_const_none) {
                        result = out;   // keep the most recent produced output
                    }
                }
            } while (left);
        }
    }

    // Periodic state persistence.
    if (self->nvs_enabled) {
        self->n_samples++;
        if (self->n_samples >= BME690_SAVE_INTERVAL) {
            uint8_t state[BSEC_MAX_STATE_BLOB_SIZE];
            uint8_t work_buffer[BSEC_MAX_WORKBUFFER_SIZE];
            uint32_t state_len = 0;
            if (bsec_get_state(self->bsec_inst, 0, state, sizeof(state),
                               work_buffer, sizeof(work_buffer), &state_len) == BSEC_OK) {
                bme690_state_save(state, state_len);
            }
            self->n_samples = 0;
        }
    }

    return result;
}
static MP_DEFINE_CONST_FUN_OBJ_1(bme690_run_obj, bme690_run);

/* ----------------------------------------------------------------------- */
/* next_call_ms(): milliseconds until the next run() should be invoked.      */
/* ----------------------------------------------------------------------- */

static mp_obj_t bme690_next_call_ms(mp_obj_t self_in)
{
    mp_bme690_obj_t *self = MP_OBJ_TO_PTR(self_in);
    int64_t now = bme690_now_ns();
    int64_t delta = self->settings.next_call - now;
    if (delta < 0) {
        delta = 0;
    }
    return mp_obj_new_int((mp_int_t)(delta / INT64_C(1000000)));
}
static MP_DEFINE_CONST_FUN_OBJ_1(bme690_next_call_ms_obj, bme690_next_call_ms);

/* ----------------------------------------------------------------------- */
/* save_state(): force a BSEC state save to NVS.                             */
/* ----------------------------------------------------------------------- */

static mp_obj_t bme690_save_state(mp_obj_t self_in)
{
    mp_bme690_obj_t *self = MP_OBJ_TO_PTR(self_in);
    if (!self->initialized) {
        mp_raise_msg(&mp_type_OSError, MP_ERROR_TEXT("sensor not initialised"));
    }
    uint8_t state[BSEC_MAX_STATE_BLOB_SIZE];
    uint8_t work_buffer[BSEC_MAX_WORKBUFFER_SIZE];
    uint32_t state_len = 0;
    bsec_library_return_t st = bsec_get_state(self->bsec_inst, 0, state, sizeof(state),
                                              work_buffer, sizeof(work_buffer), &state_len);
    if (st != BSEC_OK) {
        bme690_raise("bsec_get_state", st);
    }
    bme690_state_save(state, state_len);
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(bme690_save_state_obj, bme690_save_state);

/* ----------------------------------------------------------------------- */
/* deinit() / __del__                                                        */
/* ----------------------------------------------------------------------- */

static mp_obj_t bme690_deinit(mp_obj_t self_in)
{
    mp_bme690_obj_t *self = MP_OBJ_TO_PTR(self_in);
    if (self->initialized) {
        bme69x_set_op_mode(BME69X_SLEEP_MODE, &self->dev);
    }
    if (self->bsec_inst != NULL) {
        free(self->bsec_inst);
        self->bsec_inst = NULL;
    }
    bme690_i2c_deinit(&self->i2c);
    self->initialized = false;
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(bme690_deinit_obj, bme690_deinit);

/* ----------------------------------------------------------------------- */
/* Type / module                                                            */
/* ----------------------------------------------------------------------- */

static const mp_rom_map_elem_t bme690_locals_dict_table[] = {
    { MP_ROM_QSTR(MP_QSTR_init),         MP_ROM_PTR(&bme690_init_obj) },
    { MP_ROM_QSTR(MP_QSTR_run),          MP_ROM_PTR(&bme690_run_obj) },
    { MP_ROM_QSTR(MP_QSTR_next_call_ms), MP_ROM_PTR(&bme690_next_call_ms_obj) },
    { MP_ROM_QSTR(MP_QSTR_save_state),   MP_ROM_PTR(&bme690_save_state_obj) },
    { MP_ROM_QSTR(MP_QSTR_deinit),       MP_ROM_PTR(&bme690_deinit_obj) },
    { MP_ROM_QSTR(MP_QSTR___del__),      MP_ROM_PTR(&bme690_deinit_obj) },
};
static MP_DEFINE_CONST_DICT(bme690_locals_dict, bme690_locals_dict_table);

MP_DEFINE_CONST_OBJ_TYPE(
    mp_bme690_type,
    MP_QSTR_BME690,
    MP_TYPE_FLAG_NONE,
    make_new, bme690_make_new,
    locals_dict, (mp_obj_dict_t *)&bme690_locals_dict
);

static const mp_rom_map_elem_t bme690_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_OBJ_NEW_QSTR(MP_QSTR_bme690) },
    { MP_ROM_QSTR(MP_QSTR_BME690),   MP_ROM_PTR(&mp_bme690_type) },
    // sample-rate constants (floats) are exposed as helper functions below
};
static MP_DEFINE_CONST_DICT(bme690_globals, bme690_globals_table);

const mp_obj_module_t module_bme690 = {
    .base    = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&bme690_globals,
};

MP_REGISTER_MODULE(MP_QSTR_bme690, module_bme690);
