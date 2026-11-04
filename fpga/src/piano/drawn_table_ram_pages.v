module drawn_table_ram_pages(
    input wire clk,
    input wire write_enable,
    input wire [13:0] write_address,
    input wire [15:0] write_data,
    input wire read_enable,
    input wire [13:0] read_address,
    output wire [15:0] read_data
);
    reg [1:0] read_page;
    wire [15:0] page_data [0:2];

    always @(posedge clk)
        if (read_enable) read_page <= read_address[13:12];

    assign read_data = read_page < 3 ? page_data[read_page] : 16'hxxxx;

    genvar page_index;
    generate for (page_index=0; page_index<3; page_index=page_index+1) begin : g_page
        reg [15:0] memory [0:4095];
        reg [15:0] data;
        assign page_data[page_index] = data;

        always @(posedge clk) begin
            if (write_enable && write_address[13:12] == page_index)
                memory[write_address[11:0]] <= write_data;
            if (read_enable && read_address[13:12] == page_index)
                data <= memory[read_address[11:0]];
        end
    end endgenerate
endmodule
