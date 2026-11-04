#include "../main/hall_adc.c"
#include "../main/control_line.h"
#include "../main/fpga_protocol.h"
#include <stdarg.h>

#define SIM_EXPORT __declspec(dllexport)
static unsigned s_sim_applied_mask;
static unsigned s_sim_time_ms;
static unsigned s_sim_picks;
static unsigned s_sim_strums, s_sim_cancellations;
static unsigned s_sim_string, s_sim_velocity;
static int s_sim_raw[7], s_sim_error[7];
static unsigned s_sim_reads[7];
static bool s_sim_online;
static char s_sim_reply[256];
static char s_sim_status[4096];
static control_line_t s_sim_line;

int64_t esp_timer_get_time(void) {return (int64_t)s_sim_time_ms * 1000;}
const char *esp_err_to_name(esp_err_t error) {(void)error; return "SIM_ERROR";}
void vTaskDelay(TickType_t ticks) {(void)ticks;}
int xTaskCreate(void (*task)(void *), const char *name, unsigned stack, void *argument, unsigned priority, void *handle)
{
    (void)task; (void)name; (void)stack; (void)argument; (void)priority; (void)handle;
    return pdPASS;
}
void touch_serial_write(const char *line)
{
    snprintf(s_sim_reply, sizeof(s_sim_reply), "%s", line);
    size_t used = strlen(s_sim_status);
    snprintf(s_sim_status + used, sizeof(s_sim_status) - used, "%s", line);
}
void touch_output_log(esp_log_level_t level, const char *tag, const char *format, ...)
{
    (void)level; (void)tag; (void)format;
}
bool fpga_link_hall_trigger(unsigned string_number, unsigned velocity)
{
    ++s_sim_picks;
    s_sim_string = string_number;
    s_sim_velocity = velocity;
    return s_sim_online;
}
bool fpga_link_hall_strum(unsigned velocity)
{
    ++s_sim_strums;
    return fpga_link_hall_trigger(0, velocity);
}
void fpga_link_cancel_strums(void) {++s_sim_cancellations;}
esp_err_t adc_oneshot_new_unit(const adc_oneshot_unit_init_cfg_t *config, adc_oneshot_unit_handle_t *handle)
{
    *handle = (void *)(uintptr_t)config->unit_id;
    return ESP_OK;
}
esp_err_t adc_oneshot_config_channel(adc_oneshot_unit_handle_t handle, adc_channel_t channel, const adc_oneshot_chan_cfg_t *config)
{
    (void)handle; (void)channel; (void)config;
    return ESP_OK;
}
esp_err_t adc_oneshot_del_unit(adc_oneshot_unit_handle_t handle) {(void)handle; return ESP_OK;}
esp_err_t adc_oneshot_read(adc_oneshot_unit_handle_t handle, adc_channel_t channel, int *raw)
{
    unsigned index = (uintptr_t)handle == ADC_UNIT_1 ? (unsigned)channel : (unsigned)channel - 1;
    ++s_sim_reads[index];
    if (s_sim_error[index]) return ESP_ERR_INVALID_RESPONSE;
    *raw = s_sim_raw[index];
    return ESP_OK;
}
SIM_EXPORT int sim_hall_reset(void)
{
    s_sim_applied_mask = s_sim_time_ms = s_sim_picks = s_sim_string = s_sim_velocity = 0;
    s_sim_strums = s_sim_cancellations = 0;
    s_armed = s_started = s_calibrate = false;
    s_active_mask = CONFIG_HALL_ACTIVE_MASK;
    s_sim_online = true;
    s_valid_mask = 0;
    memset(s_events, 0, sizeof(s_events));
    memset(s_rejected, 0, sizeof(s_rejected));
    memset(s_errors, 0, sizeof(s_errors));
    memset(s_sim_reads, 0, sizeof(s_sim_reads));
    memset(s_sim_error, 0, sizeof(s_sim_error));
    memset(&s_sim_line, 0, sizeof(s_sim_line));
    for (unsigned channel = 0; channel < 7; ++channel) s_sim_raw[channel] = 1500;
    return hall_adc_start();
}
SIM_EXPORT void sim_hall_step(unsigned count)
{
    for (unsigned index = 0; index < count; ++index) {
        hall_sample_once(&s_sim_applied_mask);
        ++s_sim_time_ms;
    }
}
SIM_EXPORT int sim_hall_command(const char *line)
{
    s_sim_status[0] = 0;
    return hall_adc_host_command(line);
}
SIM_EXPORT const char *sim_hall_reply(void) {return s_sim_reply;}
SIM_EXPORT const char *sim_hall_status(void) {return s_sim_status;}
SIM_EXPORT void sim_hall_raw(unsigned channel, int raw) {s_sim_raw[channel] = raw;}
SIM_EXPORT void sim_hall_error(unsigned channel, int error) {s_sim_error[channel] = error;}
SIM_EXPORT void sim_hall_online(int online) {s_sim_online = online != 0;}
SIM_EXPORT unsigned sim_hall_picks(void) {return s_sim_picks;}
SIM_EXPORT unsigned sim_hall_strums(void) {return s_sim_strums;}
SIM_EXPORT unsigned sim_hall_cancellations(void) {return s_sim_cancellations;}
SIM_EXPORT unsigned sim_hall_string(void) {return s_sim_string;}
SIM_EXPORT unsigned sim_hall_velocity(void) {return s_sim_velocity;}
SIM_EXPORT unsigned sim_hall_valid(void) {return s_valid_mask;}
SIM_EXPORT unsigned sim_hall_reads(unsigned channel) {return s_sim_reads[channel];}
SIM_EXPORT unsigned sim_hall_rejected(unsigned channel) {return s_rejected[channel];}
SIM_EXPORT unsigned sim_hall_errors(unsigned channel) {return s_errors[channel];}
SIM_EXPORT unsigned sim_hall_threshold(unsigned channel) {return s_detector[channel].threshold;}
SIM_EXPORT unsigned sim_hall_baseline(unsigned channel) {return (unsigned)(s_detector[channel].baseline_q8 >> 8);}
SIM_EXPORT unsigned sim_hall_state(unsigned channel) {return s_detector[channel].state;}
SIM_EXPORT unsigned sim_hall_events(unsigned channel) {return s_events[channel];}
SIM_EXPORT unsigned sim_hall_noise(unsigned channel) {return s_detector[channel].noise;}
SIM_EXPORT unsigned sim_hall_calibration(unsigned channel) {return s_detector[channel].calibration;}
SIM_EXPORT unsigned sim_hall_raw_peak(unsigned channel) {return s_detector[channel].raw_peak;}
SIM_EXPORT unsigned sim_hall_filtered_peak(unsigned channel) {return s_detector[channel].filtered_peak;}
SIM_EXPORT int sim_line_byte(unsigned byte) {return control_line_feed(&s_sim_line, (uint8_t)byte);}
SIM_EXPORT const char *sim_line_text(void) {return s_sim_line.text;}
SIM_EXPORT int sim_fixed_command(unsigned opcode, unsigned mode)
{
    uint8_t command[6] = {0xa5, opcode, mode, 0, 0, 0xa5 ^ opcode ^ mode};
    return fpga_fixed_command_valid(command);
}
