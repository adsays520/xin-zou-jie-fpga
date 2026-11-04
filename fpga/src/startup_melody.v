// One-shot vocal melody transcribed from the supplied "Chengdu" score.
// It starts directly at "rang wo diao xia yan lei de" and stops on the
// sustained "liu" in "ye bu ting liu".  The written repeat and the two
// endings are expanded explicitly; no intro events are present.
//
// Score key: 1 = C, meter: 6/8.  Timing is deliberately quantized to the
// written eighth-note grid (12600 samples at 48 kHz).  Natural overlap comes
// from the independent ringing voices, not from random timing offsets.
//
// Pitch placement preserves the octave marks in the numbered score:
//   low 5 = G3: physical string 3 / selector 2 / fret 0
//       1 = C4: physical string 2 / selector 1 / fret 1
//       2 = D4: physical string 2 / selector 1 / fret 3
//       3 = E4: physical string 1 / selector 0 / fret 0
//       5 = G4: physical string 1 / selector 0 / fret 3
//       6 = A4: physical string 1 / selector 0 / fret 5
//  high 1 = C5: physical string 1 / selector 0 / fret 8
//
// This module emits only note selection and a one-clock trigger.  It does not
// alter the voice core, pitch parameters, envelope, filters or audio path.
module startup_melody (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       sample_tick,
    input  wire       cancel,
    output reg        active,
    output wire [2:0] trigger_string_sel,
    output wire [4:0] trigger_fret_sel,
    output reg        trigger
);
    localparam [2:0] P_REST = 3'd0;
    localparam [2:0] P_LOW5 = 3'd1;
    localparam [2:0] P_C4   = 3'd2;
    localparam [2:0] P_D4   = 3'd3;
    localparam [2:0] P_E4   = 3'd4;
    localparam [2:0] P_G4   = 3'd5;
    localparam [2:0] P_A4   = 3'd6;
    localparam [2:0] P_C5   = 3'd7;

    localparam [7:0] FIRST_BASE_START  = 8'd1;
    localparam [7:0] FIRST_BASE_END    = 8'd66;
    localparam [7:0] SECOND_BASE_START = 8'd72;
    localparam [7:0] SECOND_BASE_END   = 8'd137;
    localparam [7:0] TAIL_START        = 8'd138;
    localparam [7:0] LAST_EVENT        = 8'd178;

    reg started;
    reg [7:0] event_index;
    reg [17:0] frames_left;
    wire [2:0] current_pitch = melody_pitch(event_index);

    assign trigger_string_sel = pitch_string(current_pitch);
    assign trigger_fret_sel = pitch_fret(current_pitch);

    // The common 15-bar verse melody.  It is used twice: first for
    // "rang wo...zi you", then for "fen bie...ji ni".
    function [2:0] base_pitch;
        input [6:0] index;
        begin
            case (index)
                // 1.  2 2 3
                7'd0:  base_pitch = P_C4;
                7'd1:  base_pitch = P_D4;
                7'd2:  base_pitch = P_D4;
                7'd3:  base_pitch = P_E4;

                // 5 3 3 3 0 low-5
                7'd4:  base_pitch = P_G4;
                7'd5:  base_pitch = P_E4;
                7'd6:  base_pitch = P_E4;
                7'd7:  base_pitch = P_E4;
                7'd8:  base_pitch = P_REST;
                7'd9:  base_pitch = P_LOW5;

                // 1 1 2 1 6 | low-5. 0 low-5
                7'd10: base_pitch = P_C4;
                7'd11: base_pitch = P_C4;
                7'd12: base_pitch = P_D4;
                7'd13: base_pitch = P_C4;
                7'd14: base_pitch = P_A4;
                7'd15: base_pitch = P_LOW5;
                7'd16: base_pitch = P_REST;
                7'd17: base_pitch = P_LOW5;

                // 1. 2 2 3 | 6 3 5 5 0 2
                7'd18: base_pitch = P_C4;
                7'd19: base_pitch = P_D4;
                7'd20: base_pitch = P_D4;
                7'd21: base_pitch = P_E4;
                7'd22: base_pitch = P_A4;
                7'd23: base_pitch = P_E4;
                7'd24: base_pitch = P_G4;
                7'd25: base_pitch = P_G4;
                7'd26: base_pitch = P_REST;
                7'd27: base_pitch = P_D4;

                // 1 2 3 5 | 2. 0 3
                7'd28: base_pitch = P_C4;
                7'd29: base_pitch = P_D4;
                7'd30: base_pitch = P_E4;
                7'd31: base_pitch = P_G4;
                7'd32: base_pitch = P_D4;
                7'd33: base_pitch = P_REST;
                7'd34: base_pitch = P_E4;

                // 5 5 5 3 5 | 6 high-1 6 6 0 3
                7'd35: base_pitch = P_G4;
                7'd36: base_pitch = P_G4;
                7'd37: base_pitch = P_G4;
                7'd38: base_pitch = P_E4;
                7'd39: base_pitch = P_G4;
                7'd40: base_pitch = P_A4;
                7'd41: base_pitch = P_C5;
                7'd42: base_pitch = P_A4;
                7'd43: base_pitch = P_A4;
                7'd44: base_pitch = P_REST;
                7'd45: base_pitch = P_E4;

                // 2 1 2 3 | 3. 0 3
                7'd46: base_pitch = P_D4;
                7'd47: base_pitch = P_C4;
                7'd48: base_pitch = P_D4;
                7'd49: base_pitch = P_E4;
                7'd50: base_pitch = P_E4;
                7'd51: base_pitch = P_REST;
                7'd52: base_pitch = P_E4;

                // 5. 0 3 3 | 2 1 1 1 low-5
                7'd53: base_pitch = P_G4;
                7'd54: base_pitch = P_REST;
                7'd55: base_pitch = P_E4;
                7'd56: base_pitch = P_E4;
                7'd57: base_pitch = P_D4;
                7'd58: base_pitch = P_C4;
                7'd59: base_pitch = P_C4;
                7'd60: base_pitch = P_C4;
                7'd61: base_pitch = P_LOW5;

                // 2 1 3 2
                7'd62: base_pitch = P_D4;
                7'd63: base_pitch = P_C4;
                7'd64: base_pitch = P_E4;
                7'd65: base_pitch = P_D4;

                default: base_pitch = P_REST;
            endcase
        end
    endfunction

    function [2:0] base_units;
        input [6:0] index;
        begin
            case (index)
                // Dotted-quarter notes.
                7'd0, 7'd15, 7'd18, 7'd32, 7'd50, 7'd53:
                    base_units = 3'd3;

                // Quarter notes.
                7'd10, 7'd16, 7'd28, 7'd31, 7'd33, 7'd35,
                7'd46, 7'd49, 7'd51, 7'd59, 7'd62, 7'd65:
                    base_units = 3'd2;

                // All other entries are eighth notes.
                default:
                    base_units = 3'd1;
            endcase
        end
    endfunction

    // Tail after the repeated verse: second ending, "Chengdu" cadence, then
    // "he wo zai Chengdu de jie tou zou yi zou ... ye bu ting liu".
    function [2:0] tail_pitch;
        input [5:0] index;
        begin
            case (index)
                // Second ending: 5. 0 3 2 | 6 1 0 1 2
                6'd0:  tail_pitch = P_G4;
                6'd1:  tail_pitch = P_REST;
                6'd2:  tail_pitch = P_E4;
                6'd3:  tail_pitch = P_D4;
                6'd4:  tail_pitch = P_A4;
                6'd5:  tail_pitch = P_C4;
                6'd6:  tail_pitch = P_REST;
                6'd7:  tail_pitch = P_C4;
                6'd8:  tail_pitch = P_D4;

                // 1--- | 0. 0 3
                6'd9:  tail_pitch = P_C4;
                6'd10: tail_pitch = P_REST;
                6'd11: tail_pitch = P_E4;

                // 5 5 5 3 5 | 6 6 3 2
                6'd12: tail_pitch = P_G4;
                6'd13: tail_pitch = P_G4;
                6'd14: tail_pitch = P_G4;
                6'd15: tail_pitch = P_E4;
                6'd16: tail_pitch = P_G4;
                6'd17: tail_pitch = P_A4;
                6'd18: tail_pitch = P_A4;
                6'd19: tail_pitch = P_E4;
                6'd20: tail_pitch = P_D4;

                // 1 1 2 5 | 3. 0 3
                6'd21: tail_pitch = P_C4;
                6'd22: tail_pitch = P_C4;
                6'd23: tail_pitch = P_D4;
                6'd24: tail_pitch = P_G4;
                6'd25: tail_pitch = P_E4;
                6'd26: tail_pitch = P_REST;
                6'd27: tail_pitch = P_E4;

                // 5. 5 3 5 | 6 6 3 2
                6'd28: tail_pitch = P_G4;
                6'd29: tail_pitch = P_G4;
                6'd30: tail_pitch = P_E4;
                6'd31: tail_pitch = P_G4;
                6'd32: tail_pitch = P_A4;
                6'd33: tail_pitch = P_A4;
                6'd34: tail_pitch = P_E4;
                6'd35: tail_pitch = P_D4;

                // 1 1 2 3 | 2--- (stop on "liu")
                6'd36: tail_pitch = P_C4;
                6'd37: tail_pitch = P_C4;
                6'd38: tail_pitch = P_D4;
                6'd39: tail_pitch = P_E4;
                6'd40: tail_pitch = P_D4;

                default: tail_pitch = P_REST;
            endcase
        end
    endfunction

    function [2:0] tail_units;
        input [5:0] index;
        begin
            case (index)
                // Six-eighth sustained notes.
                6'd9, 6'd40:
                    tail_units = 3'd6;

                // Five-eighth rest before the chorus pickup.
                6'd10:
                    tail_units = 3'd5;

                // Dotted-quarter notes.
                6'd0, 6'd25, 6'd28:
                    tail_units = 3'd3;

                // Quarter notes.
                6'd8, 6'd12, 6'd17, 6'd20, 6'd21, 6'd24,
                6'd26, 6'd32, 6'd35, 6'd36, 6'd39:
                    tail_units = 3'd2;

                default:
                    tail_units = 3'd1;
            endcase
        end
    endfunction

    function [2:0] melody_pitch;
        input [7:0] index;
        begin
            if (index == 8'd0)
                // Pickup "rang".
                melody_pitch = P_LOW5;
            else if ((index >= FIRST_BASE_START) &&
                     (index <= FIRST_BASE_END))
                melody_pitch = base_pitch(index - FIRST_BASE_START);
            else if ((index >= SECOND_BASE_START) &&
                     (index <= SECOND_BASE_END))
                melody_pitch = base_pitch(index - SECOND_BASE_START);
            else if (index >= TAIL_START)
                melody_pitch = tail_pitch(index - TAIL_START);
            else begin
                // First ending: 1. 0. | 0. 0 low-5.
                case (index)
                    8'd67: melody_pitch = P_C4;
                    8'd68: melody_pitch = P_REST;
                    8'd69: melody_pitch = P_REST;
                    8'd70: melody_pitch = P_REST;
                    8'd71: melody_pitch = P_LOW5;
                    default: melody_pitch = P_REST;
                endcase
            end
        end
    endfunction

    function [2:0] melody_units;
        input [7:0] index;
        begin
            if (index == 8'd0)
                melody_units = 3'd1;
            else if ((index >= FIRST_BASE_START) &&
                     (index <= FIRST_BASE_END))
                melody_units = base_units(index - FIRST_BASE_START);
            else if ((index >= SECOND_BASE_START) &&
                     (index <= SECOND_BASE_END))
                melody_units = base_units(index - SECOND_BASE_START);
            else if (index >= TAIL_START)
                melody_units = tail_units(index - TAIL_START);
            else begin
                case (index)
                    8'd67: melody_units = 3'd3;
                    8'd68: melody_units = 3'd3;
                    8'd69: melody_units = 3'd3;
                    8'd70: melody_units = 3'd2;
                    8'd71: melody_units = 3'd1;
                    default: melody_units = 3'd1;
                endcase
            end
        end
    endfunction

    function [17:0] melody_frames;
        input [7:0] index;
        reg [2:0] units;
        begin
            units = melody_units(index);
            case (units)
                3'd1: melody_frames = 18'd12600;
                3'd2: melody_frames = 18'd25200;
                3'd3: melody_frames = 18'd37800;
                3'd5: melody_frames = 18'd63000;
                3'd6: melody_frames = 18'd75600;
                default: melody_frames = 18'd12600;
            endcase
        end
    endfunction

    function [2:0] pitch_string;
        input [2:0] pitch;
        begin
            case (pitch)
                P_LOW5: pitch_string = 3'd2;
                P_C4, P_D4: pitch_string = 3'd1;
                default: pitch_string = 3'd0;
            endcase
        end
    endfunction

    function [4:0] pitch_fret;
        input [2:0] pitch;
        begin
            case (pitch)
                P_LOW5: pitch_fret = 5'd0;
                P_C4:   pitch_fret = 5'd1;
                P_D4:   pitch_fret = 5'd3;
                P_E4:   pitch_fret = 5'd0;
                P_G4:   pitch_fret = 5'd3;
                P_A4:   pitch_fret = 5'd5;
                P_C5:   pitch_fret = 5'd8;
                default: pitch_fret = 5'd0;
            endcase
        end
    endfunction

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            active <= 1'b1;
            started <= 1'b0;
            event_index <= 8'd0;
            frames_left <= 18'd0;
            trigger <= 1'b0;
        end else begin
            trigger <= 1'b0;
            if (cancel) begin
                active <= 1'b0;
            end else if (active && sample_tick) begin
                if (!started) begin
                    started <= 1'b1;
                    frames_left <= melody_frames(8'd0) - 1'b1;
                    trigger <= (melody_pitch(8'd0) != P_REST);
                end else if (frames_left != 18'd0) begin
                    frames_left <= frames_left - 1'b1;
                end else if (event_index == LAST_EVENT) begin
                    active <= 1'b0;
                end else begin
                    event_index <= event_index + 1'b1;
                    frames_left <= melody_frames(event_index + 1'b1) - 1'b1;
                    trigger <= (melody_pitch(event_index + 1'b1) != P_REST);
                end
            end
        end
    end
endmodule
