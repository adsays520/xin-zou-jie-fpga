#include "touch_serial.h"
#include "ble_control.h"
#include "touch_scan_report.h"

#include <stdbool.h>
#include <stdio.h>
#include <string.h>

#include "cy8cmbr3116.h"
#include "touch_filter.h"
#include "touch_recovery.h"
#include "touch_output.h"
#include "note_trace.h"
#include "touch_layout.h"
#include "touch_board.h"
#include "driver/uart.h"
#include "driver/uart_vfs.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#define HOST_UART                 UART_NUM_0
#define HOST_UART_TX_GPIO         TOUCH_UART_TX_GPIO
#define HOST_UART_RX_GPIO         TOUCH_UART_RX_GPIO
#define HOST_UART_BAUD_RATE       115200
#define HOST_UART_RX_BUFFER_SIZE  256
#define HOST_UART_TX_BUFFER_SIZE  4096
#define TOUCH_POLL_INTERVAL_MS    2
#define CY8_INIT_RETRY_MS         2000
#define CY8_PROBE_SLOT_US         5000
#define CY8_PASS_BUDGET_US        5000
#define CY8_BUS_WAIT_US           20000
#define CY8_BUS_RESET_INTERVAL_US 500000
#define STATE_STREAM_INTERVAL_MS  200

typedef struct {
    touch_filter_t filter;
    uint16_t sensor_enable;
    touch_probe_t probe;
    bool stale_released;
    uint16_t last_raw;
    uint32_t samples;
    bool raw_seen;
    uint32_t read_disagreements;
    int64_t next_disagreement_log_us;
    uint32_t button_requests;
    uint32_t verify_requests;
    uint32_t max_request_gap_us;
    int64_t last_request_us;
    uint16_t first_raw;
    uint16_t second_raw;
    uint8_t raw_valid;
} touch_chip_t;

typedef struct {
    uint8_t online_cursor;
    uint8_t probe_cursor;
    int64_t next_probe_slot_us;
    int64_t next_bus_check_us;
    int64_t next_bus_log_us;
    int64_t bus_fault_since_us;
    int64_t next_bus_reset_us;
    TickType_t last_stream_report;
    bool all_ready_announced;
} touch_loop_t;

static const char *TAG = "TOUCH_SERIAL";
static portMUX_TYPE s_state_lock = portMUX_INITIALIZER_UNLOCKED;
static touch_chip_t s_chips[CY8_DEVICE_COUNT];
static volatile bool s_stream_enabled;
static volatile bool s_diag_requested;
static bool s_diag_running;
static uint8_t s_diag_chip;
static uint8_t s_diag_channel;
static touch_serial_command_handler_t s_command_handler;

_Static_assert(CY8_DEVICE_COUNT == TOUCH_LAYOUT_CHIP_COUNT, "Chip counts must match");
_Static_assert(CY8_DEVICE_COUNT <= 8U, "Online mask must fit uint8_t");

static void host_send(const char *message)
{
    if (strncmp(message, "KEY,", 4) == 0) ble_control_event(message);
    touch_output_uart(message);
}

void touch_serial_write(const char *line)
{
    ble_control_log(line);
    host_send(line);
    TOUCH_LOGI("HOST_REPLY", "%s", line);
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

static void host_send_changes(uint8_t chip, uint16_t changed, uint16_t buttons, const char *reason)
{
    for (uint8_t channel = 0; channel < CY8_CHANNEL_COUNT; ++channel) {
        uint16_t mask = (uint16_t)1U << channel;
        if ((changed & mask) == 0) continue;
        uint8_t key = touch_layout_key_for_source(chip, channel);
        if (key != 0) {
            host_send_key(key, (buttons & mask) != 0);
            note_trace_key(key, (buttons & mask) != 0, reason);
        }
    }
}

void touch_serial_snapshot(uint16_t buttons[8], uint8_t *online_mask)
{
    uint8_t mask = 0;
    int64_t now_us = esp_timer_get_time();
    portENTER_CRITICAL(&s_state_lock);
    for (uint8_t chip = 0; chip < CY8_DEVICE_COUNT; ++chip) {
        bool fresh = touch_filter_fresh(&s_chips[chip].filter, now_us);
        buttons[chip] = fresh ? s_chips[chip].filter.buttons : 0;
        if (fresh) mask |= (uint8_t)1U << chip;
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

static void host_diagnostic_step(void)
{
    while (s_diag_chip < CY8_DEVICE_COUNT) {
        uint8_t chip = s_diag_chip;
        if ((CY8_ACTIVE_MASK & (1U << chip)) == 0) {
            ++s_diag_chip;
            continue;
        }
        portENTER_CRITICAL(&s_state_lock);
        bool online = touch_filter_fresh(&s_chips[chip].filter, esp_timer_get_time());
        uint16_t sensor_enable = s_chips[chip].sensor_enable;
        portEXIT_CRITICAL(&s_state_lock);
        if (!online) {
            host_send_chip(chip, false, 0);
            ++s_diag_chip;
            s_diag_channel = 0;
            continue;
        }
        if (s_diag_channel == 0) host_send_chip(chip, true, sensor_enable);
        uint16_t count;
        esp_err_t err = cy8cmbr3116_read_difference_count(chip, s_diag_channel, &count);
        if (err != ESP_OK) {
            char message[64];
            snprintf(message, sizeof(message), "ERROR,DIAG,%u,%s\r\n",
                     chip, esp_err_to_name(err));
            host_send(message);
            ++s_diag_chip;
            s_diag_channel = 0;
            return;
        }
        char message[48];
        snprintf(message, sizeof(message), "DIFF,%u,%u,%u,%u\r\n",
                 chip, s_diag_channel, touch_layout_key_for_source(chip, s_diag_channel), count);
        host_send(message);
        if (++s_diag_channel == CY8_CHANNEL_COUNT) {
            ++s_diag_chip;
            s_diag_channel = 0;
        }
        return;
    }
    s_diag_running = false;
    host_send("OK,DIAG,DONE\r\n");
}

static void disconnect_chip(uint8_t chip, const char *reason, int64_t now_us)
{
    portENTER_CRITICAL(&s_state_lock);
    touch_chip_t *state = &s_chips[chip];
    bool was_online = state->filter.online;
    int64_t age_us = now_us - state->filter.last_good_us;
    int64_t confirmed_age_us = now_us - state->filter.last_confirmed_us;
    unsigned failures = state->filter.failures;
    uint16_t released = touch_filter_disconnect(&state->filter);
    touch_probe_reset(&state->probe, now_us);
    state->stale_released = false;
    portEXIT_CRITICAL(&s_state_lock);
    if (!was_online) return;
    host_send_changes(chip, released, 0, "OFFLINE");
    host_send_chip(chip, false, 0);
    TOUCH_LOGW(TAG, "OFFLINE chip=%u addr=0x%02X reason=%s failures=%u"
             " good_age_ms=%lld confirmed_age_ms=%lld",
             chip, cy8cmbr3116_address(chip), reason, failures,
             (long long)(age_us / 1000), (long long)(confirmed_age_us / 1000));
}

static void expire_stale_chips(void)
{
    for (uint8_t chip = 0; chip < CY8_DEVICE_COUNT; ++chip) {
        int64_t now_us = esp_timer_get_time();
        portENTER_CRITICAL(&s_state_lock);
        touch_chip_t *state = &s_chips[chip];
        bool expired = state->filter.online && !state->stale_released &&
                       !touch_filter_fresh(&state->filter, now_us);
        uint16_t released = 0;
        if (expired) {
            released = touch_filter_release_stale(&state->filter);
            state->stale_released = true;
        }
        portEXIT_CRITICAL(&s_state_lock);
        if (expired) {
            host_send_changes(chip, released, 0, "STALE");
            host_send_chip(chip, false, 0);
            TOUCH_LOGW(TAG, "STALE_RELEASE chip=%u addr=0x%02X fast_poll=1 released=0x%04X; keys released without probe backoff",
                       chip, cy8cmbr3116_address(chip), released);
        }
    }
}

static void accept_buttons(uint8_t chip, uint16_t raw, uint16_t sensor_enable)
{
    int64_t now_us = esp_timer_get_time();
    portENTER_CRITICAL(&s_state_lock);
    touch_chip_t *state = &s_chips[chip];
    bool was_online = state->filter.online && !state->stale_released;
    bool raw_changed = !state->raw_seen || state->last_raw != raw;
    uint16_t previous = state->filter.buttons;
    uint16_t candidate = state->filter.candidate;
    bool candidate_valid = state->filter.candidate_valid;
    unsigned failures = state->filter.failures;
    bool fresh = touch_filter_fresh(&state->filter, now_us);
    state->last_raw = raw;
    state->raw_seen = true;
    uint32_t sample = ++state->samples;
    state->sensor_enable = sensor_enable;
    uint16_t changed = touch_filter_accept(&state->filter, raw & sensor_enable, now_us);
    uint16_t buttons = state->filter.buttons;
    state->probe.failures = 0;
    state->stale_released = false;
    portEXIT_CRITICAL(&s_state_lock);
    if (raw_changed) {
        TOUCH_LOGI("TOUCH_TRACE", "RAW chip=%u raw=0x%04X sensor=0x%04X candidate=0x%04X valid=%u failures=%u fresh=%u sample=%lu",
                   chip, raw, sensor_enable, candidate, (unsigned)candidate_valid,
                   failures, (unsigned)fresh, (unsigned long)sample);
    }
    if (changed != 0) {
        TOUCH_LOGI("TOUCH_TRACE", "EDGE chip=%u raw=0x%04X before=0x%04X after=0x%04X down=0x%04X up=0x%04X sample=%lu",
                   chip, raw, previous, buttons, changed & buttons,
                   changed & (uint16_t)~buttons, (unsigned long)sample);
    }
    if (!was_online) {
        host_send_chip(chip, true, sensor_enable);
        TOUCH_LOGI(TAG, "ONLINE chip=%u addr=0x%02X sensor_en=0x%04X confirm=2",
                 chip, cy8cmbr3116_address(chip), sensor_enable);
        uint16_t disabled = touch_layout_used_channels(chip) & (uint16_t)~sensor_enable;
        if (disabled != 0) {
            char message[64];
            snprintf(message, sizeof(message), "WARN,CHIP,%u,DISABLED,0x%04X\r\n",
                     chip, disabled);
            host_send(message);
        }
    }
    host_send_changes(chip, changed, buttons, "FILTER");
}

static esp_err_t read_guarded_buttons(uint8_t chip, uint16_t *buttons, bool *verified)
{
    *verified = false;
    int64_t started_us = esp_timer_get_time();
    portENTER_CRITICAL(&s_state_lock);
    touch_chip_t *scan = &s_chips[chip];
    if (scan->last_request_us != 0) {
        int64_t gap = started_us - scan->last_request_us;
        uint32_t bounded_gap = gap > UINT32_MAX ? UINT32_MAX : (uint32_t)gap;
        if (bounded_gap > scan->max_request_gap_us) scan->max_request_gap_us = bounded_gap;
    }
    scan->last_request_us = started_us;
    ++scan->button_requests;
    scan->raw_valid = 0;
    portEXIT_CRITICAL(&s_state_lock);
    uint16_t first;
    esp_err_t err = cy8cmbr3116_read_buttons(chip, &first);
    if (err != ESP_OK) return err;
    portENTER_CRITICAL(&s_state_lock);
    uint16_t confirmed = s_chips[chip].filter.buttons;
    uint16_t enabled = s_chips[chip].sensor_enable;
    s_chips[chip].first_raw = first;
    s_chips[chip].raw_valid = 1;
    if ((first & enabled) != confirmed) ++s_chips[chip].verify_requests;
    portEXIT_CRITICAL(&s_state_lock);
    if ((first & enabled) == confirmed) {
        *buttons = first;
        *verified = true;
        return ESP_OK;
    }
    uint16_t second;
    err = cy8cmbr3116_read_buttons(chip, &second);
    if (err != ESP_OK) return err;
    portENTER_CRITICAL(&s_state_lock);
    s_chips[chip].second_raw = second;
    s_chips[chip].raw_valid |= 2;
    portEXIT_CRITICAL(&s_state_lock);
    if ((first & enabled) == (second & enabled)) {
        *buttons = second;
        *verified = true;
        return ESP_OK;
    }
    portENTER_CRITICAL(&s_state_lock);
    s_chips[chip].filter.candidate_valid = false;
    ++s_chips[chip].read_disagreements;
    portEXIT_CRITICAL(&s_state_lock);
    touch_chip_t *state = &s_chips[chip];
    int64_t now_us = esp_timer_get_time();
    if (now_us >= state->next_disagreement_log_us) {
        TOUCH_LOGW(TAG, "READ_DISAGREE chip=%u first=0x%04X verify=0x%04X total=%lu; candidate discarded",
                   chip, first, second, (unsigned long)state->read_disagreements);
        state->next_disagreement_log_us = now_us + 1000000;
    }
    return ESP_OK;
}

void touch_serial_report_scan(void)
{
    touch_chip_t snapshot[CY8_DEVICE_COUNT] = {0};
    portENTER_CRITICAL(&s_state_lock);
    for (unsigned chip = 0; chip < CY8_DEVICE_COUNT; ++chip) {
        const touch_chip_t *s = &s_chips[chip];
        snapshot[chip].filter = s->filter;
        snapshot[chip].sensor_enable = s->sensor_enable;
        snapshot[chip].samples = s->samples;
        snapshot[chip].read_disagreements = s->read_disagreements;
        snapshot[chip].button_requests = s->button_requests;
        snapshot[chip].verify_requests = s->verify_requests;
        snapshot[chip].max_request_gap_us = s->max_request_gap_us;
        snapshot[chip].last_request_us = s->last_request_us;
        snapshot[chip].first_raw = s->first_raw;
        snapshot[chip].second_raw = s->second_raw;
        snapshot[chip].raw_valid = s->raw_valid;
    }
    portEXIT_CRITICAL(&s_state_lock);
    int64_t now_us = esp_timer_get_time();
    uint8_t online = 0;
    for (unsigned chip = 0; chip < CY8_DEVICE_COUNT; ++chip) {
        if (touch_filter_fresh(&snapshot[chip].filter, now_us)) online |= (uint8_t)(1U << chip);
    }
    char line[480];
    snprintf(line, sizeof(line),
             "TOUCH,SCAN,CHIPS,%u,ACTIVE,0x%02X,ONLINE,0x%02X,STALE_MS,%u,PASS_BUDGET_US,%u\r\n",
             (unsigned)CY8_DEVICE_COUNT, (unsigned)CY8_ACTIVE_MASK, (unsigned)online,
             (unsigned)(TOUCH_STALE_US / 1000), (unsigned)CY8_PASS_BUDGET_US);
    touch_serial_write(line);
    for (unsigned chip = 0; chip < CY8_DEVICE_COUNT; ++chip) {
        const touch_chip_t *s = &snapshot[chip];
        snprintf(line, sizeof(line),
                 "TOUCH,CHIP,%u,ADDR,0x%02X,ACTIVE,%u,ONLINE,%u,FRESH,%u,SENSOR,0x%04X,"
                 "FIRST,0x%04X,SECOND,0x%04X,RAW_VALID,%u,CONFIRMED,0x%04X,"
                 "REQUESTS,%lu,VERIFIES,%lu,SAMPLES,%lu,DISAGREE,%lu,MAX_GAP_US,%lu,"
                 "TRY_AGE_MS,%lld,GOOD_AGE_MS,%lld,CONFIRM_AGE_MS,%lld,FAILURES,%u\r\n",
                 chip, cy8cmbr3116_address(chip), !!(CY8_ACTIVE_MASK & (1U << chip)),
                 (unsigned)s->filter.online, (unsigned)touch_filter_fresh(&s->filter, now_us),
                 s->sensor_enable, s->first_raw, s->second_raw, (unsigned)s->raw_valid,
                 s->filter.buttons, (unsigned long)s->button_requests,
                 (unsigned long)s->verify_requests, (unsigned long)s->samples,
                 (unsigned long)s->read_disagreements, (unsigned long)s->max_request_gap_us,
                 s->last_request_us ? (long long)((now_us - s->last_request_us) / 1000) : -1LL,
                 s->filter.last_good_us ? (long long)((now_us - s->filter.last_good_us) / 1000) : -1LL,
                 s->filter.last_confirmed_us ? (long long)((now_us - s->filter.last_confirmed_us) / 1000) : -1LL,
                 (unsigned)s->filter.failures);
        touch_serial_write(line);
    }
}

static esp_err_t poll_chip(uint8_t chip)
{
    uint16_t current_state;
    bool verified;
    esp_err_t err = read_guarded_buttons(chip, &current_state, &verified);
    if (err == ESP_OK) {
        if (verified) accept_buttons(chip, current_state, s_chips[chip].sensor_enable);
        return ESP_OK;
    }
    int64_t now_us = esp_timer_get_time();
    portENTER_CRITICAL(&s_state_lock);
    bool disconnect = touch_filter_fail(&s_chips[chip].filter, now_us);
    portEXIT_CRITICAL(&s_state_lock);
    if (disconnect) disconnect_chip(chip, "READ_FAILURE", now_us);
    return err;
}

static void probe_chip(uint8_t chip)
{
    touch_chip_t *state = &s_chips[chip];
    uint16_t current_state;
    uint16_t sensor_enable;
    bool verified = true;
    esp_err_t err;
    switch (state->probe.phase) {
    case TOUCH_PROBE_ID:
        err = cy8cmbr3116_read_device_id(chip);
        break;
    case TOUCH_PROBE_SENSORS:
        err = cy8cmbr3116_read_sensor_enable(chip, &sensor_enable);
        if (err == ESP_OK) {
            portENTER_CRITICAL(&s_state_lock);
            state->sensor_enable = sensor_enable;
            portEXIT_CRITICAL(&s_state_lock);
        }
        break;
    case TOUCH_PROBE_BUTTONS:
        err = read_guarded_buttons(chip, &current_state, &verified);
        break;
    default:
        err = ESP_ERR_INVALID_STATE;
        break;
    }
    if (err == ESP_OK) {
        if (state->probe.phase == TOUCH_PROBE_BUTTONS) {
            if (verified) accept_buttons(chip, current_state, state->sensor_enable);
            else state->probe.next_us = esp_timer_get_time() + CY8_PROBE_SLOT_US;
        } else {
            touch_probe_advance(&state->probe, esp_timer_get_time());
        }
        return;
    }
    touch_probe_failed(&state->probe, esp_timer_get_time());
    char message[64];
    snprintf(message, sizeof(message), "ERROR,CHIP,%u,0x%02X,%s\r\n",
             chip, cy8cmbr3116_address(chip), esp_err_to_name(err));
    host_send(message);
}

static void poll_touch_once(touch_loop_t *loop)
{
    int64_t pass_start_us = esp_timer_get_time();
    expire_stale_chips();
    if (pass_start_us >= loop->next_bus_check_us) {
        bool ready = cy8cmbr3116_bus_ready();
        if (!ready) {
            if (loop->bus_fault_since_us == 0) loop->bus_fault_since_us = pass_start_us;
            loop->next_bus_check_us = pass_start_us + CY8_BUS_WAIT_US;
            if (pass_start_us - loop->bus_fault_since_us >= CY8_BUS_WAIT_US &&
                pass_start_us >= loop->next_bus_reset_us) {
                cy8cmbr3116_recover_bus();
                loop->next_bus_reset_us = esp_timer_get_time() + CY8_BUS_RESET_INTERVAL_US;
                ready = cy8cmbr3116_bus_ready();
            }
            if (pass_start_us >= loop->next_bus_log_us) {
                TOUCH_LOGW(TAG, "BUS_WAIT active_mask=0x%02X; bus not idle, no per-chip probe backoff",
                           CY8_ACTIVE_MASK);
                loop->next_bus_log_us = pass_start_us + 1000000;
            }
        }
        if (ready) loop->bus_fault_since_us = 0;
        bool stalled = esp_timer_get_time() - pass_start_us >= CY8_PASS_BUDGET_US;
        uint8_t pass_start = loop->online_cursor;
        loop->online_cursor = (uint8_t)((pass_start + 1U) % CY8_DEVICE_COUNT);
        for (uint8_t offset = 0; ready && !stalled && offset < CY8_DEVICE_COUNT; ++offset) {
            uint8_t chip = (uint8_t)((pass_start + offset) % CY8_DEVICE_COUNT);
            if ((CY8_ACTIVE_MASK & (1U << chip)) == 0) continue;
            if (!s_chips[chip].filter.online) continue;
            poll_chip(chip);
            ready = cy8cmbr3116_bus_ready();
            if (!ready || esp_timer_get_time() - pass_start_us >= CY8_PASS_BUDGET_US) {
                loop->online_cursor = (uint8_t)((chip + 1U) % CY8_DEVICE_COUNT);
                stalled = true;
                break;
            }
        }

        int64_t now_us = esp_timer_get_time();
        /* One bounded probe slot follows the online slice even when that
         * slice used its time budget. Otherwise seven busy online devices
         * can permanently prevent the eighth device from joining/rejoining.
         * Regular reads retain priority and resume at online_cursor. */
        if (ready && now_us >= loop->next_probe_slot_us) {
            for (uint8_t offset = 0; offset < CY8_DEVICE_COUNT; ++offset) {
                uint8_t chip = (uint8_t)((loop->probe_cursor + offset) % CY8_DEVICE_COUNT);
                if ((CY8_ACTIVE_MASK & (1U << chip)) == 0) continue;
                if (s_chips[chip].filter.online || now_us < s_chips[chip].probe.next_us) continue;
                probe_chip(chip);
                loop->probe_cursor = (uint8_t)((chip + 1U) % CY8_DEVICE_COUNT);
                loop->next_probe_slot_us = esp_timer_get_time() + CY8_PROBE_SLOT_US;
                break;
            }
        }
        ready = ready && cy8cmbr3116_bus_ready();
        if (s_diag_requested) {
            s_diag_requested = false;
            s_diag_running = true;
            s_diag_chip = 0;
            s_diag_channel = 0;
        }
        if (ready && s_diag_running &&
            esp_timer_get_time() - pass_start_us < CY8_PASS_BUDGET_US) {
            host_diagnostic_step();
        }
        if (ready && !cy8cmbr3116_bus_ready()) ready = false;
        if (!ready) loop->next_bus_check_us = esp_timer_get_time() + CY8_BUS_WAIT_US;
    }
    expire_stale_chips();
    uint16_t buttons[CY8_DEVICE_COUNT];
    uint8_t online_mask;
    touch_serial_snapshot(buttons, &online_mask);
    if (online_mask == CY8_ACTIVE_MASK && !loop->all_ready_announced) {
        char message[40];
        snprintf(message, sizeof(message), "READY,TOUCH,%u,%u\r\n",
                 (unsigned)CY8_DEVICE_COUNT, (unsigned)TOUCH_LAYOUT_KEYS);
        host_send(message);
        loop->all_ready_announced = true;
    } else if (online_mask != CY8_ACTIVE_MASK) {
        loop->all_ready_announced = false;
    }
    TickType_t now = xTaskGetTickCount();
    if (s_stream_enabled &&
        (now - loop->last_stream_report) >= pdMS_TO_TICKS(STATE_STREAM_INTERVAL_MS)) {
        host_send_state();
        loop->last_stream_report = now;
    }
}

static void touch_task(void *argument)
{
    (void)argument;
    while (cy8cmbr3116_init() != ESP_OK) {
        host_send("ERROR,I2C_INIT\r\n");
        vTaskDelay(pdMS_TO_TICKS(CY8_INIT_RETRY_MS));
    }
    touch_loop_t loop = {0};
    for (;;) {
        poll_touch_once(&loop);
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
    if (!touch_layout_validate() || !touch_filter_self_test()) {
        ESP_LOGE(TAG, "Touch layout, state encoder or recovery filter self-test failed");
        return ESP_ERR_INVALID_STATE;
    }
    ESP_LOGI(TAG, "Layout self-test OK: %u chips, %u keys, %u hex digits",
             (unsigned)CY8_DEVICE_COUNT, (unsigned)TOUCH_LAYOUT_KEYS,
             (unsigned)TOUCH_LAYOUT_STATE_HEX_DIGITS);
    ESP_LOGI(TAG, "Touch filter self-test OK; confirm=2 stale_ms=%d failures=%d probe_slot_ms=%d",
             TOUCH_STALE_US / 1000, TOUCH_FAILURE_LIMIT, CY8_PROBE_SLOT_US / 1000);
    const uart_config_t config = {
        .baud_rate = HOST_UART_BAUD_RATE,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_DEFAULT,
    };
    esp_err_t err = uart_driver_install(HOST_UART, HOST_UART_RX_BUFFER_SIZE,
                                        HOST_UART_TX_BUFFER_SIZE, 0, NULL, 0);
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
    err = touch_output_start();
    if (err != ESP_OK) return err;

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
