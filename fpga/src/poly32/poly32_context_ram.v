// 32 x 925-bit voice context, serialized through four 64-bit SDP36KE lanes.
//
// A context is padded to 1024 bits and stored as four 256-bit chunks. The
// scheduler changes read_id at least seven clocks before context_load, so the
// synchronous four-chunk prefetch is complete before the next voice is loaded.
// A save pulse snapshots the whole context; its four chunks are then written
// in the background while the following voice is running. This replaces the
// old fifteen-wide-lane implementation with four physical RAMs.
module poly32_context_ram #(parameter integer WIDTH=925)(
    input wire clk, reset, we,
    input wire [4:0] write_id, read_id,
    input wire [WIDTH-1:0] din,
    output wire [WIDTH-1:0] dout
);
    reg [1023:0] write_buffer;
    reg [1023:0] read_buffer;
    reg [4:0] write_target;
    reg [4:0] read_target;
    reg [1:0] write_chunk;
    reg [1:0] capture_chunk;
    reg [2:0] issued_chunks;
    reg write_busy;
    reg read_busy;
    reg capture_valid;
    reg [8:0] read_address;

    wire [255:0] lane_dout;
    wire [255:0] padded_in = write_buffer[write_chunk*256 +: 256];
    wire [8:0] write_address = {2'b00, write_target, write_chunk};

    assign dout = read_buffer[WIDTH-1:0];

    genvar lane;
    generate for (lane=0; lane<4; lane=lane+1) begin : g_lane
        SDP36KE ram (
            .DO(lane_dout[lane*64 +: 64]), .DOP(),
            .SECCO(), .DECCO(), .ECCP(),
            .CLKA(clk), .CLKB(clk), .CEA(write_busy), .CEB(read_busy),
            .OCE(1'b1), .RESET(reset),
            .ADA(write_address), .ADB(read_address),
            .DI(padded_in[lane*64 +: 64]), .DIP(8'd0),
            .BLKSELA(3'd0), .BLKSELB(3'd0),
            .SECCI(1'b0), .DECCI(1'b0)
        );
        defparam ram.ECC_WRITE_EN="TRUE";
        defparam ram.ECC_READ_EN="FALSE";
        defparam ram.READ_MODE=1'b0;
        defparam ram.BLK_SEL_A=3'b000;
        defparam ram.BLK_SEL_B=3'b000;
        defparam ram.RESET_MODE="SYNC";
        defparam ram.INIT_FILE="NONE";
    end endgenerate

    always @(posedge clk) begin
        if (reset) begin
            write_buffer <= 1024'd0;
            read_buffer <= 1024'd0;
            write_target <= 5'd0;
            read_target <= 5'd31;
            write_chunk <= 2'd0;
            capture_chunk <= 2'd0;
            issued_chunks <= 3'd0;
            write_busy <= 1'b0;
            read_busy <= 1'b0;
            capture_valid <= 1'b0;
            read_address <= 9'd0;
        end else begin
            // Saves are 31 clocks apart, so a previous four-cycle write has
            // always completed before the next snapshot arrives.
            if (we) begin
                write_buffer <= {{(1024-WIDTH){1'b0}},din};
                write_target <= write_id;
                write_chunk <= 2'd0;
                write_busy <= 1'b1;
            end else if (write_busy) begin
                if (write_chunk == 2'd3)
                    write_busy <= 1'b0;
                else
                    write_chunk <= write_chunk + 1'b1;
            end

            // A changed read_id starts four sequential RAM reads. One extra
            // capture clock accounts for SDP36KE's synchronous B port.
            if (!read_busy && read_id != read_target) begin
                read_target <= read_id;
                read_address <= {2'b00,read_id,2'b00};
                issued_chunks <= 3'd1;
                capture_chunk <= 2'd0;
                capture_valid <= 1'b0;
                read_busy <= 1'b1;
            end else if (read_busy) begin
                if (capture_valid) begin
                    case (capture_chunk)
                        2'd0: read_buffer[255:0] <= lane_dout;
                        2'd1: read_buffer[511:256] <= lane_dout;
                        2'd2: read_buffer[767:512] <= lane_dout;
                        2'd3: read_buffer[1023:768] <= lane_dout;
                    endcase
                    if (capture_chunk == 2'd3)
                        read_busy <= 1'b0;
                    else
                        capture_chunk <= capture_chunk + 1'b1;
                end
                if (issued_chunks < 3'd4) begin
                    read_address <= {2'b00,read_target,issued_chunks[1:0]};
                    issued_chunks <= issued_chunks + 1'b1;
                    capture_valid <= 1'b1;
                end
            end
        end
    end
endmodule
