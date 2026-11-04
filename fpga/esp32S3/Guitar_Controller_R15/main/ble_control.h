#pragma once
#include "esp_err.h"
#include "touch_serial.h"
esp_err_t ble_control_start(touch_serial_command_handler_t handler);
bool ble_control_host_command(const char *line);

void ble_control_log(const char *line);

void ble_control_event(const char *line);
