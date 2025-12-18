#!/bin/bash
sudo apt-get install git wget flex bison gperf python3 python3-pip python3-venv cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0 pkg-config
cd ext_mod
if [ -d usqlite ]; then
  rm -rf usqlite
fi
git clone https://github.com/spatialdude/usqlite.git
cd usqlite
sed -i 's/\^esp32/\^esp32*/g' micropython.cmake
sed -i '/mtext-section-literals/a \\t\t-DSQLITE_DEBUG' micropython.cmake
cd ..

if [ -d micropython-ulab ]; then
  rm -rf micropython-ulab
fi

git clone https://github.com/v923z/micropython-ulab.git
cd ..

#cp -R font/* lib/lvgl/src/font
#yes | cp -R boards/T_DISPLAYS3 lib/micropython/ports/esp32/boards 

rm -rf lib/micropython/ports/esp32/build-T_HMI
python3 make.py esp32 clean BOARD=T_HMI DISPLAY=st7789 INDEV=xpt2046 FROZEN_MANIFEST=$(pwd)/boards/T_HMI/manifest.py --flash-size=16 --dual-core-threads --enable-cdc-repl=y