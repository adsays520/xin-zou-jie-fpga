// Peak-aware 32-voice output bus.
//
// The 29-bit input preserves the exact sum of 32 signed 24-bit voices.  Unlike
// voice-count normalization, an in-range sample is passed at exact unity and
// allocated/quiet voices do not lower the level.  Gain is reduced only when
// the real summed waveform needs headroom, then released smoothly.
module poly32_bus_manager #(
    // The following body filter has a measured worst-case response of
    // +1.173 dB.  7,000,000 leaves about 0.4 dB at its 205 Hz peak.
    parameter [23:0] CEILING = 24'd7000000,
    parameter [16:0] RELEASE_SLOW = 17'd8,
    parameter [16:0] RELEASE_FAST = 17'd512
)(
    input  wire                    clk,
    input  wire                    rst_n,
    input  wire                    input_valid,
    input  wire signed [28:0]      sum_in,
    output reg                     output_valid,
    output reg signed [23:0]       sample_out,
    output reg                     busy,
    output reg                     limited
);
    reg [5:0] step;
    reg [16:0] bus_gain;
    reg [16:0] gain_work;
    reg [28:0] held_abs;
    reg [28:0] divisor;
    reg [39:0] dividend;
    reg [39:0] quotient;
    reg [29:0] remainder;
    reg signed [28:0] held_sum;
    reg signed [46:0] product;

    wire [28:0] abs_sum = sum_in[28] ? -sum_in : sum_in;
    wire [29:0] trial = {remainder[28:0], dividend[39]};
    wire divide_hit = trial >= {1'b0, divisor};
    wire [39:0] next_quotient = {quotient[38:0], divide_hit};
    wire [16:0] ratio_gain = quotient >= 40'd65536
        ? 17'd65536 : quotient[16:0];
    wire [16:0] desired_gain = held_abs > CEILING
        ? ratio_gain : 17'd65536;
    wire [16:0] release_step = held_abs < (CEILING >> 1)
        ? RELEASE_FAST : RELEASE_SLOW;
    wire [17:0] recovered_wide = {1'b0, bus_gain} + release_step;
    wire [16:0] recovered_gain = recovered_wide >= {1'b0, desired_gain}
        ? desired_gain : recovered_wide[16:0];
    wire [16:0] next_gain = desired_gain < bus_gain
        ? desired_gain : recovered_gain;
    wire signed [30:0] scaled_sample = product >>> 16;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            step <= 0;
            bus_gain <= 17'd65536;
            gain_work <= 17'd65536;
            held_abs <= 0;
            divisor <= 1;
            dividend <= 0;
            quotient <= 0;
            remainder <= 0;
            held_sum <= 0;
            product <= 0;
            output_valid <= 0;
            sample_out <= 0;
            busy <= 0;
            limited <= 0;
        end else begin
            output_valid <= 0;
            if (input_valid && !busy) begin
                held_sum <= sum_in;
                held_abs <= abs_sum;
                divisor <= abs_sum == 0 ? 29'd1 : abs_sum;
                dividend <= {CEILING, 16'd0};
                quotient <= 0;
                remainder <= 0;
                step <= 0;
                busy <= 1;
            end else if (busy) begin
                if (step < 40) begin
                    dividend <= dividend << 1;
                    remainder <= divide_hit
                        ? trial - {1'b0, divisor} : trial;
                    quotient <= next_quotient;
                    step <= step + 1'b1;
                end else if (step == 40) begin
                    gain_work <= next_gain;
                    bus_gain <= next_gain;
                    limited <= next_gain != 17'd65536;
                    step <= 41;
                end else if (step == 41) begin
                    product <= held_sum * $signed({1'b0, gain_work});
                    step <= 42;
                end else begin
                    sample_out <= scaled_sample[23:0];
                    output_valid <= 1;
                    busy <= 0;
                end
            end
        end
    end
endmodule
