module pluck_event_queue #(
    parameter integer DEPTH=16
)(
    input wire clk,rst_n,clear,sample_tick,
    input wire uart_valid,input wire [14:0] uart_event,
    input wire local_valid,input wire [14:0] local_event,
    output wire ingress_ready,output wire event_valid,
    output wire [14:0] event_data,
    output wire [$clog2(DEPTH+1)-1:0] occupancy,
    output reg overflow
);
    localparam integer POINTER_BITS=$clog2(DEPTH);
    localparam integer COUNT_BITS=$clog2(DEPTH+1);
    (* syn_ramstyle="registers" *) reg [14:0] events[0:DEPTH-1];
    reg [POINTER_BITS-1:0] write_pointer,read_pointer;
    reg [COUNT_BITS-1:0] count;
    wire pop=sample_tick&&(count!=0)&&!clear;
    wire uart_accept=uart_valid&&((count<DEPTH)||pop);
    wire local_accept=local_valid&&((count<DEPTH-1)||
        (count==DEPTH-1&&(!uart_valid||pop))||(count==DEPTH&&pop&&!uart_valid));
    wire [1:0] push_count={1'b0,uart_accept}+{1'b0,local_accept};
    wire [POINTER_BITS-1:0] local_pointer=write_pointer+uart_accept;
    assign ingress_ready=rst_n&&!clear&&(count<=DEPTH-4);
    assign event_valid=rst_n&&pop;
    assign event_data=events[read_pointer];
    assign occupancy=count;
    genvar slot;
    generate for(slot=0;slot<DEPTH;slot=slot+1)begin:g_slot
        always @(posedge clk)if(rst_n&&!clear)begin
            if(uart_accept&&write_pointer==slot)events[slot]<=uart_event;
            else if(local_accept&&local_pointer==slot)events[slot]<=local_event;
        end
    end endgenerate
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            write_pointer<=0;read_pointer<=0;count<=0;overflow<=0;
        end else if(clear)begin
            write_pointer<=0;read_pointer<=0;count<=0;
        end else begin
            write_pointer<=write_pointer+push_count;
            if(pop)read_pointer<=read_pointer+1'b1;
            count<=count+push_count-pop;
            if((uart_valid&&!uart_accept)||(local_valid&&!local_accept))overflow<=1;
        end
    end
endmodule
