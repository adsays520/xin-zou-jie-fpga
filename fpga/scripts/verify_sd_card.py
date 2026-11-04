from iverilog_runner import compile_sim,simulate
p=compile_sim('tb_sd_card',['src/storage/sd_spi_byte.v','src/storage/sd_spi_card.v','tests/storage/tb_sd_card.sv'])
for case in range(5):
    s=simulate(p,f'sd_spi_case{case}.log',f'+CASE={case}')
    assert 'PASS SD SPI' in s and 'ERROR' not in s,s
    print(s.strip(),flush=True)
