`timescale 1ns/1ps
module tb_note_lookup;
    reg clk=0;always #10 clk=~clk;
    reg [2:0] s=0,s_q;reg [4:0] f=0,f_q;
    always @(posedge clk)begin s_q<=s;f_q<=f>20 ? 20 : f;end
    wire [149:0] baseline,normal,pipelined;
    guitar_note_params_original old(s,f,baseline[149:140],baseline[139:124],baseline[123:114],baseline[113:98],
        baseline[97:74],baseline[73:50],baseline[33:2],baseline[49:34],baseline[1:0]);
    guitar_note_params current(s,f,normal[149:140],normal[139:124],normal[123:114],normal[113:98],
        normal[97:74],normal[73:50],normal[33:2],normal[49:34],normal[1:0]);
    guitar_note_params #(.PRECLAMPED(1)) split(s_q,f_q,pipelined[149:140],pipelined[139:124],pipelined[123:114],pipelined[113:98],
        pipelined[97:74],pipelined[73:50],pipelined[33:2],pipelined[49:34],pipelined[1:0]);
    integer i,j;
    initial begin
        for(i=0;i<8;i=i+1)for(j=0;j<32;j=j+1)begin
            @(negedge clk);s=i;f=j;repeat(2)@(negedge clk);
            if(normal!==baseline || pipelined!==baseline)$fatal(1,"note parameters differ string=%0d fret=%0d old=%h normal=%h split=%h inputs=%0d,%0d",i,j,baseline,normal,pipelined,s_q,f_q);
        end
        $display("PASS all 256 string/fret inputs: all 150 parameter bits match original, including fret clamp/defaults and split lookup stage");
        $finish;
    end
endmodule
