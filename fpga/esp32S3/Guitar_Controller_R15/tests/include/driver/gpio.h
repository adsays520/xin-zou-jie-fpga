#pragma once
#include "idf_test.h"
#include <stdlib.h>
#include <stdio.h>
#define GPIO_MODE_OUTPUT 1
#define GPIO_MODE_INPUT 2
#define GPIO_PULLDOWN_ENABLE 1
#define GPIO_PULLUP_DISABLE 0
#define GPIO_INTR_DISABLE 0
#define GPIO_DRIVE_CAP_2 2
#define ESP_ERROR_CHECK(result) do { if ((result) != ESP_OK) abort(); } while (0)
typedef struct {
    uint64_t pin_bit_mask;
    int mode;
    int pull_down_en;
    int pull_up_en;
    int intr_type;
} gpio_config_t;
esp_err_t gpio_config(const gpio_config_t *config);
int gpio_set_level(int pin, unsigned level);
int gpio_get_level(int pin);
esp_err_t gpio_reset_pin(int pin);
esp_err_t gpio_set_direction(int pin,int direction);
esp_err_t gpio_set_drive_capability(int pin,int strength);
esp_err_t gpio_dump_io_configuration(FILE *stream,uint64_t mask);
