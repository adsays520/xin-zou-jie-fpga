#pragma once

#include <stdbool.h>
#include <stdint.h>

typedef struct {
    uint8_t keys[16];
    uint8_t instrument;
    bool hall_mode;
    bool enabled;
    bool initialized;
} note_trace_state_t;

void note_trace_key(uint8_t key, bool down, const char *reason);
void note_trace_ack(note_trace_state_t *state, uint16_t sequence,
                    const uint8_t keys[16], uint8_t instrument,
                    bool hall_mode, bool enabled);
