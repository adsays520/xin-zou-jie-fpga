// Synchronize an active-low board key and emit exactly one pulse per press.
// At 50 MHz, 1,000,000 stable clocks are 20 ms of debounce time.
module button_debounce (
    input wire clk,
    input wire rst_n,
    input wire key_n,
    output reg pressed
);
    localparam [19:0] DEBOUNCE_MAX = 20'd999999;

    reg key_meta, key_sync, stable_key;
    reg [19:0] stable_count;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            key_meta    <= 1'b1;
            key_sync    <= 1'b1;
            stable_key  <= 1'b1;
            stable_count <= 20'd0;
            pressed     <= 1'b0;
        end else begin
            key_meta <= key_n;
            key_sync <= key_meta;
            pressed  <= 1'b0;

            if (key_sync == stable_key) begin
                stable_count <= 20'd0;
            end else if (stable_count == DEBOUNCE_MAX) begin
                stable_key   <= key_sync;
                stable_count <= 20'd0;
                if (!key_sync)
                    pressed <= 1'b1;
            end else begin
                stable_count <= stable_count + 1'b1;
            end
        end
    end
endmodule
