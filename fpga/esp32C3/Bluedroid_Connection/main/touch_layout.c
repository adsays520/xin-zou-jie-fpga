#include "touch_layout.h"

/* Body: 琴身表.xlsx, Sheet1!B2:G9, unchanged keys 1..48.
 * Frets: 品位图.xlsx, Sheet1!B2:G14, keys 49..126.
 * User confirmed subtracting 1 from new-sheet prefixes 4..8 -> 3..7.
 * Each section is top-to-bottom, with each row left-to-right. */
const touch_source_t g_touch_layout[] = {
    {0, 11}, {0, 10}, {0, 9},  {0, 8},  {0, 7}, {0, 6},
    {0, 12}, {0, 13}, {0, 14}, {0, 0},  {0, 5}, {0, 4},
    {0, 15}, {0, 3},  {0, 2},  {0, 1},  {1, 7}, {1, 6},
    {1, 11}, {1, 10}, {1, 9},  {1, 8},  {1, 5}, {1, 4},
    {1, 12}, {1, 13}, {1, 14}, {1, 15}, {1, 3}, {1, 2},
    {2, 10}, {2, 9},  {2, 8},  {2, 7},  {1, 1}, {1, 0},
    {2, 12}, {2, 13}, {2, 11}, {2, 6},  {2, 5}, {2, 4},
    {2, 14}, {2, 15}, {2, 3},  {2, 2},  {2, 1}, {2, 0},

    {3, 12}, {3, 11}, {3, 10}, {3, 9}, {3, 8}, {3, 7},
    {3, 13}, {3, 14}, {3, 15}, {3, 6}, {3, 5}, {3, 4},
    {3, 3},  {3, 2},  {3, 1},  {3, 0}, {4, 8}, {4, 7},
    {4, 11}, {4, 10}, {4, 9},  {4, 6}, {4, 5}, {4, 4},
    {4, 12}, {4, 14}, {4, 3},  {4, 2}, {4, 1}, {4, 0},
    {4, 13}, {4, 15}, {5, 10}, {5, 9}, {5, 8}, {5, 7},
    {5, 13}, {5, 12}, {5, 11}, {5, 6}, {5, 5}, {5, 4},
    {5, 14}, {5, 15}, {5, 3},  {5, 2}, {5, 1}, {5, 0},
    {6, 12}, {6, 11}, {6, 10}, {6, 8}, {6, 7}, {6, 6},
    {6, 14}, {6, 13}, {6, 9},  {6, 5}, {6, 4}, {6, 0},
    {6, 15}, {6, 3},  {6, 2},  {6, 1}, {7, 7}, {7, 6},
    {7, 11}, {7, 10}, {7, 9},  {7, 8}, {7, 5}, {7, 4},
    {7, 12}, {7, 13}, {7, 3},  {7, 2}, {7, 1}, {7, 0},
};

_Static_assert(sizeof(g_touch_layout) / sizeof(g_touch_layout[0]) == TOUCH_LAYOUT_KEYS,
               "Expected exactly 126 physical keys");
_Static_assert(TOUCH_LAYOUT_KEYS <= UINT8_MAX, "Key numbers must fit uint8_t");

uint8_t touch_layout_key_for_source(uint8_t chip, uint8_t channel)
{
    for (uint8_t i = 0; i < TOUCH_LAYOUT_KEYS; ++i) {
        if (g_touch_layout[i].chip == chip && g_touch_layout[i].channel == channel) {
            return i + 1;
        }
    }
    return 0;
}

bool touch_layout_validate(void)
{
    uint16_t used[TOUCH_LAYOUT_CHIP_COUNT] = {0};
    for (uint8_t i = 0; i < TOUCH_LAYOUT_KEYS; ++i) {
        const touch_source_t source = g_touch_layout[i];
        if (source.chip >= TOUCH_LAYOUT_CHIP_COUNT || source.channel >= 16U) {
            return false;
        }
        uint16_t mask = (uint16_t)1U << source.channel;
        if ((used[source.chip] & mask) != 0) {
            return false;
        }
        used[source.chip] |= mask;
    }
    /* Exercise the real encoder at startup, especially keys above bit 63.
     * Only RAM is used; this does not access or write any touch chip. */
    uint16_t buttons[TOUCH_LAYOUT_CHIP_COUNT] = {0};
    char hex[TOUCH_LAYOUT_STATE_HEX_DIGITS + 1U];
    static const char digits[] = "0123456789ABCDEF";
    touch_layout_format_state(buttons, hex);
    for (unsigned p = 0; p < TOUCH_LAYOUT_STATE_HEX_DIGITS; ++p) {
        if (hex[p] != '0') return false;
    }
    for (uint8_t i = 0; i < TOUCH_LAYOUT_KEYS; ++i) {
        const touch_source_t source = g_touch_layout[i];
        buttons[source.chip] = (uint16_t)1U << source.channel;
        touch_layout_format_state(buttons, hex);
        for (unsigned p = 0; p < TOUCH_LAYOUT_STATE_HEX_DIGITS; ++p) {
            char expected = p == TOUCH_LAYOUT_STATE_HEX_DIGITS - 1U - i / 4U
                                ? digits[1U << (i % 4U)] : '0';
            if (hex[p] != expected) return false;
        }
        if (hex[TOUCH_LAYOUT_STATE_HEX_DIGITS] != '\0') return false;
        buttons[source.chip] = 0;
    }
    /* Unmapped electrodes must never become extra physical keys. */
    for (uint8_t chip = 0; chip < TOUCH_LAYOUT_CHIP_COUNT; ++chip) {
        buttons[chip] = (uint16_t)~used[chip];
    }
    touch_layout_format_state(buttons, hex);
    for (unsigned p = 0; p < TOUCH_LAYOUT_STATE_HEX_DIGITS; ++p) {
        if (hex[p] != '0') return false;
    }
    for (uint8_t chip = 0; chip < TOUCH_LAYOUT_CHIP_COUNT; ++chip) {
        buttons[chip] = UINT16_MAX;
    }
    touch_layout_format_state(buttons, hex);
    for (unsigned p = 0; p < TOUCH_LAYOUT_STATE_HEX_DIGITS; ++p) {
        char expected = p == 0 && TOUCH_LAYOUT_KEYS % 4U != 0
                            ? digits[(1U << (TOUCH_LAYOUT_KEYS % 4U)) - 1U] : 'F';
        if (hex[p] != expected) return false;
    }
    return true;
}

uint16_t touch_layout_used_channels(uint8_t chip)
{
    uint16_t mask = 0;
    for (uint8_t i = 0; i < TOUCH_LAYOUT_KEYS; ++i) {
        if (g_touch_layout[i].chip == chip) {
            mask |= (uint16_t)1U << g_touch_layout[i].channel;
        }
    }
    return mask;
}

void touch_layout_format_state(const uint16_t buttons[TOUCH_LAYOUT_CHIP_COUNT],
                               char hex[TOUCH_LAYOUT_STATE_HEX_DIGITS + 1U])
{
    static const char digits[] = "0123456789ABCDEF";
    uint8_t nibbles[TOUCH_LAYOUT_STATE_HEX_DIGITS] = {0};
    for (uint8_t i = 0; i < TOUCH_LAYOUT_KEYS; ++i) {
        const touch_source_t source = g_touch_layout[i];
        if ((buttons[source.chip] & ((uint16_t)1U << source.channel)) != 0) {
            nibbles[i / 4U] |= (uint8_t)(1U << (i % 4U));
        }
    }
    for (unsigned i = 0; i < TOUCH_LAYOUT_STATE_HEX_DIGITS; ++i) {
        hex[i] = digits[nibbles[TOUCH_LAYOUT_STATE_HEX_DIGITS - 1U - i]];
    }
    hex[TOUCH_LAYOUT_STATE_HEX_DIGITS] = '\0';
}
