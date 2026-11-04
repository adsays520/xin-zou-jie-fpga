from run_rtl import *
src=ROOT.parent/'fpga/src'
for top,files in [('tb_s3_bulk',['s3_bulk_buffer.v']),('tb_s3_spi_mobile',['s3_spi_link.v'])]:
 exe=compile_sim(top,[ROOT/(top+'.v')]+[src/f for f in files]);print(run([TOOLS/'bin/vvp.exe',exe],top+'_result.log'))
