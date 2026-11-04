from pathlib import Path
import re


EXPECTED = {
    'timing_driven': 1,
    'place_option': 2,
    'route_option': 2,
    'clock_route_order': 1,
    'route_maxfan': 23,
    'correct_hold_violation': 1,
    'convert_sdp32_36_to_sdp16_18': 0,
    'replicate_resources': 1,
    'inc_place': 0,
    'inc_pnr': 0,
}


def validate_requested_tcl(content):
    for name, value in EXPECTED.items():
        found = re.findall(r'(?m)^\s*set_option\s+-' + re.escape(name) + r'\s+(\d+)\s*$', content)
        if found != [str(value)]:
            raise ValueError(f'Backend Tcl mismatch for {name}: {found}; expected exactly {value}')
    return dict(EXPECTED)


def validate_backend_command(content, root):
    options = {}
    for line in content.splitlines():
        match = re.fullmatch(r'\s*-(\w+)(?:\s+(.*?))?\s*', line)
        if match:
            name, value = match.groups()
            if name in options:
                raise ValueError('Duplicate backend option: ' + name)
            options[name] = (value or '').strip()

    def integer(name):
        if name not in options or not options[name].isdigit():
            raise ValueError('Missing or invalid numeric backend option: ' + name)
        return int(options[name])

    def flag(name):
        if name not in options:
            return 0
        if options[name] not in ('', '0', '1'):
            raise ValueError('Invalid boolean backend option: ' + name)
        return 0 if options[name] == '0' else 1

    actual = {
        'timing_driven': flag('timing'),
        'place_option': integer('place_option'),
        'route_option': integer('route_option'),
        'clock_route_order': integer('clock_route_order'),
        'route_maxfan': integer('route_maxfan'),
        'correct_hold_violation': integer('correct_hold'),
        'convert_sdp32_36_to_sdp16_18': flag('convert_sdp32_36_to_sdp16_18'),
        'replicate_resources': flag('replicate'),
        'inc_place': flag('inc_place'),
        'inc_pnr': flag('inc_pnr'),
    }
    if actual != EXPECTED:
        raise ValueError(f'Actual backend options differ from the requested experiment: {actual}')
    if options.get('pn') != 'GW5AST-LV138FPG676AES':
        raise ValueError('Unexpected device in actual backend command')
    root = Path(root).resolve()
    for name, relative in (('d', 'impl/gwsynthesis/ensemble_daw_v9.vg'),
                           ('cst', 'constraints/audio.cst'), ('sdc', 'constraints/audio.sdc')):
        if name not in options:
            raise ValueError('Missing backend input: ' + name)
        actual_path = Path(options[name].strip('"')).resolve().as_posix().casefold()
        expected_path = (root / relative).resolve().as_posix().casefold()
        if actual_path != expected_path:
            raise ValueError('Unexpected or stale backend input: ' + name)
    return actual
