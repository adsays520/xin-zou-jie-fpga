proc check_ddr_pulse {build_name} {
    set handle [open impl/pnr/${build_name}_tr_content.html r]
    set html [read $handle]
    close $handle
    if {![regexp {name="MIN_PULSE_WIDTH_TABLE"(.*?)</table>} $html match section]} {
        error "Missing minimum pulse width table"
    }
    set values [regexp -all -inline {<tr[^>]*>\s*<td>[0-9]+</td>\s*<td>([-0-9.]+)</td>} $section]
    if {[llength $values] == 0} {error "No minimum pulse width results"}
    foreach {row slack} $values {
        if {$slack < 0} {error "Minimum pulse width did not pass: $slack ns"}
    }
    puts "PASS minimum pulse width for $build_name"
}
