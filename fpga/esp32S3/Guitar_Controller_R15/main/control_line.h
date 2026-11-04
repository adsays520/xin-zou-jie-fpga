#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct {
    char text[96];
    size_t used;
    bool discard;
} control_line_t;

bool control_line_feed(control_line_t *state, uint8_t byte);
