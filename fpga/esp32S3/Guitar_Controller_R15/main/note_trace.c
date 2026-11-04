#include "note_trace.h"

#include <stdio.h>
#include <string.h>
#include "touch_layout.h"
#include "touch_output.h"

static const uint8_t s_open_midi[6] = {40, 45, 50, 55, 59, 64};
static const uint8_t s_violin_midi[6] = {55, 55, 55, 62, 69, 76};
static const char *const s_note_names[12] = {
    "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
};

static const char *instrument_name(uint8_t instrument)
{
    static const char *const names[] = {"GUITAR", "PIANO", "BASS", "VIOLIN"};
    return instrument < 4 ? names[instrument] : "UNKNOWN";
}

void note_trace_key(uint8_t key, bool down, const char *reason)
{
    if (key == 0 || key > TOUCH_LAYOUT_KEYS) return;
    unsigned index = key - 1U;
    touch_source_t source = g_touch_layout[index];
    TOUCH_LOGI("NOTE_KEY", "%s chip=%u cs=%u key=%u string=%u fret=%u reason=%s",
               down ? "DOWN" : "UP", source.chip, source.channel, key,
               6U - index % 6U, index / 6U, reason);
}

void note_trace_ack(note_trace_state_t *state, uint16_t sequence,
                    const uint8_t keys[16], uint8_t instrument,
                    bool hall_mode, bool enabled)
{
    if (!state->initialized || state->instrument != instrument ||
        state->hall_mode != hall_mode || state->enabled != enabled) {
        TOUCH_LOGI("NOTE_MODE", "instrument=%s mode=%s enabled=%u seq=%u",
                   instrument_name(instrument), hall_mode ? "PICK" : "DIRECT",
                   (unsigned)enabled, sequence);
    }
    for (unsigned index = 0; index < TOUCH_LAYOUT_KEYS; ++index) {
        uint8_t mask = (uint8_t)(1U << (index % 8U));
        if (((state->keys[index / 8U] ^ keys[index / 8U]) & mask) == 0) continue;
        bool down = (keys[index / 8U] & mask) != 0;
        unsigned column = index % 6U;
        unsigned fret = index / 6U;
        int midi = s_open_midi[column] + fret;
        const char *role = instrument == 1 ? (down ? "NOTE_ON" : "NOTE_OFF") :
                           (down ? "PLUCK" : "KEY_RELEASE");
        if (instrument == 2) {
            midi -= 12;
            if (column >= 4) role = "BASS_UNUSED";
        } else if (instrument == 3) {
            midi = s_violin_midi[column] + fret;
            role = "MONO_CANDIDATE";
        } else if (instrument > 3) {
            role = "UNKNOWN";
        }
        if (hall_mode) role = "FRET_SELECT";
        if (!enabled) role = "TOUCH_DISABLED";
        char note[12];
        if (instrument > 3 || (instrument == 2 && column >= 4)) {
            midi = -1;
            snprintf(note, sizeof(note), "NONE");
        } else {
            snprintf(note, sizeof(note), "%s%d", s_note_names[midi % 12], midi / 12 - 1);
        }
        touch_source_t source = g_touch_layout[index];
        TOUCH_LOGI("NOTE_ACK", "%s chip=%u cs=%u key=%u note=%s midi=%d instrument=%s role=%s seq=%u",
                   down ? "DOWN" : "UP", source.chip, source.channel, index + 1U,
                   note, midi, instrument_name(instrument), role, sequence);
    }
    memcpy(state->keys, keys, sizeof(state->keys));
    state->instrument = instrument;
    state->hall_mode = hall_mode;
    state->enabled = enabled;
    state->initialized = true;
}
