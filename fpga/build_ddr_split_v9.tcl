open_project guitar_audio_low_speed.gprj
set_option -output_base_name ensemble_daw_v9_ddr_split
set_option -top_module guitar_audio_ddr_top
set_option -include_path [pwd]
set_option -timing_driven 1
set_option -gen_text_timing_rpt 1
set_option -use_cpu_as_gpio 1
set_option -global_freq 50.000
set_option -bit_compress 0
set_option -place_option 2
set_option -route_option 2
set_option -clock_route_order 1
set_option -route_maxfan 23
set_option -correct_hold_violation 1
set_option -convert_sdp32_36_to_sdp16_18 1
set_option -replicate_resources 1
set_option -inc_place 0
set_option -inc_pnr 0
run syn
puts [exec $env(V9_PYTHON) -B scripts/check_ddr_split_gate_v9.py]
set started [clock seconds]
run pnr
source scripts/check_timing.tcl
source scripts/check_ddr_pulse.tcl
check_excitation_timing ensemble_daw_v9_ddr_split $started
check_ddr_pulse ensemble_daw_v9_ddr_split
puts "V9 DDR-split timing PASS: setup=0 hold=0"
exit
