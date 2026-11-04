// Per-string low-shelf EQ for the lower four strings.
//
// Unlike a delayed one-pole signal added in parallel, this biquad has a
// monotonic magnitude response and approaches exactly 0 dB at high frequency.
// Coefficients are signed Q2.22 at 48 kHz. E4/B3 use the identity response.
module guitar_low_shelf #(
    parameter integer SAMPLE_W = 24
)(
    input  wire                         clk,
    input  wire                         rst_n,
    input  wire                         sample_valid,
    input  wire signed [SAMPLE_W-1:0]   sample_in,
    input  wire [2:0]                   string_sel,
    output reg                          output_valid,
    output reg signed [SAMPLE_W-1:0]    sample_out
);
    localparam [1:0] ST_IDLE   = 2'd0;
    localparam [1:0] ST_CALC   = 2'd1;
    localparam [1:0] ST_OUTPUT = 2'd2;

    reg [1:0] state;
    reg [2:0] coefficient_sel;
    reg [2:0] previous_string_sel;
    reg signed [23:0] x_reg;
    reg signed [23:0] x_z1;
    reg signed [23:0] x_z2;
    reg signed [23:0] y_z1;
    reg signed [23:0] y_z2;
    reg signed [50:0] accumulator;

    wire signed [47:0] b0_product =
        $signed(x_reg) * $signed(coeff_b0(coefficient_sel));
    wire signed [47:0] b1_product =
        $signed(x_z1) * $signed(coeff_b1(coefficient_sel));
    wire signed [47:0] b2_product =
        $signed(x_z2) * $signed(coeff_b2(coefficient_sel));
    wire signed [47:0] a1_product =
        $signed(y_z1) * $signed(coeff_neg_a1(coefficient_sel));
    wire signed [47:0] a2_product =
        $signed(y_z2) * $signed(coeff_neg_a2(coefficient_sel));
    wire signed [50:0] filter_sum =
        {{3{b0_product[47]}}, b0_product}
      + {{3{b1_product[47]}}, b1_product}
      + {{3{b2_product[47]}}, b2_product}
      + {{3{a1_product[47]}}, a1_product}
      + {{3{a2_product[47]}}, a2_product};
    wire signed [50:0] rounded_accumulator = accumulator[50]
        ? accumulator + 51'sd4194303 : accumulator;
    wire signed [23:0] filtered_sample = sat24(rounded_accumulator >>> 22);

    function signed [23:0] coeff_b0;
        input [2:0] index;
        begin
            case (index)
                3'd2: coeff_b0 = 24'sd4234791; // G3: +4.0 dB, 450 Hz
                3'd3: coeff_b0 = 24'sd4246439; // D3: +5.5 dB, 420 Hz
                3'd4: coeff_b0 = 24'sd4254556; // A2: +7.0 dB, 380 Hz
                3'd5: coeff_b0 = 24'sd4264004; // E2: +9.0 dB, 340 Hz
                default: coeff_b0 = 24'sd4194304; // identity
            endcase
        end
    endfunction

    function signed [23:0] coeff_b1;
        input [2:0] index;
        begin
            case (index)
                3'd2: coeff_b1 = -24'sd8074060;
                3'd3: coeff_b1 = -24'sd8106372;
                3'd4: coeff_b1 = -24'sd8143268;
                3'd5: coeff_b1 = -24'sd8180493;
                default: coeff_b1 = 24'sd0;
            endcase
        end
    endfunction

    function signed [23:0] coeff_b2;
        input [2:0] index;
        begin
            case (index)
                3'd2: coeff_b2 = 24'sd3856933;
                3'd3: coeff_b2 = 24'sd3876773;
                3'd4: coeff_b2 = 24'sd3903806;
                3'd5: coeff_b2 = 24'sd3930105;
                default: coeff_b2 = 24'sd0;
            endcase
        end
    endfunction

    function signed [23:0] coeff_neg_a1;
        input [2:0] index;
        begin
            case (index)
                3'd2: coeff_neg_a1 = 24'sd8077320;
                3'd3: coeff_neg_a1 = 24'sd8110322;
                3'd4: coeff_neg_a1 = 24'sd8147444;
                3'd5: coeff_neg_a1 = 24'sd8184885;
                default: coeff_neg_a1 = 24'sd0;
            endcase
        end
    endfunction

    function signed [23:0] coeff_neg_a2;
        input [2:0] index;
        begin
            case (index)
                3'd2: coeff_neg_a2 = -24'sd3894161;
                3'd3: coeff_neg_a2 = -24'sd3924958;
                3'd4: coeff_neg_a2 = -24'sd3959882;
                3'd5: coeff_neg_a2 = -24'sd3995413;
                default: coeff_neg_a2 = 24'sd0;
            endcase
        end
    endfunction

    function signed [23:0] sat24;
        input signed [50:0] value;
        begin
            if (value > 51'sd8388607)
                sat24 = 24'sh7fffff;
            else if (value < -51'sd8388608)
                sat24 = 24'sh800000;
            else
                sat24 = value[23:0];
        end
    endfunction

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= ST_IDLE;
            coefficient_sel <= 3'd0;
            previous_string_sel <= 3'd0;
            x_reg <= 24'sd0;
            x_z1 <= 24'sd0;
            x_z2 <= 24'sd0;
            y_z1 <= 24'sd0;
            y_z2 <= 24'sd0;
            accumulator <= 51'sd0;
            output_valid <= 1'b0;
            sample_out <= 24'sd0;
        end else begin
            output_valid <= 1'b0;
            case (state)
                ST_IDLE: begin
                    if (sample_valid) begin
                        x_reg <= sample_in;
                        coefficient_sel <= string_sel;
                        if (string_sel != previous_string_sel) begin
                            x_z1 <= 24'sd0;
                            x_z2 <= 24'sd0;
                            y_z1 <= 24'sd0;
                            y_z2 <= 24'sd0;
                            previous_string_sel <= string_sel;
                        end
                        state <= ST_CALC;
                    end
                end

                ST_CALC: begin
                    accumulator <= filter_sum;
                    state <= ST_OUTPUT;
                end

                ST_OUTPUT: begin
                    sample_out <= filtered_sample;
                    output_valid <= 1'b1;
                    x_z2 <= x_z1;
                    x_z1 <= x_reg;
                    y_z2 <= y_z1;
                    y_z1 <= filtered_sample;
                    state <= ST_IDLE;
                end

                default: state <= ST_IDLE;
            endcase
        end
    end
endmodule
