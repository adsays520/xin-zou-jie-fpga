from iverilog_runner import compile_sim,simulate
p=compile_sim("tb_drums_synth",["src/drums/drum_synth.v","src/drums/kick_modal.v","src/performance_mixer.v","tests/tb_drums_synth.sv"])
print(simulate(p,"drums_synth_smoke.log","+MODE=0"),flush=True)
