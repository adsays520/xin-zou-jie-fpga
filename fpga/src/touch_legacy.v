// Logical key 0..125: row=fret 0..20, columns=string 6..1.
// Only the already-CRC-checked logical snapshot enters here.
module touch_to_command_legacy #(
    parameter integer PIANO_GATE_CLKS=6000000
)(
    input wire clk,input wire rst_n,input wire enabled,
    input wire [127:0] keys,input wire [1:0] instrument,
    input wire hall_mode,input wire [5:0] hall_mask,input wire [47:0] hall_velocity,
    input wire [29:0] hall_frets,
    input wire hall_valid,output wire hall_ready,
    output wire [29:0] selected_frets,
    output reg [47:0] command_data,output reg command_valid,
    input wire command_ready
);
    reg [125:0] committed;
    reg [6:0] scan_index;
    reg [1:0] last_instrument;
    reg [5:0] pending_hall,gate_active,gate_expired;
    reg [47:0] pending_velocity;
    reg [29:0] pending_frets;
    reg [$clog2(PIANO_GATE_CLKS+1)-1:0] gate_timer[0:5];
    reg [5:0] gate_timer_start;
    reg [6:0] gate_note[0:5];
    reg [1:0] gate_action;
    reg [2:0] gate_action_column;
    reg [6:0] gate_action_note;
    reg [127:0] selection_keys;
    reg selection_busy;
    reg [4:0] selection_row;
    reg [4:0] selection_work[0:5],selected[0:5];
    integer i,k,expired_column,pick_column;
    genvar g;
    reg [7:0] pick_note;
    wire pressed=enabled&&!hall_mode&&keys[scan_index];
    wire [4:0] fret=scan_index/6;
    wire [2:0] column=scan_index%6;
    wire [2:0] string_number=6-column;
    reg [6:0] base_midi;
    reg [7:0] opcode,p0,p1,p2;
    assign hall_ready=pending_hall==0;
    generate for(g=0;g<6;g=g+1)begin:out_frets
        assign selected_frets[g*5+:5]=selected[g];
    end endgenerate
    function [6:0] midi_base;
        input integer col;
        begin case(col)
            0:midi_base=40;1:midi_base=45;2:midi_base=50;
            3:midi_base=55;4:midi_base=59;default:midi_base=64;
        endcase end
    endfunction
    task emit;
        input [7:0] op,a,b,c;
        begin command_data<={8'ha5,op,a,b,c,(8'ha5^op^a^b^c)};command_valid<=1;end
    endtask
    always @*begin
        expired_column=-1;pick_column=-1;
        for(k=5;k>=0;k=k-1)begin
            if(gate_active[k]&&(gate_expired[k]||!hall_mode||!enabled))expired_column=k;
            if(pending_hall[k])pick_column=k;
        end
        pick_note=0;
        if(pick_column>=0)pick_note=midi_base(pick_column)+pending_frets[pick_column*5+:5];
        case(column)
            0:base_midi=40;1:base_midi=45;2:base_midi=50;
            3:base_midi=55;4:base_midi=59;default:base_midi=64;
        endcase
        if(instrument==1)begin
            opcode=8'h05;p0=base_midi+fret;p1=100;p2={7'd0,pressed};
        end else begin
            opcode=8'h02;p0={5'd0,string_number};p1={3'd0,fret};p2=100;
        end
    end
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            committed<=0;scan_index<=0;command_data<=0;command_valid<=0;last_instrument<=0;
            pending_hall<=0;pending_velocity<=0;pending_frets<=0;gate_active<=0;gate_expired<=0;gate_action<=0;
            gate_timer_start<=0;
            gate_action_column<=0;gate_action_note<=0;
            selection_keys<=0;selection_busy<=0;selection_row<=0;
            for(i=0;i<6;i=i+1)begin
                gate_timer[i]<=0;gate_note[i]<=0;selection_work[i]<=0;selected[i]<=0;
            end
        end else if(instrument!=last_instrument)begin
            // Top already clears old voices on timbre changes.
            committed<=0;scan_index<=0;command_valid<=0;last_instrument<=instrument;
            gate_active<=0;gate_expired<=0;pending_hall<=0;gate_action<=0;
            gate_timer_start<=0;
        end else begin
            gate_timer_start<=0;
            // Recompute six highest held frets over 21 clocks, not a long
            // combinational priority chain. Latch all six results together.
            if(!selection_busy&&selection_keys!=keys)begin
                selection_keys<=keys;selection_busy<=1;selection_row<=0;
                for(i=0;i<6;i=i+1)selection_work[i]<=0;
            end else if(selection_busy)begin
                for(i=0;i<6;i=i+1)begin
                    if(selection_keys[selection_row*6+i])selection_work[i]<=selection_row;
                    if(selection_row==20)selected[i]<=selection_keys[120+i] ? 5'd20 : selection_work[i];
                end
                if(selection_row==20)selection_busy<=0;
                else selection_row<=selection_row+1'b1;
            end
            for(i=0;i<6;i=i+1)begin
                if(gate_timer_start[i])gate_timer[i]<=PIANO_GATE_CLKS-1;
                else if(gate_timer[i]!=0)gate_timer[i]<=gate_timer[i]-1'b1;
                // Predict the zero reached by this edge. Register the wide
                // comparison before priority selection / 126-key write CE.
                gate_expired[i]<=gate_timer_start[i]?(PIANO_GATE_CLKS<=1):(gate_timer[i]<=1);
            end
            if(hall_valid&&hall_ready)begin
                pending_hall<=enabled&&hall_mode ? hall_mask : 6'd0;
                pending_velocity<=hall_velocity;
                pending_frets<=hall_frets;
            end
            if(!hall_mode||!enabled)pending_hall<=0;
            if(command_valid&&command_ready)begin
                command_valid<=0;
                if(gate_action==1)begin
                    gate_active[gate_action_column]<=1;
                    gate_note[gate_action_column]<=gate_action_note;
                    gate_timer_start[gate_action_column]<=1;
                    // Starting a new gate overrides the previous idle zero.
                    gate_expired[gate_action_column]<=0;
                end else if(gate_action==2)gate_active[gate_action_column]<=0;
            end
            if(!command_valid)begin
                gate_action<=0;
                if(expired_column>=0)begin
                    emit(8'h05,{1'b0,gate_note[expired_column]},8'd1,8'd0);
                    gate_action<=2;gate_action_column<=expired_column;
                end else if(hall_mode&&pending_hall!=0)begin
                    if(!enabled)pending_hall<=0;
                    else begin
                        if(instrument==2&&pick_column>=4)pending_hall[pick_column]<=0;
                        else if(instrument==1&&gate_active[pick_column])begin
                            emit(8'h05,{1'b0,gate_note[pick_column]},8'd1,8'd0);
                            gate_action<=2;gate_action_column<=pick_column;
                        end else begin
                            if(instrument==1)begin
                                emit(8'h05,pick_note,pending_velocity[pick_column*8+:8],8'd1);
                                gate_action<=1;gate_action_column<=pick_column;gate_action_note<=pick_note;
                            end else emit(8'h02,8'd6-pick_column,{3'd0,pending_frets[pick_column*5+:5]},pending_velocity[pick_column*8+:8]);
                            pending_hall[pick_column]<=0;
                        end
                    end
                end else begin
                if(pressed!=committed[scan_index])begin
                    committed[scan_index]<=pressed;
                    // Bass intentionally uses only strings 6/5/4/3.
                    if((instrument==1||pressed)&&!(instrument==2&&string_number<3))begin
                        command_data<={8'ha5,opcode,p0,p1,p2,(8'ha5^opcode^p0^p1^p2)};
                        command_valid<=1;
                    end
                end
                scan_index<=scan_index==125 ? 0 : scan_index+1'b1;
                end
            end
        end
    end
endmodule
