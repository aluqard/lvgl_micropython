#!/bin/bash
sudo apt-get install git wget flex bison gperf python3 python3-pip python3-venv cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0 pkg-config
cd ext_mod
if [ -d usqlite ]; then
  cd usqlite
  sed -i 's/\^esp32/\^esp32*/g' micropython.cmake
  sed -i '/mtext-section-literals/a \\t\t-DSQLITE_DEBUG' micropython.cmake
  cd ..
fi
cd ..
cp -R font/* lib/lvgl/src/font
yes | cp -R boards/ESP32_WAVESHARE lib/micropython/ports/esp32/boards 
python3 make.py esp32 clean BOARD=ESP32_GENERIC_S3 BOARD_VARIANT=SPIRAM_OCT DISPLAY=st7796 INDEV=ft6x36 --usb-otg --dual-core-threads
