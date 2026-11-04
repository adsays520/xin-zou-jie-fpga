#pragma once

/* Cached scanner diagnostics only: no I2C access, reset, or configuration write. */
void touch_serial_report_scan(void);
