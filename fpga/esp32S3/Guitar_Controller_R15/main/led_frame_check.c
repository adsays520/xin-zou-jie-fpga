#include "led_frame_check.h"
#include <string.h>

static uint32_t frame_crc(const uint8_t *data, unsigned count) {
    uint32_t crc=~0U;
    for(unsigned i=0;i<count;++i) {
        crc^=data[i];
        for(unsigned bit=0;bit<8;++bit) crc=(crc>>1)^((0U-(crc&1U))&0xedb88320U);
    }
    return ~crc;
}

typedef struct {
    led_frame_check_t *out;
    const uint8_t *expected;
    unsigned expected_bits, period, frame, frame_bits, pending_high;
} decoder_t;

static void end_frame(decoder_t *d) {
    if(!d->frame_bits) return;
    if(d->frame<3) d->out->bits[d->frame]=d->frame_bits;
    if(d->frame_bits!=d->expected_bits) ++d->out->structure_errors;
    ++d->frame;d->out->frames=d->frame;d->frame_bits=0;
}

static void segment(decoder_t *d, unsigned level, unsigned ticks) {
    led_frame_check_t *r=d->out;
    if(level) {
        if(d->pending_high) ++r->structure_errors;
        d->pending_high=ticks;
        bool one=ticks>=12; /* 600ns; 50ns capture resolution */
        if(one) {
            if(ticks<r->one_min) r->one_min=ticks;
            if(ticks>r->one_max) r->one_max=ticks;
            if(ticks>20) ++r->width_errors; /* 1 high: 580..1000ns */
        } else {
            if(ticks<r->zero_min) r->zero_min=ticks;
            if(ticks>r->zero_max) r->zero_max=ticks;
            if(ticks<2 || ticks>9) ++r->width_errors; /* 0 high <470ns */
        }
        unsigned bit=d->frame_bits++;
        ++r->total_bits;
        if(d->frame>=3 || bit>=d->expected_bits) ++r->data_errors;
        else {
            if(one!=((d->expected[bit/8]>>(7-bit%8))&1U)) ++r->data_errors;
            if(d->frame==1 && one) r->middle[bit/8]|=1U<<(7-bit%8);
        }
    } else if(ticks>=1600) { /* >=80us is a frame boundary, not a data low. */
        if(d->frame_bits) {
            if(d->frame==0) r->head_low_ticks=ticks;
            if(d->frame==1) r->tail_low_ticks=ticks;
            end_frame(d);
        }
        d->pending_high=0;
    } else if(d->pending_high) {
        unsigned period=d->pending_high+ticks;
        if(period<r->period_min) r->period_min=period;
        if(period>r->period_max) r->period_max=period;
        if(period+1<d->period || period>d->period+1) ++r->period_errors;
        d->pending_high=0;
    } else if(d->frame_bits) ++r->structure_errors;
}

void led_frame_check(const rmt_symbol_word_t *symbols, unsigned count,
                     const uint8_t *expected, unsigned bytes, unsigned period_ticks,
                     led_frame_check_t *r) {
    memset(r,0,sizeof(*r));r->zero_min=r->one_min=r->period_min=~0U;
    if(!symbols || !count || !expected || !bytes || bytes>sizeof(r->middle) ||
       (period_ticks!=25 && period_ticks!=28)) {r->structure_errors=1;return;}
    decoder_t d={.out=r,.expected=expected,.expected_bits=bytes*8,.period=period_ticks};
    unsigned level=0,ticks=0;
    /* RMT packs levels in either half of a word and can split a long LOW
     * across adjacent halves. Merge runs before interpreting boundaries. */
    for(unsigned i=0;i<count;++i) for(unsigned half=0;half<2;++half) {
        unsigned n=half?symbols[i].duration1:symbols[i].duration0;
        unsigned next=half?symbols[i].level1:symbols[i].level0;
        if(!n) continue;
        if(ticks && next!=level) {segment(&d,level,ticks);ticks=0;}
        level=next;ticks+=n;
    }
    if(ticks) segment(&d,level,ticks);
    end_frame(&d);
    r->expected_crc=frame_crc(expected,bytes);
    r->middle_crc=frame_crc(r->middle,bytes);
    r->reset_measured=r->head_low_ticks>0 && r->tail_low_ticks>0;
    r->reset_ok=r->reset_measured && r->head_low_ticks>=1600 && r->tail_low_ticks>=1600;
    r->passed=r->frames==3 && r->total_bits==bytes*24 && r->reset_ok &&
        !r->data_errors && !r->width_errors && !r->period_errors && !r->structure_errors &&
        r->expected_crc==r->middle_crc;
    if(!r->zero_max) r->zero_min=0;
    if(!r->one_max) r->one_min=0;
    if(!r->period_max) r->period_min=0;
}
