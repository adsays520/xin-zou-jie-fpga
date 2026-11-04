#pragma once
#include <stdbool.h>
#include <stdint.h>
typedef enum {
    HALL_CAL_PENDING,
    HALL_CAL_OK,
    HALL_CAL_RAIL,
    HALL_CAL_NOISY,
    HALL_CAL_UNREACHABLE
} hall_calibration_t;

typedef struct {
    uint32_t deadline,last_event;
    int32_t baseline_q8;
    uint16_t samples[128], history[3];
    uint16_t count,minimum,maximum,threshold,peak,noise,raw_peak,filtered_peak;
    uint8_t state,history_index,confirmation,release_count;
    int8_t direction;
    hall_calibration_t calibration;
    bool valid;
} hall_detector_t;
void hall_detector_reset(hall_detector_t *detector);
bool hall_detector_sample(hall_detector_t *detector, uint16_t raw, uint32_t now_ms,
                          uint16_t minimum_trigger, uint16_t full_scale, uint8_t *velocity);
bool hall_detector_selftest(void);
