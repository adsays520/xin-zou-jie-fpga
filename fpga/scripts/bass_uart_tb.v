`timescale 1ns/1ps
module bass_uart_tb;
    reg clk=0,rst_n=0,rx=1;
    always #10 clk=~clk;
    wire set_timbre,piano,bass,trigger;
    wire [2:0] string_sel;
    wire [4:0] fret;
    wire [6:0] velocity;
    integer changes=0,plucks=0;
    guitar_uart_trigger dut(.clk(clk),.rst_n(rst_n),.uart_rx_i(rx),
        .local_level_step(1'b0),.local_level_bus(2'd0),.envelope_write_allowed(1'b1),
        .timbre_set(set_timbre),.timbre_piano(piano),.timbre_bass(bass),
        .trigger(trigger),.trigger_string_sel(string_sel),.trigger_fret_sel(fret),
        .trigger_velocity(velocity));
    always @(posedge clk)begin
        if(set_timbre)changes=changes+1;
        if(trigger)plucks=plucks+1;
    end
    task send_byte;
        input [7:0] value;
        integer bit_index;
        begin
            @(negedge clk);rx=0;repeat(434)@(negedge clk);
            for(bit_index=0;bit_index<8;bit_index=bit_index+1)begin
                rx=value[bit_index];repeat(434)@(negedge clk);
            end
            rx=1;repeat(450)@(negedge clk);
        end
    endtask
    task timbre;
        input [7:0] value,check;
        begin send_byte(8'ha5);send_byte(4);send_byte(value);send_byte(0);send_byte(0);send_byte(check);end
    endtask
    initial begin
        repeat(10)@(negedge clk);rst_n=1;
        repeat(20)@(negedge clk);
        timbre(2,8'ha3);
        if(!bass||piano||changes!=1)$fatal(1,"Bass frame failed");
        timbre(3,8'ha2);
        if(!bass||piano||changes!=1)$fatal(1,"Invalid timbre accepted");
        timbre(0,8'hff);
        if(!bass||changes!=1)$fatal(1,"Invalid checksum accepted");
        timbre(1,8'ha0);
        if(bass||!piano||changes!=2)$fatal(1,"Old piano frame changed");
        timbre(0,8'ha1);
        if(bass||piano||changes!=3)$fatal(1,"Old guitar frame changed");
        send_byte(8'ha5);send_byte(2);send_byte(6);send_byte(20);send_byte(110);send_byte(8'hdb);
        // A5 ^ 02 ^ 06 ^ 14 ^ 6E = DB.
        if(plucks!=1||string_sel!=5||fret!=20||velocity!=110)$fatal(1,"Old pluck frame changed");
        $display("PASS UART: timbres0/1 unchanged, bass2 valid, checksum/range guards valid, pluck unchanged");
        $finish;
    end
endmodule
