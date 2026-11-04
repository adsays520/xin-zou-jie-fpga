module pluck_event_queue_v12_reference #(
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
    wire [COUNT_BITS:0] space=DEPTH-count+pop;
    wire uart_accept=uart_valid&&(space!=0);
    wire local_accept=local_valid&&(space>{ {(COUNT_BITS){1'b0}},uart_accept});
    wire [1:0] push_count={1'b0,uart_accept}+{1'b0,local_accept};
    wire [POINTER_BITS-1:0] local_pointer=write_pointer+uart_accept;
    assign ingress_ready=rst_n&&!clear&&(count<=DEPTH-4);
    assign event_valid=rst_n&&pop;
    assign event_data=events[read_pointer];
    assign occupancy=count;
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            write_pointer<=0;read_pointer<=0;count<=0;overflow<=0;
        end else if(clear)begin
            write_pointer<=0;read_pointer<=0;count<=0;
        end else begin
            if(uart_accept)events[write_pointer]<=uart_event;
            if(local_accept)events[local_pointer]<=local_event;
            write_pointer<=write_pointer+push_count;
            if(pop)read_pointer<=read_pointer+1'b1;
            count<=count+push_count-pop;
            if((uart_valid&&!uart_accept)||(local_valid&&!local_accept))overflow<=1;
        end
    end
endmodule
