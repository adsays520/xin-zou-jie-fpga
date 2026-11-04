# Gowin may return success and emit a bitstream despite STA violations.
# Require explicit zero setup/hold counts before calling a build verified.
if {![info exists timing_report]} {
    set timing_report impl/pnr/guitar_audio_fx_tr_content.html
}
if {![file exists $timing_report]} {error "FX timing report missing: $timing_report"}
set timing_file [open $timing_report r]
set timing_html [read $timing_file]
close $timing_file
if {![regexp {Numbers of Setup Violated Endpoints</td>\s*<td>([0-9]+)</td>} $timing_html match setup_count]} {
    error "Cannot parse FX setup timing report"
}
if {![regexp {Numbers of Hold Violated Endpoints</td>\s*<td>([0-9]+)</td>} $timing_html match hold_count]} {
    error "Cannot parse FX hold timing report"
}
if {$setup_count != 0 || $hold_count != 0} {
    error "FX timing not met: setup=$setup_count, hold=$hold_count. Bitstream is unverified."
}
if {![regexp {<td>sys_clk</td>\s*<td>50\.000\(MHz\)</td>\s*<td[^>]*>([0-9.]+)\(MHz\)} $timing_html match actual_fmax]} {
    error "Cannot verify the 50 MHz FX clock constraint"
}
if {$actual_fmax < 50.0} {error "FX Fmax below 50 MHz: $actual_fmax"}
puts "PASS FX timing: setup=0 hold=0 Fmax=$actual_fmax MHz"
