#include "hall_adc.h"
#include "hall_detector.h"
#include "fpga_link.h"
#include "touch_serial.h"
#include "touch_output.h"
#include "sdkconfig.h"
#include <stdatomic.h>
#include <stdio.h>
#include <string.h>

#if CONFIG_HALL_ADC_ENABLE
#include "esp_adc/adc_oneshot.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_timer.h"

static adc_oneshot_unit_handle_t s_adc1, s_adc2;
static hall_detector_t s_detector[7];
static portMUX_TYPE s_hall_lock = portMUX_INITIALIZER_UNLOCKED;
static _Atomic bool s_calibrate;
static _Atomic bool s_armed;
static _Atomic unsigned s_active_mask = CONFIG_HALL_ACTIVE_MASK;
static _Atomic bool s_started;
static uint16_t s_raw[7], s_baseline[7], s_threshold[7];
static uint32_t s_events[7], s_rejected[7], s_errors[7];
static uint8_t s_valid_mask;
typedef struct {
    uint16_t minimum, maximum, noise, raw_peak, filtered_peak;
    uint8_t state, confirmation;
    hall_calibration_t calibration;
} hall_diagnostic_t;
static hall_diagnostic_t s_diagnostic[7];
static const adc_channel_t s_channels[7] = {ADC_CHANNEL_0, ADC_CHANNEL_1, ADC_CHANNEL_3,
    ADC_CHANNEL_4, ADC_CHANNEL_5, ADC_CHANNEL_6, ADC_CHANNEL_7};

static void hall_sample_once(unsigned *applied_mask)
{
        unsigned active_mask = s_active_mask;
        if (atomic_exchange(&s_calibrate, false) || active_mask != *applied_mask) {
            for (unsigned channel = 0; channel < 7; ++channel) hall_detector_reset(&s_detector[channel]);
            portENTER_CRITICAL(&s_hall_lock);
            s_valid_mask = 0;
            memset(s_raw, 0, sizeof(s_raw));
            memset(s_baseline, 0, sizeof(s_baseline));
            memset(s_threshold, 0, sizeof(s_threshold));
            memset(s_diagnostic, 0, sizeof(s_diagnostic));
            portEXIT_CRITICAL(&s_hall_lock);
            *applied_mask = active_mask;
            TOUCH_LOGI("HALL", "CAL mask=0x%02X: 128 idle samples per channel; leave picks untouched", active_mask);
        }
        for (unsigned channel = 0; channel < 7; ++channel) {
            if (!(active_mask & (1U << channel))) continue;
            int raw;
            esp_err_t error = adc_oneshot_read(channel < 2 ? s_adc1 : s_adc2, s_channels[channel], &raw);
            if (error != ESP_OK) {
                hall_detector_reset(&s_detector[channel]);
                portENTER_CRITICAL(&s_hall_lock);
                uint32_t errors = ++s_errors[channel];
                s_valid_mask &= (uint8_t)~(1U << channel);
                s_baseline[channel] = s_threshold[channel] = 0;
                memset(&s_diagnostic[channel], 0, sizeof(s_diagnostic[channel]));
                portEXIT_CRITICAL(&s_hall_lock);
                if (errors % 1000U == 1) TOUCH_LOGW("HALL", "ADC H%u failed: %s total=%lu", channel + 1,
                    esp_err_to_name(error), (unsigned long)errors);
                continue;
            }
            uint8_t velocity = 0;
            uint32_t now_ms = (uint32_t)(esp_timer_get_time() / 1000);
            bool trigger = hall_detector_sample(&s_detector[channel], (uint16_t)raw, now_ms,
                CONFIG_HALL_TRIGGER_RAW, CONFIG_HALL_FULL_SCALE_RAW, &velocity);
            portENTER_CRITICAL(&s_hall_lock);
            s_raw[channel] = (uint16_t)raw;
            s_baseline[channel] = (uint16_t)(s_detector[channel].baseline_q8 >> 8);
            s_threshold[channel] = s_detector[channel].threshold;
            s_diagnostic[channel] = (hall_diagnostic_t){
                .minimum = s_detector[channel].count ? s_detector[channel].minimum : 0,
                .maximum = s_detector[channel].maximum,
                .noise = s_detector[channel].noise,
                .raw_peak = s_detector[channel].raw_peak,
                .filtered_peak = s_detector[channel].filtered_peak,
                .state = s_detector[channel].state,
                .confirmation = s_detector[channel].confirmation,
                .calibration = s_detector[channel].calibration
            };
            if (s_detector[channel].valid) s_valid_mask |= (uint8_t)(1U << channel);
            else s_valid_mask &= (uint8_t)~(1U << channel);
            portEXIT_CRITICAL(&s_hall_lock);
            if (!trigger || !s_armed || s_calibrate || active_mask != s_active_mask) continue;
#if CONFIG_HALL_REVERSE_ORDER
            unsigned string_number = channel;
#else
            unsigned string_number = 7 - channel;
#endif
            bool queued = channel == 0 ? fpga_link_hall_strum(velocity) :
                fpga_link_hall_trigger(string_number, velocity);
            portENTER_CRITICAL(&s_hall_lock);
            ++s_events[channel];
            if (!queued) ++s_rejected[channel];
            portEXIT_CRITICAL(&s_hall_lock);
            if (channel == 0) TOUCH_LOGI("HALL", "STRUM H1 strings=6,5,4,3,2,1 interval_ms=8 velocity=%u queued=%u", velocity, queued);
            else TOUCH_LOGI("HALL", "PICK H%u string=%u velocity=%u queued=%u", channel + 1, string_number, velocity, queued);
        }
}

static void hall_task(void *argument)
{
    (void)argument;
    unsigned applied_mask = 0;
    for (;;) {
        hall_sample_once(&applied_mask);
        vTaskDelay(pdMS_TO_TICKS(1));
    }
}

static void hall_status(void)
{
    uint16_t raw[7], baseline[7], threshold[7];
    uint32_t events[7], rejected[7], errors[7];
    uint8_t valid_mask;
    hall_diagnostic_t diagnostic[7];
    unsigned active_mask = s_active_mask;
    portENTER_CRITICAL(&s_hall_lock);
    memcpy(raw, s_raw, sizeof(raw));
    memcpy(baseline, s_baseline, sizeof(baseline));
    memcpy(threshold, s_threshold, sizeof(threshold));
    memcpy(events, s_events, sizeof(events));
    memcpy(rejected, s_rejected, sizeof(rejected));
    memcpy(errors, s_errors, sizeof(errors));
    valid_mask = s_valid_mask;
    memcpy(diagnostic, s_diagnostic, sizeof(diagnostic));
    portEXIT_CRITICAL(&s_hall_lock);
    char message[192];
    snprintf(message, sizeof(message), "HALL,STATE,ENABLED,%u,ARMED,%u,MASK,0x%02X\r\n",
             (unsigned)s_started, (unsigned)s_armed, (unsigned)s_active_mask);
    touch_serial_write(message);
    for (unsigned channel = 0; channel < 7; ++channel) {
        snprintf(message, sizeof(message), "HALL,%u,RAW,%u,BASE,%u,THRESHOLD,%u,VALID,%u,EVENTS,%lu,REJECTED,%lu,ERRORS,%lu\r\n",
            channel + 1, raw[channel], baseline[channel], threshold[channel], !!(valid_mask & (1U << channel)),
            (unsigned long)events[channel], (unsigned long)rejected[channel], (unsigned long)errors[channel]);
        touch_serial_write(message);
        static const char *const calibration_names[] = {"CALIBRATING", "OK", "RAIL", "NOISY", "UNREACHABLE"};
        static const char *const state_names[] = {"CALIBRATING", "READY", "PEAK", "WAIT_CENTER", "INVALID"};
        const char *state = diagnostic[channel].state == 1 && diagnostic[channel].confirmation ?
            "CONFIRM" : state_names[diagnostic[channel].state];
        const char *calibration = calibration_names[diagnostic[channel].calibration];
        if (!(active_mask & (1U << channel))) state = calibration = "OFF";
        snprintf(message, sizeof(message), "HALLDIAG,%u,CAL,%s,STATE,%s,CAL_MIN,%u,CAL_MAX,%u,NOISE,%u,RAW_PEAK,%u,FILTERED_PEAK,%u\r\n",
            channel + 1, calibration, state, diagnostic[channel].minimum, diagnostic[channel].maximum,
            diagnostic[channel].noise, diagnostic[channel].raw_peak, diagnostic[channel].filtered_peak);
        touch_serial_write(message);
    }
}
#endif

bool hall_adc_host_command(const char *line)
{
    if (strncmp(line, "HALL,", 5) != 0) return false;
#if CONFIG_HALL_ADC_ENABLE
    unsigned mask;
    char extra;
    if (strcmp(line, "HALL,STATUS") == 0) {
        hall_status();
    } else if (strcmp(line, "HALL,ARM,OFF") == 0) {
        s_armed = false;
        fpga_link_cancel_strums();
        touch_serial_write("OK,HALL,ARM,OFF\r\n");
    } else if (strcmp(line, "HALL,ARM,ON") == 0 && s_started && s_active_mask != 0) {
        fpga_link_cancel_strums();
        s_calibrate = true;
        s_armed = true;
        touch_serial_write("OK,HALL,ARM,ON,CALIBRATING\r\n");
    } else if (strcmp(line, "HALL,CAL") == 0 && s_started) {
        fpga_link_cancel_strums();
        s_calibrate = true;
        touch_serial_write("OK,HALL,CAL\r\n");
    } else if (sscanf(line, "HALL,MASK,%x%c", &mask, &extra) == 1 && mask <= 0x7f) {
        s_armed = false;
        fpga_link_cancel_strums();
        s_active_mask = mask;
        s_calibrate = true;
        touch_serial_write("OK,HALL,MASK,DISARMED\r\n");
    } else {
        touch_serial_write("ERROR,HALL,ARG_OR_NOT_READY\r\n");
    }
#else
    touch_serial_write("ERROR,HALL,ADC_DISABLED\r\n");
#endif
    return true;
}

esp_err_t hall_adc_start(void)
{
    if (!hall_detector_selftest()) return ESP_FAIL;
#if CONFIG_HALL_ADC_ENABLE
    const adc_oneshot_unit_init_cfg_t first_unit = {.unit_id = ADC_UNIT_1};
    const adc_oneshot_unit_init_cfg_t second_unit = {.unit_id = ADC_UNIT_2};
    esp_err_t error = adc_oneshot_new_unit(&first_unit, &s_adc1);
    if (error != ESP_OK) return error;
    error = adc_oneshot_new_unit(&second_unit, &s_adc2);
    if (error != ESP_OK) {
        adc_oneshot_del_unit(s_adc1);
        return error;
    }
    const adc_oneshot_chan_cfg_t config = {.atten = ADC_ATTEN_DB_12, .bitwidth = ADC_BITWIDTH_12};
    for (unsigned channel = 0; channel < 7; ++channel) {
        error = adc_oneshot_config_channel(channel < 2 ? s_adc1 : s_adc2, s_channels[channel], &config);
        if (error != ESP_OK) break;
    }
    s_calibrate = true;
    if (error == ESP_OK && xTaskCreate(hall_task, "hall_picks", 4096, NULL, 5, NULL) != pdPASS) error = ESP_ERR_NO_MEM;
    if (error != ESP_OK) {
        adc_oneshot_del_unit(s_adc2);
        adc_oneshot_del_unit(s_adc1);
        return error;
    }
    s_started = true;
    TOUCH_LOGI("HALL", "ADC enabled, DISARMED; H1/H2=GPIO1/2 H3..H7=GPIO14..18 mask=0x%02X", (unsigned)s_active_mask);
#endif
    return ESP_OK;
}
