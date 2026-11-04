#pragma once
#include "esp_err.h"
#include "touch_serial.h"

esp_err_t host_usb_start(touch_serial_command_handler_t handler);
