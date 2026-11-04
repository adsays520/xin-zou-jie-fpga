#include "../main/led_frame_encoder.c"
#include <string.h>
#define EXPORT __declspec(dllexport)

typedef struct {rmt_encoder_t base;unsigned index;bool bytes;rmt_bytes_encoder_config_t cfg;} child_t;
static rmt_symbol_word_t wire[1024];
static unsigned used,space,live_children,fail_stage;

static size_t child_encode(rmt_encoder_t *base,rmt_channel_handle_t channel,const void *data,size_t size,rmt_encode_state_t *state) {
    (void)channel;child_t *self=(void *)base;
    unsigned length=self->bytes?size*8:size/sizeof(rmt_symbol_word_t),n=0;
    while(self->index<length && space) {
        unsigned i=self->index++;
        if(self->bytes) {
            unsigned shift=self->cfg.flags.msb_first?7-i%8:i%8;
            wire[used++]=(((const uint8_t *)data)[i/8]>>shift)&1?self->cfg.bit1:self->cfg.bit0;
        } else wire[used++]=((const rmt_symbol_word_t *)data)[i];
        --space;++n;
    }
    bool done=self->index==length;
    if(done) self->index=0;
    *state=(done?RMT_ENCODING_COMPLETE:0)|(!space?RMT_ENCODING_MEM_FULL:0);
    return n;
}
static esp_err_t child_reset(rmt_encoder_t *base) {((child_t *)base)->index=0;return ESP_OK;}
static esp_err_t child_del(rmt_encoder_t *base) {--live_children;free(base);return ESP_OK;}
void *rmt_alloc_encoder_mem(size_t n) {return fail_stage==1?NULL:calloc(1,n);}
static esp_err_t new_child(bool bytes,rmt_encoder_handle_t *out) {
    if(fail_stage==(bytes?2U:3U))return ESP_ERR_NO_MEM;
    child_t *self=calloc(1,sizeof(*self));if(!self)return ESP_ERR_NO_MEM;
    self->bytes=bytes;self->base.encode=child_encode;self->base.reset=child_reset;self->base.del=child_del;
    *out=&self->base;++live_children;return ESP_OK;
}
esp_err_t rmt_new_bytes_encoder(const rmt_bytes_encoder_config_t *cfg,rmt_encoder_handle_t *out) {
    esp_err_t e=new_child(true,out);if(e==ESP_OK)((child_t *)*out)->cfg=*cfg;return e;
}
esp_err_t rmt_new_copy_encoder(const rmt_copy_encoder_config_t *cfg,rmt_encoder_handle_t *out) {(void)cfg;return new_child(false,out);}
esp_err_t rmt_del_encoder(rmt_encoder_handle_t e) {return e->del(e);}
esp_err_t rmt_encoder_reset(rmt_encoder_handle_t e) {return e->reset(e);}

EXPORT int sim_frame_run(unsigned profile,unsigned capacity,unsigned restart,unsigned fail) {
    used=space=live_children=0;fail_stage=fail;memset(wire,0,sizeof(wire));
    if(!capacity || capacity>384)return ESP_ERR_INVALID_ARG;
    rmt_encoder_handle_t encoder=NULL;esp_err_t e=led_frame_encoder_new(profile,&encoder);if(e!=ESP_OK)return e;
    const uint8_t data[]={0x80,0x01,0xa5,0x5a,0x00,0xff};
    if(restart) {rmt_encode_state_t state=0;space=capacity;encoder->encode(encoder,NULL,data,sizeof(data),&state);rmt_encoder_reset(encoder);used=0;}
    for(unsigned call=0;call<100;++call) {
        rmt_encode_state_t state=0;space=capacity;unsigned before=used;
        size_t n=encoder->encode(encoder,NULL,data,sizeof(data),&state);
        if(n!=used-before) {e=ESP_FAIL;break;}
        if(state&RMT_ENCODING_COMPLETE) {e=ESP_OK;break;}
        if(!(state&RMT_ENCODING_MEM_FULL)) {e=ESP_FAIL;break;}
    }
    rmt_del_encoder(encoder);return e;
}
EXPORT unsigned sim_frame_count(void) {return used;}
EXPORT unsigned sim_frame_word(unsigned i) {return i<used?wire[i].val:0;}
EXPORT unsigned sim_frame_children(void) {return live_children;}
