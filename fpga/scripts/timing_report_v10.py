import html
from pathlib import Path
import re


TARGETS = {'sys_clk': 50.0, 'ddr_user100': 100.0, 'mem400': 400.0, 'ddr_ref100': 100.0}


def table_rows(content, anchor):
    match = re.search(r'name="' + re.escape(anchor) + r'"', content)
    if not match:
        raise ValueError('Missing timing section: ' + anchor)
    table = re.search(r'<table\b[^>]*>(.*?)</table>', content[match.end():], re.S)
    if not table:
        raise ValueError('Missing timing table: ' + anchor)
    result = []
    for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>', table.group(1), re.S):
        cells = [html.unescape(re.sub(r'<[^>]*>', '', value)).strip()
                 for value in re.findall(r'<td\b[^>]*>(.*?)</td>', row, re.S)]
        if cells:
            result.append(cells)
    if not result:
        raise ValueError('Empty timing table: ' + anchor)
    return result


def analyze(content):
    result = {}
    for kind in ('Setup', 'Hold'):
        match = re.search(r'Numbers of ' + kind + r' Violated Endpoints</td>\s*<td>(\d+)</td>', content)
        if not match:
            raise ValueError('Missing endpoint total: ' + kind)
        result[kind.lower() + '_violations'] = int(match.group(1))
    frequencies = {}
    for row in table_rows(content, 'Max_Frequency_Report'):
        name = row[1]
        if name in TARGETS:
            if name in frequencies:
                raise ValueError('Duplicate Fmax clock: ' + name)
            target = float(row[2].removesuffix('(MHz)'))
            actual = float(row[3].removesuffix('(MHz)'))
            if target != TARGETS[name]:
                raise ValueError('Changed clock target: ' + name)
            frequencies[name] = {'target_MHz': target, 'actual_MHz': actual}
    if set(frequencies) != set(TARGETS):
        raise ValueError('Incomplete Fmax clocks')
    result['Fmax'] = frequencies
    for kind, anchor in (('setup', 'Setup_Slack_Table1'), ('hold', 'Hold_Slack_Table'),
                         ('recovery', 'Recovery_Slack_Table'), ('removal', 'Removal_Slack_Table'),
                         ('min_pulse', 'MIN_PULSE_WIDTH_TABLE')):
        anchors = re.findall(r'name="(Setup_Slack_Table\d+)"', content) if kind == 'setup' else [anchor]
        if not anchors:
            raise ValueError('Missing Setup slack tables')
        rows = [row for selected in anchors for row in table_rows(content, selected)]
        slacks = [float(row[1]) for row in rows]
        result[kind + '_worst_slack_ns'] = min(slacks)
        if kind == 'setup':
            worst = min(rows, key=lambda row: float(row[1]))
            result['worst_setup_path'] = {'from': worst[2], 'to': worst[3]}
    result['Gray_8ns_active'] = bool(re.search(
        r'<td>TC_MAX_DELAY</td>\s*<td>Actived</td>\s*<td>set_max_delay 8\.000 ', content))
    result['invalid_constraints'] = bool(re.search(r'<td>(Inactived|Inactive|Invalid|Ignored)</td>', content))
    result['passed'] = (
        result['setup_violations'] == 0 and result['hold_violations'] == 0
        and all(value['actual_MHz'] >= value['target_MHz'] for value in frequencies.values())
        and all(result[kind + '_worst_slack_ns'] >= 0
                for kind in ('setup', 'hold', 'recovery', 'removal', 'min_pulse'))
        and result['Gray_8ns_active'] and not result['invalid_constraints']
    )
    return result


def read_report(path):
    return analyze(Path(path).read_text(encoding='utf-8', errors='replace'))
