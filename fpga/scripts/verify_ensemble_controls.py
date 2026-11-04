from iverilog_runner import compile_sim,simulate
shared=['src/guitar_uart_trigger.v']
touch=['src/touch_to_command.v','src/touch_legacy.v','violin_r15/violin_touch_control.v']
suites=[('tb_s3_link',['src/s3_spi_link.v']),('tb_pluck_event_queue',['src/pluck_event_queue.v']),
 ('tb_touch_to_command',touch),('tb_s3_ingress',['src/s3_control_ingress.v']+shared),('tb_s3_bulk_ingress',['src/s3_control_ingress.v']+shared),('tb_violin_controls',shared+touch)]
for top,sources in suites:
    p=compile_sim(top,sources+[f'tests/{top}.sv']);s=simulate(p,top+'_ensemble.log')
    assert 'PASS ' in s and 'ERROR' not in s,s[-4000:]
    print(s.strip(),flush=True)
