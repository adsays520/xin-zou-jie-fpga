open_project guitar_audio_low_speed.gprj
set handle [open build_ddr_split_v9.tcl r]
set content [read $handle]
close $handle
foreach line [split $content "\n"] {
    if {[regexp {^\s*set_option\s+} $line]} {
        uplevel #0 $line
    }
}
puts "PASS V9 DDR-split backend options accepted; no implementation launched"
exit
