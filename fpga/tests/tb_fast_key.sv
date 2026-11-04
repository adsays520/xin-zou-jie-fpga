`timescale 1ns/1ps
module tb_fast_key;
    reg clk=0;always #10 clk=~clk;
    reg rst_n=0,key_n=1,enable=0;wire pressed;
    integer pulses=0,wait_clocks;
    // Qualification interval accelerated to 1000 clocks; attack path is unchanged.
    verification_fast_key #(.RELEASE_CLOCKS(1000)) dut(.clk(clk),.rst_n(rst_n),.key_n(key_n),.enable(enable),.pressed(pressed));
    always @(posedge clk)if(pressed)pulses=pulses+1;
    initial begin
        repeat(8)@(negedge clk);rst_n=1;enable=1;
        repeat(1010)@(negedge clk);key_n=0;
        wait_clocks=0;
        while(!pressed)begin @(negedge clk);wait_clocks=wait_clocks+1;end
        if(wait_clocks>3)$fatal(1,"attack was delayed %0d cycles",wait_clocks);
        repeat(10)begin key_n=1;repeat(25)@(negedge clk);key_n=0;repeat(25)@(negedge clk);end
        if(pulses!=1)$fatal(1,"bounce retriggered");
        key_n=1;repeat(1010)@(negedge clk);key_n=0;repeat(8)@(negedge clk);
        if(pulses!=2)$fatal(1,"stable release did not rearm");
        enable=0;key_n=1;repeat(1010)@(negedge clk);key_n=0;repeat(8)@(negedge clk);
        if(pulses!=2)$fatal(1,"disabled mode triggered");
        $display("PASS fast key attack=%0d clocks, bounce lockout and opt-in behaviour",wait_clocks);
        $finish;
    end
endmodule
