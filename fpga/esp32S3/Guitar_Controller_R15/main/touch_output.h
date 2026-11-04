#pragma once

#include <stdint.h>
#include "esp_err.h"
#include "esp_log.h"

esp_err_t touch_output_start(void);
void touch_output_uart(const char *message);
void touch_output_log(esp_log_level_t level, const char *tag, const char *format, ...)
    __attribute__((format(printf, 3, 4)));

#define TOUCH_LOGE(tag, ...) touch_output_log(ESP_LOG_ERROR, tag, __VA_ARGS__)
#define TOUCH_LOGW(tag, ...) touch_output_log(ESP_LOG_WARN, tag, __VA_ARGS__)
#define TOUCH_LOGI(tag, ...) touch_output_log(ESP_LOG_INFO, tag, __VA_ARGS__)
