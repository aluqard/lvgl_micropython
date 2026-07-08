#include "bme690_i2c_bridge.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_rom_sys.h"   // esp_rom_delay_us

#define BME690_I2C_TIMEOUT_MS   1000

esp_err_t bme690_i2c_init(bme690_i2c_t *ctx, int port, int sda, int scl,
                          uint32_t freq, uint8_t addr)
{
    ctx->port = port;
    ctx->bus = NULL;
    ctx->dev = NULL;
    ctx->bus_owned = false;

    i2c_master_bus_config_t bus_cfg = {
        .i2c_port = port,
        .sda_io_num = sda,
        .scl_io_num = scl,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    esp_err_t err = i2c_new_master_bus(&bus_cfg, &ctx->bus);
    if (err != ESP_OK) {
        return err;
    }
    ctx->bus_owned = true;

    i2c_device_config_t dev_cfg = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address = addr,
        .scl_speed_hz = freq,
    };
    err = i2c_master_bus_add_device(ctx->bus, &dev_cfg, &ctx->dev);
    if (err != ESP_OK) {
        i2c_del_master_bus(ctx->bus);
        ctx->bus = NULL;
        ctx->bus_owned = false;
        return err;
    }
    return ESP_OK;
}

void bme690_i2c_deinit(bme690_i2c_t *ctx)
{
    if (ctx->dev != NULL) {
        i2c_master_bus_rm_device(ctx->dev);
        ctx->dev = NULL;
    }
    if (ctx->bus != NULL && ctx->bus_owned) {
        i2c_del_master_bus(ctx->bus);
        ctx->bus = NULL;
        ctx->bus_owned = false;
    }
}

// Read: write the register address, then read `length` bytes (repeated start).
BME69X_INTF_RET_TYPE bme690_i2c_read(uint8_t reg_addr, uint8_t *reg_data,
                                     uint32_t length, void *intf_ptr)
{
    bme690_i2c_t *ctx = (bme690_i2c_t *)intf_ptr;
    esp_err_t err = i2c_master_transmit_receive(ctx->dev, &reg_addr, 1,
                                                reg_data, length,
                                                BME690_I2C_TIMEOUT_MS);
    return (err == ESP_OK) ? BME69X_INTF_RET_SUCCESS : -1;
}

// Write: register address followed by the data bytes in a single transaction.
BME69X_INTF_RET_TYPE bme690_i2c_write(uint8_t reg_addr, const uint8_t *reg_data,
                                      uint32_t length, void *intf_ptr)
{
    bme690_i2c_t *ctx = (bme690_i2c_t *)intf_ptr;

    // Small stack buffer: bme69x transfers are short (register writes).
    uint8_t buf[64];
    if (length + 1 > sizeof(buf)) {
        return -1;
    }
    buf[0] = reg_addr;
    for (uint32_t i = 0; i < length; i++) {
        buf[i + 1] = reg_data[i];
    }
    esp_err_t err = i2c_master_transmit(ctx->dev, buf, length + 1, BME690_I2C_TIMEOUT_MS);
    return (err == ESP_OK) ? BME69X_INTF_RET_SUCCESS : -1;
}

void bme690_delay_us(uint32_t period, void *intf_ptr)
{
    (void)intf_ptr;
    // For long waits (>= ~2 ticks) yield to the scheduler to avoid starving
    // other tasks / tripping the watchdog; use busy-wait for short delays.
    uint32_t ms = period / 1000;
    if (ms >= (2 * portTICK_PERIOD_MS)) {
        vTaskDelay(ms / portTICK_PERIOD_MS);
    } else {
        esp_rom_delay_us(period);
    }
}
