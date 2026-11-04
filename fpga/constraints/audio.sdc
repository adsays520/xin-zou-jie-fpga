# R7: original audio stays at 50 MHz; only excitation storage uses DDR.
create_clock -name sys_clk -period 20.000 -waveform {0.000 10.000} [get_ports {clk}]
create_generated_clock -name mem400 -source [get_ports {clk}] -master_clock sys_clk -divide_by 1 -multiply_by 8 [get_pins {u_ddr_pll/PLL_inst/CLKOUT2}]
create_generated_clock -name ddr_user100 -source [get_pins {u_ddr_pll/PLL_inst/CLKOUT2}] -master_clock mem400 -divide_by 4 -multiply_by 1 [get_pins {u_ddr3/gw3_top/u_ddr_phy_top/fclkdiv/CLKOUT}]
# Keep 50/100 MHz pointer paths visible. No clock-group cut may override bounds.
create_generated_clock -name ddr_ref100 -source [get_ports {clk}] -master_clock sys_clk -divide_by 1 -multiply_by 2 [get_pins {u_ddr_pll/PLL_inst/CLKOUT1}]
set_clock_groups -asynchronous -group [get_clocks {ddr_ref100}] -group [get_clocks {mem400}] -group [get_clocks {sys_clk ddr_user100}]
set_max_delay 8.000 -from [get_clocks {sys_clk ddr_user100}] -to [get_pins {u_memory/u_requests/*gray_meta*/D u_memory/u_responses/*gray_meta*/D}]
set_false_path -hold -to [get_pins {u_memory/u_requests/*gray_meta*/D u_memory/u_responses/*gray_meta*/D}]
set_false_path -to [get_pins {mem_up_meta*/D fault_meta*/D}]

report_timing -setup -from_clock [get_clocks {sys_clk}] -to_clock [get_clocks {sys_clk}] -max_paths 25 -max_common_paths 1
report_timing -setup -from_clock [get_clocks {ddr_user100}] -to_clock [get_clocks {ddr_user100}] -max_paths 25 -max_common_paths 1
report_timing -setup -max_paths 50 -max_common_paths 1
report_exceptions -setup -max_paths 32 -max_common_paths 1
report_timing -setup -from_clock [get_clocks {ddr_ref100}] -to_clock [get_clocks {ddr_ref100}] -max_paths 25 -max_common_paths 1
set_false_path -to [get_pins {mem_pipe*/CLEAR sys_pipe*/CLEAR}]

set_max_delay 20.000 -from [get_clocks {sys_clk}] -to [get_ports {HP_BCK HP_WS HP_DIN}]
report_timing -setup -to [get_ports {HP_BCK HP_WS HP_DIN}] -max_paths 12 -max_common_paths 1
