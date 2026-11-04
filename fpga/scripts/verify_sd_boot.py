"""Exercise the actual FAT loader and DDR bank with sparse, fragmented FAT32 media."""
from pathlib import Path
import struct,json
from iverilog_runner import compile_sim,simulate,ROOT
out=ROOT/'tests/runtime_temp';out.mkdir(exist_ok=True)
bank=(ROOT/'sd_card/PIANOSMS.BIN').read_bytes()
(out/'sd_expected.hex').write_text(''.join(f'{v:02x}\n' for v in bank))
def image(case,spc=1,mbr=True):
    base=2048 if mbr else 0;total=131072 if spc==1 else 1048576
    fat=1024;data=base+32+2*fat;sectors={}
    def sector(lba):return sectors.setdefault(lba,bytearray(512))
    def put(b,o,v,n=4):b[o:o+n]=v.to_bytes(n,'little')
    if mbr:
        b=sector(0);b[510:]=b'\x55\xaa';b[446+32+4]=0x0c
        put(b,446+32+8,base);put(b,446+32+12,total)
    b=sector(base);b[510:]=b'\x55\xaa';put(b,11,512,2);b[13]=spc
    put(b,14,32,2);b[16]=2;put(b,32,total);put(b,36,fat);put(b,44,2)
    put(b,40,0x81 if spc>1 else 0,2)
    fatbase=base+32+(fat if spc>1 else 0)
    def chain(c,n):put(sector(fatbase+c//128),(c%128)*4,n|0xa0000000)
    def address(c,s=0):return data+(c-2)*spc+s
    # The first root cluster is full; the file lives in a fragmented successor.
    for s in range(spc):
        b=sector(address(2,s))
        for off in range(0,512,32):b[off]=0xe5
    chain(2,700);chain(700,0x0fffffff)
    b=sector(address(700));b[:96]=b'\xe5'+bytes(31)+b'PIANOSMSBIN'+bytes([0x0f])+bytes(20)+b'PIANOSMSBIN'+bytes([0x10])+bytes(20)
    off=96;b[off:off+11]=b'PIANOSMSBIN';b[off+11]=0x20
    put(b,off+26,3,2);put(b,off+28,len(bank))
    clusters=[3+7*n for n in range((550+spc-1)//spc)]
    for n,c in enumerate(clusters):
        chain(c,clusters[n+1] if n+1<len(clusters) else 0x0fffffff)
        for s in range(spc):
            i=n*spc+s
            if i<550:sector(address(c,s))[:]=bank[i*512:(i+1)*512]
    if case==2:put(b,off+28,len(bank)-1)
    if case==3:put(sector(fatbase+3//128),(3%128)*4,0x0ffffff8)
    if case==4:b[off]=0
    if case==5:sector(address(3))[0]^=1
    if case==7:put(sector(base),36,1) # FAT cannot address all clusters
    items=sorted(sectors.items());assert len(items)<800
    (out/f'sd{case}_lba.hex').write_text(''.join(f'{v:08x}\n' for v in [x[0] for x in items]+[0xffffffff]*(800-len(items))))
    payload=b''.join(x[1] for x in items)+bytes((800-len(items))*512)
    (out/f'sd{case}_data.hex').write_text(''.join(f'{v:02x}\n' for v in payload))
for case in range(8):image(case,8 if case==1 else 1,case!=1)
exe=compile_sim('tb_sd_boot',['src/guitar_uart_trigger.v','src/storage/piano_sd_boot.v','src/piano/piano_ddr_bank.v','tests/piano/piano_packet_memory.sv','tests/storage/tb_sd_boot.sv'])
logs=[]
for case in range(8):
    s=simulate(exe,f'sd_boot_case{case}.log',f'+CASE={case}')
    assert 'PASS SD BOOT' in s and 'ERROR' not in s,s[-4000:]
    print(s.strip(),flush=True);logs.append(s.strip())
(ROOT/'tests/results/sd_boot_summary.json').write_text(json.dumps({'cases':8,'results':logs},indent=2))
