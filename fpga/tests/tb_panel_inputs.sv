`timescale 1ns/1ps
module tb_panel_inputs;
 reg clk=0,rst_n=0;always #10 clk=~clk;
 reg a=1,b=1,c=1,d=1,u=1,r=1,n=1,l=1;
 wire row,col,slide,vib,up,right,down,left;
 panel_inputs #(.STABLE_CLKS(3)) dut(.clk(clk),.rst_n(rst_n),.sw1_a(a),.sw1_b(b),.sw2_a(c),.sw2_b(d),
 .up_n(u),.right_n(r),.down_n(n),.left_n(l),.row_next(row),.col_next(col),.slide_step(slide),.vibrato_step(vib),.up(up),.right(right),.down(down),.left(left));
 integer rows=0,cols=0,slides=0,vibs=0,ups=0,downs=0;
 always @(posedge clk)begin if(row)rows=rows+1;if(col)cols=cols+1;if(slide)slides=slides+1;if(vib)vibs=vibs+1;if(up)ups=ups+1;if(down)downs=downs+1;end
 task wait6;begin repeat(6)@(negedge clk);end endtask
 task sw1;input[1:0]v;begin {a,b}=v;wait6;end endtask
 task sw2;input[1:0]v;begin {c,d}=v;wait6;end endtask
 initial begin
  wait6;rst_n=1;wait6;
  sw1(1);sw1(3);if(cols!=0||rows!=0)$fatal(1,"contact bounce produced detent");
  sw1(1);sw1(0);if(cols!=1)$fatal(1,"one click must equal TWO Gray transitions");
  sw1(2);sw1(3);if(cols!=2)$fatal(1,"second detent missing");
  sw1(2);sw1(0);sw1(1);sw1(3);if(rows!=2)$fatal(1,"CCW detents");
  sw1(0);sw1(3);if(cols!=2||rows!=2)$fatal(1,"illegal Gray jump counted");
  sw2(1);sw2(0);sw2(2);sw2(3);if(slides!=2)$fatal(1,"SW2 up-slide count");
  sw2(2);sw2(0);if(vibs!=1||cols!=2)$fatal(1,"encoders interfere");
  u=0;repeat(30)@(negedge clk);if(ups!=1)$fatal(1,"held up repeats");
  u=1;wait6;n=0;repeat(20)@(negedge clk);if(downs!=1)$fatal(1,"confirm debounce");
  $display("PASS panel inputs: two transitions/detent, reversal bounce, illegal Gray, independent encoders, debounced single actions");$finish;
 end
endmodule
