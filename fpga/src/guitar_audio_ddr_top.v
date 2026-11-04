// Original 50 MHz instrument engine plus a real DDR3 piano parameter store.
// Reset is S0/K16, active low. U4 is in the DDR 1.5 V I/O bank.
module guitar_audio_ddr_top #(parameter integer SD_POWERUP_CLKS=5000000)(
 input wire clk,reset_n,key_next_n,key_pluck_n,uart_rx_i,
 input wire sw1_enc_a,sw1_enc_b,sw2_enc_a,sw2_enc_b,
 input wire sw1_up_n,sw1_right_n,sw1_down_n,sw1_left_n,
 input wire sd_miso,output wire sd_clk,sd_mosi,sd_cs,
 input wire spi_sclk,spi_cs_n,spi_mosi,output wire spi_miso,fpga_irq,fpga_ready,
 output wire uart_tx_o,output wire [5:0] led_n,
 output wire lcd_sck,lcd_sda,lcd_cs_n,lcd_dc,lcd_rst_n,lcd_led,
 output wire HP_BCK,HP_WS,HP_DIN,
 output wire [14:0] ddr_addr,output wire [2:0] ddr_bank,
 output wire ddr_cs,ddr_ras,ddr_cas,ddr_we,ddr_ck,ddr_ck_n,
 output wire ddr_cke,ddr_odt,ddr_reset_n,output wire [3:0] ddr_dm,
 inout wire [31:0] ddr_dq,inout wire [3:0] ddr_dqs,ddr_dqs_n
);
 (* syn_preserve=1 *) reg [2:0] reset_pipe;
 always @(posedge clk or negedge reset_n)
  if(!reset_n)reset_pipe<=0;else reset_pipe<={reset_pipe[1:0],1'b1};
 wire rst_n=reset_pipe[2];
 wire pll_lock,pll_stop,memory_clk,mem_clk,calibrated,ddr_rst,ddr_ref100;
 wire cmd_ready,wr_data_rdy,rd_data_valid,rd_data_end;
 wire [2:0] cmd;wire cmd_en;wire [28:0] addr;
 wire [255:0] wr_data,rd_data;wire [31:0] wr_data_mask;
 wire wr_data_en,wr_data_end;
 Gowin_PLL u_ddr_pll(
  .lock(pll_lock),.clkout0(),.clkout1(ddr_ref100),.clkout2(memory_clk),
  .clkin(clk),.reset(!rst_n),.enclk0(1'b1),.enclk1(1'b1),.enclk2(pll_stop));
 DDR3_Memory_Interface_Top u_ddr3(
  .clk(ddr_ref100),.memory_clk(memory_clk),.pll_stop(pll_stop),
  .pll_lock(pll_lock),.rst_n(rst_n),.clk_out(mem_clk),.ddr_rst(ddr_rst),
  .init_calib_complete(calibrated),
  .cmd_ready(cmd_ready),.cmd(cmd),.cmd_en(cmd_en),.addr(addr),
  .wr_data_rdy(wr_data_rdy),.wr_data(wr_data),.wr_data_en(wr_data_en),
  .wr_data_end(wr_data_end),.wr_data_mask(wr_data_mask),
  .rd_data(rd_data),.rd_data_valid(rd_data_valid),.rd_data_end(rd_data_end),
  .sr_req(1'b0),.ref_req(1'b0),.sr_ack(),.ref_ack(),.burst(1'b0),
  .O_ddr_addr(ddr_addr),.O_ddr_ba(ddr_bank),.O_ddr_cs_n(ddr_cs),
  .O_ddr_ras_n(ddr_ras),.O_ddr_cas_n(ddr_cas),.O_ddr_we_n(ddr_we),
  .O_ddr_clk(ddr_ck),.O_ddr_clk_n(ddr_ck_n),.O_ddr_cke(ddr_cke),
  .O_ddr_odt(ddr_odt),.O_ddr_reset_n(ddr_reset_n),.O_ddr_dqm(ddr_dm),
  .IO_ddr_dq(ddr_dq),.IO_ddr_dqs(ddr_dqs),.IO_ddr_dqs_n(ddr_dqs_n));
 wire run_n=rst_n&&calibrated&&!ddr_rst&&pll_lock;
 (* syn_preserve=1 *) reg [2:0] sys_pipe,mem_pipe;
 always @(posedge clk or negedge run_n)
  if(!run_n)sys_pipe<=0;else sys_pipe<={sys_pipe[1:0],1'b1};
 always @(posedge mem_clk or negedge run_n)
  if(!run_n)mem_pipe<=0;else mem_pipe<={mem_pipe[1:0],1'b1};
 (* syn_preserve=1,async_reg="true" *) reg mem_up_meta,mem_up_sync,fault_meta,fault_sync;
 reg ever_ready,lost_ready,startup_timeout;
 reg [26:0] startup_count;
 wire transport_fault,bank_ready,bank_fault;
 wire transport_ready=sys_pipe[2]&&mem_up_sync&&!fault_sync&&!lost_ready&&!startup_timeout;
 always @(posedge clk or negedge rst_n)begin
  if(!rst_n)begin
   mem_up_meta<=0;mem_up_sync<=0;fault_meta<=0;fault_sync<=0;
   ever_ready<=0;lost_ready<=0;startup_timeout<=0;startup_count<=0;
  end else begin
   mem_up_meta<=mem_pipe[2];mem_up_sync<=mem_up_meta;
   fault_meta<=transport_fault;fault_sync<=fault_meta;
   if(transport_ready)ever_ready<=1;
   if(ever_ready&&!(sys_pipe[2]&&mem_up_sync))lost_ready<=1;
   if(!ever_ready&&!startup_timeout)begin
    if(startup_count==99999999)startup_timeout<=1;
    else startup_count<=startup_count+1'b1;
   end
  end
 end
 wire bank_req_valid,bank_req_ready,bank_rsp_valid,bank_rsp_ready;
 wire [63:0] bank_req_data,bank_rsp_data;
 wire space_req_valid,space_req_ready,space_rsp_valid,space_rsp_ready,space_fault;
 wire [63:0] space_req_data,space_rsp_data;
 wire req_valid,req_ready,rsp_valid,rsp_ready;
 wire [63:0] req_data,rsp_data;
 piano_audio_ddr_arbiter u_arbiter(
  .clk(clk),.rst_n(sys_pipe[2]),
  .piano_req_valid(bank_req_valid),.piano_req_ready(bank_req_ready),.piano_req_data(bank_req_data),
  .piano_rsp_valid(bank_rsp_valid),.piano_rsp_ready(bank_rsp_ready),.piano_rsp_data(bank_rsp_data),
  .audio_req_valid(space_req_valid),.audio_req_ready(space_req_ready),.audio_req_data(space_req_data),
  .audio_rsp_valid(space_rsp_valid),.audio_rsp_ready(space_rsp_ready),.audio_rsp_data(space_rsp_data),
  .req_valid(req_valid),.req_ready(req_ready),.req_data(req_data),.rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.rsp_data(rsp_data));
 piano_ddr_transport u_memory(
  .clk(clk),.sys_rst_n(sys_pipe[2]),.mem_clk(mem_clk),.mem_rst_n(mem_pipe[2]),
  .calibrated(mem_pipe[2]),.req_valid(req_valid),.req_ready(req_ready),.req_data(req_data),
  .rsp_valid(rsp_valid),.rsp_ready(rsp_ready),.rsp_data(rsp_data),.fault(transport_fault),
  .cmd_ready(cmd_ready),.wr_data_rdy(wr_data_rdy),.cmd(cmd),.cmd_en(cmd_en),.addr(addr),
  .wr_data(wr_data),.wr_data_mask(wr_data_mask),.wr_data_en(wr_data_en),.wr_data_end(wr_data_end),
  .rd_data(rd_data),.rd_data_valid(rd_data_valid),.rd_data_end(rd_data_end));
 wire [5:0] audio_led_n;
 wire system_fault=fault_sync||lost_ready||startup_timeout;
 assign led_n=system_fault||bank_fault||space_fault?6'b010101:audio_led_n;
 guitar_audio_top #(.SD_POWERUP_CLKS(SD_POWERUP_CLKS)) u_audio(
  .sw1_enc_a(sw1_enc_a),.sw1_enc_b(sw1_enc_b),.sw2_enc_a(sw2_enc_a),.sw2_enc_b(sw2_enc_b),
  .sw1_up_n(sw1_up_n),.sw1_right_n(sw1_right_n),.sw1_down_n(sw1_down_n),.sw1_left_n(sw1_left_n),
  .clk(clk),.rst(!rst_n),.key_next_n(key_next_n),.key_pluck_n(key_pluck_n),
  .uart_rx_i(uart_rx_i),.uart_tx_o(uart_tx_o),
  .sd_miso(sd_miso),.sd_clk(sd_clk),.sd_mosi(sd_mosi),.sd_cs(sd_cs),
  .spi_sclk(spi_sclk),.spi_cs_n(spi_cs_n),.spi_mosi(spi_mosi),.spi_miso(spi_miso),.fpga_irq(fpga_irq),.fpga_ready(fpga_ready),.led_n(audio_led_n),
  .lcd_sck(lcd_sck),.lcd_sda(lcd_sda),.lcd_cs_n(lcd_cs_n),.lcd_dc(lcd_dc),
  .lcd_rst_n(lcd_rst_n),.lcd_led(lcd_led),.HP_BCK(HP_BCK),.HP_WS(HP_WS),.HP_DIN(HP_DIN),
  .piano_memory_ready(transport_ready),.piano_transport_fault(system_fault),
  .piano_bank_ready(bank_ready),.piano_memory_fault(bank_fault),
  .piano_req_valid(bank_req_valid),.piano_req_ready(bank_req_ready),.piano_req_data(bank_req_data),
  .piano_rsp_valid(bank_rsp_valid),.piano_rsp_ready(bank_rsp_ready),.piano_rsp_data(bank_rsp_data),
  .space_req_valid(space_req_valid),.space_req_ready(space_req_ready),.space_req_data(space_req_data),
  .space_rsp_valid(space_rsp_valid),.space_rsp_ready(space_rsp_ready),.space_rsp_data(space_rsp_data),.space_memory_fault(space_fault));
endmodule
