#pragma once
#include "driver/rmt_tx.h"

/* Temporary RX on the existing TX pad. Does not observe a LED's DOUT. */
void led_probe_begin(int pin);
void led_probe_end(int pin, const rmt_symbol_word_t *expected, unsigned bits, esp_err_t tx_error);
void led_probe_frame_end(int pin, const uint8_t *expected, unsigned bytes,
                         unsigned profile, unsigned encoder, esp_err_t tx_error);
