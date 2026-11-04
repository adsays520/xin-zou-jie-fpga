// Per-voice acoustic output polish. This block is deliberately outside
// guitar_voice: it cannot alter the delay length, allpass tuning, loop damping
// or excitation that establish the note pitch and the physical-string timbre.
//
// Two conservative operations are performed at the 48 kHz sample boundary:
//   1. A unity-DC three-tap binomial FIR, (x[n] + 2*x[n-1] + x[n-2]) / 4,
//      gently removes the brittle top octave without moving spectral peaks.
//   2. A string-dependent release gain makes the synthesized residual decay
//      below audibility before guitar_voice reaches its fixed lifetime limit.
//      Bass strings retain a longer tail than treble strings.
module guitar_output_polish #(
    parameter integer SAMPLE_W = 24
)(
    input  wire                       clk,
    input  wire                       rst_n,
    input  wire                       note_on,
    input  wire [2:0]                 string_sel,
    input  wire                       sample_valid,
    input  wire signed [SAMPLE_W-1:0] sample_in,
    output reg                        output_valid,
    output reg signed [SAMPLE_W-1:0]  sample_out
);
    localparam [15:0] UNITY_Q15 = 16'd32767;

    reg signed [SAMPLE_W-1:0] sample_z1;
    reg signed [SAMPLE_W-1:0] sample_z2;
    reg [17:0] age_samples;
    reg [17:0] hold_samples;
    reg [3:0] release_shift;
    reg [15:0] release_gain_q15;

    wire signed [25:0] fir_sum =
        {{2{sample_in[SAMPLE_W-1]}}, sample_in}
      + ({{2{sample_z1[SAMPLE_W-1]}}, sample_z1} <<< 1)
      + {{2{sample_z2[SAMPLE_W-1]}}, sample_z2};
    // Compensate the arithmetic right-shift bias for negative samples.
    wire signed [25:0] fir_rounded = fir_sum[25]
        ? fir_sum + 26'sd3 : fir_sum;
    wire signed [SAMPLE_W-1:0] fir_sample = fir_rounded >>> 2;
    wire signed [39:0] gain_product =
        $signed(fir_sample) * $signed({1'b0, release_gain_q15});
    wire [15:0] shifted_release = release_gain_q15 >> release_shift;
    wire [15:0] release_step = (shifted_release == 16'd0)
        ? 16'd1 : shifted_release;

    function [17:0] string_hold_samples;
        input [2:0] selected_string;
        begin
            case (selected_string)
                3'd0: string_hold_samples = 18'd30000; // E4: 0.625 s
                3'd1: string_hold_samples = 18'd36000; // B3: 0.750 s
                3'd2: string_hold_samples = 18'd43200; // G3: 0.900 s
                3'd3: string_hold_samples = 18'd50400; // D3: 1.050 s
                3'd4: string_hold_samples = 18'd60000; // A2: 1.250 s
                default: string_hold_samples = 18'd67200; // E2: 1.400 s
            endcase
        end
    endfunction

    function [3:0] string_release_shift;
        input [2:0] selected_string;
        begin
            // One-pole gain time constants: about 0.34 s for strings 1..3
            // and 0.68 s for the three wound bass strings.
            if (selected_string <= 3'd2)
                string_release_shift = 4'd14;
            else
                string_release_shift = 4'd15;
        end
    endfunction

    function signed [SAMPLE_W-1:0] sat_sample;
        input signed [39:0] value;
        begin
            if (value > 40'sd8388607)
                sat_sample = 24'sh7fffff;
            else if (value < -40'sd8388608)
                sat_sample = 24'sh800000;
            else
                sat_sample = value[SAMPLE_W-1:0];
        end
    endfunction

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sample_z1 <= {SAMPLE_W{1'b0}};
            sample_z2 <= {SAMPLE_W{1'b0}};
            age_samples <= 18'd0;
            hold_samples <= 18'd67200;
            release_shift <= 4'd15;
            release_gain_q15 <= UNITY_Q15;
            output_valid <= 1'b0;
            sample_out <= {SAMPLE_W{1'b0}};
        end else begin
            output_valid <= 1'b0;

            // A new note starts with full gain and fresh FIR history, so an
            // old voice's residue cannot contaminate a stolen/retriggered note.
            if (note_on) begin
                sample_z1 <= {SAMPLE_W{1'b0}};
                sample_z2 <= {SAMPLE_W{1'b0}};
                age_samples <= 18'd0;
                hold_samples <= string_hold_samples(string_sel);
                release_shift <= string_release_shift(string_sel);
                release_gain_q15 <= UNITY_Q15;
                sample_out <= {SAMPLE_W{1'b0}};
            end else if (sample_valid) begin
                sample_z2 <= sample_z1;
                sample_z1 <= sample_in;
                output_valid <= 1'b1;
                sample_out <= sat_sample(gain_product >>> 15);

                if (age_samples != 18'h3ffff)
                    age_samples <= age_samples + 1'b1;

                if (age_samples >= hold_samples) begin
                    if (release_gain_q15 > release_step)
                        release_gain_q15 <= release_gain_q15 - release_step;
                    else
                        release_gain_q15 <= 16'd0;
                end
            end
        end
    end
endmodule
