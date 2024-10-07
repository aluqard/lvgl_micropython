import gc
import thmi
import lcd_bus
import task_handler
from machine import SPI, Pin, SDCard
import fs_driver

thmi.power_on()
thmi.enable()

disp_bus = lcd_bus.I80Bus(
    dc=thmi.LCD_DC_PIN,
    wr=thmi.LCD_PCLK_PIN,
    freq=20_000_000,
    data0=thmi.LCD_DATA0_PIN,
    data1=thmi.LCD_DATA1_PIN,
    data2=thmi.LCD_DATA2_PIN,
    data3=thmi.LCD_DATA3_PIN,
    data4=thmi.LCD_DATA4_PIN,
    data5=thmi.LCD_DATA5_PIN,
    data6=thmi.LCD_DATA6_PIN,
    data7=thmi.LCD_DATA7_PIN)

fb1 = disp_bus.allocate_framebuffer(int(thmi.LCD_WIDTH * thmi.LCD_WIDTH / 10), lcd_bus.MEMORY_INTERNAL | lcd_bus.MEMORY_DMA)
fb2 = disp_bus.allocate_framebuffer(int(thmi.LCD_WIDTH * thmi.LCD_WIDTH / 10), lcd_bus.MEMORY_INTERNAL | lcd_bus.MEMORY_DMA)

#fb1 = disp_bus.allocate_framebuffer(int(thmi.LCD_WIDTH * thmi.LCD_WIDTH / 10), lcd_bus.MEMORY_SPIRAM)
#fb2 = disp_bus.allocate_framebuffer(int(thmi.LCD_WIDTH * thmi.LCD_WIDTH / 10), lcd_bus.MEMORY_SPIRAM)
    
import st7789
import lvgl as lv

lv.init()

display = st7789.ST7789(
    data_bus=disp_bus,
    frame_buffer1=fb1,
    frame_buffer2=fb2,
    display_width=thmi.LCD_WIDTH,
    display_height=thmi.LCD_HEIGHT,
    power_pin=thmi.PWR_EN_PIN,
    power_on_state=st7789.STATE_HIGH,
    backlight_pin=thmi.LCD_BK_LIGHT_PIN,
    backlight_on_state=st7789.STATE_HIGH,
    # reset=_RST,
    # reset_state=st7796.STATE_LOW,
    color_space=lv.COLOR_FORMAT.RGB565,
    color_byte_order=st7789.BYTE_ORDER_BGR,
    rgb565_byte_swap=True,
)

import xpt2046

spi_bus = SPI.Bus(
    host=1,
    mosi=thmi.TP_MOSI_PIN,
    miso=thmi.TP_MISO_PIN,
    sck=thmi.TP_SCLK_PIN)

api_dev = SPI.Device(
    spi_bus=spi_bus,
    freq=1_000_000,
    cs=thmi.TP_CS_PIN)

indev = xpt2046.XPT2046(api_dev)

display.init()
display.set_power(True)
display.set_rotation(lv.DISPLAY_ROTATION._180)
#display.invert_colors()
display.set_params(display._INVOFF)
display.set_backlight(100)

th = task_handler.TaskHandler()

scrn = lv.screen_active()
scrn.set_style_bg_color(lv.color_hex(0xffffff), 0)

slider = lv.slider(scrn)
slider.set_size(150, 20)
slider.center()

label = lv.label(scrn)
label.set_text('HELLO WORLD!')
label.align(lv.ALIGN.CENTER, 0, -50)


import time

print('red')
scrn = lv.screen_active()
scrn.set_style_bg_color(lv.color_hex(0xFF0000), 0)
lv.refr_now(lv.display_get_default())
time.sleep_ms(5000)

print('green')
scrn.set_style_bg_color(lv.color_hex(0x00FF00), 0)
lv.refr_now(lv.display_get_default())
time.sleep_ms(5000)

print('blue')
scrn.set_style_bg_color(lv.color_hex(0x0000FF), 0)
lv.refr_now(lv.display_get_default())

