#include "fpga_scheduler.h"

fpga_schedule_kind_t fpga_schedule_next(fpga_scheduler_t *scheduler, bool command_available, bool pick_available)
{
    if (pick_available && (!command_available || scheduler->prefer_pick)) {
        scheduler->prefer_pick = false;
        return FPGA_SCHEDULE_PICK;
    }
    if (command_available) {
        scheduler->prefer_pick = true;
        return FPGA_SCHEDULE_COMMAND;
    }
    return FPGA_SCHEDULE_NONE;
}
