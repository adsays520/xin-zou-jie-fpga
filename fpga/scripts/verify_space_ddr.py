from iverilog_runner import compile_sim,simulate
p=compile_sim('tb_space_ddr_equivalence',['src/effects/master_space_fx.v','src/effects/stereo_ddr_delay.v','src/piano/piano_audio_ddr_arbiter.v','src/piano/piano_ddr_transport.v','src/excitation_ddr/async_fifo64.v','tests/ref/master_space_fx_pre_ddr.v','tests/piano/ddr_parameter_app_model.sv','tests/piano/tb_space_ddr_equivalence.sv','D:/Gowin/Gowin_V1.9.12.03_x64/IDE/simlib/gw5a/prim_sim.v'])
s=simulate(p,'space_ddr_equivalence.log')
assert 'PASS DDR space equivalence' in s,s
print(s,flush=True)
