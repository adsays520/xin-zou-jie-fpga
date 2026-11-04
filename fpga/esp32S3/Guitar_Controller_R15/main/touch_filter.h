#pragma once

#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#define TOUCH_STALE_US 60000
#define TOUCH_FAILURE_LIMIT 3

typedef struct {
    int64_t last_good_us;
    int64_t last_confirmed_us;
    uint16_t buttons;
    uint16_t candidate;
    uint8_t failures;
    bool candidate_valid;
    bool online;
} touch_filter_t;

static inline bool touch_filter_fresh(const touch_filter_t *state, int64_t now_us)
{
    return state->online && now_us - state->last_good_us < TOUCH_STALE_US &&
           now_us - state->last_confirmed_us < TOUCH_STALE_US;
}

static inline uint16_t touch_filter_accept(touch_filter_t *state, uint16_t buttons,
                                          int64_t now_us)
{
    uint16_t previous = state->buttons;
    if (!touch_filter_fresh(state, now_us)) {
        state->buttons = 0;
        state->candidate_valid = false;
        state->last_confirmed_us = now_us;
    }
    if (state->candidate_valid) {
        uint16_t consistent = (uint16_t)~(buttons ^ state->candidate);
        state->buttons = (state->buttons & (uint16_t)~consistent) | (buttons & consistent);
        state->last_confirmed_us = now_us;
    }
    state->candidate = buttons;
    state->candidate_valid = true;
    state->failures = 0;
    state->online = true;
    state->last_good_us = now_us;
    return previous ^ state->buttons;
}

static inline bool touch_filter_fail(touch_filter_t *state, int64_t now_us)
{
    state->candidate_valid = false;
    if (state->failures < UINT8_MAX) ++state->failures;
    (void)now_us;
    return state->online && state->failures >= TOUCH_FAILURE_LIMIT;
}

static inline uint16_t touch_filter_release_stale(touch_filter_t *state)
{
    uint16_t released = state->buttons;
    state->buttons = 0;
    state->candidate_valid = false;
    return released;
}

static inline uint16_t touch_filter_disconnect(touch_filter_t *state)
{
    uint16_t released = state->buttons;
    memset(state, 0, sizeof(*state));
    return released;
}

static inline bool touch_filter_self_test(void)
{
    touch_filter_t state = {0};
    if (touch_filter_fresh(&state, 0)) return false;
    if (touch_filter_accept(&state, 1, 1000) != 0 || state.buttons != 0) return false;
    if (touch_filter_accept(&state, 1, 6000) != 1 || state.buttons != 1) return false;
    if (touch_filter_fail(&state, 11000) || state.buttons != 1) return false;
    if (touch_filter_accept(&state, 0, 16000) != 0 || state.buttons != 1) return false;
    if (touch_filter_accept(&state, 0, 21000) != 1 || state.buttons != 0) return false;
    if (touch_filter_accept(&state, 3, 26000) != 0) return false;
    if (touch_filter_accept(&state, 1, 31000) != 1 || state.buttons != 1) return false;
    if (touch_filter_fail(&state, 36000) || touch_filter_fail(&state, 41000)) return false;
    if (!touch_filter_fail(&state, 46000)) return false;
    if (touch_filter_disconnect(&state) != 1 || state.online || state.buttons != 0) return false;
    if (touch_filter_accept(&state, UINT16_MAX, 51000) != 0) return false;
    if (touch_filter_accept(&state, UINT16_MAX, 56000) != UINT16_MAX) return false;
    if (!touch_filter_fresh(&state, 115999) || touch_filter_fresh(&state, 116000)) return false;
    if (touch_filter_accept(&state, 1, 116000) != UINT16_MAX || state.buttons != 0) return false;
    if (touch_filter_accept(&state, 1, 121000) != 1 || state.buttons != 1) return false;
    touch_filter_disconnect(&state);
    touch_filter_accept(&state, 1, 200000);
    touch_filter_accept(&state, 1, 205000);
    for (unsigned attempt = 0; attempt < 5; ++attempt) {
        if (touch_filter_fail(&state, 210000 + 10000 * attempt)) return false;
        if (touch_filter_accept(&state, 0, 215000 + 10000 * attempt) != 0) return false;
    }
    if (!touch_filter_fresh(&state, 264999) || touch_filter_fresh(&state, 265000)) return false;
    if (touch_filter_accept(&state, 0, 265000) != 1 || state.buttons != 0) return false;
    touch_filter_disconnect(&state);
    touch_filter_accept(&state, 1, 300000);
    touch_filter_accept(&state, 1, 305000);
    if (touch_filter_fail(&state, 366000)) return false;
    if (touch_filter_release_stale(&state) != 1 || !state.online || state.buttons != 0) return false;
    if (state.last_good_us != 305000 || touch_filter_fresh(&state, 366000)) return false;
    if (touch_filter_accept(&state, 1, 367000) != 0) return false;
    if (touch_filter_accept(&state, 1, 372000) != 1) return false;
    return true;
}
