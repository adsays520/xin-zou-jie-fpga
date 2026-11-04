"""Current V16 violin verification entry. Legacy waveguide fixtures are archival."""
from pathlib import Path
import subprocess,sys
P=Path(__file__).resolve().parent
for script,args in [('verify_violin_sms.py',[]),('violin_sms_integer_model.py',['--compare']),('check_violin_sms_acoustics.py',[])]:
 subprocess.run([sys.executable,str(P/script),*args],check=True)
print('PASS V16 SMS violin verification')
