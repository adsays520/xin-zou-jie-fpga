#pragma once
#include <stdbool.h>
#include <stdint.h>
#define LED_COUNT 27
#define LED_GUIDE_CAPACITY 256
typedef struct { uint32_t at_ms, duration_ms; uint8_t position, string_number; } led_cue_t;
/* Global index 0..12=GPIO3, 13..26=GPIO7. Position is physical 1..21. */
int led_position_pixel(unsigned position);
int led_string_pixel(unsigned string_number);
bool led_cue_valid(const led_cue_t *cue);
void led_live_mask(const uint8_t keys[16], uint32_t *mask);
uint32_t led_cue_mask(const led_cue_t *cues, unsigned count, uint32_t elapsed_ms);
/* Continuous local showcase; bounded by level, GRB output, 20ms animation steps. */
void led_demo_frame(uint64_t elapsed_ms, uint8_t level, uint32_t live,
                    uint32_t picks, uint8_t grb[LED_COUNT*3]);
