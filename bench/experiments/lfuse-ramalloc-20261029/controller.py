"""One LFUSE sampled-replay A/B; exact original sampling; no deployment."""
import json,os,re,sys,time,traceback,statistics
from pathlib import Path
import psutil
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'harness'))
import replay_ab_20261027 as rp
ns=rp.ns
ns.EXE_C=ns.CONTROL_ROOT/'runs/native-pipe-deploy-prep-20261029/build/strata.exe'
ns.EXE_C_SHA='A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8'
ns.CONFIG_SHA='060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93'
KEYS=['STRATA_'+x for x in ['DF_QB_Q4','DF_BRANCH','GDN_SPLIT','LFUSE','QFUSE','TSUM','MMVF_ROWS','ATTN_LANECELL']]
S={};ROWS=[];PAIRS=[]

def write(n,x):
 p=R/n;t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(x,indent=2,ensure_ascii=False),encoding='utf-8');t.replace(p)
def save(**kw):
 S.update(kw,utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()));write('campaign.json',S)
def identity():
 best=json.loads((ns.CONTROL_ROOT/'bench/results/2026-10-29-native-pipe/BEST.json').read_text(encoding='utf-8-sig'))
 assert best['binary_sha256']==ns.EXE_C_SHA and best['config_sha256']==ns.CONFIG_SHA
 assert ns.sha(ns.EXE_C)==ns.EXE_C_SHA and ns.sha(ns.CONFIG)==ns.CONFIG_SHA
def gate(tag,live=False):
 identity();p=ns.processes();write('processes-'+tag+'.json',p)
 allowed={pid for _,pid,_ in ns.api_pids()}|set(ns.watch_pids()) if live else rp.own_pids()
 assert not [x for x in p if x['pid'] not in allowed],('PROCESS_GATE',p)
def verify():
 identity();h=ns.http_json('/health',8);m=ns.http_json('/metrics',8)
 es=[p for p in psutil.process_iter(['name']) if (p.info['name'] or '').lower()=='strata.exe'];assert len(es)==1
 p=es[0];env=p.environ();assert ns.sha(p.exe())==ns.EXE_C_SHA and h['loaded']
 cfg=json.loads(ns.CONFIG.read_text(encoding='utf-8-sig'))
 assert all(env.get(k)==v for k,v in cfg['env'].items())
 assert not any(k in env for k in KEYS)
 assert p.nice()==psutil.ABOVE_NORMAL_PRIORITY_CLASS
 assert m['engine']['expert_slots']==3153 and m['engine']['arena_mib']==20479
 text=Path(cfg['log']).read_text(encoding='utf-8',errors='replace');text=text[text.rfind('engine started:'):]
 facts=ns.startup_facts(text);assert facts['ram_budget_gib']=='20.00' and facts['locked_mib']=='20479'
 return {'verified':True,'pid':p.pid,'priority':p.nice(),'binary_sha256':ns.EXE_C_SHA,
         'config_sha256':ns.CONFIG_SHA,'health':h,'engine':m['engine'],'startup':facts}
def spec(arm):
 env={'STRATA_NATIVE_PIPE':'1'}
 if arm=='F':env['STRATA_LFUSE']='1'
 return dict(exe=str(ns.EXE_C),sha=ns.EXE_C_SHA,serve_dir=rp.SERVE_V0142,env=env,args={},strict_capacity=True,split=False)

def make_body(point,max_tokens):
 original=json.loads((rp.REQ_DIR/(point+'.json')).read_text(encoding='utf-8'))
 body=json.loads(json.dumps(original));body['max_tokens']=max_tokens
 assert {k:v for k,v in body.items() if k!='max_tokens'}=={k:v for k,v in original.items() if k!='max_tokens'}
 return body
rp.make_body=make_body

def text_of(d,p):
 r=json.loads((d/('resp-'+p+'.json')).read_text(encoding='utf-8'))
 m=r['choices'][0]['message']
 return (m.get('reasoning_content') or '')+'\n'+(m.get('content') or '')+json.dumps(m.get('tool_calls') or [],sort_keys=True,ensure_ascii=False)
def prefix(a,b):
 return next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),min(len(a),len(b)))
def repeated(text):
 words=re.findall(r'[A-Za-z]+',text.lower())
 for n in range(2,7):
  for i in range(len(words)-4*n+1):
   q=words[i:i+n]
   if all(words[i+j*n:i+(j+1)*n]==q for j in (1,2,3)):
    return True
 return False
def rate(rows):
 tokens=sum(float(x['m_out_tokens']) for x in rows)
 ms=sum(float(x['m_decode_ms']) for x in rows)
 assert tokens>0 and ms>0
 return tokens/ms*1000

def run(index,rnd,arm,points=None,tokens=512):
 gate('block-%02d'%index);save(phase='BLOCK',current={'index':index,'round':rnd,'arm':arm})
 old=rp.POINTS
 if points is not None:rp.POINTS=points
 try:meta,rows=rp.run_block(R/'out',index,rnd,arm,spec(arm),tokens)
 finally:rp.POINTS=old
 d=R/'out'/('block-%02d-%s-r%d'%(index,arm,rnd))
 text=(d/'engine.log').read_text(encoding='utf-8',errors='replace') if (d/'engine.log').exists() else ''
 S.setdefault('completed',[]).append({'index':index,'round':rnd,'arm':arm,'path':str(d),'status':meta['status']});save()
 assert meta['status']=='OK' and len(rows)==len(points or old),(arm,meta)
 assert 'NATIVE_PIPE ACTIVE' in text
 assert not re.search(r'(?i)(NATIVE_PIPE FATAL|CUDA error|CUDA_ERROR|fatal error|NATIVE_PIPE_CHECK MISMATCH|check_mismatch_rows=[1-9][0-9]*)',text)
 bad=[p for p in (points or old) if repeated(text_of(d,p))]
 write('quality-block-%02d.json'%index,{'repeated_points':bad,'semantic_parity':'NOT_MEASURED','operator_bitwise':'NOT_MEASURED'})
 assert not bad,('BROKEN_REPETITION',arm,bad)
 ROWS.extend(rows);write('rows.json',ROWS)
 return d,rows

def prepare():
 identity();gate('prelaunch',True)
 write('prelaunch_verify.json',verify())
 cfg=json.loads(ns.CONFIG.read_text(encoding='utf-8-sig'));audits=[]
 for arm in ('C','F'):
  d=R/('config-audit-'+arm);d.mkdir(exist_ok=True);_,got=rp.build_cfg(arm,spec(arm),d)
  expected=json.loads(json.dumps(cfg));expected['cwd']=str(ns.EXE_C.parent);expected['log']=str(d/'engine.log')
  if arm=='F':expected['env']['STRATA_LFUSE']='1'
  assert got==expected,('CONFIG_DIFF',arm)
  audits.append({'arm':arm,'allowed_diff_only':True,'config_sha256':ns.sha(d/'config.json')})
 sampling={}
 for p in rp.POINTS:
  body=make_body(p,512)
  assert body.get('temperature')==1.0 and body.get('seed')==1000+int(p[1:])
  sampling[p]={k:body[k] for k in ('temperature','top_p','top_k','min_p','seed','presence_penalty','reasoning_effort') if k in body}
 write('sampling.json',sampling);write('config-audit.json',audits)
 write('inputs.json',{'requests':{p.name:ns.sha(p) for p in rp.REQ_DIR.glob('p*.json')},
       'harness':{p.name:ns.sha(p) for p in (R/'harness').glob('*.py')},'controller_sha256':ns.sha(Path(__file__))})
 print('PREPARED: exact original temp1/top_p/top_k/min_p/seeds preserved; config C/F allowed diff only',flush=True)

def main():
 assert os.environ['COMPUTERNAME']=='DESKTOP-LKMLUPC'
 assert not (R/'campaign.json').exists(),'TERMINAL_OR_RUNNING_NO_RERUN'
 ns.log.path=R/'controller.log';save(task_id='LUNA-20261012-027',task='LFUSE_AB',phase='PREFLIGHT',controller_pid=os.getpid(),authorization='user2026-10-29 好去測看看; LFUSE8 paired rounds, restore existing API; no deployment')
 stopped=False;error=None
 try:
  prepare();gate('pre-stop',True);write('initial_verify.json',verify())
  (R/'out').mkdir();write('rows.json',[])
  stopped=True;ns.stop_api(R);gate('after-stop')
  smoke=[]
  for i,arm in enumerate(('C','F','C')):
   d,rows=run(i,0,arm,['p01','p05','p08'],128);smoke.append(d)
  q=[]
  for p in ('p01','p05','p08'):
   a,b,c=[text_of(d,p) for d in smoke]
   q.append({'point':p,'AA_prefix_chars':prefix(a,c),'F_vs_C_prefix_chars':prefix(a,b),
             'F_vs_C2_prefix_chars':prefix(c,b),'identical_to_C':a==b})
  write('smoke-exactness.json',q)
  assert not all(max(x['F_vs_C_prefix_chars'],x['F_vs_C2_prefix_chars'])<x['AA_prefix_chars'] for x in q),'SMOKE_EXTRA_EARLY_DIVERGENCE_ALL3'
  i=3
  for rnd in range(1,9):
   blocks={}
   for arm in (('C','F') if rnd%2 else ('F','C')):
    d,rows=run(i,rnd,arm);blocks[arm]=rows;i+=1
   delta=100*(rate(blocks['F'])/rate(blocks['C'])-1)
   PAIRS.append({'round':rnd,'C_tok_s':rate(blocks['C']),'F_tok_s':rate(blocks['F']),'delta_percent':delta})
   write('pairs.json',PAIRS);save(pair_count=len(PAIRS),last_pair=PAIRS[-1])
   if rnd==3 and (all(x['delta_percent']<0 for x in PAIRS) or statistics.mean(x['delta_percent'] for x in PAIRS)<-3):
    save(verdict='REJECT_EARLY');break
  else:
   ds=[p['delta_percent'] for p in PAIRS];mean=statistics.mean(ds);half=2.364624251*statistics.stdev(ds)/(8**0.5)
   write('primary.json',{'n_rounds':8,'mean_delta_percent':mean,'ci95':[mean-half,mean+half],
        'speed_gate_pass':mean>=3 and mean-half>0,'quality_parity':'INCONCLUSIVE_NO_OPERATOR_TEST','deployment':False})
   save(verdict='SPEED_PASS_QUALITY_UNCONFIRMED' if mean>=3 and mean-half>0 else 'REJECT_NO_3PCT_CONFIRMED_GAIN')
 except BaseException:
  error=traceback.format_exc();save(error=error,phase='ERROR')
 finally:
  save(before_restore_phase=S.get('phase'),phase='RESTORE')
  try:
   if stopped:gate('pre-restore');restore=ns.restore_api(R)
   else:restore={'restored':True,'not_stopped':True}
  except BaseException:restore={'restored':False,'error':traceback.format_exc()}
  try:v=verify()
  except BaseException:v={'verified':False,'error':traceback.format_exc()}
  write('restore.json',restore);write('final_verify.json',v)
  save(phase='DONE' if error is None and v['verified'] else 'FAILED',restored=restore.get('restored'),verified=v['verified'])

if __name__=='__main__':
 if '--prepare' in sys.argv:prepare()
 else:main()
