"""Piano melody with prominent acoustic guitar for the user's 6/8 score."""
from copy import deepcopy
from math import ceil

from piano_scores import Automation, BAR, PPQ, Point, Project, Track, Clip, Note
from fuji_arrangement import _emit
from time_machine_score import BPM, EIGHTH_TICKS, hand_notes, warp


PROFILE = {
    'id':'p07_time_machine', 'title':'Time Machine · 透亮钢琴与木吉他双奏',
    'genre':'用户钢琴谱改编 / 6/8钢琴与吉他', 'key':'五降号（降D大调／降B小调关系调）',
    'bpm':BPM, 'bars':38, 'piano_lead':True, 'guitar_lead':False, 'original':False,
    'gain_policy':'clear-piano-acoustic-duet',
    'description':'按用户三页6/8钢琴谱整理72小节，钢琴右手采用与单键试音90相同的力度层，减轻左手铺底，保留双手完整音符。钢琴与木吉他以接近同等响度为目标；木吉他沿用《霓虹航线》的清音与自然包络。慢板附点四分音符52，两谱面小节对应一格4/4网格。',
    'mix_note':'已载入Time Machine透亮钢琴对照版：右手保持单键试音的力度层，左手减轻；钢琴总线30–36、木吉他56–66、慢板52。未自动连接或播放；听感以实板试听为准。',
    'attribution':'根据用户提供的三页Time Machine钢琴PDF作本地工作转谱与吉他再编配；原谱未标注作者及速度，速度和伴奏为本工程选择。',
}


def source_tick(units):
    return round(warp(units)*EIGHTH_TICKS)


def normalized_piano():
    notes=[]
    for hand in ('right','left'):
        for original in hand_notes(hand):
            notes.append({**original,'start_tick':source_tick(original['start'])+original['roll_offset'],
                          'end_tick':source_tick(original['end'])})
    notes.sort(key=lambda note:(note['start_tick'],note['pitch'],note['hand']!='right'))
    merged=[]
    for note in notes:
        if merged and (merged[-1]['start_tick'],merged[-1]['pitch'])==(note['start_tick'],note['pitch']):
            merged[-1]['end_tick']=max(merged[-1]['end_tick'],note['end_tick'])
        else:merged.append(note.copy())
    by_pitch={}
    for note in merged:by_pitch.setdefault(note['pitch'],[]).append(note)
    for group in by_pitch.values():
        for first,following in zip(group,group[1:]):
            if first['end_tick']>following['start_tick']:
                first['end_tick']=max(first['start_tick']+1,following['start_tick']-1)
    return merged


def guitar_pitch(pitch):
    pitch-=12
    while pitch<45:pitch+=12
    while pitch>68:pitch-=12
    return pitch


def compose_time_machine():
    tracks=[Track('piano','01 钢琴右手·完整主旋律与装饰',100,id='p07-right'),
            Track('piano','02 钢琴左手·轻分解伴奏',70,id='p07-left'),
            Track('guitar','03 木吉他·霓虹航线清音与自然衰减',72,id='p07-guitar')]
    for note in normalized_piano():
        bar=int(note['start']//6)+1
        if note['hand']=='right':
            # Match the manual keyboard's default velocity-90 bank (80..111).
            # Keep phrase dynamics within that bank; do not dim high notes by
            # accidentally crossing into the softer bank below velocity 80.
            velocity=90 if bar<=4 else 94 if bar<=32 else 98 if bar<=56 else 102 if bar<=61 else 92
        else:velocity=64 if bar<33 else 67 if bar<62 else 59
        _emit(tracks,0 if note['hand']=='right' else 1,note['start_tick'],note['end_tick']-note['start_tick'],
              note['pitch'],velocity,f'原谱{bar}小节·钢琴{note["hand"]}')
    left=hand_notes('left')
    for bar in range(5,72):
        if bar in (20,24,56,63,64):continue  # let piano breaths and fermatas speak
        tones=[note for note in left if note['start']<(bar*6) and note['end']>(bar-1)*6]
        if not tones:continue
        ordered=[]
        for note in tones:
            pitch=guitar_pitch(note['pitch'])
            if pitch not in ordered:ordered.append(pitch)
        for pulse,eighth in enumerate((0,2,4)):
            pitch=ordered[pulse%len(ordered)]
            start=source_tick((bar-1)*6+eighth)
            _emit(tracks,2,start,round(.58*PPQ),pitch,58 if pulse else 63,
                  f'原谱{bar}小节·吉他轻分解')
        if bar in (25,33,41,49,57,65):
            tones=sorted(set(ordered))[:3]
            for voice,pitch in enumerate(tones):
                _emit(tracks,2,source_tick((bar-1)*6+3)+voice*14,round(.55*PPQ),pitch,56-voice*3,
                      f'原谱{bar}小节·吉他弱扫弦')
    project=Project(PROFILE['title'],bpm=BPM,bars=38,tracks=tracks,loop_end=38*BAR,guitar_sustain=127)
    project.parameters.update({'bus.piano':32,'bus.guitar':0,'bus.violin':0,'bus.bass':0,'bus.drums':0,
        # Same guitar FX settings as Neon Runway. Clean bypass ignores Tone/Level;
        # natural per-voice decay above is separate from these FX registers.
        'guitar.amp':0,'guitar.drive':25,'guitar.tone':58,'guitar.level':82,'guitar.mix':127,
        'guitar.cabinet':0,'guitar.gate':0,'guitar.compressor':0,'guitar.modulation':0,
        'space.chorus_mix':0,'space.delay_mix':0,'space.delay_feedback':0})
    # Use source positions, not the fixed 4/4 editor bar number, for dynamics.
    for target,changes in {
        'bus.piano':[(1,32),(5,34),(33,36),(57,35),(62,32),(65,33),(72,30)],
        'bus.guitar':[(1,0),(5,56),(25,60),(33,64),(49,66),(62,56),(65,58),(72,0)]}.items():
        points=[];previous=None
        for source_bar,value in changes:
            tick=source_tick((source_bar-1)*6)
            if previous is not None:points.append(Point(tick-PPQ//8,previous))
            points.append(Point(tick,value));previous=value
        points.extend([Point(source_tick(72*6),previous),Point(project.length-PPQ//2,0)])
        project.automation.append(Automation(target,'linear',points))
    for target in ('bus.violin','bus.bass','bus.drums'):
        project.automation.append(Automation(target,'step',[Point(0,0)]))
    return project.validate()


def short_time_machine(project):
    """Twelve source 6/8 bars (25..36), an arranged cadence and natural tail."""
    result=deepcopy(project)
    result.name='Time Machine · 透亮钢琴木吉他双奏37秒试听'
    result.bars,result.loop_start,result.loop_end=8,0,8*BAR
    start,end=source_tick(24*6),source_tick(36*6)
    for track in result.tracks:
        selected=[]
        for clip in track.clips:
            for note in clip.notes:
                first,last=clip.start+note.start,clip.start+note.start+note.duration
                if first<end and last>start:
                    a,b=max(first,start),min(last,end)
                    selected.append(Note(a-start,b-a,note.pitch,note.velocity,note.id))
        track.clips=[Clip('原谱第25–36小节·6/8试听',0,6*BAR,selected,id=f'{track.id}-excerpt')] if selected else []
    for lane in result.automation:
        amount=lane.value_at(start,result.parameters[lane.target])
        result.parameters[lane.target]=amount
        lane.points=[Point(0,amount),Point(7*BAR,amount),Point(8*BAR-PPQ//2,0)]
    for pitch in (61,65,68,73):_emit(result.tracks,0,6*BAR,3*PPQ,pitch,90,'试听·降D大调收束')
    for pitch in (49,56):_emit(result.tracks,1,6*BAR,3*PPQ,pitch,56,'试听·钢琴低音收束')
    for voice,pitch in enumerate((49,53,56,61)):
        _emit(result.tracks,2,6*BAR+voice*14,round(.6*PPQ),pitch,55-voice*2,'试听·吉他轻扫收束')
    return result.validate()
