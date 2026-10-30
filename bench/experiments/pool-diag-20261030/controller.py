import os,sys,json,traceback
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path.insert(0,r'C:\Users\User\Strata-Adrian-control\runs\big-exact-20261030')
import base as c
rp=c.rp;ns=c.ns;c.R=R;rp.make_body=c.make_body
CAND=Path(r'C:\Users\User\pooldiag-20261030\build\strata.exe')
CSHA=(R/'candidate.sha').read_text().strip().upper()
def write(n,v): (R/n).write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
def spec(arm):
 env={'STRATA_NATIVE_PIPE':'1'}
 if arm=='D':env['STRATA_POOL_DIAG']='1'
 return dict(exe=str(ns.EXE_C if arm=='C' else CAND),sha=ns.EXE_C_SHA if arm=='C' else CSHA,serve_dir=rp.SERVE_V0142,env=env,args={},strict_capacity=True,split=False)
c.spec=spec
def audit(arm,d,cfg):
 original=json.loads(ns.CONFIG.read_text(encoding='utf-8-sig'))
 original['exe']=spec(arm)['exe'];original['cwd']=str(Path(spec(arm)['exe']).parent);original['log']=str(d/'engine.log');original['open_browser']=False
 original['env'].update(spec(arm)['env'])
 assert cfg==original,('CONFIG_DIFF',arm)
 assert cfg['env'].get('STRATA_IQ3S_MT1')=='1' and 'STRATA_IQ_MT_MIN' not in cfg['env']
 assert cfg['env'].get('STRATA_POOL_DIAG')==('1' if arm=='D' else None)
def main():
 assert os.environ['COMPUTERNAME']=='DESKTOP-LKMLUPC'
 assert not (R/'campaign.json').exists(),'NO_RERUN'
 ns.log.path=R/'controller.log';c.save(task_id='LUNA-20261012-027',task='POOL_DIAG',phase='PREFLIGHT',controller_pid=os.getpid(),authorization='user 2026-10-30 C/D diagnostic and restore')
 stopped=False;error=None;blocks=[]
 try:
  c.identity();assert ns.sha(CAND)==CSHA;c.gate('pre-stop',True);write('initial_verify.json',c.verify());m=ns.http_json('/metrics',8);assert m['live']['state']=='idle' and m['live']['queued']==0
  for arm in ('C','D'):
   d=R/('config-audit-'+arm);d.mkdir();_,cfg=rp.build_cfg(arm,spec(arm),d);audit(arm,d,cfg)
  write('sampling.json',{p:c.make_body(p,512) for p in ('p01','p05','p08')})
  (R/'out').mkdir();stopped=True;c.save(phase='STOP_API');ns.stop_api(R);c.gate('after-stop')
  for idx,arm in enumerate(('C','D','C','D')):
   rnd=idx//2+1;c.gate('block-start-%02d'%idx);d,rows=c.run(idx,rnd,arm,['p01','p05','p08'],512)
   meta=json.loads((d/'meta.json').read_text());cfg=json.loads((d/'config.json').read_text());audit(arm,d,cfg)
   log=(d/'engine.log').read_text(encoding='utf-8',errors='replace');lines=[l for l in log.splitlines() if l.startswith('POOL_DIAG ')]
   assert len(lines)==(3 if arm=='D' else 0),('POOL_DIAG_LINES',arm,len(lines))
   n=sum(x['windows'] for x in rows);assert n and all(x.get('ms_window') is not None for x in rows)
   blocks.append({'index':idx,'round':rnd,'arm':arm,'path':str(d),'rate':c.rate(rows),'windows':n,'ms_window':sum(x['ms_window']*x['windows'] for x in rows)/n,'rows':rows,'pool_diag':lines});write('blocks.json',blocks)
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
