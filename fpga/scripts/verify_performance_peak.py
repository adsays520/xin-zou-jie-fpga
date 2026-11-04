from iverilog_runner import compile_sim,simulate
p=compile_sim("tb_performance_peak",["src/performance_mixer.v","tests/tb_performance_peak.sv"])
print(simulate(p,"performance_peak.log"),flush=True)
