import os
import machine
import feathers3 as f3
import lvgl as lv
import lcd_bus
import i2c
import hx8357b
import ft5x36
import task_handler
from machine import SPI
from i2c import I2C
import fs_driver


TFT_WIDTH = const(320)
TFT_HEIGHT = const(480)
TFT_DC = const(3)
TFT_CS = const(1)
TFT_FREQ = const(40_000_000)
TP_FREQ = const(100_000)
SD_CS = const(5)

class peripherals:
    def __init__(self):     
        spi_bus = SPI.Bus(
                    host=1,
                    miso=f3.SPI_MISO,
                    mosi=f3.SPI_MOSI,
                    sck=f3.SPI_CLK)

        display_bus = lcd_bus.SPIBus(
            spi_bus=spi_bus,
            dc=TFT_DC,
            cs=TFT_CS,
            freq=TFT_FREQ
        )

        buf1 = display_bus.allocate_framebuffer((int)(TFT_WIDTH * TFT_WIDTH * 2 / 10), lcd_bus.MEMORY_INTERNAL | lcd_bus.MEMORY_DMA)
        buf2 = display_bus.allocate_framebuffer((int)(TFT_WIDTH * TFT_WIDTH * 2 / 10), lcd_bus.MEMORY_INTERNAL | lcd_bus.MEMORY_DMA)
        #buf1 = display_bus.allocate_framebuffer((int)(TFT_WIDTH * TFT_WIDTH * 2 / 10), lcd_bus.MEMORY_SPIRAM)
        #buf2 = display_bus.allocate_framebuffer((int)(TFT_WIDTH * TFT_WIDTH * 2 / 10), lcd_bus.MEMORY_SPIRAM)

        lv.init()
        
        display = hx8357b.HX8357B(
            data_bus=display_bus,
            display_width=TFT_WIDTH,
            display_height=TFT_HEIGHT,
            frame_buffer1=buf1,
            frame_buffer2=buf2,
            color_space=lv.COLOR_FORMAT.RGB565,
            color_byte_order=hx8357b.BYTE_ORDER_BGR,
            rgb565_byte_swap=True
        )

        i2c_bus = I2C.Bus(host=1, scl=f3.I2C_SCL, sda=f3.I2C_SDA, freq=TP_FREQ)
        touch_i2c = I2C.Device(i2c_bus, ft5x36.I2C_ADDR, ft5x36.BITS)
        indev = ft5x36.FT5x36(
            device=touch_i2c,
            touch_cal=None,
            startup_rotation=lv.DISPLAY_ROTATION._180,  # NOQA
            debug=False,
            factors=(1.0, 1.0))

        sd = machine.SDCard(spi_bus=spi_bus, cs=33, freq=10_000_000)
        os.mount(sd, '/sd')

        #fs_drv = lv.fs_drv_t()
        #fs_driver.fs_register(fs_drv, 'S')

        display.init()
        display.set_params(display._INVOFF)
        display.set_rotation(lv.DISPLAY_ROTATION._90)
        display.set_backlight(100)
