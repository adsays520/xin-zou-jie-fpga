proc check_excitation_timing {build_name started} {
    set base impl/pnr/$build_name
    foreach suffix {.fs .rpt.txt _tr_content.html} {
        set path ${base}${suffix}
        if {![file exists $path] || [file mtime $path] < $started} {
            error "Missing or stale build output: $path"
        }
    }
    set handle [open ${base}_tr_content.html r]
    set html [read $handle]
    close $handle
    foreach kind {Setup Hold} {
        set pattern [format {Numbers of %s Violated Endpoints</td>\s*<td>([0-9]+)</td>} $kind]
        if {![regexp $pattern $html match count] || $count != 0} {
            error "R10 Pro DDR $kind timing did not pass"
        }
    }
    foreach {clock frequency} {sys_clk 50.000 ddr_user100 100.000 mem400 400.000 ddr_ref100 100.000} {
        set pattern [format {<td>%s</td>\s*<td>%s\(MHz\)</td>\s*<td[^>]*>([0-9.]+)\(MHz\)</td>} $clock $frequency]
        if {![regexp $pattern $html match actual] || $actual < $frequency} {
            error "Missing or failing Fmax for $clock"
        }
    }
    if {![regexp {<td>TC_MAX_DELAY</td>\s*<td>Actived</td>\s*<td>set_max_delay 8\.000 } $html]} {
        error "Gray pointer maximum delay is not active"
    }
    if {[regexp {<td>(Inactived|Inactive|Invalid|Ignored)</td>} $html]} {
        error "Inactive timing constraints require review"
    }
    puts "R10 Pro DDR PASS: current bitstream, all four clocks, Setup/Hold and Gray pointer bounds"
}
