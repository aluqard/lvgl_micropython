#!/bin/bash
sudo apt-get install git wget flex bison gperf python3 python3-pip python3-venv cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0 pkg-config
cp -R font/* lib/lvgl/src/font
yes | cp -R boards/T_DISPLAYS3 lib/micropython/ports/esp32/boards 
python3 make.py esp32 clean BOARD=T_DISPLAYS3 BOARD_VARIANT=SPIRAM_OCT DISPLAY=st7789 FROZEN_MANIFEST=/home/aluqard/lvgl_micropython_aluqard/lib/micropython/ports/esp32/boards/T_DISPLAYS3/manifest.py --usb-otg --dual-core-threads
