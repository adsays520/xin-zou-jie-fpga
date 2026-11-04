import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
sys.path.insert(0, str(PROJECT / 'experiments/violin_v3'))
from fixed_model import Settings, compile_tables


class Program:
    def __init__(self):
        self.states = []

    def step(self, name, body):
        self.states.append((name, body))

    def mul(self, name, left, right, shift, body, add='64\'sd0'):
        self.step(name, f"mul_left <= {left}; mul_right <= {right}; mul_add <= {add}; mul_shift <= 6'd{shift}; return_state <= S_{name}_DONE; state <= S_ALU_MUL;")
        self.step(name + '_DONE', body)

    def fit(self, target, width=32, unsigned=False):
        lower = 0 if unsigned else -(1 << (width - 1))
        upper = (1 << width) - 1 if unsigned else (1 << (width - 1)) - 1
        return f"if (alu_result < {signed64(lower)} || alu_result > {signed64(upper)}) overflow_o <= 1'b1; {target} <= alu_result;"

    def render(self):
        names = [name for name, body in self.states]
        if len(names) > 256:
            raise ValueError('State register capacity exceeded')
        constants = '\n'.join(f'localparam S_{name} = {index};' for index, name in enumerate(names))
        cases = []
        for index, (name, body) in enumerate(self.states):
            following = names[index + 1] if index + 1 < len(names) else 'IDLE'
            cases.append(f'S_{name}: begin\n state <= S_{following};\n {body}\nend')
        return constants, '\n'.join(cases)


def signed64(value):
    return f"-64'sd{-value}" if value < 0 else f"64'sd{value}"


def build(tables):
    program = Program()
    program.step('BOOT', "neck_we <= 1; neck_waddr <= boot_index; neck_wdata <= 0; if (boot_index < 128) begin bridge_we <= 1; bridge_waddr <= boot_index[6:0]; bridge_wdata <= 0; history_we <= 1; history_waddr <= boot_index[6:0]; history_wdata <= 0; end if (boot_index == 511) state <= S_BOOT_END; else begin boot_index <= boot_index + 1'b1; state <= S_BOOT; end")
    program.step('BOOT_END', "ready_o <= 1; state <= S_IDLE;")
    program.step('IDLE', "if (frame_request) begin frame_request <= 0; job_busy <= 1; job_clocks <= 0; substep <= 0; state <= S_ENV; end else if (fifo_pop) begin event_data <= event_fifo[fifo_read]; state <= S_COMMAND_LOOKUP; end else state <= S_IDLE;")
    program.step('COMMAND_LOOKUP', "note_parameters <= note_rom[event_data[13:7]]; velocity_parameters <= velocity_rom[event_data[6:0]];")
    program.step('COMMAND_APPLY', "state <= S_IDLE; if (event_data[16]) gate <= 0; else if (!event_data[14]) begin if (event_data[13:7] == current_key) gate <= 0; end else if (event_data[13:7]>=55 && event_data[13:7]<=100 && event_data[6:0]!=0) begin current_key <= event_data[13:7]; target_period <= note_parameters[31:0]; target_pressure <= note_parameters[63:32]; target_velocity <= velocity_parameters[31:0]; target_loudness <= velocity_parameters[63:32]; if (!started || (!gate && envelope < 17)) begin period <= note_parameters[31:0]; pressure <= note_parameters[63:32]; velocity <= velocity_parameters[31:0]; residue[0]<=0; residue[1]<=0; residue[2]<=0; end else if (!event_data[15]) rebow_remaining <= REBOW_SAMPLES; if (!event_data[15] || !gate) begin note_age<=0; vibrato_entry<=0; end gate<=1; started<=1; end else invalid_event_o<=1;")
    program.step('ENV', "if (rebow_remaining != 0) begin rebow_remaining <= rebow_remaining - 1'b1; envelope <= envelope > REBOW_STEP ? envelope-REBOW_STEP : 0; end else if (gate) envelope <= envelope >= CONTROL_ONE-ATTACK_STEP ? CONTROL_ONE : envelope+ATTACK_STEP; else envelope <= envelope > RELEASE_STEP ? envelope-RELEASE_STEP : 0;")
    for index, (current, target, alpha) in enumerate((('period', 'target_period', 'GLIDE_ALPHA'), ('pressure', 'target_pressure', 'CONTROL_ALPHA'), ('velocity', 'target_velocity', 'CONTROL_ALPHA'), ('loudness', 'target_loudness', 'CONTROL_ALPHA'), ('loss_gain', '(envelope != 0 ? LOSS_GAIN_ON : LOSS_GAIN_OFF)', 'LOSS_ALPHA'))):
        program.mul('SMOOTH' + str(index), f'$signed({target})-$signed({current})', alpha, 24,
                    f"if ($signed({current})+alu_result < -64'sd2147483648 || $signed({current})+alu_result > 64'sd2147483647) overflow_o<=1; {current} <= $signed({current})+alu_result; residue[{index}] <= alu_accumulator - (alu_result <<< 24);",
                    add=f'{{{{32{{residue[{index}][31]}}}},residue[{index}]}}')
    program.step('VIB_FETCH', "if (note_age >= VIBRATO_DELAY) vibrato_entry <= vibrato_entry >= CONTROL_ONE-VIBRATO_ENTRY_STEP ? CONTROL_ONE : vibrato_entry+VIBRATO_ENTRY_STEP; vibrato_address <= phase[31:22]; phase_fraction <= phase[21:0];")
    program.step('VIB_WAIT', 'vibrato_first <= vibrato_rom[vibrato_address]; vibrato_second <= vibrato_rom[(vibrato_address+1\'b1)&10\'h3ff];')
    program.mul('VIB_INTERP', '$signed({1\'b0,vibrato_second})-$signed({1\'b0,vibrato_first})', '$signed({1\'b0,phase_fraction})', 22, 'ratio_full <= $signed({1\'b0,vibrato_first}) + alu_result;')
    program.mul('VIB_ENTRY', 'ratio_full-32\'sd4194304', 'vibrato_entry', 24, 'ratio <= 32\'sd4194304 + alu_result;')
    program.mul('MODULATE', 'period', 'ratio', 22, program.fit('modulated_period', 26, True))
    program.mul('BOW_POSITION', 'modulated_period', 'BOW_POSITION', 24, 'bridge_delay <= alu_result[25:0]; neck_delay <= modulated_period - alu_result[25:0];')
    program.step('WAVE_FETCH', "neck_raddr <= neck_write - neck_delay[24:16]; neck_older_addr <= neck_write - neck_delay[24:16] - 1'b1; bridge_raddr <= bridge_write - bridge_delay[22:16]; bridge_older_addr <= bridge_write - bridge_delay[22:16] - 1'b1; if (neck_delay < 65536 || neck_delay > (510<<16) || bridge_delay < 65536 || bridge_delay > (126<<16)) overflow_o<=1;")
    program.step('WAVE_WAIT', '')
    program.mul('NECK_INTERP', '$signed(neck_older)-$signed(neck_recent)', '$signed({1\'b0,neck_delay[15:0]})', 16, 'neck_out <= $signed(neck_recent) + alu_result;')
    program.mul('BRIDGE_INTERP', '$signed(bridge_older)-$signed(bridge_recent)', '$signed({1\'b0,bridge_delay[15:0]})', 16, 'bridge_out <= $signed(bridge_recent) + alu_result;')
    program.mul('LOSS', '(bridge_out <<< 6)-loss_state', 'STRING_FEED', 22, 'loss_state <= loss_state + alu_result;')
    program.mul('REFLECTION', 'loss_state', 'loss_gain', 30, 'bridge_reflection <= envelope != 0 ? -alu_result : -(alu_accumulator < 0 ? -((-alu_accumulator)>>>30) : (alu_accumulator>>>30));')
    program.mul('BOW_VELOCITY', 'velocity', 'envelope', 28, 'relative_velocity <= alu_result - bridge_reflection + neck_out; if (envelope == 0) begin interaction<=0; state<=S_WAVE_WRITE; end')
    program.mul('FRICTION_SHAPE', 'relative_velocity+32\'sd1049', '(32\'sd83886080-(pressure<<<2))', 24, 'shaped <= alu_result < 0 ? -alu_result : alu_result;')
    program.step('FRICTION_CLAMP', "if (shaped <= FRICTION_LOWER) begin reflection <= 18'd256901; state<=S_INTERACTION; end else if (shaped >= FRICTION_UPPER) begin reflection <= 18'd2621; state<=S_INTERACTION; end")
    program.mul('FRICTION_INDEX', 'shaped-FRICTION_LOWER', 'FRICTION_SCALE', 20, "friction_position <= alu_result >= (1023<<16) ? (1023<<16) : alu_result; ")
    program.step('FRICTION_FETCH', "friction_address <= friction_position[25:16] >= 1023 ? 1022 : friction_position[25:16]; friction_fraction <= friction_position[25:16]>=1023 ? 17'd65536 : {1'b0,friction_position[15:0]};")
    program.step('FRICTION_WAIT', "friction_first <= friction_rom[friction_address]; friction_second <= friction_rom[friction_address+1'b1];")
    program.mul('FRICTION_INTERP', '$signed({1\'b0,friction_second})-$signed({1\'b0,friction_first})', '$signed({1\'b0,friction_fraction})', 16, 'reflection <= friction_first + alu_result;')
    program.mul('INTERACTION', 'relative_velocity', '$signed({1\'b0,reflection})', 18, program.fit('interaction', 26))
    program.step('WAVE_WRITE', "neck_we<=1; neck_waddr<=neck_write; neck_wdata<=bridge_reflection+interaction; bridge_we<=1; bridge_waddr<=bridge_write; bridge_wdata<=-neck_out+interaction; if ($signed(bridge_reflection)+$signed(interaction)>8388607 || $signed(bridge_reflection)+$signed(interaction)<-8388608 || -$signed(neck_out)+$signed(interaction)>8388607 || -$signed(neck_out)+$signed(interaction)<-8388608) overflow_o<=1; neck_write<=neck_write+1'b1; bridge_write<=bridge_write+1'b1; phase<=phase+PHASE_INCREMENT; note_age<=note_age+1'b1;")
    program.mul('VOICE_GAIN', 'bridge_out', 'loudness', 18, program.fit('voice_output', 32))
    program.step('BODY_START', "body_value <= voice_output <<< 4; body_section<=0; if ($signed(voice_output)>134217727 || $signed(voice_output)<-134217728) overflow_o<=1;")
    program.step('BODY_FETCH', 'body_feed0<=body_rom0[body_section];body_feed1<=body_rom1[body_section];body_feed2<=body_rom2[body_section];body_feedback1<=body_rom3[body_section];body_feedback2<=body_rom4[body_section];')
    program.mul('BODY_B0', '$signed(body_feed0)', 'body_value', 22, program.fit('body_output'), add='$signed(body_state0[body_section]) <<< 22')
    program.mul('BODY_B1', '$signed(body_feed1)', 'body_value', 0, 'body_acc <= alu_result;', add='$signed(body_state1[body_section]) <<< 22')
    program.mul('BODY_A1', '-$signed(body_feedback1)', 'body_output', 22, program.fit('body_state0[body_section]'), add='body_acc')
    program.mul('BODY_B2', '$signed(body_feed2)', 'body_value', 0, 'body_acc <= alu_result;')
    program.mul('BODY_A2', '-$signed(body_feedback2)', 'body_output', 22, program.fit('body_state1[body_section]'), add='body_acc')
    program.step('BODY_NEXT', "body_value<=body_output; if(body_section<5) begin body_section<=body_section+1'b1; state<=S_BODY_FETCH; end")
    program.mul('DC', 'dc_previous_output', 'DC_POLE', 22, 'dc_residue <= alu_accumulator - (alu_result <<< 22); dc_output <= $signed(body_value)-$signed(dc_previous_input)+alu_result; dc_previous_input<=body_value; dc_previous_output <= $signed(body_value)-$signed(dc_previous_input)+alu_result;', add='$signed(dc_residue)')
    program.mul('OUTPUT_GAIN', 'dc_output', 'OUTPUT_GAIN', 31, program.fit('internal_sample', 24))
    program.step('HISTORY_WRITE', "history_we<=1; history_waddr<=history_write; history_wdata<=internal_sample; internal_valid_o<=1; internal_sample_o<=internal_sample;")
    program.step('SUBSTEP_NEXT', "history_write<=history_write+1'b1; if(!substep)begin substep<=1; state<=S_ENV;end else begin fir_tap<=0; fir_acc<=0; state<=S_FIR_FETCH;end")
    program.step('FIR_FETCH', "history_raddr <= history_write - 1'b1 - fir_tap; history_other_addr <= history_write - 1'b1 - (7'd94-fir_tap);")
    program.step('FIR_WAIT', '')
    program.step('FIR_PREADD', "fir_preadd <= fir_tap==47 ? $signed(history_recent) : $signed({history_recent[23],history_recent})+$signed({history_older[23],history_older}); fir_coefficient<=fir_coeff[fir_tap];")
    program.step('FIR_MULTIPLY', 'fir_product <= fir_preadd * fir_coefficient;')
    program.step('FIR_ACCUMULATE', "fir_acc<=fir_acc+$signed(fir_product); if(fir_tap==47)state<=S_FIR_FINAL;else begin fir_tap<=fir_tap+1'b1;state<=S_FIR_FETCH;end")
    program.step('FIR_FINAL', "pending_output<=sat24(rne(fir_acc,6'd23)); if(rne(fir_acc,6'd23)>8388607 || rne(fir_acc,6'd23)<-8388608)overflow_o<=1; pending_valid<=1; produced_o<=1; job_busy<=0; last_cycles_o<=job_clocks; state<=S_IDLE;")
    program.step('ALU_MUL', 'alu_product <= mul_left * mul_right; state<=S_ALU_ADD;')
    program.step('ALU_ADD', "if (mul_shift==0) begin alu_result<=alu_product+mul_add; state<=return_state; end else begin alu_accumulator<=alu_product+mul_add; state<=S_ALU_SHIFT; end")
    program.step('ALU_SHIFT', "alu_shifted<=alu_accumulator>>>mul_shift; alu_increment<= ((alu_accumulator & ((64'd1<<mul_shift)-1)) > (64'd1<<(mul_shift-1))) || (((alu_accumulator & ((64'd1<<mul_shift)-1)) == (64'd1<<(mul_shift-1))) && ((alu_accumulator>>>mul_shift)&1)); state<=S_ALU_ROUND;")
    program.step('ALU_ROUND', 'alu_result<=alu_shifted+alu_increment; state<=return_state;')
    constants, cases = program.render()
    reset = {name: 0 for name in ('boot_index', 'ready_o', 'frame_request', 'job_busy', 'job_clocks', 'substep', 'pending_valid', 'pending_output', 'sample_o', 'sample_valid_o', 'produced_o', 'internal_valid_o', 'internal_sample_o', 'deadline_miss_o', 'overflow_o', 'invalid_event_o', 'last_cycles_o', 'event_data', 'note_parameters', 'velocity_parameters', 'target_velocity', 'velocity', 'target_loudness', 'loudness', 'loss_state', 'envelope', 'note_age', 'phase', 'vibrato_entry', 'rebow_remaining', 'gate', 'started', 'neck_write', 'bridge_write', 'history_write', 'neck_we', 'bridge_we', 'history_we', 'dc_previous_input', 'dc_previous_output', 'dc_residue')}
    reset.update(period=tables.periods[14], target_period=tables.periods[14], pressure=tables.pressure[14], target_pressure=tables.pressure[14], loss_gain=tables.loss_gain_off, current_key=69)
    reset_text='\n'.join(f'{name} <= {value};' for name, value in reset.items())
    scalar_names={'ATTACK_STEP':'attack_step','RELEASE_STEP':'release_step','REBOW_STEP':'rebow_step','REBOW_SAMPLES':'rebow_samples','VIBRATO_DELAY':'vibrato_delay_samples','VIBRATO_ENTRY_STEP':'vibrato_entry_step','PHASE_INCREMENT':'phase_increment','CONTROL_ALPHA':'control_alpha','GLIDE_ALPHA':'glide_alpha','LOSS_ALPHA':'loss_alpha','LOSS_GAIN_ON':'loss_gain_on','LOSS_GAIN_OFF':'loss_gain_off','STRING_FEED':'string_feed','DC_POLE':'dc_pole','OUTPUT_GAIN':'output_gain','BOW_POSITION':'bow_position','FRICTION_LOWER':'friction_lower','FRICTION_UPPER':'friction_upper','FRICTION_SCALE':'friction_scale'}
    parameters='\n'.join(f"localparam signed [31:0] {name}=32'sd{getattr(tables, field)};" for name,field in scalar_names.items())
    template=(ROOT/'core_template.txt').read_text(encoding='utf-8')
    return template.replace('@PARAMETERS@',parameters).replace('@CONSTANTS@',constants).replace('@RESET@',reset_text).replace('@CASES@',cases), len(program.states)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--assets', action='store_true')
    args=parser.parse_args()
    tables=compile_tables(Settings.load())
    if args.assets:
        directory=ROOT/'rom';directory.mkdir(exist_ok=True)
        notes=[0]*128; velocities=[0]*128
        for index in range(46):notes[index+55]=(tables.pressure[index]<<32)|tables.periods[index]
        for index in range(127):velocities[index+1]=(tables.loudness[index]<<32)|tables.drive[index]
        for name,values,width in [('notes.hex',notes,64),('velocities.hex',velocities,64),('friction.hex',tables.friction,18),('vibrato.hex',tables.vibrato_ratio,24),('body.hex',[value for section in tables.body for value in section],24),('fir.hex',tables.fir[:48],24)]:
            (directory/name).write_text(''.join(f'{value&((1<<width)-1):0{(width+3)//4}x}\n' for value in values),encoding='ascii')
        (directory/'tables.json').write_text(json.dumps(asdict(tables),indent=2)+'\n',encoding='utf-8')
        for index in range(5):
            (directory/f'body{index}.hex').write_text(''.join(f'{section[index]&0xffffff:06x}\n' for section in tables.body),encoding='ascii')
    source,count=build(tables)
    target = ROOT / 'violin_core.v'
    print('*** Begin Patch')
    if target.exists():
        print('*** Update File: '+str(target).replace('\\','/')+'\n@@')
        print('\n'.join('-'+line for line in target.read_text(encoding='utf-8').splitlines()))
    else:
        print('*** Add File: '+str(target).replace('\\','/'))
    print('\n'.join('+'+line for line in source.splitlines()))
    print('*** End Patch')


if __name__=='__main__':main()
