from iverilog_runner import compile_sim,simulate
for top,src in [('tb_panel_spi',['src/s3_spi_link.v']),('tb_panel_visuals',['src/panel_raster.v','src/verification/verification_visuals.v','D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v'])]:
 p=compile_sim(top,src+['tests/'+top+'.sv']);s=simulate(p,top+'.log');assert 'PASS panel' in s,s;print(s,flush=True)
