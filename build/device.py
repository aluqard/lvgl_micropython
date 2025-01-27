from micropython import const
import lcd_bus
import sdl_pointer
import task_handler
import lvgl as lv
import sdl_display
import display_driver_framework
import fs_driver

_WIDTH = const(480)
_HEIGHT = const(320)

class DEVICE:
    def __init__(self, width = _WIDTH, height = _HEIGHT):
        bus = lcd_bus.SDLBus(flags=0)
        buf1 = bus.allocate_framebuffer(width * height * 4, 0)

        display = sdl_display.SDLDisplay(
            data_bus=bus,
            display_width=width,
            display_height=height,
            frame_buffer1=buf1,
            color_space=lv.COLOR_FORMAT.ARGB8888,
            color_byte_order=display_driver_framework.BYTE_ORDER_BGR
        )
        display.init()

        mouse = sdl_pointer.SDLPointer()
        th = task_handler.TaskHandler(duration=5)

        fs_drv = lv.fs_drv_t()
        fs_driver.fs_register(fs_drv, 'D')