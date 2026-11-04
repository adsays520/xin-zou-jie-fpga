// Low-level downward expander for one time-multiplexed voice context.
//
// This block never changes pitch, delay length, loop coefficients or the
// physical-string state.  Above START_LEVEL its target is exact unity.  Only
// the late, low-level tail is progressively attenuated so quantization and
// residual excitation noise cannot dominate after the musical partials fade.
// One instance is shared by all 32 contexts in guitar_poly32_tdm.
module poly32_tail_cleaner #(
    parameter [23:0] START_LEVEL = 24'd65536, // -42.1 dBFS in signed Q23
    parameter integer GAIN_RIGHT_SHIFT = 1,   // START_LEVEL >> 1 = Q15 unity
    parameter [15:0] FALL_STEP = 16'd256,     // 2.67 ms, unity to zero
    parameter [15:0] RISE_STEP = 16'd256      // 2.67 ms soft pick attack
)(
    input  wire [23:0] envelope_level,
    input  wire [23:0] sample_magnitude,
    input  wire [15:0] gain_in,
    output reg  [15:0] gain_next,
    output wire [15:0] target_gain,
    output wire        cleaning
);
    wire [23:0] control_level = sample_magnitude > envelope_level
        ? sample_magnitude : envelope_level;
    wire [23:0] scaled_gain = control_level >> GAIN_RIGHT_SHIFT;
    wire [15:0] expanded_gain = |scaled_gain[23:16]
        ? 16'd32768 : scaled_gain[15:0];

    assign target_gain = control_level >= START_LEVEL
        ? 16'd32768 : expanded_gain;
    assign cleaning = gain_in != 16'd32768;

    always @* begin
        gain_next = gain_in;
        if (target_gain < gain_in) begin
            if ((gain_in - target_gain) > FALL_STEP)
                gain_next = gain_in - FALL_STEP;
            else
                gain_next = target_gain;
        end else if (target_gain > gain_in) begin
            if ((target_gain - gain_in) > RISE_STEP)
                gain_next = gain_in + RISE_STEP;
            else
                gain_next = target_gain;
        end
    end
endmodule
