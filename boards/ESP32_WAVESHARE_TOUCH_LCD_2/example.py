# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()

import gc
import os
from micropython import const
import machine
import waveshare as ws
import lcd_bus
import i2c
import lvgl as lv
import st7789
import task_handler
from machine import SPI
from i2c import I2C
import fs_driver


TFT_WIDTH = ws.LCD_WIDTH
TFT_HEIGHT = ws.LCD_HEIGHT
TFT_FREQ = const(40_000_000)
TP_FREQ = const(100_000)

def createimagefromfile(path):
    
    with open(path, 'rb') as f:
        imgdata = f.read()
    
    imagedsc = lv.image_dsc_t({
        'data_size': len(imgdata),
        'data': imgdata
    })
    
    return imagedsc


class test:
    def __init__(self):
        pass
    
    def start(self):
        spi_bus = SPI.Bus(
            host=1,
            miso=ws.LCD_MISO,
            mosi=ws.LCD_MOSI,
            sck=ws.LCD_SCLK
        )
        
        sd_bus = SPI.Bus(
            host=2,
            miso=ws.SD_MISO,
            mosi=ws.SD_MOSI,
            sck=ws.SD_SCLK
        )
        
        display_bus = lcd_bus.SPIBus(
            spi_bus=spi_bus,
            dc=ws.LCD_DC,
            cs=ws.LCD_CS,
            freq=TFT_FREQ
        )

        #buf1 = display_bus.allocate_framebuffer((int)(TFT_WIDTH * TFT_WIDTH / 10), lcd_bus.MEMORY_INTERNAL | lcd_bus.MEMORY_DMA)
        #buf2 = display_bus.allocate_framebuffer((int)(TFT_WIDTH * TFT_WIDTH / 10), lcd_bus.MEMORY_INTERNAL | lcd_bus.MEMORY_DMA)
        buf1 = display_bus.allocate_framebuffer((int)(TFT_WIDTH * TFT_WIDTH / 10), lcd_bus.MEMORY_SPIRAM)
        buf2 = display_bus.allocate_framebuffer((int)(TFT_WIDTH * TFT_WIDTH / 10), lcd_bus.MEMORY_SPIRAM)

        lv.init()
        #lv.log_register_print_cb(print)
        
        display = st7789.ST7789(
            data_bus=display_bus,
            display_width=ws.LCD_WIDTH,
            display_height=ws.LCD_HEIGHT,
            frame_buffer1=buf1,
            frame_buffer2=buf2,
            reset_pin=ws.LCD_RST,
            reset_state=st7789.STATE_LOW,
            backlight_pin=ws.LCD_BL,
            backlight_on_state=st7789.STATE_LOW,
            color_space=lv.COLOR_FORMAT.RGB565,
            color_byte_order=st7789.BYTE_ORDER_BGR,
            rgb565_byte_swap=True
        )
        '''
        i2c_bus = I2C.Bus(host=1, scl=f3.I2C_SCL, sda=f3.I2C_SDA, freq=TP_FREQ)
        touch_i2c = I2C.Device(i2c_bus, ft5x36.I2C_ADDR, ft5x36.BITS)
        indev = ft5x36.FT5x36(
            device=touch_i2c,
            touch_cal=None,
            startup_rotation=lv.DISPLAY_ROTATION._180,  # NOQA
            debug=False,
            factors=(1.0, 1.0))
        '''
        
        sd = machine.SDCard(spi_bus=sd_bus, cs=ws.SD_CS, freq=10_000_000)
        os.mount(sd, '/sd')
        
        #fs_drv = lv.fs_drv_t()
        #fs_driver.fs_register(fs_drv, 'S')

        display.init()
        display.set_power(True)
        #display.set_params(display._INVOFF)
        display.set_rotation(lv.DISPLAY_ROTATION._90)
        display.set_backlight(100)

        th = task_handler.TaskHandler()
        
        def touch_event(evt):
            code = evt.get_code()
            if code == lv.EVENT.CLICKED:
                print("Clicked event seen")
            elif code == lv.EVENT.VALUE_CHANGED:
                print("Value changed seen")


        def create_slider(color):
            slider = lv.slider(lv.screen_active())
            slider.set_range(0, 255)
            slider.set_size(10, 130)
            slider.set_style_bg_color(color, lv.PART.KNOB)
            slider.set_style_bg_color(color, lv.PART.INDICATOR)
            slider.add_event_cb(slider_event_cb, lv.EVENT.VALUE_CHANGED, None)
            return slider

        def slider_event_cb(e):
            # Recolor the image based on the sliders' values
            color  = lv.color_make(red_slider.get_value(), green_slider.get_value(), blue_slider.get_value())
            intense = intense_slider.get_value()
            #print(intense)
            #img.set_style_img_recolor_opa(intense, 0)
            #img.set_style_img_recolor(color, 0)
        
        scr = lv.screen_active()
        scr.set_style_bg_color(lv.color_hex(0xdddddd), 0)
        btn = lv.button(scr)
        btn.align(lv.ALIGN.CENTER, 0, 0)
        btn.add_event_cb(touch_event, lv.EVENT.ALL, None)
        label = lv.label(btn)
        label.set_text('Hello World!')

        img = lv.image(scr)
        img.set_src(createimagefromfile('/sd/transistor.png'))
        img.set_pos(50, 50)
        
        img = lv.image(scr)
        img.set_src(createimagefromfile('/sd/gearsx32px.png'))
        img.set_pos(100, 50)
        
        img = lv.image(scr)
        img.set_src(createimagefromfile('/sd/graduationx32.png'))
        img.set_pos(150, 50)
        
        img = lv.image(scr)
        img.set_src(createimagefromfile('/sd/wrenchx32.png'))
        img.set_pos(200, 50)
        
        img = lv.image(scr)
        img.set_src(createimagefromfile('/sd/gearx48.png'))
        img.set_pos(250, 50)
        
        '''
        img = lv.image(scr)
        img.set_src(createimagefromfile('/sd/day-rain.png'))
        img.set_pos(150, 0)
        
        red_slider = create_slider(lv.palette_main(lv.PALETTE.RED))
        green_slider = create_slider(lv.palette_main(lv.PALETTE.GREEN))
        blue_slider = create_slider(lv.palette_main(lv.PALETTE.BLUE))
        intense_slider = create_slider(lv.palette_main(lv.PALETTE.GREY))

        red_slider.set_value(lv.OPA._20, lv.ANIM.ON)
        green_slider.set_value(lv.OPA._90, lv.ANIM.OFF)
        blue_slider.set_value(lv.OPA._60, lv.ANIM.OFF)
        intense_slider.set_value(lv.OPA._50, lv.ANIM.OFF)

        red_slider.align(lv.ALIGN.LEFT_MID, 25, 0)
        green_slider.align_to(red_slider, lv.ALIGN.OUT_RIGHT_MID, 25, 0)
        blue_slider.align_to(green_slider, lv.ALIGN.OUT_RIGHT_MID, 25, 0)
        intense_slider.align_to(blue_slider, lv.ALIGN.OUT_RIGHT_MID, 25, 0)
        '''
        #lv.event_send(intense_slider, lv.EVENT.VALUE_CHANGED, None)
        #lv.scr_load(scr)
