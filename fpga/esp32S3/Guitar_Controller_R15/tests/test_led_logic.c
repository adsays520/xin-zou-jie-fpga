#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "led_logic.h"
int main(void) {
    assert(led_position_pixel(21)==0);assert(led_position_pixel(9)==12);
    assert(led_position_pixel(8)==13);assert(led_position_pixel(1)==20);
    assert(led_string_pixel(6)==21);assert(led_string_pixel(1)==26);
    assert(led_position_pixel(0)==-1);assert(led_position_pixel(22)==-1);
    assert(led_string_pixel(0)==-1);assert(led_string_pixel(7)==-1);
    unsigned checks=0;
    for(unsigned i=0;i<126;++i) {
        uint8_t keys[16]={0};uint32_t mask;
        keys[i/8]=1U<<(i%8);led_live_mask(keys,&mask);
        uint32_t expected=(1U<<(20-i/6))|(1U<<(21+i%6));
        assert(mask==expected);++checks;
    }
    /* All pairs: releasing one key must preserve another key's shared LED. */
    for(unsigned i=0;i<126;++i) for(unsigned j=0;j<126;++j) {
        uint8_t a[16]={0},b[16]={0},both[16]={0};uint32_t ma,mb,m;
        a[i/8]|=1U<<(i%8);b[j/8]|=1U<<(j%8);
        for(unsigned k=0;k<16;++k) both[k]=a[k]|b[k];
        led_live_mask(a,&ma);led_live_mask(b,&mb);led_live_mask(both,&m);
        assert(m==(ma|mb));++checks;
    }
    led_cue_t c[3]={{100,200,21,6},{200,300,21,1},{0,50,0,6}};
    assert(led_cue_mask(c,3,0)==(1U<<21));
    assert(led_cue_mask(c,3,50)==0);
    assert(led_cue_mask(c,3,100)==((1U<<0)|(1U<<21)));
    assert(led_cue_mask(c,3,250)==((1U<<0)|(1U<<21)|(1U<<26)));
    assert(led_cue_mask(c,3,300)==((1U<<0)|(1U<<26)));
    assert(led_cue_mask(c,3,500)==0);
    led_cue_t bad[]={{0,0,1,1},{0,1,22,1},{0,1,1,7},{0,1,0,0},{3600000,1,1,1},{0,3600001,1,1}};
    for(unsigned i=0;i<sizeof(bad)/sizeof(bad[0]);++i) assert(!led_cue_valid(&bad[i]));
    printf("PASS: all 126 touch keys, %u exhaustive single/pair cases, mapping boundaries, overlapping cues, timing and invalid inputs\n",checks);
    return 0;
}
