import csv
from datetime import datetime
import hashlib
import json

from build_library import ROOT,neon
from arrangement_model import Project
from arrangement_playback import compile_plan
from time_machine_score import BPM,EIGHTH_TICKS,FERMATAS,hand_notes
from time_machine_arrangement import PROFILE,compose_time_machine,short_time_machine,source_tick,normalized_piano


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def save_projects():
    full=compose_time_machine();paths={};reports={}
    for variant,score in (('full',full),('short',short_time_machine(full))):
        path=ROOT/'projects'/f'p07_time_machine_{variant}.tang.json'
        score.save(path);assert Project.load(path)==score
        plan=compile_plan(score,True,ensemble=True)
        reports[path.name]={**neon.analyze(score),'sha256':digest(path),'preparation_seconds_minimum':plan.preparation_seconds,
            'guitar_sustain':score.guitar_sustain,'guitar_envelope':'board_natural' if score.guitar_sustain==127 else 'custom_short'}
        paths[variant]=path.relative_to(ROOT).as_posix()
    return {**PROFILE,**paths,'duration_seconds':full.bars*240/BPM,'short_seconds':8*240/BPM},reports


def main():
    previous={p.name:digest(p) for p in (ROOT/'projects').glob('*.tang.json') if not p.name.startswith('p07_time_machine_')}
    entry,reports=save_projects()
    catalog=json.loads((ROOT/'catalog.json').read_text(encoding='utf-8'))
    catalog['songs']=[song for song in catalog['songs'] if song['id']!=PROFILE['id']]
    catalog['songs'].insert(3,entry)
    (ROOT/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
    assert all(digest(ROOT/'projects'/name)==sha for name,sha in previous.items())
    with (ROOT/'time_machine_piano_reference.csv').open('w',newline='',encoding='utf-8-sig') as stream:
        writer=csv.writer(stream);writer.writerow(['hand','source_bar','eighth_offset','pitch','midi','length_eighths','sounding_start_tick','roll_offset_ticks','tied_source_bars'])
        for hand in ('right','left'):
            for note in hand_notes(hand):
                writer.writerow([hand,int(note['start']//6)+1,str(note['start']%6),note['name'],note['pitch'],
                    str(note['end']-note['start']),source_tick(note['start'])+note['roll_offset'],note['roll_offset'],','.join(map(str,note['source_bars']))])
    source=ROOT/'source_scores/time_machine_user_pdf/score.pdf'
    proof={'generated_at':datetime.now().astimezone().isoformat(),'projects':reports,
        'source_pdf':'source_scores/time_machine_user_pdf/score.pdf','source_pdf_sha256':digest(source),
        'source_pages':3,'source_meter':'6/8','source_bars':72,'sounding_octaves_included':True,
        'chosen_dotted_quarter_bpm':BPM,'tempo_not_printed_in_source':True,
        'editor_grid':'two source 6/8 bars per fixed 4/4 grid bar; eighth=160 ticks; fermatas shift later events',
        'fermata_extra_eighths':[(str(point),str(extra)) for point,extra in FERMATAS],
        'source_notes':{hand:len(hand_notes(hand)) for hand in ('right','left')},'normalized_piano_notes':len(normalized_piano()),
        'previous_projects':previous,'previous_project_files_unchanged':True,
        'source_sha256':{name:digest(ROOT/name) for name in ('time_machine_score.py','time_machine_arrangement.py','build_time_machine.py')},
        'real_serial_connected':False,'board_listening_validated':False}
    (ROOT/'time_machine_validation.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(reports,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
