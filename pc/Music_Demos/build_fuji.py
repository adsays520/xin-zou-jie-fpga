"""Save the user-PDF arrangement and preserve all earlier demo projects."""
import csv
from datetime import datetime
import hashlib
import json

from build_library import ROOT, neon
from arrangement_model import Project
from arrangement_playback import compile_plan
from fuji_arrangement import PROFILE, compose_fuji, fuji_short, normalized_piano
from fuji_score import hand_notes


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_projects():
    full = compose_fuji()
    paths, reports = {}, {}
    for variant, project in (('full', full), ('short', fuji_short(full))):
        path = ROOT / 'projects' / f'p04_fuji_{variant}.tang.json'
        project.save(path)
        assert Project.load(path) == project
        plan = compile_plan(project, True, ensemble=True)
        reports[path.name] = {**neon.analyze(project), 'sha256': digest(path),
                             'guitar_sustain': project.guitar_sustain,
                             'preparation_seconds_minimum': plan.preparation_seconds}
        paths[variant] = path.relative_to(ROOT).as_posix()
    return {**PROFILE, **paths, 'duration_seconds': 94, 'short_seconds': 16}, reports


def main():
    previous = {path.name: digest(path) for path in (ROOT / 'projects').glob('*.tang.json')
                if not path.name.startswith('p04_fuji_')}
    entry, reports = save_projects()
    catalog = json.loads((ROOT / 'catalog.json').read_text(encoding='utf-8'))
    catalog['songs'] = [song for song in catalog['songs'] if song['id'] != PROFILE['id']]
    catalog['songs'].insert(3, entry)
    (ROOT / 'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding='utf-8')
    assert all(digest(ROOT / 'projects' / name) == value for name, value in previous.items())
    source = ROOT / 'source_scores/fuji_user_pdf/score.pdf'
    reference = ROOT / 'fuji_piano_reference.csv'
    with reference.open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.writer(stream)
        writer.writerow(('hand', 'source_bar', 'beat', 'pitch', 'midi', 'length_beats', 'source_bars_tied'))
        for hand in ('right', 'left'):
            for note in hand_notes(hand):
                writer.writerow((hand, int(note['start'] // 16) + 1, str(note['start'] % 16 / 4 + 1),
                                 note['name'], note['pitch'], str((note['end'] - note['start']) / 4),
                                 ','.join(map(str, sorted(set(note['source_bars']))))))
    report = {'generated_at': datetime.now().astimezone().isoformat(), 'projects': reports,
              'source_pdf': 'source_scores/fuji_user_pdf/score.pdf', 'source_pdf_sha256': digest(source),
              'printed_bars': 45, 'arranged_bars': 47, 'bpm_from_score': 120, 'key_from_score': 'F major',
              'source_notes': {hand: len(hand_notes(hand)) for hand in ('right', 'left')},
              'normalized_piano_notes': len(normalized_piano()),
              'transcription_note': 'Manual working transcription of both staves; a few ambiguous/rest-spaced rhythmic figures regularized. Simultaneous piano unisons merged and overlapping same-pitch gates safely re-articulated.',
              'previous_projects': previous, 'previous_project_files_unchanged': True,
              'source_sha256': {name: digest(ROOT / name) for name in ('fuji_score.py', 'fuji_arrangement.py', 'build_fuji.py')},
              'real_serial_connected': False, 'board_listening_validated': False}
    (ROOT / 'fuji_validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(reports, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
