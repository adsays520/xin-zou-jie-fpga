open_project guitar_audio_low_speed.gprj
set_option -output_base_name ensemble_panel_v14
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
if {$env(PANEL_V14_PHASE) eq "synthesis"} {
    run syn
    puts "V14 new synthesis finished"
    exit
}
puts [exec $env(V14_PYTHON) -B -X utf8 scripts/check_functional_v14.py]
set started [clock seconds]
run pnr
source scripts/check_timing.tcl
source scripts/check_ddr_pulse.tcl
check_excitation_timing ensemble_panel_v14 $started
check_ddr_pulse ensemble_panel_v14
puts "V14 timing PASS: setup=0 hold=0"
exit

