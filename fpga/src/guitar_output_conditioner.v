// Shared post-body anti-ringing conditioner.
//
// A one-pole low-pass y += (x-y)/4 suppresses sample-wide corners and the high
// harmonics they excite.  It is outside the string feedback loop, so delay,
// fractional tuning, damping and therefore pitch are unchanged.  Tiny deltas
// snap exactly to the input to avoid a fixed-point tail limit cycle.
module guitar_output_conditioner (
    input  wire                      clk,
    input  wire                      rst_n,
    input  wire                      sample_valid,
    input  wire signed [23:0]        sample_in,
    output reg                       output_valid,
    output reg signed [23:0]         sample_out
);
    wire signed [24:0] state_extended = {sample_out[23], sample_out};
    wire signed [24:0] input_extended = {sample_in[23], sample_in};
    wire signed [24:0] delta = input_extended - state_extended;
    wire signed [24:0] biased_delta = delta[24]
        ? delta + 25'sd3 : delta;
    wire signed [24:0] step = biased_delta >>> 2;
    wire signed [24:0] next_sample = state_extended + step;
    wire tiny_delta = (delta < 25'sd4) && (delta > -25'sd4);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            output_valid <= 1'b0;
            sample_out <= 24'sd0;
        end else begin
            output_valid <= 1'b0;
            if (sample_valid) begin
                sample_out <= tiny_delta ? sample_in : next_sample[23:0];
                output_valid <= 1'b1;
            end
        end
    end
endmodule
