#include "fpga_link.h"
#include "fpga_protocol.h"
#include "fpga_scheduler.h"
#include "touch_layout.h"
#include "touch_serial.h"
#include "touch_output.h"
#include "note_trace.h"
#include "ble_control.h"
#include "led_indicator.h"
#include <stdio.h>
#include <stdatomic.h>
#include <string.h>
#include "driver/gpio.h"
#include "driver/spi_master.h"
#include "esp_log.h"
#include "esp_random.h"
#include "esp_rom_sys.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"
#include "freertos/task.h"

#define FPGA_CS 10
#define FPGA_MOSI 11
#define FPGA_SCLK 12
#define FPGA_MISO 13
#define FPGA_IRQ 8
#define FPGA_READY 9
#define STRUM_INTERVAL_MS 8

static const char *TAG = "FPGA_LINK";
static spi_device_handle_t s_spi;
static QueueHandle_t s_commands;
static QueueHandle_t s_picks;
static portMUX_TYPE s_lock = portMUX_INITIALIZER_UNLOCKED;
static uint8_t s_reply[64];
static uint8_t s_panel_values[32],s_panel_mask;
static _Atomic bool s_online;
static _Atomic bool s_touch_enabled = true;
static _Atomic unsigned s_strum_generation;
typedef struct {
    uint8_t string_number;
    uint8_t velocity;
    uint8_t keys[16];
    bool strum;
    unsigned generation;
} fpga_pick_t;

static void build_keys(uint8_t keys[16], uint8_t *online)
{
    uint16_t buttons[8];
    touch_serial_snapshot(buttons, online);
    memset(keys, 0, 16);
    for (unsigned i = 0; i < TOUCH_LAYOUT_KEYS; ++i) {
        touch_source_t src = g_touch_layout[i];
        /* Do not transmit stale held keys belonging to disconnected chips. */
        if ((*online & (1U << src.chip)) && (buttons[src.chip] & (1U << src.channel))) {
            keys[i / 8U] |= (uint8_t)(1U << (i % 8U));
        }
    }
}


/* One outstanding raw packet. Fixed/Hall scheduling resumes between packets. */
static uint8_t s_bulk_packet[266];
static unsigned s_bulk_length;
static _Atomic bool s_bulk_pending, s_bulk_ok;
static SemaphoreHandle_t s_bulk_mutex, s_bulk_done;
enum { BULK_OK, BULK_ARGUMENT, BULK_OFFLINE, BULK_LOCK_TIMEOUT, BULK_PENDING,
       BULK_NO_CAPABILITY, BULK_FRAGMENT_TIMEOUT, BULK_FPGA_ERROR, BULK_REPLAY_TIMEOUT };
static _Atomic unsigned s_bulk_result;
const char *fpga_link_bulk_error(void)
{
    static const char *names[]={"OK","ARGUMENT","OFFLINE","LOCK_TIMEOUT","PENDING",
        "NO_CAPABILITY","FRAGMENT_ACK_TIMEOUT","FPGA_PACKET_ERROR","REPLAY_TIMEOUT"};
    unsigned code=s_bulk_result;
    return code<sizeof(names)/sizeof(names[0])?names[code]:"UNKNOWN";
}
unsigned fpga_link_reply_flags(void)
{
    portENTER_CRITICAL(&s_lock);unsigned flags=s_reply[3];portEXIT_CRITICAL(&s_lock);
    return flags;
}

bool fpga_link_bulk_send(const uint8_t *data, unsigned length)
{
    if (length<6 || length>266) {s_bulk_result=BULK_ARGUMENT;return false;}
    if (!s_bulk_mutex || !s_online) {s_bulk_result=BULK_OFFLINE;return false;}
    if (xSemaphoreTake(s_bulk_mutex,pdMS_TO_TICKS(100))!=pdTRUE) {s_bulk_result=BULK_LOCK_TIMEOUT;return false;}
    if (s_bulk_pending) {s_bulk_result=BULK_PENDING;xSemaphoreGive(s_bulk_mutex);return false;}
    s_bulk_result=BULK_OK;
    xSemaphoreTake(s_bulk_done,0);
    memcpy(s_bulk_packet,data,length);s_bulk_length=length;s_bulk_ok=false;s_bulk_pending=true;
    /* Link worker has its own bounded deadline; wait for its completion so a
       timed-out caller never overwrites a buffer still being read. */
    xSemaphoreTake(s_bulk_done,portMAX_DELAY);
    bool ok=s_bulk_ok;xSemaphoreGive(s_bulk_mutex);return ok;
}
static bool bulk_exchange(uint8_t tx[64],uint8_t rx[64],uint32_t session,uint16_t sequence)
{
    TickType_t until=xTaskGetTickCount()+pdMS_TO_TICKS(500);
    unsigned attempts=0,valid_replies=0;esp_err_t last_error=ESP_OK;
    memset(rx,0,64);
    do {
        spi_transaction_t t={.length=512,.tx_buffer=tx,.rx_buffer=rx};
        /* ESP-IDF requires portMAX_DELAY here. This sole SPI worker also
         * owns the ordinary heartbeat path; finite waits are rejected before
         * any clocks are sent, rather than acting as a bus-lock timeout. */
        esp_err_t e=spi_device_acquire_bus(s_spi,portMAX_DELAY);
        if(e==ESP_OK) {
            gpio_set_level(FPGA_CS,0);esp_rom_delay_us(2);
            e=spi_device_polling_transmit(s_spi,&t);esp_rom_delay_us(2);
            gpio_set_level(FPGA_CS,1);spi_device_release_bus(s_spi);
        }
        ++attempts;last_error=e;
        if(e==ESP_OK&&fpga_reply_valid(rx))++valid_replies;
        if(e==ESP_OK && fpga_reply_valid(rx) && fpga_frame_session(rx)==session && fpga_frame_sequence(rx)==sequence){
            portENTER_CRITICAL(&s_lock);memcpy(s_reply,rx,64);portEXIT_CRITICAL(&s_lock);
            return true;
        }
        vTaskDelay(pdMS_TO_TICKS(2));
    }while((int32_t)(until-xTaskGetTickCount())>0);
    TOUCH_LOGW("FPGA_BULK","TIMEOUT kind=%u seq=%u session=%08lX attempts=%u valid=%u SPI=%s rxseq=%u rxsession=%08lX flags=%02X good=%lu bad=%lu txhead=%02X%02X%02X%02X%02X%02X%02X%02X crc=%02X%02X",
        tx[3],sequence,(unsigned long)session,attempts,valid_replies,esp_err_to_name(last_error),fpga_frame_sequence(rx),(unsigned long)fpga_frame_session(rx),rx[3],
        (unsigned long)((uint32_t)rx[8]|(uint32_t)rx[9]<<8|(uint32_t)rx[10]<<16|(uint32_t)rx[11]<<24),
        (unsigned long)((uint32_t)rx[12]|(uint32_t)rx[13]<<8|(uint32_t)rx[14]<<16|(uint32_t)rx[15]<<24),
        tx[0],tx[1],tx[2],tx[3],tx[4],tx[5],tx[6],tx[7],tx[62],tx[63]);
    return false;
}
static bool bulk_transfer(uint32_t session,uint16_t *sequence)
{
    uint8_t rx[64],tx[64];bool capable;
    portENTER_CRITICAL(&s_lock);capable=(s_reply[3]&0x10)!=0;portEXIT_CRITICAL(&s_lock);
    if(!capable){s_bulk_result=BULK_NO_CAPABILITY;return false;}
    for(unsigned offset=0;offset<s_bulk_length;) {
        unsigned n=s_bulk_length-offset;if(n>48)n=48;
        memset(tx,0,64);tx[0]=0xa5;tx[1]=0x53;tx[2]=1;tx[3]=3;
        tx[4]=*sequence;tx[5]=*sequence>>8;
        tx[6]=(offset==0?1:0)|(offset+n==s_bulk_length?2:0);tx[7]=n;
        memcpy(tx+8,s_bulk_packet+offset,n);
        for(unsigned k=0;k<4;++k)tx[56+k]=(uint8_t)(session>>(k*8));
        uint16_t crc=fpga_crc16(tx,62);tx[62]=crc>>8;tx[63]=crc;
        if(!bulk_exchange(tx,rx,session,*sequence)){s_bulk_result=BULK_FRAGMENT_TIMEOUT;return false;}
        ++*sequence;offset+=n;
    }
    /* Pump ordinary heartbeat frames until validation/replay finishes. */
    TickType_t until=xTaskGetTickCount()+pdMS_TO_TICKS(1500);
    do {
        uint8_t online,keys[16];build_keys(keys,&online);
        fpga_frame_build(tx,session,*sequence,online,keys,NULL);tx[30]=s_touch_enabled?1:0;
        uint16_t crc=fpga_crc16(tx,62);tx[62]=crc>>8;tx[63]=crc;
        if(!bulk_exchange(tx,rx,session,*sequence)){s_bulk_result=BULK_FRAGMENT_TIMEOUT;return false;}
        ++*sequence;
        if(!(rx[3]&0x40) && (rx[3]&0x20)){s_bulk_result=(rx[3]&0x80)?BULK_FPGA_ERROR:BULK_OK;return !(rx[3]&0x80);}
        vTaskDelay(pdMS_TO_TICKS(2));
    }while((int32_t)(until-xTaskGetTickCount())>0);
    s_bulk_result=BULK_REPLAY_TIMEOUT;return false;
}

static void link_task(void *arg)
{
    (void)arg;
    uint32_t session = esp_random();
    if (session == 0) session = 1;
    uint16_t sequence = 1;
    uint8_t tx[64], rx[64], command[6];
    fpga_pick_t pick;
    fpga_pick_t strum = {0};
    unsigned strum_remaining = 0;
    TickType_t next_strum_tick = 0;
    bool pending_strum = false, prefer_strum = false;
    fpga_scheduler_t scheduler = {0};
    bool command_slot_ready = true, hall_slot_ready = true;
    bool pending = false, pending_command = false;
    bool pending_pick = false;
    bool pending_trace = false;
    bool trace_initialized = false;
    uint8_t traced_keys[16] = {0};
    uint8_t traced_online = 0;
    note_trace_state_t note_trace = {0};
    TickType_t last_ack = xTaskGetTickCount(), last_warning = last_ack;
    for (;;) {
        if (s_bulk_pending && !s_online) {s_bulk_result=BULK_OFFLINE;s_bulk_ok=false;s_bulk_pending=false;xSemaphoreGive(s_bulk_done);}
        if (!pending && s_bulk_pending) {
            s_bulk_ok=bulk_transfer(session,&sequence);s_bulk_pending=false;xSemaphoreGive(s_bulk_done);
        }
        if (!pending) {
            uint8_t keys[16], online;
            build_keys(keys, &online);
            unsigned generation = s_strum_generation;
            if (strum.generation != generation) strum_remaining = 0;
            fpga_pick_t queued_pick;
            bool queued = xQueuePeek(s_picks, &queued_pick, 0) == pdTRUE;
            while (queued && queued_pick.strum && queued_pick.generation != generation) {
                xQueueReceive(s_picks, &queued_pick, 0);
                queued = xQueuePeek(s_picks, &queued_pick, 0) == pdTRUE;
            }
            bool queued_ready = queued && (!queued_pick.strum || strum_remaining == 0);
            bool strum_ready = strum_remaining != 0 &&
                (int32_t)(xTaskGetTickCount() - next_strum_tick) >= 0;
            fpga_schedule_kind_t scheduled = fpga_schedule_next(&scheduler,
                command_slot_ready && uxQueueMessagesWaiting(s_commands) != 0,
                hall_slot_ready && (strum_ready || queued_ready));
            pending_command = scheduled == FPGA_SCHEDULE_COMMAND && xQueueReceive(s_commands, command, 0) == pdTRUE;
            pending_pick = pending_strum = false;
            if (scheduled == FPGA_SCHEDULE_PICK) {
                if (strum_ready && (!queued_ready || prefer_strum)) {
                    pick = strum;
                    pending_pick = pending_strum = true;
                } else if (queued_ready && xQueueReceive(s_picks, &pick, 0) == pdTRUE) {
                    pending_pick = true;
                    if (pick.strum) {
                        strum = pick;
                        strum_remaining = 6;
                        pending_strum = true;
                    }
                }
                prefer_strum = !pending_strum;
            }
            fpga_frame_build(tx, session, sequence, online, keys, pending_command ? command : NULL);
            tx[30] = s_touch_enabled ? 1 : 0;
            if (pending_pick) {
                fpga_frame_attach_pick(tx, pick.string_number, pick.velocity, pick.keys);
            }
            uint16_t crc = fpga_crc16(tx, 62);
            tx[62] = (uint8_t)(crc >> 8); tx[63] = (uint8_t)crc;
            if (!trace_initialized || memcmp(keys, traced_keys, sizeof(keys)) != 0 ||
                online != traced_online || pending_command || pending_pick) {
                char key_text[33];
                for (unsigned index = 0; index < sizeof(keys); ++index) {
                    snprintf(key_text + index * 2, 3, "%02X", keys[index]);
                }
                TOUCH_LOGI("FPGA_TRACE", "FRAME seq=%u online=0x%02X keys_le=%s cmd=0x%02X pick=%u velocity=%u",
                           sequence, online, key_text, pending_command ? command[1] : 0,
                           pending_pick ? pick.string_number : 0, pending_pick ? pick.velocity : 0);
                memcpy(traced_keys, keys, sizeof(keys));
                traced_online = online;
                trace_initialized = true;
                pending_trace = true;
            }
            pending = true;
        }
        spi_transaction_t transaction = { .length = 64 * 8, .tx_buffer = tx, .rx_buffer = rx };
        esp_err_t err = spi_device_acquire_bus(s_spi, portMAX_DELAY);
        if (err == ESP_OK) {
            /* IDF full-duplex does not support cs_ena_pretrans. Manual CS
             * guarantees setup/hold for the FPGA's 50 MHz synchronizers. */
            gpio_set_level(FPGA_CS, 0);
            esp_rom_delay_us(2);
            err = spi_device_polling_transmit(s_spi, &transaction);
            esp_rom_delay_us(2);
            gpio_set_level(FPGA_CS, 1);
            spi_device_release_bus(s_spi);
        }
        TickType_t now = xTaskGetTickCount();
        bool valid = err == ESP_OK && fpga_reply_valid(rx);
        bool ack = valid && fpga_frame_session(rx) == session && fpga_frame_sequence(rx) == sequence;
        if (valid) {
            portENTER_CRITICAL(&s_lock);
            memcpy(s_reply, rx, 64);
            if (fpga_frame_session(rx) == session && (rx[48] & 0xf8) == 0xd0 && rx[49] == 8 && (rx[48] & 7) < 6) {
                unsigned bank = rx[48] & 7;
                for (unsigned i=0;i<6 && bank*6+i<32;++i) s_panel_values[bank*6+i]=rx[50+i];
                s_panel_mask |= (uint8_t)(1U<<bank);
            }
            portEXIT_CRITICAL(&s_lock);
        }
        if (ack) {
            command_slot_ready = fpga_command_slot_ready(rx);
            hall_slot_ready = fpga_hall_slot_ready(rx);
            note_trace_ack(&note_trace, sequence, rx + 16, rx[7], rx[38] != 0, tx[30] != 0);
            if (pending_trace) {
                TOUCH_LOGI("FPGA_TRACE", "ACK seq=%u", sequence);
                pending_trace = false;
            }
            if (!s_online) ESP_LOGI(TAG, "ONLINE: CRC/session/sequence verified");
            s_online = true;
            last_ack = now;
            if (pending_command) {
                ESP_LOGI(TAG, "ACK command 0x%02X seq=%u (accepted, not an audio completion)", command[1], sequence);
            }
            if (pending_pick) led_indicator_pick(pick.string_number);
            if (pending_pick) {char event[48];snprintf(event,sizeof(event),"HIT,%u,%u\n",pick.string_number,pick.velocity);ble_control_event(event);}
            if (pending_pick) TOUCH_LOGI(TAG, "ACK pick string=%u velocity=%u seq=%u", pick.string_number, pick.velocity, sequence);
            if (pending_strum) {
                --strum_remaining;
                --strum.string_number;
                next_strum_tick = now + pdMS_TO_TICKS(STRUM_INTERVAL_MS);
            }
            ++sequence;
            pending = false;
        }
        if ((now - last_ack) > pdMS_TO_TICKS(1000)) {s_online = false;portENTER_CRITICAL(&s_lock);s_panel_mask=0;portEXIT_CRITICAL(&s_lock);}
        if ((now - last_warning) > pdMS_TO_TICKS(2000) && !s_online) {
            ESP_LOGW(TAG, "No verified ACK; retrying seq=%u, IRQ=%d READY=%d SPI=%s. Check FPGA bitstream/wiring",
                     sequence, gpio_get_level(FPGA_IRQ), gpio_get_level(FPGA_READY), esp_err_to_name(err));
            last_warning = now;
        }
        /* Polling works with the four SPI wires only; IRQ/READY are optional.
         * FPGA cannot originate clocks. Pending commands are never dropped
         * or automatically changed after an uncertain acknowledgement. */
        vTaskDelay(pdMS_TO_TICKS(2));
    }
}

static bool enqueue(uint8_t opcode, unsigned a, unsigned b, unsigned c)
{
    if (s_commands == NULL || !s_online || a > 255 || b > 255 || c > 255) return false;
    uint8_t command[6] = {0xA5, opcode, (uint8_t)a, (uint8_t)b, (uint8_t)c, 0};
    for (unsigned i = 0; i < 5; ++i) command[5] ^= command[i];
    return fpga_fixed_command_valid(command) && xQueueSend(s_commands, command, 0) == pdTRUE;
}

bool fpga_link_host_command(const char *line)
{
    if (strncmp(line, "FPGA,", 5) != 0) return false;
    unsigned a = 0, b = 0, c = 0; char extra;
    bool ok = false;
    if (strcmp(line, "FPGA,TOUCH,ON") == 0 || strcmp(line, "FPGA,TOUCH,OFF") == 0) {
        s_touch_enabled = strcmp(line, "FPGA,TOUCH,ON") == 0;
        touch_serial_write(s_touch_enabled ? "OK,FPGA,TOUCH,ON\r\n" : "OK,FPGA,TOUCH,OFF\r\n");
        return true;
    }
    if (strcmp(line, "FPGA,PANEL") == 0) {
        uint8_t values[32],mask,page,motion;
        portENTER_CRITICAL(&s_lock);
        memcpy(values,s_panel_values,32);mask=s_panel_mask;page=s_reply[60];motion=s_reply[61];
        portEXIT_CRITICAL(&s_lock);
        if(!s_online || mask!=0x3f) { touch_serial_write("PANEL,WAIT\r\n");return true; }
        char message[192];
        int used=snprintf(message,sizeof(message),"PANEL,8,%u,%u",page,motion);
        for(unsigned i=0;i<32 && used>0 && (size_t)used<sizeof(message);++i)
            used+=snprintf(message+used,sizeof(message)-(size_t)used,",%u",values[i]);
        if(used>0 && (size_t)used+2<sizeof(message)) {message[used++]='\r';message[used++]='\n';message[used]='\0';touch_serial_write(message);}
        return true;
    }
    if (strcmp(line, "FPGA,STATUS") == 0) {
        uint8_t reply[64];
        portENTER_CRITICAL(&s_lock);
        memcpy(reply, s_reply, 64);
        portEXIT_CRITICAL(&s_lock);
        char message[512];
        snprintf(message, sizeof(message), "FPGA,%s,ACK,%u,ONLINE,0x%02X,RGB,%u,%u,%u,PIXEL,%u,%u,PAGE,%u,MODE,%s,FRETS,%u,%u,%u,%u,%u,%u,TRIGGER_CAP,%u,OVERRIDE,%u,SNAPSHOT_CAP,%u,CTRL_READY,%u,HALL_READY,%u,CTRL_QUEUE,%u,PICK_QUEUE,%u,TOUCH_ENABLED,%u\r\n",
                 s_online ? "ONLINE" : "OFFLINE", fpga_frame_sequence(reply), reply[6],
                 reply[32], reply[33], reply[34], reply[35], reply[36], reply[37],
                 reply[38] ? "PICK" : "DIRECT", reply[40], reply[41], reply[42], reply[43], reply[44], reply[45],
                 (reply[39] & 0xfc) == 0xa0, reply[39] & 3,
                 reply[46] == FPGA_HALL_SNAPSHOT_TAG, fpga_command_slot_ready(reply), fpga_hall_slot_ready(reply),
                 s_commands != NULL ? (unsigned)uxQueueMessagesWaiting(s_commands) : 0,
                 s_picks != NULL ? (unsigned)uxQueueMessagesWaiting(s_picks) : 0, (unsigned)s_touch_enabled);
        touch_serial_write(message);
        char bulk[112];snprintf(bulk,sizeof(bulk),"FPGA,BULK,FLAGS,0x%02X,CAP,%u,BUSY,%u,ERROR,%u,LAST,%s\r\n",reply[3],!!(reply[3]&16),!!(reply[3]&64),!!(reply[3]&128),fpga_link_bulk_error());
        touch_serial_write(bulk);
        return true;
    }
    if (strcmp(line, "FPGA,TRIGGER,AUTO") == 0) {
        ok = enqueue(0x09, 0, 0, 0);
    } else if (strcmp(line, "FPGA,TRIGGER,DIRECT") == 0) {
        ok = enqueue(0x09, 1, 0, 0);
    } else if (strcmp(line, "FPGA,TRIGGER,HALL") == 0) {
        ok = enqueue(0x09, 2, 0, 0);
    } else if (sscanf(line, "FPGA,PLUCK,%u,%u,%u%c", &a, &b, &c, &extra) == 3 && a >= 1 && a <= 6 && b <= 20 && c >= 1 && c <= 127) {
        ok = enqueue(0x02, a, b, c);
    } else if (sscanf(line, "FPGA,PICK,%u,%u%c", &a, &b, &extra) == 2) {
        ok = fpga_link_hall_trigger(a, b);
    } else if (sscanf(line, "FPGA,STRUM,%u%c", &a, &extra) == 1) {
        ok = fpga_link_hall_strum(a);
    } else if (sscanf(line, "FPGA,TIMBRE,%u%c", &a, &extra) == 1 && a <= 3) {
        ok = enqueue(0x04, a, 0, 0);
    } else if (sscanf(line, "FPGA,VIOLIN,%u,%u,%u%c", &a, &b, &c, &extra) == 3 &&
               a >= 55 && a <= 100 && b >= 1 && b <= 127 && (c == 0 || c == 1 || c == 3)) {
        ok = enqueue(0x08, a, b, c);
    } else if (sscanf(line, "FPGA,MODE,%u%c", &a, &extra) == 1 && a <= 1) {
        ok = enqueue(0x03, a, 0, 0);
    } else if (sscanf(line, "FPGA,LEVEL,%u,%u%c", &a, &b, &extra) == 2 && a <= 4 && b <= 127) {
        ok = enqueue(0x70, a, b, 0);
    } else if (sscanf(line, "FPGA,HIT,%u,%u%c", &a, &b, &extra) == 2 && a < 12 && b >= 1 && b <= 127) {
        ok = enqueue(0x50, a, b, 0);
    }
    touch_serial_write(ok ? "OK,FPGA,QUEUED\r\n" : "ERROR,FPGA,ARG_OR_QUEUE\r\n");
    return true;
}

bool fpga_link_hall_trigger(unsigned string_number, unsigned velocity)
{
    if (s_picks == NULL || !s_online || string_number < 1 || string_number > 6 || velocity < 1 || velocity > 127) return false;
    fpga_pick_t pick = {.string_number = (uint8_t)string_number, .velocity = (uint8_t)velocity};
    uint8_t online;
    build_keys(pick.keys, &online);
    return xQueueSend(s_picks, &pick, 0) == pdTRUE;
}

bool fpga_link_hall_strum(unsigned velocity)
{
    if (s_picks == NULL || !s_online || velocity < 1 || velocity > 127) return false;
    fpga_pick_t pick = {.string_number = 6, .velocity = (uint8_t)velocity,
        .strum = true, .generation = s_strum_generation};
    uint8_t online;
    build_keys(pick.keys, &online);
    return xQueueSend(s_picks, &pick, 0) == pdTRUE;
}

void fpga_link_cancel_strums(void)
{
    atomic_fetch_add(&s_strum_generation, 1U);
}

esp_err_t fpga_link_start(void)
{
    if (fpga_crc16((const uint8_t *)"123456789", 9) != 0x29B1) return ESP_FAIL;
    const gpio_config_t outputs = { .pin_bit_mask = 1ULL << FPGA_CS, .mode = GPIO_MODE_OUTPUT };
    ESP_ERROR_CHECK(gpio_config(&outputs));
    gpio_set_level(FPGA_CS, 1);
    const gpio_config_t inputs = { .pin_bit_mask = (1ULL << FPGA_IRQ) | (1ULL << FPGA_READY),
                                  .mode = GPIO_MODE_INPUT, .pull_down_en = GPIO_PULLDOWN_ENABLE };
    ESP_ERROR_CHECK(gpio_config(&inputs));
    spi_bus_config_t bus = { .mosi_io_num = FPGA_MOSI, .miso_io_num = FPGA_MISO,
                            .sclk_io_num = FPGA_SCLK, .quadwp_io_num = -1, .quadhd_io_num = -1,
                            .max_transfer_sz = 64 };
    esp_err_t err = spi_bus_initialize(SPI2_HOST, &bus, SPI_DMA_DISABLED);
    if (err != ESP_OK) return err;
    spi_device_interface_config_t dev = { .clock_speed_hz = 1000000, .mode = 0,
                                        .spics_io_num = -1, .queue_size = 1 };
    err = spi_bus_add_device(SPI2_HOST, &dev, &s_spi);
    if (err != ESP_OK) return err;
    s_bulk_mutex=xSemaphoreCreateMutex();s_bulk_done=xSemaphoreCreateBinary();
    if(!s_bulk_mutex||!s_bulk_done)return ESP_ERR_NO_MEM;
    s_commands = xQueueCreate(32, 6);
    s_picks = xQueueCreate(32, sizeof(fpga_pick_t));
    if (s_commands == NULL || s_picks == NULL) return ESP_ERR_NO_MEM;
    if (xTaskCreate(link_task, "fpga_spi", 4096, NULL, 5, NULL) != pdPASS) return ESP_ERR_NO_MEM;
    ESP_LOGI(TAG, "S3 master: SCLK=12 MOSI=11 MISO=13 CS=10, mode0 1MHz, 64-byte full duplex");
    return ESP_OK;
}
