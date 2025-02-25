#!/bin/bash
sudo apt install git wget flex bison gperf python3 python3-pip python3-venv cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0 pkg-config libxext-dev libxkbcommon-dev libegl1-mesa-dev libwayland-dev -y
cd ext_mod
if [ -d usqlite ]; then
  rm -rf usqlite
fi
git clone https://github.com/spatialdude/usqlite.git
cd usqlite
sed -i 's/\^esp32/\^esp32*/g' micropython.cmake
sed -i '/mtext-section-literals/a \\t\t-DSQLITE_DEBUG' micropython.cmake
cd ..

if [ ! -d micropython-ulab ]; then
  rm -rf micropython-ulab
fi

git clone https://github.com/v923z/micropython-ulab.git
cd ..

python3 make.py unix clean DISPLAY=sdl_display INDEV=sdl_pointer --heap-size=128000000

cd build
if [ -f lvgl_micropy_unix ]; then
  sudo chmod +x lvgl_micropy_unix
fi