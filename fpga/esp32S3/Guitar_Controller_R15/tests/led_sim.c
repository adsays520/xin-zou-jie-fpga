#include "../main/led_indicator.c"
#include "../main/led_probe.c"
#include "../main/led_frame_check.c"
#include <setjmp.h>
#include <stdlib.h>

#define SIM_EXPORT __declspec(dllexport)
static int64_t sim_now;
static uint16_t sim_buttons[8];
static uint8_t sim_online,sim_grb[LED_COUNT*3];
static unsigned sim_channels,sim_encoders,sim_enables,sim_deletes,sim_encoder_deletes;
static unsigned sim_transmits,sim_bad_timing,sim_priority,sim_task_steps,sim_task_limit;
static int sim_fail_kind,sim_fail_index,sim_task_fail,sim_tx_fail;
static unsigned sim_pin[2],sim_resolution[2],sim_dma,sim_memory,sim_current_pin,sim_waits;
static void (*sim_task)(void *);
static jmp_buf sim_exit;
static char sim_reply[256];
static char sim_trace[4096];
static rmt_rx_done_callback_t sim_rx_callback;
static rmt_symbol_word_t *sim_rx_buffer;
static unsigned sim_rx_capacity,sim_probe_fault,sim_receiving;
static unsigned sim_gpio_resets,sim_gpio_errors,sim_gpio_dumps;
static unsigned sim_zero_high,sim_zero_low,sim_one_high,sim_one_low;
static unsigned sim_byte_transmits;
static unsigned sim_queue_depth,sim_rx_used,sim_rx_repeats;
static unsigned sim_output[8],sim_route[8],sim_latch[8],sim_pullup[8],sim_pulldown[8],sim_drive[8];

int64_t esp_timer_get_time(void) {return sim_now;}
const char *esp_err_to_name(esp_err_t e) {(void)e;return "SIM_ERROR";}
void touch_serial_write(const char *s) {snprintf(sim_reply,sizeof(sim_reply),"%s",s);strncat(sim_trace,s,sizeof(sim_trace)-strlen(sim_trace)-1);}
void touch_serial_snapshot(uint16_t buttons[8],uint8_t *online) {memcpy(buttons,sim_buttons,sizeof(sim_buttons));*online=sim_online;}
void vTaskDelay(TickType_t ticks) {sim_now+=(int64_t)ticks*1000;if(++sim_task_steps>=sim_task_limit)longjmp(sim_exit,1);}
void vTaskDelete(void *task) {(void)task;longjmp(sim_exit,1);}
int xTaskCreate(void (*task)(void *),const char *name,unsigned stack,void *arg,unsigned priority,void *handle) {
    (void)name;(void)stack;(void)arg;(void)handle;sim_task=task;sim_priority=priority;return sim_task_fail?0:pdPASS;
}
esp_err_t rmt_new_tx_channel(const rmt_tx_channel_config_t *c,rmt_channel_handle_t *out) {
    unsigned b=sim_channels++;
    if(sim_fail_kind==1 && (int)b==sim_fail_index)return ESP_ERR_NO_MEM;
    sim_output[c->gpio_num]=1;sim_route[c->gpio_num]=1;
    sim_pin[b]=c->gpio_num;sim_current_pin=c->gpio_num;sim_resolution[b]=c->resolution_hz;sim_dma=c->flags.with_dma;sim_memory=c->mem_block_symbols;sim_queue_depth=c->trans_queue_depth;*out=(void *)(uintptr_t)(b+1);return ESP_OK;
}
esp_err_t rmt_new_copy_encoder(const rmt_copy_encoder_config_t *c,rmt_encoder_handle_t *out) {
    (void)c;unsigned b=sim_encoders++;
    if(sim_fail_kind==2 && (int)b==sim_fail_index)return ESP_ERR_NO_MEM;
    *out=(void *)(uintptr_t)(b+1);return ESP_OK;
}
esp_err_t led_frame_encoder_new(unsigned profile,rmt_encoder_handle_t *out) {
    if(sim_fail_kind==4 && (int)profile==sim_fail_index)return ESP_ERR_NO_MEM;
    *out=(void *)(uintptr_t)(101+profile);return ESP_OK;
}
esp_err_t rmt_enable(rmt_channel_handle_t c) {(void)c;unsigned b=sim_enables++;return sim_fail_kind==3 && (int)b==sim_fail_index?ESP_ERR_NO_MEM:ESP_OK;}
esp_err_t rmt_disable(rmt_channel_handle_t c) {(void)c;return ESP_OK;}
esp_err_t rmt_tx_switch_gpio(rmt_channel_handle_t c,int pin,bool inverted) {(void)c;(void)inverted;sim_output[sim_current_pin]=0;sim_output[pin]=sim_route[pin]=1;sim_current_pin=pin;return ESP_OK;}
esp_err_t gpio_reset_pin(int pin) {++sim_gpio_resets;sim_output[pin]=0;sim_pullup[pin]=1;sim_pulldown[pin]=0;return ESP_OK;}
esp_err_t gpio_set_direction(int pin,int direction) {if(sim_latch[pin])++sim_gpio_errors;sim_route[pin]=0;sim_output[pin]=direction==GPIO_MODE_OUTPUT;return ESP_OK;}
int gpio_set_level(int pin,unsigned level) {sim_latch[pin]=level;return ESP_OK;}
esp_err_t gpio_config(const gpio_config_t *c) {
    for(unsigned pin=0;pin<8;++pin) if(c->pin_bit_mask&(1ULL<<pin)) {
        sim_output[pin]=c->mode==GPIO_MODE_OUTPUT;sim_route[pin]=0;
        sim_pullup[pin]=c->pull_up_en;sim_pulldown[pin]=c->pull_down_en;
    }
    return ESP_OK;
}
esp_err_t gpio_set_drive_capability(int pin,int strength) {sim_drive[pin]=strength;return ESP_OK;}
esp_err_t gpio_dump_io_configuration(FILE *stream,uint64_t mask) {(void)stream;if(mask!=((1ULL<<7)|(1ULL<<3)))++sim_gpio_errors;++sim_gpio_dumps;return ESP_OK;}
esp_err_t rmt_del_channel(rmt_channel_handle_t c) {(void)c;++sim_deletes;return ESP_OK;}
esp_err_t rmt_del_encoder(rmt_encoder_handle_t c) {(void)c;++sim_encoder_deletes;return ESP_OK;}
esp_err_t rmt_tx_wait_all_done(rmt_channel_handle_t c,int timeout) {(void)c;(void)timeout;sim_waits=sim_transmits;return ESP_OK;}
esp_err_t rmt_new_rx_channel(const rmt_rx_channel_config_t *c,rmt_channel_handle_t *out) {
    (void)c;if(sim_probe_fault==6)return ESP_ERR_NO_MEM;*out=(void *)99;return ESP_OK;
}
esp_err_t rmt_rx_register_event_callbacks(rmt_channel_handle_t c,const rmt_rx_event_callbacks_t *cb,void *context) {
    (void)c;(void)context;sim_rx_callback=cb->on_recv_done;return ESP_OK;
}
esp_err_t rmt_receive(rmt_channel_handle_t c,void *buffer,size_t size,const rmt_receive_config_t *cfg) {
    (void)c;(void)cfg;if(sim_probe_fault==5)return ESP_FAIL;
    sim_rx_buffer=buffer;sim_rx_capacity=size/sizeof(rmt_symbol_word_t);sim_receiving=1;sim_rx_used=sim_rx_repeats=0;return ESP_OK;
}
esp_err_t rmt_transmit(rmt_channel_handle_t c,rmt_encoder_handle_t e,const void *payload,size_t size,const rmt_transmit_config_t *cfg) {
    (void)cfg;if(sim_tx_fail)return ESP_FAIL;
    if(sim_transmits-sim_waits>=(probe_state==6?sim_queue_depth:1))++sim_bad_timing;
    for(unsigned pin=3;pin<=7;pin+=4) {
        if(!sim_output[pin] || sim_pullup[pin] || !sim_pulldown[pin] || sim_drive[pin]!=2)++sim_gpio_errors;
        if(sim_route[pin]!=(pin==sim_current_pin) || sim_latch[pin])++sim_gpio_errors;
    }
    (void)c;unsigned b=sim_current_pin==7,offset=b?39:0,count=b?42:39;const rmt_symbol_word_t *s=payload;
    rmt_symbol_word_t expanded[338];
    if((uintptr_t)e>=101 && (uintptr_t)e<=103) {
        unsigned profile=(uintptr_t)e-101,period=profile==2?28:25;
        const uint8_t *bytes=payload;++sim_byte_transmits;
        if(size!=count)++sim_bad_timing;
        expanded[0]=(rmt_symbol_word_t){.level0=0,.duration0=3000,.level1=0,.duration1=3000};
        for(unsigned i=0;i<count*8;++i) {
            bool one=(bytes[i/8]>>(7-i%8))&1;
            unsigned high=profile?(one?18:7):(one?17:5);
            expanded[i+1]=(rmt_symbol_word_t){.level0=1,.duration0=high,.level1=0,.duration1=period-high};
        }
        expanded[count*8+1]=expanded[0];s=expanded;size=(count*8+2)*sizeof(*s);
    }
    sim_pin[b]=sim_current_pin;
    if(sim_dma && count*8+2>=sim_memory/2)++sim_bad_timing;
    if(size!=(count*8+2)*sizeof(*s))++sim_bad_timing;
    for(unsigned i=0;i<count;++i) {
        uint8_t byte=0;
        for(unsigned bit=0;bit<8;++bit) {
            const rmt_symbol_word_t *w=&s[1+i*8+bit];
            unsigned period=w->duration0+w->duration1;
            if(w->level0!=1 || w->level1!=0 || (period!=25 && period!=28))++sim_bad_timing;
            if(w->duration0>w->duration1) {sim_one_high=w->duration0;sim_one_low=w->duration1;}
            else {sim_zero_high=w->duration0;sim_zero_low=w->duration1;}
            byte=(byte<<1)|(w->duration0>w->duration1);
        }
        sim_grb[offset+i]=byte;
    }
    for(unsigned reset=0;reset<2;++reset) {unsigned index=reset?count*8+1:0;if(s[index].level0 || s[index].level1 || s[index].duration0+s[index].duration1!=6000)++sim_bad_timing;}
    if(sim_receiving && probe_state==6) {
        if(sim_rx_used+count*8>sim_rx_capacity)abort();
        unsigned first=sim_rx_used;
        for(unsigned i=0;i<count*8;++i)sim_rx_buffer[sim_rx_used++]=s[i+1];
        /* Hardware omits the external idles. Only the idle between two
         * ordinary queued transactions can be used to prove a frame reset. */
        if(sim_rx_repeats)sim_rx_buffer[first-1].duration1+=12000;
        sim_rx_buffer[sim_rx_used-1].duration1=0;
        if(++sim_rx_repeats==3) {
            if(sim_probe_fault==10)sim_rx_used=count*8;
            if(sim_probe_fault==11) {
                unsigned i=count*8;
                sim_rx_buffer[i].duration0=sim_rx_buffer[i].duration0>=12?5:17;
                sim_rx_buffer[i].duration1=25-sim_rx_buffer[i].duration0;
            }
            if(sim_probe_fault==12)sim_rx_buffer[count*8-1].duration1=1000;
            if(sim_probe_fault==13)sim_rx_buffer[count*16-1].duration1=1000;
            sim_receiving=0;
            rmt_rx_done_event_data_t event={.received_symbols=sim_rx_buffer,.num_symbols=sim_rx_used};
            sim_rx_callback((void *)99,&event,NULL);
        }
    } else if(sim_receiving) {
        unsigned bits=sim_probe_fault==1?24:count*8;
        if(bits+1>sim_rx_capacity)abort();
        /* RX can start with low, so its word boundary differs from TX. */
        for(unsigned i=0;i<=bits;++i) {
            sim_rx_buffer[i]=(rmt_symbol_word_t){.level0=0,.duration0=i?s[i].duration1:s[0].duration0+s[0].duration1+3,
                .level1=1,.duration1=i<bits?s[i+1].duration0:0};
        }
        sim_rx_buffer[bits].duration0=20000;
        if(sim_probe_fault==2) {
            sim_rx_buffer[0].duration1=sim_rx_buffer[0].duration1>=12?5:17;
            sim_rx_buffer[1].duration0=25-sim_rx_buffer[0].duration1;
        }
        if(sim_probe_fault==3)sim_rx_buffer[100].duration0=200;
        if(sim_probe_fault==4) {sim_rx_buffer[0].duration1=11;sim_rx_buffer[1].duration0=14;}
        if(sim_probe_fault==7)sim_rx_buffer[0].duration0=1000;
        if(sim_probe_fault==8)sim_rx_buffer[bits].duration0=1000;
        if(sim_probe_fault==9) {sim_rx_buffer[0].duration0=0;sim_rx_buffer[bits].duration0=0;}
        sim_receiving=0;
        rmt_rx_done_event_data_t event={.received_symbols=sim_rx_buffer,.num_symbols=bits+1};
        sim_rx_callback((void *)99,&event,NULL);
    }
    ++sim_transmits;return ESP_OK;
}
SIM_EXPORT void sim_led_reset(void) {
    release_channels();memset(cues,0,sizeof(cues));memset(pick_until,0,sizeof(pick_until));
    stream_mask=0;stream_until=0;cue_count=guide_end=0;brightness=LED_DEFAULT_BRIGHTNESS;mode=LED_DEFAULT_MODE;started=false;playing=false;origin=0;
    probe_state=0;gpio_report_requested=false;timing_profile=LED_DEFAULT_TIMING;scope_mode=scope_pin=0;scope_until=0;sim_probe_fault=sim_receiving=0;sim_trace[0]=0;
    memset(tx_frames,0,sizeof(tx_frames));memset(tx_bits,0,sizeof(tx_bits));memset(tx_last_ms,0,sizeof(tx_last_ms));tx_switches=0;
    output_enabled=false;output_pin=output_period_ms=output_on_ms=0;output_origin=0;memset(output_rgb,0,sizeof(output_rgb));
    sim_gpio_resets=sim_gpio_errors=sim_gpio_dumps=0;
    sim_zero_high=sim_zero_low=sim_one_high=sim_one_low=0;
    encoder_kind=1;sim_byte_transmits=0;
    memset(sim_output,0,sizeof(sim_output));memset(sim_route,0,sizeof(sim_route));
    memset(sim_latch,0,sizeof(sim_latch));memset(sim_pullup,0,sizeof(sim_pullup));
    memset(sim_pulldown,0,sizeof(sim_pulldown));memset(sim_drive,0,sizeof(sim_drive));
    memset(sim_buttons,0,sizeof(sim_buttons));memset(sim_grb,0,sizeof(sim_grb));sim_online=255;sim_now=1000000;
    sim_channels=sim_encoders=sim_enables=sim_deletes=sim_encoder_deletes=sim_transmits=sim_bad_timing=0;
    sim_dma=sim_memory=sim_waits=sim_queue_depth=sim_rx_used=sim_rx_repeats=0;sim_current_pin=3;memset(sim_pin,0,sizeof(sim_pin));
    sim_fail_kind=sim_fail_index=sim_task_fail=sim_tx_fail=0;sim_reply[0]=0;sim_task=NULL;
}
SIM_EXPORT int sim_led_start(void) {return led_indicator_start();}
SIM_EXPORT const char *sim_led_command(const char *line) {sim_reply[0]=0;if(!led_indicator_command(line))strcpy(sim_reply,"UNHANDLED");return sim_reply;}
SIM_EXPORT void sim_led_run(unsigned loops) {sim_task_steps=0;sim_task_limit=loops;if(setjmp(sim_exit)==0 && sim_task)sim_task(NULL);}
SIM_EXPORT void sim_led_key(unsigned key,int down) {touch_source_t s=g_touch_layout[key-1];if(down)sim_buttons[s.chip]|=1U<<s.channel;else sim_buttons[s.chip]&=~(1U<<s.channel);}
SIM_EXPORT void sim_led_online(unsigned mask) {sim_online=mask;}
SIM_EXPORT void sim_led_pick(unsigned string_number) {led_indicator_pick(string_number);}
SIM_EXPORT void sim_led_time(unsigned ms) {sim_now=1000000+(int64_t)ms*1000;}
SIM_EXPORT unsigned sim_led_byte(unsigned pixel,unsigned channel) {return sim_grb[pixel*3+channel];}
SIM_EXPORT unsigned sim_led_pin(unsigned b) {return sim_pin[b];}
SIM_EXPORT unsigned sim_led_resolution(unsigned b) {return sim_resolution[b];}
SIM_EXPORT unsigned sim_led_bad_timing(void) {return sim_bad_timing;}
SIM_EXPORT unsigned sim_led_gpio_errors(void) {return sim_gpio_errors;}
SIM_EXPORT unsigned sim_led_gpio_resets(void) {return sim_gpio_resets;}
SIM_EXPORT unsigned sim_led_gpio_dumps(void) {return sim_gpio_dumps;}
SIM_EXPORT unsigned sim_led_transmits(void) {return sim_transmits;}
SIM_EXPORT unsigned sim_led_byte_transmits(void) {return sim_byte_transmits;}
SIM_EXPORT unsigned sim_led_zero_high(void) {return sim_zero_high;}
SIM_EXPORT unsigned sim_led_zero_low(void) {return sim_zero_low;}
SIM_EXPORT unsigned sim_led_one_high(void) {return sim_one_high;}
SIM_EXPORT unsigned sim_led_one_low(void) {return sim_one_low;}
SIM_EXPORT unsigned sim_led_bank_frames(unsigned bank) {return tx_frames[bank];}
SIM_EXPORT unsigned sim_led_switches(void) {return tx_switches;}
SIM_EXPORT unsigned sim_led_priority(void) {return sim_priority;}
SIM_EXPORT unsigned sim_led_dma(void) {return sim_dma;}
SIM_EXPORT unsigned sim_led_memory(void) {return sim_memory;}
SIM_EXPORT unsigned sim_led_waits(void) {return sim_waits;}
SIM_EXPORT unsigned sim_led_deletes(void) {return sim_deletes;}
SIM_EXPORT unsigned sim_led_encoder_deletes(void) {return sim_encoder_deletes;}
SIM_EXPORT void sim_led_fail(int kind,int index) {sim_fail_kind=kind;sim_fail_index=index;}
SIM_EXPORT void sim_led_fail_task(void) {sim_task_fail=1;}
SIM_EXPORT void sim_led_fail_tx(void) {sim_tx_fail=1;}
SIM_EXPORT void sim_led_probe_fault(unsigned fault) {sim_probe_fault=fault;}
SIM_EXPORT const char *sim_led_trace(void) {return sim_trace;}
