#define open sim_vfs_open
#define read sim_vfs_read
#define close sim_vfs_close
#include "../main/host_usb.c"
#include <stdio.h>

#define SIM_EXPORT __declspec(dllexport)
static char s_sim_path[64], s_sim_reply[256], s_sim_command[128];
static int s_sim_open_failure, s_sim_task_failure, s_sim_tasks, s_sim_closes, s_sim_flags, s_sim_commands;
static bool s_sim_driver_installed;
static int s_sim_driver_installs, s_sim_driver_failure, s_sim_vfs_driver;
static unsigned s_sim_rx_size, s_sim_tx_size;

int sim_vfs_open(const char *path, int flags, ...)
{
    if (!s_sim_driver_installed || !s_sim_vfs_driver) {errno = EIO; return -1;}
    snprintf(s_sim_path, sizeof(s_sim_path), "%s", path);
    s_sim_flags = flags;
    if (s_sim_open_failure) {errno = ENOENT; return -1;}
    return 7;
}
int sim_vfs_read(int descriptor, void *buffer, size_t size)
{
    (void)descriptor; (void)buffer; (void)size;
    return 0;
}
int sim_vfs_close(int descriptor) {(void)descriptor; ++s_sim_closes; return 0;}
void vTaskDelay(TickType_t ticks) {(void)ticks;}
const char *esp_err_to_name(esp_err_t error) {(void)error; return "SIM_ERROR";}
bool usb_serial_jtag_is_driver_installed(void) {return s_sim_driver_installed;}
esp_err_t usb_serial_jtag_driver_install(usb_serial_jtag_driver_config_t *config)
{
    ++s_sim_driver_installs;
    if (s_sim_driver_failure) return ESP_ERR_NO_MEM;
    s_sim_driver_installed = true;
    s_sim_rx_size = config->rx_buffer_size;
    s_sim_tx_size = config->tx_buffer_size;
    return ESP_OK;
}
void usb_serial_jtag_vfs_use_driver(void) {s_sim_vfs_driver = s_sim_driver_installed;}
int xTaskCreate(void (*task)(void *), const char *name, unsigned stack, void *argument, unsigned priority, void *handle)
{
    (void)task; (void)name; (void)stack; (void)argument; (void)priority; (void)handle;
    ++s_sim_tasks;
    return s_sim_task_failure ? 0 : pdPASS;
}
void touch_output_log(esp_log_level_t level, const char *tag, const char *format, ...)
{
    (void)level; (void)tag; (void)format;
}
void touch_serial_write(const char *line) {snprintf(s_sim_reply, sizeof(s_sim_reply), "%s", line);}
static bool sim_command(const char *line)
{
    ++s_sim_commands;
    snprintf(s_sim_command, sizeof(s_sim_command), "%s", line);
    return strcmp(line, "HALL,UNKNOWN") != 0;
}
SIM_EXPORT void sim_usb_reset(void)
{
    s_usb = -1;
    s_handler = NULL;
    s_sim_path[0] = s_sim_reply[0] = s_sim_command[0] = 0;
    s_sim_open_failure = s_sim_task_failure = s_sim_tasks = s_sim_closes = s_sim_flags = s_sim_commands = 0;
    s_sim_driver_installed = false;
    s_sim_driver_installs = s_sim_driver_failure = s_sim_vfs_driver = 0;
    s_sim_rx_size = s_sim_tx_size = 0;
}
SIM_EXPORT int sim_usb_start(void) {return host_usb_start(sim_command);}
SIM_EXPORT void sim_usb_open_failure(int failure) {s_sim_open_failure = failure;}
SIM_EXPORT void sim_usb_task_failure(int failure) {s_sim_task_failure = failure;}
SIM_EXPORT const char *sim_usb_path(void) {return s_sim_path;}
SIM_EXPORT const char *sim_usb_reply(void) {return s_sim_reply;}
SIM_EXPORT const char *sim_usb_command(void) {return s_sim_command;}
SIM_EXPORT int sim_usb_tasks(void) {return s_sim_tasks;}
SIM_EXPORT int sim_usb_closes(void) {return s_sim_closes;}
SIM_EXPORT int sim_usb_commands(void) {return s_sim_commands;}
SIM_EXPORT int sim_usb_nonblocking(void) {return (s_sim_flags & O_NONBLOCK) != 0;}
SIM_EXPORT void sim_usb_line(const char *line) {usb_dispatch_line(line);}
SIM_EXPORT void sim_usb_existing_driver(void) {s_sim_driver_installed = true;}
SIM_EXPORT void sim_usb_driver_failure(void) {s_sim_driver_failure = 1;}
SIM_EXPORT int sim_usb_driver_installs(void) {return s_sim_driver_installs;}
SIM_EXPORT int sim_usb_rx_ready(void) {return s_sim_driver_installed && s_sim_vfs_driver && s_sim_tasks == 1 && s_usb >= 0;}
SIM_EXPORT unsigned sim_usb_rx_size(void) {return s_sim_rx_size;}
SIM_EXPORT unsigned sim_usb_tx_size(void) {return s_sim_tx_size;}
