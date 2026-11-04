#include "../main/fpga_link.c"
#include <setjmp.h>
#include <stdlib.h>

#define SIM_EXPORT __declspec(dllexport)
struct sim_queue {
    unsigned length, item_size, head, count;
    uint8_t items[32][32];
};
static struct sim_queue s_sim_queues[2];
static unsigned s_sim_queue_count, s_sim_ticks, s_sim_iterations, s_sim_limit;
static unsigned s_sim_transfers, s_sim_accepted, s_sim_crc_errors;
static uint8_t s_sim_transmitted[2048][64], s_sim_frames[2048][64], s_sim_last[64];
static unsigned s_sim_frame_ticks[2048], s_sim_cancel_transfer;
static uint16_t s_sim_buttons[8];
static uint8_t s_sim_online_mask;
static unsigned s_sim_panel_mode;
static bool s_sim_have_sequence, s_sim_snapshot_capable;
static bool s_sim_command_busy, s_sim_hall_busy, s_sim_hold_command, s_sim_hold_hall, s_sim_continuous_controls;
static unsigned s_sim_bad_replies, s_sim_mutation_transfer, s_sim_mutation_key;
static unsigned s_sim_led_picks, s_sim_led_last_string;
void led_indicator_pick(unsigned string_number) {++s_sim_led_picks;s_sim_led_last_string=string_number;}
static void (*s_sim_task)(void *);
static jmp_buf s_sim_exit;
static char s_sim_reply[1024];
static unsigned s_sim_bulk_mode;

QueueHandle_t xQueueCreate(unsigned length, unsigned item_size)
{
    if (s_sim_queue_count >= 2 || length > 32 || item_size > 32) return NULL;
    QueueHandle_t queue = &s_sim_queues[s_sim_queue_count++];
    queue->length = length;
    queue->item_size = item_size;
    return queue;
}
int xQueueSend(QueueHandle_t queue, const void *item, TickType_t wait)
{
    (void)wait;
    if (queue->count == queue->length) return pdFALSE;
    memcpy(queue->items[(queue->head + queue->count) % queue->length], item, queue->item_size);
    ++queue->count;
    return pdTRUE;
}
int xQueueReceive(QueueHandle_t queue, void *item, TickType_t wait)
{
    (void)wait;
    if (queue->count == 0) return pdFALSE;
    memcpy(item, queue->items[queue->head], queue->item_size);
    queue->head = (queue->head + 1) % queue->length;
    --queue->count;
    return pdTRUE;
}
unsigned uxQueueMessagesWaiting(QueueHandle_t queue) {return queue->count;}
int xQueuePeek(QueueHandle_t queue, void *item, TickType_t wait)
{
    (void)wait;
    if (queue->count == 0) return pdFALSE;
    memcpy(item, queue->items[queue->head], queue->item_size);
    return pdTRUE;
}
void touch_serial_snapshot(uint16_t buttons[8], uint8_t *online)
{
    memcpy(buttons, s_sim_buttons, sizeof(s_sim_buttons));
    *online = s_sim_online_mask;
}
static void sim_set_key(unsigned key)
{
    memset(s_sim_buttons, 0, sizeof(s_sim_buttons));
    if (key >= 1 && key <= TOUCH_LAYOUT_KEYS) {
        touch_source_t source = g_touch_layout[key - 1];
        s_sim_buttons[source.chip] = (uint16_t)(1U << source.channel);
    }
}
void touch_serial_write(const char *line) {size_t n=strlen(s_sim_reply);snprintf(s_sim_reply+n, sizeof(s_sim_reply)-n, "%s", line);}
void touch_output_log(esp_log_level_t level, const char *tag, const char *format, ...)
{
    (void)level; (void)tag; (void)format;
}
const char *esp_err_to_name(esp_err_t error) {(void)error; return "SIM_ERROR";}
TickType_t xTaskGetTickCount(void) {return s_sim_ticks;}
void vTaskDelay(TickType_t ticks)
{
    s_sim_ticks += ticks;
    if (s_sim_continuous_controls && uxQueueMessagesWaiting(s_commands) < 32) enqueue(0x70, 0, 80, 0);
    if (++s_sim_iterations >= s_sim_limit) longjmp(s_sim_exit, 1);
}
int xTaskCreate(void (*task)(void *), const char *name, unsigned stack, void *argument, unsigned priority, void *handle)
{
    (void)name; (void)stack; (void)argument; (void)priority; (void)handle;
    s_sim_task = task;
    return pdPASS;
}
esp_err_t gpio_config(const gpio_config_t *config) {(void)config; return ESP_OK;}
int gpio_set_level(int pin, unsigned level) {(void)pin; (void)level; return 0;}
int gpio_get_level(int pin) {(void)pin; return 1;}
void esp_rom_delay_us(unsigned microseconds) {(void)microseconds;}
uint32_t esp_random(void) {return 0x12345678;}
esp_err_t spi_bus_initialize(int host, const spi_bus_config_t *config, int dma)
{
    (void)host; (void)config; (void)dma;
    return ESP_OK;
}
esp_err_t spi_bus_add_device(int host, const spi_device_interface_config_t *config, spi_device_handle_t *device)
{
    (void)host; (void)config;
    *device = (void *)1;
    return ESP_OK;
}
/* Match the actual ESP-IDF SPI driver contract, not an always-success mock. */
esp_err_t spi_device_acquire_bus(spi_device_handle_t device, TickType_t wait) {(void)device; return wait==portMAX_DELAY?ESP_OK:ESP_ERR_INVALID_ARG;}
void spi_device_release_bus(spi_device_handle_t device) {(void)device;}
esp_err_t spi_device_polling_transmit(spi_device_handle_t device, spi_transaction_t *transaction)
{
    (void)device;
    const uint8_t *transmitted = transaction->tx_buffer;
    uint8_t *reply = transaction->rx_buffer;
    if (transaction->length != 512 || s_sim_transfers >= 2048) abort();
    memcpy(s_sim_transmitted[s_sim_transfers++], transmitted, 64);
    memset(reply, 0, 64);
    reply[0] = 0x5A; reply[1] = 0x53; reply[2] = 1;
    reply[3] = 1U | (s_sim_command_busy ? 0U : 2U);
    if(s_sim_bulk_mode)reply[3]|=0x30;
    if(s_sim_bulk_mode==2)reply[3]|=0x80;
    if(s_sim_bulk_mode==4)reply[3]|=0x40;
    reply[6] = s_sim_online_mask; reply[38] = 1; reply[39] = 0xA2;
    if (s_sim_have_sequence) {
        memcpy(reply + 4, s_sim_last + 4, 2);
        memcpy(reply + 56, s_sim_last + 56, 4);
        memcpy(reply + 16, s_sim_last + 8, 16);
    }
    if (s_sim_snapshot_capable) {
        reply[46] = FPGA_HALL_SNAPSHOT_TAG;
        reply[47] = (s_sim_command_busy ? 0U : 1U) | (s_sim_hall_busy ? 0U : 2U);
    }
    if (s_sim_panel_mode) {
        unsigned bank=(s_sim_transfers-1)%6;
        reply[48]=0xd0|bank; reply[49]=8;
        for(unsigned i=0;i<6 && bank*6+i<32;++i)reply[50+i]=(uint8_t)(bank*6+i);
        reply[60]=3; reply[61]=0x22;
        if(s_sim_panel_mode==2)reply[56]^=0x80;
    }
    uint16_t checksum = fpga_crc16(reply, 62);
    reply[62] = (uint8_t)(checksum >> 8); reply[63] = (uint8_t)checksum;
    if (s_sim_bad_replies != 0) {--s_sim_bad_replies; reply[63] ^= 1;}
    bool valid = fpga_crc16(transmitted, 62) == ((uint16_t)transmitted[62] << 8 | transmitted[63]);
    if (!valid) ++s_sim_crc_errors;
    bool duplicate = s_sim_have_sequence && fpga_frame_sequence(transmitted) == fpga_frame_sequence(s_sim_last) &&
        fpga_frame_session(transmitted) == fpga_frame_session(s_sim_last);
    bool available = transmitted[3] == 0 || (transmitted[3] == 1 && !s_sim_command_busy) ||
        (transmitted[3] == 2 && !s_sim_hall_busy) ||
        (transmitted[3] == 3 && s_sim_bulk_mode && s_sim_bulk_mode!=3);
    if (valid && !duplicate && available) {
        memcpy(s_sim_last, transmitted, 64);
        s_sim_frame_ticks[s_sim_accepted] = s_sim_ticks;
        memcpy(s_sim_frames[s_sim_accepted++], transmitted, 64);
        s_sim_have_sequence = true;
        if (transmitted[3] == 1 && s_sim_hold_command) s_sim_command_busy = true;
        if (transmitted[3] == 2 && s_sim_hold_hall) s_sim_hall_busy = true;
    }
    if (s_sim_mutation_transfer == s_sim_transfers) sim_set_key(s_sim_mutation_key);
    if (s_sim_cancel_transfer == s_sim_transfers) fpga_link_cancel_strums();
    return ESP_OK;
}
SIM_EXPORT int sim_link_reset(void)
{
    memset(s_sim_queues, 0, sizeof(s_sim_queues));
    memset(s_sim_last, 0, sizeof(s_sim_last));
    memset(s_sim_buttons, 0, sizeof(s_sim_buttons));
    memset(s_reply, 0, sizeof(s_reply));
    s_sim_queue_count = s_sim_ticks = s_sim_iterations = s_sim_transfers = s_sim_accepted = s_sim_crc_errors = 0;
    s_sim_bad_replies = s_sim_mutation_transfer = s_sim_mutation_key = 0;
    s_sim_led_picks=s_sim_led_last_string=0;
    s_sim_cancel_transfer = 0; s_sim_panel_mode=0; s_panel_mask=0; memset(s_panel_values,0,sizeof(s_panel_values));
    s_sim_have_sequence = s_sim_command_busy = s_sim_hall_busy = false;
    s_sim_hold_command = s_sim_hold_hall = s_sim_continuous_controls = false;
    s_sim_snapshot_capable = true;
    s_sim_online_mask = 0xFF;
    s_online = false; s_touch_enabled = true;
    s_strum_generation = 0;
    s_commands = s_picks = NULL;
    s_sim_reply[0] = 0;s_sim_bulk_mode=0;s_bulk_result=0;
    return fpga_link_start();
}
SIM_EXPORT void sim_link_run(unsigned iterations)
{
    s_sim_limit = iterations;
    if (setjmp(s_sim_exit) == 0) s_sim_task(NULL);
}
SIM_EXPORT void sim_link_online(int online) {s_online = online != 0;}
SIM_EXPORT unsigned sim_link_led_picks(void) {return s_sim_led_picks;}
SIM_EXPORT unsigned sim_link_led_string(void) {return s_sim_led_last_string;}
SIM_EXPORT void sim_link_key(unsigned key) {sim_set_key(key);}
SIM_EXPORT void sim_link_online_mask(unsigned mask) {s_sim_online_mask = (uint8_t)mask;}
SIM_EXPORT unsigned sim_link_key_chip(unsigned key) {return g_touch_layout[key - 1].chip;}
SIM_EXPORT int sim_link_pick(unsigned string_number, unsigned velocity) {return fpga_link_hall_trigger(string_number, velocity);}
SIM_EXPORT int sim_link_strum(unsigned velocity) {return fpga_link_hall_strum(velocity);}
SIM_EXPORT void sim_link_cancel_strums(void) {fpga_link_cancel_strums();}
SIM_EXPORT void sim_link_cancel_at(unsigned transfer) {s_sim_cancel_transfer = transfer;}
SIM_EXPORT void sim_link_ticks(unsigned ticks) {s_sim_ticks = ticks;}
SIM_EXPORT unsigned sim_link_accepted_tick(unsigned index) {return s_sim_frame_ticks[index];}
SIM_EXPORT const char *sim_link_host(const char *line) {s_sim_reply[0]=0;fpga_link_host_command(line); return s_sim_reply;}
SIM_EXPORT int sim_link_control(unsigned level) {return enqueue(0x70, 0, level, 0);}
SIM_EXPORT void sim_link_continuous_controls(int enabled) {s_sim_continuous_controls = enabled != 0;}
SIM_EXPORT void sim_link_hold_command(int hold) {s_sim_hold_command = hold != 0;}
SIM_EXPORT void sim_link_hold_hall(int hold) {s_sim_hold_hall = hold != 0;}
SIM_EXPORT void sim_link_bad_replies(unsigned count) {s_sim_bad_replies = count;}
SIM_EXPORT void sim_link_mutation(unsigned transfer, unsigned key) {s_sim_mutation_transfer = transfer; s_sim_mutation_key = key;}
SIM_EXPORT void sim_link_legacy_reply(void) {s_sim_snapshot_capable = false;}
SIM_EXPORT unsigned sim_link_accepted_count(void) {return s_sim_accepted;}
SIM_EXPORT unsigned sim_link_transfer_count(void) {return s_sim_transfers;}
SIM_EXPORT unsigned sim_link_accepted_byte(unsigned index, unsigned offset) {return s_sim_frames[index][offset];}
SIM_EXPORT unsigned sim_link_transmitted_byte(unsigned index, unsigned offset) {return s_sim_transmitted[index][offset];}
SIM_EXPORT unsigned sim_link_queue_count(unsigned kind) {return uxQueueMessagesWaiting(kind == 1 ? s_commands : s_picks);}
SIM_EXPORT unsigned sim_link_crc_errors(void) {return s_sim_crc_errors;}
SIM_EXPORT const char *sim_link_status(void) {s_sim_reply[0]=0;fpga_link_host_command("FPGA,STATUS"); return s_sim_reply;}

SIM_EXPORT void sim_link_panel(unsigned mode) {s_sim_panel_mode=mode;}

void ble_control_log(const char *line) {(void)line;}
void ble_control_event(const char *line) {(void)line;}

SemaphoreHandle_t xSemaphoreCreateMutex(void){return (void*)1;}
SemaphoreHandle_t xSemaphoreCreateBinary(void){return (void*)2;}
int xSemaphoreTake(SemaphoreHandle_t h,TickType_t t){(void)h;(void)t;return pdTRUE;}
int xSemaphoreGive(SemaphoreHandle_t h){(void)h;return pdTRUE;}

SIM_EXPORT int sim_link_bulk(const uint8_t *bytes,unsigned length,unsigned mode) {
    if(length>266)return -1;
    s_sim_bulk_mode=mode;s_reply[3]=mode?0x31:1;s_bulk_result=0;
    memcpy(s_bulk_packet,bytes,length);s_bulk_length=length;s_sim_limit=100000;
    uint16_t sequence=1;return bulk_transfer(0x12345678,&sequence);
}
SIM_EXPORT const char *sim_link_bulk_error(void){return fpga_link_bulk_error();}
