#include "led_probe.h"
#include "led_frame_check.h"
#include "driver/rmt_rx.h"
#include "touch_serial.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_timer.h"
#include <stdatomic.h>
#include <stdio.h>

static rmt_symbol_word_t captured[1152] __attribute__((aligned(64)));
static _Atomic bool complete;
static unsigned received;
static rmt_channel_handle_t receiver;
static bool receiver_enabled;
static esp_err_t receiver_error;

static bool capture_done(rmt_channel_handle_t channel,
                         const rmt_rx_done_event_data_t *event, void *context) {
    (void)channel;(void)context;
    received=event->num_symbols;
    atomic_store(&complete,true);
    return false;
}

void led_probe_begin(int pin) {
    receiver=NULL;receiver_enabled=false;
    rmt_rx_channel_config_t channel={.gpio_num=pin,.clk_src=RMT_CLK_SRC_DEFAULT,
        .resolution_hz=20000000,.mem_block_symbols=2304,.flags.with_dma=1};
    rmt_rx_event_callbacks_t callbacks={.on_recv_done=capture_done};
    rmt_receive_config_t receive={.signal_range_min_ns=75,.signal_range_max_ns=1000000};
    /* RX creation enables input on the same pad without disabling TX output. */
    atomic_store(&complete,false);received=0;
    receiver_error=rmt_new_rx_channel(&channel,&receiver);
    if(receiver_error==ESP_OK) receiver_error=rmt_rx_register_event_callbacks(receiver,&callbacks,NULL);
    if(receiver_error==ESP_OK) {receiver_error=rmt_enable(receiver);receiver_enabled=receiver_error==ESP_OK;}
    if(receiver_error==ESP_OK) receiver_error=rmt_receive(receiver,captured,sizeof(captured),&receive);
}

void led_probe_end(int pin, const rmt_symbol_word_t *expected, unsigned bits, esp_err_t tx_error) {
    esp_err_t error=receiver_error==ESP_OK?tx_error:receiver_error;
    if(error==ESP_OK) {
        int64_t deadline=esp_timer_get_time()+100000;
        while(!atomic_load(&complete) && esp_timer_get_time()<deadline) vTaskDelay(pdMS_TO_TICKS(1));
        if(!atomic_load(&complete)) error=ESP_FAIL;
    }
    /* Disable RX before reading its buffer or releasing resources, even on timeout. */
    if(receiver_enabled) rmt_disable(receiver);
    if(receiver) rmt_del_channel(receiver);
    receiver=NULL;receiver_enabled=false;

    unsigned highs=0,bad_data=0,bad_width=0,bad_period=0;
    unsigned zero_min=32767,zero_max=0,one_min=32767,one_max=0;
    unsigned pending_high=0;
    unsigned head_low=0,tail_low=0,period_min=32767,period_max=0;
    if(error==ESP_OK) {
        if(received>384) {received=384;error=ESP_FAIL;}
        for(unsigned i=0;i<received;++i) for(unsigned half=0;half<2;++half) {
            unsigned duration=half?captured[i].duration1:captured[i].duration0;
            unsigned level=half?captured[i].level1:captured[i].level0;
            if(!duration) continue;
            if(level) {
                if(pending_high) ++bad_period;
                pending_high=duration;
                bool one=duration>=12;
                if(highs>=bits || one!=(expected[highs+1].duration0>=12)) ++bad_data;
                if(one) {
                    if(duration<one_min) one_min=duration;
                    if(duration>one_max) one_max=duration;
                    if(duration<12 || duration>20) ++bad_width;
                } else {
                    if(duration<zero_min) zero_min=duration;
                    if(duration>zero_max) zero_max=duration;
                    if(duration>9) ++bad_width;
                }
                ++highs;
            } else if(pending_high) {
                /* Last low merges with RESET and is intentionally much longer. */
                unsigned expected_period=highs<=bits?
                    expected[highs].duration0+expected[highs].duration1:0;
                if(highs<bits && (pending_high+duration+1<expected_period || pending_high+duration>expected_period+1)) ++bad_period;
                if(highs<bits) {
                    unsigned period=pending_high+duration;
                    if(period<period_min) period_min=period;
                    if(period>period_max) period_max=period;
                } else tail_low+=duration;
                pending_high=0;
            } else if(!highs) head_low+=duration;
            else if(highs==bits) tail_low+=duration;
        }
    }
    /* Head may include the software time between RX arming and TX start.
     * Tail is an observed idle duration, not a claim of exact RESET length. */
    bool reset_measured=head_low>0 && tail_low>0;
    bool reset_ok=reset_measured && head_low>=1600 && tail_low>=1600;
    bool data_ok=error==ESP_OK && highs==bits && !bad_data && !bad_width && !bad_period;
    const char *verdict=data_ok?(reset_ok?"PASS":reset_measured?"FAIL":"DATA_ONLY"):"FAIL";
    char reply[480];
    snprintf(reply,sizeof(reply),
        "LED,CHECK,GPIO,%d,RESULT,%s,BITS,%u,EXPECTED,%u,DATA_ERRORS,%u,WIDTH_ERRORS,%u,PERIOD_ERRORS,%u,T0H_NS,%u,%u,T1H_NS,%u,%u,PERIOD_NS,%u,%u,HEAD_LOW_NS,%u,TAIL_LOW_NS,%u,RESET_OK,%u,RESET_MEASURED,%u,ERR,%d,SCOPE,FIRST_FRAME_S3_PAD\r\n",
        pin,verdict,highs,bits,bad_data,bad_width,bad_period,
        zero_max?zero_min*50:0,zero_max*50,one_max?one_min*50:0,one_max*50,
        period_max?period_min*50:0,period_max*50,head_low*50,tail_low*50,reset_ok,reset_measured,error);
    touch_serial_write(reply);
}

void led_probe_frame_end(int pin,const uint8_t *expected,unsigned bytes,
                         unsigned profile,unsigned encoder,esp_err_t tx_error) {
    esp_err_t error=receiver_error==ESP_OK?tx_error:receiver_error;
    if(error==ESP_OK) {
        int64_t deadline=esp_timer_get_time()+100000;
        while(!atomic_load(&complete) && esp_timer_get_time()<deadline) vTaskDelay(pdMS_TO_TICKS(1));
        if(!atomic_load(&complete)) error=ESP_FAIL;
    }
    if(receiver_enabled) rmt_disable(receiver);
    if(receiver) rmt_del_channel(receiver);
    receiver=NULL;receiver_enabled=false;
    led_frame_check_t check={0};
    if(received>1152) {received=1152;error=ESP_FAIL;}
    if(error==ESP_OK) led_frame_check(captured,received,expected,bytes,profile==2?28:25,&check);
    char reply[480];
    snprintf(reply,sizeof(reply),
        "LED,FRAME,GPIO,%d,RESULT,%s,FRAMES,%u,BITS,%u,EXPECTED,%u,F0_BITS,%u,F1_BITS,%u,F2_BITS,%u,DATA_ERRORS,%u,WIDTH_ERRORS,%u,PERIOD_ERRORS,%u,STRUCTURE_ERRORS,%u,HEAD_LOW_NS,%u,TAIL_LOW_NS,%u,RESET_OK,%u,ERR,%d,SCOPE,THREE_FRAMES_S3_PAD\r\n",
        pin,error==ESP_OK && check.passed?"PASS":"FAIL",check.frames,check.total_bits,bytes*24,
        check.bits[0],check.bits[1],check.bits[2],check.data_errors,check.width_errors,
        check.period_errors,check.structure_errors,check.head_low_ticks*50,check.tail_low_ticks*50,check.reset_ok,error);
    touch_serial_write(reply);
    snprintf(reply,sizeof(reply),
        "LED,FRAME,GPIO,%d,ENCODER,%s,TX_GRB,%02X,%02X,%02X,RX_GRB,%02X,%02X,%02X,TX_CRC32,%08lX,RX_CRC32,%08lX,T0H_NS,%u,%u,T1H_NS,%u,%u,PERIOD_NS,%u,%u,SYMBOLS,%u\r\n",
        pin,encoder?"BYTES":"COPY",expected[0],expected[1],expected[2],
        check.middle[0],check.middle[1],check.middle[2],(unsigned long)check.expected_crc,
        (unsigned long)check.middle_crc,check.zero_min*50,check.zero_max*50,
        check.one_min*50,check.one_max*50,check.period_min*50,check.period_max*50,received);
    touch_serial_write(reply);
}
