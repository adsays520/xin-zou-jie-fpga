#include "hall_detector.h"
#include <string.h>

void hall_detector_reset(hall_detector_t *detector)
{
    memset(detector, 0, sizeof(*detector));
    detector->minimum = UINT16_MAX;
}

static uint16_t median_three(const uint16_t history[3])
{
    uint16_t lower = history[0] < history[1] ? history[0] : history[1];
    uint16_t upper = history[0] > history[1] ? history[0] : history[1];
    return history[2] < lower ? lower : (history[2] > upper ? upper : history[2]);
}

static void finish_calibration(hall_detector_t *detector, uint16_t minimum_trigger)
{
    for (unsigned index = 1; index < 128; ++index) {
        uint16_t value = detector->samples[index];
        unsigned position = index;
        while (position > 0 && detector->samples[position - 1] > value) {
            detector->samples[position] = detector->samples[position - 1];
            --position;
        }
        detector->samples[position] = value;
    }
    uint16_t neutral = (uint16_t)(((unsigned)detector->samples[63] + detector->samples[64]) / 2U);
    detector->baseline_q8 = (int32_t)neutral << 8;
    detector->noise = detector->samples[115] - detector->samples[12];
    unsigned threshold = (unsigned)detector->noise * 3U + 8U;
    if (threshold < minimum_trigger) threshold = minimum_trigger;
    detector->threshold = (uint16_t)(threshold > 4095U ? 4095U : threshold);
    unsigned available = neutral > 4095U - neutral ? neutral : 4095U - neutral;
    unsigned noise_limit = minimum_trigger > 128U ? minimum_trigger : 128U;
    detector->calibration = HALL_CAL_OK;
    if (neutral < 64U || neutral > 4031U) detector->calibration = HALL_CAL_RAIL;
    else if (threshold > available) detector->calibration = HALL_CAL_UNREACHABLE;
    else if (threshold > noise_limit) detector->calibration = HALL_CAL_NOISY;
    detector->valid = detector->calibration == HALL_CAL_OK;
    detector->state = detector->valid ? 1 : 4;
    for (unsigned index = 0; index < 3; ++index) detector->history[index] = neutral;
}

bool hall_detector_sample(hall_detector_t *detector, uint16_t raw, uint32_t now_ms,
                          uint16_t minimum_trigger, uint16_t full_scale, uint8_t *velocity)
{
    if (detector->state == 0) {
        detector->samples[detector->count++] = raw;
        if (raw < detector->minimum) detector->minimum = raw;
        if (raw > detector->maximum) detector->maximum = raw;
        if (detector->count == 128) finish_calibration(detector, minimum_trigger);
        return false;
    }
    int raw_displacement = (int)raw - (detector->baseline_q8 >> 8);
    unsigned raw_magnitude = (unsigned)(raw_displacement < 0 ? -raw_displacement : raw_displacement);
    if (raw_magnitude > detector->raw_peak) detector->raw_peak = (uint16_t)raw_magnitude;
    detector->history[detector->history_index] = raw;
    detector->history_index = (detector->history_index + 1U) % 3U;
    uint16_t filtered = median_three(detector->history);
    int displacement = (int)filtered - (detector->baseline_q8 >> 8);
    unsigned magnitude = (unsigned)(displacement < 0 ? -displacement : displacement);
    if (magnitude > detector->filtered_peak) detector->filtered_peak = (uint16_t)magnitude;
    if (!detector->valid) return false;
    unsigned release_threshold = (unsigned)detector->threshold * 3U / 4U;
    if (detector->state == 1) {
        if (magnitude >= detector->threshold) {
            int8_t direction = displacement < 0 ? -1 : 1;
            if (direction != detector->direction) detector->confirmation = 0;
            detector->direction = direction;
            if (++detector->confirmation >= 3) {
                detector->state = 2;
                detector->peak = (uint16_t)magnitude;
                detector->deadline = now_ms + 4U;
                detector->confirmation = 0;
            }
        } else {
            detector->confirmation = 0;
            if (magnitude < detector->threshold / 2U)
                detector->baseline_q8 += (((int32_t)filtered << 8) - detector->baseline_q8) / 256;
        }
    } else if (detector->state == 2) {
        if (magnitude > detector->peak) detector->peak = (uint16_t)magnitude;
        if ((int32_t)(now_ms - detector->deadline) >= 0) {
            unsigned scale = full_scale > detector->threshold ? full_scale : detector->threshold + 1U;
            unsigned strength = 12U + (unsigned)detector->peak * 115U / scale;
            *velocity = (uint8_t)(strength > 127U ? 127U : strength);
            detector->state = 3;
            detector->last_event = now_ms;
            detector->release_count = 0;
            return true;
        }
    } else if (detector->state == 3) {
        if ((uint32_t)(now_ms - detector->last_event) >= 35U && magnitude < release_threshold) {
            if (++detector->release_count >= 3) {
                detector->state = 1;
                detector->release_count = 0;
            }
        } else detector->release_count = 0;
    }
    return false;
}

bool hall_detector_selftest(void)
{
    hall_detector_t detector;
    uint8_t velocity = 0;
    unsigned events = 0;
    hall_detector_reset(&detector);
    for (unsigned sample = 0; sample < 128; ++sample)
        if (hall_detector_sample(&detector, 1500, sample, 32, 700, &velocity)) return false;
    if (!detector.valid || detector.threshold != 32) return false;
    for (unsigned sample = 128; sample < 200; ++sample)
        events += hall_detector_sample(&detector, 2200, sample, 32, 700, &velocity);
    if (events != 1 || velocity != 127) return false;
    for (unsigned sample = 200; sample < 240; ++sample)
        events += hall_detector_sample(&detector, 1520, sample, 32, 700, &velocity);
    for (unsigned sample = 240; sample < 250; ++sample)
        events += hall_detector_sample(&detector, 1300, sample, 32, 700, &velocity);
    if (events != 2 || velocity < 1 || velocity > 127) return false;
    hall_detector_reset(&detector);
    for (unsigned sample = 0; sample < 200; ++sample)
        if (hall_detector_sample(&detector, 0, sample, 32, 700, &velocity)) return false;
    return !detector.valid;
}
