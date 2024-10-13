from micropython import const
from machine import Pin
from i2c import I2C
import waveshare as ws
import time

MODE_DEBUG_INFO_MODE       = const(0xD101)
MODE_DEBUG_INFO_BOOT_TIME  = const(0xD1FC)

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

SYNC_SIGNAL = const(0xAB)
tx_buf_len = const(2)
rx_buf_len = const(27)
regdata_len = const(100)

tx_buf = bytearray(2)
tx_mv = memoryview(tx_buf)
rx_buf = bytearray(rx_buf_len)
rx_mv = memoryview(rx_buf)
regdata = bytearray(regdata_len)
regdata_mv = memoryview(regdata)

def COMBINE_H8L4_H(buf, h, l):
    return (buf[h & 0xFF] << 4 | buf[l & 0xFF] >> 4)

def COMBINE_H8L4_L(buf, h, l):
    return (buf[h & 0xFF] << 4 | buf[l & 0xFF] & 0xF)

def COMBINE_H4L8(buf, h, l):
    return ((buf[h] & 0x0F) << 8 | buf[l])

def get_point(n):
    _state = 0
    _x = -1
    _y = -1
    _id = -1
    _pressure = 0
    _rotation = 0
    
    if n == 0:
        _state = rx_buf[MODE_NORMAL_0_REG & 0xFF] & 0xF;
        _x = COMBINE_H8L4_H(rx_buf, MODE_NORMAL_1_REG, MODE_NORMAL_3_REG);
        _y = COMBINE_H8L4_L(rx_buf, MODE_NORMAL_2_REG, MODE_NORMAL_3_REG);
        _pressure = rx_buf[MODE_NORMAL_4_REG & 0xF];
        
    elif n == 1:
        _state = rx_buf[MODE_NORMAL_7_REG & 0xFF] & 0xF;
        _x = COMBINE_H8L4_H(rx_buf, MODE_NORMAL_8_REG, MODE_NORMAL_10_REG);
        _y = COMBINE_H8L4_L(rx_buf, MODE_NORMAL_9_REG, MODE_NORMAL_10_REG);
        _pressure = rx_buf[MODE_NORMAL_11_REG & 0xF];

    elif n == 2:
        _state = rx_buf[MODE_NORMAL_12_REG & 0xFF] & 0xF;
        _x = COMBINE_H8L4_H(rx_buf, MODE_NORMAL_13_REG, MODE_NORMAL_15_REG);
        _y = COMBINE_H8L4_L(rx_buf, MODE_NORMAL_14_REG, MODE_NORMAL_15_REG);
        _pressure = rx_buf[MODE_NORMAL_16_REG & 0xF];
        
    elif n == 3:
        _state = rx_buf[MODE_NORMAL_17_REG & 0xFF] & 0xF;
        _x = COMBINE_H8L4_H(rx_buf, MODE_NORMAL_18_REG, MODE_NORMAL_20_REG);
        _y = COMBINE_H8L4_L(rx_buf, MODE_NORMAL_19_REG, MODE_NORMAL_20_REG);
        _pressure = rx_buf[MODE_NORMAL_21_REG & 0xF];
        
    elif n == 4:
        _state = rx_buf[MODE_NORMAL_22_REG & 0xFF] & 0xF;
        _x = COMBINE_H8L4_H(rx_buf, MODE_NORMAL_23_REG, MODE_NORMAL_25_REG);
        _y = COMBINE_H8L4_L(rx_buf, MODE_NORMAL_24_REG, MODE_NORMAL_25_REG);
        _pressure = rx_buf[MODE_NORMAL_26_REG & 0xF];     
    
    _id = n

    if _rotation == 0:
        pass
        
    elif _rotation == 1:
        tmp = _x
        _x = _y
        _y = tmp
    
    return _pressure, _x, _y

def touch_cb(pin):

    read(device, MODE_NORMAL_5_REG)
    if rx_buf[0] & 0x0F == 0x00:
        write(device, MODE_NORMAL_5_REG, [0])
        print('no touched')
   
    else:
        read(device, MODE_NORMAL_0_REG)
        write(device, MODE_NORMAL_5_REG, [0])
        
        res = (rx_buf[MODE_NORMAL_5_REG & 0xFF] & 0x0F)
        
        print('touched {}'.format(get_point(0)))
        
def read(device, reg):
    tx_buf[0] = (reg >> 8) & 0xFF
    tx_buf[1] = reg & 0xFF
    
    for i in range(rx_buf_len):
        rx_buf[i] = 0x00

    device.write_readinto(tx_mv[:tx_buf_len], rx_mv[:rx_buf_len])
    

def write(device, reg, data=None):
    tx_buf[0] = (reg >> 8) & 0xFF
    tx_buf[1] = reg & 0xFF

    device.write(tx_mv[:tx_buf_len])
    
    if data is not None:
        device.write(bytearray(data))

TP_FREQ = const(400_000)
TP_ADDR = 0x1A

tp_rst = Pin(ws.TP_RST, Pin.OUT)
tp_int = Pin(ws.TP_INT, Pin.IN, Pin.PULL_UP)

tp_int.irq(trigger=Pin.IRQ_RISING, handler=touch_cb)

tp_rst.on()
time.sleep_ms(50)
tp_rst.off()
time.sleep_ms(5)
tp_rst.on()
time.sleep_ms(50)

i2c_bus = I2C.Bus(host=1, scl=3, sda=1, freq=TP_FREQ)
device = I2C.Device(i2c_bus, TP_ADDR, 8)

write(device, MODE_DEBUG_INFO_MODE)
read(device, MODE_DEBUG_INFO_BOOT_TIME)

print('Touchpad id: {},{},{},{}'.format(rx_buf[0], rx_buf[1], rx_buf[2], rx_buf[3]))

'''
while True:
    read(device, MODE_NORMAL_5_REG)
    if rx_buf[0] & 0x0F == 0x00:
        regdata[0] = 0
        write(device, MODE_NORMAL_5_REG, 1)
        print('no touch data1 {}'.format(rx_buf[0]))
   
    else:
        
#        touch_cnt = rx_buf[0] & 0x0F
#        if  touch_cnt > 5 or touch_cnt == 0:
#            regdata[0] = 0
#            write(device, MODE_NORMAL_5_REG, 1)
#            print('no touch data2 {}'.format(rx_buf[0]))
#            continue
        
        read(device, MODE_NORMAL_0_REG)
        regdata[0] = 0
        write(device, MODE_NORMAL_5_REG, 1)
        
        res = (rx_buf[MODE_NORMAL_5_REG & 0xFF] & 0x0F)
        print(res)
    
    time.sleep_ms(5)
'''