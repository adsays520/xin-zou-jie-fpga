#include "../main/touch_serial.c"
#include <stdarg.h>

#define SIM_EXPORT __declspec(dllexport)

static int64_t s_sim_time;
static bool s_sim_bus_ready;
static bool s_sim_reset_recovers_bus;
static unsigned s_sim_bus_resets;
static uint16_t s_sim_buttons[8];
static uint16_t s_sim_ids[8];
static int s_sim_failures[8];
static unsigned s_sim_error_us[8];
static unsigned s_sim_reads[8][4];
static unsigned s_sim_success_read_us;
static unsigned s_sim_uart_writes;
static unsigned s_sim_raw_traces;
static unsigned s_sim_edge_traces;
static touch_loop_t s_sim_loop;
static note_trace_state_t s_sim_note_trace;
static char s_sim_notes[512][256];
static unsigned s_sim_note_count;
static char s_sim_reports[16][480];
static unsigned s_sim_report_count;
static unsigned s_sim_button_sequence[8][64];
static unsigned s_sim_sequence_length[8],s_sim_sequence_cursor[8];

void *memset(void *destination, int value, size_t length)
{
    unsigned char *bytes = destination;
    for (size_t index = 0; index < length; ++index) bytes[index] = (unsigned char)value;
    return destination;
}

void *memcpy(void *destination, const void *source, size_t length)
{
    unsigned char *output = destination;
    const unsigned char *input = source;
    for (size_t index = 0; index < length; ++index) output[index] = input[index];
    return destination;
}

size_t strlen(const char *text)
{
    size_t length = 0;
    while (text[length]) ++length;
    return length;
}

int strcmp(const char *first, const char *second)
{
    while (*first && *first == *second) { ++first; ++second; }
    return (unsigned char)*first - (unsigned char)*second;
}

int snprintf(char *buffer, size_t size, const char *format, ...)
{
    va_list arguments;
    va_start(arguments, format);
    int written = vsnprintf(buffer, size, format, arguments);
    va_end(arguments);
    return written;
}

const char *esp_err_to_name(esp_err_t error) { (void)error; return "SIM_ERROR"; }
int64_t esp_timer_get_time(void) { return s_sim_time; }
TickType_t xTaskGetTickCount(void) { return (TickType_t)(s_sim_time / 1000); }
void vTaskDelay(TickType_t ticks) { s_sim_time += (int64_t)ticks * 1000; }
int xTaskCreate(void (*task)(void *), const char *name, unsigned stack, void *argument,
                unsigned priority, void *handle)
{
    (void)task; (void)name; (void)stack; (void)argument; (void)priority; (void)handle;
    return pdPASS;
}
int uart_write_bytes(int port, const void *data, size_t length)
{
    (void)port; (void)data;
    ++s_sim_uart_writes;
    return (int)length;
}
int uart_read_bytes(int port, void *data, uint32_t length, TickType_t wait)
{
    (void)port; (void)data; (void)length; (void)wait;
    return 0;
}
esp_err_t uart_driver_install(int port, int receive_size, int transmit_size,
                              int queue_size, void *queue, int flags)
{
    (void)port; (void)receive_size; (void)transmit_size; (void)queue_size; (void)queue; (void)flags;
    return ESP_OK;
}
esp_err_t uart_param_config(int port, const uart_config_t *config)
{
    (void)port; (void)config; return ESP_OK;
}
esp_err_t uart_set_pin(int port, int transmit, int receive, int rts, int cts)
{
    (void)port; (void)transmit; (void)receive; (void)rts; (void)cts; return ESP_OK;
}
void uart_vfs_dev_use_driver(int port) { (void)port; }
esp_err_t touch_output_start(void) { return ESP_OK; }
void touch_output_uart(const char *message)
{
    if (strncmp(message, "TOUCH,", 6) == 0 && s_sim_report_count < 16) {
        snprintf(s_sim_reports[s_sim_report_count++], 480, "%s", message);
    }
}
void touch_output_log(esp_log_level_t level, const char *tag, const char *format, ...)
{
    (void)level;
    if (strcmp(tag, "TOUCH_TRACE") == 0) {
        if (format[0] == 'R') ++s_sim_raw_traces;
        if (format[0] == 'E') ++s_sim_edge_traces;
    }
    if (strncmp(tag, "NOTE_", 5) == 0 && s_sim_note_count < 512) {
        char *message = s_sim_notes[s_sim_note_count++];
        int prefix = snprintf(message, 256, "%s: ", tag);
        va_list arguments;
        va_start(arguments, format);
        vsnprintf(message + prefix, 256 - prefix, format, arguments);
        va_end(arguments);
    }
}

static esp_err_t simulated_read(uint8_t chip, unsigned operation)
{
    ++s_sim_reads[chip][operation];
    if (s_sim_failures[chip]) {
        if (s_sim_failures[chip] > 0) --s_sim_failures[chip];
        s_sim_time += s_sim_error_us[chip];
        return ESP_ERR_INVALID_RESPONSE;
    }
    s_sim_time += s_sim_success_read_us;
    return ESP_OK;
}

uint8_t cy8cmbr3116_address(uint8_t chip) { return (uint8_t)(0x37 + chip); }
esp_err_t cy8cmbr3116_init(void) { return ESP_OK; }
bool cy8cmbr3116_bus_ready(void) { return s_sim_bus_ready; }
esp_err_t cy8cmbr3116_recover_bus(void)
{
    ++s_sim_bus_resets;
    s_sim_time += 500;
    if (s_sim_reset_recovers_bus) s_sim_bus_ready = true;
    return ESP_OK;
}
esp_err_t cy8cmbr3116_read_device_id(uint8_t chip)
{
    esp_err_t result = simulated_read(chip, 0);
    if (result == ESP_OK && s_sim_ids[chip] != 0x0A05) result = ESP_ERR_INVALID_RESPONSE;
    return result;
}
esp_err_t cy8cmbr3116_read_sensor_enable(uint8_t chip, uint16_t *mask)
{
    esp_err_t result = simulated_read(chip, 1);
    if (result == ESP_OK) *mask = UINT16_MAX;
    return result;
}
esp_err_t cy8cmbr3116_read_buttons(uint8_t chip, uint16_t *buttons)
{
    esp_err_t result = simulated_read(chip, 2);
    if (result == ESP_OK) {
        unsigned value = s_sim_buttons[chip];
        if (s_sim_sequence_cursor[chip] < s_sim_sequence_length[chip]) {
            value = s_sim_button_sequence[chip][s_sim_sequence_cursor[chip]++];
        }
        if (value > UINT16_MAX) return ESP_ERR_INVALID_RESPONSE;
        *buttons = (uint16_t)value;
    }
    return result;
}
esp_err_t cy8cmbr3116_read_difference_count(uint8_t chip, uint8_t channel, uint16_t *count)
{
    (void)channel;
    esp_err_t result = simulated_read(chip, 3);
    if (result == ESP_OK) *count = 42;
    return result;
}

SIM_EXPORT void sim_reset(int online)
{
    memset(s_chips, 0, sizeof(s_chips));
    memset(&s_sim_loop, 0, sizeof(s_sim_loop));
    memset(s_sim_reads, 0, sizeof(s_sim_reads));
    memset(s_sim_failures, 0, sizeof(s_sim_failures));
    memset(s_sim_buttons, 0, sizeof(s_sim_buttons));
    memset(s_sim_sequence_length, 0, sizeof(s_sim_sequence_length));
    memset(s_sim_sequence_cursor, 0, sizeof(s_sim_sequence_cursor));
    s_sim_uart_writes = 0;
    s_sim_raw_traces = 0;
    s_sim_edge_traces = 0;
    s_sim_note_count = 0;
    s_sim_report_count = 0;
    memset(&s_sim_note_trace, 0, sizeof(s_sim_note_trace));
    s_sim_time = 1000000;
    s_sim_success_read_us = 500;
    s_sim_bus_ready = true;
    s_sim_reset_recovers_bus = false;
    s_sim_bus_resets = 0;
    s_diag_requested = false;
    s_diag_running = false;
    s_stream_enabled = false;
    for (uint8_t chip = 0; chip < 8; ++chip) {
        s_sim_ids[chip] = 0x0A05;
        s_sim_error_us[chip] = 500;
        if (online && (CY8_ACTIVE_MASK & (1U << chip))) {
            accept_buttons(chip, 0, UINT16_MAX);
            accept_buttons(chip, 0, UINT16_MAX);
        }
    }
}
SIM_EXPORT void sim_buttons(unsigned chip, unsigned buttons) { s_sim_buttons[chip] = (uint16_t)buttons; }
SIM_EXPORT void sim_set_read_cost(unsigned elapsed_us) { s_sim_success_read_us = elapsed_us; }
SIM_EXPORT void sim_button_sample(unsigned chip, unsigned buttons)
{
    if (s_sim_sequence_length[chip] < 64) {
        s_sim_button_sequence[chip][s_sim_sequence_length[chip]++] = buttons;
    }
}
SIM_EXPORT unsigned sim_disagreements(unsigned chip) { return s_chips[chip].read_disagreements; }
SIM_EXPORT void sim_scan_report(void) { s_sim_report_count = 0; touch_serial_report_scan(); }
SIM_EXPORT unsigned sim_scan_report_count(void) { return s_sim_report_count; }
SIM_EXPORT const char *sim_scan_report_at(unsigned index) { return s_sim_reports[index]; }
SIM_EXPORT unsigned sim_time_us(void) { return (unsigned)s_sim_time; }
SIM_EXPORT unsigned sim_confirmed_us(unsigned chip) { return (unsigned)s_chips[chip].filter.last_confirmed_us; }
SIM_EXPORT void sim_id(unsigned chip, unsigned identity) { s_sim_ids[chip] = (uint16_t)identity; }
SIM_EXPORT void sim_fail(unsigned chip, int count, unsigned duration_us)
{
    s_sim_failures[chip] = count;
    s_sim_error_us[chip] = duration_us;
}
SIM_EXPORT void sim_bus(int ready) { s_sim_bus_ready = ready != 0; }
SIM_EXPORT void sim_recoverable_bus(int recoverable) { s_sim_reset_recovers_bus = recoverable != 0; }
SIM_EXPORT unsigned sim_bus_resets(void) { return s_sim_bus_resets; }
SIM_EXPORT void sim_diag(void) { s_diag_requested = true; }
SIM_EXPORT int sim_tick(unsigned elapsed_us)
{
    s_sim_time += elapsed_us;
    int64_t started = s_sim_time;
    poll_touch_once(&s_sim_loop);
    return (int)(s_sim_time - started);
}
SIM_EXPORT unsigned sim_mask(void)
{
    uint16_t buttons[8];
    uint8_t mask;
    touch_serial_snapshot(buttons, &mask);
    return mask;
}
SIM_EXPORT unsigned sim_state(unsigned chip)
{
    uint16_t buttons[8];
    uint8_t mask;
    touch_serial_snapshot(buttons, &mask);
    return buttons[chip];
}
SIM_EXPORT unsigned sim_online(unsigned chip) { return s_chips[chip].filter.online; }
SIM_EXPORT unsigned sim_read_count(unsigned chip, unsigned operation) { return s_sim_reads[chip][operation]; }
SIM_EXPORT unsigned sim_uart_writes(void) { return s_sim_uart_writes; }
SIM_EXPORT unsigned sim_trace_count(unsigned edges) { return edges ? s_sim_edge_traces : s_sim_raw_traces; }
SIM_EXPORT unsigned sim_note_count(void) { return s_sim_note_count; }
SIM_EXPORT const char *sim_note_at(unsigned index) { return s_sim_notes[index]; }
SIM_EXPORT void sim_ack(const uint8_t *keys, unsigned instrument, int hall, int enabled, unsigned sequence)
{
    note_trace_ack(&s_sim_note_trace, sequence, keys, instrument, hall != 0, enabled != 0);
}
SIM_EXPORT unsigned sim_filter_test(void) { return touch_filter_self_test(); }
SIM_EXPORT unsigned sim_probe_limit_test(void)
{
    touch_probe_t probe = {0};
    touch_probe_reset(&probe, 0);
    if (probe.next_us != 10000 || probe.phase != TOUCH_PROBE_ID) return 0;
    touch_probe_advance(&probe, 50000);
    if (probe.phase != TOUCH_PROBE_SENSORS || probe.next_us != 50000) return 0;
    for (unsigned attempt = 0; attempt < 40; ++attempt) {
        touch_probe_failed(&probe, 100000);
        if (probe.next_us > 300000 || probe.next_us < 110000 || probe.phase != TOUCH_PROBE_ID) return 0;
    }
    return 1;
}

void ble_control_log(const char *line) {(void)line;}
void ble_control_event(const char *line) {(void)line;}
