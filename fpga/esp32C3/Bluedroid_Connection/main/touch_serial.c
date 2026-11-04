#include "touch_serial.h"

#include <stdbool.h>
#include <stdio.h>
#include <string.h>

#include "cy8cmbr3116.h"
#include "touch_layout.h"
#include "touch_board.h"
#include "driver/uart.h"
#include "driver/uart_vfs.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#define HOST_UART                 UART_NUM_0
#define HOST_UART_TX_GPIO         TOUCH_UART_TX_GPIO
#define HOST_UART_RX_GPIO         TOUCH_UART_RX_GPIO
#define HOST_UART_BAUD_RATE       115200
#define HOST_UART_RX_BUFFER_SIZE  256
#if CONFIG_IDF_TARGET_ESP32S3
#define TOUCH_POLL_INTERVAL_MS    5
#else
#define TOUCH_POLL_INTERVAL_MS    20
#endif
#define CY8_RETRY_INTERVAL_MS     2000
#define STATE_STREAM_INTERVAL_MS  200

static const char *TAG = "TOUCH_SERIAL";
static portMUX_TYPE s_state_lock = portMUX_INITIALIZER_UNLOCKED;
static uint16_t s_button_state[CY8_DEVICE_COUNT];
static uint16_t s_sensor_enable[CY8_DEVICE_COUNT];
static bool s_online[CY8_DEVICE_COUNT];
static volatile bool s_stream_enabled;
static volatile bool s_diag_requested;
static touch_serial_command_handler_t s_command_handler;

_Static_assert(CY8_DEVICE_COUNT == TOUCH_LAYOUT_CHIP_COUNT, "Chip counts must match");
_Static_assert(CY8_DEVICE_COUNT <= 8U, "Online mask must fit uint8_t");

static void host_send(const char *message)
{
    uart_write_bytes(HOST_UART, message, strlen(message));
}

void touch_serial_write(const char *line)
{
    host_send(line);
}

void touch_serial_set_command_handler(touch_serial_command_handler_t handler)
{
    s_command_handler = handler;
}

static void host_send_key(uint8_t key, bool down)
{
    char message[32];
    snprintf(message, sizeof(message), "KEY,%u,%s\r\n", key, down ? "DOWN" : "UP");
    host_send(message);
}

static void host_send_chip(uint8_t chip, bool online, uint16_t sensor_enable)
{
    char message[64];
    if (online) {
        snprintf(message, sizeof(message), "CHIP,%u,0x%02X,ONLINE,SENSOR_EN,0x%04X\r\n",
                 chip, cy8cmbr3116_address(chip), sensor_enable);
    } else {
        snprintf(message, sizeof(message), "CHIP,%u,0x%02X,OFFLINE\r\n",
                 chip, cy8cmbr3116_address(chip));
    }
    host_send(message);
}

void touch_serial_snapshot(uint16_t buttons[8], uint8_t *online_mask)
{
    uint8_t mask = 0;
    portENTER_CRITICAL(&s_state_lock);
    for (uint8_t chip = 0; chip < CY8_DEVICE_COUNT; ++chip) {
        buttons[chip] = s_button_state[chip];
        if (s_online[chip]) {
            mask |= (uint8_t)1U << chip;
        }
    }
    portEXIT_CRITICAL(&s_state_lock);
    *online_mask = mask;
}

static void host_send_state(void)
{
    uint16_t buttons[CY8_DEVICE_COUNT];
    uint8_t online_mask;
    touch_serial_snapshot(buttons, &online_mask);
    char keys[TOUCH_LAYOUT_STATE_HEX_DIGITS + 1U];
    touch_layout_format_state(buttons, keys);
    char message[TOUCH_LAYOUT_STATE_HEX_DIGITS + 32U];
    snprintf(message, sizeof(message), "STATE,0x%s,ONLINE,0x%02X\r\n",
             keys, online_mask);
    host_send(message);
}

static void host_send_diagnostics(void)
{
    for (uint8_t chip = 0; chip < CY8_DEVICE_COUNT; ++chip) {
        if (!s_online[chip]) {
            host_send_chip(chip, false, 0);
            continue;
        }

        host_send_chip(chip, true, s_sensor_enable[chip]);
        uint16_t counts[CY8_CHANNEL_COUNT];
        esp_err_t err = cy8cmbr3116_read_difference_counts(chip, counts);
        if (err != ESP_OK) {
            char message[64];
            snprintf(message, sizeof(message), "ERROR,DIAG,%u,%s\r\n",
                     chip, esp_err_to_name(err));
            host_send(message);
            continue;
        }
        for (uint8_t channel = 0; channel < CY8_CHANNEL_COUNT; ++channel) {
            char message[48];
            snprintf(message, sizeof(message), "DIFF,%u,%u,%u,%u\r\n",
                     chip, channel, touch_layout_key_for_source(chip, channel),
                     counts[channel]);
            host_send(message);
        }
    }
}

static void touch_task(void *argument)
{
    (void)argument;
    while (cy8cmbr3116_init() != ESP_OK) {
        host_send("ERROR,I2C_INIT\r\n");
        vTaskDelay(pdMS_TO_TICKS(CY8_RETRY_INTERVAL_MS));
    }

    TickType_t next_retry[CY8_DEVICE_COUNT] = {0};
    TickType_t last_stream_report = 0;
    bool all_ready_announced = false;

    for (;;) {
        TickType_t now = xTaskGetTickCount();
        uint8_t online_count = 0;

        for (uint8_t chip = 0; chip < CY8_DEVICE_COUNT; ++chip) {
            if (!s_online[chip]) {
                if (now < next_retry[chip]) {
                    continue;
                }
                uint16_t sensor_enable = 0;
                esp_err_t err = cy8cmbr3116_verify(chip, &sensor_enable);
                if (err != ESP_OK) {
                    char message[64];
                    snprintf(message, sizeof(message), "ERROR,CHIP,%u,0x%02X,%s\r\n",
                             chip, cy8cmbr3116_address(chip), esp_err_to_name(err));
                    host_send(message);
                    next_retry[chip] = now + pdMS_TO_TICKS(CY8_RETRY_INTERVAL_MS);
                    continue;
                }
                portENTER_CRITICAL(&s_state_lock);
                s_online[chip] = true;
                s_sensor_enable[chip] = sensor_enable;
                portEXIT_CRITICAL(&s_state_lock);
                host_send_chip(chip, true, sensor_enable);
                uint16_t disabled = touch_layout_used_channels(chip) & (uint16_t)~sensor_enable;
                if (disabled != 0) {
                    char message[64];
                    snprintf(message, sizeof(message), "WARN,CHIP,%u,DISABLED,0x%04X\r\n",
                             chip, disabled);
                    host_send(message);
                }
            }

            uint16_t current_state = 0;
            esp_err_t err = cy8cmbr3116_read_buttons(chip, &current_state);
            if (err != ESP_OK) {
                portENTER_CRITICAL(&s_state_lock);
                s_online[chip] = false;
                portEXIT_CRITICAL(&s_state_lock);
                host_send_chip(chip, false, 0);
                next_retry[chip] = now + pdMS_TO_TICKS(CY8_RETRY_INTERVAL_MS);
                continue;
            }

            uint16_t previous_state;
            portENTER_CRITICAL(&s_state_lock);
            previous_state = s_button_state[chip];
            s_button_state[chip] = current_state;
            portEXIT_CRITICAL(&s_state_lock);

            uint16_t changed = current_state ^ previous_state;
            for (uint8_t channel = 0; channel < CY8_CHANNEL_COUNT; ++channel) {
                uint16_t mask = (uint16_t)1U << channel;
                if ((changed & mask) != 0) {
                    uint8_t key = touch_layout_key_for_source(chip, channel);
                    if (key != 0) {
                        host_send_key(key, (current_state & mask) != 0);
                    }
                }
            }
            ++online_count;
        }

        if (online_count == CY8_DEVICE_COUNT && !all_ready_announced) {
            char message[40];
            snprintf(message, sizeof(message), "READY,TOUCH,%u,%u\r\n",
                     (unsigned)CY8_DEVICE_COUNT, (unsigned)TOUCH_LAYOUT_KEYS);
            host_send(message);
            all_ready_announced = true;
        } else if (online_count != CY8_DEVICE_COUNT) {
            all_ready_announced = false;
        }

        if (s_diag_requested) {
            s_diag_requested = false;
            host_send_diagnostics();
        }
        if (s_stream_enabled &&
            (now - last_stream_report) >= pdMS_TO_TICKS(STATE_STREAM_INTERVAL_MS)) {
            host_send_state();
            last_stream_report = now;
        }
        vTaskDelay(pdMS_TO_TICKS(TOUCH_POLL_INTERVAL_MS));
    }
}

static void host_rx_task(void *argument)
{
    (void)argument;
    char line[32];
    size_t used = 0;

    for (;;) {
        uint8_t byte;
        if (uart_read_bytes(HOST_UART, &byte, 1, pdMS_TO_TICKS(100)) <= 0) {
            continue;
        }
        if (byte == '\r' || byte == '\n') {
            if (used == 0) {
                continue;
            }
            line[used] = '\0';
            if (strcmp(line, "PING") == 0) {
                host_send("PONG\r\n");
            } else if (strcmp(line, "GET") == 0) {
                host_send_state();
            } else if (strcmp(line, "STREAM,ON") == 0) {
                s_stream_enabled = true;
                host_send("OK,STREAM,ON\r\n");
            } else if (strcmp(line, "STREAM,OFF") == 0) {
                s_stream_enabled = false;
                host_send("OK,STREAM,OFF\r\n");
            } else if (strcmp(line, "DIAG") == 0) {
                s_diag_requested = true;
                host_send("OK,DIAG\r\n");
            } else if (s_command_handler != NULL && s_command_handler(line)) {
                /* Application handler emitted its own reply. */
            } else {
                host_send("ERROR,COMMAND\r\n");
            }
            used = 0;
        } else if (used < sizeof(line) - 1) {
            line[used++] = (char)byte;
        } else {
            used = 0;
            host_send("ERROR,LINE_TOO_LONG\r\n");
        }
    }
}

esp_err_t touch_serial_start(void)
{
    if (!touch_layout_validate()) {
        ESP_LOGE(TAG, "Touch layout or state encoder self-test failed");
        return ESP_ERR_INVALID_STATE;
    }
    ESP_LOGI(TAG, "Layout self-test OK: %u chips, %u keys, %u hex digits",
             (unsigned)CY8_DEVICE_COUNT, (unsigned)TOUCH_LAYOUT_KEYS,
             (unsigned)TOUCH_LAYOUT_STATE_HEX_DIGITS);
    const uart_config_t config = {
        .baud_rate = HOST_UART_BAUD_RATE,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };
    esp_err_t err = uart_driver_install(HOST_UART, HOST_UART_RX_BUFFER_SIZE,
                                        0, 0, NULL, 0);
    if (err != ESP_OK) {
        return err;
    }
    err = uart_param_config(HOST_UART, &config);
    if (err != ESP_OK) {
        return err;
    }
    err = uart_set_pin(HOST_UART, HOST_UART_TX_GPIO, HOST_UART_RX_GPIO,
                       UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
    if (err != ESP_OK) {
        return err;
    }
    uart_vfs_dev_use_driver(HOST_UART);

    if (xTaskCreate(host_rx_task, "host_uart_rx", 3072, NULL, 5, NULL) != pdPASS ||
        xTaskCreate(touch_task, "cy8_touch", 4096, NULL, 6, NULL) != pdPASS) {
        return ESP_ERR_NO_MEM;
    }
    host_send("READY,UART\r\n");
    ESP_LOGI(TAG, "UART0 TX=GPIO%d RX=GPIO%d %d 8N1; I2C SDA=GPIO%d SCL=GPIO%d",
             HOST_UART_TX_GPIO, HOST_UART_RX_GPIO, HOST_UART_BAUD_RATE,
             TOUCH_SDA_GPIO, TOUCH_SCL_GPIO);
    return ESP_OK;
}
