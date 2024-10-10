#define MICROPY_HW_BOARD_NAME               "T-DISPLAYS3"
#define MICROPY_HW_MCU_NAME                 "ESP32S3"
#define MICROPY_PY_NETWORK_HOSTNAME_DEFAULT "mpy-ttgo-t-displays3"
#define MICROPY_HW_SDMMC_SLOT_CONFIG() { \
    .clk = GPIO_NUM_12, \
    .cmd = GPIO_NUM_11, \
    .d0 = GPIO_NUM_13, \
    .d1 = GPIO_NUM_NC, \
    .d2 = GPIO_NUM_NC, \
    .d3 = GPIO_NUM_NC, \
    .d4 = GPIO_NUM_NC, \
    .d5 = GPIO_NUM_NC, \
    .d6 = GPIO_NUM_NC, \
    .d7 = GPIO_NUM_NC, \
    .cd = GPIO_NUM_NC, \
    .wp = GPIO_NUM_NC, \
    .width   = 1, \
    .flags = 0, \
}