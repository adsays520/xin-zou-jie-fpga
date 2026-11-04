#ifndef TOUCH_IDF_TEST_H
#define TOUCH_IDF_TEST_H
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef int esp_err_t;
typedef int esp_log_level_t;
typedef uint32_t TickType_t;
typedef int portMUX_TYPE;
typedef struct {
    int baud_rate;
    int data_bits;
    int parity;
    int stop_bits;
    int flow_ctrl;
    int source_clk;
} uart_config_t;

#define ESP_OK 0
#define ESP_FAIL (-1)
#define ESP_ERR_NO_MEM 0x101
#define ESP_ERR_INVALID_ARG 0x102
#define ESP_ERR_INVALID_STATE 0x103
#define ESP_ERR_INVALID_RESPONSE 0x108
#define ESP_LOG_ERROR 1
#define ESP_LOG_WARN 2
#define ESP_LOG_INFO 3
#define ESP_LOGE(...) ((void)0)
#define ESP_LOGI(...) ((void)0)
#define ESP_LOGW(...) ((void)0)
#define UART_NUM_0 0
#define UART_DATA_8_BITS 8
#define UART_PARITY_DISABLE 0
#define UART_STOP_BITS_1 1
#define UART_HW_FLOWCTRL_DISABLE 0
#define UART_SCLK_DEFAULT 0
#define UART_PIN_NO_CHANGE (-1)
#define portMUX_INITIALIZER_UNLOCKED 0
#define portENTER_CRITICAL(lock) ((void)(lock))
#define portEXIT_CRITICAL(lock) ((void)(lock))
#define pdMS_TO_TICKS(milliseconds) ((TickType_t)(milliseconds))
#define pdPASS 1
#ifdef __TINYC__
#define TOUCH_ASSERT_NAME_INNER(line) touch_static_assert_##line
#define TOUCH_ASSERT_NAME(line) TOUCH_ASSERT_NAME_INNER(line)
#define _Static_assert(condition, message) typedef char TOUCH_ASSERT_NAME(__LINE__)[(condition) ? 1 : -1]
#endif

const char *esp_err_to_name(esp_err_t error);
int64_t esp_timer_get_time(void);
TickType_t xTaskGetTickCount(void);
void vTaskDelay(TickType_t ticks);
int xTaskCreate(void (*task)(void *), const char *name, unsigned stack, void *argument,
                unsigned priority, void *handle);
int uart_write_bytes(int port, const void *data, size_t length);
int uart_read_bytes(int port, void *data, uint32_t length, TickType_t wait);
esp_err_t uart_driver_install(int port, int receive_size, int transmit_size,
                              int queue_size, void *queue, int flags);
esp_err_t uart_param_config(int port, const uart_config_t *config);
esp_err_t uart_set_pin(int port, int transmit, int receive, int rts, int cts);
void uart_vfs_dev_use_driver(int port);
#endif
