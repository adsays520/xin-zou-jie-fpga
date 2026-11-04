module poly32_road_bank (
    output wire secco,decco,
    output wire [23:0] dout,
    output wire [7:0] dop,eccp,
    input wire clka,clkb,cea,ceb,oce,reset,
    input wire [4:0] bank,
    input wire [9:0] ada,adb,last_address,
    input wire init_pack,
    input wire [23:0] din
);
    wire [19:0] write_scaled=ada*10'd683;
    wire [19:0] read_scaled=adb*10'd683;
    wire [9:0] write_row={1'b0,write_scaled[19:11]};
    wire [9:0] read_row={1'b0,read_scaled[19:11]};
    wire [1:0] write_slot=ada-(write_row*10'd3);
    wire [1:0] read_slot=adb-(read_row*10'd3);
    wire [12:0] base_row={8'd0,bank}*13'd200;
    wire [12:0] write_global=base_row+{3'd0,write_row};
    wire [12:0] read_global=base_row+{3'd0,read_row};
    wire [71:0] bank_data[0:6];
    reg [2:0] returned_group;
    reg [1:0] returned_slot;
    reg [23:0] first_sample[0:31],second_sample[0:31];
    wire [71:0] selected_word=bank_data[returned_group];
    wire [71:0] initialization_word=write_slot==0 ? {48'd0,din} :
        write_slot==1 ? {24'd0,din,first_sample[bank]} :
        {din,second_sample[bank],first_sample[bank]};
    assign dout=returned_slot==0 ? selected_word[23:0] :
        returned_slot==1 ? selected_word[47:24] : selected_word[71:48];
    assign secco=0;
    assign decco=0;
    assign dop=0;
    assign eccp=0;
    always @(posedge clkb)if(ceb)begin
        returned_group<=read_global[12:10];returned_slot<=read_slot;
    end
    always @(posedge clka)if(cea&&init_pack)begin
        if(write_slot==0)first_sample[bank]<=din;
        if(write_slot==1)second_sample[bank]<=din;
    end
    genvar group_index,lane_index;
    generate for(group_index=0;group_index<7;group_index=group_index+1)begin:g_group
        wire write_enable=cea&&(write_global[12:10]==group_index)&&(!init_pack||write_slot==2||ada==last_address);
        wire read_enable=ceb&&(read_global[12:10]==group_index)&&!write_enable;
        wire [71:0] playback_word=write_slot==0 ? {bank_data[group_index][71:24],din} :
            write_slot==1 ? {bank_data[group_index][71:48],din,bank_data[group_index][23:0]} :
            {din,bank_data[group_index][47:0]};
        wire [71:0] write_word=init_pack ? initialization_word : playback_word;
        for(lane_index=0;lane_index<4;lane_index=lane_index+1)begin:g_lane
            wire [35:0] lane_word;
            assign bank_data[group_index][lane_index*18 +: 18]=lane_word[17:0];
            SDPX9B ram(
                .DO(lane_word),.DI({18'd0,write_word[lane_index*18 +: 18]}),.CLKA(clka),.CLKB(clkb),
                .CEA(write_enable),.CEB(read_enable),.OCE(oce),.RESET(reset),
                .ADA({write_global[9:0],2'b00,2'b11}),.ADB({read_global[9:0],4'd0}),
                .BLKSELA(3'd0),.BLKSELB(3'd0));
            defparam ram.BIT_WIDTH_0=18,ram.BIT_WIDTH_1=18,ram.READ_MODE=1'b0;
            defparam ram.BLK_SEL_0=3'b000,ram.BLK_SEL_1=3'b000,ram.RESET_MODE="SYNC";
        end
    end endgenerate
endmodule
