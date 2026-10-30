import json,hashlib,re,subprocess,difflib,sys
from pathlib import Path
import psutil
R=Path(r'C:\Users\User\Strata-Adrian-control');N=R/'runs/native-pipe-deploy-prep-20261029'
sys.path.insert(0,str(N));import controller_prep as c
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
write=lambda n,x:(N/n).write_text(json.dumps(x,indent=2),encoding='utf-8')
s=json.loads((N/'campaign.json').read_text());assert s['phase']=='DONE' and s['verified'] and len(s['completed'])==2
br=json.loads((N/'build-result.json').read_text());assert br['exit_code']==0
vf=c.final_verify();write('independent-live-verify.json',vf)
inv=c.ns.processes();write('final-processes.json',inv)
allowed={p for _,p,_ in c.ns.api_pids()}|set(c.ns.watch_pids())|{psutil.Process().pid}
assert not [p for p in inv if p['pid'] not in allowed]
source=json.loads((N/'source-comparison.json').read_text());pin=json.loads((N/'source-pin.json').read_text());W=Path(pin['worktree'])
assert all(sha(W/p)==v['expected'] for p,v in source.items())
before=json.loads((N/'main-before.json').read_text())
assert subprocess.check_output(['git','-C',str(R),'rev-parse','HEAD'],text=True).strip()==before['head']
assert subprocess.check_output(['git','-C',str(R),'status','--porcelain=v1','--untracked-files=no'],text=True)==before['status']
assert all(sha(R/p)==v for p,v in before['dirty_sha'].items())
assert not subprocess.check_output(['git','-C',str(W),'status','--porcelain'],text=True).strip()
result={};totalbytes=0;totallines=0
for block in s['completed']:
 d=Path(block['path']);meta=json.loads((d/'meta.json').read_text());cfg=json.loads((d/'config.json').read_text());rows=json.loads((d/'results.json').read_text())
 assert len(rows)==(3 if block['arm']=='SMOKE' else 10) and all(not r.get('error') for r in rows)
 assert meta['status']=='OK' and meta['rows']==(3 if block['arm']=='SMOKE' else 10)
 assert meta['binary_sha256']==br['binary_sha256']
 assert meta['priority_gate']['priority']==psutil.ABOVE_NORMAL_PRIORITY_CLASS and meta['priority_gate']['before_first_request']
 f=meta['startup'];assert str(f['slots'])=='3153' and str(f['ram_budget_gib'])=='20.00' and str(f['locked_mib'])=='20479'
 assert cfg['env']['STRATA_NATIVE_PIPE']=='1' and cfg['env']['STRATA_NATIVE_PIPE_CHECK']=='1'
 assert cfg['args'][cfg['args'].index('--pool-workers')+1]=='9' and cfg['args'][cfg['args'].index('--pool-affinity')+1]=='all'
 raw=(d/'engine.log').read_bytes();txt=raw.decode('utf-8');totalbytes+=len(raw);totallines+=len(txt.splitlines())
 assert not any(x in txt for x in ['NATIVE_PIPE FATAL','NATIVE_PIPE_CHECK MISMATCH','MISS_OVERLAP_CHECK MISMATCH'])
 checks=re.findall(r'NATIVE_PIPE_CHECK batches=(\d+) values=(\d+) gu_type=(\d+) down_type=(\d+) mismatch=0',txt)
 pairs=sorted({(int(x[2]),int(x[3])) for x in checks});expected=c.EXPECTED_FORMATS
 if block['arm']=='CHK':assert expected<=set(pairs)
 assert checks
 result[block['arm']]={'requests':meta['rows'],'values_compared_at_least':max(int(x[1]) for x in checks),'mismatches':0,'observed_pairs':pairs,'missing_pairs':sorted(expected-set(pairs)),'log_bytes':len(raw),'log_lines':len(txt.splitlines()),'log_sha256':sha(d/'engine.log'),'meta':meta}
inputs={p.name:sha(p) for p in c.rp.REQ_DIR.glob('*.json')}
old=json.loads((R/'runs/native-pipeline-20261029/audit.json').read_text())
assert all(inputs[k]==v['sha256'] for k,v in old['inputs'].items())
harness={p.name:sha(p) for p in (N/'harness').glob('*.py')}
assert all(sha(R/'runs/native-pipeline-20261029/harness'/k)==v for k,v in harness.items())
current=c.ns.CONFIG;raw=current.read_bytes();assert sha(current)==c.ns.CONFIG_SHA
livecfg=json.loads(raw.decode('utf-8-sig'));lp=psutil.Process(vf['pid']);env=lp.environ()
assert env.get('STRATA_IQ3S_MT1')=='1' and not any(v for k,v in env.items() if k.startswith('STRATA_') and any(x in k for x in ('PIPE','CHECK','DIAG','MT_MIN')) and v!='0')
log=Path(livecfg['log']);text=log.read_text(encoding='utf-8',errors='replace')
ram=re.findall(r'RAM budget ([\d.]+) GiB',text);locked=re.findall(r'locked (\d+) MiB via working-set minimum \+ VirtualLock',text)
assert ram[-1]=='20.00' and locked[-1]=='20479'
write('live-detail.json',dict(pid=lp.pid,creation=lp.create_time(),priority=lp.nice(),env={k:v for k,v in env.items() if k.startswith('STRATA_')},ram_budget_gib=ram[-1],locked_mib=locked[-1],engine_log=str(log),engine_log_sha256=sha(log)))
(N/'live-original.json').write_bytes(raw)
cfg=json.loads(raw.decode('utf-8-sig'));candidate=json.loads(json.dumps(cfg));candidate['exe']=str(N/'build/strata.exe');candidate['env']['STRATA_NATIVE_PIPE']='1'
assert not any(candidate['env'].get(k) for k in ('STRATA_NATIVE_PIPE_CHECK','STRATA_CPU_PHASE_DIAG','STRATA_IQ_MT_MIN'))
# Preserve all original bytes except the two explicitly authorized config changes.
txt=raw.decode('utf-8');txt=txt.replace(json.dumps(cfg['exe']),json.dumps(candidate['exe']),1)
needle='"STRATA_IQ3S_MT1": "1"';assert txt.count(needle)==1
txt=txt.replace(needle,needle+',\r\n        "STRATA_NATIVE_PIPE": "1"')
assert json.loads(txt)==candidate
(N/'candidate-live.json').write_bytes(txt.encode('utf-8'))
diff=''.join(difflib.unified_diff(raw.decode('utf-8').splitlines(True),txt.splitlines(True),fromfile=str(current),tofile=str(N/'candidate-live.json')))
(N/'candidate-config.diff').write_text(diff,encoding='utf-8')
write('audit.json',{'verified':True,'verdict':'READY' if br['binary_sha256']==br['original_binary_sha256'] else 'READY_REBUILT_SHA_DIFFERS','blocks':result,'engine_log_bytes':totalbytes,'engine_log_lines':totallines,'inputs_sha256':inputs,'harness_sha256':harness,'main_unchanged':True,'worktree_clean':True,'live':vf,'candidate_config_sha256':sha(N/'candidate-live.json'),'original_config_sha256':sha(current)})
print(json.dumps({k:v for k,v in json.loads((N/'audit.json').read_text()).items() if k not in ('inputs_sha256','harness_sha256','blocks')},indent=2))

