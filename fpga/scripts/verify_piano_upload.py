from pathlib import Path
import sys
r=Path(__file__).resolve().parents[1];sys.path.insert(0,str(r/'host'))
from piano_ddr_loader import chunk_packet,command
from iverilog_runner import compile_sim,simulate
raw=(r/'host/assets/piano_sms_ddr.bin').read_bytes()
packets=b''.join(chunk_packet(i,raw[i*256:(i+1)*256]) for i in range(1100))
malicious=(command(2,6,0,127)+command(5,60,110,1)+command(0x50,0,127,0)+command(0x91,1,0,0))*11
malicious=malicious[:256].ljust(256,b'\xa5')
evil=chunk_packet(0,malicious)+chunk_packet(1,malicious)[:-1]+bytes([chunk_packet(1,malicious)[-1]^1])
for name,data in [('piano_upload_packets.hex',packets),('piano_upload_evil.hex',evil)]:
 (r/'tests/runtime_temp'/name).write_text(''.join(f'{b:02x}\n' for b in data))
p=compile_sim('tb_piano_upload',['src/guitar_uart_trigger.v','src/piano/piano_ddr_bank.v','tests/piano/piano_packet_memory.sv','tests/piano/tb_piano_upload.sv'])
s=simulate(p,'piano_upload.log')
assert 'PASS piano upload' in s,s
print(s,flush=True)
