// Tang Mega 138K Pro audio output, single 50 MHz clock domain.
// The word/WS alignment is cycle-equivalent to the vendor audio_sinewave
// example. Unlike that example, BCK is not used as an internal clock, so the
// generated BCK never traverses ordinary routing as a data-path clock.
module audio_drive_v12_reference(
    input wire clk,
    input wire rst_n,
    input wire [15:0] idata_left,
    input wire [15:0] idata_right,
    output wire req,
    output wire sample_tick,
    output wire HP_BCK,
    output wire HP_WS,
    output wire HP_DIN
);
    // BCK = 1.536 MHz: 48 kHz x 16 bits x 2 channels.
    localparam [31:0] PHASE_STEP = 32'd263882791;
    reg [31:0] phase;
    reg bck_toggle_lookahead;
    reg HP_BCK_r, HP_WS_r, HP_DIN_r;
    reg [4:0] b_cnt;
    reg req_r, req_r1;
    reg [15:0] idata_r;
    wire [32:0] phase_next = {1'b0,phase} + {1'b0,PHASE_STEP};
    // Predict the carry for the next phase value one cycle ahead. The two
    // constant comparisons run in parallel, removing the 32-bit carry chain
    // from the high-fanout audio sample enable without shifting any I2S edge.
    wire bck_toggle = bck_toggle_lookahead;
    // Values here are evaluated before the nonblocking BCK update.
    wire bck_rise = bck_toggle && !HP_BCK_r;

    assign HP_BCK = HP_BCK_r;
    assign HP_WS = HP_WS_r;
    assign HP_DIN = HP_DIN_r;
    assign req = req_r;
    // Once each complete left/right frame: 1.536 MHz / 32 = 48 kHz.
    assign sample_tick = bck_rise && (b_cnt == 5'd31);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            phase <= 32'd0;
            bck_toggle_lookahead <= 1'b0;
            HP_BCK_r <= 1'b0;
            HP_WS_r <= 1'b0;
            HP_DIN_r <= 1'b0;
            b_cnt <= 5'd0;
            req_r <= 1'b0;
            req_r1 <= 1'b0;
            idata_r <= 16'd0;
        end else begin
            phase <= phase_next[31:0];
            bck_toggle_lookahead <= (phase >= 32'd3767201714) && (phase < 32'd4031084505);
            if (bck_toggle)
                HP_BCK_r <= ~HP_BCK_r;

            // Exact state-update order of the vendor serializer on posedge
            // BCK, expressed as a one-clock enable in the 50 MHz domain.
            if (bck_rise) begin
                b_cnt <= b_cnt + 1'b1;
                req_r <= (b_cnt == 5'd0) || (b_cnt == 5'd16);
                req_r1 <= req_r;
                idata_r <= req_r1
                    ? ((b_cnt < 5'd16) ? idata_left : idata_right)
                    : (idata_r << 1);
                HP_DIN_r <= idata_r[15];
                if (b_cnt == 5'd3)
                    HP_WS_r <= 1'b0;
                else if (b_cnt == 5'd19)
                    HP_WS_r <= 1'b1;
            end
        end
    end
endmodule
