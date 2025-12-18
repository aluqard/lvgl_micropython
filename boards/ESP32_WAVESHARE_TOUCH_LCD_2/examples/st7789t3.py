import time
from micropython import const  # NOQA
from machine import Pin

import lvgl as lv  # NOQA
import lcd_bus  # NOQA
import display_driver_framework


_SWRESET = const(0x01)
_SLPIN = const(0x10)
_SLPOUT = const(0x11)
_PTLON = const(0x12)
_NORON = const(0x13)
_MADCTL = const(0x36)
_COLMOD = const(0x3A)
_IFMODE = const(0xB0)
_PORCTRL = const(0xB2)
_GCTRL = const(0xB7)
_VCOMS = const(0xBB)
_LCMCTRL = const(0xC0)
_VDVVRHEN = const(0xC2)
_VRHS = const(0xC3)
_VDVSET = const(0xC4)
_FRCTR2 = const(0xC6)
_PWCTRL1 = const(0xD0)
_INVON = const(0x21)
_CASET = const(0x2A)
_RASET = const(0x2B)
_PGC = const(0xE0)
_NGC = const(0xE1)
_DISPON = const(0x29)

COLOR_MODE_65K = const(0x50)
COLOR_MODE_16BIT = const(0x05)
COLOR_MODE_262K = const(0x60)

STATE_HIGH = display_driver_framework.STATE_HIGH
STATE_LOW = display_driver_framework.STATE_LOW
STATE_PWM = display_driver_framework.STATE_PWM

BYTE_ORDER_RGB = display_driver_framework.BYTE_ORDER_RGB
BYTE_ORDER_BGR = display_driver_framework.BYTE_ORDER_BGR

_MADCTL_MH = const(0x04)  # Refresh 0=Left to Right, 1=Right to Left
_MADCTL_BGR = const(0x08)  # BGR color order
_MADCTL_ML = const(0x10)  # Refresh 0=Top to Bottom, 1=Bottom to Top
_MADCTL_MV = const(0x20)  # 0=Normal, 1=Row/column exchange
_MADCTL_MX = const(0x40)  # 0=Left to Right, 1=Right to Left
_MADCTL_MY = const(0x80)  # 0=Top to Bottom, 1=Bottom to Top


class ST7789T3(display_driver_framework.DisplayDriver):
    _ORIENTATION_TABLE = (
        0x0,
        _MADCTL_MV | _MADCTL_MY,
        _MADCTL_MY | _MADCTL_MX,
        _MADCTL_MV | _MADCTL_MX
    )

    def init(self):
        param_buf = bytearray(14)
        param_mv = memoryview(param_buf)
        
        # exit sleep mode
        self.set_params(_SLPOUT)
        time.sleep_ms(500)  # NOQA
        
        #param_buf[0] = (COLOR_MODE_262K | COLOR_MODE_16BIT) & 0x77
        param_buf[0] = 0x55
        self.set_params(_COLMOD, param_mv[:1])
        time.sleep_ms(50)  # NOQA
        
        param_buf[0] = 0x00
        self.set_params(_MADCTL, param_mv[:1])
        
        param_buf[0] = 0x00
        param_buf[1] = 0x00
        param_buf[2] = 0x00
        param_buf[3] = 0xF0
        self.set_params(_CASET, param_mv[:4])
        
        param_buf[0] = 0x00
        param_buf[1] = 0x00
        param_buf[2] = 0x00
        param_buf[3] = 0xF0
        self.set_params(_RASET, param_mv[:4])
        
        self.set_params(_INVON)
        time.sleep_ms(10)  # NOQA
        
        self.set_params(_NORON)
        time.sleep_ms(10)  # NOQA
        
        self.set_params(_DISPON)
        time.sleep_ms(500)  # NOQA
        
        display_driver_framework.DisplayDriver.init(self)

