from iverilog_runner import compile_sim,simulate
p=compile_sim("tb_drums_lifecycle",["src/drums/drum_synth.v","src/drums/kick_modal.v","src/performance_mixer.v","tests/tb_drums_lifecycle.sv"])
print(simulate(p,"drums_lifecycle.log"),flush=True)
