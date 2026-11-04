`timescale 1ns/1ps
// Full production top, real UART receiver, actual poly32 guitar engine and
// vendor RAM models. Measures a single idle E2 attack at the final S16 word tap.
module tb_top_latency;
    reg clk=0;always #10 clk=~clk;
    reg rst=1,key_next_n=1,key_pluck_n=1,uart_rx=1;
    wire tx,bck,ws,din,pa;wire [5:0] leds;
    guitar_audio_top dut(.clk(clk),.rst(rst),.key_next_n(key_next_n),.key_pluck_n(key_pluck_n),
        .uart_rx_i(uart_rx),.uart_tx_o(tx),.HP_BCK(bck),.HP_WS(ws),.HP_DIN(din),.PA_EN(pa),.led_n(leds));
    // Shorten only the pre-test released-key qualification. Press-to-audio
    // logic and all audio clocks, algorithms, gain and serializer are unchanged.
    defparam dut.u_fast_pluck_button.RELEASE_CLOCKS=1000;
    task uart_byte(input [7:0] b);
        integer j;
        begin
            @(negedge clk);uart_rx=0;repeat(434)@(negedge clk);
            for(j=0;j<8;j=j+1)begin uart_rx=b[j];repeat(434)@(negedge clk);end
            uart_rx=1;repeat(434)@(negedge clk);
        end
    endtask
    task command(input [7:0] cmd,a,b,c);
        begin uart_byte(8'hA5);uart_byte(cmd);uart_byte(a);uart_byte(b);uart_byte(c);uart_byte(8'hA5^cmd^a^b^c);end
    endtask
    time press_time;
    initial begin
        force GSR.GSRI=1'b0;
        repeat(8)@(negedge clk);rst=0;
        force GSR.GSRI=1'b1;
        command(8'h85,1,0,0);
        // Let the fast key qualify an idle, released switch before the first press.
        repeat(6000)@(negedge clk);
        if(!dut.verification_fast_key_enable)$fatal(1,"real UART did not enable fast key");
        if(dut.audio_word_l!==0 || dut.audio_word_r!==0)$fatal(1,"idle output is not silent");
        press_time=$time;key_pluck_n=0;
        wait(dut.audio_word_l!=0 || dut.audio_word_r!=0);
        if($time-press_time>5000000)$fatal(1,"E2 digital onset exceeds 5 ms");
        $display("PASS full-top idle E2: F15 edge to first nonzero S16 word = %0d ns",$time-press_time);
        if(dut.poly_deadline_miss || dut.piano_deadline_miss || dut.drum_deadline_miss)$fatal(1,"audio deadline missed");
        key_pluck_n=1;
        repeat(1000)@(negedge clk);
        $finish;
    end
    initial begin #30000000;$fatal(1,"full top latency timeout");end
endmodule
