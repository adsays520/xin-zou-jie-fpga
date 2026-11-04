#pragma once

#include <stdbool.h>
#include <stdint.h>

#define TOUCH_BODY_ROWS 8U
#define TOUCH_FRET_ROWS 13U
#define TOUCH_LAYOUT_ROWS (TOUCH_BODY_ROWS + TOUCH_FRET_ROWS)
#define TOUCH_LAYOUT_COLS 6U
#define TOUCH_BODY_KEYS (TOUCH_BODY_ROWS * TOUCH_LAYOUT_COLS)
#define TOUCH_FRET_KEYS (TOUCH_FRET_ROWS * TOUCH_LAYOUT_COLS)
#define TOUCH_LAYOUT_KEYS (TOUCH_LAYOUT_ROWS * TOUCH_LAYOUT_COLS)
#define TOUCH_LAYOUT_CHIP_COUNT 8U
#define TOUCH_LAYOUT_STATE_HEX_DIGITS ((TOUCH_LAYOUT_KEYS + 3U) / 4U)

typedef struct {
    uint8_t chip;     /* Normalized prefix 0..7; new sheet prefixes minus 1. */
    uint8_t channel;  /* CY8CMBR3116 的 CS0..CS15 */
} touch_source_t;

/* Body keys 1..48 unchanged; fret keys 49..126 follow the new sheet. */
extern const touch_source_t g_touch_layout[];

/* Returns 1..126, or 0 for an unmapped channel (including chip 7 CS14/15). */
uint8_t touch_layout_key_for_source(uint8_t chip, uint8_t channel);

/* Validate ranges and uniqueness before starting polling. */
bool touch_layout_validate(void);
uint16_t touch_layout_used_channels(uint8_t chip);

/* Bit 0 = key 1. Output high-to-low hex, including leading zeros. */
void touch_layout_format_state(const uint16_t buttons[TOUCH_LAYOUT_CHIP_COUNT],
                               char hex[TOUCH_LAYOUT_STATE_HEX_DIGITS + 1U]);
