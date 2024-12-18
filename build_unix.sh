#!/bin/bash
sudo apt install git wget flex bison gperf python3 python3-pip python3-venv cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0 pkg-config libxext-dev libxkbcommon-dev libegl1-mesa-dev libwayland-dev -y
cd ext_mod
if [ -d usqlite ]; then
  echo usqlite does not exist.
  cd usqlite
  sed -i 's/\^esp32/\^esp32*/g' micropython.cmake
  sed -i '/mtext-section-literals/a \\t\t-DSQLITE_DEBUG' micropython.cmake
  cd ..
fi
cd ..
cp -R font/* lib/lvgl/src/font
python3 make.py unix clean DISPLAY=sdl_display INDEV=sdl_pointer
