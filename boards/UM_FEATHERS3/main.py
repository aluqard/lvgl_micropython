# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()

import gc
import os
import feathers3 as f3
from micropython import const
import peripherals
import lvgl as lv
import task_handler

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
        peripherals.peripherals()
        
    def touch_event(self, evt):
        code = evt.get_code()
        if code == lv.EVENT.CLICKED:
            print("Clicked event seen")
        elif code == lv.EVENT.VALUE_CHANGED:
            print("Value changed seen")


    def create_slider(self, color):
        slider = lv.slider(lv.screen_active())
        slider.set_range(0, 255)
        slider.set_size(10, 200)
        slider.set_style_bg_color(color, lv.PART.KNOB)
        slider.set_style_bg_color(color, lv.PART.INDICATOR)
        slider.add_event_cb(self.slider_event_cb, lv.EVENT.VALUE_CHANGED, None)
        return slider

    def slider_event_cb(self, e):
        # Recolor the image based on the sliders' values
        color  = lv.color_make(self.red_slider.get_value(), self.green_slider.get_value(), self.blue_slider.get_value())
        intense = self.intense_slider.get_value()
        #print(intense)
        #img.set_style_img_recolor_opa(intense, 0)
        #img.set_style_img_recolor(color, 0)
        
    def start(self):
        scr = lv.screen_active()
        btn = lv.button(scr)
        btn.align(lv.ALIGN.CENTER, 0, 0)
        btn.add_event_cb(self.touch_event, lv.EVENT.ALL, None)
        label = lv.label(btn)
        label.set_text('Hello World!')

        img = lv.image(scr)
        img.set_src(createimagefromfile('/sd/transistor.png'))
        img.set_pos(200, 200)
        
        img = lv.image(scr)
        img.set_src(createimagefromfile('/sd/gearsx32px.png'))
        img.set_pos(240, 200)
        
        img = lv.image(scr)
        img.set_src(createimagefromfile('/sd/graduationx32.png'))
        img.set_pos(280, 200)
        
        img = lv.image(scr)
        img.set_src(createimagefromfile('/sd/wrenchx32.png'))
        img.set_pos(320, 200)
        
        img = lv.image(scr)
        img.set_src(createimagefromfile('/sd/gearx48.png'))
        img.set_pos(360, 200)

        img = lv.image(scr)
        img.set_src(createimagefromfile('/sd/day-rain.png'))
        img.set_pos(150, 50)
        
        self.red_slider = self.create_slider(lv.palette_main(lv.PALETTE.RED))
        self.green_slider = self.create_slider(lv.palette_main(lv.PALETTE.GREEN))
        self.blue_slider = self.create_slider(lv.palette_main(lv.PALETTE.BLUE))
        self.intense_slider = self.create_slider(lv.palette_main(lv.PALETTE.GREY))

        self.red_slider.set_value(lv.OPA._20, lv.ANIM.ON)
        self.green_slider.set_value(lv.OPA._90, lv.ANIM.OFF)
        self.blue_slider.set_value(lv.OPA._60, lv.ANIM.OFF)
        self.intense_slider.set_value(lv.OPA._50, lv.ANIM.OFF)

        self.red_slider.align(lv.ALIGN.LEFT_MID, 25, 0)
        self.green_slider.align_to(self.red_slider, lv.ALIGN.OUT_RIGHT_MID, 25, 0)
        self.blue_slider.align_to(self.green_slider, lv.ALIGN.OUT_RIGHT_MID, 25, 0)
        self.intense_slider.align_to(self.blue_slider, lv.ALIGN.OUT_RIGHT_MID, 25, 0)

        #lv.event_send(intense_slider, lv.EVENT.VALUE_CHANGED, None)

        #lv.scr_load(scr)
        
        th = task_handler.TaskHandler(duration=5)


