#include "led_logic.h"
int led_position_pixel(unsigned p) { return p >= 1 && p <= 21 ? 21-(int)p : -1; }
int led_string_pixel(unsigned s) { return s >= 1 && s <= 6 ? 27-(int)s : -1; }
bool led_cue_valid(const led_cue_t *c) {
    return c && c->position <= 21 && c->string_number <= 6 &&
        (c->position || c->string_number) && c->duration_ms >= 1 &&
        c->duration_ms <= 3600000 && c->at_ms <= 3600000-c->duration_ms;
}
void led_live_mask(const uint8_t keys[16], uint32_t *mask) {
    *mask=0;
    for(unsigned i=0;i<126;++i) if(keys[i/8] & (1U<<(i%8))) {
        *mask |= 1U<<led_position_pixel(i/6+1);
        *mask |= 1U<<led_string_pixel(6-i%6);
    }
}
uint32_t led_cue_mask(const led_cue_t *cues,unsigned count,uint32_t elapsed) {
    uint32_t mask=0;
    for(unsigned i=0;i<count;++i) {
        const led_cue_t *c=&cues[i];
        if(!led_cue_valid(c) || elapsed<c->at_ms || elapsed-c->at_ms>=c->duration_ms) continue;
        if(c->position) mask|=1U<<led_position_pixel(c->position);
        if(c->string_number) mask|=1U<<led_string_pixel(c->string_number);
    }
    return mask;
}

void led_demo_frame(uint64_t elapsed_ms,uint8_t level,uint32_t live,
                    uint32_t picks,uint8_t grb[LED_COUNT*3]) {
    /* Inspired by the supplied h417 example's breathing, chase tails and
     * moving palette bands. Render a complete frame without blocking delays. */
    static const uint8_t palette[6][3]={ /* RGB neon palette, wrap smoothly */
        {0,255,220},{0,75,255},{128,0,255},
        {255,0,140},{180,0,255},{0,100,255}
    };
    uint64_t tick=elapsed_ms/20;
    unsigned ring=LED_COUNT*256U;
    unsigned head=(unsigned)((tick*24U)%ring);
    unsigned reverse=(unsigned)((ring-(tick*14U)%ring+ring/2)%ring);
    unsigned breath=(unsigned)(tick%256U);
    if(breath>128) breath=256-breath;
    for(unsigned i=0;i<LED_COUNT;++i) {
        unsigned phase=(unsigned)((tick*2U+i*96U)%1536U);
        unsigned a=phase/256U,b=(a+1)%6U,f=phase%256U;
        unsigned energy=72U+breath/2U; /* visible background, never a full blackout */
        unsigned d=(head+ring-i*256U)%ring;
        unsigned e=(i*256U+ring-reverse)%ring;
        if(d<4*256U) energy+=(4*256U-d)*160U/(4*256U);
        if(e<3*256U) energy+=(3*256U-e)*96U/(3*256U);
        if(energy>255) energy=255;
        uint8_t rgb[3];
        for(unsigned c=0;c<3;++c) {
            unsigned color=(palette[a][c]*(256U-f)+palette[b][c]*f+128U)/256U;
            rgb[c]=(uint8_t)((color*energy*level+32512U)/65025U);
        }
        /* Performance feedback stays visible above the moving background. */
        if(live&(1U<<i)) {rgb[0]=level/4;rgb[1]=level;rgb[2]=level;}
        if(picks&(1U<<i)) {rgb[0]=level;rgb[1]=level/4;rgb[2]=level;}
        grb[i*3]=rgb[1];grb[i*3+1]=rgb[0];grb[i*3+2]=rgb[2];
    }
}
