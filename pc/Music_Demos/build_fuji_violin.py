import hashlib
import json
from datetime import datetime

from build_library import ROOT, neon
from arrangement_model import Project
from fuji_violin_harmony import PROFILE, compose_fuji_violin, fuji_violin_short


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_projects():
    full = compose_fuji_violin()
    paths, reports = {}, {}
    for variant, score in (('full', full), ('short', fuji_violin_short(full))):
        path = ROOT / 'projects' / f'p05_fuji_violin_{variant}.tang.json'
        score.save(path)
        assert Project.load(path) == score
        paths[variant] = path.relative_to(ROOT).as_posix()
        reports[path.name] = {**neon.analyze(score), 'sha256': digest(path)}
    return {**PROFILE, **paths, 'duration_seconds': 94, 'short_seconds': 16}, reports


def main():
    previous = {path.name: digest(path) for path in (ROOT / 'projects').glob('*.tang.json')
                if not path.name.startswith('p05_fuji_violin_')}
    entry, reports = save_projects()
    catalog = json.loads((ROOT / 'catalog.json').read_text(encoding='utf-8'))
    catalog['songs'] = [song for song in catalog['songs'] if song['id'] != PROFILE['id']]
    catalog['songs'].insert(3, entry)
    (ROOT / 'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding='utf-8')
    assert all(digest(ROOT / 'projects' / name) == value for name, value in previous.items())
    proof = {'generated_at': datetime.now().astimezone().isoformat(), 'projects': reports,
             'previous_projects': previous, 'previous_project_files_unchanged': True,
             'source_sha256': {name: digest(ROOT / name) for name in ('fuji_violin_harmony.py', 'build_fuji_violin.py')},
             'real_serial_connected': False, 'board_listening_validated': False}
    (ROOT / 'fuji_violin_validation.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(reports, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
