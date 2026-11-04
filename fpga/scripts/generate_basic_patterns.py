"""Export the same built-in basic grooves as editable host JSON files."""
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'host'))
from drum_patterns import BASIC_PRESETS,preset
for name in BASIC_PRESETS:
    preset(name).save(root/'host/presets'/f'{name}.json')
print('Exported five editable basic drum grooves.')
