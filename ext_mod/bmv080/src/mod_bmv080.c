// MicroPython C module for the Bosch BMV080 particulate matter sensor (SPI, polling).
//
// Wraps the closed-source BMV080 vendor library (lib_bmv080.a + lib_postProcessor.a)
// and provides a small SPI com-bridge built directly on the ESP-IDF spi_master driver.
//
// Python usage:
//   import bmv080
//   s = bmv080.BMV080(sck=36, mosi=35, miso=37, cs=9, host=2, freq=1_000_000)
//   s.open()
//   s.configure(mode=bmv080.CONTINUOUS)       # optional parameters
//   s.start()
//   while True:
//       d = s.read()                          # dict or None if no new sample yet
//       if d:
//           print(d["pm2_5"], d["pm1"], d["pm10"])
//   s.stop(); s.close()

#include "py/obj.h"
#include "py/runtime.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "driver/spi_master.h"

#include "bmv080.h"
#include "bmv080_defs.h"

#include <string.h>

/* ----------------------------------------------------------------------- */
/* Object                                                                   */
/* ----------------------------------------------------------------------- */

typedef struct _mp_bmv080_obj_t {
    mp_obj_base_t base;
    // SPI configuration (from constructor)
    int sck;
    int mosi;
    int miso;
    int cs;
    int host;               // SPI host id (SPI2_HOST=1, SPI3_HOST=2)
    int freq;
    // runtime state
    spi_device_handle_t spi;
    bmv080_handle_t handle;
    bool bus_initialized;
    bool measuring;
} mp_bmv080_obj_t;

// Scratch used to shuttle one sample out of the data_ready callback.
typedef struct _bmv080_capture_t {
    bool got;
    bmv080_output_t out;
} bmv080_capture_t;

extern const mp_obj_type_t mp_bmv080_type;

/* ----------------------------------------------------------------------- */
/* SPI com-bridge (ported from the Bosch xtensa_esp32 example combridge.c)  */
/* The vendor lib transfers a 16-bit header (as SPI address phase) followed */
/* by a payload of 16-bit words, MSB first. The ESP32 is little-endian so   */
/* every payload word is byte-swapped.                                      */
/* ----------------------------------------------------------------------- */

static int8_t combridge_spi_read_16bit(bmv080_sercom_handle_t handle, uint16_t header,
                                       uint16_t *payload, uint16_t payload_length)
{
    spi_transaction_ext_t t = (spi_transaction_ext_t){
        .base = {
            .flags = (SPI_TRANS_VARIABLE_ADDR | SPI_TRANS_VARIABLE_CMD),
            .addr = header,
            .length = payload_length * 2 * 8,
            .rxlength = payload_length * 2 * 8,
            .tx_buffer = NULL,
            .rx_buffer = (void *)payload,
        },
        .command_bits = 0,
        .address_bits = 16,
        .dummy_bits = 0,
    };

    esp_err_t err = spi_device_polling_transmit((spi_device_handle_t)handle, (spi_transaction_t *)&t);

    for (int i = 0; i < payload_length; i++) {
        payload[i] = ((payload[i] << 8) | (payload[i] >> 8)) & 0xffff;
    }
    return (int8_t)err;
}

static int8_t combridge_spi_write_16bit(bmv080_sercom_handle_t handle, uint16_t header,
                                        const uint16_t *payload, uint16_t payload_length)
{
    uint16_t *swapped = (uint16_t *)calloc(payload_length, sizeof(uint16_t));
    if (swapped == NULL) {
        return (int8_t)ESP_ERR_NO_MEM;
    }
    for (int i = 0; i < payload_length; i++) {
        swapped[i] = ((payload[i] << 8) | (payload[i] >> 8)) & 0xffff;
    }

    spi_transaction_ext_t t = (spi_transaction_ext_t){
        .base = {
            .flags = (SPI_TRANS_VARIABLE_ADDR | SPI_TRANS_VARIABLE_CMD),
            .addr = header,
            .length = payload_length * 2 * 8,
            .rx_buffer = NULL,
            .tx_buffer = (void *)swapped,
        },
        .command_bits = 0,
        .address_bits = 16,
        .dummy_bits = 0,
    };

    esp_err_t err = spi_device_transmit((spi_device_handle_t)handle, (spi_transaction_t *)&t);
    free(swapped);
    return (int8_t)err;
}

static int8_t combridge_delay(uint32_t period_ms)
{
    vTaskDelay(period_ms / portTICK_PERIOD_MS);
    return 0;
}

/* ----------------------------------------------------------------------- */
/* Helpers                                                                  */
/* ----------------------------------------------------------------------- */

static void bmv080_raise(const char *what, bmv080_status_code_t status)
{
    mp_raise_msg_varg(&mp_type_OSError, MP_ERROR_TEXT("%s failed with BMV080 status %d"),
                      what, (int)status);
}

// data_ready callback: copy the sensor output into the caller-provided capture.
static void bmv080_data_ready_cb(bmv080_output_t output, void *params)
{
    bmv080_capture_t *cap = (bmv080_capture_t *)params;
    cap->out = output;
    cap->got = true;
}

/* ----------------------------------------------------------------------- */
/* Constructor                                                              */
/* ----------------------------------------------------------------------- */

static mp_obj_t bmv080_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw,
                                const mp_obj_t *all_args)
{
    enum { ARG_sck, ARG_mosi, ARG_miso, ARG_cs, ARG_host, ARG_freq };
    const mp_arg_t allowed_args[] = {
        { MP_QSTR_sck,  MP_ARG_INT | MP_ARG_KW_ONLY | MP_ARG_REQUIRED },
        { MP_QSTR_mosi, MP_ARG_INT | MP_ARG_KW_ONLY | MP_ARG_REQUIRED },
        { MP_QSTR_miso, MP_ARG_INT | MP_ARG_KW_ONLY | MP_ARG_REQUIRED },
        { MP_QSTR_cs,   MP_ARG_INT | MP_ARG_KW_ONLY | MP_ARG_REQUIRED },
        { MP_QSTR_host, MP_ARG_INT | MP_ARG_KW_ONLY, { .u_int = 2 } },        // SPI3_HOST
        { MP_QSTR_freq, MP_ARG_INT | MP_ARG_KW_ONLY, { .u_int = 1000000 } },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all_kw_array(n_args, n_kw, all_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_bmv080_obj_t *self = m_new_obj(mp_bmv080_obj_t);
    self->base.type = &mp_bmv080_type;
    self->sck = args[ARG_sck].u_int;
    self->mosi = args[ARG_mosi].u_int;
    self->miso = args[ARG_miso].u_int;
    self->cs = args[ARG_cs].u_int;
    self->host = args[ARG_host].u_int;
    self->freq = args[ARG_freq].u_int;
    self->spi = NULL;
    self->handle = NULL;
    self->bus_initialized = false;
    self->measuring = false;

    return MP_OBJ_FROM_PTR(self);
}

/* ----------------------------------------------------------------------- */
/* open(): init SPI bus + device, open the vendor driver                    */
/* ----------------------------------------------------------------------- */

static mp_obj_t mp_bmv080_open(mp_obj_t self_in)
{
    mp_bmv080_obj_t *self = MP_OBJ_TO_PTR(self_in);

    if (self->handle != NULL) {
        return mp_const_none;  // already open
    }

    spi_bus_config_t buscfg = {
        .miso_io_num = self->miso,
        .mosi_io_num = self->mosi,
        .sclk_io_num = self->sck,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
    };
    esp_err_t err = spi_bus_initialize(self->host, &buscfg, SPI_DMA_CH_AUTO);
    if (err != ESP_OK) {
        mp_raise_msg_varg(&mp_type_OSError, MP_ERROR_TEXT("spi_bus_initialize failed %d"), (int)err);
    }
    self->bus_initialized = true;

    spi_device_interface_config_t devcfg = {
        .address_bits = 16,
        .clock_speed_hz = self->freq,
        .mode = 0,
        .spics_io_num = self->cs,
        .queue_size = 1,
    };
    err = spi_bus_add_device(self->host, &devcfg, &self->spi);
    if (err != ESP_OK) {
        spi_bus_free(self->host);
        self->bus_initialized = false;
        mp_raise_msg_varg(&mp_type_OSError, MP_ERROR_TEXT("spi_bus_add_device failed %d"), (int)err);
    }

    bmv080_status_code_t st = bmv080_open(&self->handle, (bmv080_sercom_handle_t)self->spi,
                                          (const bmv080_callback_read_t)combridge_spi_read_16bit,
                                          (const bmv080_callback_write_t)combridge_spi_write_16bit,
                                          (const bmv080_callback_delay_t)combridge_delay);
    if (st != E_BMV080_OK) {
        spi_bus_remove_device(self->spi);
        self->spi = NULL;
        spi_bus_free(self->host);
        self->bus_initialized = false;
        self->handle = NULL;
        bmv080_raise("bmv080_open", st);
    }

    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(bmv080_open_obj, mp_bmv080_open);

/* ----------------------------------------------------------------------- */
/* driver_version() -> (major, minor, patch)                                */
/* ----------------------------------------------------------------------- */

static mp_obj_t bmv080_driver_version(mp_obj_t self_in)
{
    (void)self_in;
    uint16_t major = 0, minor = 0, patch = 0;
    char git_hash[12] = {0};
    int32_t commits = 0;
    bmv080_status_code_t st = bmv080_get_driver_version(&major, &minor, &patch, git_hash, &commits);
    if (st != E_BMV080_OK) {
        bmv080_raise("bmv080_get_driver_version", st);
    }
    mp_obj_t tup[3] = {
        mp_obj_new_int(major), mp_obj_new_int(minor), mp_obj_new_int(patch),
    };
    return mp_obj_new_tuple(3, tup);
}
static MP_DEFINE_CONST_FUN_OBJ_1(bmv080_driver_version_obj, bmv080_driver_version);

/* ----------------------------------------------------------------------- */
/* configure(): set measurement parameters before start()                   */
/* ----------------------------------------------------------------------- */

static mp_obj_t bmv080_configure(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args)
{
    enum { ARG_self, ARG_integration_time, ARG_algorithm, ARG_obstruction, ARG_vibration };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_self,             MP_ARG_OBJ | MP_ARG_REQUIRED },
        { MP_QSTR_integration_time, MP_ARG_OBJ | MP_ARG_KW_ONLY, { .u_obj = mp_const_none } },
        { MP_QSTR_algorithm,        MP_ARG_OBJ | MP_ARG_KW_ONLY, { .u_obj = mp_const_none } },
        { MP_QSTR_obstruction,      MP_ARG_OBJ | MP_ARG_KW_ONLY, { .u_obj = mp_const_none } },
        { MP_QSTR_vibration,        MP_ARG_OBJ | MP_ARG_KW_ONLY, { .u_obj = mp_const_none } },
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, pos_args, kw_args, MP_ARRAY_SIZE(allowed_args), allowed_args, args);

    mp_bmv080_obj_t *self = MP_OBJ_TO_PTR(args[ARG_self].u_obj);
    if (self->handle == NULL) {
        mp_raise_msg(&mp_type_OSError, MP_ERROR_TEXT("sensor not open"));
    }

    bmv080_status_code_t st;
    if (args[ARG_integration_time].u_obj != mp_const_none) {
        float v = mp_obj_get_float(args[ARG_integration_time].u_obj);
        st = bmv080_set_parameter(self->handle, "integration_time", &v);
        if (st != E_BMV080_OK) bmv080_raise("set integration_time", st);
    }
    if (args[ARG_algorithm].u_obj != mp_const_none) {
        bmv080_measurement_algorithm_t a =
            (bmv080_measurement_algorithm_t)mp_obj_get_int(args[ARG_algorithm].u_obj);
        st = bmv080_set_parameter(self->handle, "measurement_algorithm", &a);
        if (st != E_BMV080_OK) bmv080_raise("set measurement_algorithm", st);
    }
    if (args[ARG_obstruction].u_obj != mp_const_none) {
        bool b = mp_obj_is_true(args[ARG_obstruction].u_obj);
        st = bmv080_set_parameter(self->handle, "do_obstruction_detection", &b);
        if (st != E_BMV080_OK) bmv080_raise("set do_obstruction_detection", st);
    }
    if (args[ARG_vibration].u_obj != mp_const_none) {
        bool b = mp_obj_is_true(args[ARG_vibration].u_obj);
        st = bmv080_set_parameter(self->handle, "do_vibration_filtering", &b);
        if (st != E_BMV080_OK) bmv080_raise("set do_vibration_filtering", st);
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_KW(bmv080_configure_obj, 1, bmv080_configure);

/* ----------------------------------------------------------------------- */
/* start() / stop()                                                         */
/* ----------------------------------------------------------------------- */

static mp_obj_t bmv080_start(mp_obj_t self_in)
{
    mp_bmv080_obj_t *self = MP_OBJ_TO_PTR(self_in);
    if (self->handle == NULL) {
        mp_raise_msg(&mp_type_OSError, MP_ERROR_TEXT("sensor not open"));
    }
    bmv080_status_code_t st = bmv080_start_continuous_measurement(self->handle);
    if (st != E_BMV080_OK) {
        bmv080_raise("bmv080_start_continuous_measurement", st);
    }
    self->measuring = true;
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(bmv080_start_obj, bmv080_start);

static mp_obj_t bmv080_stop(mp_obj_t self_in)
{
    mp_bmv080_obj_t *self = MP_OBJ_TO_PTR(self_in);
    if (self->handle == NULL || !self->measuring) {
        return mp_const_none;
    }
    bmv080_status_code_t st = bmv080_stop_measurement(self->handle);
    if (st != E_BMV080_OK) {
        bmv080_raise("bmv080_stop_measurement", st);
    }
    self->measuring = false;
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(bmv080_stop_obj, bmv080_stop);

/* ----------------------------------------------------------------------- */
/* read() -> dict | None                                                    */
/* Polls the sensor via bmv080_serve_interrupt. Returns a dict when a new   */
/* sample is available, otherwise None.                                     */
/* ----------------------------------------------------------------------- */

static mp_obj_t bmv080_read(mp_obj_t self_in)
{
    mp_bmv080_obj_t *self = MP_OBJ_TO_PTR(self_in);
    if (self->handle == NULL || !self->measuring) {
        mp_raise_msg(&mp_type_OSError, MP_ERROR_TEXT("measurement not started"));
    }

    bmv080_capture_t cap = { .got = false };
    bmv080_status_code_t st = bmv080_serve_interrupt(self->handle, bmv080_data_ready_cb, &cap);
    if (st != E_BMV080_OK) {
        bmv080_raise("bmv080_serve_interrupt", st);
    }
    if (!cap.got) {
        return mp_const_none;
    }

    mp_obj_t dict = mp_obj_new_dict(11);
    #define STORE_F(key, val) \
        mp_obj_dict_store(dict, MP_ROM_QSTR(MP_QSTR_##key), mp_obj_new_float((mp_float_t)(val)))
    #define STORE_B(key, val) \
        mp_obj_dict_store(dict, MP_ROM_QSTR(MP_QSTR_##key), mp_obj_new_bool(val))

    STORE_F(runtime, cap.out.runtime_in_sec);
    STORE_F(pm1, cap.out.pm1_mass_concentration);
    STORE_F(pm2_5, cap.out.pm2_5_mass_concentration);
    STORE_F(pm10, cap.out.pm10_mass_concentration);
    STORE_F(pm1_number, cap.out.pm1_number_concentration);
    STORE_F(pm2_5_number, cap.out.pm2_5_number_concentration);
    STORE_F(pm10_number, cap.out.pm10_number_concentration);
    STORE_B(is_obstructed, cap.out.is_obstructed);
    STORE_B(is_outside_measurement_range, cap.out.is_outside_measurement_range);
    #undef STORE_F
    #undef STORE_B

    return dict;
}
static MP_DEFINE_CONST_FUN_OBJ_1(bmv080_read_obj, bmv080_read);

/* ----------------------------------------------------------------------- */
/* close() / __del__                                                        */
/* ----------------------------------------------------------------------- */

static mp_obj_t mp_bmv080_close(mp_obj_t self_in)
{
    mp_bmv080_obj_t *self = MP_OBJ_TO_PTR(self_in);

    if (self->handle != NULL) {
        if (self->measuring) {
            bmv080_stop_measurement(self->handle);
            self->measuring = false;
        }
        bmv080_close(&self->handle);
        self->handle = NULL;
    }
    if (self->spi != NULL) {
        spi_bus_remove_device(self->spi);
        self->spi = NULL;
    }
    if (self->bus_initialized) {
        spi_bus_free(self->host);
        self->bus_initialized = false;
    }
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_1(bmv080_close_obj, mp_bmv080_close);

/* ----------------------------------------------------------------------- */
/* Type / module                                                            */
/* ----------------------------------------------------------------------- */

static const mp_rom_map_elem_t bmv080_locals_dict_table[] = {
    { MP_ROM_QSTR(MP_QSTR_open),           MP_ROM_PTR(&bmv080_open_obj) },
    { MP_ROM_QSTR(MP_QSTR_driver_version), MP_ROM_PTR(&bmv080_driver_version_obj) },
    { MP_ROM_QSTR(MP_QSTR_configure),      MP_ROM_PTR(&bmv080_configure_obj) },
    { MP_ROM_QSTR(MP_QSTR_start),          MP_ROM_PTR(&bmv080_start_obj) },
    { MP_ROM_QSTR(MP_QSTR_read),           MP_ROM_PTR(&bmv080_read_obj) },
    { MP_ROM_QSTR(MP_QSTR_stop),           MP_ROM_PTR(&bmv080_stop_obj) },
    { MP_ROM_QSTR(MP_QSTR_close),          MP_ROM_PTR(&bmv080_close_obj) },
    { MP_ROM_QSTR(MP_QSTR___del__),        MP_ROM_PTR(&bmv080_close_obj) },
};
static MP_DEFINE_CONST_DICT(bmv080_locals_dict, bmv080_locals_dict_table);

MP_DEFINE_CONST_OBJ_TYPE(
    mp_bmv080_type,
    MP_QSTR_BMV080,
    MP_TYPE_FLAG_NONE,
    make_new, bmv080_make_new,
    locals_dict, (mp_obj_dict_t *)&bmv080_locals_dict
);

static const mp_rom_map_elem_t bmv080_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__),        MP_OBJ_NEW_QSTR(MP_QSTR_bmv080) },
    { MP_ROM_QSTR(MP_QSTR_BMV080),          MP_ROM_PTR(&mp_bmv080_type) },
    // measurement_algorithm constants
    { MP_ROM_QSTR(MP_QSTR_FAST_RESPONSE),   MP_ROM_INT(E_BMV080_MEASUREMENT_ALGORITHM_FAST_RESPONSE) },
    { MP_ROM_QSTR(MP_QSTR_BALANCED),        MP_ROM_INT(E_BMV080_MEASUREMENT_ALGORITHM_BALANCED) },
    { MP_ROM_QSTR(MP_QSTR_HIGH_PRECISION),  MP_ROM_INT(E_BMV080_MEASUREMENT_ALGORITHM_HIGH_PRECISION) },
};
static MP_DEFINE_CONST_DICT(bmv080_globals, bmv080_globals_table);

const mp_obj_module_t module_bmv080 = {
    .base    = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&bmv080_globals,
};

MP_REGISTER_MODULE(MP_QSTR_bmv080, module_bmv080);
