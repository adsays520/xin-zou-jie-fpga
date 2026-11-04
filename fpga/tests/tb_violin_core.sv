`timescale 1ns/1ps
module tb_violin_core;
parameter FRAMES=31000;
reg clk=0,rst_n=0,sample_tick=0,command_valid=0;
reg [16:0] command=0;
wire command_ready,ready,produced,internal_valid,deadline,overflow,invalid,sample_valid;
wire signed [23:0] sample_data,internal_data;
wire [15:0] cycles;
reg [23:0] expected[0:FRAMES-1],internal_expected[0:FRAMES*2-1];
reg [17:0] commands[0:FRAMES-1];
integer frame,clock_index,produced_count=0,internal_count=0,max_cycles=0;
reg signed [23:0] previous_sample=0;
always #10 clk=~clk;
violin_core dut(.clk(clk),.rst_n(rst_n),.sample_tick(sample_tick),
 .command_valid(command_valid),.command_ready(command_ready),
 .command_force_off(command[16]),.command_legato(command[15]),.command_on(command[14]),
 .command_key(command[13:7]),.command_velocity(command[6:0]),
 .ready_o(ready),.sample_o(sample_data),.sample_valid_o(sample_valid),.produced_o(produced),
 .internal_valid_o(internal_valid),.internal_sample_o(internal_data),
 .deadline_miss_o(deadline),.overflow_o(overflow),.invalid_event_o(invalid),.last_cycles_o(cycles));
always @(negedge clk)begin
 if(rst_n)begin
  if(deadline||overflow||invalid)$fatal(1,"Status failure frame=%0d state=%0d deadline=%b overflow=%b invalid=%b neck=%0d bridge=%0d interaction=%0d reflection=%0d wavewrites=%0d/%0d",frame,dut.state,deadline,overflow,invalid,dut.neck_out,dut.bridge_out,dut.interaction,dut.bridge_reflection,dut.neck_wdata,dut.bridge_wdata);
  if(internal_valid)begin
   if(internal_data!==internal_expected[internal_count])$fatal(1,"Internal mismatch %0d actual=%0d expected=%0d period=%0d pressure=%0d loud=%0d env=%0d voice=%0d body=%0d dc=%0d",internal_count,internal_data,$signed(internal_expected[internal_count]),dut.period,dut.pressure,dut.loudness,dut.envelope,dut.voice_output,dut.body_value,dut.dc_output);
   internal_count=internal_count+1;
  end
  if(produced)begin
   if(dut.pending_output!==expected[produced_count])$fatal(1,"FIR mismatch %0d actual=%0d expected=%0d",produced_count,dut.pending_output,$signed(expected[produced_count]));
   produced_count=produced_count+1;
   if(cycles>max_cycles)max_cycles=cycles;
  end
  if(!sample_valid&&sample_data!==previous_sample)$fatal(1,"Output changed outside frame boundary");
  previous_sample=sample_data;
 end
end
initial begin
 $readmemh("violin_r15/test_results/expected.hex",expected);
 $readmemh("violin_r15/test_results/internal.hex",internal_expected);
 $readmemh("violin_r15/test_results/commands.hex",commands);
 repeat(5)@(negedge clk);rst_n=1;
 wait(ready);@(negedge clk);
 command=commands[0][16:0];command_valid=commands[0][17];
 @(negedge clk);command_valid=0;repeat(32)@(negedge clk);
 for(frame=0;frame<FRAMES;frame=frame+1)begin
  sample_tick=1;@(negedge clk);sample_tick=0;
  for(clock_index=1;clock_index<1041;clock_index=clock_index+1)begin
   if(clock_index==1000&&frame+1<FRAMES)begin
    if(!command_ready)$fatal(1,"Command queue blocked");
    command=commands[frame+1][16:0];command_valid=commands[frame+1][17];
   end
   if(clock_index==1001)command_valid=0;
   @(negedge clk);
  end
 end
 if(produced_count!=FRAMES||internal_count!=FRAMES*2)$fatal(1,"Incomplete render");
 $display("PASS violin full core: frames=%0d internal=%0d max_cycles=%0d budget=1041",produced_count,internal_count,max_cycles);
 $finish;
end
initial begin #1000000000000;$fatal(1,"Timeout");end
endmodule
