from micropython import const
from machine import Pin

LCD_WIDTH = const(240)
LCD_HEIGHT = const(320)

PWR_EN_PIN = const(10)
PWR_ON_PIN = const(14)
BAT_ADC_PIN = const(5)
BUTTON1_PIN = const(0)
BUTTON2_PIN = const(21)

# lcd
LCD_DATA0_PIN = const(48)
LCD_DATA1_PIN = const(47)
LCD_DATA2_PIN = const(39)
LCD_DATA3_PIN = const(40)
LCD_DATA4_PIN = const(41)
LCD_DATA5_PIN = const(42)
LCD_DATA6_PIN = const(45)
LCD_DATA7_PIN = const(46)
LCD_PCLK_PIN = const(8)
LCD_CS_PIN = const(6)
LCD_DC_PIN = const(7)
LCD_BK_LIGHT_PIN  = const(38)

## touch screen
TP_SCLK_PIN = const(1)
TP_MISO_PIN = const(4)
TP_MOSI_PIN = const(3)
TP_CS_PIN = const(2)
TP_IRQ_PIN = const(9)

## sd card
SD_MISO_PIN = const(13)
SD_MOSI_PIN = const(11)
SD_SCLK_PIN = const(12)

SDIO_DATA0_PIN = const(13)
SDIO_CMD_PIN = const(11)
SDIO_SCLK_PIN = const(12)

pwr = Pin(PWR_ON_PIN, Pin.OUT)
en = Pin(PWR_EN_PIN, Pin.OUT)
bl = Pin(LCD_BK_LIGHT_PIN, Pin.OUT)

def power_on():
    pwr.on()

def power_off():
    pwr.off()

def power_en_on():
    en.on()

def power_en_off():
    en.off()

def led_bl_on():
    bl.on()

def led_bl_off():
    bl.off()
