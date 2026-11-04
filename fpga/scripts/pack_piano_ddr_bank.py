from pathlib import Path
import hashlib,json,zlib
ROOT=Path(__file__).resolve().parents[1]
def pack():
 p=ROOT/'src/piano/sms';d=ROOT/'src/piano/sms_ddr';d.mkdir(exist_ok=True)
 def words(name):return [int(x,16) for x in (p/name).read_text().split()]
 w=words('weights.hex');f=words('frequency.hex');t=words('transient.hex');n=words('noise.hex')
 assert (len(w),len(f),len(t),len(n))==(5632,5632,2816,352)
 image=[]
 for bank in range(352):
  image.extend(w[bank*16+m]|f[bank*16+m]<<192 for m in range(16))
  image.extend(t[bank*8+m] for m in range(8));image.append(n[bank])
 raw=b''.join(q.to_bytes(32,'little') for q in image)
 assert len(raw)==281600
 crc=zlib.crc32(raw)&0xffffffff
 (d/'bank_image.hex').write_text(''.join(f'{v:064x}\n' for v in image),encoding='ascii')
 (d/'bank_config.vh').write_text(f"`ifndef PIANO_BANK_CONFIG_VH\n`define PIANO_BANK_CONFIG_VH\n`define PIANO_BANK_CRC32 32'h{crc:08x}\n`endif\n",encoding='ascii')
 assets=ROOT/'host/assets';assets.mkdir(exist_ok=True)
 (assets/'piano_sms_ddr.bin').write_bytes(raw)
 manifest=dict(format='harmonic_sms_ddr_v1',bytes=len(raw),chunks=1100,chunk_bytes=256,
               records=8800,record_bytes=32,crc32=crc,sha256=hashlib.sha256(raw).hexdigest(),
               recordings_played=False)
 (assets/'piano_sms_ddr.json').write_text(json.dumps(manifest,indent=2))
 print('PASS packed DDR piano parameter bank',manifest,flush=True)
 return manifest
if __name__=='__main__':pack()
