`ifndef DRUM_PARAMETER_BANK_V
`define DRUM_PARAMETER_BANK_V
`include "src/drums/rom/drum_bank_config.vh"
module drum_parameter_bank(
    input wire clk,rst_n,boundary,read_enable,
    input wire [9:0] read_address,
    output reg [31:0] read_data,
    input wire load_begin,byte_valid,chunk_valid,load_commit,load_error,
    input wire [7:0] byte_data,
    input wire [10:0] chunk_index,
    output wire load_ready,
    output reg [10:0] chunk_count,
    output reg initialized,fault,active_bank
);
    (* syn_ramstyle="block_ram" *) reg [31:0] memory[0:2047];
    initial $readmemh("src/drums/rom/drum_bank.hex",memory);
    reg session_active,switch_pending;
    reg [11:0] byte_count;
    reg [23:0] byte_word;
    reg [31:0] crc,verify_crc,verify_word;
    reg [9:0] verify_index;
    reg [2:0] verify_state;
    reg [1:0] verify_byte;
    wire verify_issue=verify_state==1&&!read_enable;
    wire [10:0] memory_address=read_enable?{active_bank,read_address}:{1'b1,verify_index};
    assign load_ready=session_active&&!fault&&!initialized&&verify_state==0;
    function [31:0] crc_byte;
        input [31:0] previous_crc;
        input [7:0] value;
        reg [31:0] work;
        integer bit_index;
        begin
            work=previous_crc^{24'd0,value};
            for(bit_index=0;bit_index<8;bit_index=bit_index+1)
                work=work[0]?(work>>1)^32'hedb88320:(work>>1);
            crc_byte=work;
        end
    endfunction
    wire [31:0] verify_next=crc_byte(verify_crc,verify_word[7:0]);
    always @(posedge clk)begin
        if(read_enable||verify_issue)read_data<=memory[memory_address];
        if(rst_n&&load_ready&&byte_valid&&byte_count<3072&&byte_count[1:0]==3)
            memory[{1'b1,byte_count[11:2]}]<={byte_data,byte_word};
    end
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            session_active<=0;switch_pending<=0;byte_count<=0;byte_word<=0;
            crc<=32'hffffffff;verify_crc<=32'hffffffff;verify_word<=0;
            verify_index<=0;verify_state<=0;verify_byte<=0;
            chunk_count<=0;initialized<=0;fault<=0;active_bank<=0;
        end else begin
            if(switch_pending&&boundary)begin active_bank<=1;switch_pending<=0;end
            case(verify_state)
                1:if(!read_enable)verify_state<=2;
                2:begin verify_word<=read_data;verify_byte<=0;verify_state<=3;end
                3:begin
                    verify_crc<=verify_next;verify_word<=verify_word>>8;
                    if(verify_byte==3)begin
                        if(verify_index==767)begin
                            verify_state<=0;
                            if((verify_next^32'hffffffff)==`DRUM_BANK_CRC32)begin
                                initialized<=1;switch_pending<=1;
                            end else fault<=1;
                        end else begin verify_index<=verify_index+1'b1;verify_state<=1;end
                    end else verify_byte<=verify_byte+1'b1;
                end
                default:begin end
            endcase
            if(load_begin)begin
                if(!active_bank&&!initialized)begin
                    session_active<=1;switch_pending<=0;byte_count<=0;byte_word<=0;
                    chunk_count<=0;fault<=0;crc<=32'hffffffff;verify_state<=0;
                end else fault<=1;
            end else if(load_error)begin session_active<=0;verify_state<=0;fault<=1;end
            else if(!fault)begin
                if(byte_valid)begin
                    if(!load_ready||byte_count>=3072)begin fault<=1;session_active<=0;end
                    else begin
                        byte_word<={byte_data,byte_word[23:8]};byte_count<=byte_count+1'b1;
                        crc<=crc_byte(crc,byte_data);
                    end
                end
                if(chunk_valid)begin
                    if(!load_ready||chunk_index!=chunk_count||byte_count!={chunk_count+11'd1,8'd0})begin
                        fault<=1;session_active<=0;
                    end else chunk_count<=chunk_count+1'b1;
                end
                if(load_commit)begin
                    session_active<=0;
                    if(byte_count!=3072||chunk_count!=12||(crc^32'hffffffff)!=`DRUM_BANK_CRC32)fault<=1;
                    else begin verify_state<=1;verify_index<=0;verify_crc<=32'hffffffff;end
                end
            end
        end
    end
endmodule
`endif
