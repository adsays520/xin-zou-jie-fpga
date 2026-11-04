// Functional DDR application-interface model, NOT an electrical DDR3 PHY model.
// Command/data channels stall independently and reads return variable latency.
// Unwritten memory is intentionally X: the client must enforce history validity.
module ddr_app_model(
    input wire clk,rst_n,calib_complete,freeze,corrupt,
    input wire [2:0] cmd,input wire cmd_en,input wire [28:0] addr,
    output wire cmd_ready,
    input wire [255:0] wr_data,input wire [31:0] wr_data_mask,
    input wire wr_data_en,wr_data_end,output wire wr_data_rdy,
    output reg [255:0] rd_data,output reg rd_data_valid
);
    reg [255:0] memory[0:8191];
    reg [31:0] random_state=32'hc0ffee21;
    reg have_command,have_data;reg [2:0] saved_cmd;
    reg [28:0] saved_addr;reg [255:0] saved_data;reg [31:0] saved_mask;
    reg [4:0] read_count;reg [12:0] read_index;
    integer b;
    assign cmd_ready=calib_complete&&!freeze&&!have_command&&random_state[0];
    assign wr_data_rdy=calib_complete&&!freeze&&!have_data&&random_state[3];
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            have_command<=0;have_data<=0;read_count<=0;
            rd_data_valid<=0;rd_data<=0;random_state<=32'hc0ffee21;
        end else begin
            random_state<={random_state[30:0],random_state[31]^random_state[21]^random_state[1]^random_state[0]};
            rd_data_valid<=0;
            if(cmd_en&&cmd_ready)begin
                if(addr[2:0]!=0||addr>=65536)$fatal(1,"DDR address unit/alignment error %h",addr);
                if(cmd!=0&&cmd!=1)$fatal(1,"unsupported command");
                have_command<=1;saved_cmd<=cmd;saved_addr<=addr;
            end
            if(wr_data_en&&wr_data_rdy)begin
                if(!wr_data_end)$fatal(1,"BL8 at 1:4 must end on its one 256-bit beat");
                have_data<=1;saved_data<=wr_data;saved_mask<=wr_data_mask;
            end
            if(have_command&&!freeze)begin
                if(saved_cmd==0&&have_data)begin
                    for(b=0;b<32;b=b+1)
                        if(!saved_mask[b])memory[saved_addr>>3][b*8 +: 8]<=saved_data[b*8 +: 8];
                    have_command<=0;have_data<=0;
                end else if(saved_cmd==1&&read_count==0)begin
                    read_count<=1+random_state[7:4];read_index<=saved_addr[15:3];have_command<=0;
                end
            end
            if(read_count!=0&&!freeze)begin
                read_count<=read_count-1'b1;
                if(read_count==1)begin
                    rd_data<=memory[read_index] ^ (corrupt ? {8{32'h00010001}} : 256'd0);
                    rd_data_valid<=1;
                end
            end
        end
    end
endmodule
