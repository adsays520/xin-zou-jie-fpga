`timescale 1ns/1ps
module tb_context_roundtrip;
    reg clk=0;always #10 clk=~clk;
    reg reset=1,we=0;reg [4:0] write_id=0,read_id=31;
    reg [990:0] din=0;wire [990:0] dout;wire [924:0] old_dout;
    reg [990:0] expected[0:31];integer i,j,pass;
    poly32_context_ram #(.WIDTH(991)) dut(clk,reset,we,write_id,read_id,din,dout);
    poly32_context_ram old_width(clk,reset,we,write_id,read_id,din[924:0],old_dout);
    initial begin
        force GSR.GSRI=0;
        repeat(8)@(negedge clk);reset=0;force GSR.GSRI=1;
        for(pass=0;pass<2;pass=pass+1)begin
            for(i=0;i<32;i=i+1)begin
                for(j=0;j<991;j=j+1)expected[i][j]=((i*101+j*13+(j>>3)+pass*7)%17)<8;
                @(negedge clk);write_id=i;din=expected[i];we=1;
                @(negedge clk);we=0;
                repeat(30)@(negedge clk);
            end
            for(i=0;i<32;i=i+1)begin
                @(negedge clk);read_id=i;
                repeat(7)@(negedge clk);
                if(dout!==expected[i])$fatal(1,"991-bit context mismatch pass=%0d voice=%0d",pass,i);
                if(old_dout!==expected[i][924:0])$fatal(1,"legacy context mismatch");
            end
        end
        $display("PASS all 32 voice contexts: 991-bit and legacy 925-bit, two overwrite passes, seven-clock prefetch");
        $finish;
    end
endmodule
