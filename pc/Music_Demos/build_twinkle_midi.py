"""Traditional public-domain Twinkle melody, slow guide and acoustic ensemble."""
from pathlib import Path
import json
import zipfile
import build_original_midi_1103 as writer


def main():
    folder=Path(__file__).resolve().parent/'MIDI_Twinkle_1103'
    folder.mkdir(exist_ok=True)
    writer.OUT=folder
    phrases=[
        [60,60,67,67,69,69,67], [65,65,64,64,62,62,60],
        [67,67,65,65,64,64,62], [67,67,65,65,64,64,62],
        [60,60,67,67,69,69,67], [65,65,64,64,62,62,60],
    ]
    melody=writer.Part('Guide - Twinkle melody','piano',0)
    for phrase,pitches in enumerate(phrases):
        for i,pitch in enumerate(pitches):
            melody.add(phrase*8+i,1.85 if i==6 else .85,pitch,78 if i==0 else 74)
    solo=writer.save('Twinkle_Star','小星星·慢速单旋律',80,12,[melody],melody.label,
                     'C大调、4/4、完整六句；推荐用作MIDI跟灯练习。')
    guitar=writer.Part('Guitar - Clean acoustic arpeggio','guitar',1)
    left=writer.Part('Piano - Gentle bass','piano',2)
    chords={'C':(36,[48,52,55,60]),'F':(41,[48,53,57,60]),'G':(43,[50,55,59,62])}
    progression=[('C','C'),('F','C'),('F','C'),('G','C'),('C','F'),('C','G'),
                 ('C','F'),('C','G'),('C','C'),('F','C'),('F','C'),('G','C')]
    for bar,names in enumerate(progression):
        for half,name in enumerate(names):
            root,voicing=chords[name]
            at=bar*4+half*2
            left.add(at,1.8,root,55)
            left.add(at+1,.8,root+7,51)
            for j,pitch in enumerate(voicing):guitar.add(at+j*.5,.43,pitch,65 if j==0 else 59)
    ensemble=writer.save('Twinkle_Ensemble','小星星·钢琴木吉他',80,12,[melody,left,guitar],melody.label,
                         '钢琴主旋律与轻左手，清音木吉他分解伴奏；无鼓、无失真。')
    # Verify all 42 melody notes, with deliberate gaps between repeated pitches.
    parsed=writer.read_midi(folder/'Twinkle_Star.mid')
    assert [n.pitch for n in parsed.notes]==[p for phrase in phrases for p in phrase]
    assert len(parsed.notes)==42 and abs(parsed.duration-36)<.001
    assert all(a.end<=b.start for a,b in zip(parsed.notes,parsed.notes[1:]))
    (folder/'验证记录.json').write_text(json.dumps({'passed':True,'tracks':[solo,ensemble],
        'melody_notes_checked':42,'physical_listening':False},ensure_ascii=False,indent=2),encoding='utf8')
    (folder/'使用说明.txt').write_text('《小星星》 MIDI / 80 BPM / C大调 / 4拍 / 36秒\n\n'
        'Twinkle_Star.mid：单旋律，推荐导入MIDI跟灯页，选择 Guide - Twinkle melody。\n'
        'Twinkle_Ensemble.mid：钢琴主旋律＋轻左手＋清音木吉他分解伴奏。\n'
        '自动实机演奏：在编曲工作台打开同名.tang.json，连接FPGA并启用实机发送；合奏版需确认v8合奏能力。\n'
        'MIDI跟灯页用于手动演奏辅助；导入MIDI不会自动播放伴奏。\n'
        '已核对42个旋律音及重复音之间的松音间隙，两份原生工程均通过现有实机合奏协议编译。尚未实板听音。\n',encoding='utf-8-sig')
    archive=folder.parent/'MIDI_Twinkle_1103.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for path in folder.iterdir():
            if path.is_file():z.write(path,folder.name+'/'+path.name)
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    print(folder)
    print('PASS: 42 melody notes; 80 BPM; 36 seconds; solo and ensemble compiled')


if __name__=='__main__':main()
