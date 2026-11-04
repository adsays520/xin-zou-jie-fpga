#include "esp_err.h"
#include "esp_log.h"
#include "touch_serial.h"

void app_main(void)
{
    esp_err_t err = touch_serial_start();
    if (err != ESP_OK) {
        ESP_LOGE("MAIN", "Touch UART startup failed: %s", esp_err_to_name(err));
    }
}
