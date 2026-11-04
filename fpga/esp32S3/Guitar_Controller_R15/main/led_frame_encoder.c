/* SPDX-License-Identifier: Apache-2.0
 * Uses the ESP-IDF public composite bytes/copy encoder API pattern.
 * No WCH PIOC code or microcode is used on ESP32.
 */
#include "led_frame_encoder.h"
#include <stdlib.h>

typedef struct {
    rmt_encoder_t base; /* first member permits conversion from base pointer */
    rmt_encoder_handle_t bytes,low;
    rmt_symbol_word_t reset;
    unsigned phase; /* leading reset, complete GRB frame, trailing reset */
} led_frame_encoder_t;

static size_t RMT_ENCODER_FUNC_ATTR encode_frame(rmt_encoder_t *base,rmt_channel_handle_t channel,
        const void *data,size_t size,rmt_encode_state_t *state) {
    led_frame_encoder_t *self=(void *)base;
    size_t total=0;
    *state=RMT_ENCODING_RESET;
    while(self->phase<3) {
        rmt_encode_state_t child=RMT_ENCODING_RESET;
        if(self->phase==1) total+=self->bytes->encode(self->bytes,channel,data,size,&child);
        else total+=self->low->encode(self->low,channel,&self->reset,sizeof(self->reset),&child);
        if(child&RMT_ENCODING_COMPLETE) ++self->phase;
        if(self->phase==3) {
            self->phase=0;
            *state=RMT_ENCODING_COMPLETE|(child&RMT_ENCODING_MEM_FULL);
            return total;
        }
        if(child&RMT_ENCODING_MEM_FULL) {*state=RMT_ENCODING_MEM_FULL;return total;}
    }
    return total;
}

static esp_err_t RMT_ENCODER_FUNC_ATTR reset_frame(rmt_encoder_t *base) {
    led_frame_encoder_t *self=(void *)base;self->phase=0;
    esp_err_t a=rmt_encoder_reset(self->bytes),b=rmt_encoder_reset(self->low);
    return a!=ESP_OK?a:b;
}

static esp_err_t delete_frame(rmt_encoder_t *base) {
    led_frame_encoder_t *self=(void *)base;
    if(self->bytes) rmt_del_encoder(self->bytes);
    if(self->low) rmt_del_encoder(self->low);
    free(self);return ESP_OK;
}

esp_err_t led_frame_encoder_new(unsigned profile,rmt_encoder_handle_t *out) {
    if(!out || profile>2) return ESP_ERR_INVALID_ARG;
    *out=NULL;
    led_frame_encoder_t *self=rmt_alloc_encoder_mem(sizeof(*self));
    if(!self) return ESP_ERR_NO_MEM;
    *self=(led_frame_encoder_t){0};
    self->base.encode=encode_frame;self->base.reset=reset_frame;self->base.del=delete_frame;
    unsigned period=profile==2?28:25,zero=profile?7:5,one=profile?18:17;
    rmt_bytes_encoder_config_t bytes={
        .bit0={.level0=1,.duration0=zero,.level1=0,.duration1=period-zero},
        .bit1={.level0=1,.duration0=one,.level1=0,.duration1=period-one},
        .flags.msb_first=1};
    rmt_copy_encoder_config_t low={};
    self->reset=(rmt_symbol_word_t){.level0=0,.duration0=3000,.level1=0,.duration1=3000};
    esp_err_t e=rmt_new_bytes_encoder(&bytes,&self->bytes);
    if(e==ESP_OK) e=rmt_new_copy_encoder(&low,&self->low);
    if(e!=ESP_OK) {delete_frame(&self->base);return e;}
    *out=&self->base;return ESP_OK;
}
