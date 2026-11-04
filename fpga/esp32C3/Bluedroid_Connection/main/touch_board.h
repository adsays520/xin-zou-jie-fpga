#pragma once
#include "sdkconfig.h"

#if CONFIG_IDF_TARGET_ESP32S3
/* S3 N16R8: keep Octal PSRAM pins 35..37 and native USB 19/20 free. */
#define TOUCH_SDA_GPIO 5
#define TOUCH_SCL_GPIO 4
#define TOUCH_UART_TX_GPIO 43
#define TOUCH_UART_RX_GPIO 44
#else
/* Preserve the existing C3 board wiring. */
#define TOUCH_SDA_GPIO 4
#define TOUCH_SCL_GPIO 5
#define TOUCH_UART_TX_GPIO 21
#define TOUCH_UART_RX_GPIO 20
#endif
