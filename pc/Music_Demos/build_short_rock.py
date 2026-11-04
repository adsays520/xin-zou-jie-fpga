"""Add the new song without rewriting any of the twenty existing projects."""
from datetime import datetime
import hashlib
import json
from pathlib import Path

from build_library import ROOT, neon, short_version
from demo_headroom import with_headroom
from rock_short_tail import PROFILE, compose_short_rock
from arrangement_playback import compile_plan


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    originals = {path.name: digest(path) for path in (ROOT / 'projects').glob('*.tang.json')
                 if not path.name.startswith(PROFILE['id'])}
    project = compose_short_rock()
    paths, reports = {}, {}
    for variant, score in (('full', project), ('short', short_version(project, PROFILE['title']))):
        score = with_headroom(score)
        path = ROOT / 'projects' / f'{PROFILE["id"]}_{variant}.tang.json'
        score.save(path)
        paths[variant] = path.relative_to(ROOT).as_posix()
        reports[variant] = {**neon.analyze(score), 'sha256': digest(path),
                            'guitar_sustain': score.guitar_sustain,
                            'preparation_seconds_minimum': compile_plan(score, True, ensemble=True).preparation_seconds}
    catalog = json.loads((ROOT / 'catalog.json').read_text(encoding='utf-8'))
    catalog['songs'] = [song for song in catalog['songs'] if song['id'] != PROFILE['id']]
    catalog['songs'].insert(3, {**PROFILE, **paths, 'piano_lead': False,
        'duration_seconds': project.bars * 240 / project.bpm, 'short_seconds': 8 * 240 / project.bpm})
    (ROOT / 'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding='utf-8')
    unchanged = all(digest(ROOT / 'projects' / name) == value for name, value in originals.items())
    assert unchanged and len(originals) >= 20
    proof = {'generated_at': datetime.now().astimezone().isoformat(), 'projects': reports,
             'original_twenty_projects_unchanged': unchanged, 'original_sha256': originals,
             'real_serial_connected': False, 'board_listening_validated': False}
    (ROOT / 'short_rock_validation.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(reports, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
