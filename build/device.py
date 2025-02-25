from micropython import const
import lcd_bus
import sdl_pointer
import task_handler
import lvgl as lv
import sdl_display
import display_driver_framework
import fs_driver

_WIDTH = const(800)
_HEIGHT = const(480)

class DEVICE:
    def __init__(self, width=_WIDTH, height=_HEIGHT, fullscreen=False):
        self.bus = lcd_bus.SDLBus(flags=0 if fullscreen==False else 1)
        #self.buf1 = self.bus.allocate_framebuffer(1920 * 1080 * 4, 0)

        self.display = sdl_display.SDLDisplay(
            data_bus=self.bus,
            display_width=width,
            display_height=height,
            #frame_buffer1=self.buf1,
            color_space=lv.COLOR_FORMAT.ARGB8888,
            color_byte_order=display_driver_framework.BYTE_ORDER_BGR,
        )
        self.display.init()

        self.mouse = sdl_pointer.SDLPointer()
        self.th = task_handler.TaskHandler(duration=5)

        fs_drv = lv.fs_drv_t()
        fs_driver.fs_register(fs_drv, 'D')
