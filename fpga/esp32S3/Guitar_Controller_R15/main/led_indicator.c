#include "led_indicator.h"
#include "led_logic.h"
#include "led_probe.h"
#include "led_frame_encoder.h"
#include "touch_layout.h"
#include "touch_serial.h"
#include "driver/rmt_tx.h"
#include "driver/rmt_encoder.h"
#include "driver/gpio.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_timer.h"
#include "esp_log.h"
#include <stdio.h>
#include <stdatomic.h>
#include <string.h>

/* Dedicated low-priority output task. Never bit-bang or wait in Hall/SPI tasks. */
static portMUX_TYPE lock=portMUX_INITIALIZER_UNLOCKED;
static rmt_channel_handle_t channels[2];
static rmt_encoder_handle_t encoders[2];
static rmt_encoder_handle_t frame_encoders[3];
static unsigned encoder_kind=1; /* 1 complete byte frame; 0 legacy symbol copy */
static uint8_t frame_bytes[2][14*3];
static bool channel_enabled[2];
static int active_pin=3;
static rmt_symbol_word_t symbols[2][14*24+2];
static const unsigned lengths[2]={13,14};
static const int pins[2]={3,7}; /* 13 LEDs on GPIO3; 14 LEDs on GPIO7 */
static led_cue_t cues[LED_GUIDE_CAPACITY];
#define LED_DEFAULT_BRIGHTNESS 32
#define LED_DEFAULT_MODE 4
#define LED_DEFAULT_TIMING 1
static unsigned cue_count, brightness=LED_DEFAULT_BRIGHTNESS, mode=LED_DEFAULT_MODE; /* 0 OFF 1 LIVE 2 GUIDE 3 BOTH 4 DEMO */
static unsigned timing_profile=LED_DEFAULT_TIMING; /* preserve working LEGACY 350/900ns 800k */
static unsigned scope_mode; /* 0 normal, 1 zeros, 2 dim 0x01/0x02 markers */
static unsigned scope_pin; /* 0 both; 7 or 3 fixes TX to one pin during scope */
static bool output_enabled;
static unsigned output_pin,output_rgb[3],output_period_ms,output_on_ms;
static int64_t output_origin;
static uint32_t tx_frames[2],tx_bits[2],tx_last_ms[2],tx_switches;
static int64_t scope_until;
static _Atomic bool started;
static _Atomic unsigned probe_state; /* 1/2 known data, 3/4 live data, 5/6 full-frame capture */
static _Atomic bool gpio_report_requested;
static bool playing;
static int64_t origin;
static int64_t pick_until[6];
static uint32_t guide_end;
static uint32_t stream_mask;
static int64_t stream_until;

void led_indicator_pick(unsigned string_number) {
    if(string_number<1 || string_number>6) return;
    int64_t until=esp_timer_get_time()+160000;
    portENTER_CRITICAL(&lock);pick_until[string_number-1]=until;portEXIT_CRITICAL(&lock);
}

static void led_task(void *arg) {
    (void)arg;
    uint8_t previous[LED_COUNT*3]={0};bool first=true;
    unsigned previous_timing=~0U,previous_scope=0,previous_scope_pin=0;
    unsigned previous_encoder=~0U;
    bool previous_output=false;
    int64_t next_scope_frame=0;
    for(;;) {
        if(atomic_exchange(&gpio_report_requested,false)) {
            touch_serial_write("LED,GPIO,BEGIN\r\n");
            gpio_dump_io_configuration(stdout,(1ULL<<7)|(1ULL<<3));
            touch_serial_write("LED,GPIO,END\r\n");
        }
        uint16_t buttons[8];uint8_t online,keys[16]={0};
        touch_serial_snapshot(buttons,&online);
        for(unsigned i=0;i<TOUCH_LAYOUT_KEYS;++i) {
            touch_source_t s=g_touch_layout[i];
            if((online&(1U<<s.chip)) && (buttons[s.chip]&(1U<<s.channel))) keys[i/8]|=1U<<(i%8);
        }
        uint32_t live,guide=0,picks=0;led_live_mask(keys,&live);
        int64_t now=esp_timer_get_time();unsigned current_mode,level,profile,scope,selected_pin,encoder;
        unsigned rgb[3]={0};bool manual;
        portENTER_CRITICAL(&lock);
        current_mode=mode;level=brightness;
        profile=timing_profile;
        encoder=encoder_kind;
        if(now>=scope_until) scope_mode=0;
        scope=scope_mode;
        manual=output_enabled;
        selected_pin=manual?output_pin:scope?scope_pin:0;
        if(manual) {
            uint64_t elapsed=now>=output_origin?(uint64_t)(now-output_origin)/1000:0;
            bool lit=!output_period_ms || elapsed%output_period_ms<output_on_ms;
            if(lit) memcpy(rgb,output_rgb,sizeof(rgb));
        }
        for(unsigned s=1;s<=6;++s) if(now<pick_until[s-1]) picks|=1U<<led_string_pixel(s);
        if(playing) {
            /* PLAY can be received after this task sampled `now`, before the
             * lock was acquired. Clamp that interleaving to time zero. */
            uint32_t elapsed=now>=origin?(uint32_t)((now-origin)/1000):0;
            if(elapsed>=guide_end) playing=false;
            else guide=led_cue_mask(cues,cue_count,elapsed);
        }
        if(now < stream_until) guide |= stream_mask;
        portEXIT_CRITICAL(&lock);
        uint8_t grb[LED_COUNT*3]={0};
        for(unsigned i=0;i<LED_COUNT;++i) {
            bool l=(current_mode==1 || current_mode==3) && (live&(1U<<i));
            bool g=(current_mode==2 || current_mode==3) && (guide&(1U<<i));
            bool p=(current_mode==1 || current_mode==3) && (picks&(1U<<i));
            grb[i*3]=(l||p)?level:0; /* G */
            grb[i*3+1]=p?level:0;   /* R: accepted Hall pluck is amber */
            grb[i*3+2]=g?level:0;   /* B: score guide; overlap with live is cyan */
        }
        if(current_mode==4) led_demo_frame((uint64_t)now/1000,(uint8_t)level,live,picks,grb);
        if(scope) for(unsigned i=0;i<sizeof(grb);++i) {
            grb[i]=scope==1?0:scope==2?(i<39?1:2):
                ((i%3)==(scope-3)?16:0); /* fixed G/R/B at visible low brightness */
        }
        if(manual) for(unsigned pixel=0;pixel<LED_COUNT;++pixel) {
            bool selected=!selected_pin || selected_pin==(unsigned)pins[pixel<13?0:1];
            grb[pixel*3]=selected?rgb[1]:0;
            grb[pixel*3+1]=selected?rgb[0]:0;
            grb[pixel*3+2]=selected?rgb[2]:0;
        }
        unsigned probe_request=atomic_load(&probe_state);
        bool probe=probe_request==1 || probe_request==3 || probe_request==5;
        bool probe_frame=probe_request==5;
        bool probe_live=probe_request==3 || probe_frame;
        if(probe) atomic_store(&probe_state,probe_frame?6:probe_live?4:2);
        if(first || probe || encoder!=previous_encoder || profile!=previous_timing || scope!=previous_scope || manual!=previous_output || selected_pin!=previous_scope_pin ||
           ((scope || manual) && now>=next_scope_frame) || memcmp(previous,grb,sizeof(grb))) {
            for(unsigned bank=0;bank<2;++bank) {
                /* Clear the previous bank once when a manual test changes pin.
                 * Later frames stay on the selected pin without switching. */
                if(selected_pin && pins[bank]!=(int)selected_pin &&
                   !(manual && (!previous_output || selected_pin!=previous_scope_pin))) continue;
                unsigned k=0,offset=bank?13:0;
                for(unsigned byte=0;byte<lengths[bank]*3;++byte)
                    frame_bytes[bank][byte]=probe && !probe_live?(byte%3==bank?16:0):grb[offset*3+byte];
                /* An explicit reset after every GPIO attachment also discards
                 * any edge created while the matrix output was switched. */
                symbols[bank][k++]=(rmt_symbol_word_t){.level0=0,.duration0=3000,.level1=0,.duration1=3000};
                for(unsigned byte=0;byte<lengths[bank]*3;++byte) for(int bit=7;bit>=0;--bit) {
                    /* CHECK uses a dim known pattern containing both 0 and 1. */
                    uint8_t value=frame_bytes[bank][byte];
                    bool one=(value>>bit)&1;
                    /* Keep the 20MHz clock and high widths unchanged in SLOW714.
                     * Only LOW grows: 28 ticks/bit = 1.40us = 714286 bit/s. */
                    unsigned high=profile?(one?18:7):(one?17:5);
                    unsigned period=profile==2?28:25;
                    symbols[bank][k++]=(rmt_symbol_word_t){.level0=1,.duration0=high,.level1=0,.duration1=period-high};
                }
                symbols[bank][k++]=(rmt_symbol_word_t){.level0=0,.duration0=3000,.level1=0,.duration1=3000};
                rmt_transmit_config_t config={.loop_count=0};
                /* S3 has one DMA-capable RMT TX channel. Reuse it only after
                 * a complete frame, and keep the other strip input low. The
                 * 768-symbol DMA buffer holds a full frame in one half; no
                 * mid-frame refill ISR is needed for either strip. */
                esp_err_t e=ESP_OK;
                if(active_pin!=pins[bank]) {
                    int old_pin=active_pin;
                    e=rmt_disable(channels[0]);
                    if(e==ESP_OK) {channel_enabled[0]=false;e=rmt_tx_switch_gpio(channels[0],pins[bank],false);}
                    /* The latch is preloaded LOW before restoring GPIO output.
                     * Do not reset here: IDF reset enables pull-up and disables
                     * output. Startup's pull-down remains during the short
                     * SDK switch interval in which the old output is disabled. */
                    if(e==ESP_OK) e=gpio_set_level(old_pin,0);
                    if(e==ESP_OK) e=gpio_set_direction(old_pin,GPIO_MODE_OUTPUT);
                    if(e==ESP_OK) e=rmt_enable(channels[0]);
                    if(e==ESP_OK) {
                        channel_enabled[0]=true;active_pin=pins[bank];
                        portENTER_CRITICAL(&lock);++tx_switches;portEXIT_CRITICAL(&lock);
                    }
                }
                if(e!=ESP_OK) {ESP_LOGE("LED","RMT switch failed: %s; LED worker stopped",esp_err_to_name(e));started=false;vTaskDelete(NULL);return;}
                if(probe) {
                    gpio_dump_io_configuration(stdout,(1ULL<<7)|(1ULL<<3));
                    led_probe_begin(pins[bank]);
                }
                /* Queue three unchanged, ordinary frame transactions so RX
                 * sees both idle boundaries of the middle frame. No marker
                 * pulses or special bits are injected into the LED stream. */
                for(unsigned repeat=0;repeat<(probe_frame?3U:1U) && e==ESP_OK;++repeat) {
                    if(encoder) e=rmt_transmit(channels[0],frame_encoders[profile],
                        frame_bytes[bank],lengths[bank]*3,&config);
                    else e=rmt_transmit(channels[0],encoders[0],symbols[bank],k*sizeof(rmt_symbol_word_t),&config);
                }
                if(e==ESP_OK) e=rmt_tx_wait_all_done(channels[0],100);
                if(e==ESP_OK) {
                    portENTER_CRITICAL(&lock);
                    tx_frames[bank]+=probe_frame?3:1;tx_bits[bank]=lengths[bank]*24;
                    tx_last_ms[bank]=(uint32_t)(esp_timer_get_time()/1000);
                    portEXIT_CRITICAL(&lock);
                }
                if(probe_frame) led_probe_frame_end(pins[bank],frame_bytes[bank],lengths[bank]*3,profile,encoder,e);
                else if(probe) led_probe_end(pins[bank],symbols[bank],lengths[bank]*24,e);
                if(e!=ESP_OK) {ESP_LOGE("LED","RMT timeout; LED worker stopped");started=false;vTaskDelete(NULL);return;}
            }
            if(probe) {atomic_store(&probe_state,0);first=true;}
            else {memcpy(previous,grb,sizeof(grb));first=false;}
            previous_encoder=encoder;previous_timing=profile;previous_scope=scope;previous_scope_pin=selected_pin;previous_output=manual;next_scope_frame=now+20000;
        }
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

static void release_channels(void) {
    for(unsigned i=0;i<3;++i) if(frame_encoders[i]) {rmt_del_encoder(frame_encoders[i]);frame_encoders[i]=NULL;}
    for(unsigned b=0;b<2;++b) {
        if(channel_enabled[b]) {rmt_disable(channels[b]);channel_enabled[b]=false;}
        if(encoders[b]) {rmt_del_encoder(encoders[b]);encoders[b]=NULL;}
        if(channels[b]) {rmt_del_channel(channels[b]);channels[b]=NULL;}
    }
}

esp_err_t led_indicator_start(void) {
    if(started || channels[0] || channels[1]) return ESP_ERR_INVALID_STATE;
    esp_err_t e;
    active_pin=pins[0];
    for(unsigned b=0;b<2;++b) {
        e=gpio_reset_pin(pins[b]);if(e!=ESP_OK) return e;
        e=gpio_set_level(pins[b],0);if(e!=ESP_OK) return e;
        gpio_config_t pad={.pin_bit_mask=1ULL<<pins[b],.mode=GPIO_MODE_OUTPUT,
            .pull_up_en=GPIO_PULLUP_DISABLE,.pull_down_en=GPIO_PULLDOWN_ENABLE,
            .intr_type=GPIO_INTR_DISABLE};
        e=gpio_config(&pad);if(e!=ESP_OK) return e;
        /* Explicit normal drive; do not assume maximum drive cures ringing. */
        e=gpio_set_drive_capability(pins[b],GPIO_DRIVE_CAP_2);if(e!=ESP_OK) return e;
    }
    for(unsigned b=0;b<1;++b) {
        rmt_tx_channel_config_t channel={.gpio_num=pins[b],.clk_src=RMT_CLK_SRC_DEFAULT,
            .resolution_hz=20000000,.mem_block_symbols=768,.trans_queue_depth=3,.flags.with_dma=1};
        e=rmt_new_tx_channel(&channel,&channels[b]);if(e!=ESP_OK) goto failed;
        rmt_copy_encoder_config_t encoder={};
        e=rmt_new_copy_encoder(&encoder,&encoders[b]);if(e!=ESP_OK) goto failed;
        for(unsigned i=0;i<3;++i) {e=led_frame_encoder_new(i,&frame_encoders[i]);if(e!=ESP_OK) goto failed;}
        e=rmt_enable(channels[b]);if(e!=ESP_OK) goto failed;
        channel_enabled[b]=true;
    }
    if(xTaskCreate(led_task,"led_indicator",4096,NULL,2,NULL)!=pdPASS) {e=ESP_ERR_NO_MEM;goto failed;}
    started=true;
    ESP_LOGI("LED","READY GPIO7=13 GPIO3=14 GRB BYTE_FRAME_DMA MSB_FIRST RESET=300us BEFORE_AND_AFTER; DEMO CYBER brightness=32 LEGACY800");
    return ESP_OK;
failed:
    release_channels();return e;
}

bool led_indicator_command(const char *line) {
    if(strncmp(line,"LED,",4)) return false;
    if(!started) {touch_serial_write("ERROR,LED,NOT_READY\r\n");return true;}
    if(!strcmp(line,"LED,OUTPUT,STATUS")) {
        unsigned pin,r,g,b,period,on;bool enabled;
        portENTER_CRITICAL(&lock);
        pin=output_pin;r=output_rgb[0];g=output_rgb[1];b=output_rgb[2];
        period=output_period_ms;on=output_on_ms;enabled=output_enabled;
        portEXIT_CRITICAL(&lock);
        char report[160];
        snprintf(report,sizeof(report),"LED,OUTPUT,STATE,ENABLED,%u,PIN,%u,RGB,%u,%u,%u,PERIOD_MS,%u,ON_MS,%u\r\n",enabled,pin,r,g,b,period,on);
        touch_serial_write(report);return true;
    }
    if(!strncmp(line,"LED,OUTPUT,",11)) {
        unsigned pin,r,g,b,period,on;char extra;
        bool valid=sscanf(line,"LED,OUTPUT,%u,%u,%u,%u,%u,%u%c",&pin,&r,&g,&b,&period,&on,&extra)==6 &&
            (pin==0 || pin==3 || pin==7) && r<=255 && g<=255 && b<=255 &&
            ((!period && !on) || (period>=100 && period<=60000 && on>=10 && on<=period-10));
        if(valid) {
            portENTER_CRITICAL(&lock);
            output_pin=pin;output_rgb[0]=r;output_rgb[1]=g;output_rgb[2]=b;
            output_period_ms=period;output_on_ms=on;output_origin=esp_timer_get_time();
            output_enabled=true;scope_mode=0;mode=0;playing=false;
            portEXIT_CRITICAL(&lock);
        }
        touch_serial_write(valid?"OK,LED\r\n":"ERROR,LED,OUTPUT_ARG\r\n");return true;
    }
    if(!strcmp(line,"LED,GPIO")) {
        atomic_store(&gpio_report_requested,true);
        touch_serial_write("OK,LED,GPIO,QUEUED\r\n");return true;
    }
    if(!strcmp(line,"LED,TX,STATUS")) {
        uint32_t frames[2],bits[2],last[2],switches;
        portENTER_CRITICAL(&lock);
        memcpy(frames,tx_frames,sizeof(frames));memcpy(bits,tx_bits,sizeof(bits));
        memcpy(last,tx_last_ms,sizeof(last));switches=tx_switches;
        portEXIT_CRITICAL(&lock);
        char report[160];
        for(unsigned bank=0;bank<2;++bank) {
            snprintf(report,sizeof(report),"LED,TX,GPIO,%d,FRAMES,%lu,BITS,%lu,LAST_MS,%lu,SWITCHES,%lu\r\n",
                pins[bank],(unsigned long)frames[bank],(unsigned long)bits[bank],
                (unsigned long)last[bank],(unsigned long)switches);
            touch_serial_write(report);
        }
        return true;
    }
    if(!strcmp(line,"LED,CHECK") || !strcmp(line,"LED,CHECK,LIVE") || !strcmp(line,"LED,CHECK,FRAME")) {
        unsigned idle=0;
        bool queued=atomic_compare_exchange_strong(&probe_state,&idle,
            !strcmp(line,"LED,CHECK,FRAME")?5:!strcmp(line,"LED,CHECK,LIVE")?3:1);
        touch_serial_write(queued?"OK,LED,CHECK,QUEUED\r\n":"ERROR,LED,CHECK,BUSY\r\n");
        return true;
    }
    unsigned a,b,c,d;char extra;bool ok=false;char reply[128];
    if(!strcmp(line,"LED,STATUS")) {
        portENTER_CRITICAL(&lock);
        unsigned m=mode,n=cue_count,l=brightness,t=timing_profile,s=scope_mode,e=encoder_kind;bool p=playing;
        portEXIT_CRITICAL(&lock);
        snprintf(reply,sizeof(reply),"LED,STATE,MODE,%u,BRIGHT,%u,EVENTS,%u,PLAYING,%u,TIMING,%s,SCOPE,%u,ENCODER,%s\r\n",m,l,n,p,t==2?"SLOW714":t?"LEGACY":"XL6028",s,e?"BYTES":"COPY");
        touch_serial_write(reply);return true;
    }
    if(!strcmp(line,"LED,GUIDE,STATUS")) {
        touch_serial_write("LED,GUIDE,CAP,1,TTL_MS,1000\r\n");return true;
    }
    if(!strncmp(line,"LED,GUIDE,",10)) {
        bool valid=strlen(line)<=19 && sscanf(line,"LED,GUIDE,%x,%x%c",&a,&b,&extra)==2 && a<0x200000U && b<0x40U;
        if(valid) {
            uint32_t mask=0;
            for(unsigned i=0;i<21;++i) if(a&(1U<<i)) mask|=1U<<led_position_pixel(i+1);
            for(unsigned i=0;i<6;++i) if(b&(1U<<i)) mask|=1U<<led_string_pixel(i+1);
            portENTER_CRITICAL(&lock);
            stream_mask=mask;stream_until=esp_timer_get_time()+1000000;
            playing=false;scope_mode=0;output_enabled=false;
            if(mode!=3) mode=2;
            portEXIT_CRITICAL(&lock);
        }
        touch_serial_write(valid?"OK,LED,GUIDE\r\n":"ERROR,LED,GUIDE_ARG\r\n");return true;
    }
    portENTER_CRITICAL(&lock);
    if(!strncmp(line,"LED,MODE,",9) || !strcmp(line,"LED,CLEAR") || !strcmp(line,"LED,STOP") || !strcmp(line,"LED,PLAY") || !strcmp(line,"LED,TEST")) {stream_mask=0;stream_until=0;}
    if(!strcmp(line,"LED,MODE,OFF")) {mode=0;playing=false;scope_mode=0;output_enabled=false;ok=true;}
    else if(!strcmp(line,"LED,MODE,DEMO")) {mode=4;playing=false;scope_mode=0;output_enabled=false;scope_pin=0;ok=true;}
    else if(!strcmp(line,"LED,TIMING,XL")) {timing_profile=0;ok=true;}
    else if(!strcmp(line,"LED,TIMING,LEGACY")) {timing_profile=1;ok=true;}
    else if(!strcmp(line,"LED,TIMING,SLOW714")) {timing_profile=2;ok=true;}
    else if(!strcmp(line,"LED,ENCODER,BYTES")) {encoder_kind=1;ok=true;}
    else if(!strcmp(line,"LED,ENCODER,COPY")) {encoder_kind=0;ok=true;}
    else if(!strcmp(line,"LED,SCOPE,OFF")) {scope_mode=0;ok=true;}
    else if(!strcmp(line,"LED,SCOPE,ZERO")) {output_enabled=false;scope_mode=1;scope_until=esp_timer_get_time()+90000000;ok=true;}
    else if(!strcmp(line,"LED,SCOPE,MARK")) {output_enabled=false;scope_mode=2;scope_until=esp_timer_get_time()+90000000;ok=true;}
    else if(!strcmp(line,"LED,SCOPE,GREEN")) {output_enabled=false;scope_mode=3;scope_until=esp_timer_get_time()+90000000;ok=true;}
    else if(!strcmp(line,"LED,SCOPE,RED")) {output_enabled=false;scope_mode=4;scope_until=esp_timer_get_time()+90000000;ok=true;}
    else if(!strcmp(line,"LED,SCOPE,BLUE")) {output_enabled=false;scope_mode=5;scope_until=esp_timer_get_time()+90000000;ok=true;}
    else if(sscanf(line,"LED,SCOPE,PIN,%u%c",&a,&extra)==1 && (a==0 || a==7 || a==3)) {scope_pin=a;ok=true;}
    else if(!strcmp(line,"LED,MODE,LIVE")) {output_enabled=false;mode=1;playing=false;ok=true;}
    else if(!strcmp(line,"LED,MODE,GUIDE")) {output_enabled=false;mode=2;ok=true;}
    else if(!strcmp(line,"LED,MODE,BOTH")) {output_enabled=false;mode=3;ok=true;}
    else if(!strcmp(line,"LED,STOP")) {playing=false;ok=true;}
    else if(!strcmp(line,"LED,CLEAR")) {playing=false;cue_count=0;guide_end=0;ok=true;}
    else if(sscanf(line,"LED,BRIGHT,%u%c",&a,&extra)==1 && a<=255) {brightness=a;ok=true;}
    else if(sscanf(line,"LED,ADD,%u,%u,%u,%u%c",&a,&b,&c,&d,&extra)==4 && b<=21 && c<=6) {
        led_cue_t cue={.at_ms=a,.position=b,.string_number=c,.duration_ms=d};
        if(!playing && cue_count<LED_GUIDE_CAPACITY && led_cue_valid(&cue)) {
            cues[cue_count++]=cue;if(a+d>guide_end) guide_end=a+d;ok=true;
        }
    }
    else if(!strcmp(line,"LED,TEST")) {
        output_enabled=false;scope_mode=0;
        playing=false;cue_count=0;
        for(unsigned i=0;i<27;++i) cues[cue_count++]=(led_cue_t){.at_ms=i*250,.duration_ms=200,
            .position=i<21?21-i:0,.string_number=i>=21?27-i:0};
        guide_end=27*250;origin=esp_timer_get_time();mode=2;playing=true;ok=true;
    }
    else if(!strcmp(line,"LED,PLAY") && cue_count) {
        output_enabled=false;scope_mode=0;
        origin=esp_timer_get_time();playing=true;if(mode!=3) mode=2;ok=true;
    }
    portEXIT_CRITICAL(&lock);
    touch_serial_write(ok?"OK,LED\r\n":"ERROR,LED,ARG_OR_BUSY\r\n");return true;
}
