open_project guitar_audio_low_speed.gprj
set handle [open build_merged.tcl r]
set content [read $handle]
close $handle
foreach line [split $content "\n"] {
    if {[regexp {^\s*set_option\s+} $line]} {
        uplevel #0 $line
    }
}
puts "PASS V9 backend options accepted; no synthesis or PnR launched"
exit
