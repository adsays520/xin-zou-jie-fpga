#pragma once
#include "driver/rmt_tx.h"

/* Decode three actual, consecutive frames. Interior idle intervals bound the
 * middle frame even when RMT omits the initial/final idle from its RX buffer. */
typedef struct {
    unsigned frames, bits[3], total_bits;
    unsigned data_errors, width_errors, period_errors, structure_errors;
    unsigned head_low_ticks, tail_low_ticks;
    unsigned zero_min, zero_max, one_min, one_max, period_min, period_max;
    uint8_t middle[42];
    uint32_t expected_crc, middle_crc;
    bool reset_measured, reset_ok, passed;
} led_frame_check_t;

void led_frame_check(const rmt_symbol_word_t *symbols, unsigned count,
                     const uint8_t *expected, unsigned bytes, unsigned period_ticks,
                     led_frame_check_t *result);
