#pragma once
#include <stdbool.h>
#include <stdint.h>
#include "esp_err.h"
esp_err_t fpga_link_start(void);
bool fpga_link_host_command(const char *line);
/* Safe event adapter: string 1..6, measured velocity 1..127. No event is
 * accepted until the SPI link has a verified acknowledgement. */
bool fpga_link_hall_trigger(unsigned string_number, unsigned velocity);
bool fpga_link_hall_strum(unsigned velocity);
void fpga_link_cancel_strums(void);

/* BLE worker only; blocking SPI packet delivery, never call from GATT callback. */
bool fpga_link_bulk_send(const uint8_t *data, unsigned length);
const char *fpga_link_bulk_error(void);
unsigned fpga_link_reply_flags(void);
