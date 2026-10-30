import json,re,sys,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'harness'))
import replay_ab_20261027 as rp
ns=rp.ns
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
state=json.loads((R/'campaign.json').read_text())
assert state['phase']=='DONE' and state['verified']
old=R.parent/'native-pipeline-20261029'
rows=json.loads((R/'rows.json').read_text())
records=[];size=lines=0
for b in state['completed']:
 d=Path(b['path']);m=json.loads((d/'meta.json').read_text());cfg=json.loads((d/'config.json').read_text())
 assert m['status']=='OK' and m['rows']==10
 assert m['binary_sha256']=='3F98913EDB0B01D5D5DD3282412725141C298BF5CC9E890DD286AA0720C27230'
 assert m['priority_gate']['before_first_request'] and m['priority_gate']['priority']==32768
 f=m['startup'];assert str(f['slots'])=='3153' and str(f['ram_budget_gib'])=='20.00' and str(f['locked_mib'])=='20479'
 assert cfg['env'].get('STRATA_NATIVE_PIPE')==('1' if b['arm']=='P' else None)
 assert not any(v for k,v in cfg['env'].items() if 'DIAG' in k or k in ('STRATA_NATIVE_PIPE_CHECK','STRATA_IQ_MT_MIN'))
 raw=(d/'engine.log').read_bytes();text=raw.decode('utf-8',errors='replace');size+=len(raw);lines+=len(text.splitlines())
 assert not any(x in text for x in ['NATIVE_PIPE FATAL','NATIVE_PIPE_CHECK MISMATCH','CPU_PHASE_DECODE ','NATIVE_PIPE_CHECK batches='])
 base=next(x for x in json.loads((old/'campaign.json').read_text())['completed'] if x['arm']==b['arm'])
 ref=json.loads((Path(base['path'])/'config.json').read_text());cfg.pop('log');ref.pop('log');assert cfg==ref
 records.append(dict(block=b,meta=m,config_sha256=sha(d/'config.json'),log_sha256=sha(d/'engine.log'),command=json.loads((d/'command.json').read_text())))
assert len(rows)==10*len(records) and all(not r.get('error') and not r.get('m_error') for r in rows)
for p in (R/'harness').glob('*.py'):assert sha(p)==sha(old/'harness'/p.name)
eng=[p for p in __import__('psutil').process_iter(['name']) if p.info['name'].lower()=='strata.exe'];assert len(eng)==1
p=eng[0];assert sha(Path(p.exe()))==ns.EXE_C_SHA and ns.sha(ns.CONFIG)==ns.CONFIG_SHA
env=p.environ();assert env.get('STRATA_IQ3S_MT1')=='1' and not any(v for k,v in env.items() if 'DIAG' in k or k in ('STRATA_NATIVE_PIPE_CHECK','STRATA_IQ_MT_MIN') or k=='STRATA_NATIVE_PIPE')
assert p.nice()==32768 and ns.http_json('/health')['loaded']
cfg=json.loads(ns.CONFIG.read_text(encoding='utf-8-sig'));facts=ns.startup_facts(Path(cfg['log']).read_text(encoding='utf-8',errors='replace'))
assert str(facts['slots'])=='3153' and str(facts['ram_budget_gib'])=='20.00' and str(facts['locked_mib'])=='20479'
result=dict(verified=True,blocks=records,engine_log_bytes=size,engine_log_lines=lines,formal_rows=len(rows),harness_unchanged=True,restore_pid=p.pid,restore_startup=facts,restore_env={k:v for k,v in env.items() if k.startswith('STRATA_')},restore_priority=p.nice(),coverage='所有新增 block meta/config/command/完整 engine logs 與正式 rows；原十個 O/P config/meta、輸入 SHA 和 harness SHA。未逐字審閱自然語言輸出，未作完整 source audit。')
(R/'audit.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(dict(verified=True,blocks=len(records),rows=len(rows),bytes=size,lines=lines,restore_pid=p.pid)))

