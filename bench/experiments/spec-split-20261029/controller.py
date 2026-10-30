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
S={};ROWS=[]
FORMATS={(21,20),(16,20),(16,42),(21,42),(17,20),(17,42),(18,20),(18,42),(22,20),(22,42)}
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
 assert not any(env.get(k) for k in ['STRATA_NATIVE_PIPE_CHECK','STRATA_PCIE_BALANCE','STRATA_PARTIAL_PIN','STRATA_CPU_PHASE_DIAG'])
 assert p.nice()==psutil.ABOVE_NORMAL_PRIORITY_CLASS and h['loaded'];assert '--spec-split' not in p.cmdline()
 cfg=json.loads(ns.CONFIG.read_text(encoding='utf-8-sig'));text=Path(cfg['log']).read_text(encoding='utf-8',errors='replace');text=text[text.rfind('engine started:'):];facts=ns.startup_facts(text)
 assert str(m['engine']['expert_slots'])=='3153' and str(m['engine']['arena_mib'])=='20479'
 assert facts['ram_budget_gib']=='20.00' and facts['locked_mib']=='20479'
 return dict(verified=True,pid=p.pid,binary_sha256=ns.EXE_C_SHA,config_sha256=ns.CONFIG_SHA,priority=p.nice(),env={k:env.get(k) for k in ['STRATA_NATIVE_PIPE','STRATA_IQ3S_MT1']},health=h,engine=m['engine'],startup=facts)
build0=rp.build_cfg
def build_cfg(a,spec,d):
 p,c=build0(a,spec,d)
 if a!='C':c['args'].append('--spec-split')
 p.write_text(json.dumps(c,indent=1),encoding='utf-8')
 return p,c
rp.build_cfg=build_cfg

def spec(a):
 env=dict(STRATA_NATIVE_PIPE='1',STRATA_NATIVE_PIPE_CHECK='1' if a in ['SMOKE','CHK'] else None)
 return dict(exe=str(EXE),sha=SHA,serve_dir=rp.SERVE_V0142,env=env,args={},strict_capacity=True,split=a!='C')

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
 if a in ['SMOKE','CHK']:
  hits=re.findall(r'NATIVE_PIPE_CHECK batches=(\d+) values=(\d+) gu_type=(\d+) down_type=(\d+) mismatch=0',text);seen={(int(x[2]),int(x[3])) for x in hits}
  write('check-'+a+'.json',dict(seen=sorted(seen),expected=sorted(FORMATS),missing=sorted(FORMATS-seen),checks=len(hits),values=sum(int(x[1]) for x in hits)));assert hits
  if a=='CHK':assert FORMATS<=seen
 if a in ['SMOKE','CHK']:
  assert any(float(re.search(r'avg T ([\d.]+)',r['timing_line']).group(1))>1 for r in rows), 'no multi-token window timing evidence'
  write('split-active-'+a+'.json',dict(runtime_flag=True,source_condition='split_ && T>=2 && !batch_rec_ => G=2',timing_rows=rows,captured=re.findall(r'strata verify: captured the (\d+)-token window',text),evidence_limit='No dedicated split marker or graph count in default log; source/args plus multi-token timing evidence'))
 if a in ['C','S']:ROWS.extend(rows);write('rows.json',ROWS)
 return True

def rates():
 g={}
 for r in ROWS:g.setdefault((r['round'],r['arm']),[]).append(r)
 return {k:sum(r.get('m_out_tokens') or r['tokens'] for r in rs)*1000/sum(r.get('m_decode_ms') or r['decode_ms'] for r in rs) for k,rs in g.items()}
def main():
 assert os.environ['COMPUTERNAME']=='DESKTOP-LKMLUPC'
 assert not (R/'campaign.json').exists()
 ns.log.path=R/'controller.log';save(task_id='LUNA-20261012-027',task='SPEC_SPLIT',phase='PREFLIGHT',candidate_sha=SHA,controller_pid=os.getpid(),authorization='2026-10-29 user SPEC_SPLIT brief; authorized 測')
 stopped=False;error=None
 try:
  gate('pre-stop',True);write('initial_verify.json',verify());write('rows.json',[])
  cfg=json.loads(ns.CONFIG.read_text(encoding='utf-8-sig'));evidence=[]
  for a in ['C','S','SMOKE','CHK']:
   d=R/('config-audit-'+a);d.mkdir();_,c=rp.build_cfg(a,spec(a),d)
   expected=json.loads(json.dumps(cfg));expected['cwd']=str(EXE.parent);expected['log']=str(d/'engine.log')
   if a!='C':expected['args'].append('--spec-split')
   if a in ['SMOKE','CHK']:expected['env']['STRATA_NATIVE_PIPE_CHECK']='1'
   assert c==expected,(a,'unexpected config diff')
   evidence.append(dict(arm=a,equal_except_authorized=True,config=c,config_sha256=ns.sha(d/'config.json')))
  write('config-audit.json',evidence)
  write('inputs.json',dict(requests={p.name:ns.sha(p) for p in rp.REQ_DIR.glob('*.json')},harness={p.name:ns.sha(p) for p in (R/'harness').glob('*.py')}))
  (R/'out').mkdir();stopped=True;ns.stop_api(R);gate('after-stop')
  run(0,0,'SMOKE',['p01','p05','p08'],128);run(1,0,'CHK',tokens=128)
  i=1
  for rd in range(1,6):
   for a in (['C','S'] if rd%2 else ['S','C']):i+=1;run(i,rd,a)
   rt=rates();vals=[100*(rt[(j,'S')]/rt[(j,'C')]-1) for j in range(1,rd+1)];write('round-deltas.json',vals)
   if rd==3 and (all(x<0 for x in vals) or st.mean(vals)<-3):save(verdict='EARLY_STOP');break
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
