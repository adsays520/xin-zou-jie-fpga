#include "host_usb.h"
#include "control_line.h"
#include "touch_output.h"
#include "sdkconfig.h"
#include "driver/usb_serial_jtag.h"
#include "driver/usb_serial_jtag_vfs.h"
#include <errno.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static int s_usb = -1;
static touch_serial_command_handler_t s_handler;

static void usb_dispatch_line(const char *line)
{
    if (strcmp(line, "PING") == 0) {
        touch_serial_write("PONG,R15-HALL-v3.4.27-BLE\r\n");
    } else if (strncmp(line, "BLE,", 4) == 0 || strncmp(line, "LED,", 4) == 0 || strncmp(line, "HALL,", 5) == 0 || strncmp(line, "FPGA,", 5) == 0 ||
               strcmp(line, "TOUCH,STATUS") == 0 || strcmp(line, "I2C,STATUS") == 0) {
        if (!s_handler(line)) touch_serial_write("ERROR,COMMAND\r\n");
    } else {
        touch_serial_write("ERROR,USB_COMMAND\r\n");
    }
}

static void usb_task(void *argument)
{
    (void)argument;
    control_line_t line = {0};
    uint8_t bytes[128];
    for (;;) {
        int count = read(s_usb, bytes, sizeof(bytes));
        for (int index = 0; index < count; ++index) {
            if (!control_line_feed(&line, bytes[index])) continue;
            usb_dispatch_line(line.text);
        }
        vTaskDelay(pdMS_TO_TICKS(5));
    }
}

esp_err_t host_usb_start(touch_serial_command_handler_t handler)
{
    if (handler == NULL || s_usb >= 0) return ESP_ERR_INVALID_STATE;
    if (!usb_serial_jtag_is_driver_installed()) {
        usb_serial_jtag_driver_config_t config = {.tx_buffer_size = 4096, .rx_buffer_size = 1024};
        esp_err_t error = usb_serial_jtag_driver_install(&config);
        if (error != ESP_OK) {
            TOUCH_LOGE("HOST_USB", "USB RX driver install failed: %s", esp_err_to_name(error));
            return error;
        }
    }
    usb_serial_jtag_vfs_use_driver();
#if CONFIG_ESP_CONSOLE_SECONDARY_USB_SERIAL_JTAG
    const char *path = "/dev/secondary";
#else
    const char *path = "/dev/usbserjtag";
#endif
    s_usb = open(path, O_RDONLY | O_NONBLOCK);
    if (s_usb < 0) {
        TOUCH_LOGE("HOST_USB", "Cannot open USB control path=%s errno=%d", path, errno);
        return ESP_FAIL;
    }
    s_handler = handler;
    if (xTaskCreate(usb_task, "host_usb_rx", 4096, NULL, 4, NULL) != pdPASS) {
        close(s_usb);
        s_usb = -1;
        return ESP_ERR_NO_MEM;
    }
    TOUCH_LOGI("HOST_USB", "R15-HALL-v3.4.27-BLE native USB RX/TX driver enabled path=%s; Hall starts disarmed", path);
    return ESP_OK;
}
