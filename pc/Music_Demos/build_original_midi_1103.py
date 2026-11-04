"""Reproducible original MIDI practice scores and matching Tang arrangements."""
from pathlib import Path
from dataclasses import dataclass, field
import hashlib
import json
import struct
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'drum_bass_pitch_20261013/violin_r15'
sys.path[:0] = [str(APP), str(APP.parent/'host'), str(APP.parent/'tools/python_deps')]
from midi_guide import read_midi, fingering
from arrangement_model import Project, Track, Clip, Note, BAR, PPQ
from arrangement_playback import compile_plan

OUT = ROOT / 'Music_Demos/MIDI_Originals_1103'
PROGRAM = {'guitar':25, 'piano':0, 'bass':33, 'violin':40}
DRUMS = {36:0,38:1,42:2,46:3,39:4,49:5,51:6,45:7,47:8,50:9,37:10,56:11}


def vlq(n):
    parts = [n & 127]
    while n >> 7:
        n >>= 7; parts.insert(0, (n & 127) | 128)
    return bytes(parts)


def chunk(tag, data):
    return tag + struct.pack('>I', len(data)) + data


@dataclass
class Part:
    label: str
    instrument: str
    channel: int
    notes: list = field(default_factory=list)
    program: int | None = None

    def add(self, beat, length, pitch, velocity):
        self.notes.append((round(beat*PPQ), max(1,round(length*PPQ)), pitch, max(1,min(127,velocity))))


def save(stem, title, bpm, bars, parts, guide, description, rock=False):
    total = bars * BAR
    tempo = round(60000000/bpm)
    conductor = b'\0\xff\x51\x03'+tempo.to_bytes(3,'big')+b'\0\xff\x58\x04\x04\x02\x18\x08'
    conductor += vlq(total)+b'\xff\x2f\0'
    chunks = [chunk(b'MTrk', conductor)]
    project = Project(name=title,bpm=bpm,bars=bars,loop_end=total,guitar_sustain=46 if rock else 52,violin_legato=True)
    project.parameters.update({'bus.guitar':68,'bus.piano':70,'bus.bass':55,'bus.violin':37,'bus.drums':88,
                               'guitar.amp':3 if rock else 0,'guitar.drive':60 if rock else 0,
                               'guitar.level':64 if rock else 80,'guitar.mix':100 if rock else 0,
                               'guitar.cabinet':int(rock),'guitar.compressor':0,'guitar.gate':0,
                               'space.delay_mix':0,'space.chorus_mix':0})
    expected = 0
    for part in parts:
        label = part.label.encode('utf8')
        buf = b'\0\xff\x03'+vlq(len(label))+label
        if part.instrument != 'drums':
            program = part.program if part.program is not None else PROGRAM[part.instrument]
            buf += b'\0'+bytes((0xC0|part.channel,program))
        events = []
        track = Track(instrument=part.instrument,name=part.label,level=100)
        clip = Clip(name=title,start=0,length=total)
        for at, duration, pitch, velocity in part.notes:
            end = min(total, at+duration)
            if at < 0 or end <= at: raise ValueError('Invalid generated note time')
            events.extend(((at,1,bytes((0x90|part.channel,pitch,velocity))),
                           (end,0,bytes((0x80|part.channel,pitch,0)))))
            clip.notes.append(Note(at,end-at,DRUMS[pitch] if part.instrument=='drums' else pitch,velocity))
            expected += 1
        previous = 0
        for tick, _, message in sorted(events):
            buf += vlq(tick-previous)+message; previous=tick
        buf += vlq(total-previous)+b'\xff\x2f\0'
        chunks.append(chunk(b'MTrk',buf))
        track.clips=[clip]; project.tracks.append(track)
    midi = b'MThd'+struct.pack('>IHHH',6,1,len(chunks),PPQ)+b''.join(chunks)
    path=OUT/(stem+'.mid');path.write_bytes(midi)
    parsed=read_midi(path)
    assert len(parsed.notes)==expected
    assert abs(parsed.duration-bars*4*60/bpm)<.001
    project.validate()
    plan=compile_plan(project,hardware=True,ensemble=True)
    project.save(OUT/(stem+'.tang.json'))
    # Validate exported projects through the public loader as well.
    loaded=Project.load(OUT/(stem+'.tang.json'))
    assert loaded.to_dict()==project.to_dict()
    selected=next(p for p in parts if p.label==guide)
    assert all(fingering(n[2]) is not None for n in selected.notes)
    edges=sorted([(n.start,1) for n in parsed.notes]+[(n.end,-1) for n in parsed.notes])
    active=peak=0
    for _, delta in edges: active+=delta;peak=max(peak,active)
    return dict(file=path.name,title=title,bpm=bpm,bars=bars,seconds=round(parsed.duration,2),
                tracks=[p.label for p in parts],guide_track=guide,notes=expected,peak_simultaneous_notes=peak,
                compiled_hardware_events=len(plan.events),description=description,
                sha256=hashlib.sha256(midi).hexdigest())


# E minor, C major, G major, D major; playable low guitar voicings.
CHORDS=[(40,[52,55,59,64]),(36,[48,52,55,60]),(43,[50,55,59,62]),(38,[50,54,57,62])]
MOTIFS=[(64,67,71,69,67,64,62),(64,67,72,71,67,64,60),
        (67,71,74,72,71,67,62),(66,69,74,72,69,66,62)]
RHYTHM=[(0,.65),(1,.4),(1.5,.4),(2,.65),(3,.35),(3.5,.2),(3.75,.2)]


def melody(part, bar, section=0, velocity=83, low=False):
    pitches=list(MOTIFS[bar%4])
    if section%2:
        pitches=pitches[2:]+pitches[:2]
    if bar%8==7: pitches=[66,69,67,66,64,62,64]
    if low: pitches=[p-12 for p in pitches]
    for i,((beat,duration),pitch) in enumerate(zip(RHYTHM,pitches)):
        part.add(bar*4+beat,duration,pitch,velocity+(4 if i==0 else -4 if i%2 else 0))


def rhythm(parts, bars, rock=False, gentle=False):
    guitar,bass,drums=parts
    for bar in range(bars):
        root,chord=CHORDS[bar%4]
        if guitar is not None:
            if rock:
                for beat in (0,.75,1.5,2,2.75,3.5):
                    for j,pitch in enumerate((root+12,root+19)):
                        guitar.add(bar*4+beat+j*.018,.32,pitch,83-j*5)
            else:
                sequence=[chord[0],chord[2],chord[1],chord[3],chord[0],chord[2],chord[1],chord[3]]
                for j,pitch in enumerate(sequence):guitar.add(bar*4+j*.5,.42,pitch,68+(6 if j%4==0 else 0))
        if bass is not None:
            for beat,length,pitch in [(0,.8,root),(1.5,.35,root+7),(2,.8,root),(3,.4,root+12),(3.5,.35,root+7)]:
                bass.add(bar*4+beat,length,pitch,79)
        if drums is not None:
            for j in range(8):drums.add(bar*4+j*.5,.08,42,54+(10 if j%2==0 else 0))
            for beat in (0,2,2.75) if rock else (0,2):drums.add(bar*4+beat,.12,36,99 if not gentle else 76)
            for beat in (1,3):drums.add(bar*4+beat,.12,38,96 if not gentle else 70)
            if bar%8==0:drums.add(bar*4,.22,49,78)
            if bar%8==7:
                for j,pitch in enumerate((38,47,45,50)):drums.add(bar*4+3+j*.25,.1,pitch,77+j*3)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    catalog=[]
    lead=Part('Guide - First lights','guitar',0)
    for bar in range(16):melody(lead,bar,bar//8,78,low=bar<8)
    catalog.append(save('01_First_Lights','灯轨初航',80,16,[lead],lead.label,'单旋律入门，前半低音区，后半高音区，适合检查跟灯映射。'))
    lead=Part('Guide - Repeated touches','piano',0)
    for bar in range(8):
        # Lowest-fret choices land on chip1: keys 22,17,29,24 respectively.
        pitch=(58,61,63,67)[bar%4]
        step=1 if bar<2 else .5 if bar<6 else .25
        for n in range(round(3/step)):lead.add(bar*4+n*step,step*.45,pitch,77+(n%3)*4)
        lead.add(bar*4+3.25,.3,(58,61,63,67)[(bar+1)%4],82)
    catalog.append(save('02_Echo_Retrigger','回声连击',96,8,[lead],lead.label,'针对1号板的键22/17/29/24，连击逐级加速，每小节留出恢复空隙；可调到50%练习。'))
    guitar=Part('Guide - Acoustic strums','guitar',0)
    for bar in range(16):
        _,chord=CHORDS[bar%4]
        for j,pitch in enumerate([chord[0],chord[1],chord[2],chord[3]]):guitar.add(bar*4+j*.5,.4,pitch,76)
        for beat,reverse in ((2,False),(3,True)):
            for j,pitch in enumerate(chord[::-1] if reverse else chord):guitar.add(bar*4+beat+j*.035,.55,pitch,86-j*4)
    catalog.append(save('03_Dusk_Strumming','暮色扫弦',88,16,[guitar],guitar.label,'木吉他分解与上下扫弦交替，适合同时亮起多个品位和弦灯。'))
    lead=Part('Guide - Harbor lead guitar','guitar',0)
    piano=Part('Piano - Moving harmony','piano',1)
    bass=Part('Bass - Anchor','bass',2)
    violin=Part('Violin - Answering phrases','violin',3)
    drums=Part('Drums - Harbor groove','drums',9)
    for bar in range(32):
        melody(lead,bar,bar//8,86 if 8<=bar<24 else 78)
        _,chord=CHORDS[bar%4]
        for beat,pitch in zip((0,1.5,2.5,3.5),(chord[1],chord[2],chord[3],chord[2])):piano.add(bar*4+beat,min(.75,3.95-beat),pitch,65)
        if bar>=4:
            phrase=[(0,1.4,chord[1]+12),(1.5,.9,chord[2]+12),(2.5,1.45,chord[3]+12)]
            for beat,length,pitch in phrase:violin.add(bar*4+beat,length,pitch,57)
    rhythm((None,bass,drums),32)
    catalog.append(save('04_Star_Harbor','星港合奏',104,32,[lead,piano,bass,violin,drums],lead.label,'主吉他、流动钢琴和声、轻提琴答句，Bass与鼓共同推进；用于展示多乐器同时发声。'))
    lead=Part('Guide - Neon distorted lead','guitar',0,program=30)
    chords=Part('Guitar - Power rhythm','guitar',1,program=30)
    bass=Part('Bass - Engine','bass',2)
    drums=Part('Drums - Rock backbeat','drums',9)
    for bar in range(32):melody(lead,bar,bar//8,92,low=bar<8)
    rhythm((chords,bass,drums),32,rock=True)
    catalog.append(save('05_Neon_Engine','霓虹引擎',118,32,[lead,chords,bass,drums],lead.label,'失真主奏叠加强力和弦、紧凑低音和突出鼓点；原生工程吉他延音46。',rock=True))
    piano=Part('Guide - Window piano melody','piano',0)
    left=Part('Piano - Left hand','piano',1)
    guitar=Part('Guitar - Clear acoustic reply','guitar',2)
    violin=Part('Violin - Soft counterline','violin',3)
    for bar in range(24):
        melody(piano,bar,bar//8,82)
        root,chord=CHORDS[bar%4]
        for beat,pitch in zip((0,1,2,3),(root,root+7,root+12,root+7)):left.add(bar*4+beat,.85,pitch,63)
        for j,pitch in enumerate([chord[0],chord[2],chord[1],chord[3]]):guitar.add(bar*4+.5+j,.75,pitch,78)
        if bar>=4:
            violin.add(bar*4,1.85,chord[1]+12,53)
            violin.add(bar*4+1.9,.9,chord[2]+12,55)
            violin.add(bar*4+2.85,1.14,chord[3]+12,52)
    catalog.append(save('06_Window_Tides','窗边潮汐',72,24,[piano,left,guitar,violin],piano.label,'缓慢钢琴主旋律、清音木吉他回应、轻提琴对位；可切换吉他轨练习。'))
    (OUT/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf8')
    lines=['原创 MIDI 练习与合奏 / 2026-11-03','',
           '一、MIDI跟灯：打开工作区“打开MIDI跟灯.cmd”，连接S3 COM30并握手，导入.mid，选择下面推荐的Guide轨。',
           '当前MIDI页只做实体跟灯练习，由你手动演奏发声；不会自动播放MIDI伴奏。',
           '二、实机合奏：在“编曲工作台→打开”选择同名.tang.json；连接FPGA串口，探测合奏能力，启用v8独立合奏与实机发送后播放。',
           'MID轨道中的GM音色用于普通MIDI软件；FPGA的失真、混音等设置保存在配套.tang.json中。',
           'MIDI与原生工程的音符一致。多音跟灯显示品位/弦集合，不能单独表示所有交叉点；Bass轨可能超出当前跟灯音域。',
           '曲目已通过MIDI重新读取、音符数/总时长核对、推荐轨音域检查，以及现有FPGA合奏事件编译检查；尚未实板听音。','']
    for item in catalog:
        lines += [f"{item['file']}  《{item['title']}》",f"  {item['bpm']} BPM / {item['bars']}小节 / {item['seconds']}秒 / 峰值{item['peak_simultaneous_notes']}个音符重叠",
                  f"  跟灯选轨：{item['guide_track']}",f"  {item['description']}",'']
    (OUT/'使用说明.txt').write_text('\n'.join(lines),encoding='utf-8-sig')
    archive=OUT.parent/'MIDI_Originals_1103.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in OUT.iterdir():
            if p.is_file():z.write(p,'MIDI_Originals_1103/'+p.name)
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    print(json.dumps(catalog,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
