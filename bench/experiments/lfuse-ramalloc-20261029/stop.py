import sys,json,time
from pathlib import Path
import psutil
R=Path(r'C:\Users\User\Strata-Adrian-control\runs\lfuse-ab-20261029-attempt2')
sys.path.insert(0,str(R));import controller as c
c.identity()
s=json.loads((R/'campaign.json').read_text(encoding='utf-8'))
assert s['phase']=='BLOCK'
p=psutil.Process(s['controller_pid']);assert str(R).lower().replace('strata-adrian-control','strata-adrian-control') in ' '.join(p.cmdline()).lower() or 'lfuse-ab-20261029-attempt2' in ' '.join(p.cmdline())
allowed={p.pid}|{x.pid for x in p.children(recursive=True)}|{x.pid for x in p.parents()}
procs=c.ns.processes()
assert not [x for x in procs if x['pid'] not in allowed],procs
eng=[x for x in p.children(recursive=True) if x.name().lower()=='strata.exe']
assert len(eng)==1
engine=eng[0];assert c.ns.sha(Path(engine.exe()))==c.ns.EXE_C_SHA
chain=[engine.parent().cmdline(),engine.parent().parent().cmdline()]
assert any('lfuse-ab-20261029-attempt2' in ' '.join(x) and '--config' in x for x in chain)
record={'reason':'USER_REQUESTED_EARLY_STOP','authorization':'user2026-10-29 看起來沒用可以提早結束了吧','utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'campaign_before':s,'engine_pid':engine.pid,'engine_command':engine.cmdline(),'processes':procs,'exclude_partial_round':s['current']['round']}
(R/'user-stop.json').write_text(json.dumps(record,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'stop_engine_pid':engine.pid,'completed_pairs':s.get('pair_count'),'partial_round':s['current']['round']}),flush=True)
engine.terminate()
