module piano_sd_boot #(
    parameter integer CLOCK_HZ=50000000,parameter integer KEEP_STAGE=1,parameter MULTI_FILE=0
)(
    input wire clk,rst_n,cancel,memory_ready,
    input wire next_file,file_select,
    input wire card_ready,input wire [7:0] card_error,card_byte,
    input wire card_byte_valid,card_sector_done,
    output reg card_read_start,output reg [31:0] card_read_lba,
    output reg upload_begin,upload_valid,upload_commit,upload_error,
    output wire [10:0] upload_index,output reg [2047:0] upload_data,
    input wire upload_ready,input wire [10:0] upload_count,
    input wire bank_initialized,bank_fault,
    output reg active,finished,output reg [7:0] error,output wire loading,
    output wire stage_valid,output wire [7:0] stage_index,stage_data
);
    localparam WAIT_CARD=0,READ_START=1,READ_WAIT=2,FETCH=3,FETCH_WAIT=4,
        PROCESS=5,PARSED=6,CLUSTER_ADDRESS=7,PUBLISH=8,WAIT_UPLOAD=9,
        WAIT_BEGIN=10,VERIFY=11,FINISHED=12,GEOMETRY=13,CLUSTERS=14,CHECK_BPB=15;
    localparam BOOT=0,DIRECTORY=1,FAT=2,PAYLOAD=3;
    reg [3:0] state;reg [1:0] kind;
    reg [7:0] sector[0:511];reg [8:0] read_address,write_address,scan_index;
    reg [7:0] read_byte;reg [9:0] byte_count;
    always @(posedge clk)begin
        if(card_byte_valid&&state==READ_WAIT&&byte_count<512)sector[write_address]<=card_byte;
        read_byte<=sector[read_address];
    end
    reg [15:0] bps,reserved,root_entries,fat16,total16,extflags,fs_version,signature;
    reg [7:0] spc,nfats;
    reg [31:0] total_sectors,fat_sectors,root_cluster;
    reg [7:0] mbr_type;reg [31:0] mbr_lba,mbr_size,partition_candidate,partition_size;
    reg partitioned;reg [31:0] volume_lba,volume_size;
    reg [31:0] fat_start,data_start,cluster_count,cluster;
    reg [2:0] spc_shift;reg [7:0] sectors_per_cluster,sector_in_cluster,root_hops;
    reg [8:0] fat_offset;reg [31:0] fat_entry;reg fat_for_file;
    reg entry_match,file_found;reg [7:0] entry_attribute;
    reg [31:0] entry_cluster,entry_size,file_cluster;
    reg [10:0] chunk_index;
    reg bank_started,abort_pending;reg [7:0] abort_code;reg [31:0] watchdog;
    reg selected_file;
    wire drum_file=MULTI_FILE&&selected_file;
    wire [87:0] file_name=drum_file?"DRUMS   BIN":"PIANOSMSBIN";
    wire [31:0] file_bytes=drum_file?32'd3072:32'd281600;
    wire [10:0] last_chunk=drum_file?11'd11:11'd1099;
    assign upload_index=chunk_index;
    assign loading=bank_started;
    assign stage_valid=active&&!cancel&&!abort_pending&&state==PROCESS&&kind==PAYLOAD;
    assign stage_index=scan_index[7:0];assign stage_data=read_byte;
    function [2:0] cluster_shift;
        input [7:0] value;
        begin case(value)
            2:cluster_shift=1;4:cluster_shift=2;8:cluster_shift=3;16:cluster_shift=4;
            32:cluster_shift=5;64:cluster_shift=6;128:cluster_shift=7;default:cluster_shift=0;
        endcase end
    endfunction
    function [7:0] filename_byte;
        input [3:0] index;
        begin filename_byte=index<11?file_name[87-index*8-:8]:8'd0;end
    endfunction
    reg [32:0] overhead,computed_clusters,volume_end;
    wire [39:0] fat_capacity={1'b0,fat_sectors,7'd0};
    wire valid_bpb=signature==16'haa55&&bps==512&&spc!=0&&spc<=128&&
        (spc&(spc-1'b1))==0&&reserved!=0&&(nfats==1||nfats==2)&&root_entries==0&&
        fat16==0&&total16==0&&fat_sectors!=0&&fs_version==0&&overhead<total_sectors&&
        computed_clusters>=65525&&computed_clusters<=33'h00ffffff5&&
        fat_capacity>=computed_clusters+2&&root_cluster>=2&&root_cluster<computed_clusters+2&&
        !volume_end[32]&&(!partitioned||total_sectors<=volume_size)&&
        (!extflags[7]||extflags[3:0]<nfats);
    wire [8:0] mbr_offset=scan_index-9'd446;
    wire [4:0] entry_offset=scan_index[4:0];
    task fail;
        input [7:0] code;
        begin
            error<=code;active<=0;finished<=1;state<=FINISHED;
            card_read_start<=0;upload_begin<=0;upload_valid<=0;upload_commit<=0;
            upload_error<=bank_started&&!bank_initialized&&!bank_fault;
        end
    endtask
    task next_fat;
        input for_file;
        begin
            fat_for_file<=for_file;fat_offset<={cluster[6:0],2'b00};
            card_read_lba<=fat_start+(cluster>>7);kind<=FAT;state<=READ_START;
        end
    endtask
    always @(posedge clk or negedge rst_n)begin
        if(!rst_n)begin
            state<=WAIT_CARD;kind<=BOOT;active<=1;finished<=0;error<=0;selected_file<=0;
            card_read_start<=0;card_read_lba<=0;upload_begin<=0;upload_valid<=0;
            upload_commit<=0;upload_error<=0;upload_data<=0;
            read_address<=0;write_address<=0;scan_index<=0;byte_count<=0;
            bps<=0;reserved<=0;root_entries<=0;fat16<=0;total16<=0;extflags<=0;fs_version<=0;signature<=0;
            spc<=0;nfats<=0;total_sectors<=0;fat_sectors<=0;root_cluster<=0;
            mbr_type<=0;mbr_lba<=0;mbr_size<=0;partition_candidate<=0;partition_size<=0;
            partitioned<=0;volume_lba<=0;volume_size<=0;fat_start<=0;data_start<=0;cluster_count<=0;
            cluster<=0;spc_shift<=0;sectors_per_cluster<=0;sector_in_cluster<=0;root_hops<=0;
            fat_offset<=0;fat_entry<=0;fat_for_file<=0;entry_match<=0;file_found<=0;
            entry_attribute<=0;entry_cluster<=0;entry_size<=0;file_cluster<=0;
            chunk_index<=0;bank_started<=0;abort_pending<=0;abort_code<=8'h7f;watchdog<=0;
            overhead<=0;computed_clusters<=0;volume_end<=0;
        end else begin
            card_read_start<=0;upload_begin<=0;upload_valid<=0;upload_commit<=0;upload_error<=0;
            if(active&&watchdog<CLOCK_HZ*10)watchdog<=watchdog+1'b1;
            if(!(cancel||abort_pending))case(state)
                WAIT_CARD:if(card_ready&&memory_ready)begin card_read_lba<=0;kind<=BOOT;state<=READ_START;end
                READ_START:if(card_ready)begin
                    card_read_start<=1;byte_count<=0;write_address<=0;file_found<=0;
                    if(kind==BOOT)begin
                        bps<=0;reserved<=0;root_entries<=0;fat16<=0;total16<=0;extflags<=0;fs_version<=0;signature<=0;
                        spc<=0;nfats<=0;total_sectors<=0;fat_sectors<=0;root_cluster<=0;
                        mbr_type<=0;mbr_lba<=0;mbr_size<=0;partition_candidate<=0;partition_size<=0;
                    end
                    if(kind==FAT)fat_entry<=0;
                    state<=READ_WAIT;
                end
                READ_WAIT:begin
                    if(card_byte_valid)begin byte_count<=byte_count+1'b1;write_address<=write_address+1'b1;end
                    if(card_sector_done)begin
                        if(byte_count!=512)fail(8'h21);
                        else begin scan_index<=kind==FAT?fat_offset:9'd0;state<=FETCH;end
                    end
                end
                FETCH:begin read_address<=scan_index;state<=FETCH_WAIT;end
                FETCH_WAIT:state<=PROCESS;
                PROCESS:begin
                    if(kind==BOOT)begin
                        case(scan_index)
                            11:bps[7:0]<=read_byte;12:bps[15:8]<=read_byte;13:spc<=read_byte;
                            14:reserved[7:0]<=read_byte;15:reserved[15:8]<=read_byte;16:nfats<=read_byte;
                            17:root_entries[7:0]<=read_byte;18:root_entries[15:8]<=read_byte;
                            19:total16[7:0]<=read_byte;20:total16[15:8]<=read_byte;
                            22:fat16[7:0]<=read_byte;23:fat16[15:8]<=read_byte;
                            32:total_sectors[7:0]<=read_byte;33:total_sectors[15:8]<=read_byte;
                            34:total_sectors[23:16]<=read_byte;35:total_sectors[31:24]<=read_byte;
                            36:fat_sectors[7:0]<=read_byte;37:fat_sectors[15:8]<=read_byte;
                            38:fat_sectors[23:16]<=read_byte;39:fat_sectors[31:24]<=read_byte;
                            40:extflags[7:0]<=read_byte;41:extflags[15:8]<=read_byte;
                            42:fs_version[7:0]<=read_byte;43:fs_version[15:8]<=read_byte;
                            44:root_cluster[7:0]<=read_byte;45:root_cluster[15:8]<=read_byte;
                            46:root_cluster[23:16]<=read_byte;47:root_cluster[31:24]<=read_byte;
                            510:signature[7:0]<=read_byte;511:signature[15:8]<=read_byte;
                        endcase
                        if(scan_index>=446&&scan_index<=509)case(mbr_offset[3:0])
                            4:mbr_type<=read_byte;
                            8:mbr_lba[7:0]<=read_byte;9:mbr_lba[15:8]<=read_byte;
                            10:mbr_lba[23:16]<=read_byte;11:mbr_lba[31:24]<=read_byte;
                            12:mbr_size[7:0]<=read_byte;13:mbr_size[15:8]<=read_byte;14:mbr_size[23:16]<=read_byte;
                            15:if(partition_candidate==0&&(mbr_type==8'h0b||mbr_type==8'h0c)&&mbr_lba!=0)begin
                                partition_candidate<=mbr_lba;partition_size<={read_byte,mbr_size[23:0]};end
                        endcase
                        if(scan_index==511)state<=PARSED;
                        else begin scan_index<=scan_index+1'b1;state<=FETCH;end
                    end else if(kind==DIRECTORY)begin
                        if(entry_offset==0)begin
                            entry_match<=read_byte==filename_byte(0);entry_cluster<=0;entry_size<=0;entry_attribute<=0;
                        end else if(entry_offset<=10&&read_byte!=filename_byte(entry_offset[3:0]))entry_match<=0;
                        case(entry_offset)
                            11:entry_attribute<=read_byte;
                            20:entry_cluster[23:16]<=read_byte;21:entry_cluster[31:24]<=read_byte;
                            26:entry_cluster[7:0]<=read_byte;27:entry_cluster[15:8]<=read_byte;
                            28:entry_size[7:0]<=read_byte;29:entry_size[15:8]<=read_byte;30:entry_size[23:16]<=read_byte;
                        endcase
                        if(entry_offset==0&&read_byte==0)fail(8'h32);
                        else if(entry_offset==31&&entry_match&&(entry_attribute&8'h18)==0&&entry_attribute!=8'h0f)begin
                            if({read_byte,entry_size[23:0]}!=file_bytes)fail(8'h33);
                            else if((entry_cluster&32'h0fffffff)<2||(entry_cluster&32'h0fffffff)>=cluster_count+2)fail(8'h34);
                            else begin file_cluster<=entry_cluster&32'h0fffffff;file_found<=1;state<=PARSED;end
                        end else if(scan_index==511)state<=PARSED;
                        else begin scan_index<=scan_index+1'b1;state<=FETCH;end
                    end else if(kind==FAT)begin
                        fat_entry[scan_index[1:0]*8+:8]<=read_byte;
                        if(scan_index==fat_offset+3)state<=PARSED;
                        else begin scan_index<=scan_index+1'b1;state<=FETCH;end
                    end else begin
                        if(KEEP_STAGE)upload_data[scan_index[7:0]*8+:8]<=read_byte;
                        if(scan_index[7:0]==255)state<=PUBLISH;
                        else begin scan_index<=scan_index+1'b1;state<=FETCH;end
                    end
                end
                PARSED:case(kind)
                    BOOT:state<=GEOMETRY;
                    DIRECTORY:if(file_found)begin
                        cluster<=file_cluster;chunk_index<=0;upload_begin<=1;bank_started<=1;state<=WAIT_BEGIN;
                    end else if({1'b0,sector_in_cluster}+1<{1'b0,sectors_per_cluster})begin
                        sector_in_cluster<=sector_in_cluster+1'b1;card_read_lba<=card_read_lba+1'b1;state<=READ_START;
                    end else if(root_hops==127)fail(8'h35);
                    else begin root_hops<=root_hops+1'b1;next_fat(0);end
                    FAT:if(fat_entry[27:0]<2||fat_entry[27:0]>=cluster_count+2||fat_entry[27:0]>=28'hffffff7)fail(8'h36);
                        else begin cluster<={4'd0,fat_entry[27:0]};kind<=fat_for_file?PAYLOAD:DIRECTORY;state<=CLUSTER_ADDRESS;end
                    default:fail(8'h37);
                endcase
                GEOMETRY:begin
                    overhead<={17'd0,reserved}+({1'b0,fat_sectors}<<(nfats==2?1:0));
                    volume_end<={1'b0,volume_lba}+{1'b0,total_sectors};state<=CLUSTERS;
                end
                CLUSTERS:begin computed_clusters<=({1'b0,total_sectors}-overhead)>>cluster_shift(spc);state<=CHECK_BPB;end
                CHECK_BPB:if(valid_bpb)begin
                        fat_start<=volume_lba+reserved+((extflags[7]&&extflags[3:0]==1)?fat_sectors:32'd0);
                        data_start<=volume_lba+overhead[31:0];cluster_count<=computed_clusters[31:0];
                        cluster<=root_cluster;spc_shift<=cluster_shift(spc);sectors_per_cluster<=spc;
                        kind<=DIRECTORY;root_hops<=0;state<=CLUSTER_ADDRESS;
                    end else if(!partitioned&&signature==16'haa55&&partition_candidate!=0&&partition_size!=0)begin
                        partitioned<=1;volume_lba<=partition_candidate;volume_size<=partition_size;
                        card_read_lba<=partition_candidate;state<=READ_START;
                    end else fail(8'h30);
                CLUSTER_ADDRESS:begin
                    card_read_lba<=data_start+((cluster-2)<<spc_shift);sector_in_cluster<=0;state<=READ_START;
                end
                WAIT_BEGIN:if(upload_ready&&upload_count==0)begin bank_started<=1;kind<=PAYLOAD;state<=CLUSTER_ADDRESS;end
                PUBLISH:if(upload_ready)begin upload_valid<=1;state<=WAIT_UPLOAD;end
                WAIT_UPLOAD:if(upload_count==chunk_index+1'b1)begin
                    if(chunk_index==last_chunk)begin upload_commit<=1;state<=VERIFY;end
                    else begin
                        chunk_index<=chunk_index+1'b1;
                        if(scan_index==255)begin scan_index<=256;state<=FETCH;end
                        else if({1'b0,sector_in_cluster}+1<{1'b0,sectors_per_cluster})begin
                            sector_in_cluster<=sector_in_cluster+1'b1;card_read_lba<=card_read_lba+1'b1;state<=READ_START;
                        end else next_fat(1);
                    end
                end
                VERIFY:if(bank_initialized)begin active<=0;finished<=1;state<=FINISHED;end
                default:begin end
            endcase
            if(active&&card_error!=0)begin abort_pending<=1;abort_code<=8'h10|card_error;end
            if(active&&bank_started&&bank_fault)fail(8'h40);
            if(active&&cancel)begin abort_pending<=1;abort_code<=8'h7f;end
            if(active&&watchdog==CLOCK_HZ*10-1)begin abort_pending<=1;abort_code<=8'h7e;end
            // Never interrupt a DDR write/readback transaction halfway through.
            if(active&&(cancel||abort_pending)&&!upload_valid&&(!bank_started||upload_ready||bank_initialized||bank_fault))
                fail(cancel?8'h7f:abort_code);
            if(MULTI_FILE&&next_file&&finished)begin
                state<=WAIT_CARD;kind<=BOOT;active<=1;finished<=0;error<=0;selected_file<=file_select;
                bank_started<=0;abort_pending<=0;watchdog<=0;chunk_index<=0;
                partitioned<=0;volume_lba<=0;volume_size<=0;partition_candidate<=0;partition_size<=0;
            end
        end
    end
endmodule
