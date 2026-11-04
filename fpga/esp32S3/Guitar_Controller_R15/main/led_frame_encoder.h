#pragma once
#include "driver/rmt_encoder.h"

/* profile0=XL800, 1=legacy800, 2=SLOW714. Input is a complete GRB byte frame. */
esp_err_t led_frame_encoder_new(unsigned profile,rmt_encoder_handle_t *encoder);
