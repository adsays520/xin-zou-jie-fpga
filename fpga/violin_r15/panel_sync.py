"""CRC-protected FPGA state is relayed through S3 as a bounded ASCII status line."""
def decode_panel_line(line):
    parts=line.strip().split(',')
    if len(parts)!=36 or parts[:2]!=['PANEL','8']:
        return None
    try: page,motion,*values=map(int,parts[2:])
    except ValueError:return None
    if not 0<=page<8 or not 0<=motion<128 or len(values)!=32 or any(not 0<=v<=127 for v in values):return None
    maxima={0:4,1:10,6:5,9:1,10:1,11:1,18:96,19:4,25:4,26:20,27:10,28:50,30:1,31:1}
    if any(values[i]>maximum for i,maximum in maxima.items()):return None
    return page,motion,tuple(values)
