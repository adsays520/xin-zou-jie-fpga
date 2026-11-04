from iverilog_runner import compile_sim,simulate
p=compile_sim('tb_piano_ddr_transport',['src/excitation_ddr/async_fifo64.v','src/piano/piano_ddr_transport.v','tests/piano/ddr_parameter_app_model.sv','tests/piano/tb_piano_ddr_transport.sv','D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v'])
s=simulate(p,'piano_ddr_transport.log')
assert 'PASS DDR transport' in s,s
print(s,flush=True)
