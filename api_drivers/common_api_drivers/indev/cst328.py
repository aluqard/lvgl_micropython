from micropython import const  # NOQA
import pointer_framework
import time
import machine  # NOQA

I2C_ADDR                  = const(0x1A)
BITS                      = 8
SYNC_SIGNAL               = const(0xAB)


# BYTE 3:KEY_NUM
# BYTE 2:TP_NRX
# BYTE 1:NC
# BYTE 0:TP_NTX
CST328_INFO_1_REG          = const(0XD1F4)

# BYTE 3 ~ BYTE 2:TP_RESY
# BYTE 1 ~ BYTE 0:TP_RESX
CST328_INFO_2_REG          = const(0XD1F8)

# BYTE 3 ~ BYTE 2:0XCACA
# BYTE 1 ~ BYTE 0:BOOT_TIMER
CST328_INFO_3_REG          = const(0XD1FC)

# BYTE 3 ~ BYTE 2:IC_TYPE
# BYTE 1 ~ BYTE 0:PROJECT_ID
CST328_INFO_4_REG          = const(0XD204)

# BYTE 3:FW_MAJOR
# BYTE 2:FW_MINOR
# BYTE 1 ~ BYTE 0:FW_BUILD
CST328_INFO_5_REG          = const(0XD208)

# BYTE 3:CHECKSNM_H
# BYTE 2:CHECKSNM_H
# BYTE 1:CHECKSNM_L
# BYTE 0:CHECKSNM_L
CST328_INFO_6_REG          = const(0XD20C)

MODE_DEBUG_INFO_REG        = const(0xD101)
CHIP_SYSTEM_RESET_REG      = const(0xD102)
REDO_CALIBRATION_REG       = const(0xD104)
CHIP_DEEP_SLEEP_REG        = const(0xD105)
MODE_DEBUG_POINT_REG       = const(0xD108)
MODE_NORMAL_REG            = const(0xD109)
MODE_DEBUG_RAWDATA_REG     = const(0xD10A)
MODE_DEBUG_WRITE_REG       = const(0xD10B)
MODE_DEBUG_CALIBRATION_REG = const(0xD10C)
MODE_DEBUG_DIFF_REG        = const(0xD10D)
MODE_FACTORY_REG           = const(0xD119)

# touch information register
# MODE_NORMAL
# BIT 7 ~ BIT 4: 1st finger ID
# BIT 3 ~ BIT 0: 1st finger state: pressed (0x06) or lifted
MODE_NORMAL_0_REG          = const(0xD000)


# BIT 7 ~ BIT 0: The X coordinate value of the 1st finger is eight high digits: X_Position>>4
MODE_NORMAL_1_REG          = const(0xD001)

# BIT 7 ~ BIT 0: The Y coordinate value of the 1st finger is eight high digits: Y_Position>>4
MODE_NORMAL_2_REG          = const(0xD002)

# BIT 7 ~ BIT 4: The X coordinate value of the 1st finger X_Position&0x0F
# BIT 3 ~ BIT 0: The Y coordinate value of the 1st finger Y_Position&0x0F
MODE_NORMAL_3_REG          = const(0xD003)


# BIT 7 ~ BIT 0: 1st finger pressure value
MODE_NORMAL_4_REG          = const(0xD004)


# BIT 7 ~ BIT 4: Report button flag (0x80)
# BIT 3 ~ BIT 0: Report the number of fingers
MODE_NORMAL_5_REG          = const(0xD005)


# BIT 7 ~ BIT 0: Fixed 0xAB
MODE_NORMAL_6_REG          = const(0xD006)

# BIT 7 ~ BIT 4: 2nd finger ID
# BIT 3 ~ BIT 0: 2nd finger state: pressed (0x06) or lifted
MODE_NORMAL_7_REG          = const(0xD007)


# BIT 7 ~ BIT 0: The X coordinate value of the 2nd finger is eight high digits: X_Position>>4
MODE_NORMAL_8_REG          = const(0xD008)

# BIT 7 ~ BIT 0: The Y coordinate value of the 2nd finger is eight high digits: Y_Position>>4
MODE_NORMAL_9_REG          = const(0xD009)

# BIT 7 ~ BIT 4: The X coordinate value of the 2nd finger X_Position&0x0F
# BIT 3 ~ BIT 0: The Y coordinate value of the 2nd finger Y_Position&0x0F
MODE_NORMAL_10_REG         = const(0xD00A)


# BIT 7 ~ BIT 0: 2nd finger pressure value
MODE_NORMAL_11_REG         = const(0xD00B)

# BIT 7 ~ BIT 4: 3rd finger ID
# BIT 3 ~ BIT 0: 3rd finger state: pressed (0x06) or lifted
MODE_NORMAL_12_REG         = const(0xD00C)

# BIT 7 ~ BIT 0: The X coordinate value of the 3rd finger is eight high digits: X_Position>>4
MODE_NORMAL_13_REG         = const(0xD00D)

# BIT 7 ~ BIT 0: The Y coordinate value of the 3rd finger is eight high digits: Y_Position>>4
MODE_NORMAL_14_REG         = const(0xD00E)

# BIT 7 ~ BIT 4: The X coordinate value of the 3rd finger X_Position&0x0F
# BIT 3 ~ BIT 0: The Y coordinate value of the 3rd finger Y_Position&0x0F
MODE_NORMAL_15_REG         = const(0xD00F)

# BIT 7 ~ BIT 0: 3rd finger pressure value
MODE_NORMAL_16_REG         = const(0xD010)

# BIT 7 ~ BIT 4: 4th finger ID
# BIT 3 ~ BIT 0: 4th finger state: pressed (0x06) or lifted
MODE_NORMAL_17_REG         = const(0xD011)

# BIT 7 ~ BIT 0: The X coordinate value of the 4th finger is eight high digits: X_Position>>4
MODE_NORMAL_18_REG         = const(0xD012)

# BIT 7 ~ BIT 0: The Y coordinate value of the 4th finger is eight high digits: Y_Position>>4
MODE_NORMAL_19_REG         = const(0xD013)

# BIT 7 ~ BIT 4: The X coordinate value of the 4th finger X_Position&0x0F
# BIT 3 ~ BIT 0: The Y coordinate value of the 4th finger Y_Position&0x0F
MODE_NORMAL_20_REG         = const(0xD014)

# BIT 7 ~ BIT 0: 4th finger pressure value
MODE_NORMAL_21_REG         = const(0xD015)

# BIT 7 ~ BIT 4: 5th finger ID
# BIT 3 ~ BIT 0: 5th finger state: pressed (0x06) or lifted
MODE_NORMAL_22_REG         = const(0xD016)

# BIT 7 ~ BIT 0: The X coordinate value of the 5th finger is eight high digits: X_Position>>4
MODE_NORMAL_23_REG         = const(0xD017)

# BIT 7 ~ BIT 0: The Y coordinate value of the 5th finger is eight high digits: Y_Position>>4
MODE_NORMAL_24_REG         = const(0xD018)

# BIT 7 ~ BIT 4: The X coordinate value of the 5th finger X_Position&0x0F
# BIT 3 ~ BIT 0: The Y coordinate value of the 5th finger Y_Position&0x0F
MODE_NORMAL_25_REG         = const(0xD019)

# BIT 7 ~ BIT 0: 5th finger pressure value
MODE_NORMAL_26_REG         = const(0xD01A)

def COMBINE_H8L4_H(buf, h, l):
    return (buf[h & 0xFF] << 4 | buf[l & 0xFF] >> 4)

def COMBINE_H8L4_L(buf, h, l):
    return (buf[h & 0xFF] << 4 | buf[l & 0xFF] & 0xF)

def COMBINE_H4L8(buf, h, l):
    return ((buf[h] & 0x0F) << 8 | buf[l])

def hw_reset(reset_pin):
    pin = machine.Pin(reset_pin, machine.Pin.OUT)
    pin.on()
    time.sleep_ms(50)  # NOQA
    pin.off()
    time.sleep_ms(5)  # NOQA
    pin.on()
    time.sleep_ms(50)  # NOQA
    
class CST328(pointer_framework.PointerDriver):
    
    def _read_reg(self, reg):
        self._tx_buf[0] = (reg >> 8) & 0xFF
        self._tx_buf[1] = reg & 0xFF
        
        for i in range(self._rx_buf_len):
            self._rx_buf[i] = 0x00
            
        self._device.write_readinto(self._tx_mv[:self._tx_buf_len], self._rx_mv[:self._rx_buf_len])

    def _write_reg(self, reg):
        self._tx_buf[0] = (reg >> 8) & 0xFF
        self._tx_buf[1] = reg & 0xFF
        self._device.write(self._tx_mv[:self._tx_buf_len])

    def _write_data(self, reg, data):
        self._tx_buf[0] = (reg >> 8) & 0xFF
        self._tx_buf[1] = reg & 0xFF
        self._device.write(self._tx_mv[:self._tx_buf_len])
        
        if data is not None:
            #for i in range(length):
            self._device.write(bytearray(data))
        
    def __init__(
        self,
        device,
        reset_pin=None,
        int_pin=None,
        touch_cal=None,
        startup_rotation=pointer_framework.lv.DISPLAY_ROTATION._0,
        debug=False
    ):
        self._touched = False
        self._fingernum = 0
        self._coord_x = -1
        self._coord_y = -1
        self.startup_rotation = startup_rotation
        
        self._tx_buf_len = const(2)
        self._rx_buf_len = const(27)
        
        self._tx_buf = bytearray(self._tx_buf_len)
        self._tx_mv = memoryview(self._tx_buf)
        self._rx_buf = bytearray(self._rx_buf_len)
        self._rx_mv = memoryview(self._rx_buf)

        self._device = device

        if reset_pin is None:
            self._reset_pin = None
        else:
            self._reset_pin = machine.Pin(reset_pin, machine.Pin.OUT)
            self._reset_pin.value(1)
        
        if int_pin is None:
            self._int_pin = None
        else:
            self._int_pin = machine.Pin(int_pin, machine.Pin.IN)
            self._int_pin.irq(trigger=machine.Pin.IRQ_RISING, handler=self._touch_cb)
        
        super().__init__(
            touch_cal=touch_cal, startup_rotation=startup_rotation, debug=debug
        )
        
        self._write_reg(MODE_DEBUG_INFO_REG)
        self._read_reg(CST328_INFO_3_REG)

    def hw_reset(self):
        if self._reset_pin is None:
            return

        self._reset_pin(1)
        time.sleep_ms(50)  # NOQA
        self._reset_pin(0)
        time.sleep_ms(5)  # NOQA
        self._reset_pin(1)
        time.sleep_ms(50)  # NOQA

    def _touch_cb(self, _):
        
        self._read_reg(MODE_NORMAL_5_REG)
        if self._rx_buf[0] & 0x0F == 0x00:
            self._write_data(MODE_NORMAL_5_REG, [0])
            self._touched = False
            #print('no touched')
   
        else:
            self._read_reg(MODE_NORMAL_0_REG)
            self._write_data(MODE_NORMAL_5_REG, [0])
            res = (self._rx_buf[MODE_NORMAL_5_REG & 0xFF] & 0x0F)
        
            pressure, x, y = self.get_point(0)
            self._touched = True
            self._coord_x = x
            self._coord_y = y
            #print('_touch_cb(): {}, {}, {}'.format(res, self._coord_x, self._coord_y))
        
    def _get_coords(self):

        if self._touched == False:
            return None
        
        pressure, x, y = self.get_point(0)
        self._coord_x = x
        self._coord_y = y
            
        #print('_get_coords(): {}, {}, {}'.format(self.PRESSED, self._coord_x, self._coord_y))
        
        return self.PRESSED, self._coord_x, self._coord_y

    def get_point(self, n):
        _state = 0
        _x = -1
        _y = -1
        _id = -1
        _pressure = 0
        _rotation = 0
        
        _fingernum = (self._rx_buf[MODE_NORMAL_5_REG & 0xFF] & 0x0F)
        
        if n == 0:
            _state = self._rx_buf[MODE_NORMAL_0_REG & 0xFF] & 0xF;
            _x = COMBINE_H8L4_H(self._rx_buf, MODE_NORMAL_1_REG, MODE_NORMAL_3_REG);
            _y = COMBINE_H8L4_L(self._rx_buf, MODE_NORMAL_2_REG, MODE_NORMAL_3_REG);
            _pressure = self._rx_buf[MODE_NORMAL_4_REG & 0xF];
            
        elif n == 1:
            _state = self._rx_buf[MODE_NORMAL_7_REG & 0xFF] & 0xF;
            _x = COMBINE_H8L4_H(self._rx_buf, MODE_NORMAL_8_REG, MODE_NORMAL_10_REG);
            _y = COMBINE_H8L4_L(self._rx_buf, MODE_NORMAL_9_REG, MODE_NORMAL_10_REG);
            _pressure = self._rx_buf[MODE_NORMAL_11_REG & 0xF];

        elif n == 2:
            _state = rx_buf[MODE_NORMAL_12_REG & 0xFF] & 0xF;
            _x = COMBINE_H8L4_H(self._rx_buf, MODE_NORMAL_13_REG, MODE_NORMAL_15_REG);
            _y = COMBINE_H8L4_L(self._rx_buf, MODE_NORMAL_14_REG, MODE_NORMAL_15_REG);
            _pressure = self._rx_buf[MODE_NORMAL_16_REG & 0xF];
            
        elif n == 3:
            _state = rx_buf[MODE_NORMAL_17_REG & 0xFF] & 0xF;
            _x = COMBINE_H8L4_H(self._rx_buf, MODE_NORMAL_18_REG, MODE_NORMAL_20_REG);
            _y = COMBINE_H8L4_L(self._rx_buf, MODE_NORMAL_19_REG, MODE_NORMAL_20_REG);
            _pressure = self._rx_buf[MODE_NORMAL_21_REG & 0xF];
            
        elif n == 4:
            _state = rx_buf[MODE_NORMAL_22_REG & 0xFF] & 0xF;
            _x = COMBINE_H8L4_H(self._rx_buf, MODE_NORMAL_23_REG, MODE_NORMAL_25_REG);
            _y = COMBINE_H8L4_L(self._rx_buf, MODE_NORMAL_24_REG, MODE_NORMAL_25_REG);
            _pressure = self._rx_buf[MODE_NORMAL_26_REG & 0xF];     
        
        _id = n

        if self.startup_rotation == pointer_framework.lv.DISPLAY_ROTATION._0:
            pass
            
        elif self.startup_rotation == pointer_framework.lv.DISPLAY_ROTATION._90:
            tmp = _x
            _x = _y
            _y = tmp
        
        return _pressure, _x, _y
