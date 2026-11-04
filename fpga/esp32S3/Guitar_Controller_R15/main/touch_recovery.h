#pragma once

#include <stdbool.h>
#include <stdint.h>

#define TOUCH_PROBE_MIN_US 10000
#define TOUCH_PROBE_MAX_US 200000

typedef enum {
    TOUCH_PROBE_ID,
    TOUCH_PROBE_SENSORS,
    TOUCH_PROBE_BUTTONS,
} touch_probe_phase_t;

typedef struct {
    int64_t next_us;
    uint8_t failures;
    touch_probe_phase_t phase;
} touch_probe_t;

static inline void touch_probe_reset(touch_probe_t *probe, int64_t now_us)
{
    probe->next_us = now_us + TOUCH_PROBE_MIN_US;
    probe->failures = 0;
    probe->phase = TOUCH_PROBE_ID;
}

static inline void touch_probe_failed(touch_probe_t *probe, int64_t now_us)
{
    if (probe->failures < 6) ++probe->failures;
    int64_t delay_us = (int64_t)TOUCH_PROBE_MIN_US << (probe->failures - 1);
    if (delay_us > TOUCH_PROBE_MAX_US) delay_us = TOUCH_PROBE_MAX_US;
    probe->next_us = now_us + delay_us;
    probe->phase = TOUCH_PROBE_ID;
}

static inline void touch_probe_advance(touch_probe_t *probe, int64_t now_us)
{
    if (probe->phase < TOUCH_PROBE_BUTTONS) ++probe->phase;
    probe->next_us = now_us;
}
