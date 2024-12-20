#!/bin/bash
sudo apt-get install git wget flex bison gperf python3 python3-pip python3-venv cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0 pkg-config
cp -R font/* lib/lvgl/src/font
python3 make.py esp32 clean BOARD=ARDUINO_NANO_ESP32 BOARD_VARIANT=SPIRAM_OCT DISPLAY=st7796 INDEV=ft6x36 --usb-otg --dual-core-threads
