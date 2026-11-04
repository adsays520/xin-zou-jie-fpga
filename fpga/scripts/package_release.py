"""Release only the matching DDR firmware, parameter bank and verified sources."""
from pathlib import Path
import hashlib,json,re,zipfile,runpy
r=Path(__file__).resolve().parents[1];out=r/'tests/results';target='ensemble_rom_block_r6_20261020'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks={'rom_block_build_r6.log': 'Merged build timing PASS: setup=0 hold=0', 'ensemble_host_tests.log': 'Ran 113 tests', 'ensemble_ui_render.log': 'PASS: GUI render', 'packed_road.log': 'PASS PACKED ROAD', 'guitar_memory_audio.log': 'PASS GUITAR MEMORY AUDIO', 'violin_core_31000.log': 'frames=31000 internal=62000 max_cycles=852', 'tb_s3_link_ensemble.log': 'PASS S3 SPI', 'tb_pluck_event_queue_ensemble.log': 'PASS pluck_event_queue', 'tb_touch_to_command_ensemble.log': 'PASS touch/pick', 'tb_s3_ingress_ensemble.log': 'PASS ingress', 'tb_s3_bulk_ingress_ensemble.log': 'PASS S3 BULK INGRESS', 'tb_violin_controls_ensemble.log': 'PASS R15 controls', 'piano_upload.log': 'PASS piano upload: 1100 host packets', 'ensemble_board.log': 'PASS ENSEMBLE BOARD', 'sd_spi_case0.log': 'PASS SD SPI case=0', 'sd_spi_case1.log': 'PASS SD SPI case=1', 'sd_spi_case2.log': 'PASS SD SPI case=2', 'sd_spi_case3.log': 'PASS SD SPI case=3', 'sd_spi_case4.log': 'PASS SD SPI case=4', 'sd_boot_case0.log': 'PASS SD BOOT case=0', 'sd_boot_case1.log': 'PASS SD BOOT case=1', 'sd_boot_case2.log': 'PASS SD BOOT case=2', 'sd_boot_case3.log': 'PASS SD BOOT case=3', 'sd_boot_case4.log': 'PASS SD BOOT case=4', 'sd_boot_case5.log': 'PASS SD BOOT case=5', 'sd_boot_case6.log': 'PASS SD BOOT case=6', 'sd_boot_case7.log': 'PASS SD BOOT case=7'}
checks['verification_rom_netlist.log']='PASS VERIFICATION ROM NETLIST'
for name,marker in checks.items():assert marker in (out/name).read_text(encoding='utf-8'),name
assert re.search(r'Ran 113 tests[\s\S]*\bOK\b',(out/'ensemble_host_tests.log').read_text())
assert 'GowinSynthesis finish' in (out/'rom_block_build_r6.log').read_text()
full_log=(out/'rom_block_build_r6.log').read_text(encoding='utf-8')
(out/'accepted_synthesis.log').write_text(full_log[:full_log.index('GowinSynthesis finish')+len('GowinSynthesis finish')]+'\n',encoding='utf-8')
selection=dict(fresh_synthesis_performed=True,synthesized_target=target,pnr_target=target,
 netlist_sha256=sha(r/f'impl/gwsynthesis/{target}.vg'),synthesis_log='tests/results/accepted_synthesis.log',
 reason='Shared SD/PC parameter staging, corrected FAT/cancellation/isolation, plus four block ROMs replacing logic sine lookup; normalized RTL and isolated post-synthesis primitives verified',
 pnr_options=dict(place_option=2,route_option=2,replicate_resources=1))
(out/'build_selection_proof.json').write_text(json.dumps(selection,indent=2),encoding='utf-8')
runpy.run_path(str(r/'scripts/verify_piano_sms_import.py'),run_name='__main__')
baseline=json.loads((r/'docs/BASELINE_DDR_RELEASE.json').read_text(encoding='utf-8'))
for name,value in baseline['unchanged_algorithm_files'].items():assert sha(r/name)==value,name
source_hashes=json.loads((out/'build_source_sha256.json').read_text())
for name,value in source_hashes.items():assert sha(r/name)==value,name
build_after=json.loads((out/'build_source_matches_after.json').read_text())
assert build_after['passed'] and build_after['sources']==source_hashes,'Built source snapshot does not match delivery'
host=json.loads((out/'host_source_validation.json').read_text())
assert host['passed'] and host['tests']==113
for name,value in host['sources'].items():assert sha(r/name)==value,('host source changed after testing',name)
for top in ('tb_piano_upload','tb_sd_boot','tb_sd_card','tb_ensemble_board','tb_s3_link','tb_pluck_event_queue','tb_touch_to_command','tb_s3_ingress','tb_s3_bulk_ingress','tb_violin_controls','tb_verification_rom_netlist'):
 record=json.loads((out/(top+'_source_sha256.json')).read_text())
 for name,value in record.items():
  path=Path(name) if Path(name).is_absolute() else r/name
  assert sha(path)==value,('tested source changed',top,name)
unit=json.loads((r/'docs/verification_rom_implementation.json').read_text())
assert sha(r/unit['captured_netlist'])==unit['unit_synthesis_netlist_sha256']
for name,value in json.loads((out/'rom_unit_syn_source_sha256.json').read_text()).items():assert sha(r/name)==value,('unit synthesis source',name)
for name,value in json.loads((out/'verification_rom_netlist_source_sha256.json').read_text()).items():
 path=Path(name) if Path(name).is_absolute() else r/name
 assert sha(path)==value,('unit post-synthesis source',name)
def normalized_rtl(p):return re.sub(r'\s+','',re.sub(r'/\*[\s\S]*?\*/|//[^\n]*','',p.read_text()))
assert sha(r/unit['reference_rtl'])==unit['reference_rtl_sha256']
assert normalized_rtl(r/unit['reference_rtl'])==normalized_rtl(r/'src/verification/verification_dds.v')
for name,record in json.loads((out/'retained_component_test_binding.json').read_text()).items():
 assert sha(r/name)==record['source_sha256'],('retained component differs from tested module',name)
evidence=json.loads((out/'test_evidence_manifest.json').read_text())
for name,value in evidence['files'].items():assert sha(out/name)==value,('test evidence changed',name)

audio=json.loads((out/'pipeline_audio_equivalence.json').read_text())
assert audio.get('passed') and sha(r/audio['file'])==audio['current_sha256']==audio['baseline_sha256'],'pipeline changed audition'
firmware=r/f'impl/pnr/{target}.fs';assert firmware.stat().st_size>100000
netlist=r/f'impl/gwsynthesis/{target}.vg';assert netlist.stat().st_size>100000
html=(r/f'impl/pnr/{target}_tr_content.html').read_text(errors='replace')
for label in ('Setup','Hold'):
 m=re.search(r'Numbers of '+label+r' Violated Endpoints</td>\s*<td>([0-9]+)</td>',html)
 assert m and int(m[1])==0,(label,m[1] if m else 'missing')
clock_table=re.search(r'<a name="Clock_Report">[\s\S]*?</table>',html);assert clock_table,'clock summary missing'
clock_periods={name:float(period) for name,period in re.findall(r'<td>(sys_clk|mem400|ddr_user100|ddr_ref100)</td>\s*<td>(?:Base|Generated)</td>\s*<td>([0-9.]+)</td>',clock_table[0])}
assert clock_periods=={'sys_clk':20.0,'mem400':2.5,'ddr_user100':10.0,'ddr_ref100':10.0},clock_periods
report=(r/f'impl/pnr/{target}.rpt.txt').read_text(errors='replace')
expected_pads=json.loads((r/'docs/piano_sms_import.json').read_text(encoding='utf-8'))['expected_audio_pinout']
expected_pads.update(spi_sclk='P21',spi_mosi='U17',spi_miso='U24',spi_cs_n='V23',fpga_irq='AC26',fpga_ready='U25',sd_mosi='D24',sd_cs='B25',sd_clk='D23',sd_miso='H23')
pads={m[1]:(m[2],m[3]) for m in re.finditer(r'^\s*(\w+(?:\[\d+\])?)\s*\|\s*-\s*\|\s*([A-Z]+\d+)/\d+\s*\|\s*([YN])\s*\|',report,re.M)}
for name,pad in expected_pads.items():assert pads.get(name)==(pad,'Y'),('audio pin changed or unconstrained',name,pads.get(name),pad)
resources={}
for label in ('Logic','Register','CLS','BSRAM','DSP'):
 m=re.search(r'^\s*'+label+r'\s*\|\s*([0-9.]+)/([0-9.]+)',report,re.M);assert m,label
 used,total=map(float,m.groups());assert used<=total,label
 resources[label]={'used':used,'available':total}
assert resources['BSRAM']['available']==340
proof={'file':netlist.relative_to(r).as_posix(),'sha256':sha(netlist)}
(out/'pnr_netlist_sha256.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
validation={'date':'2026-10-20','firmware':firmware.relative_to(r).as_posix(),'firmware_sha256':sha(firmware),
 'synthesis_netlist':proof,'top':'guitar_audio_ddr_top','device':'GW5AST-LV138FPG676AES',
 'audio_clock_mhz':50,'ddr_user_clock_mhz':100,'ddr_memory_clock_mhz':400,
 'setup_violated_endpoints':0,'hold_violated_endpoints':0,'physical_resources':resources,'reported_clock_period_ns':clock_periods,
 'host_tests':113,'baseline_piano_bank_cases':352,'baseline_piano_integer_compared_frames_per_case':2048,
 'verification_rom_post_synthesis_clocks':327745,'verification_rom_table_addresses':1024,'sd_spi_cases':5,'sd_fat_ddr_cases':8,'shared_parameter_staging':True,'test_source_binding':True,'violin_compared_frames':31000,'violin_internal_samples':62000,'violin_max_cycles':852,
 'sd_scope':'read-only FAT32, fragmented MBR/superfloppy root PIANOSMS.BIN, 281600 synthesis parameter bytes, full DDR readback',
 'esp_firmware':'existing R15 compatible; reference sources only, not built/flashed here',
 'piano_voices':16,'piano_max_clocks':899,'audio_frame_clocks':1042,
 'parameter_bank_bytes':281600,'parameter_upload_chunks':1100,'parameter_crc32':2644131955,
 'parameter_location':'real DDR native x32 base 0x100000; current-voice caches on chip',
 'delay_history':'32768 stereo S16 frames in DDR native x32 base 0x200000',
 'phy_simulation_scope':'SD sector provider, guitar delay/excitation banks and DDR PHY/PLL modeled in whole-board test; actual vendor guitar RAM/core equivalence and SD physical SPI/init/CRC16 separately passed; real context RAM, FAT, DDR FIFO/transport/bank, physical ESP SPI, UART, audio/mixer/final DAC retained',
 'baseline_space_equivalence_scope':'70064 stereo frames compared bit-for-bit to original RAM implementation; idle clocks collapsed, transaction completion checked against 1042-clock deadline; continuous competing piano traffic',
 'hardware_flash_and_listening':'not performed; ESP reference not built/flashed','reset_pin':'K16 low active; previous U4 is no longer reset','audio_pinout':expected_pads,'all_audio_pins_explicitly_constrained':True,
 'checks':checks}
(out/'release_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# 全乐器固件验收结果（2026-10-20）','','位流：'+firmware.relative_to(r).as_posix(),'','顶层 guitar_audio_ddr_top；GW5AST-LV138FPG676AES；音频50 MHz，DDR用户接口100 MHz，存储时钟400 MHz。','','| 资源 | 占用 | 可用 |','| --- | ---: | ---: |']
for label,data in resources.items():lines.append('| '+label+' | '+str(data['used'])+' | '+str(data['available'])+' |')
lines+=['','所有已约束时钟的建立／保持时间违例均为0。',
'','本轮通过：113项上位机测试；小提琴31000帧／62000内部采样逐位核对，最慢852时钟；32声部RAM存取与6弦各3个代表品位的吉他实际原语音频比较（另检查全部126个品位延迟长度）；ESP CRC、会话、重试去重、背压、触摸与拨杆；真实115200串口266字节参数包指令隔离；5组SD SPI与8组FAT32／DDR加载；完整串口参数上传及8800记录回读。',
'','校音正弦表改用4块RAM：全部1024地址、327745个时钟及32326个非零立体声帧的独立综合网表／实际厂商原语与原RTL比较通过；归一化RTL一致，输出数值与延迟不变。',
'','SD物理SPI初始化与CRC16、实际RAM原语及吉他核心逐位比较单独验证；整机使用扇区卡模型及吉他延迟／激励存储行为模型（可选 --vendor-guitar-banks 跑实际原语），经真实FAT32、真实双时钟FIFO和DDR原生接口完成8800参数写入与读回，随后检查钢琴、算法鼓、Bass、吉他音高、串口小提琴、ESP触摸与模式切换至最终DAC输出。仿真以行为模型替代加密DDR PHY和PLL，不代替硬件电气验证。',
'','SD文件281600字节，CRC32 9D9A4073；只读FAT32，无卡时上位机备用加载；尚未自动写卡保存旋钮或混音预设。复位K16，功放使能Y25；ESP与SD全部新增接口均核对最终管脚约束。',
'','未烧录FPGA或ESP，未进行实板听音。ESP参考源码未在本轮编译，现有R15 ESP固件可继续使用。',
'','钢琴拟合参数、试听及其数值检查沿用上一版封存结果；本轮只将它们用于音色保持核对，未冒充新测试。历史文档中的资源不作为本版验收。',
'','位流SHA256：'+sha(firmware),'网表SHA256：'+sha(netlist)]
(r/'docs/固件验收结果.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
memory=json.loads((r/'docs/memory_import.json').read_text());memory['new_full_design_resource_status']='fresh synthesis/PNR passed, setup=0 hold=0';memory['new_physical_bram']=resources['BSRAM'];memory['report']=f'impl/pnr/{target}.rpt.txt'
(r/'docs/memory_import.json').write_text(json.dumps(memory,ensure_ascii=False,indent=2),encoding='utf-8')
imports=json.loads((r/'docs/esp_violin_import.json').read_text())
for name,item in imports.items():assert sha(r/name)==item['current_sha256'],name
for name,value in json.loads((r/'esp32_ref/SOURCE_SHA256.json').read_text()).items():assert sha(r/'esp32_reference'/name)==value,name
assert (r/'sd_card/PIANOSMS.BIN').read_bytes()==(r/'host/assets/piano_sms_ddr.bin').read_bytes()
result_files=set(checks)|{'build_source_sha256.json','pnr_netlist_sha256.json','release_validation.json','piano_sms_import_check.json','sd_boot_summary.json','pipeline_audio_equivalence.json','accepted_synthesis.log','build_selection_proof.json','build_source_matches_after.json','host_source_validation.json','retained_component_test_binding.json','shared_stage_fast_checks.log','test_evidence_manifest.json','verification_rom_netlist_source_sha256.json','rom_unit_syn_source_sha256.json','rom_unit_syn.log'}
for prefix in ('tb_packed_road','tb_guitar_memory_audio','tb_violin_core','tb_s3_link','tb_pluck_event_queue','tb_touch_to_command','tb_s3_ingress','tb_s3_bulk_ingress','tb_violin_controls','tb_piano_upload','tb_sd_boot','tb_sd_card','tb_ensemble_board','tb_verification_rom_netlist'):
 result_files|={prefix+'_compile.log',prefix+'_preprocess.log',prefix+'_source_sha256.json'}
# Historical entry points are deliberately excluded; the two current projects
# and build_merged.tcl use the DDR top and the current constraints.
legacy_scripts={'verify_piano_sms_top.py','verify_sms_ddr_board.py','verify_sms_ddr_board_r3.py','verify_merged_iverilog.py','verify_merged_xsim.py','verify_sms_ddr_board_r4.py'}
legacy_piano={'piano_additive_rom.v','piano_spectrum_rom.v','piano_poly16_tdm.v'}
legacy_previews={'piano_sms_A0_C4_C6_C7_C8.wav','piano_ddr_model_C2_C3_C4_C6_C7_C8.wav'}
legacy_tests={'tb_piano_sms_top.sv','tb_sms_ddr_board.sv','tb_sms_ddr_board_r3.sv','piano_sms_r3_pre_pipeline.v','tb_sms_ddr_board_r4.sv'}
files=[]
for p in sorted(r.rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(r);name=rel.as_posix()
 if any(part in ('__pycache__','runtime_temp','work','xsim.dir','.pytest_cache') for part in rel.parts):continue
 if p.suffix in ('.pyc','.vvp','.wdb','.jou','.user','.npz','.exe'):continue
 if name=='SHA256清单.json' or name=='docs/INTEGRATION_STATUS.md' or name.startswith('violin_r15/test_results/'):continue
 if len(rel.parts)==1:
  if p.suffix in ('.tcl','.gprj') and p.name not in ('build_merged.tcl','guitar_audio_low_speed.gprj','guitar_audio_merged.gprj','verification_rom_unit.gprj','rom_unit_syn.tcl'):continue
  if p.suffix in ('.log','.pb','.txt'):continue
 if name.startswith(('docs/history/','scripts/history/','tools/sms_analysis/','src/piano_pcm/')):continue
 if name=='docs/DDR任务状态.md' or name.startswith('constraints/route_guide.'):continue
 if name.startswith('src/excitation_ddr/') and p.name!='async_fifo64.v':continue
 if name in ('src/audio.cst','src/guitar_audio_fm_demo.sdc'):continue
 if name.startswith('src/piano/') and p.name in legacy_piano:continue
 if name.startswith('src/piano/sms/') and re.search(r'_[012]\.hex$',p.name):continue
 if name.startswith('scripts/') and (p.name in legacy_scripts or p.name.startswith('integrate_')):continue
 if name.startswith('preview/') and p.name in legacy_previews:continue
 if name.startswith('tests/') and p.name in legacy_tests:continue
 if name.startswith('impl/'):
  if not p.name.startswith(target):continue
  if p.suffix not in ('.fs','.html','.txt','.vg','.xml'):continue
 if name.startswith('tests/results/') and p.name not in result_files:continue
 files.append(p)
manifest={p.relative_to(r).as_posix():sha(p) for p in files}
for name in source_hashes:assert name in manifest,('missing build dependency',name)
for group in ('reference_files_retained_exact','baseline_unchanged_sources'):
 for name in json.loads((r/'docs/piano_sms_import.json').read_text(encoding='utf-8'))[group]:assert name in manifest,('missing audit file',name)
mf=r/'SHA256清单.json';mf.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');files.append(mf)
archive=r.parent/'全乐器_小提琴_ESP_板载SD_DDR_20261020.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in files:z.write(p,Path(r.name)/p.relative_to(r))
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for name,value in manifest.items():assert hashlib.sha256(z.read(r.name+'/'+name)).hexdigest()==value,name
 assert [n for n in z.namelist() if n.endswith('.fs')]==[r.name+'/impl/pnr/'+target+'.fs']
 assert not any('/src/piano_pcm/' in n or 'piano_loop/' in n or 'drum_sample_rom.v' in n for n in z.namelist())
print('PASS ENSEMBLE release ZIP:',archive,'bytes=',archive.stat().st_size,'files=',len(files),flush=True)
print('SHA256',sha(archive),flush=True)
