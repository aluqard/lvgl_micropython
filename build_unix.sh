#!/bin/bash
sudo apt install git wget flex bison gperf python3 python3-pip python3-venv cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0 pkg-config
cd ext_mod
if [ ! -d "$usqlite" ]; then
  echo usqlite does not exist.
  git clone https://github.com/spatialdude/usqlite.git
  cd usqlite
  sed -i 's/\^esp32/\^esp32*/g' micropython.cmake
  sed -i '/mtext-section-literals/a \\t\t-DSQLITE_DEBUG' micropython.cmake
  cd ..
fi
cd ..
python3 make.py unix clean DISPLAY=sdl_display INDEV=sdl_pointer