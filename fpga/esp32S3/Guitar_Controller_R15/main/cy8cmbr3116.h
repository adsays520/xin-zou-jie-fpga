#pragma once

#include <stdbool.h>
#include <stdint.h>
#include "esp_err.h"

#define CY8_DEVICE_COUNT 8U
#define CY8_CHANNEL_COUNT 16U
#define CY8_ACTIVE_MASK 0xFFU

uint8_t cy8cmbr3116_address(uint8_t chip);
esp_err_t cy8cmbr3116_init(void);
bool cy8cmbr3116_bus_ready(void);
esp_err_t cy8cmbr3116_recover_bus(void);
esp_err_t cy8cmbr3116_read_device_id(uint8_t chip);
esp_err_t cy8cmbr3116_read_sensor_enable(uint8_t chip, uint16_t *sensor_enable);
esp_err_t cy8cmbr3116_verify(uint8_t chip, uint16_t *sensor_enable);
esp_err_t cy8cmbr3116_read_buttons(uint8_t chip, uint16_t *button_state);
esp_err_t cy8cmbr3116_read_difference_counts(uint8_t chip,
                                          uint16_t counts[CY8_CHANNEL_COUNT]);
esp_err_t cy8cmbr3116_read_difference_count(uint8_t chip, uint8_t channel, uint16_t *count);
void cy8cmbr3116_report(void);
