import json,os,re,sys,time,traceback,subprocess,statistics as st
from pathlib import Path
import psutil
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'harness'))
import replay_ab_20261027 as rp
ns=rp.ns
ns.EXE_C=ns.CONTROL_ROOT/'runs/native-pipe-deploy-prep-20261029/build/strata.exe'
ns.EXE_C_SHA='A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8'
ns.CONFIG_SHA='060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93'
EXE=ns.EXE_C
SHA=ns.sha(EXE) if EXE.exists() else None
KEYS=['STRATA_'+x for x in ['DF_QB_Q4','DF_BRANCH','GDN_SPLIT','LFUSE','QFUSE','TSUM','MMVF_ROWS','ATTN_LANECELL']]
S={};ROWS=[]
def write(n,x):
 p=R/n;t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(x,indent=2,ensure_ascii=False),encoding='utf-8');t.replace(p)
def save(**kw):
 S.update(kw,utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()));write('campaign.json',S)
def identity():
 best=json.loads((ns.CONTROL_ROOT/'bench/results/2026-10-29-native-pipe/BEST.json').read_text(encoding='utf-8-sig'))
 assert best['binary_sha256']==ns.EXE_C_SHA and best['config_sha256']==ns.CONFIG_SHA,'current-best manifest mismatch'
 assert ns.sha(ns.EXE_C)==ns.EXE_C_SHA and ns.sha(ns.CONFIG)==ns.CONFIG_SHA
 assert ns.sha(EXE)==SHA

def gate(tag,live=False):
 identity();p=ns.processes();write('processes-'+tag+'.json',p)
 allowed={pid for _,pid,_ in ns.api_pids()}|set(ns.watch_pids()) if live else rp.own_pids()
 assert not [x for x in p if x['pid'] not in allowed],('process gate',p)

def verify():
 identity();h=ns.http_json('/health',8);m=ns.http_json('/metrics',8)
 es=[p for p in psutil.process_iter(['name']) if (p.info['name'] or '').lower()=='strata.exe'];assert len(es)==1
 p=es[0];env=p.environ();assert ns.sha(p.exe())==ns.EXE_C_SHA
 assert env.get('STRATA_NATIVE_PIPE')=='1' and env.get('STRATA_IQ3S_MT1')=='1'
 assert not any(k in env for k in KEYS)
 assert not any(env.get(k) for k in ['STRATA_NATIVE_PIPE_CHECK','STRATA_PCIE_BALANCE','STRATA_PARTIAL_PIN','STRATA_CPU_PHASE_DIAG'])
 assert p.nice()==psutil.ABOVE_NORMAL_PRIORITY_CLASS and h['loaded'];assert '--spec-split' not in p.cmdline()
 cfg=json.loads(ns.CONFIG.read_text(encoding='utf-8-sig'));text=Path(cfg['log']).read_text(encoding='utf-8',errors='replace');text=text[text.rfind('engine started:'):];facts=ns.startup_facts(text)
 assert str(m['engine']['expert_slots'])=='3153' and str(m['engine']['arena_mib'])=='20479'
 assert facts['ram_budget_gib']=='20.00' and facts['locked_mib']=='20479'
 return dict(verified=True,pid=p.pid,binary_sha256=ns.EXE_C_SHA,config_sha256=ns.CONFIG_SHA,priority=p.nice(),env={k:env.get(k) for k in ['STRATA_NATIVE_PIPE','STRATA_IQ3S_MT1']+KEYS},health=h,engine=m['engine'],startup=facts)
def spec(a):
 env=dict(STRATA_NATIVE_PIPE='1')
 if a!='C':env.update({k:'1' for k in KEYS})
 return dict(exe=str(EXE),sha=SHA,serve_dir=rp.SERVE_V0142,env=env,args={},strict_capacity=True,split=False)

def run(i,rd,a,points=None,tokens=512):
 gate('block-%02d'%i);save(phase='BLOCK',current=dict(index=i,round=rd,arm=a))
 old=rp.POINTS
 if points:rp.POINTS=points
 try:meta,rows=rp.run_block(R/'out',i,rd,a,spec(a),tokens)
 finally:rp.POINTS=old
 d=R/'out'/('block-%02d-%s-r%d'%(i,a,rd));text=(d/'engine.log').read_text(encoding='utf-8',errors='replace')
 S.setdefault('completed',[]).append(dict(index=i,round=rd,arm=a,path=str(d),status=meta['status']));save()
 assert meta['status']=='OK' and len(rows)==len(points or old),(a,meta)
 assert 'NATIVE_PIPE ACTIVE' in text and 'NATIVE_PIPE FATAL' not in text and 'NATIVE_PIPE_CHECK MISMATCH' not in text
 active=[line for line in text.splitlines() if any(k in line for k in KEYS)]
 write('switch-active-'+a+'-r%d.json'%rd,dict(log_lines=active,env_verified_in_meta=True,evidence_limit='Effective engine env verified; dedicated log marker may be absent; no per-kernel counters'))
 assert not re.search(r'(?i)(NATIVE_PIPE FATAL|CUDA error|CUDA_ERROR|fatal error)',text), 'fatal/CUDA error'
 if a in ['C','G']:ROWS.extend(rows);write('rows.json',ROWS)

 return True

def rates():
 g={}
 for r in ROWS:g.setdefault((r['round'],r['arm']),[]).append(r)
 return {k:sum(r['m_out_tokens'] for r in rs)*1000/sum(r['m_decode_ms'] for r in rs) for k,rs in g.items()}
def main():
 assert os.environ['COMPUTERNAME']=='DESKTOP-LKMLUPC'
 assert not (R/'campaign.json').exists()
 ns.log.path=R/'controller.log';save(task_id='LUNA-20261012-027',task='GPU_EXACT_BUNDLE',phase='PREFLIGHT',candidate_sha=SHA,controller_pid=os.getpid(),authorization='2026-10-29 user GPU_EXACT_BUNDLE brief attempt 2; env-only benchmark; no source/build/live-config/GitHub writes')
 stopped=False;error=None
 try:
  gate('pre-stop',True);write('initial_verify.json',verify());write('rows.json',[])
  cfg=json.loads(ns.CONFIG.read_text(encoding='utf-8-sig'));evidence=[]
  for a in ['C','G','SMOKE']:
   d=R/('config-audit-'+a);d.mkdir();_,c=rp.build_cfg(a,spec(a),d)
   expected=json.loads(json.dumps(cfg));expected['cwd']=str(EXE.parent);expected['log']=str(d/'engine.log')
   if a!='C':expected['env'].update({k:'1' for k in KEYS})
   assert c==expected,(a,'unexpected config diff')
   evidence.append(dict(arm=a,equal_except_authorized=True,config=c,config_sha256=ns.sha(d/'config.json')))
  write('config-audit.json',evidence)
  write('inputs.json',dict(requests={p.name:ns.sha(p) for p in rp.REQ_DIR.glob('*.json')},harness={p.name:ns.sha(p) for p in (R/'harness').glob('*.py')}))
  (R/'out').mkdir();stopped=True;ns.stop_api(R);gate('after-stop')
  run(0,0,'SMOKE',['p01','p05','p08'],512)
  i=0
  for rd in range(1,6):
   for a in (['C','G'] if rd%2 else ['G','C']):i+=1;run(i,rd,a)
   rt=rates();vals=[100*(rt[(j,'G')]/rt[(j,'C')]-1) for j in range(1,rd+1)];write('round-deltas.json',vals)
   if rd==3:
    mean=st.mean(vals);err=4.302652729911275*st.stdev(vals)/(3**0.5);lo,hi=mean-err,mean+err
    stop=all(x<0 for x in vals) or mean < -3
    extend=not stop and (0<=mean<=5 or lo<=0<=hi)
    write('round3-decision.json',dict(mean_pct=mean,ci95_pct=[lo,hi],df=2,all_negative=all(x<0 for x in vals),early_stop=stop,extend_to_5=extend))
    if stop:save(verdict='EARLY_STOP');break
    if not extend:save(verdict='MEASURE_COMPLETE_3');break
  if 'verdict' not in S:save(verdict='MEASURE_COMPLETE')
 except BaseException:error=traceback.format_exc();save(error=error,phase='ERROR')
 finally:
  save(before_restore_phase=S.get('phase'),phase='RESTORE')
  if stopped:
   gate('pre-restore');restore=ns.restore_api(R)
  else:restore=dict(restored=True,not_stopped=True)
  try:v=verify()
  except BaseException:v=dict(verified=False,error=traceback.format_exc())
  write('final_verify.json',v);save(phase='DONE' if error is None and v['verified'] else 'FAILED',restored=restore.get('restored'),verified=v['verified'])
if __name__=='__main__':main()
