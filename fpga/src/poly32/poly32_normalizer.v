// Timbre-independent normalization of a signed 32-voice sum.
// 29 bits hold 32 full-scale signed 24-bit voices without wrap.
// 1/sqrt(N) normalization uses the phrase high-water voice count; disappearing
// tails never raise the normalization gain. A peak-envelope ceiling reserves
// 12 dB for the existing body filter. Division is serial (40 clocks/frame).
module poly32_normalizer #(
    parameter [23:0] CEILING = 24'd2097151
)(
    input wire clk, rst_n, input_valid,
    input wire signed [28:0] sum_in,
    input wire [5:0] voice_count,
    output reg output_valid,
    output reg signed [23:0] sample_out,
    output reg busy,
    output reg limited
);
    reg [5:0] high_count, step;
    reg [16:0] norm_gain, gain_work;
    reg [28:0] peak, divisor;
    reg [39:0] dividend, quotient;
    reg [29:0] remainder;
    reg signed [28:0] held_sum;
    reg signed [46:0] product;
    wire [28:0] abs_sum = sum_in[28] ? -sum_in : sum_in;
    wire [28:0] decay = (peak >> 12) ? (peak >> 12) : 29'd1;
    wire [28:0] decayed = peak > decay ? peak - decay : 29'd0;
    wire [28:0] next_peak = abs_sum > decayed ? abs_sum : decayed;
    wire [5:0] next_count = voice_count > high_count ? voice_count : high_count;
    wire [16:0] target_gain = norm_lut(next_count);
    wire [16:0] smooth_gain = norm_gain > target_gain + 17'd256
        ? norm_gain - 17'd256 : target_gain;
    wire [29:0] trial = {remainder[28:0], dividend[39]};
    wire hit = trial >= {1'b0, divisor};
    wire [39:0] next_quotient = {quotient[38:0], hit};

    function [16:0] norm_lut;
        input [5:0] n;
        begin
            case(n)
                6'd1: norm_lut=17'd65536;
                6'd2: norm_lut=17'd46340;
                6'd3: norm_lut=17'd37837;
                6'd4: norm_lut=17'd32768;
                6'd5: norm_lut=17'd29308;
                6'd6: norm_lut=17'd26754;
                6'd7: norm_lut=17'd24770;
                6'd8: norm_lut=17'd23170;
                6'd9: norm_lut=17'd21845;
                6'd10: norm_lut=17'd20724;
                6'd11: norm_lut=17'd19759;
                6'd12: norm_lut=17'd18918;
                6'd13: norm_lut=17'd18176;
                6'd14: norm_lut=17'd17515;
                6'd15: norm_lut=17'd16921;
                6'd16: norm_lut=17'd16384;
                6'd17: norm_lut=17'd15894;
                6'd18: norm_lut=17'd15446;
                6'd19: norm_lut=17'd15034;
                6'd20: norm_lut=17'd14654;
                6'd21: norm_lut=17'd14301;
                6'd22: norm_lut=17'd13972;
                6'd23: norm_lut=17'd13665;
                6'd24: norm_lut=17'd13377;
                6'd25: norm_lut=17'd13107;
                6'd26: norm_lut=17'd12852;
                6'd27: norm_lut=17'd12612;
                6'd28: norm_lut=17'd12385;
                6'd29: norm_lut=17'd12169;
                6'd30: norm_lut=17'd11965;
                6'd31: norm_lut=17'd11770;
                6'd32: norm_lut=17'd11585;
                default: norm_lut=17'd65536;
            endcase
        end
    endfunction

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            high_count<=0; norm_gain<=65536; gain_work<=65536;
            peak<=0; divisor<=1; step<=0; dividend<=0; quotient<=0;
            remainder<=0; held_sum<=0; product<=0;
            output_valid<=0; sample_out<=0; busy<=0; limited<=0;
        end else begin
            output_valid<=0;
            if (input_valid && !busy) begin
                held_sum<=sum_in;
                high_count<=next_count;
                norm_gain<=smooth_gain;
                gain_work<=smooth_gain;
                peak<=next_peak;
                divisor<=next_peak == 0 ? 29'd1 : next_peak;
                dividend<={CEILING,16'd0};
                quotient<=0; remainder<=0; step<=0; busy<=1;
                if (voice_count==0 && sum_in==0) begin
                    high_count<=0; norm_gain<=65536; gain_work<=65536; peak<=0;
                end
            end else if (busy) begin
                if (step<40) begin
                    dividend<=dividend<<1;
                    remainder<=hit ? trial-{1'b0,divisor} : trial;
                    quotient<=next_quotient;
                    step<=step+1'b1;
                end else if (step==40) begin
                    // Clamp the ratio to unity before narrowing the quotient.
                    if (quotient < gain_work) begin
                        gain_work<=quotient[16:0];
                        limited<=1;
                    end else limited<=0;
                    step<=41;
                end else if (step==41) begin
                    product <= held_sum * $signed({1'b0,gain_work});
                    step<=42;
                end else begin
                    sample_out <= product >>> 16;
                    output_valid<=1; busy<=0;
                end
            end
        end
    end
endmodule
