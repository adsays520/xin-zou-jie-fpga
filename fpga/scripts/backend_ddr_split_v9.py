from pathlib import Path
import re

from backend_options_v9 import EXPECTED as NATIVE_EXPECTED


STEM = 'ensemble_daw_v9_ddr_split'
TCL = 'build_ddr_split_v9.tcl'
EXPECTED = {**NATIVE_EXPECTED, 'convert_sdp32_36_to_sdp16_18': 1}


def validate_tcl(content):
    for name, value in EXPECTED.items():
        found = re.findall(r'(?m)^\s*set_option\s+-' + re.escape(name) + r'\s+(\d+)\s*$', content)
        if found != [str(value)]:
            raise ValueError(f'DDR-compatible Tcl mismatch: {name}={found}, expected {value}')
    return dict(EXPECTED)


def validate_command(content, root):
    options = {}
    for line in content.splitlines():
        match = re.fullmatch(r'\s*-(\w+)(?:\s+(.*?))?\s*', line)
        if match:
            name, value = match.groups()
            if name in options:
                raise ValueError('Duplicate backend option: ' + name)
            options[name] = (value or '').strip()

    def integer(name):
        value = options.get(name)
        if value is None or not value.isdigit():
            raise ValueError('Missing or invalid backend integer: ' + name)
        return int(value)

    def flag(name):
        if name not in options:
            return 0
        if options[name] not in ('', '0', '1'):
            raise ValueError('Invalid backend boolean: ' + name)
        return int(options[name] != '0')

    actual = {name: integer(name) for name in ('place_option', 'route_option', 'clock_route_order', 'route_maxfan')}
    actual.update(timing_driven=flag('timing'), correct_hold_violation=integer('correct_hold'),
                  convert_sdp32_36_to_sdp16_18=flag('convert_sdp32_36_to_sdp16_18'),
                  replicate_resources=flag('replicate'), inc_place=flag('inc_place'), inc_pnr=flag('inc_pnr'))
    if actual != EXPECTED:
        raise ValueError(f'DDR-compatible actual backend mismatch: {actual}')
    if options.get('pn') != 'GW5AST-LV138FPG676AES':
        raise ValueError('Unexpected device')
    root = Path(root).resolve()
    for name, relative in (('d', f'impl/gwsynthesis/{STEM}.vg'),
                           ('cst', 'constraints/audio.cst'), ('sdc', 'constraints/audio.sdc')):
        if name not in options or Path(options[name].strip('"')).resolve().as_posix().casefold() != (
                root / relative).resolve().as_posix().casefold():
            raise ValueError('Unexpected or stale backend input: ' + name)
    return actual
