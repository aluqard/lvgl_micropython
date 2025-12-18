from micropython import const

# LCD
LCD_WIDTH   = const(240)
LCD_HEIGHT  = const(320)
LCD_SCLK    = const(39)
LCD_MOSI    = const(38)
LCD_MISO    = const(40)
LCD_DC      = const(42)
LCD_RST     = const(-1)
LCD_CS      = const(45)
LCD_BL      = const(1)

# Touch Panel
TP_SDA	    = const(48)
TP_SCL	    = const(47)

# SD
SD_MISO	    = const(40)
SD_MOSI	    = const(38)
SD_SCLK	    = const(39)
SD_CS	    = const(41)

# QMI8658C
IMU_SCL	    = const(48)
IMU_SDA	    = const(47)

#RTC
RTC_SCL	    = const(10)
RTC_SDA	    = const(11)
RTC_INT	    = const(9)

#ETC
PWR_KEY     = const(6)
BAT_ADC     = const(5)