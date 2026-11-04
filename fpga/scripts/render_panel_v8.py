from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from iverilog_runner import compile_sim,simulate,ROOT
p=compile_sim('tb_panel_raster',['src/panel_raster.v','tests/tb_panel_raster.sv'])
s=simulate(p,'panel_raster.log');assert 'PASS panel raster' in s,s
out=ROOT/'tests/results/panel_previews';out.mkdir(exist_ok=True)
images=[]
for i in range(5):
 q=np.frombuffer((ROOT/f'tests/results/panel_page_{i}.rgb565').read_bytes(),dtype='>u2').astype(np.uint16).reshape(160,128)
 rgb=np.stack([((q>>11)&31)*255//31,((q>>5)&63)*255//63,(q&31)*255//31],axis=-1).astype(np.uint8)
 im=Image.fromarray(rgb).resize((384,480),Image.Resampling.NEAREST);im.save(out/f'page_{i}.png');images.append(im)
canvas=Image.new('RGB',(384*5,480),(0,0,0))
for i,im in enumerate(images):canvas.paste(im,(i*384,0))
canvas.save(out/'control_pages.png');print(s);print(out/'control_pages.png')
