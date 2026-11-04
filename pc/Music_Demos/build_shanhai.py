"""Publish the user-score arrangement without rewriting previous projects."""
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path

from build_library import ROOT, neon
from arrangement_model import BAR, PPQ, Project
from arrangement_playback import compile_plan
from shanhai_arrangement import PROFILE, compose_shanhai, shanhai_short
from shanhai_score import melody_notes, source_location


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_projects():
    project = compose_shanhai()
    paths, reports = {}, {}
    for variant, score in (('full', project), ('short', shanhai_short(project))):
        path = ROOT / 'projects' / f'{PROFILE["id"]}_{variant}.tang.json'
        score.save(path)
        assert Project.load(path) == score
        plan = compile_plan(score, True, ensemble=True)
        reports[path.name] = {**neon.analyze(score), 'sha256': digest(path),
                             'guitar_sustain': score.guitar_sustain,
                             'preparation_seconds_minimum': plan.preparation_seconds,
                             'drum_bus_base': score.parameters['bus.drums'],
                             'maximum_drum_bus': max(point.value for lane in score.automation
                                                     if lane.target == 'bus.drums' for point in lane.points)}
        paths[variant] = path.relative_to(ROOT).as_posix()
    entry = {**PROFILE, **paths, 'piano_lead': False, 'duration_seconds': 180, 'short_seconds': 20}
    return entry, reports


def main():
    originals = {path.name: digest(path) for path in (ROOT / 'projects').glob('*.tang.json')
                 if not path.name.startswith(PROFILE['id'] + '_')}
    entry, reports = save_projects()
    catalog = json.loads((ROOT / 'catalog.json').read_text(encoding='utf-8'))
    catalog['songs'] = [song for song in catalog['songs'] if song['id'] != PROFILE['id']]
    catalog['songs'].insert(3, entry)
    (ROOT / 'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding='utf-8')
    previous_unchanged = all(digest(ROOT / 'projects' / name) == value for name, value in originals.items())
    assert previous_unchanged
    with (ROOT / 'shanhai_melody_reference.csv').open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.writer(stream)
        writer.writerow(('page', 'row', 'source_bar', 'beat', 'degree', 'midi_E', 'length_beats', 'source_bars_tied'))
        for note in melody_notes():
            bar = int(note['start'] // 16) + 1
            writer.writerow((*source_location(bar), bar, str(note['start'] % 16 / 4 + 1), note['degree'],
                             note['pitch'], str((note['end'] - note['start']) / 4),
                             ','.join(map(str, sorted(set(note['source_bars']))))))
    source_directory = ROOT / 'source_scores/shanhai_user_pages'
    report = {'generated_at': datetime.now().astimezone().isoformat(), 'projects': reports,
              'score_pages': {path.name: digest(path) for path in source_directory.glob('page_*.png')},
              'source_printed_bars': 70, 'full_arranged_bars': 72,
              'source_transcription': 'Manual working transcription; some beamed rhythms regularized. Same-pitch ties merged; long notes re-picked for the short guitar envelope.',
              'tempo_bpm': 96, 'tempo_is_arrangement_choice': True,
              'pitch_reference': '1=E4, printed C fingering with capo +4 retained',
              'previous_projects': originals, 'previous_project_files_unchanged': previous_unchanged,
              'source_sha256': {name: digest(ROOT / name) for name in ('shanhai_score.py', 'shanhai_arrangement.py', 'build_shanhai.py')},
              'real_serial_connected': False, 'board_listening_validated': False}
    (ROOT / 'shanhai_validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(reports, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
