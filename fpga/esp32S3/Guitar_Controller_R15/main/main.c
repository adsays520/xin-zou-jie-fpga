#include "esp_err.h"
#include "esp_log.h"
#include "cy8cmbr3116.h"
#include "fpga_link.h"
#include "hall_adc.h"
#include "led_indicator.h"
#include "ble_control.h"
#include "host_usb.h"
#include "touch_serial.h"
#include "touch_scan_report.h"
#include <string.h>

static bool app_command(const char *line)
{
    if (strcmp(line, "TOUCH,STATUS") == 0) {
        touch_serial_report_scan();
        return true;
    }
    if (strcmp(line, "I2C,STATUS") == 0) {
        cy8cmbr3116_report();
        touch_serial_write("OK,I2C,STATUS\r\n");
        return true;
    }
    return ble_control_host_command(line) || led_indicator_command(line) || hall_adc_host_command(line) || fpga_link_host_command(line);
}

void app_main(void)
{
    ESP_LOGI("MAIN", "R15-HALL-v3.4.26-BLE; touch guard v3.3; Hall starts disarmed; H1 strum 6..1; H2..H7 single strings 6..1; fair offline probe slots; I2C=200kHz touch poll=2ms; LED GPIO3=13 GPIO7=14 default CYBER DEMO");
    touch_serial_set_command_handler(app_command);
    ESP_ERROR_CHECK(touch_serial_start());
    esp_err_t err = fpga_link_start();
    if (err != ESP_OK) {
        ESP_LOGE("MAIN", "SPI startup failed: %s; UART/touch remain available", esp_err_to_name(err));
    }
    err = hall_adc_start();
    if (err != ESP_OK) ESP_LOGE("MAIN", "Hall startup failed: %s", esp_err_to_name(err));
    err = led_indicator_start();
    if (err != ESP_OK) ESP_LOGE("MAIN", "LED startup failed: %s; audio control continues", esp_err_to_name(err));
    err = ble_control_start(app_command);
    if (err != ESP_OK) ESP_LOGE("MAIN", "BLE startup failed: %s", esp_err_to_name(err));
    err = host_usb_start(app_command);
    if (err != ESP_OK) ESP_LOGE("MAIN", "USB control startup failed: %s", esp_err_to_name(err));
}
