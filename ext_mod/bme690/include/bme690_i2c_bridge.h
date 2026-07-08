// I2C com-bridge for the BME690 sensor, built on the ESP-IDF 5.x "new" I2C
// master driver (driver/i2c_master.h) so it can coexist with MicroPython's
// machine.I2C (legacy driver) as long as they use different I2C port numbers.

#ifndef BME690_I2C_BRIDGE_H_
#define BME690_I2C_BRIDGE_H_

#include <stdint.h>
#include "driver/i2c_master.h"
#include "bme69x_defs.h"

// Per-sensor I2C context. A pointer to this is stored in bme69x_dev.intf_ptr.
typedef struct _bme690_i2c_t {
    i2c_master_bus_handle_t bus;
    i2c_master_dev_handle_t dev;
    int port;
    bool bus_owned;   // true if we created the bus (and must delete it)
} bme690_i2c_t;

// Initialise the I2C bus + device. Returns ESP_OK on success.
esp_err_t bme690_i2c_init(bme690_i2c_t *ctx, int port, int sda, int scl,
                          uint32_t freq, uint8_t addr);

void bme690_i2c_deinit(bme690_i2c_t *ctx);

// bme69x_dev callback implementations.
BME69X_INTF_RET_TYPE bme690_i2c_read(uint8_t reg_addr, uint8_t *reg_data,
                                     uint32_t length, void *intf_ptr);
BME69X_INTF_RET_TYPE bme690_i2c_write(uint8_t reg_addr, const uint8_t *reg_data,
                                      uint32_t length, void *intf_ptr);
void bme690_delay_us(uint32_t period, void *intf_ptr);

#endif /* BME690_I2C_BRIDGE_H_ */
