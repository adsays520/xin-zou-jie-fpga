// Immediate synchronised press, followed by release qualification. The 20 ms
// lockout suppresses retriggers, not attack latency. Opt-in at the top level.
module verification_fast_key #(parameter RELEASE_CLOCKS=1000000)(
    input wire clk,rst_n,key_n,enable,
    output reg pressed
);
    reg meta,sync,armed;
    reg [$clog2(RELEASE_CLOCKS+1)-1:0] released;
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin meta<=1;sync<=1;armed<=0;released<=0;pressed<=0;end
        else begin
            meta<=key_n;sync<=meta;pressed<=0;
            if(!enable)begin armed<=0;released<=0;end
            else if(!armed)begin
                if(!sync)released<=0;
                else if(released==RELEASE_CLOCKS-1)begin armed<=1;released<=0;end
                else released<=released+1'b1;
            end else if(!sync)begin pressed<=1;armed<=0;released<=0;end
        end
    end
endmodule
