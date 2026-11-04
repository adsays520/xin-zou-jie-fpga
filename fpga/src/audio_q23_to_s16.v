// Convert signed 24-bit PCM to signed 16-bit PCM without a negative DC bias.
// The discarded eight bits are rounded to nearest; exact ties go to even.
module audio_q23_to_s16 (
    input  wire signed [23:0] sample_q23,
    output reg  signed [15:0] sample_s16
);
    reg [23:0] magnitude;
    reg [16:0] rounded_magnitude;
    reg signed [17:0] signed_result;

    always @* begin
        magnitude = sample_q23[23] ? (~sample_q23 + 1'b1) : sample_q23;
        rounded_magnitude = magnitude >> 8;

        if ((magnitude[7:0] > 8'h80) ||
            ((magnitude[7:0] == 8'h80) && rounded_magnitude[0]))
            rounded_magnitude = rounded_magnitude + 1'b1;

        signed_result = sample_q23[23]
            ? -$signed({1'b0, rounded_magnitude})
            :  $signed({1'b0, rounded_magnitude});

        if (signed_result > 18'sd32767)
            sample_s16 = 16'sh7fff;
        else if (signed_result < -18'sd32768)
            sample_s16 = 16'sh8000;
        else
            sample_s16 = signed_result[15:0];
    end
endmodule
