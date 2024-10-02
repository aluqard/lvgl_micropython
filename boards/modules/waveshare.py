from micropython import const

# LCD
LCD_WIDTH   = const(240)
LCD_HEIGHT  = const(320)
LCD_MISO	= const(46)
LCD_MOSI	= const(45)
LCD_SCLK	= const(40)
LCD_CS	    = const(42)
LCD_DC	    = const(41)
LCD_RST	    = const(39)
LCD_BL	    = const(5)

# Touch Panel
TP_SDA	    = const(1)
TP_SCL	    = const(3)
TP_INT	    = const(4)
TP_RST	    = const(2)

# SD
SD_MISO	    = const(16)
SD_MOSI	    = const(17)
SD_SCLK	    = const(14)
SD_CS	    = const(21)

# QMI8658C
IMU_SCL	    = const(10)
IMU_SDA	    = const(11)
IMU_INT1	= const(13)
IMU_INT2	= const(12)

#RTC
RTC_SCL	    = const(10)
RTC_SDA	    = const(11)
RTC_INT	    = const(9)

#PCM5101APWR
I2S_LRCK    = const(38)
I2S_DIN     = const(47)
I2S_BCK     = const(48)

#ETC
PWR_KEY     = const(6)
BAT_CTRL    = const(7)
BAT_ADC     = const(8)