#pragma once

#include <stdbool.h>
#include <stdint.h>
#include "esp_err.h"

#ifdef __cplusplus
extern "C" {
#endif

/** Start UART and the CY8CMBR3116 polling task. */
esp_err_t touch_serial_start(void);

/* One coherent, read-only snapshot. Arrays must hold eight chips. */
void touch_serial_snapshot(uint16_t buttons[8], uint8_t *online_mask);
/* Optional application commands, set before touch_serial_start(). */
typedef bool (*touch_serial_command_handler_t)(const char *line);
void touch_serial_set_command_handler(touch_serial_command_handler_t handler);
void touch_serial_write(const char *line);

#ifdef __cplusplus
}
#endif
