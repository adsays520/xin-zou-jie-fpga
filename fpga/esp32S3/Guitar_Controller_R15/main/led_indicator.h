#pragma once
#include <stdbool.h>
#include "esp_err.h"
esp_err_t led_indicator_start(void);
bool led_indicator_command(const char *line);
void led_indicator_pick(unsigned string_number);
