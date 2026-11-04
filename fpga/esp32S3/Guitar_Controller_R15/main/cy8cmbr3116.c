#include "cy8cmbr3116.h"
#include "touch_board.h"
#include "touch_output.h"

#include <inttypes.h>
#include <stddef.h>
#include <string.h>

#include "driver/gpio.h"
#include "driver/i2c_master.h"
#include "esp_log.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#define CY8_I2C_FREQUENCY_HZ 200000
#define CY8_I2C_TIMEOUT_MS 10
#define CY8_SLOW_READ_US 5000
#define CY8_LOG_INTERVAL_US 1000000
#define CY8_SLOW_LOG_INTERVAL_US 10000000
#define CY8_SUMMARY_INTERVAL_US 30000000
#define CY8_REG_SENSOR_EN 0x00
#define CY8_REG_DEVICE_ID 0x90
#define CY8_REG_BUTTON_STAT 0xAA
#define CY8_REG_DIFF_COUNT_0 0xBA
#define CY8_DEVICE_ID_3116 0x0A05

typedef struct {
    uint32_t requests;
    uint32_t reads;
    uint32_t errors;
    uint32_t api_timeouts;
    uint32_t invalid_responses;
    uint32_t verify_errors;
    uint32_t slow_ok;
    uint32_t recoveries;
    uint32_t retry_reads;
    uint32_t retry_saved;
    uint32_t retry_failed;
    uint32_t streak;
    uint32_t max_us;
    uint32_t max_ok_us;
    uint32_t last_error_duration_us;
    uint32_t suppressed;
    int64_t last_ok_us;
    int64_t last_error_us;
    int64_t last_error_log_us;
    int64_t last_slow_log_us;
    int64_t last_recovery_log_us;
    int64_t last_retry_log_us;
    esp_err_t last_error;
    uint8_t last_error_reg;
    uint8_t before_lines;
    uint8_t after_lines;
} cy8_diagnostics_t;

static const char *TAG = "CY8_I2C";
static const uint8_t s_addresses[CY8_DEVICE_COUNT] = {
    0x37, 0x38, 0x39, 0x3A, 0x3B, 0x3C, 0x3D, 0x3E,
};
static i2c_master_bus_handle_t s_bus;
static i2c_master_dev_handle_t s_devices[CY8_DEVICE_COUNT];
static portMUX_TYPE s_diagnostics_lock = portMUX_INITIALIZER_UNLOCKED;
static cy8_diagnostics_t s_diagnostics[CY8_DEVICE_COUNT];
static int64_t s_next_summary_us;
static uint32_t s_summary_errors;
static uint32_t s_summary_slow;
static uint32_t s_summary_recoveries;
static uint32_t s_summary_retry_saved;

static uint8_t bus_lines(void)
{
    return (uint8_t)((gpio_get_level(TOUCH_SDA_GPIO) << 1) |
                     gpio_get_level(TOUCH_SCL_GPIO));
}

bool cy8cmbr3116_bus_ready(void)
{
    return bus_lines() == 3;
}

esp_err_t cy8cmbr3116_recover_bus(void)
{
    if (s_bus == NULL) return ESP_ERR_INVALID_STATE;
    uint8_t before = bus_lines();
    int64_t started_us = esp_timer_get_time();
    esp_err_t result = i2c_master_bus_reset(s_bus);
    uint8_t after = bus_lines();
    TOUCH_LOGW(TAG, "BUS_RECOVERY result=%s us=%lld pre=%u/%u post=%u/%u",
               esp_err_to_name(result), (long long)(esp_timer_get_time() - started_us),
               (before >> 1) & 1U, before & 1U, (after >> 1) & 1U, after & 1U);
    return result;
}

static const char *register_name(uint8_t reg)
{
    if (reg == CY8_REG_DEVICE_ID) return "DEVICE_ID";
    if (reg == CY8_REG_SENSOR_EN) return "SENSOR_EN";
    if (reg == CY8_REG_BUTTON_STAT) return "BUTTONS";
    return "DIFF_COUNT";
}

static void periodic_summary(int64_t now_us)
{
    if (now_us < s_next_summary_us) return;
    s_next_summary_us = now_us + CY8_SUMMARY_INTERVAL_US;
    uint32_t reads = 0;
    uint32_t errors = 0;
    uint32_t slow = 0;
    uint32_t recoveries = 0;
    uint32_t retry_saved = 0;
    unsigned failing = 0;
    portENTER_CRITICAL(&s_diagnostics_lock);
    for (uint8_t chip = 0; chip < CY8_DEVICE_COUNT; ++chip) {
        reads += s_diagnostics[chip].reads;
        errors += s_diagnostics[chip].errors + s_diagnostics[chip].verify_errors;
        slow += s_diagnostics[chip].slow_ok;
        recoveries += s_diagnostics[chip].recoveries;
        retry_saved += s_diagnostics[chip].retry_saved;
        if (s_diagnostics[chip].streak != 0) failing |= 1U << chip;
    }
    portEXIT_CRITICAL(&s_diagnostics_lock);
    if (errors == s_summary_errors && slow == s_summary_slow &&
        recoveries == s_summary_recoveries && retry_saved == s_summary_retry_saved) return;
    s_summary_errors = errors;
    s_summary_slow = slow;
    s_summary_recoveries = recoveries;
    s_summary_retry_saved = retry_saved;
    TOUCH_LOGW(TAG, "SUMMARY up_ms=%" PRId64 " reads=%" PRIu32
             " errors=%" PRIu32 " slow_ok=%" PRIu32
             " recoveries=%" PRIu32 " retry_saved=%" PRIu32 " failing_mask=0x%02X",
             now_us / 1000, reads, errors, slow, recoveries, retry_saved, failing);
}

static void record_request(uint8_t chip, uint8_t reg, unsigned attempts,
                           esp_err_t err, int64_t start_us)
{
    int64_t now_us = esp_timer_get_time();
    bool log_retry = false;
    uint32_t retry_saved;
    portENTER_CRITICAL(&s_diagnostics_lock);
    cy8_diagnostics_t *stats = &s_diagnostics[chip];
    ++stats->requests;
    if (attempts > 1) {
        ++stats->retry_reads;
        if (err == ESP_OK) {
            ++stats->retry_saved;
            log_retry = stats->retry_saved == 1 ||
                        now_us - stats->last_retry_log_us >= CY8_SLOW_LOG_INTERVAL_US;
            if (log_retry) stats->last_retry_log_us = now_us;
        } else {
            ++stats->retry_failed;
        }
    }
    retry_saved = stats->retry_saved;
    portEXIT_CRITICAL(&s_diagnostics_lock);
    if (log_retry) {
        TOUCH_LOGW(TAG, "RETRY_OK chip=%u addr=0x%02X op=%s attempts=%u"
                 " request_us=%" PRId64 " retry_saved=%" PRIu32,
                 chip, s_addresses[chip], register_name(reg), attempts,
                 now_us - start_us, retry_saved);
    }
    periodic_summary(now_us);
}

static void record_read(uint8_t chip, uint8_t reg, size_t length,
                        esp_err_t err, int64_t start_us, int64_t end_us,
                        uint8_t before_lines, uint8_t after_lines)
{
    int64_t elapsed_us = end_us - start_us;
    uint32_t duration_us = elapsed_us > UINT32_MAX ? UINT32_MAX : (uint32_t)elapsed_us;
    bool log_error = false;
    bool log_slow = false;
    bool log_recovery = false;
    uint32_t recovered_errors = 0;
    uint32_t suppressed = 0;
    cy8_diagnostics_t snapshot;

    portENTER_CRITICAL(&s_diagnostics_lock);
    cy8_diagnostics_t *stats = &s_diagnostics[chip];
    ++stats->reads;
    if (duration_us > stats->max_us) stats->max_us = duration_us;
    if (err != ESP_OK) {
        ++stats->errors;
        ++stats->streak;
        if (err == ESP_ERR_TIMEOUT) ++stats->api_timeouts;
        if (err == ESP_ERR_INVALID_RESPONSE) ++stats->invalid_responses;
        stats->last_error_us = end_us;
        stats->last_error = err;
        stats->last_error_reg = reg;
        stats->last_error_duration_us = duration_us;
        stats->before_lines = before_lines;
        stats->after_lines = after_lines;
        log_error = stats->errors == 1 ||
                    end_us - stats->last_error_log_us >= CY8_LOG_INTERVAL_US;
        if (log_error) {
            stats->last_error_log_us = end_us;
            suppressed = stats->suppressed;
            stats->suppressed = 0;
        } else {
            ++stats->suppressed;
        }
    } else {
        recovered_errors = stats->streak;
        if (recovered_errors != 0) {
            ++stats->recoveries;
            log_recovery = stats->recoveries == 1 ||
                           end_us - stats->last_recovery_log_us >= CY8_LOG_INTERVAL_US;
            if (log_recovery) stats->last_recovery_log_us = end_us;
            suppressed = stats->suppressed;
            stats->suppressed = 0;
        }
        stats->streak = 0;
        stats->last_ok_us = end_us;
        if (duration_us > stats->max_ok_us) stats->max_ok_us = duration_us;
        if (duration_us >= CY8_SLOW_READ_US) {
            ++stats->slow_ok;
            log_slow = stats->slow_ok == 1 ||
                       end_us - stats->last_slow_log_us >= CY8_SLOW_LOG_INTERVAL_US;
            if (log_slow) stats->last_slow_log_us = end_us;
        }
    }
    snapshot = *stats;
    portEXIT_CRITICAL(&s_diagnostics_lock);

    if (log_error) {
        TOUCH_LOGE(TAG, "FAIL chip=%u addr=0x%02X op=%s reg=0x%02X len=%u"
                 " err=%s(0x%X) us=%" PRIu32
                 " pre(SDA/SCL)=%u/%u post(SDA/SCL)=%u/%u"
                 " streak=%" PRIu32 " total=%" PRIu32 " suppressed=%" PRIu32,
                 chip, s_addresses[chip], register_name(reg), reg, (unsigned)length,
                 esp_err_to_name(err), (unsigned)err, duration_us,
                 (before_lines >> 1) & 1U, before_lines & 1U,
                 (after_lines >> 1) & 1U, after_lines & 1U,
                 snapshot.streak, snapshot.errors, suppressed);
    }
    if (log_recovery) {
        TOUCH_LOGW(TAG, "RECOVER chip=%u addr=0x%02X op=%s failures=%" PRIu32
                 " since_error_ms=%" PRId64 " us=%" PRIu32
                 " post(SDA/SCL)=%u/%u suppressed=%" PRIu32 " recoveries=%" PRIu32,
                 chip, s_addresses[chip], register_name(reg), recovered_errors,
                 (end_us - snapshot.last_error_us) / 1000, duration_us,
                 (after_lines >> 1) & 1U, after_lines & 1U, suppressed, snapshot.recoveries);
    }
    if (log_slow) {
        TOUCH_LOGW(TAG, "SLOW_OK chip=%u addr=0x%02X op=%s reg=0x%02X"
                 " us=%" PRIu32 " total=%" PRIu32 " max_ok_us=%" PRIu32,
                 chip, s_addresses[chip], register_name(reg), reg,
                 duration_us, snapshot.slow_ok, snapshot.max_ok_us);
    }
    periodic_summary(end_us);
}

void cy8cmbr3116_report(void)
{
    cy8_diagnostics_t snapshot[CY8_DEVICE_COUNT];
    portENTER_CRITICAL(&s_diagnostics_lock);
    memcpy(snapshot, s_diagnostics, sizeof(snapshot));
    portEXIT_CRITICAL(&s_diagnostics_lock);
    int64_t now_us = esp_timer_get_time();
    uint8_t lines = bus_lines();
    TOUCH_LOGI(TAG, "STATUS version=R15-I2C-GUARD-v3.3 up_ms=%" PRId64
             " SDA=%d SCL=%d hz=%d api_timeout_ms=%d scl_wait=IDF_DEFAULT"
             " current(SDA/SCL)=%u/%u", now_us / 1000,
             TOUCH_SDA_GPIO, TOUCH_SCL_GPIO, CY8_I2C_FREQUENCY_HZ,
             CY8_I2C_TIMEOUT_MS, (lines >> 1) & 1U, lines & 1U);
    for (uint8_t chip = 0; chip < CY8_DEVICE_COUNT; ++chip) {
        const cy8_diagnostics_t *stats = &snapshot[chip];
        TOUCH_LOGI(TAG, "STATS chip=%u addr=0x%02X requests=%" PRIu32 " reads=%" PRIu32
                 " errors=%" PRIu32 " api_timeout=%" PRIu32 " invalid_response=%" PRIu32
                 " verify=%" PRIu32 " slow_ok=%" PRIu32 " recoveries=%" PRIu32
                 " retry_reads=%" PRIu32 " retry_saved=%" PRIu32 " retry_failed=%" PRIu32
                 " streak=%" PRIu32 " max_us=%" PRIu32 " max_ok_us=%" PRIu32
                 " good_age_ms=%" PRId64 " error_age_ms=%" PRId64,
                 chip, s_addresses[chip], stats->requests, stats->reads, stats->errors,
                 stats->api_timeouts, stats->invalid_responses, stats->verify_errors,
                 stats->slow_ok, stats->recoveries,
                 stats->retry_reads, stats->retry_saved, stats->retry_failed, stats->streak,
                 stats->max_us, stats->max_ok_us,
                 stats->last_ok_us == 0 ? (int64_t)-1 : (now_us - stats->last_ok_us) / 1000,
                 stats->last_error_us == 0 ? (int64_t)-1 : (now_us - stats->last_error_us) / 1000);
        if (stats->errors != 0) {
            TOUCH_LOGI(TAG, "LAST_ERROR chip=%u addr=0x%02X op=%s reg=0x%02X"
                     " err=%s us=%" PRIu32 " pre(SDA/SCL)=%u/%u post(SDA/SCL)=%u/%u",
                     chip, s_addresses[chip], register_name(stats->last_error_reg),
                     stats->last_error_reg, esp_err_to_name(stats->last_error),
                     stats->last_error_duration_us,
                     (stats->before_lines >> 1) & 1U, stats->before_lines & 1U,
                     (stats->after_lines >> 1) & 1U, stats->after_lines & 1U);
        }
    }
}

uint8_t cy8cmbr3116_address(uint8_t chip)
{
    return chip < CY8_DEVICE_COUNT ? s_addresses[chip] : 0;
}

esp_err_t cy8cmbr3116_init(void)
{
    if (s_bus != NULL) return ESP_OK;
    const i2c_master_bus_config_t bus_config = {
        .i2c_port = I2C_NUM_0,
        .sda_io_num = TOUCH_SDA_GPIO,
        .scl_io_num = TOUCH_SCL_GPIO,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = true,
    };
    esp_err_t err = i2c_new_master_bus(&bus_config, &s_bus);
    if (err != ESP_OK) {
        TOUCH_LOGE(TAG, "INIT_FAIL SDA=%d SCL=%d err=%s",
                 TOUCH_SDA_GPIO, TOUCH_SCL_GPIO, esp_err_to_name(err));
        return err;
    }
    for (uint8_t chip = 0; chip < CY8_DEVICE_COUNT; ++chip) {
        if ((CY8_ACTIVE_MASK & (1U << chip)) == 0) continue;
        const i2c_device_config_t device_config = {
            .dev_addr_length = I2C_ADDR_BIT_LEN_7,
            .device_address = s_addresses[chip],
            .scl_speed_hz = CY8_I2C_FREQUENCY_HZ,
        };
        err = i2c_master_bus_add_device(s_bus, &device_config, &s_devices[chip]);
        if (err != ESP_OK) {
            TOUCH_LOGE(TAG, "ADD_FAIL chip=%u addr=0x%02X err=%s",
                     chip, s_addresses[chip], esp_err_to_name(err));
            for (uint8_t previous_chip = 0; previous_chip < chip; ++previous_chip) {
                if (s_devices[previous_chip] == NULL) continue;
                i2c_master_bus_rm_device(s_devices[previous_chip]);
                s_devices[previous_chip] = NULL;
            }
            i2c_del_master_bus(s_bus);
            s_bus = NULL;
            return err;
        }
    }
    s_next_summary_us = esp_timer_get_time() + CY8_SUMMARY_INTERVAL_US;
    TOUCH_LOGI(TAG, "R15-I2C-GUARD-v3.3 SDA=%d SCL=%d hz=%d api_timeout_ms=%d"
             " scl_wait=IDF_DEFAULT internal_pullup=ON addresses=0x37..0x3E"
             " active_mask=0x%02X attempts=1 retries=next_pass output=queued"
             " pre/post are API-boundary samples, not a fault waveform",
             TOUCH_SDA_GPIO, TOUCH_SCL_GPIO, CY8_I2C_FREQUENCY_HZ, CY8_I2C_TIMEOUT_MS,
             CY8_ACTIVE_MASK);
    return ESP_OK;
}

static esp_err_t cy8_read(uint8_t chip, uint8_t reg, uint8_t *data, size_t length)
{
    if (chip >= CY8_DEVICE_COUNT || data == NULL || length == 0 ||
        (CY8_ACTIVE_MASK & (1U << chip)) == 0) return ESP_ERR_INVALID_ARG;
    if (s_devices[chip] == NULL) return ESP_ERR_INVALID_STATE;
    int64_t request_start_us = esp_timer_get_time();
    uint8_t before_lines = bus_lines();
    int64_t start_us = esp_timer_get_time();
    esp_err_t err = i2c_master_transmit_receive(s_devices[chip], &reg, 1,
                                              data, length, CY8_I2C_TIMEOUT_MS);
    int64_t end_us = esp_timer_get_time();
    uint8_t after_lines = bus_lines();
    record_read(chip, reg, length, err, start_us, end_us, before_lines, after_lines);
    record_request(chip, reg, 1, err, request_start_us);
    return err;
}

static esp_err_t cy8_read_u16(uint8_t chip, uint8_t reg, uint16_t *value)
{
    if (value == NULL) return ESP_ERR_INVALID_ARG;
    uint8_t bytes[2];
    esp_err_t err = cy8_read(chip, reg, bytes, sizeof(bytes));
    if (err == ESP_OK) *value = (uint16_t)bytes[0] | ((uint16_t)bytes[1] << 8);
    return err;
}

esp_err_t cy8cmbr3116_read_device_id(uint8_t chip)
{
    uint16_t device_id;
    esp_err_t err = cy8_read_u16(chip, CY8_REG_DEVICE_ID, &device_id);
    if (err != ESP_OK) return err;
    if (device_id != CY8_DEVICE_ID_3116) {
        portENTER_CRITICAL(&s_diagnostics_lock);
        ++s_diagnostics[chip].verify_errors;
        portEXIT_CRITICAL(&s_diagnostics_lock);
        TOUCH_LOGE(TAG, "VERIFY_FAIL chip=%u addr=0x%02X device_id=0x%04X expected=0x%04X",
                 chip, s_addresses[chip], device_id, CY8_DEVICE_ID_3116);
        return ESP_ERR_INVALID_RESPONSE;
    }
    return ESP_OK;
}

esp_err_t cy8cmbr3116_read_sensor_enable(uint8_t chip, uint16_t *sensor_enable)
{
    return cy8_read_u16(chip, CY8_REG_SENSOR_EN, sensor_enable);
}

esp_err_t cy8cmbr3116_verify(uint8_t chip, uint16_t *sensor_enable)
{
    if (sensor_enable == NULL) return ESP_ERR_INVALID_ARG;
    esp_err_t err = cy8cmbr3116_read_device_id(chip);
    if (err != ESP_OK) return err;
    err = cy8cmbr3116_read_sensor_enable(chip, sensor_enable);
    if (err == ESP_OK) {
        TOUCH_LOGI(TAG, "VERIFY_OK chip=%u addr=0x%02X device_id=0x%04X sensor_en=0x%04X",
                   chip, s_addresses[chip], CY8_DEVICE_ID_3116, *sensor_enable);
    }
    return err;
}

esp_err_t cy8cmbr3116_read_buttons(uint8_t chip, uint16_t *button_state)
{
    return cy8_read_u16(chip, CY8_REG_BUTTON_STAT, button_state);
}

esp_err_t cy8cmbr3116_read_difference_counts(uint8_t chip,
                                           uint16_t counts[CY8_CHANNEL_COUNT])
{
    if (counts == NULL) return ESP_ERR_INVALID_ARG;
    for (uint8_t channel = 0; channel < CY8_CHANNEL_COUNT; ++channel) {
        esp_err_t err = cy8_read_u16(chip,
                                   (uint8_t)(CY8_REG_DIFF_COUNT_0 + 2U * channel),
                                   &counts[channel]);
        if (err != ESP_OK) return err;
    }
    return ESP_OK;
}

esp_err_t cy8cmbr3116_read_difference_count(uint8_t chip, uint8_t channel, uint16_t *count)
{
    if (channel >= CY8_CHANNEL_COUNT) return ESP_ERR_INVALID_ARG;
    return cy8_read_u16(chip, (uint8_t)(CY8_REG_DIFF_COUNT_0 + 2U * channel), count);
}
