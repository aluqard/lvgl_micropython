set(IDF_TARGET esp32s3)

# 8 MB flash, no external PSRAM (512 KB internal SRAM only):
# the spiram_sx / spiram_oct fragments are intentionally omitted so CONFIG_SPIRAM
# stays disabled (enabling PSRAM that isn't present would hang/panic at boot).
set(SDKCONFIG_DEFAULTS
    boards/sdkconfig.base
    boards/sdkconfig.ble
    boards/sdkconfig.240mhz
    boards/ESP32_GENERIC_S3/sdkconfig.board
)
