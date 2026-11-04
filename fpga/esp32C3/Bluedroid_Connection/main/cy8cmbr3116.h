#pragma once

#include <stdint.h>
#include "esp_err.h"

#define CY8_DEVICE_COUNT 8U
#define CY8_CHANNEL_COUNT 16U

/* Normalized prefixes 0..7 correspond to addresses 0x37..0x3E. */
uint8_t cy8cmbr3116_address(uint8_t chip);

/* Initializes the shared bus; deliberately never resets or writes to a chip. */
esp_err_t cy8cmbr3116_init(void);

/* Read-only verification and 16-channel touch state. */
esp_err_t cy8cmbr3116_verify(uint8_t chip, uint16_t *sensor_enable);
esp_err_t cy8cmbr3116_read_buttons(uint8_t chip, uint16_t *button_state);
esp_err_t cy8cmbr3116_read_difference_counts(uint8_t chip, uint16_t counts[CY8_CHANNEL_COUNT]);
