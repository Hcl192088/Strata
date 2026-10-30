import os,sys,json,time,traceback,statistics,math
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path.insert(0,r'C:\Users\User\Strata-Adrian-control\runs\big-exact-20261030')
import base as c
rp=c.rp;ns=c.ns;c.R=R;rp.make_body=c.make_body
CAND=Path(r'C:\Users\User\nt1ext-20261030\build\strata.exe')
CSHA='FD272B491C4498D4F6F31546B5E1E26BAAD744DE837174F6A507B98718FC129A'
def write(n,v): (R/n).write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
def spec(arm):
 env={'STRATA_NATIVE_PIPE':'1'}
 if arm=='B':env['STRATA_IQ_NT1_EXT']='1'
 return dict(exe=str(ns.EXE_C if arm=='C' else CAND),sha=ns.EXE_C_SHA if arm=='C' else CSHA,serve_dir=rp.SERVE_V0142,env=env,args={},strict_capacity=True,split=False)
c.spec=spec
def audit(arm,d,cfg):
 original=json.loads(ns.CONFIG.read_text(encoding='utf-8-sig'))
 original['exe']=spec(arm)['exe'];original['cwd']=str(Path(spec(arm)['exe']).parent);original['log']=str(d/'engine.log');original['open_browser']=False
 original['env'].update(spec(arm)['env'])
 assert cfg==original,('CONFIG_DIFF',arm)
 assert cfg['env'].get('STRATA_IQ3S_MT1')=='1' and 'STRATA_IQ_MT_MIN' not in cfg['env']
 assert cfg['env'].get('STRATA_IQ_NT1_EXT')==('1' if arm=='B' else None)
def main():
 assert os.environ['COMPUTERNAME']=='DESKTOP-LKMLUPC'
 assert not (R/'campaign.json').exists(),'NO_RERUN'
 ns.log.path=R/'controller.log';c.save(task_id='LUNA-20261012-027',task='NT1_EXT_PHASE2',phase='PREFLIGHT',controller_pid=os.getpid(),authorization='user 2026-10-30 A/B only, restore API, REPORT_LOCAL')
 stopped=False;error=None;blocks=[];pairs=[]
 try:
  c.identity();assert ns.sha(CAND)==CSHA;c.gate('pre-stop',True);write('initial_verify.json',c.verify());m=ns.http_json('/metrics',8);assert m['live']['state']=='idle' and m['live']['queued']==0
  for arm in ('C','B'):
   d=R/('config-audit-'+arm);d.mkdir();_,cfg=rp.build_cfg(arm,spec(arm),d);audit(arm,d,cfg)
  write('sampling.json',{p:{k:v for k,v in c.make_body(p,512).items() if k in ('temperature','top_p','top_k','min_p','seed','max_tokens','presence_penalty')} for p in rp.POINTS})
  (R/'out').mkdir();stopped=True;c.save(phase='STOP_API');ns.stop_api(R);c.gate('after-stop')
  for rnd in range(1,6):
   pair={}
   for arm in (('C','B') if rnd%2 else ('B','C')):
    idx=len(blocks);c.gate('block-start-%02d'%idx);d,rows=c.run(idx,rnd,arm,None,512)
    meta=json.loads((d/'meta.json').read_text());cfg=json.loads((d/'config.json').read_text());audit(arm,d,cfg)
    eff=meta['effective_env'];assert eff.get('STRATA_IQ3S_MT1')=='1' and 'STRATA_IQ_MT_MIN' not in eff
    assert eff.get('STRATA_IQ_NT1_EXT')==('1' if arm=='B' else None)
    log=(d/'engine.log').read_text(encoding='utf-8',errors='replace');active='STRATA_IQ_NT1_EXT active' in log
    assert active==(arm=='B'),('CANDIDATE_NOT_EXERCISED' if arm=='B' else 'CONTROL_FLAG_ACTIVE')
    assert all(x.get('windows') and all(x.get(k) is not None for k in ('gpu_wait_ms','cpu_ms','draft_ms','ms_window')) for x in rows),'TIMING_MISSING'
    n=sum(x['windows'] for x in rows)
    b={'index':idx,'round':rnd,'arm':arm,'path':str(d),'rate':c.rate(rows),'tokens':sum(x['m_out_tokens'] for x in rows),'windows':n,'segments':{k:sum(x[k]*x['windows'] for x in rows)/n for k in ('gpu_wait_ms','cpu_ms','draft_ms','ms_window')},'output_lengths':[x['completion_tokens'] for x in rows],'rows':rows}
    blocks.append(b);pair[arm]=b;write('blocks.json',blocks)
   pairs.append({'round':rnd,'delta_percent':100*(pair['B']['rate']/pair['C']['rate']-1),'cpu_ms_window_diff':pair['B']['segments']['cpu_ms']-pair['C']['segments']['cpu_ms']});write('pairs.json',pairs)
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
