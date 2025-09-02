import gc
import os
import tdisplays3 as tds3
import lcd_bus
import lvgl as lv
import st7789
import task_handler
from machine import SPI, Pin
import machine

# RD 9 - might have to be pulled high
rd = machine.Pin(tds3.LCD_RD_PIN, machine.Pin.OUT)
rd.on()

# CS 6 - might have to be pulled low
cs = machine.Pin(tds3.LCD_CS_PIN, machine.Pin.OUT)
cs.off()

#pwr = Pin(tds3.PWR_ON_PIN, Pin.OUT)
#pwr.on()

#bl = Pin(tds3.LCD_BK_LIGHT_PIN, Pin.OUT)
#bl.on()

class test():
    def __init__(self):
        pass
    
    def start(self):
        self.disp_bus = lcd_bus.I80Bus(
            dc=tds3.LCD_DC_PIN,
            wr=tds3.LCD_WR_PIN,
            cs=tds3.LCD_CS_PIN,
            freq=20_000_000,
            data0=tds3.LCD_DATA0_PIN,
            data1=tds3.LCD_DATA1_PIN,
            data2=tds3.LCD_DATA2_PIN,
            data3=tds3.LCD_DATA3_PIN,
            data4=tds3.LCD_DATA4_PIN,
            data5=tds3.LCD_DATA5_PIN,
            data6=tds3.LCD_DATA6_PIN,
            data7=tds3.LCD_DATA7_PIN)

        fb1 = self.disp_bus.allocate_framebuffer(int(240 * 240 / 10), lcd_bus.MEMORY_INTERNAL | lcd_bus.MEMORY_DMA)
        fb2 = self.disp_bus.allocate_framebuffer(int(240 * 240 / 10), lcd_bus.MEMORY_INTERNAL | lcd_bus.MEMORY_DMA)

#        fb1 = disp_bus.allocate_framebuffer(int(170 * 170 / 10), lcd_bus.MEMORY_SPIRAM)
#        fb2 = disp_bus.allocate_framebuffer(int(170 * 170 / 10), lcd_bus.MEMORY_SPIRAM)

        self.display = st7789.ST7789(
            data_bus=self.disp_bus,
            frame_buffer1=fb1,
            frame_buffer2=fb2,
            display_width=240,
            display_height=320,
            reset_pin=tds3.LCD_RST_PIN,
            reset_state=st7789.STATE_LOW,
            backlight_pin=tds3.LCD_BK_LIGHT_PIN,
            backlight_on_state=st7789.STATE_HIGH,
            color_space=lv.COLOR_FORMAT.RGB888,
            color_byte_order=st7789.BYTE_ORDER_BGR
        )
        
        '''
        try:
            sd = SDCard(slot=1, freq=1_230_000)
            os.mount(sd, '/sd')
            fs_drv = lv.fs_drv_t()
            fs_driver.fs_register(fs_drv, 'S')
        except Exception as e:
            print('{e}')
        '''
        
        lv.init()

        self.display.init()
        self.display.set_power(True)
        self.display.set_rotation(lv.DISPLAY_ROTATION._270)
        #display.invert_colors(True)
        self.display.set_backlight(100)

        scr = lv.screen_active()
        scr.set_style_bg_color(lv.color_hex(0xffffff), 0)
        
        btn = lv.button(scr);
        label = lv.label(btn)
        label.set_text('HELLO WORLD!')
        btn.center()

        th = task_handler.TaskHandler()

