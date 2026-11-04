// Initialization writes samples in ascending order. Pack adjacent samples
// into one 64-bit word, halving native RAM use (one SDP36KE per voice).
// The last even sample is flushed with an unused zero upper half. Reads do
// not begin until initialization is complete. Runtime reads stay one cycle.
module poly32_scratch_bank (
    output wire secco,decco,
    output wire [23:0] dout,
    output wire [7:0] dop,eccp,
    input wire clka,clkb,cea,ceb,oce,reset,
    input wire [4:0] bank,
    input wire [9:0] ada,adb,last_address,
    input wire [23:0] din
);
    reg [23:0] even_sample[0:31];
    wire [13:0] base_row={9'd0,bank}*14'd300;
    wire [13:0] write_row=base_row+{5'd0,ada[9:1]};
    wire [13:0] read_row=base_row+{5'd0,adb[9:1]};
    reg [18:0] read_select;
    reg read_odd;
    wire [63:0] bank_data[0:18];
    wire [63:0] write_data = ada[0]
        ? {16'd0,din,even_sample[bank]} : {40'd0,din};
    wire flush = cea && (ada[0] || ada==last_address);
    always @(posedge clka) if(cea && !ada[0]) even_sample[bank]<=din;
    always @(posedge clkb) if(ceb) begin read_select<=19'b1<<read_row[13:9]; read_odd<=adb[0]; end
    genvar sample_bit,group_index;
    generate for(sample_bit=0;sample_bit<24;sample_bit=sample_bit+1)begin:g_output
        wire [18:0] terms;
        for(group_index=0;group_index<19;group_index=group_index+1)begin:g_term
            assign terms[group_index]=read_select[group_index]&&
                (read_odd?bank_data[group_index][sample_bit+24]:bank_data[group_index][sample_bit]);
        end
        assign dout[sample_bit]=|terms;
    end endgenerate
    assign secco=0; assign decco=0; assign dop=0; assign eccp=0;
    genvar g;
    generate for(g=0;g<19;g=g+1) begin:g_bank
        SDP36KE ram (
            .DO(bank_data[g]), .DOP(), .SECCO(), .DECCO(), .ECCP(),
            .CLKA(clka), .CLKB(clkb), .CEA(flush && write_row[13:9]==g),
            .CEB(ceb && read_row[13:9]==g), .OCE(oce), .RESET(reset),
            .ADA(write_row[8:0]), .ADB(read_row[8:0]), .DI(write_data), .DIP(8'd0),
            .BLKSELA(3'd0), .BLKSELB(3'd0), .SECCI(1'b0), .DECCI(1'b0)
        );
        defparam ram.ECC_WRITE_EN="TRUE";
        defparam ram.ECC_READ_EN="FALSE";
        defparam ram.READ_MODE=1'b0;
        defparam ram.BLK_SEL_A=3'b000;
        defparam ram.BLK_SEL_B=3'b000;
        defparam ram.RESET_MODE="SYNC";
        defparam ram.INIT_FILE="NONE";
    end endgenerate
endmodule
