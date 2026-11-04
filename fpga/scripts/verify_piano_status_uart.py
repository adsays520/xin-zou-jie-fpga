from iverilog_runner import compile_sim,simulate
p=compile_sim('tb_piano_status_uart',['src/verification/verification_telemetry.v','src/piano/piano_bank_status_tx.v','tests/piano/tb_piano_status_uart.sv'])
s=simulate(p,'piano_status_uart.log')
assert 'PASS DDR status UART' in s,s
print(s,flush=True)
