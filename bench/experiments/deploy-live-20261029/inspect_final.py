import sys,json,re
from pathlib import Path
B=Path(r'C:\Users\User\Strata-Adrian-control');R=B/'runs/native-pipe-deploy-live-20261029'
sys.path.insert(0,str(R))
import deploy as d
d.S=json.loads((R/'state.json').read_text(encoding='utf-8'))
d.gate('independent-final-processes')
txt=(R/'rollback-startup.log').read_text(encoding='utf-8')
d.write('independent-final-verification.json',d.verify(False,txt))
log=Path(json.loads(d.ns.CONFIG.read_bytes())['log']).read_text(encoding='utf-8',errors='replace')
pos=log.rfind('NATIVE_PIPE ACTIVE')
lines=[x for x in log[pos:].splitlines() if re.search(r'NATIVE_PIPE ACTIVE|NATIVE_PIPE FATAL|NATIVE_PIPE_CHECK MISMATCH|generated in|decode timing:',x)]
d.write('smoke-log-evidence.json',dict(lines=lines,parsed=d.ns.parse_request('\n'.join(lines)),scope='last NATIVE_PIPE activation through rollback; only pipeline and timing lines, no prompts'))
print(json.dumps(dict(state=d.S,final_verified=True,smoke_lines=lines),ensure_ascii=False))
