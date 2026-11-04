// Eight groups of four voices. Each voice packs two adjacent 24-bit delay
// samples into one 64-bit SDP36KE word, so four voices consume four RAMs per
// group instead of eight generated 1024 x 24 RAMs.
//
// Initialization arrives in ascending address order and is pair-packed. In
// playback, the B-port word already read for the current sample supplies the
// untouched half of the A-port write (read/modify/write without another RAM).
module poly32_road_bank (
    output wire secco, decco,
    output wire [23:0] dout,
    output wire [7:0] dop, eccp,
    input wire clka, clkb, cea, ceb, oce, reset,
    input wire [4:0] bank,
    input wire [9:0] ada, adb, last_address,
    input wire init_pack,
    input wire [23:0] din
);
    reg [23:0] even_sample [0:31];
    reg [4:0] read_bank;
    reg read_odd;
    wire [63:0] bank_data [0:31];
    wire [63:0] selected_word = bank_data[read_bank];

    wire init_flush = ada[0] || ada == last_address;
    wire write_enable = cea && (!init_pack || init_flush);
    wire [63:0] init_write_data = ada[0]
        ? {16'd0,din,even_sample[bank]} : {40'd0,din};
    always @(posedge clka)
        if (cea && init_pack && !ada[0]) even_sample[bank] <= din;
    always @(posedge clkb)
        if (ceb) begin
            read_bank <= bank;
            read_odd <= adb[0];
        end

    assign dout = read_odd ? selected_word[47:24] : selected_word[23:0];
    assign secco = 1'b0;
    assign decco = 1'b0;
    assign dop = 8'd0;
    assign eccp = 8'd0;

    genvar group_index;
    genvar voice_index;
    generate for (group_index=0; group_index<8; group_index=group_index+1) begin : g_group
        for (voice_index=0; voice_index<4; voice_index=voice_index+1) begin : g_voice
            localparam integer RAM_INDEX = group_index*4 + voice_index;
            // Keep the playback read/modify/write path local to this RAM.
            // Using the globally selected word here creates a 32-to-1
            // RAM-output crossbar feeding every RAM input and destroys Fmax.
            wire [63:0] local_loop_write_data = ada[0]
                ? {16'd0,din,bank_data[RAM_INDEX][23:0]}
                : {16'd0,bank_data[RAM_INDEX][47:24],din};
            wire [63:0] local_write_data = init_pack
                ? init_write_data : local_loop_write_data;
            SDP36KE ram (
                .DO(bank_data[RAM_INDEX]), .DOP(),
                .SECCO(), .DECCO(), .ECCP(),
                .CLKA(clka), .CLKB(clkb),
                .CEA(write_enable && bank == RAM_INDEX),
                .CEB(ceb && bank == RAM_INDEX),
                .OCE(oce), .RESET(reset),
                .ADA(ada[9:1]), .ADB(adb[9:1]),
                .DI(local_write_data), .DIP(8'd0),
                .BLKSELA(3'd0), .BLKSELB(3'd0),
                .SECCI(1'b0), .DECCI(1'b0)
            );
            defparam ram.ECC_WRITE_EN="TRUE";
            defparam ram.ECC_READ_EN="FALSE";
            defparam ram.READ_MODE=1'b0;
            defparam ram.BLK_SEL_A=3'b000;
            defparam ram.BLK_SEL_B=3'b000;
            defparam ram.RESET_MODE="SYNC";
            defparam ram.INIT_FILE="NONE";
        end
    end endgenerate
endmodule
