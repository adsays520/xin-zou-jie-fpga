// R7 excitation transport only. Payload crosses a genuine dual-clock RAM,
// not a wide asynchronous mailbox. Gray pointers require the R7 SDC bounds.
module excitation_async_fifo64(
    input wire wclk,wrst_n,wvalid,output wire wready,input wire [63:0] wdata,
    input wire rclk,rrst_n,output reg rvalid,input wire rready,output reg [63:0] rdata
);
    localparam AW=3;
    reg [AW:0] wbin,wgray,rbin,rgray;
    (* syn_preserve=1,async_reg="true" *) reg [AW:0] rgray_meta,rgray_sync;
    (* syn_preserve=1,async_reg="true" *) reg [AW:0] wgray_meta,wgray_sync;
    wire [AW:0] wnext=wbin+1'b1;
    wire [AW:0] wgray_next=(wnext>>1)^wnext;
    reg full;
    wire empty=rgray==wgray_sync;
    reg fetching;
    wire fetch=!fetching&&(!rvalid||rready)&&!empty;
    wire [63:0] ram_data;
    assign wready=wrst_n&&!full;
    SDP36KE ram(
        .DO(ram_data),.DOP(),.SECCO(),.DECCO(),.ECCP(),
        .CLKA(wclk),.CLKB(rclk),.CEA(wvalid&&wready),.CEB(fetch),
        .OCE(1'b1),.RESET(!rrst_n),
        .ADA({6'd0,wbin[AW-1:0]}),.ADB({6'd0,rbin[AW-1:0]}),
        .DI(wdata),.DIP(8'd0),.BLKSELA(3'd0),.BLKSELB(3'd0),
        .SECCI(1'b0),.DECCI(1'b0));
    defparam ram.ECC_WRITE_EN="TRUE",ram.ECC_READ_EN="FALSE";
    defparam ram.READ_MODE=1'b0,ram.BLK_SEL_A=3'b000,ram.BLK_SEL_B=3'b000;
    defparam ram.RESET_MODE="SYNC",ram.INIT_FILE="NONE";
    always @(posedge wclk or negedge wrst_n)begin
        if(!wrst_n)begin wbin<=0;wgray<=0;full<=0;rgray_meta<=0;rgray_sync<=0;end
        else begin
            rgray_meta<=rgray;rgray_sync<=rgray_meta;
            if(wvalid&&wready)begin wbin<=wnext;wgray<=wgray_next;end
            full<=(wvalid&&wready ? wgray_next : wgray)==
                {~rgray_sync[AW:AW-1],rgray_sync[AW-2:0]};
        end
    end
    always @(posedge rclk or negedge rrst_n)begin
        if(!rrst_n)begin
            rbin<=0;rgray<=0;wgray_meta<=0;wgray_sync<=0;
            fetching<=0;rvalid<=0;rdata<=0;
        end else begin
            wgray_meta<=wgray;wgray_sync<=wgray_meta;
            if(rvalid&&rready)rvalid<=0;
            fetching<=fetch;
            if(fetching)begin rdata<=ram_data;rvalid<=1;end
            // Do not release the RAM location until it has reached rdata.
            if(fetching)begin rbin<=rbin+1'b1;rgray<=((rbin+1'b1)>>1)^(rbin+1'b1);end
        end
    end
endmodule
