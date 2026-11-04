#pragma once
#include <stdbool.h>

typedef enum {
    FPGA_SCHEDULE_NONE,
    FPGA_SCHEDULE_COMMAND,
    FPGA_SCHEDULE_PICK
} fpga_schedule_kind_t;

typedef struct {
    bool prefer_pick;
} fpga_scheduler_t;

fpga_schedule_kind_t fpga_schedule_next(fpga_scheduler_t *scheduler, bool command_available, bool pick_available);
