// Tang Mega 138K Pro board top.
// Six standard-tuned guitar strings, frets 0..20, selected from keys.
module guitar_audio_top #(
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
    parameter ENABLE_OUTPUT_CONDITIONER = 1'b1,
    parameter integer SD_POWERUP_CLKS=5000000
)(
    input wire clk,
    input wire sw1_enc_a,sw1_enc_b,sw2_enc_a,sw2_enc_b,
    input wire sw1_up_n,sw1_right_n,sw1_down_n,sw1_left_n,
    input wire rst,
    input wire key_next_n,
    input wire key_pluck_n,
    input wire uart_rx_i,
    input wire spi_sclk,spi_cs_n,spi_mosi,
    input wire sd_miso,output wire sd_clk,sd_mosi,sd_cs,
    output wire spi_miso,fpga_irq,fpga_ready,
    output wire uart_tx_o,
    output wire [5:0] led_n,
    output wire lcd_sck,
    output wire lcd_sda,
    output wire lcd_cs_n,
    output wire lcd_dc,
    output wire lcd_rst_n,
    output wire lcd_led,
    output wire HP_BCK,
    output wire HP_WS,
    output wire HP_DIN,
    input wire piano_memory_ready,piano_transport_fault,
    output wire piano_bank_ready,piano_memory_fault,
    output wire piano_req_valid,input wire piano_req_ready,output wire [63:0] piano_req_data,
    input wire piano_rsp_valid,output wire piano_rsp_ready,input wire [63:0] piano_rsp_data,
    output wire space_req_valid,input wire space_req_ready,output wire [63:0] space_req_data,
    input wire space_rsp_valid,output wire space_rsp_ready,input wire [63:0] space_rsp_data,
    output wire space_memory_fault
);
    reg timbre_bass,timbre_violin;
    wire ensemble_mode,ensemble_changed,ensemble_valid,ensemble_query;
    wire [1:0] ensemble_target;
    wire [7:0] ensemble_a,ensemble_b,ensemble_c,ensemble_sequence;
    wire [6:0] bass_bus_level;
    wire ensemble_tx,ensemble_tx_busy,ensemble_tx_hold,ensemble_mix_deadline;
    wire ensemble_guitar=ensemble_mode&&ensemble_valid&&ensemble_target==0;
    wire ensemble_bass=ensemble_mode&&ensemble_valid&&ensemble_target==1;
    wire ensemble_piano=ensemble_mode&&ensemble_valid&&ensemble_target==2;
    wire ensemble_violin=ensemble_mode&&ensemble_valid&&ensemble_target==3;
    wire [2:0] ensemble_string=ensemble_a[2:0]-3'd1;
    wire uart_timbre_violin,uart_violin_on,uart_violin_off,uart_violin_legato;
    wire [6:0] uart_violin_key,uart_violin_velocity,violin_bus_level;
    wire signed [23:0] violin_sample;
    wire violin_fault,violin_active,trigger_hall_mode,trigger_mode_changed;
    wire pluck_ingress_ready,pluck_event_valid,pluck_queue_overflow;
    wire [14:0] pluck_event_data;
    reg [2:0] pluck_selected_string;
    reg [4:0] pluck_selected_fret;
    reg [6:0] pluck_selected_velocity;
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
    wire bank_upload_begin,bank_upload_valid,bank_upload_commit,bank_upload_error,bank_query,bank_upload_ready;
    wire bank_upload_cancel,bank_upload_session,sd_active,sd_finished,sd_loading;
    wire sd_upload_begin,sd_upload_valid,sd_upload_commit,sd_upload_error;
    wire [10:0] sd_upload_index;wire [2047:0] sd_upload_data;
    wire sd_stage_valid;wire [7:0] sd_stage_index,sd_stage_data;
    wire [7:0] sd_boot_error,sd_card_error,sd_byte;
    wire sd_card_ready,sd_byte_valid,sd_sector_done,sd_read_start;
    wire [31:0] sd_read_lba;
    reg sd_drum_file,sd_next_file,sd_piano_finished;
    reg [7:0] sd_piano_error;
    wire drum_parameter_ready,drum_parameter_initialized,drum_parameter_fault,drum_parameter_active_bank;
    wire [10:0] drum_parameter_count;
    wire effective_upload_begin=(sd_upload_begin&&!sd_drum_file)||(bank_upload_begin&&!sd_active);
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin sd_drum_file<=0;sd_next_file<=0;sd_piano_finished<=0;sd_piano_error<=0;end
        else begin
            sd_next_file<=0;
            if(sd_finished&&!sd_drum_file)begin
                sd_drum_file<=1;sd_next_file<=1;sd_piano_finished<=1;sd_piano_error<=sd_boot_error;
            end
        end
    end
    wire [10:0] bank_upload_index,bank_upload_count;wire [2047:0] bank_upload_data;
    wire [7:0] bank_query_sequence,bank_status_error;wire [2:0] bank_status;
    wire bank_status_tx,bank_status_busy,bank_status_hold,verification_tx;
    assign uart_tx_o=ensemble_tx_busy?ensemble_tx:bank_status_busy?bank_status_tx:verification_tx;
    wire uart_timbre_bass;
    wire uart_piano_note_on,uart_piano_note_off;
    wire [6:0] uart_piano_key,uart_piano_velocity;
    wire [2:0] uart_piano_pedal_level;
    wire [6:0] guitar_bus_level, piano_bus_level, drum_bus_level;
    wire uart_custom_envelope_mode;
    wire [7:0] uart_byte_data;
    wire uart_byte_valid;
    wire verification_running,verification_visual_enable,verification_capture_request;
    wire verification_fast_key_enable,verification_fast_pluck;
    (* syn_keep=1 *) wire verification_start_event;
    wire [63:0] verification_frequencies;
    wire [27:0] verification_gains,verification_pans;
    wire signed [23:0] verification_sample_l,verification_sample_r;
    wire verification_valid,verification_latency_valid,verification_deadline_miss;
    wire [31:0] verification_latency_cycles;
    wire [2:0] verification_active_count;
    wire verification_tx_busy;
    reg signed [23:0] verification_hold_l,verification_hold_r;
    wire [7:0] visual_pixel_x,visual_pixel_y;
    wire [15:0] visual_pixel_rgb;
    wire [1:0] visual_display_page;
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
    reg [2:0] lookup_string_q;
    reg [4:0] lookup_fret_q;
    reg [6:0] lookup_velocity_q;
    reg lookup_custom_q,lookup_note_q;
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
    wire bass_valid,bass_active,bass_deadline_miss;
    wire signed [23:0] bass_sample;
    reg signed [23:0] bass_hold;
    wire [23:0] pitch_ratio_q20,pitch_ratio_smoothed;
    wire pitch_enabled;
    wire signed [23:0] guitar_selected=fx_bypass?(!ensemble_mode&&timbre_bass?bass_hold:guitar_hold):fx_hold;
    reg [15:0] frame_audio_word_l,frame_audio_word_r;
    reg signed [23:0] output_sample_l,output_sample_r;
    reg output_word_pending;
    // 0..5 correspond to strings 1..6: E4, B3, G3, D3, A2, E2.
    reg [2:0] string_sel;
    reg [4:0] fret_sel;
    reg [6:0] note_velocity;
    reg note_on;

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
                        screen_selected_bus<=screen_selected_bus==2 ? 0 : screen_selected_bus+1'b1;
                        next_long_done<=1;
                    end
                end else begin
                    if (!next_long_done) screen_page<=screen_page==2 ? 0 : screen_page+1'b1;
                    next_hold_active<=0;
                end
            end
            if(verification_fast_key_enable)begin
                hold_active<=0;long_plucked<=0;pluck_hold_clocks<=0;
            end else if (pluck_pressed) begin
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
    wire piano_core_note_on=ensemble_mode?(piano_bank_ready&&ensemble_piano&&ensemble_c[0]):
        timbre_piano&&(drawn_mode||piano_bank_ready)&&(note_on||uart_piano_note_on);
    wire [6:0] piano_core_key=ensemble_mode?ensemble_a[6:0]:(uart_piano_note_on||uart_piano_note_off)
        ?uart_piano_key:requested_piano_key;
    wire [6:0] piano_core_velocity=ensemble_mode?ensemble_b[6:0]:uart_piano_note_on
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
            piano_note_on_q<=piano_core_note_on&&(ensemble_mode||!drawn_mode);
            piano_drawn_on_q<=piano_core_note_on&&drawn_mode&&!ensemble_mode;
            piano_note_off_q<=ensemble_mode?(ensemble_piano&&!ensemble_c[0]):uart_piano_note_off&&timbre_piano;
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
    wire signed [23:0] instrument_source_l = timbre_violin ? violin_sample : timbre_piano
        ? (drawn_mode ? drawn_hold : piano_hold_l) : guitar_selected;
    wire signed [23:0] instrument_source_r = timbre_violin ? violin_sample : timbre_piano
        ? (drawn_mode ? drawn_hold : piano_hold_r) : guitar_selected;
    wire signed [23:0] instrument_mix_l,instrument_mix_r;
    ensemble_mixer u_performance_mixer (
        .clk(clk),.rst_n(rst_n),.sample_tick(sample_tick),
        .clear(clear_voice_bank),.ensemble_mode(ensemble_mode),
        .legacy_l(instrument_source_l),.legacy_r(instrument_source_r),
        .guitar_sample(guitar_selected),.bass_sample(bass_hold),.piano_l(piano_hold_l),.piano_r(piano_hold_r),.violin_sample(violin_sample),
        .guitar_target(guitar_bus_level),.bass_target(bass_bus_level),.piano_target(piano_bus_level),.violin_target(violin_bus_level),
        .drum_l(drum_hold_l),.drum_r(drum_hold_r),
        .legacy_target(timbre_violin ? violin_bus_level : timbre_piano ? piano_bus_level : timbre_bass ? bass_bus_level : guitar_bus_level),
        .drum_target(drum_bus_level),.mix_l(instrument_mix_l),.mix_r(instrument_mix_r),.deadline_miss(ensemble_mix_deadline));
    wire panel_row_next,panel_col_next,panel_up,panel_right,panel_down,panel_left,panel_slide,panel_vibrato;
    wire [3:0] panel_page,panel_row,panel_col;wire panel_editing,panel_reset_pitch;
    wire [7:0] panel_semi,panel_cents,panel_hz,panel_return;
    wire [255:0] panel_values;
    wire [47:0] panel_command_data;wire panel_command_valid,panel_command_ready;
    wire [23:0] panel_ratio,panel_inverse;wire panel_active;
    wire [1:0] panel_gesture;wire [4:0] panel_steps;wire signed [12:0] panel_cent_position;
    reg [23:0] melodic_ratio,melodic_inverse;
    always @(posedge clk or negedge rst_n)begin
     if(!rst_n)begin melodic_ratio<=1048576;melodic_inverse<=1048576;end
     else if(sample_tick)begin melodic_ratio<=panel_ratio;melodic_inverse<=panel_inverse;end
    end
    panel_inputs u_panel_inputs(.clk(clk),.rst_n(rst_n),
     .sw1_a(sw1_enc_a),.sw1_b(sw1_enc_b),.sw2_a(sw2_enc_a),.sw2_b(sw2_enc_b),
     .up_n(sw1_up_n),.right_n(sw1_right_n),.down_n(sw1_down_n),.left_n(sw1_left_n),
     .row_next(panel_row_next),.col_next(panel_col_next),.up(panel_up),.right(panel_right),.down(panel_down),.left(panel_left),
     .slide_step(panel_slide),.vibrato_step(panel_vibrato));
    panel_controller u_panel_control(.clk(clk),.rst_n(rst_n),
     .row_next(panel_row_next),.col_next(panel_col_next),.up(panel_up),.right(panel_right),.down(panel_down),.left(panel_left),
     .values(panel_values),.command_ready(panel_command_ready),.command_data(panel_command_data),.command_valid(panel_command_valid),
     .page(panel_page),.focus_row(panel_row),.focus_col(panel_col),.editing(panel_editing),
     .slide_semi(panel_semi),.vibrato_cents(panel_cents),.vibrato_hz(panel_hz),.return_10ms(panel_return),.reset_pitch(panel_reset_pitch));
    panel_pitch u_panel_pitch(.clk(clk),.rst_n(rst_n),.slide_step(panel_slide),.vibrato_step(panel_vibrato),
     .clear(panel_reset_pitch||uart_timbre_set||ensemble_changed),.slide_semi(panel_semi),.vibrato_cents(panel_cents),.vibrato_hz(panel_hz),.return_10ms(panel_return),
     .ratio_q20(panel_ratio),.inverse_q20(panel_inverse),.active(panel_active),.gesture(panel_gesture),.steps(panel_steps),.cents(panel_cent_position));
    assign panel_values[0+:8]=timbre_violin?8'd4:timbre_bass?8'd3:timbre_piano?8'd2:fx_amp!=0?8'd1:8'd0;
    assign panel_values[8+:8]=fx_amp;
    assign panel_values[16+:8]=fx_drive;
    assign panel_values[24+:8]=fx_tone;
    assign panel_values[32+:8]=fx_level;
    assign panel_values[40+:8]=fx_mix;
    assign panel_values[48+:8]=fx_modulation;
    assign panel_values[56+:8]=fx_rate;
    assign panel_values[64+:8]=fx_depth;
    assign panel_values[72+:8]=fx_flags[0];
    assign panel_values[80+:8]=fx_flags[1];
    assign panel_values[88+:8]=fx_flags[2];
    assign panel_values[96+:8]=fx_threshold;
    assign panel_values[104+:8]=space_chorus_mix;
    assign panel_values[112+:8]=space_chorus_rate;
    assign panel_values[120+:8]=space_chorus_depth;
    assign panel_values[128+:8]=space_delay_mix;
    assign panel_values[136+:8]=space_delay_time;
    assign panel_values[144+:8]=space_delay_feedback;
    assign panel_values[152+:8]=uart_piano_pedal_level;
    assign panel_values[160+:8]=guitar_bus_level;
    assign panel_values[168+:8]=piano_bus_level;
    assign panel_values[176+:8]=bass_bus_level;
    assign panel_values[184+:8]=violin_bus_level;
    assign panel_values[192+:8]=drum_bus_level;
    assign panel_values[200+:8]=panel_semi;
    assign panel_values[208+:8]=panel_cents;
    assign panel_values[216+:8]=panel_hz;
    assign panel_values[224+:8]=panel_return;
    assign panel_values[232+:8]=8'd0;
    assign panel_values[240+:8]=poly_mode;
    assign panel_values[248+:8]={7'd0,ensemble_mode};
    st7735_status #(.PANEL_UI(1)) u_status_screen (
        .panel_values(panel_values),.panel_page(panel_page),.panel_row(panel_row),.panel_col(panel_col),.panel_editing(panel_editing),
        .clk(clk),.rst_n(rst_n),
        .guitar_level(guitar_bus_level),.piano_level(timbre_violin ? violin_bus_level : piano_bus_level),
        .drum_level(drum_bus_level),.selected_bus(screen_selected_bus),
        .page(panel_page>=5?2'd3:2'd0),.visual_page_select(panel_page>=5?panel_page-5:2'd0),.visual_page(visual_display_page),
        .visual_pixel_rgb(visual_pixel_rgb),.visual_pixel_x(visual_pixel_x),.visual_pixel_y(visual_pixel_y),
        .fx_drive(fx_drive),.fx_tone(fx_tone),
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

    // Legacy PA_EN removed: Y25 belongs to the wired SW1 direction input.
    assign reference_sample = reference_c4(reference_phase);
    // The optional stages below are compile-time pass-throughs when disabled,
    // so this final selection has one unambiguous non-reference source.
    assign selected_sample_l = verification_running ? verification_hold_l : USE_REFERENCE_TONE
        ? reference_sample : (space_bypass ? instrument_mix_l : space_hold_l);
    assign selected_sample_r = verification_running ? verification_hold_r : USE_REFERENCE_TONE
        ? reference_sample : (space_bypass ? instrument_mix_r : space_hold_r);
    assign audio_word_l = frame_audio_word_l;
    assign audio_word_r = frame_audio_word_r;
    verification_control u_verification_control (
        .clk(clk),.rst_n(rst_n),.byte_valid(uart_byte_valid),.byte_data(uart_byte_data),
        .sample_tick(sample_tick),.running(verification_running),.visual_enable(verification_visual_enable),
        .capture_request(verification_capture_request),.start_event(verification_start_event),
        .fast_key_enable(verification_fast_key_enable),
        .frequencies(verification_frequencies),.gains(verification_gains),.pans(verification_pans));
    verification_dds u_verification_dds (
        .clk(clk),.rst_n(rst_n),.sample_tick(sample_tick),.running(verification_running),
        .start_event(verification_start_event),.frequencies(verification_frequencies),
        .gains(verification_gains),.pans(verification_pans),
        .sample_l(verification_sample_l),.sample_r(verification_sample_r),.sample_valid(verification_valid),
        .latency_valid(verification_latency_valid),.latency_cycles(verification_latency_cycles),
        .deadline_miss(verification_deadline_miss),.active_count(verification_active_count));
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin verification_hold_l<=0;verification_hold_r<=0;end
        else if(verification_valid)begin verification_hold_l<=verification_sample_l;verification_hold_r<=verification_sample_r;end
    end
    verification_telemetry u_verification_telemetry (
        .clk(clk),.rst_n(rst_n),.sample_tick(sample_tick),.request(verification_capture_request&&!bank_status_hold&&!ensemble_tx_hold),
        .sample_l(audio_word_l),.sample_r(audio_word_r),
        .flags({piano_bank_ready,piano_memory_fault,2'd0,verification_fast_key_enable,(ensemble_mix_deadline|pluck_queue_overflow|violin_fault|verification_deadline_miss|poly_deadline_miss|piano_deadline_miss|drawn_deadline_miss|drum_deadline_miss|bass_deadline_miss|fx_deadline_miss|space_deadline_miss),
                     verification_latency_valid,verification_running}),
        .active_count(verification_active_count),.latency_cycles(verification_latency_cycles),
        .uart_tx(verification_tx),.busy(verification_tx_busy));
    piano_bank_status_tx u_bank_status_tx(
        .clk(clk),.rst_n(rst_n),.query(bank_query),.query_sequence(bank_query_sequence),
        .bank_status(!piano_memory_ready?3'd5:sd_active&&!sd_drum_file?(sd_loading?3'd7:3'd6):bank_status),
        .upload_count(bank_upload_count),.status_error(bank_status_error==5?bank_status_error:
            sd_piano_finished&&sd_piano_error!=0&&(bank_status==0||bank_status==4)&&!bank_upload_session?
            (8'h80|sd_piano_error):bank_status_error),
        .verification_busy(verification_tx_busy||ensemble_tx_busy),.hold_verification(bank_status_hold),
        .tx(bank_status_tx),.busy(bank_status_busy));
    ensemble_capabilities u_ensemble_capabilities(.clk(clk),.rst_n(rst_n),.query(ensemble_query),
        .query_sequence(ensemble_sequence),.ensemble_mode(ensemble_mode),.piano_ready(piano_bank_ready),
        .other_busy(bank_status_hold||verification_tx_busy),.tx(ensemble_tx),.busy(ensemble_tx_busy),.hold_other(ensemble_tx_hold));
    verification_visuals u_verification_visuals (
        .clk(clk),.rst_n(rst_n),.sample_tick(sample_tick),.sample_l(audio_word_l),.sample_r(audio_word_r),
        .display_page(visual_display_page),.pixel_x(visual_pixel_x),.pixel_y(visual_pixel_y),.pixel_rgb(visual_pixel_rgb),.led_n(led_n));
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
    assign active = violin_active || voice_bank_active || piano_active || drawn_active || drum_active || bass_active;
    // Drum state is independent of guitar timbre/mode changes and Riff flushes.
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin drum_hold_l<=0;drum_hold_r<=0;end
        else if(drum_valid)begin drum_hold_l<=drum_sample_l;drum_hold_r<=drum_sample_r;end
    end
    always @(posedge clk or negedge rst_n) begin
        if(!rst_n||clear_voice_bank) begin
            guitar_hold<=0;piano_hold_l<=0;piano_hold_r<=0;drawn_hold<=0;fx_hold<=0;guitar_electric_hold<=0;bass_hold<=0;
        end
        else begin
            if(conditioned_sample_valid) guitar_hold<=conditioned_sample_q23;
            if(poly_mix_valid)guitar_electric_hold<=poly_mix_sample;
            if(fx_valid)fx_hold<=fx_sample;
            if(bass_valid)bass_hold<=bass_sample;
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
    verification_fast_key u_fast_pluck_button (
        .clk(clk),.rst_n(rst_n),.key_n(key_pluck_n),
        .enable(verification_fast_key_enable && !verification_running),.pressed(verification_fast_pluck));

    // The board's BL616 USB/JTAG bridge supplies a low-speed 115200-baud UART.
    // This adapter can only provide a string/fret selection and one-cycle
    // pluck request; it has no access to the audio sample path or model data.
    // ESP controls and scanned touch/Hall events share one atomic command ingress.
    wire [383:0] bulk_fragment;wire [5:0] bulk_length;wire [1:0] bulk_flags;
    wire bulk_fragment_valid,bulk_ready,bulk_busy,bulk_error,bulk_request,bulk_grant,bulk_valid,bulk_replaying;wire [7:0] bulk_byte;
    s3_bulk_buffer u_s3_bulk(.clk(clk),.rst_n(rst_n),.fragment_data(bulk_fragment),.fragment_length(bulk_length),.fragment_flags(bulk_flags),.fragment_valid(bulk_fragment_valid),.fragment_ready(bulk_ready),.request(bulk_request),.grant(bulk_grant),.busy(bulk_busy),.error(bulk_error),.data(bulk_byte),.valid(bulk_valid),.replaying(bulk_replaying));
    wire [47:0] s3_command_data,touch_command_data;
    wire s3_command_valid,s3_command_ready,touch_command_valid,ingress_ready;
    wire [127:0] s3_touch_keys;wire [7:0] s3_touch_online;
    wire s3_touch_enabled,s3_hall_valid,s3_hall_ready;
    wire [5:0] s3_hall_mask;wire [47:0] s3_hall_velocity;
    wire [29:0] s3_selected_frets,s3_hall_frets;
    wire [7:0] control_byte_data;wire control_byte_valid;
    wire [1:0] s3_instrument=timbre_violin?2'd3:timbre_bass?2'd2:timbre_piano?2'd1:2'd0;
    wire [23:0] s3_rgb_sample={visual_pixel_rgb[15:11],visual_pixel_rgb[15:13],
        visual_pixel_rgb[10:5],visual_pixel_rgb[10:9],visual_pixel_rgb[4:0],visual_pixel_rgb[4:2]};
    s3_spi_link #(.PANEL_TELEMETRY(1)) u_s3_link(.panel_values(panel_values),.panel_ui_page(panel_page),.panel_motion({panel_gesture,panel_steps}),.clk(clk),.rst_n(rst_n),.spi_sclk(spi_sclk),.spi_cs_n(spi_cs_n),.spi_mosi(spi_mosi),
        .spi_miso(spi_miso),.fpga_irq(fpga_irq),.fpga_ready(fpga_ready),
        .touch_keys(s3_touch_keys),.touch_online(s3_touch_online),.touch_enabled(s3_touch_enabled),
        .hall_mask(s3_hall_mask),.hall_velocity(s3_hall_velocity),.hall_frets(s3_hall_frets),.hall_valid(s3_hall_valid),.hall_ready(ensemble_mode||s3_hall_ready),
        .bulk_data(bulk_fragment),.bulk_length(bulk_length),.bulk_flags(bulk_flags),.bulk_valid(bulk_fragment_valid),.bulk_ready(bulk_ready),.bulk_busy(bulk_busy),.bulk_error(bulk_error),
        .command_data(s3_command_data),.command_valid(s3_command_valid),.command_ready(s3_command_ready),
        .rgb24(s3_rgb_sample),.pixel_x(visual_pixel_x),.pixel_y(visual_pixel_y),
        .display_page(visual_display_page),.instrument(s3_instrument),.hall_mode(trigger_hall_mode),.selected_frets(s3_selected_frets),
        .trigger_mode(trigger_hall_mode?2'd2:2'd1));
    touch_to_command u_touch_commands(.clk(clk),.rst_n(rst_n&&!bank_upload_session),
        .enabled(!ensemble_mode&&s3_touch_enabled&&(s3_instrument!=1||piano_bank_ready||drawn_mode)),.keys(s3_touch_keys),
        .instrument(s3_instrument),.hall_mode(trigger_hall_mode),.hall_mask(s3_hall_mask),.hall_velocity(s3_hall_velocity),.hall_frets(s3_hall_frets),
        .hall_valid(s3_hall_valid&&!ensemble_mode),.hall_ready(s3_hall_ready),.selected_frets(s3_selected_frets),
        .command_data(touch_command_data),.command_valid(touch_command_valid),.command_ready(ingress_ready&&!s3_command_valid&&!panel_command_valid));
    assign s3_command_ready=ensemble_mode||ingress_ready;
    assign panel_command_ready=ingress_ready&&(!s3_command_valid||ensemble_mode);
    s3_control_ingress u_control_ingress(.clk(clk),.rst_n(rst_n),.uart_rx_i(uart_rx_i),
        .bulk_request(bulk_request),.bulk_busy(bulk_busy),.bulk_replaying(bulk_replaying),.bulk_data(bulk_byte),.bulk_valid(bulk_valid),.bulk_grant(bulk_grant),.bulk_allowed(!sd_active),
        .commands_enabled(pluck_ingress_ready&&!bank_upload_session),
        .command_data((s3_command_valid&&!ensemble_mode)?s3_command_data:panel_command_valid?panel_command_data:touch_command_data),
        .command_valid(panel_command_valid||(!ensemble_mode&&(s3_command_valid||touch_command_valid))),.command_ready(ingress_ready),
        .byte_data(control_byte_data),.byte_valid(control_byte_valid));
    guitar_uart_trigger #(.EXTERNAL_BYTES(1'b1),.EXTERNAL_STAGE(1'b1)) u_uart_trigger (
        .clk(clk),
        .rst_n(rst_n),
        .uart_rx_i(uart_rx_i),
        .stage_active(sd_active&&!sd_drum_file),.stage_valid(sd_stage_valid&&!sd_drum_file),.stage_index(sd_stage_index),.stage_data(sd_stage_data),
        .external_byte_data(control_byte_data),.external_byte_valid(control_byte_valid),.upload_session(bank_upload_session),.bank_upload_cancel(bank_upload_cancel),
        .local_level_step(local_level_step),.local_level_bus(timbre_violin&&screen_selected_bus==1?2'd3:screen_selected_bus),
        .trigger_string_sel(uart_trigger_string_sel),
        .trigger_fret_sel(uart_trigger_fret_sel),
        .trigger_velocity(uart_trigger_velocity),
        .trigger(uart_pluck_trigger),
        .mode_set(uart_mode_set),
        .mode_poly4(uart_mode_poly4),
        .timbre_set(uart_timbre_set),
        .timbre_piano(uart_timbre_piano),
        .timbre_bass(uart_timbre_bass),.timbre_violin(uart_timbre_violin),
        .violin_note_on(uart_violin_on),.violin_note_off(uart_violin_off),.violin_legato(uart_violin_legato),
        .violin_key(uart_violin_key),.violin_velocity(uart_violin_velocity),.violin_bus_level(violin_bus_level),
        .hall_mode(trigger_hall_mode),.trigger_mode_changed(trigger_mode_changed),
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
        .uart_byte_data(uart_byte_data),.uart_byte_valid(uart_byte_valid),
        .bank_upload_ready(bank_upload_ready&&!sd_active),.bank_upload_begin(bank_upload_begin),
        .bank_upload_valid(bank_upload_valid),.bank_upload_commit(bank_upload_commit),.bank_upload_error(bank_upload_error),
        .bank_upload_index(bank_upload_index),.bank_upload_data(bank_upload_data),
        .bank_query(bank_query),.bank_query_sequence(bank_query_sequence)
        ,.ensemble_mode(ensemble_mode),.ensemble_changed(ensemble_changed),.ensemble_valid(ensemble_valid),.ensemble_query(ensemble_query)
        ,.ensemble_target(ensemble_target),.ensemble_a(ensemble_a),.ensemble_b(ensemble_b),.ensemble_c(ensemble_c)
        ,.ensemble_sequence(ensemble_sequence),.bass_bus_level(bass_bus_level)
    );

    drawn_synth_control u_drawn_control(
        .clk(clk),.rst_n(rst_n),.byte_data(uart_byte_data),.byte_valid(uart_byte_valid),
        .write_allowed(!drawn_active),.mode(drawn_mode),.mode_event(drawn_mode_event),
        .envelope_step(drawn_envelope_step),.ram_we(drawn_ram_we),
        .ram_addr(drawn_ram_addr),.ram_data(drawn_ram_data),
        .wave_loaded(drawn_wave_loaded),.envelope_loaded(drawn_envelope_loaded),
        .upload_error(drawn_upload_error));

    drum_machine u_drums(
        .parameter_load_begin(sd_upload_begin&&sd_drum_file),.parameter_byte_valid(sd_stage_valid&&sd_drum_file),
        .parameter_chunk_valid(sd_upload_valid&&sd_drum_file),.parameter_load_commit(sd_upload_commit&&sd_drum_file),
        .parameter_load_error(sd_upload_error&&sd_drum_file),.parameter_byte_data(sd_stage_data),
        .parameter_chunk_index(sd_upload_index),.parameter_load_ready(drum_parameter_ready),
        .parameter_chunk_count(drum_parameter_count),.parameter_initialized(drum_parameter_initialized),
        .parameter_fault(drum_parameter_fault),.parameter_active_bank(drum_parameter_active_bank),
        .clk(clk),.rst_n(rst_n),.sample_tick(sample_tick),
        .byte_data(uart_byte_data),.byte_valid(uart_byte_valid),
        .sample_valid(drum_valid),.sample_l(drum_sample_l),.sample_r(drum_sample_r),
        .playing(drum_playing),.pattern_ready(drum_ready),.current_step(drum_step),
        .active(drum_active),.deadline_miss(drum_deadline_miss),.clipped(drum_clipped));

    guitar_pitch_control u_pitch_control(
        .clk(clk),.rst_n(rst_n),.byte_valid(uart_byte_valid),.byte_data(uart_byte_data),
        .ratio_q20(pitch_ratio_q20),.enabled(pitch_enabled));
    reg [47:0] panel_guitar_product;
    always @(posedge clk)panel_guitar_product<=(pitch_enabled?pitch_ratio_q20:24'd1048576)*melodic_ratio;
    wire [23:0] panel_guitar_ratio=panel_guitar_product[47:20]>4194304?24'd4194304:
      panel_guitar_product[47:20]<262144?24'd262144:panel_guitar_product[43:20];
    guitar_pitch_shift u_pitch_shift(
        .clk(clk),.rst_n(rst_n),.sample_tick(sample_tick),
        .ratio_q20(panel_guitar_ratio),.ratio_smoothed(pitch_ratio_smoothed));

    guitar_fx_control u_fx_control(
        .clk(clk),.rst_n(rst_n),.byte_data(uart_byte_data),.byte_valid(uart_byte_valid),
        .amp(fx_amp),.drive(fx_drive),.tone(fx_tone),.level(fx_level),.mix(fx_mix),
        .rate(fx_rate),.depth(fx_depth),.threshold(fx_threshold),
        .modulation(fx_modulation),.flags(fx_flags),.changed(fx_changed));
    guitar_fx u_fx(
        .clk(clk),.rst_n(rst_n),.sample_tick(sample_tick),.history_clear(clear_voice_bank),
        .sample_in(ensemble_mode?(fx_electric_source?guitar_electric_hold:guitar_hold):
            (timbre_piano||timbre_violin)?24'sd0:(timbre_bass?bass_hold:(fx_electric_source?guitar_electric_hold:guitar_hold))),
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
        .clk(clk),.rst_n(rst_n),
        .memory_ready(piano_memory_ready),.transport_fault(piano_transport_fault),.memory_fault(space_memory_fault),
        .req_valid(space_req_valid),.req_ready(space_req_ready),.req_data(space_req_data),
        .rsp_valid(space_rsp_valid),.rsp_ready(space_rsp_ready),.rsp_data(space_rsp_data),.sample_tick(sample_tick),.changed(space_changed),
        .sample_l(instrument_mix_l),.sample_r(instrument_mix_r),
        .chorus_mix(space_chorus_mix),.chorus_rate(space_chorus_rate),
        .chorus_depth(space_chorus_depth),.delay_mix(space_delay_mix),
        .delay_time(space_delay_time),.delay_feedback(space_delay_feedback),
        .bypass(space_bypass),.output_valid(space_valid),
        .output_l(space_sample_l),.output_r(space_sample_r),
        .deadline_miss(space_deadline_miss));

    guitar_note_params #(.PRECLAMPED(1)) u_note_params (
        .string_sel(lookup_string_q),
        .fret_sel(lookup_fret_q),
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

    // Split fret limiting from the original table. Carry the trigger and all
    // associated metadata through the same stage; table values stay identical.
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            lookup_string_q<=5;lookup_fret_q<=0;lookup_velocity_q<=0;
            lookup_custom_q<=0;lookup_note_q<=0;
        end else begin
            lookup_string_q<=ensemble_mode?ensemble_string:string_sel;
            lookup_fret_q<=ensemble_mode?ensemble_b[4:0]:fret_sel>20 ? 5'd20 : fret_sel;
            lookup_velocity_q<=ensemble_mode?ensemble_c[6:0]:note_velocity;lookup_custom_q<=uart_custom_envelope_mode;
            lookup_note_q<=ensemble_mode?ensemble_guitar:note_on&&!timbre_piano&&!timbre_bass&&!timbre_violin;
        end
    end

    // Note parameters are stable for a sample frame after a pluck request.
    // Register the lookup outputs and align the poly32 trigger to both stages so
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
            poly_string_q<=lookup_string_q;
            poly_velocity_q<=lookup_velocity_q;
            poly_custom_q<=lookup_custom_q;
            poly_note_on_q<=lookup_note_q;
        end
    end

    pluck_event_queue u_pluck_event_queue(
        .clk(clk),.rst_n(rst_n),.sample_tick(sample_tick),
        .clear(ensemble_changed||trigger_mode_changed||uart_mode_set||uart_timbre_set||(drawn_mode_event&&timbre_piano&&!ensemble_mode)),
        .uart_valid(!ensemble_mode&&uart_pluck_trigger&&(!timbre_bass||uart_trigger_string_sel>=2)),
        .uart_event({uart_trigger_string_sel,uart_trigger_fret_sel,uart_trigger_velocity}),
        .local_valid(!ensemble_mode&&(long_pluck_pulse||verification_fast_pluck)),
        .local_event({pluck_selected_string,pluck_selected_fret,pluck_selected_velocity}),
        .ingress_ready(pluck_ingress_ready),.event_valid(pluck_event_valid),
        .event_data(pluck_event_data),.overflow(pluck_queue_overflow));

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            string_sel   <= 3'd5;
            fret_sel     <= 5'd0;
            note_velocity <= 7'd110;
            note_on <= 1'b0;
            pluck_selected_string<=3'd5;
            pluck_selected_fret<=5'd0;
            pluck_selected_velocity<=7'd110;
            poly_mode <= 1'b1;
            timbre_piano <= 1'b0;
            timbre_bass <= 1'b0;
            timbre_violin <= 1'b0;
            clear_voice_bank <= 1'b0;
        end else begin
            note_on <= 1'b0;
            clear_voice_bank <= 1'b0;

            if (pluck_event_valid) begin
                {string_sel,fret_sel,note_velocity}<=pluck_event_data;
                note_on<=1'b1;
            end

            if (uart_pluck_trigger && (!timbre_bass || uart_trigger_string_sel>=2)) begin
                pluck_selected_string<=uart_trigger_string_sel;
                pluck_selected_fret<=uart_trigger_fret_sel;
                pluck_selected_velocity<=uart_trigger_velocity;
            end

            // Mode changes are control-only frames. Flush voice and body
            // history once so samples from the previous mode cannot leak
            // into the first note used for comparison.
            if (uart_mode_set) begin
                poly_mode <= uart_mode_poly4;
                note_on <= 1'b0;
                clear_voice_bank <= 1'b1;
            end
            // Clear old notes on a timbre switch so the previous instrument
            // cannot reappear when the user switches back later.
            if (uart_timbre_set) begin
                note_on <= 1'b0;
                timbre_piano <= uart_timbre_piano;
                timbre_bass <= uart_timbre_bass;
                timbre_violin <= uart_timbre_violin;
                if(uart_timbre_bass&&string_sel<2)string_sel<=3'd5;
                if(uart_timbre_bass&&pluck_selected_string<2)pluck_selected_string<=3'd5;
                clear_voice_bank <= 1'b1;
            end
            if(ensemble_changed&&ensemble_mode)poly_mode<=1;
            if(ensemble_changed||trigger_mode_changed||(effective_upload_begin&&(timbre_piano||ensemble_mode)))begin note_on<=0;clear_voice_bank<=1;end
            if(drawn_mode_event&&timbre_piano&&!ensemble_mode)begin
                note_on<=1'b0;
                clear_voice_bank<=1'b1;
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
        .pitch_enabled((pitch_enabled||panel_active)&&(ensemble_mode||(!timbre_piano&&!timbre_bass))),.pitch_ratio_q20(pitch_ratio_smoothed),
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

    violin_channel #(.PANEL_PITCH(1)) u_violin_channel(.panel_ratio_q20(melodic_ratio),.panel_inverse_q20(melodic_inverse),.clk(clk),.rst_n(rst_n),.sample_tick(sample_tick),.selected(timbre_violin||ensemble_mode),
        .timbre_change(ensemble_changed||uart_timbre_set||uart_mode_set||trigger_mode_changed),
        .note_on(ensemble_mode?(ensemble_violin&&ensemble_c[0]):uart_violin_on),
        .note_off(ensemble_mode?(ensemble_violin&&!ensemble_c[0]):uart_violin_off),
        .legato(ensemble_mode?ensemble_c[1]:uart_violin_legato),
        .key(ensemble_mode?ensemble_a[6:0]:uart_violin_key),.velocity(ensemble_mode?ensemble_b[6:0]:uart_violin_velocity),.pluck(note_on&&!ensemble_mode),
        .string_sel(string_sel),.fret_sel(fret_sel),.pluck_velocity(note_velocity),
        .sample_out(violin_sample),.fault(violin_fault),.active(violin_active));
    bass_poly8 #(.PANEL_PITCH(1)) u_bass(.panel_ratio_q20(melodic_ratio),
        .clk(clk),.rst_n(voice_path_rst_n),.sample_tick(sample_tick),
        .note_on(ensemble_mode?ensemble_bass:note_on&&timbre_bass),.poly_mode(poly_mode),
        .string_sel(ensemble_mode?ensemble_string:string_sel),.fret_sel(ensemble_mode?ensemble_b[4:0]:fret_sel),
        .velocity(ensemble_mode?ensemble_c[6:0]:note_velocity),
        .sample_valid(bass_valid),.sample_out(bass_sample),
        .active(bass_active),.deadline_miss(bass_deadline_miss));

    sd_spi_card #(.POWERUP_CLKS(SD_POWERUP_CLKS)) u_sd_card(.clk(clk),.rst_n(rst_n),
        .read_start(sd_read_start),.read_lba(sd_read_lba),.initialized(),.read_ready(sd_card_ready),
        .error(sd_card_error),.data_byte(sd_byte),.data_valid(sd_byte_valid),.sector_done(sd_sector_done),
        .sd_clk(sd_clk),.sd_mosi(sd_mosi),.sd_miso(sd_miso),.sd_cs(sd_cs));
    piano_sd_boot #(.KEEP_STAGE(0),.MULTI_FILE(1)) u_sd_boot(.clk(clk),.rst_n(rst_n),.cancel(bank_upload_cancel),
        .memory_ready(sd_drum_file||piano_memory_ready),.next_file(sd_next_file),.file_select(sd_drum_file),
        .card_ready(sd_card_ready),.card_error(sd_card_error),.card_byte(sd_byte),.card_byte_valid(sd_byte_valid),
        .card_sector_done(sd_sector_done),.card_read_start(sd_read_start),.card_read_lba(sd_read_lba),
        .upload_begin(sd_upload_begin),.upload_valid(sd_upload_valid),.upload_commit(sd_upload_commit),.upload_error(sd_upload_error),
        .upload_index(sd_upload_index),.upload_data(sd_upload_data),
        .upload_ready(sd_drum_file?drum_parameter_ready:bank_upload_ready),
        .upload_count(sd_drum_file?drum_parameter_count:bank_upload_count),
        .bank_initialized(sd_drum_file?drum_parameter_initialized:piano_bank_ready),
        .bank_fault(sd_drum_file?drum_parameter_fault:piano_memory_fault),
        .active(sd_active),.finished(sd_finished),.error(sd_boot_error),.loading(sd_loading),
        .stage_valid(sd_stage_valid),.stage_index(sd_stage_index),.stage_data(sd_stage_data));
    piano_wavetable16_tdm #(.PANEL_PITCH(1)) u_piano_wavetable(.panel_ratio_q20(melodic_ratio),
        .clk(clk),.rst_n(voice_path_rst_n),.sample_tick(sample_tick),
        .note_on(piano_note_on_q),.note_off(piano_note_off_q),
        .poly_mode(poly_mode),.requested_key(piano_key_q),
        .velocity(piano_velocity_q),.pedal_level(uart_piano_pedal_level),
        .sample_valid(piano_mix_valid),.sample_out(piano_mix_sample),
        .active(piano_active),.deadline_miss(piano_deadline_miss),
        .requested_phase_step(piano_requested_phase_step),
        .memory_rst_n(rst_n),.memory_ready(piano_memory_ready),.transport_fault(piano_transport_fault),
        .bank_ready(piano_bank_ready),.memory_fault(piano_memory_fault),
        .upload_begin(effective_upload_begin),.upload_valid(sd_active?(sd_upload_valid&&!sd_drum_file):bank_upload_valid),
        .upload_commit(sd_active?(sd_upload_commit&&!sd_drum_file):bank_upload_commit),
        .upload_error((sd_upload_error&&!sd_drum_file)||(bank_upload_error&&!sd_active)),
        .upload_index(sd_active?sd_upload_index:bank_upload_index),.upload_data(bank_upload_data),
        .upload_ready(bank_upload_ready),.upload_count(bank_upload_count),
        .bank_status(bank_status),.status_error(bank_status_error),
        .req_valid(piano_req_valid),.req_ready(piano_req_ready),.req_data(piano_req_data),
        .rsp_valid(piano_rsp_valid),.rsp_ready(piano_rsp_ready),.rsp_data(piano_rsp_data)
    );
    drawn_synth16 #(.PANEL_PITCH(1)) u_drawn_synth(.panel_ratio_q20(melodic_ratio),
        .clk(clk),.rst_n(rst_n),
        .voice_rst_n(voice_path_rst_n&&!ensemble_mode&&timbre_piano&&drawn_mode),.sample_tick(sample_tick),
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
