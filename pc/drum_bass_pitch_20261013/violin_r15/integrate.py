from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent


def replace(source, before, after, count=1):
    if source.count(before) != count:
        raise ValueError(f'Unexpected integration anchor: {before[:90]}')
    return source.replace(before, after)


def emit(path, source):
    print('*** Add File: ' + str(path).replace('\\', '/'))
    if path.exists():
        raise ValueError(f'Refusing to overwrite existing candidate: {path}')
    print('\n'.join('+' + line for line in source.splitlines()))


def main():
    print('*** Begin Patch')
    parser = (PROJECT / 'src/guitar_uart_trigger.v').read_text()
    parser = replace(parser, '    output reg        timbre_bass,', '''    output reg        timbre_bass,
    output reg        timbre_violin,
    output reg        violin_note_on,violin_note_off,violin_legato,
    output reg [6:0]  violin_key,violin_velocity,violin_bus_level,''')
    parser = replace(parser, '            timbre_bass <= 1\'b0;', '''            timbre_bass <= 1'b0;
            timbre_violin<=0;violin_note_on<=0;violin_note_off<=0;violin_legato<=0;
            violin_key<=69;violin_velocity<=100;violin_bus_level<=127;''')
    parser = replace(parser, "        end else begin\n            trigger <= 1'b0;", "        end else begin\n            violin_note_on<=0;violin_note_off<=0;\n            trigger <= 1'b0;")
    parser = replace(parser, "                    2'd2: drum_bus_level", "                    2'd3: violin_bus_level <= violin_bus_level >= 120 ? 0 : violin_bus_level+8;\n                    2'd2: drum_bus_level")
    parser = replace(parser, "(frame_payload0 <= 8'd2)", "(frame_payload0 <= 8'd3)", 2)
    parser = replace(parser, "                            timbre_bass <= frame_payload0==8'd2;", "                            timbre_bass <= frame_payload0==8'd2;\n                            timbre_violin <= frame_payload0==8'd3;")
    parser = replace(parser, '                            (frame_command == CMD_PIANO_KEY)', '''                            (frame_command == 8'h08) &&
                            (frame_payload0 >= 55) && (frame_payload0 <= 100) &&
                            (frame_payload1 >= 1) && (frame_payload1 <= 127) &&
                            (frame_payload2 == 0 || frame_payload2 == 1 || frame_payload2 == 3)) begin
                            violin_key<=frame_payload0[6:0];violin_velocity<=frame_payload1[6:0];
                            violin_legato<=frame_payload2[1];
                            violin_note_on<=frame_payload2[0];violin_note_off<=!frame_payload2[0];
                        end else if ((rx_data == frame_xor) &&
                            (frame_command == CMD_PIANO_KEY)''')
    parser = replace(parser, "                                8'd2: drum_bus_level", "                                8'd3: violin_bus_level <= frame_payload1[6:0];\n                                8'd2: drum_bus_level")
    emit(ROOT / 'guitar_uart_trigger.v', parser)

    audio = (PROJECT / 'timing_r10c/audio_core.v').read_text()
    audio = replace(audio, '    reg timbre_bass;', '''    reg timbre_bass;
    reg timbre_violin;
    wire uart_timbre_violin,uart_violin_on,uart_violin_off,uart_violin_legato;
    wire [6:0] uart_violin_key,uart_violin_velocity,violin_bus_level;
    wire signed [23:0] violin_sample;
    wire violin_fault,violin_active;''')
    audio = replace(audio, 'wire piano_core_note_on=(note_on&&timbre_piano)||uart_piano_note_on;', 'wire piano_core_note_on=timbre_piano&&(note_on||uart_piano_note_on);')
    audio = replace(audio, 'piano_note_off_q<=uart_piano_note_off;', 'piano_note_off_q<=uart_piano_note_off&&timbre_piano;')
    audio = replace(audio, 'instrument_source_l = timbre_piano', 'instrument_source_l = timbre_violin ? violin_sample : timbre_piano')
    audio = replace(audio, 'instrument_source_r = timbre_piano', 'instrument_source_r = timbre_violin ? violin_sample : timbre_piano')
    audio = replace(audio, '.instrument_target(timbre_piano ? piano_bus_level : guitar_bus_level)', '.instrument_target(timbre_violin ? violin_bus_level : timbre_piano ? piano_bus_level : guitar_bus_level)')
    audio = replace(audio, '.piano_level(piano_bus_level)', '.piano_level(timbre_violin ? violin_bus_level : piano_bus_level)')
    audio = replace(audio, '.local_level_bus(screen_selected_bus)', ".local_level_bus(timbre_violin&&screen_selected_bus==1 ? 2'd3 : screen_selected_bus)")
    audio = replace(audio, 's3_instrument=timbre_bass', "s3_instrument=timbre_violin ? 2'd3 : timbre_bass")
    audio = replace(audio, '.timbre_bass(uart_timbre_bass),', '''.timbre_bass(uart_timbre_bass),
        .timbre_violin(uart_timbre_violin),.violin_note_on(uart_violin_on),
        .violin_note_off(uart_violin_off),.violin_legato(uart_violin_legato),
        .violin_key(uart_violin_key),.violin_velocity(uart_violin_velocity),.violin_bus_level(violin_bus_level),''')
    audio = replace(audio, '.sample_in(timbre_piano?24\'sd0:', ".sample_in((timbre_piano||timbre_violin)?24'sd0:")
    audio = replace(audio, 'lookup_note_q<=note_on&&!timbre_piano&&!timbre_bass;', 'lookup_note_q<=note_on&&!timbre_piano&&!timbre_bass&&!timbre_violin;')
    audio = replace(audio, "            timbre_bass <= 1'b0;", "            timbre_bass <= 1'b0;\n            timbre_violin <= 1'b0;")
    audio = replace(audio, '                timbre_bass <= uart_timbre_bass;', '                timbre_bass <= uart_timbre_bass;\n                timbre_violin <= uart_timbre_violin;')
    audio = replace(audio, '            if (uart_mode_set) begin', "            if (uart_mode_set) begin\n                note_on<=1'b0;")
    audio = replace(audio, '            if (uart_timbre_set) begin', "            if (uart_timbre_set) begin\n                note_on<=1'b0;")
    audio = replace(audio, '            if(drawn_mode_event&&timbre_piano)begin', "            if(drawn_mode_event&&timbre_piano)begin\n                note_on<=1'b0;")
    audio = replace(audio, 'verification_deadline_miss|poly_deadline_miss', 'violin_fault|verification_deadline_miss|poly_deadline_miss')
    audio = replace(audio, 'assign active = voice_bank_active', 'assign active = violin_active || voice_bank_active')
    audio = replace(audio, '    bass_poly8 u_bass(', '''    violin_channel u_violin_channel(
        .clk(clk),.rst_n(rst_n),.sample_tick(sample_tick),.selected(timbre_violin),
        .timbre_change(uart_timbre_set||uart_mode_set),
        .note_on(uart_violin_on),.note_off(uart_violin_off),.legato(uart_violin_legato),
        .key(uart_violin_key),.velocity(uart_violin_velocity),
        .pluck(note_on),.string_sel(string_sel),.fret_sel(fret_sel),.pluck_velocity(note_velocity),
        .sample_out(violin_sample),.fault(violin_fault),.active(violin_active));

    bass_poly8 u_bass(''')
    emit(ROOT / 'audio_core.v', audio)

    spi = (PROJECT / 'src/s3_spi_link.v').read_text()
    spi = replace(spi, "(op>=8'h02&&op<=8'h06)||op==8'h23", "(op>=8'h02&&op<=8'h06)||op==8'h08||op==8'h23")
    emit(ROOT / 's3_spi_link.v', spi)
    touch = (PROJECT / 'src/touch_to_command.v').read_text()
    emit(ROOT / 'touch_legacy.v', replace(touch, 'module touch_to_command #(', 'module touch_to_command_legacy #('))
    board = (PROJECT / 'output_r12b/guitar_excitation_ddr_top.v').read_text()
    emit(ROOT / 'board_top.v', replace(board, 'module guitar_ddr_output_r12b_top(', 'module guitar_ddr_violin_r15_top('))
    project = (PROJECT / 'guitar_ddr_bram_r13.gprj').read_text()
    for original, candidate in [('src/guitar_uart_trigger.v','violin_r15/guitar_uart_trigger.v'),('timing_r10c/audio_core.v','violin_r15/audio_core.v'),('src/s3_spi_link.v','violin_r15/s3_spi_link.v'),('src/touch_to_command.v','violin_r15/touch_to_command.v'),('output_r12b/guitar_excitation_ddr_top.v','violin_r15/board_top.v')]:
        project = replace(project, original, candidate)
    extra = ''.join(f'        <File path="violin_r15/{name}.v" type="file.verilog" enable="1" />\n' for name in ['violin_core','violin_channel','violin_touch_control','touch_legacy'])
    project = replace(project, '    </FileList>', extra+'    </FileList>')
    emit(PROJECT / 'guitar_ddr_violin_r15.gprj', project)
    for phase in ['build','pnr']:
        source=(PROJECT / f'{phase}_ddr_bram_r13.tcl').read_text()
        source=source.replace('guitar_ddr_bram_r13.gprj','guitar_ddr_violin_r15.gprj').replace('guitar_audio_s3_link_r13_bram','guitar_audio_violin_r15').replace('guitar_ddr_output_r12b_top','guitar_ddr_violin_r15_top')
        emit(PROJECT / f'{phase}_ddr_violin_r15.tcl',source)
    print('*** End Patch')


if __name__ == '__main__':
    main()
