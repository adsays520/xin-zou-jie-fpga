from iverilog_runner import compile_sim,simulate
p=compile_sim('tb_panel_lcd',['src/st7735_status.v','src/panel_raster.v','tests/reference_v11/panel_raster.v','tests/tb_panel_lcd.sv'])
s=simulate(p,'tb_panel_lcd.log');assert 'PASS panel LCD' in s,s
print(s,flush=True)
