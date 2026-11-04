from iverilog_runner import compile_sim,simulate
cases=[('tb_panel_inputs',['src/panel_inputs.v']),('tb_panel_pitch',['src/panel_pitch.v']),('tb_panel_controller',['src/panel_controller.v'])]
for top,sources in cases:
 p=compile_sim(top,sources+['tests/'+top+'.sv'])
 text=simulate(p,top+'.log');assert 'PASS panel' in text and 'ERROR' not in text,text
 print(text,flush=True)
