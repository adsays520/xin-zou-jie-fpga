#include "control_line.h"

bool control_line_feed(control_line_t *state, uint8_t byte)
{
    if (byte == '\r' || byte == '\n') {
        bool complete = !state->discard && state->used != 0;
        state->text[state->used] = '\0';
        state->used = 0;
        state->discard = false;
        return complete;
    }
    if (state->discard) return false;
    if (byte < 32 || byte > 126 || state->used == sizeof(state->text) - 1) {
        state->used = 0;
        state->discard = true;
        return false;
    }
    state->text[state->used++] = (char)byte;
    return false;
}
