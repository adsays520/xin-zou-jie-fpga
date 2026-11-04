#pragma once
#include <stdbool.h>
#include "esp_err.h"
esp_err_t hall_adc_start(void);
bool hall_adc_host_command(const char *line);
