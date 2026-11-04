`timescale 1ns/1ps
module tb_drums_synth;
 reg clk=0;always #10 clk=~clk;
 reg rst_n=0,tick=0,panic=0,hit=0,hit2=0;
 reg [3:0] voice=0,voice2=0;reg [6:0] velocity=127,velocity2=127;
 reg [1:0] kit=0;reg lwe=0;reg [3:0] lv=0;reg [6:0] level=127;
 wire valid,active,deadline,clipped;wire signed [23:0] l,r;
 drum_synth dut(.clk(clk),.rst_n(rst_n),.sample_tick(tick),.panic(panic),
 .hit(hit),.hit_voice(voice),.hit_velocity(velocity),.hit2(hit2),.hit2_voice(voice2),.hit2_velocity(velocity2),
 .kit(kit),.level_we(lwe),.level_voice(lv),.level_value(level),
 .sample_valid(valid),.sample_l(l),.sample_r(r),.active(active),.deadline_miss(deadline),.clipped(clipped));
 integer clocks,max_clocks=0,n,k,v,f,count,frames,mode=0;
 task frame;
 begin
  tick=1;@(negedge clk);tick=0;clocks=1;
  while(!valid)begin @(negedge clk);clocks=clocks+1;if(clocks>=1041)$fatal(1,"sample deadline");end
  if(clocks>max_clocks)max_clocks=clocks;
  if(deadline||clipped||^l===1'bx||^r===1'bx)$fatal(1,"bad output k=%0d v=%0d n=%0d l=%0d r=%0d",k,v,n,l,r);
  repeat(4)@(negedge clk);
 end endtask
 task strike;input integer d,vel;
 begin voice=d;velocity=vel;hit=1;@(negedge clk);hit=0;end endtask
 task stop;
 begin panic=1;@(negedge clk);panic=0;frame();if(l!=0||r!=0||active)$fatal(1,"panic");end endtask
 initial begin
  if($value$plusargs("MODE=%d",mode))begin end
  repeat(5)@(negedge clk);rst_n=1;
  for(v=0;v<12;v=v+1)begin lv=v;lwe=1;@(negedge clk);lwe=0;@(negedge clk);end
  if(mode==0)begin
   for(k=0;k<3;k=k+1)begin kit=k;
    for(v=0;v<12;v=v+1)begin stop();strike(v,127);count=0;
     for(n=0;n<512;n=n+1)begin frame();if(l!=0||r!=0)count=count+1;end
     if(count<450)$fatal(1,"silent voice kit=%0d voice=%0d count=%0d",k,v,count);
    end
    stop();
    for(n=0;n<4096;n=n+1)begin
     if(n%37==0)for(v=0;v<12;v=v+1)strike(v,127);
     frame();
    end
   end
   stop();strike(3,127);repeat(100)frame();strike(2,127);repeat(64)frame();
   if(dut.body_env[3]!=0||dut.noise_env[3]!=0)$fatal(1,"hat choke");stop();
  end else begin
   f=$fopen("tests/results/drums_synth_q23.txt","w");
   for(k=0;k<3;k=k+1)begin kit=k;
    for(v=0;v<12;v=v+1)begin
     if((mode==2&&v==0)||(mode==1&&(v==0||k==1)))begin
      stop();strike(v,110);frames=v==0?24000:(v==5?48000:24000);
      for(n=0;n<frames;n=n+1)begin frame();$fwrite(f,"%0d %0d %0d %0d %0d\n",k,v,n,l,r);end
      $display("RENDER kit=%0d voice=%0d",k,v);
     end
    end
   end
   stop();kit=1;v=12;
   for(n=0;n<(mode==2?0:96000);n=n+1)begin
    if(n%24000==0||n==24480)strike(0,110);
    frame();$fwrite(f,"%0d %0d %0d %0d %0d\n",kit,v,n,l,r);
   end
   $fclose(f);stop();
  end
  $display("PASS algorithmic drums mode=%0d: no samples, no clipping/deadline, max cycles=%0d",mode,max_clocks);
  $finish;
 end
endmodule
