from run_rtl import *
src=ROOT.parent/'fpga/src'
exe=compile_sim('tb_mobile_ingress',[ROOT/'tb_mobile_ingress.v',src/'s3_control_ingress.v',src/'guitar_uart_trigger.v']);print(run([TOOLS/'bin/vvp.exe',exe],'ingress_result.log'))
