// Behavioral memory models for fast spectral analysis of the unchanged
// arithmetic core. Full-top integration is separately tested with Gowin RAMs.
module poly32_road_bank(output wire secco,decco,output reg [23:0] dout,
 output wire [7:0] dop,eccp,input wire clka,clkb,cea,ceb,oce,reset,
 input wire [4:0] bank,input wire [9:0] ada,adb,last_address,
 input wire init_pack,input wire [23:0] din);
 reg [23:0] mem[0:32767];assign secco=0;assign decco=0;assign dop=0;assign eccp=0;
 always @(posedge clka)if(cea)mem[{bank,ada}]<=din;
 always @(posedge clkb)if(ceb)dout<=mem[{bank,adb}];
endmodule
module poly32_scratch_bank(output wire secco,decco,output reg [23:0] dout,
 output wire [7:0] dop,eccp,input wire clka,clkb,cea,ceb,oce,reset,
 input wire [4:0] bank,input wire [9:0] ada,adb,last_address,input wire [23:0] din);
 reg [23:0] mem[0:32767];assign secco=0;assign decco=0;assign dop=0;assign eccp=0;
 always @(posedge clka)if(cea)mem[{bank,ada}]<=din;
 always @(posedge clkb)if(ceb)dout<=mem[{bank,adb}];
endmodule
module poly32_context_ram #(parameter WIDTH=991)(input wire clk,reset,we,
 input wire [4:0] write_id,read_id,input wire [WIDTH-1:0] din,output reg [WIDTH-1:0] dout);
 reg [WIDTH-1:0] mem[0:31];always @(posedge clk)begin
  if(we)mem[write_id]<=din;if(reset)dout<=0;else dout<=mem[read_id];end
endmodule
