// Five parallel acoustic-guitar body modes, shared by all six strings.
//
// Each mode is an iirpeak biquad at 48 kHz. The five filters share the same
// input history, and their products are scheduled over a handful of 50 MHz
// clocks between audio samples. Biquad coefficients use signed Q2.22 because
// -a1 approaches +2; dry/mix gains use signed Q1.23.
module guitar_body_filter #(
    parameter integer SAMPLE_W = 24
)(
    input  wire                         clk,
    input  wire                         rst_n,
    input  wire                         sample_valid,
    input  wire signed [SAMPLE_W-1:0]   sample_in,
    output reg                          output_valid,
    output reg signed [SAMPLE_W-1:0]    sample_out
);
    localparam [1:0] ST_IDLE   = 2'd0;
    localparam [1:0] ST_CALC   = 2'd1;
    localparam [1:0] ST_MIX    = 2'd2;
    localparam [1:0] ST_OUTPUT = 2'd3;
    localparam signed [23:0] DRY_GAIN_Q23 = 24'sd7381975; // 0.88

    reg [1:0] state;
    reg [2:0] mode_index;
    reg signed [23:0] x_reg;
    reg signed [23:0] x_z1;
    reg signed [23:0] x_z2;
    reg signed [23:0] y_z1 [0:4];
    reg signed [23:0] y_z2 [0:4];
    reg signed [50:0] modal_accumulator;
    reg signed [47:0] mode_mix_product;
    reg signed [51:0] mix_accumulator;
    integer reset_index;

    wire signed [24:0] input_difference =
        $signed({x_reg[23], x_reg}) - $signed({x_z2[23], x_z2});
    wire signed [48:0] numerator_product =
        $signed(input_difference) * $signed(mode_b0_q22(mode_index));
    wire signed [47:0] feedback_1_product =
        $signed(y_z1[mode_index]) * $signed(mode_neg_a1_q22(mode_index));
    wire signed [47:0] feedback_2_product =
        $signed(y_z2[mode_index]) * $signed(mode_neg_a2_q22(mode_index));
    wire signed [50:0] modal_sum =
        {{2{numerator_product[48]}}, numerator_product}
      + {{3{feedback_1_product[47]}}, feedback_1_product}
      + {{3{feedback_2_product[47]}}, feedback_2_product};
    // Arithmetic shifts round negative values downward. Biasing only a
    // negative accumulator makes fixed-point decay symmetric about zero.
    wire signed [50:0] modal_rounded = modal_accumulator[50]
        ? modal_accumulator + 51'sd4194303 : modal_accumulator;
    wire signed [23:0] modal_sample = sat24(modal_rounded >>> 22);
    wire signed [47:0] dry_product =
        $signed(sample_in) * $signed(DRY_GAIN_Q23);
    // Keep the final addition signed before the Q23 arithmetic shift.  A bare
    // concatenation is unsigned in Verilog; mixing it directly into this
    // expression turns negative samples into a large positive value and drives
    // the output saturator to +full-scale.
    wire signed [51:0] final_mix = mix_accumulator
        + $signed({{4{mode_mix_product[47]}}, mode_mix_product});

    function signed [23:0] mode_b0_q22;
        input [2:0] index;
        begin
            case (index)
                3'd0: mode_b0_q22 = 24'sd4114;  // 105 Hz, Q=7
                3'd1: mode_b0_q22 = 24'sd6244;  // 205 Hz, Q=9
                3'd2: mode_b0_q22 = 24'sd8629;  // 315 Hz, Q=10
                3'd3: mode_b0_q22 = 24'sd23544; // 690 Hz, Q=8
                default: mode_b0_q22 = 24'sd49606; // 1280 Hz, Q=7
            endcase
        end
    endfunction

    function signed [23:0] mode_neg_a1_q22;
        input [2:0] index;
        begin
            case (index)
                3'd0: mode_neg_a1_q22 = 24'sd8379589;
                3'd1: mode_neg_a1_q22 = 24'sd8373105;
                3'd2: mode_neg_a1_q22 = 24'sd8364234;
                3'd3: mode_neg_a1_q22 = 24'sd8307518;
                default: mode_neg_a1_q22 = 24'sd8173312;
            endcase
        end
    endfunction

    function signed [23:0] mode_neg_a2_q22;
        input [2:0] index;
        begin
            case (index)
                3'd0: mode_neg_a2_q22 = -24'sd4186077;
                3'd1: mode_neg_a2_q22 = -24'sd4181817;
                3'd2: mode_neg_a2_q22 = -24'sd4177045;
                3'd3: mode_neg_a2_q22 = -24'sd4147215;
                default: mode_neg_a2_q22 = -24'sd4095092;
            endcase
        end
    endfunction

    function signed [23:0] mode_mix_q23;
        input [2:0] index;
        begin
            case (index)
                3'd0: mode_mix_q23 = 24'sd1845494; // 0.220
                3'd1: mode_mix_q23 = 24'sd2181038; // 0.260
                3'd2: mode_mix_q23 = 24'sd1509949; // 0.180
                3'd3: mode_mix_q23 = 24'sd461373;  // 0.055
                default: mode_mix_q23 = 24'sd209715; // 0.025
            endcase
        end
    endfunction

    function signed [23:0] sat24;
        input signed [51:0] value;
        begin
            if (value > 52'sd8388607)
                sat24 = 24'sh7fffff;
            else if (value < -52'sd8388608)
                sat24 = 24'sh800000;
            else
                sat24 = value[23:0];
        end
    endfunction

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= ST_IDLE;
            mode_index <= 3'd0;
            x_reg <= 24'sd0;
            x_z1 <= 24'sd0;
            x_z2 <= 24'sd0;
            modal_accumulator <= 51'sd0;
            mode_mix_product <= 48'sd0;
            mix_accumulator <= 52'sd0;
            output_valid <= 1'b0;
            sample_out <= 24'sd0;
            for (reset_index = 0; reset_index < 5; reset_index = reset_index + 1) begin
                y_z1[reset_index] <= 24'sd0;
                y_z2[reset_index] <= 24'sd0;
            end
        end else begin
            output_valid <= 1'b0;
            case (state)
                ST_IDLE: begin
                    if (sample_valid) begin
                        x_reg <= sample_in;
                        mode_index <= 3'd0;
                        mix_accumulator <=
                            {{4{dry_product[47]}}, dry_product};
                        state <= ST_CALC;
                    end
                end

                ST_CALC: begin
                    modal_accumulator <= modal_sum;
                    state <= ST_MIX;
                end

                ST_MIX: begin
                    y_z2[mode_index] <= y_z1[mode_index];
                    y_z1[mode_index] <= modal_sample;
                    mode_mix_product <=
                        $signed(modal_sample) * $signed(mode_mix_q23(mode_index));
                    // Accumulate the preceding mode's registered product. The
                    // fifth mode is handled once more in ST_OUTPUT.
                    if (mode_index == 3'd0) begin
                        mode_index <= 3'd1;
                        state <= ST_CALC;
                    end else begin
                        mix_accumulator <= mix_accumulator
                            + {{4{mode_mix_product[47]}}, mode_mix_product};
                        if (mode_index == 3'd4)
                            state <= ST_OUTPUT;
                        else begin
                            mode_index <= mode_index + 1'b1;
                            state <= ST_CALC;
                        end
                    end
                end

                ST_OUTPUT: begin
                    // mode_mix_product now contains mode 4; modes 0..3 have
                    // already been accumulated by their following pass.
                    sample_out <= sat24(final_mix >>> 23);
                    output_valid <= 1'b1;
                    x_z2 <= x_z1;
                    x_z1 <= x_reg;
                    state <= ST_IDLE;
                end

                default: state <= ST_IDLE;
            endcase
        end
    end
endmodule
