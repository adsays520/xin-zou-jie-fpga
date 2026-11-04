#include "../main/led_frame_check.c"
#define EXPORT __declspec(dllexport)
static led_frame_check_t result;
EXPORT const led_frame_check_t *sim_check(const rmt_symbol_word_t *symbols,unsigned count,
        const uint8_t *bytes,unsigned size,unsigned period) {
    led_frame_check(symbols,count,bytes,size,period,&result);return &result;
}
