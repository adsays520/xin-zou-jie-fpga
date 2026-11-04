// Tang Mega 138K Pro board top.
// Six standard-tuned guitar strings, frets 0..20, selected from keys.
module guitar_audio_top_original #(
    // Keep this at 1 for the first board check. Set to 0 only after the C4
    // reference tone is clean; then the physical-string output is selected.
    parameter USE_REFERENCE_TONE = 1'b0,
    // Centralized compile-time audio-path switches.  All are disabled for the
    // raw diagnostic path: string core -> 32-voice bus -> I2S.  No lower-level
    // module default can silently override these selections.
    parameter ENABLE_PICK_SOFTENER = 1'b0,
    parameter ENABLE_VOICE_FIR = 1'b0,
    // Per-voice Attack/Decay/Sustain/Release envelope, started by Note-On.
    parameter ENABLE_VOICE_ADSR = 1'b1,
    // Keep the physical string feedback untouched; the dynamic time-domain
    // equalizer below shapes only the audible tail of each independent voice.
    parameter ENABLE_TAIL_HF_DAMPING = 1'b0,
    parameter ENABLE_DYNAMIC_TAIL_EQ = 1'b1,
    parameter ENABLE_BODY_FILTER = 1'b1,
    parameter ENABLE_OUTPUT_CONDITIONER = 1'b1
)(
    input wire clk,
    input wire rst,
    input wire key_next_n,
    input wire key_pluck_n,
    input wire uart_rx_i,
    output wire lcd_sck,
    output wire lcd_sda,
    output wire lcd_cs_n,
    output wire lcd_dc,
    output wire lcd_rst_n,
    output wire lcd_led,
    output wire HP_BCK,
    output wire HP_WS,
    output wire HP_DIN,
    output wire PA_EN
);
    wire rst_n = !rst;
    wire sample_tick;
    wire [15:0] audio_word_l,audio_word_r;
    wire signed [23:0] body_sample_q23;
    wire signed [23:0] conditioned_sample_q23;
    wire signed [23:0] selected_sample_l,selected_sample_r;
    wire signed [15:0] rounded_audio_word_l,rounded_audio_word_r;
    wire signed [23:0] reference_sample;
    wire body_sample_valid;
    wire conditioned_sample_valid;
    wire active;
    wire next_pressed;
    wire pluck_pressed;
    reg [1:0] screen_selected_bus;
    reg [1:0] screen_page;
    reg key_next_meta,key_next_sync,next_hold_active,next_long_done;
    reg [24:0] next_hold_clocks;
    reg local_level_step;
    reg key_pluck_meta,key_pluck_sync,hold_active,long_plucked;
    reg [24:0] pluck_hold_clocks;
    wire long_pluck_pulse = hold_active && !long_plucked &&
        pluck_hold_clocks == 25'd29999999;
    wire uart_pluck_trigger;
    wire uart_mode_set;
    wire uart_mode_poly4;
    wire uart_timbre_set;
    wire uart_timbre_piano;
    wire uart_piano_note_on,uart_piano_note_off;
    wire [6:0] uart_piano_key,uart_piano_velocity;
    wire [2:0] uart_piano_pedal_level;
    wire [6:0] guitar_bus_level, piano_bus_level, drum_bus_level;
    wire uart_custom_envelope_mode;
    wire [7:0] uart_byte_data;
    wire uart_byte_valid;
    wire drum_valid,drum_active,drum_playing,drum_ready,drum_deadline_miss,drum_clipped;
    wire [5:0] drum_step;
    wire signed [23:0] drum_sample_l,drum_sample_r;
    reg signed [23:0] drum_hold_l,drum_hold_r;
    wire drawn_mode,drawn_mode_event,drawn_active,drawn_valid,drawn_deadline_miss;
    wire [23:0] drawn_envelope_step;
    wire drawn_ram_we,drawn_wave_loaded,drawn_envelope_loaded,drawn_upload_error;
    wire [13:0] drawn_ram_addr;
    wire [15:0] drawn_ram_data;
    wire signed [23:0] drawn_sample;
    wire [31:0] piano_requested_phase_step;
    reg signed [23:0] drawn_hold;
    wire envelope_ram_we;
    wire [11:0] envelope_ram_addr;
    wire [15:0] envelope_ram_data;
    wire envelope_loaded;
    wire envelope_upload_error;
    wire [2:0] uart_trigger_string_sel;
    wire [4:0] uart_trigger_fret_sel;
    wire [6:0] uart_trigger_velocity;
    wire [9:0] requested_delay_len;
    wire [15:0] requested_loop_gain_q15;
    wire [9:0] requested_pick_offset;
    wire [15:0] requested_scrape_q15;
    wire [23:0] requested_damping_q23;
    wire [23:0] requested_allpass_q23;
    wire [31:0] requested_init_phase_step;
    wire [15:0] requested_noise_mix_q15;
    wire [1:0] requested_excitation_smooth;
    reg [9:0] poly_delay_q,poly_pick_q;
    reg [15:0] poly_loop_q,poly_scrape_q,poly_noise_q;
    reg [23:0] poly_damping_q,poly_allpass_q;
    reg [31:0] poly_phase_q;
    reg [1:0] poly_smooth_q;
    reg [2:0] poly_string_q;
    reg [6:0] poly_velocity_q;
    reg poly_custom_q,poly_note_on_q;
    wire poly_mix_valid;
    wire signed [23:0] poly_mix_sample;
    wire poly_mix_clipped;
    wire voice_bank_active;
    wire envelope_write_allowed = !voice_bank_active;
    wire [5:0] poly_active_count;
    wire [31:0] poly_occupied, poly_dropped, poly_stolen;
    wire poly_deadline_miss;
    wire piano_mix_valid,piano_active,piano_deadline_miss;
    wire signed [23:0] piano_mix_sample;
    wire piano_board_valid;
    wire signed [23:0] piano_board_sample_l,piano_board_sample_r;
    reg signed [23:0] guitar_hold,piano_hold_l,piano_hold_r;
    wire [4:0] fx_amp;
    wire [6:0] fx_drive,fx_tone,fx_level,fx_mix,fx_rate,fx_depth,fx_threshold;
    wire [2:0] fx_modulation,fx_flags;
    wire fx_changed,fx_valid,fx_bypass,fx_deadline_miss,fx_electric_source;
    wire signed [23:0] fx_sample;
    reg signed [23:0] fx_hold;
    wire [6:0] space_chorus_mix,space_chorus_rate,space_chorus_depth;
    wire [6:0] space_delay_mix,space_delay_time,space_delay_feedback;
    wire space_changed,space_valid,space_bypass,space_deadline_miss;
    wire signed [23:0] space_sample_l,space_sample_r;
    reg signed [23:0] space_hold_l,space_hold_r;
    reg signed [23:0] guitar_electric_hold;
    wire signed [23:0] guitar_selected=fx_bypass?guitar_hold:fx_hold;
    reg [15:0] frame_audio_word_l,frame_audio_word_r;
    reg signed [23:0] output_sample_l,output_sample_r;
    reg output_word_pending;
    // 0..5 correspond to strings 1..6: E4, B3, G3, D3, A2, E2.
    reg [2:0] string_sel;
    reg [4:0] fret_sel;
    reg [6:0] note_velocity;
    reg note_on;
    reg pluck_pending;
    reg poly_mode;
    reg timbre_piano;
    reg clear_voice_bank;
    reg [31:0] reference_phase;
    wire voice_path_rst_n = rst_n && !clear_voice_bank;

    // G15 tap selects a bus; hold G15 for 0.6 s to change screen page.
    // F15 tap raises the selected bus by 8 (wraps after 127);
    // hold F15 for 0.6 s to pluck the currently selected guitar note.
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            screen_selected_bus<=0;screen_page<=0;local_level_step<=0;
            key_next_meta<=1;key_next_sync<=1;
            next_hold_active<=0;next_long_done<=0;next_hold_clocks<=0;
            key_pluck_meta<=1;key_pluck_sync<=1;
            hold_active<=0;long_plucked<=0;pluck_hold_clocks<=0;
        end else begin
            key_pluck_meta<=key_pluck_n;
            key_pluck_sync<=key_pluck_meta;
            key_next_meta<=key_next_n;
            key_next_sync<=key_next_meta;
            local_level_step<=0;
            if (next_pressed) begin
                next_hold_active<=1;next_long_done<=0;next_hold_clocks<=0;
            end else if (next_hold_active) begin
                if (!key_next_sync) begin
                    if (!next_long_done) next_hold_clocks<=next_hold_clocks+1'b1;
                    if (!next_long_done && next_hold_clocks==25'd29999999) begin
                        screen_page<=screen_page==2 ? 0 : screen_page+1'b1;
                        next_long_done<=1;
                    end
                end else begin
                    if (!next_long_done) screen_selected_bus<=screen_selected_bus==2 ? 0 : screen_selected_bus+1'b1;
                    next_hold_active<=0;
                end
            end
            if (pluck_pressed) begin
                hold_active<=1;long_plucked<=0;pluck_hold_clocks<=0;
            end else if (hold_active) begin
                if (!key_pluck_sync) begin
                    if (!long_plucked) pluck_hold_clocks<=pluck_hold_clocks+1'b1;
                    if (long_pluck_pulse) long_plucked<=1;
                end else begin
                    if (!long_plucked) local_level_step<=1;
                    hold_active<=0;
                end
            end
        end
    end

    // The serial/UI address remains string+fret for compatibility, but the
    // piano engine receives an absolute piano key number.  Equivalent pitches
    // on different guitar strings therefore use exactly the same piano model.
    function [6:0] piano_base_key;
        input [2:0] selected_string;
        begin
            case (selected_string)
                3'd0: piano_base_key=7'd64; // E4
                3'd1: piano_base_key=7'd59; // B3
                3'd2: piano_base_key=7'd55; // G3
                3'd3: piano_base_key=7'd50; // D3
                3'd4: piano_base_key=7'd45; // A2
                default: piano_base_key=7'd40; // E2
            endcase
        end
    endfunction
    wire [6:0] requested_piano_key = piano_base_key(string_sel)+fret_sel;
    wire piano_core_note_on=(note_on&&timbre_piano)||uart_piano_note_on;
    wire [6:0] piano_core_key=(uart_piano_note_on||uart_piano_note_off)
        ?uart_piano_key:requested_piano_key;
    wire [6:0] piano_core_velocity=uart_piano_note_on
        ?uart_piano_velocity:note_velocity;
    reg piano_note_on_q,piano_note_off_q,piano_drawn_on_q;
    reg [6:0] piano_key_q,piano_velocity_q;
    // A one-clock event stage removes the string/fret arithmetic from the
    // wavetable key ROM -> phase-step write path. On/off and key travel together.
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            piano_note_on_q<=0;piano_note_off_q<=0;piano_drawn_on_q<=0;
            piano_key_q<=0;piano_velocity_q<=0;
        end else begin
            piano_note_on_q<=piano_core_note_on&&!drawn_mode;
            piano_drawn_on_q<=piano_core_note_on&&drawn_mode;
            piano_note_off_q<=uart_piano_note_off;
            piano_key_q<=piano_core_key;
            piano_velocity_q<=piano_core_velocity;
        end
    end

    function signed [23:0] sat_mix24;
        input signed [24:0] value;
        begin
            if(value>25'sd8388607) sat_mix24=24'sh7fffff;
            else if(value<-25'sd8388608) sat_mix24=24'sh800000;
            else sat_mix24=value[23:0];
        end
    endfunction
    // A timbre selection is exclusive: a lingering guitar voice must not
    // add subharmonics to a new low piano note (or vice versa).
    wire signed [23:0] instrument_source_l = timbre_piano
        ? (drawn_mode ? drawn_hold : piano_hold_l) : guitar_selected;
    wire signed [23:0] instrument_source_r = timbre_piano
        ? (drawn_mode ? drawn_hold : piano_hold_r) : guitar_selected;
    wire signed [23:0] instrument_mix_l,instrument_mix_r;
    performance_mixer u_performance_mixer (
        .clk(clk),.rst_n(rst_n),.sample_tick(sample_tick),
        .instrument_l(instrument_source_l),.instrument_r(instrument_source_r),
        .drum_l(drum_hold_l),.drum_r(drum_hold_r),
        .instrument_target(timbre_piano ? piano_bus_level : guitar_bus_level),
        .drum_target(drum_bus_level),.mix_l(instrument_mix_l),.mix_r(instrument_mix_r));
    st7735_status u_status_screen (
        .clk(clk),.rst_n(rst_n),
        .guitar_level(guitar_bus_level),.piano_level(piano_bus_level),
        .drum_level(drum_bus_level),.selected_bus(screen_selected_bus),
        .page(screen_page),.fx_drive(fx_drive),.fx_tone(fx_tone),
        .fx_mix(fx_mix),.fx_amp(fx_amp),.fx_modulation(fx_modulation),
        .chorus_mix(space_chorus_mix),.delay_mix(space_delay_mix),
        .chorus_depth(space_chorus_depth),
        .drum_playing(drum_playing),.lcd_sck(lcd_sck),.lcd_sda(lcd_sda),
        .lcd_cs_n(lcd_cs_n),.lcd_dc(lcd_dc),.lcd_rst_n(lcd_rst_n),
        .lcd_led(lcd_led));

    // 261.625565 Hz at 48 kHz, represented as a 32-bit phase increment.
    localparam [31:0] C4_PHASE_STEP = 32'd23409859;

    // A low-amplitude, continuous C4 triangle reference. It is intentionally
    // simple and deterministic: if this is not a clear musical C4 on board,
    // the remaining fault is outside the FM string algorithm.
    function signed [23:0] reference_c4;
        input [31:0] phase_in;
        reg signed [23:0] magnitude;
        begin
            case (phase_in[31:30])
                2'd0: magnitude = {3'b000, phase_in[29:9]};
                2'd1: magnitude = {3'b000, 21'd2097151 - phase_in[29:9]};
                2'd2: magnitude = -$signed({3'b000, phase_in[29:9]});
                default: magnitude = -$signed({3'b000, 21'd2097151 - phase_in[29:9]});
            endcase
            reference_c4 = magnitude;
        end
    endfunction

    assign PA_EN = 1'b1;
    assign reference_sample = reference_c4(reference_phase);
    // The optional stages below are compile-time pass-throughs when disabled,
    // so this final selection has one unambiguous non-reference source.
    assign selected_sample_l = USE_REFERENCE_TONE
        ? reference_sample : (space_bypass ? instrument_mix_l : space_hold_l);
    assign selected_sample_r = USE_REFERENCE_TONE
        ? reference_sample : (space_bypass ? instrument_mix_r : space_hold_r);
    assign audio_word_l = frame_audio_word_l;
    assign audio_word_r = frame_audio_word_r;
    audio_q23_to_s16 u_output_quantizer_l (
        .sample_q23(output_sample_l),.sample_s16(rounded_audio_word_l)
    );
    audio_q23_to_s16 u_output_quantizer_r (
        .sample_q23(output_sample_r),.sample_s16(rounded_audio_word_r)
    );
    // Split the final instrument mix and output rounding across two 50 MHz
    // cycles. The serializer does not load the next L/R words until later BCK
    // edges, so this still supplies the same audio frame without a deep path.
    always @(posedge clk or negedge rst_n)
        if (!rst_n) begin
            output_sample_l<=0;output_sample_r<=0;output_word_pending<=0;
            frame_audio_word_l<=0;frame_audio_word_r<=0;
        end else begin
            output_word_pending<=sample_tick;
            if(sample_tick)begin
                output_sample_l<=selected_sample_l;
                output_sample_r<=selected_sample_r;
            end
            if(output_word_pending)begin
                frame_audio_word_l<=rounded_audio_word_l;
                frame_audio_word_r<=rounded_audio_word_r;
            end
        end
    always @(posedge clk or negedge rst_n)
        if(!rst_n)begin space_hold_l<=0;space_hold_r<=0;end
        else if(space_valid)begin space_hold_l<=space_sample_l;space_hold_r<=space_sample_r;end
    assign active = voice_bank_active || piano_active || drawn_active || drum_active;
    // Drum state is independent of guitar timbre/mode changes and Riff flushes.
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin drum_hold_l<=0;drum_hold_r<=0;end
        else if(drum_valid)begin drum_hold_l<=drum_sample_l;drum_hold_r<=drum_sample_r;end
    end
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n||clear_voice_bank) begin
            guitar_hold<=0;piano_hold_l<=0;piano_hold_r<=0;drawn_hold<=0;fx_hold<=0;guitar_electric_hold<=0;
        end
        else begin
            if(conditioned_sample_valid) guitar_hold<=conditioned_sample_q23;
            if(poly_mix_valid)guitar_electric_hold<=poly_mix_sample;
            if(fx_valid)fx_hold<=fx_sample;
            if(drawn_valid)drawn_hold<=drawn_sample;
            if(piano_board_valid) begin
                piano_hold_l<=piano_board_sample_l;
                piano_hold_r<=piano_board_sample_r;
            end
        end
    end



    button_debounce u_next_button (
        .clk(clk), .rst_n(rst_n), .key_n(key_next_n), .pressed(next_pressed)
    );

    button_debounce u_pluck_button (
        .clk(clk), .rst_n(rst_n), .key_n(key_pluck_n), .pressed(pluck_pressed)
    );

    // The board's BL616 USB/JTAG bridge supplies a low-speed 115200-baud UART.
    // This adapter can only provide a string/fret selection and one-cycle
    // pluck request; it has no access to the audio sample path or model data.
    guitar_uart_trigger u_uart_trigger (
        .clk(clk),
        .rst_n(rst_n),
        .uart_rx_i(uart_rx_i),
        .local_level_step(local_level_step),.local_level_bus(screen_selected_bus),
        .trigger_string_sel(uart_trigger_string_sel),
        .trigger_fret_sel(uart_trigger_fret_sel),
        .trigger_velocity(uart_trigger_velocity),
        .trigger(uart_pluck_trigger),
        .mode_set(uart_mode_set),
        .mode_poly4(uart_mode_poly4),
        .timbre_set(uart_timbre_set),
        .timbre_piano(uart_timbre_piano),
        .piano_note_on(uart_piano_note_on),
        .piano_note_off(uart_piano_note_off),
        .piano_key(uart_piano_key),
        .piano_velocity(uart_piano_velocity),
        .piano_pedal_level(uart_piano_pedal_level),
        .guitar_bus_level(guitar_bus_level),
        .piano_bus_level(piano_bus_level),
        .drum_bus_level(drum_bus_level),
        .envelope_write_allowed(envelope_write_allowed),
        .custom_envelope_mode(uart_custom_envelope_mode),
        .envelope_ram_we(envelope_ram_we),
        .envelope_ram_addr(envelope_ram_addr),
        .envelope_ram_data(envelope_ram_data),
        .envelope_loaded(envelope_loaded),
        .envelope_upload_error(envelope_upload_error),
        .envelope_command(),
        .uart_byte_data(uart_byte_data),.uart_byte_valid(uart_byte_valid)
    );

    drawn_synth_control u_drawn_control(
        .clk(clk),.rst_n(rst_n),.byte_data(uart_byte_data),.byte_valid(uart_byte_valid),
        .write_allowed(!drawn_active),.mode(drawn_mode),.mode_event(drawn_mode_event),
        .envelope_step(drawn_envelope_step),.ram_we(drawn_ram_we),
        .ram_addr(drawn_ram_addr),.ram_data(drawn_ram_data),
        .wave_loaded(drawn_wave_loaded),.envelope_loaded(drawn_envelope_loaded),
        .upload_error(drawn_upload_error));

    drum_machine u_drums(
        .clk(clk),.rst_n(rst_n),.sample_tick(sample_tick),
        .byte_data(uart_byte_data),.byte_valid(uart_byte_valid),
        .sample_valid(drum_valid),.sample_l(drum_sample_l),.sample_r(drum_sample_r),
        .playing(drum_playing),.pattern_ready(drum_ready),.current_step(drum_step),
        .active(drum_active),.deadline_miss(drum_deadline_miss),.clipped(drum_clipped));

    guitar_fx_control u_fx_control(
        .clk(clk),.rst_n(rst_n),.byte_data(uart_byte_data),.byte_valid(uart_byte_valid),
        .amp(fx_amp),.drive(fx_drive),.tone(fx_tone),.level(fx_level),.mix(fx_mix),
        .rate(fx_rate),.depth(fx_depth),.threshold(fx_threshold),
        .modulation(fx_modulation),.flags(fx_flags),.changed(fx_changed));
    guitar_fx u_fx(
        .clk(clk),.rst_n(rst_n),.sample_tick(sample_tick),.history_clear(clear_voice_bank),
        .sample_in(timbre_piano?24'sd0:(fx_electric_source?guitar_electric_hold:guitar_hold)),
        .amp(fx_amp),.drive(fx_drive),.tone(fx_tone),.level(fx_level),.mix(fx_mix),
        .rate(fx_rate),.depth(fx_depth),.threshold(fx_threshold),
        .modulation(fx_modulation),.flags(fx_flags),.changed(fx_changed),
        .output_valid(fx_valid),.sample_out(fx_sample),.bypass(fx_bypass),
        .electric_source(fx_electric_source),.deadline_miss(fx_deadline_miss));

    master_space_fx_control u_space_control(
        .clk(clk),.rst_n(rst_n),.byte_data(uart_byte_data),.byte_valid(uart_byte_valid),
        .chorus_mix(space_chorus_mix),.chorus_rate(space_chorus_rate),
        .chorus_depth(space_chorus_depth),.delay_mix(space_delay_mix),
        .delay_time(space_delay_time),.delay_feedback(space_delay_feedback),
        .changed(space_changed));
    master_space_fx u_space_fx(
        .clk(clk),.rst_n(rst_n),.sample_tick(sample_tick),.changed(space_changed),
        .sample_l(instrument_mix_l),.sample_r(instrument_mix_r),
        .chorus_mix(space_chorus_mix),.chorus_rate(space_chorus_rate),
        .chorus_depth(space_chorus_depth),.delay_mix(space_delay_mix),
        .delay_time(space_delay_time),.delay_feedback(space_delay_feedback),
        .bypass(space_bypass),.output_valid(space_valid),
        .output_l(space_sample_l),.output_r(space_sample_r),
        .deadline_miss(space_deadline_miss));

    guitar_note_params u_note_params (
        .string_sel(string_sel),
        .fret_sel(fret_sel),
        .delay_len(requested_delay_len),
        .loop_gain_q15(requested_loop_gain_q15),
        .pick_offset(requested_pick_offset),
        .scrape_q15(requested_scrape_q15),
        .damping_q23(requested_damping_q23),
        .allpass_q23(requested_allpass_q23),
        .noise_mix_q15(requested_noise_mix_q15),
        .excitation_smooth(requested_excitation_smooth),
        .init_phase_step(requested_init_phase_step)
    );

    // Note parameters are stable for a sample frame after a pluck request.
    // Register the lookup outputs and delay the poly32 trigger one clock so
    // a UART fret change on the same sample tick is captured before the event.
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n) begin
            poly_delay_q<=0;poly_pick_q<=0;poly_loop_q<=0;
            poly_scrape_q<=0;poly_noise_q<=0;poly_damping_q<=0;
            poly_allpass_q<=0;poly_phase_q<=0;poly_smooth_q<=0;
            poly_string_q<=0;poly_velocity_q<=0;poly_custom_q<=0;
            poly_note_on_q<=0;
        end else begin
            poly_delay_q<=requested_delay_len;
            poly_pick_q<=requested_pick_offset;
            poly_loop_q<=requested_loop_gain_q15;
            poly_scrape_q<=requested_scrape_q15;
            poly_noise_q<=requested_noise_mix_q15;
            poly_damping_q<=requested_damping_q23;
            poly_allpass_q<=requested_allpass_q23;
            poly_phase_q<=requested_init_phase_step;
            poly_smooth_q<=requested_excitation_smooth;
            poly_string_q<=string_sel;
            poly_velocity_q<=note_velocity;
            poly_custom_q<=uart_custom_envelope_mode;
            poly_note_on_q<=note_on&&!timbre_piano;
        end
    end

    // Power-up stays silent. G15 selects the next pair; F15/UART starts a note.
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            string_sel   <= 3'd5;
            fret_sel     <= 5'd0;
            note_velocity <= 7'd110;
            note_on <= 1'b0;
            pluck_pending <= 1'b0;
            poly_mode <= 1'b1;
            timbre_piano <= 1'b0;
            clear_voice_bank <= 1'b0;
        end else begin
            note_on <= 1'b0;
            clear_voice_bank <= 1'b0;

            // A button or UART event queues one request for the next frame.
            if (sample_tick) begin
                if (pluck_pending) begin
                    note_on <= 1'b1;
                    pluck_pending <= 1'b0;
                end
            end

            // UART and buttons are the only guitar note sources.
            if (uart_pluck_trigger) begin
                string_sel <= uart_trigger_string_sel;
                fret_sel <= uart_trigger_fret_sel;
                note_velocity <= uart_trigger_velocity;
                pluck_pending <= 1'b1;
            end

            if (long_pluck_pulse)
                pluck_pending <= 1'b1;

            // Mode changes are control-only frames. Flush voice and body
            // history once so samples from the previous mode cannot leak
            // into the first note used for comparison.
            if (uart_mode_set) begin
                poly_mode <= uart_mode_poly4;
                clear_voice_bank <= 1'b1;
                pluck_pending <= 1'b0;
            end
            // Clear old notes on a timbre switch so the previous instrument
            // cannot reappear when the user switches back later.
            if (uart_timbre_set) begin
                timbre_piano <= uart_timbre_piano;
                clear_voice_bank <= 1'b1;
                pluck_pending <= 1'b0;
            end
            if(drawn_mode_event&&timbre_piano)begin
                clear_voice_bank<=1'b1;pluck_pending<=1'b0;
            end
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            reference_phase <= 32'd0;
        else if (sample_tick)
            reference_phase <= reference_phase + C4_PHASE_STEP;
    end

    audio_drive u_audio_drive (
        .clk(clk), .rst_n(rst_n), .idata_left(audio_word_l),
        .idata_right(audio_word_r), .req(),
        .sample_tick(sample_tick), .HP_BCK(HP_BCK),
        .HP_WS(HP_WS), .HP_DIN(HP_DIN)
    );

    guitar_poly32_tdm #(
        .ENABLE_PICK_SOFTENER(ENABLE_PICK_SOFTENER),
        .ENABLE_VOICE_FIR(ENABLE_VOICE_FIR),
        .ENABLE_VOICE_ADSR(ENABLE_VOICE_ADSR),
        .ENABLE_PIANO_TIMBRE(1'b0),
        .ENABLE_TAIL_HF_DAMPING(ENABLE_TAIL_HF_DAMPING),
        .ENABLE_DYNAMIC_TAIL_EQ(ENABLE_DYNAMIC_TAIL_EQ)
    ) u_poly32 (
        .clk(clk), .rst_n(voice_path_rst_n),
        .poly_mode(poly_mode), .sample_tick(sample_tick),
        .note_on(poly_note_on_q), .requested_delay_len(poly_delay_q),
        .requested_loop_gain_q15(poly_loop_q),
        .requested_pick_offset(poly_pick_q),
        .requested_scrape_q15(poly_scrape_q),
        .requested_damping_q23(poly_damping_q),
        .requested_allpass_q23(poly_allpass_q),
        .requested_init_phase_step(poly_phase_q),
        .requested_noise_mix_q15(poly_noise_q),
        .requested_excitation_smooth(poly_smooth_q),
        .requested_string_sel(poly_string_q), .velocity(poly_velocity_q),
        .requested_custom_envelope(poly_custom_q),
        .envelope_ram_we(envelope_ram_we),
        .envelope_ram_addr(envelope_ram_addr),
        .envelope_ram_data(envelope_ram_data),
        .sample_valid(poly_mix_valid), .sample_out(poly_mix_sample),
        .active(voice_bank_active), .active_count(poly_active_count),
        .occupied(poly_occupied), .dropped_events(poly_dropped),
        .stolen_events(poly_stolen), .deadline_miss(poly_deadline_miss),
        .limited(poly_mix_clipped)
    );

    piano_wavetable16_tdm u_piano_wavetable(
        .clk(clk),.rst_n(voice_path_rst_n),.sample_tick(sample_tick),
        .note_on(piano_note_on_q),.note_off(piano_note_off_q),
        .poly_mode(poly_mode),.requested_key(piano_key_q),
        .velocity(piano_velocity_q),.pedal_level(uart_piano_pedal_level),
        .sample_valid(piano_mix_valid),.sample_out(piano_mix_sample),
        .active(piano_active),.deadline_miss(piano_deadline_miss),
        .requested_phase_step(piano_requested_phase_step)
    );
    drawn_synth16 u_drawn_synth(
        .clk(clk),.rst_n(rst_n),
        .voice_rst_n(voice_path_rst_n&&timbre_piano&&drawn_mode),.sample_tick(sample_tick),
        .note_on(piano_drawn_on_q),.note_off(piano_note_off_q),.poly_mode(poly_mode),
        .requested_key(piano_key_q),.velocity(piano_velocity_q),
        .requested_phase_step(piano_requested_phase_step),.envelope_step(drawn_envelope_step),
        .pedal_level(uart_piano_pedal_level),.ram_we(drawn_ram_we),
        .ram_addr(drawn_ram_addr),.ram_data(drawn_ram_data),
        .sample_valid(drawn_valid),.sample_out(drawn_sample),.active(drawn_active),
        .deadline_miss(drawn_deadline_miss));
    piano_soundboard u_piano_soundboard(
        .clk(clk),.rst_n(voice_path_rst_n),.sample_valid(piano_mix_valid),
        .sample_in(piano_mix_sample),.pedal_level(uart_piano_pedal_level),
        .output_valid(piano_board_valid),
        .sample_out_l(piano_board_sample_l),.sample_out_r(piano_board_sample_r)
    );

    generate
        if (ENABLE_BODY_FILTER) begin : g_body_filter
            // Five shared acoustic-body modes for all six strings.
            guitar_body_filter u_body_filter (
                .clk(clk), .rst_n(voice_path_rst_n),
                .sample_valid(poly_mix_valid), .sample_in(poly_mix_sample),
                .output_valid(body_sample_valid),
                .sample_out(body_sample_q23)
            );
        end else begin : g_bypass_body_filter
            assign body_sample_valid = poly_mix_valid;
            assign body_sample_q23 = poly_mix_sample;
        end

        if (ENABLE_OUTPUT_CONDITIONER) begin : g_output_conditioner
            guitar_output_conditioner u_output_conditioner (
                .clk(clk), .rst_n(voice_path_rst_n),
                .sample_valid(body_sample_valid), .sample_in(body_sample_q23),
                .output_valid(conditioned_sample_valid),
                .sample_out(conditioned_sample_q23)
            );
        end else begin : g_bypass_output_conditioner
            assign conditioned_sample_valid = body_sample_valid;
            assign conditioned_sample_q23 = body_sample_q23;
        end
    endgenerate
endmodule
