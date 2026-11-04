from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent


def change(source, before, after):
    if source.count(before)!=1:
        raise ValueError('Unexpected timing-repair anchor: '+before)
    return source.replace(before,after)


def add(path, source):
    if path.exists():
        raise ValueError(f'Refusing to overwrite {path}')
    print('*** Add File: '+str(path).replace('\\','/'))
    print('\n'.join('+'+line for line in source.splitlines()))


def main():
    print('*** Begin Patch')
    source = (PROJECT/'src/effects/master_space_fx.v').read_text()
    add(ROOT/'space_gold.v',source.replace('module master_space_fx(','module master_space_fx_gold('))
    source=change(source,'    reg signed [15:0] lfo;', '''    reg signed [15:0] lfo;
    (* syn_preserve=1 *) reg signed [15:0] lfo_operand;
    reg [6:0] depth_operand;''')
    source=change(source,'delay_samples<=2400;phase<=0;lfo<=0;motion<=0;', 'delay_samples<=2400;phase<=0;lfo<=0;motion<=0;lfo_operand<=0;depth_operand<=0;')
    source=change(source,"                    motion<=lfo*$signed({1'b0,chorus_depth});",'                    lfo_operand<=lfo;depth_operand<=chorus_depth;')
    source=change(source,'                    state<=2;\n                end\n                2:begin', '''                    state<=11;
                end
                11:begin motion<=lfo_operand*$signed({1'b0,depth_operand});state<=2;end
                2:begin''')
    add(ROOT/'master_space_fx.v',source)
    source=(PROJECT/'audio_r11b/scratch_cache.v').read_text()
    source=change(source,'    wire [31:0] fill_by_voice,error_by_voice;', '    wire [31:0] response_match_by_voice,error_by_voice;')
    source=change(source,'    wire fill=|fill_by_voice;\n    wire reset_lines=(flush&&!previous_flush)||(previous_ready&&!memory_ready);', '''    wire reset_lines=(flush&&!previous_flush)||(previous_ready&&!memory_ready);
    wire response_selected=response_bank==bank;
    wire error_eligible=live&&rsp_valid&&!response_write&&!reset_lines&&
        !(response_selected&&(invalidate||write_accept));
    wire fill=error_eligible&&(|response_match_by_voice);''')
    source=change(source,'        wire filling=live&&rsp_valid&&!response_write&&response_matches&&\n            !invalidating&&!writing&&!reset_lines;', '        wire filling=fill&&response_matches;')
    source=change(source,'assign fill_by_voice[voice_index]=filling;', 'assign response_match_by_voice[voice_index]=response_matches;')
    source=change(source,'assign error_by_voice[voice_index]=filling&&response_last&&!first_beat;', 'assign error_by_voice[voice_index]=response_matches&&response_last&&!first_beat;')
    source=change(source,'if(|error_by_voice)protocol_fault<=1;', 'if(error_eligible&&(|error_by_voice))protocol_fault<=1;')
    add(ROOT/'scratch_cache.v',source)
    target=PROJECT/'guitar_ddr_violin_r15.gprj'
    source=target.read_text()
    updated=change(source,'src/effects/master_space_fx.v','violin_r15/master_space_fx.v')
    updated=change(updated,'audio_r11b/scratch_cache.v','violin_r15/scratch_cache.v')
    print('*** Update File: '+str(target).replace('\\','/')+'\n@@')
    print('\n'.join('-'+line for line in source.splitlines()))
    print('\n'.join('+'+line for line in updated.splitlines()))
    print('*** End Patch')


if __name__=='__main__':
    main()
