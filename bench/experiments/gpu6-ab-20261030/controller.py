import os,sys,json,time,traceback,statistics,math,re
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path.insert(0,r'C:\Users\User\Strata-Adrian-control\runs\big-exact-20261030')
import base as c
rp=c.rp;ns=c.ns;c.R=R;rp.make_body=c.make_body
FLAGS=['STRATA_DF_BRANCH','STRATA_MMVF_ROWS','STRATA_DF_QB_Q4','STRATA_DF_PLE','STRATA_ATTN_LANECELL','STRATA_EXPERT_V2']
FORBIDDEN=['STRATA_'+x for x in ('GDN_SPLIT','TSUM','LFUSE','QFUSE','FUSE_HEAD_GR','GR_DOWN_MAX4')]
http_original=rp.http_local
current={'arm':None,'dir':None}
def checked_http(path,body=None,timeout=900):
 result=http_original(path,body,timeout)
 d=current['dir']
 if d and (d/'engine.log').exists():
  log=(d/'engine.log').read_text(encoding='utf-8',errors='replace')
  if re.search(r'(?i)\bfatal\b|cuda[_ ]error',log): raise RuntimeError('FATAL_OR_CUDA_ERROR in '+str(d/'engine.log'))
 if path=='/v1/chat/completions' and current['arm']=='B':
  msg=result['choices'][0]['message']
  s=(msg.get('reasoning_content') or '')+'\n'+(msg.get('content') or '')+json.dumps(msg.get('tool_calls') or [],ensure_ascii=False)
  if re.search(r'(.{30,}?)\1{3}',s,re.DOTALL): raise RuntimeError('REPETITION_LOOP in '+str(d))
 return result
rp.http_local=checked_http
c.repeated=lambda text:False
def write(n,v): (R/n).write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
def spec(arm):
 env={'STRATA_NATIVE_PIPE':'1'}
 if arm=='B':env.update({k:'1' for k in FLAGS})
 return dict(exe=str(ns.EXE_C),sha=ns.EXE_C_SHA,serve_dir=rp.SERVE_V0142,env=env,args={},strict_capacity=True,split=False)
c.spec=spec
def audit(arm,d,cfg):
 original=json.loads(ns.CONFIG.read_text(encoding='utf-8-sig'))
 original['exe']=spec(arm)['exe'];original['cwd']=str(Path(spec(arm)['exe']).parent);original['log']=str(d/'engine.log');original['open_browser']=False
 original['env'].update(spec(arm)['env'])
 assert cfg==original,('CONFIG_DIFF',arm)
 assert cfg['env'].get('STRATA_IQ3S_MT1')=='1' and 'STRATA_IQ_MT_MIN' not in cfg['env']
 assert all(cfg['env'].get(k)==('1' if arm=='B' else None) for k in FLAGS)
 assert all(k not in cfg['env'] for k in FORBIDDEN)
def main():
 assert os.environ['COMPUTERNAME']=='DESKTOP-LKMLUPC'
 assert not (R/'campaign.json').exists(),'NO_RERUN'
 ns.log.path=R/'controller.log';c.save(task_id='LUNA-20261012-027',task='GPU6_BUNDLE_AB',phase='PREFLIGHT',controller_pid=os.getpid(),authorization='user 2026-10-30 A/B only, restore API, REPORT_LOCAL')
 stopped=False;error=None;blocks=[];pairs=[]
 try:
  c.identity();c.gate('pre-stop',True);write('initial_verify.json',c.verify());m=ns.http_json('/metrics',8);assert m['live']['state']=='idle' and m['live']['queued']==0
  for arm in ('C','B'):
   d=R/('config-audit-'+arm);d.mkdir();_,cfg=rp.build_cfg(arm,spec(arm),d);audit(arm,d,cfg)
  write('sampling.json',{p:{k:v for k,v in c.make_body(p,512).items() if k in ('temperature','top_p','top_k','min_p','seed','max_tokens','presence_penalty')} for p in rp.POINTS})
  (R/'out').mkdir();stopped=True;c.save(phase='STOP_API');ns.stop_api(R);c.gate('after-stop')
  for rnd in range(1,6):
   pair={}
   for arm in (('C','B') if rnd%2 else ('B','C')):
    idx=len(blocks);c.gate('block-start-%02d'%idx);current.update(arm=arm,dir=R/'out'/('block-%02d-%s-r%d'%(idx,arm,rnd)));d,rows=c.run(idx,rnd,arm,None,512);current.update(arm=None,dir=None)
    meta=json.loads((d/'meta.json').read_text());cfg=json.loads((d/'config.json').read_text());audit(arm,d,cfg)
    eff=meta['effective_env'];assert eff.get('STRATA_IQ3S_MT1')=='1' and 'STRATA_IQ_MT_MIN' not in eff
    assert all(eff.get(k)==('1' if arm=='B' else None) for k in FLAGS)
    assert all(k not in eff for k in FORBIDDEN)
    log=(d/'engine.log').read_text(encoding='utf-8',errors='replace');assert not re.search(r'(?i)\bfatal\b|cuda[_ ]error',log),('FATAL_OR_CUDA_ERROR',str(d))
    assert all(x.get('windows') and all(x.get(k) is not None for k in ('gpu_wait_ms','cpu_ms','draft_ms','ms_window')) for x in rows),'TIMING_MISSING'
    n=sum(x['windows'] for x in rows)
    b={'index':idx,'round':rnd,'arm':arm,'path':str(d),'rate':c.rate(rows),'tokens':sum(x['m_out_tokens'] for x in rows),'windows':n,'segments':{k:sum(x[k]*x['windows'] for x in rows)/n for k in ('gpu_wait_ms','cpu_ms','draft_ms','ms_window')},'output_lengths':[x['completion_tokens'] for x in rows],'rows':rows}
    blocks.append(b);pair[arm]=b;write('blocks.json',blocks)
   pairs.append({'round':rnd,'delta_percent':100*(pair['B']['rate']/pair['C']['rate']-1),'gpu_wait_ms_window_diff':pair['B']['segments']['gpu_wait_ms']-pair['C']['segments']['gpu_wait_ms']});write('pairs.json',pairs)
   if rnd==3 and (all(x['delta_percent']<0 for x in pairs) or statistics.mean(x['delta_percent'] for x in pairs)<-3):break
  ds=[p['delta_percent'] for p in pairs];n=len(ds);t={3:4.3026527299,5:2.7764451052}[n];mean=statistics.mean(ds);half=t*statistics.stdev(ds)/math.sqrt(n)
  write('result.json',{'rounds':n,'pairs':pairs,'mean_percent':mean,'ci95_percent':[mean-half,mean+half],'quality':'UNCONFIRMED','early_stop':n==3})
 except BaseException:
  error=traceback.format_exc();c.save(phase='ERROR',error=error)
 finally:
  c.save(phase='RESTORE')
  try:
   if stopped:c.gate('pre-restore');restore=ns.restore_api(R)
   else:restore={'restored':True,'not_stopped':True}
  except BaseException:restore={'restored':False,'error':traceback.format_exc()}
  try:v=c.verify()
  except BaseException:v={'verified':False,'error':traceback.format_exc()}
  write('restore.json',restore);write('final_verify.json',v);c.save(phase='DONE' if error is None and v.get('verified') and restore.get('restored') else 'FAILED',restored=restore.get('restored'),verified=v.get('verified'),error=error)
if __name__=='__main__':main()
