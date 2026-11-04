#include "touch_output.h"

#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include "driver/uart.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/task.h"
#include "touch_serial.h"
#include "touch_layout.h"

#define TOUCH_OUTPUT_DEPTH 64
#define TOUCH_OUTPUT_BYTES 512

typedef struct {
    const char *tag;
    int64_t time_us;
    esp_log_level_t level;
    bool uart;
    char text[TOUCH_OUTPUT_BYTES];
} touch_output_event_t;

static QueueHandle_t s_output_queue;
static portMUX_TYPE s_output_lock = portMUX_INITIALIZER_UNLOCKED;
static uint32_t s_dropped_uart;
static uint32_t s_dropped_logs;
static bool s_resync_needed;

static void queue_output(touch_output_event_t *event)
{
    if (s_output_queue != NULL && xQueueSend(s_output_queue, event, 0) == pdTRUE) return;
    portENTER_CRITICAL(&s_output_lock);
    if (event->uart) {
        ++s_dropped_uart;
        s_resync_needed = true;
    } else {
        ++s_dropped_logs;
    }
    portEXIT_CRITICAL(&s_output_lock);
}

void touch_output_uart(const char *message)
{
    touch_output_event_t event = {.uart = true};
    if (strlen(message) >= sizeof(event.text)) {
        portENTER_CRITICAL(&s_output_lock);
        ++s_dropped_uart;
        s_resync_needed = true;
        portEXIT_CRITICAL(&s_output_lock);
        return;
    }
    memcpy(event.text, message, strlen(message) + 1);
    queue_output(&event);
}

void touch_output_log(esp_log_level_t level, const char *tag, const char *format, ...)
{
    touch_output_event_t event = {.tag = tag, .time_us = esp_timer_get_time(), .level = level};
    va_list arguments;
    va_start(arguments, format);
    int written = vsnprintf(event.text, sizeof(event.text), format, arguments);
    va_end(arguments);
    if (written < 0 || (size_t)written >= sizeof(event.text)) {
        portENTER_CRITICAL(&s_output_lock);
        ++s_dropped_logs;
        portEXIT_CRITICAL(&s_output_lock);
        return;
    }
    queue_output(&event);
}

static void output_snapshot(void)
{
    uint16_t buttons[8];
    uint8_t online_mask;
    char keys[TOUCH_LAYOUT_STATE_HEX_DIGITS + 1U];
    char message[TOUCH_LAYOUT_STATE_HEX_DIGITS + 32U];
    touch_serial_snapshot(buttons, &online_mask);
    touch_layout_format_state(buttons, keys);
    snprintf(message, sizeof(message), "STATE,0x%s,ONLINE,0x%02X\r\n", keys, online_mask);
    uart_write_bytes(UART_NUM_0, message, strlen(message));
}

static void output_task(void *argument)
{
    (void)argument;
    touch_output_event_t event;
    uint32_t reported_uart = 0;
    uint32_t reported_logs = 0;
    int64_t next_report_us = 0;
    for (;;) {
        if (xQueueReceive(s_output_queue, &event, pdMS_TO_TICKS(20)) == pdTRUE) {
            if (event.uart) {
                uart_write_bytes(UART_NUM_0, event.text, strlen(event.text));
            } else if (event.level == ESP_LOG_ERROR) {
                ESP_LOGE(event.tag, "%s event_ms=%lld", event.text, (long long)(event.time_us / 1000));
            } else if (event.level == ESP_LOG_WARN) {
                ESP_LOGW(event.tag, "%s event_ms=%lld", event.text, (long long)(event.time_us / 1000));
            } else {
                ESP_LOGI(event.tag, "%s event_ms=%lld", event.text, (long long)(event.time_us / 1000));
            }
        }
        if (uxQueueMessagesWaiting(s_output_queue) != 0) continue;
        portENTER_CRITICAL(&s_output_lock);
        bool resync = s_resync_needed;
        s_resync_needed = false;
        uint32_t dropped_uart = s_dropped_uart;
        uint32_t dropped_logs = s_dropped_logs;
        portEXIT_CRITICAL(&s_output_lock);
        if (resync) output_snapshot();
        int64_t now_us = esp_timer_get_time();
        if (now_us >= next_report_us &&
            (dropped_uart != reported_uart || dropped_logs != reported_logs)) {
            ESP_LOGW("TOUCH_OUTPUT", "QUEUE_OVERFLOW uart=%lu logs=%lu; STATE resync after UART loss",
                     (unsigned long)dropped_uart, (unsigned long)dropped_logs);
            reported_uart = dropped_uart;
            reported_logs = dropped_logs;
            next_report_us = now_us + 1000000;
        }
    }
}

esp_err_t touch_output_start(void)
{
    if (s_output_queue != NULL) return ESP_ERR_INVALID_STATE;
    s_output_queue = xQueueCreate(TOUCH_OUTPUT_DEPTH, sizeof(touch_output_event_t));
    if (s_output_queue == NULL) return ESP_ERR_NO_MEM;
    if (xTaskCreate(output_task, "touch_output", 4096, NULL, 3, NULL) != pdPASS) {
        vQueueDelete(s_output_queue);
        s_output_queue = NULL;
        return ESP_ERR_NO_MEM;
    }
    return ESP_OK;
}
