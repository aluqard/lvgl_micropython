#!/bin/bash
sudo apt-get install git wget flex bison gperf python3 python3-pip python3-venv cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0 pkg-config
cd ext_mod
if [ ! -d "$usqlite" ]; then
  git clone https://github.com/spatialdude/usqlite.git
  cd usqlite
  sed -i 's/\^esp32/\^esp32*/g' micropython.cmake
  sed -i '/mtext-section-literals/a \\t\t-DSQLITE_DEBUG' micropython.cmake
  cd ..
fi
cd ..
yes | cp -R boards/UM_FEATHERS3 lib/micropython/ports/esp32/boards 
python3 make.py esp32 clean BOARD=UM_FEATHERS3 BOARD_VARIANT=SPIRAM_OCT DISPLAY=hx8357b INDEV=ft5x36 FROZEN_MANIFEST=/home/aluqard/lvgl_micropython_aluqard/lib/micropython/ports/esp32/boards/UM_FEATHERS3/manifest.py --usb-otg --dual-core-threads