import json,os,re,sys,time,subprocess,traceback
from pathlib import Path
import psutil
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R));import base as c
rp=c.rp;ns=c.ns
state={}
def save(**kw):
 state.update(kw,utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()));c.write('campaign.json',state)
def block(index,arm,points,tokens,exe,sha):
 c.gate('pre-'+arm)
 d=R/'out'/('block-%02d-%s-r0'%(index,arm))
 env={'STRATA_NATIVE_PIPE':'1','STRATA_CPU_PHASE_DIAG':'1','STRATA_IO_ARRIVAL_DIAG':str(d/'arrivals.csv')}
 if arm=='SMOKE':env['STRATA_NATIVE_PIPE_CHECK']='1'
 spec=dict(exe=str(exe),sha=sha,serve_dir=rp.SERVE_V0142,env=env,args={},strict_capacity=True,split=False)
 old=rp.POINTS;rp.POINTS=points;save(phase=arm)
 try:meta,rows=rp.run_block(R/'out',index,0,arm,spec,tokens)
 finally:rp.POINTS=old
 c.write(arm+'-rows.json',rows);c.write(arm+'-meta.json',meta)
 assert meta['status']=='OK' and len(rows)==len(points),(arm,meta)
 text=(d/'engine.log').read_text(encoding='utf-8',errors='replace')
 assert 'NATIVE_PIPE ACTIVE' in text
 assert not re.search(r'(?i)(NATIVE_PIPE FATAL|CUDA error|CUDA_ERROR|fatal error|NATIVE_PIPE_CHECK MISMATCH|MISS_OVERLAP_CHECK MISMATCH|check_mismatch_rows=[1-9][0-9]*|IO_ARRIVAL_DIAG (?:LIMIT|event failure|wait failure))',text)
 assert not any(c.repeated(c.text_of(d,p)) for p in points)
 assert len(re.findall(r'^CPU_PHASE_DECODE ',text,re.M))==len(points)
 lines=(d/'arrivals.csv').read_text().splitlines()
 assert sum(x.startswith('B,') for x in lines)==len(points)
 assert sum(x.startswith('E,') for x in lines)==len(points)
 assert any(x.startswith('Q,') for x in lines) and any(x.startswith('D,') for x in lines)
 if arm=='SMOKE':
  checks=re.findall(r'NATIVE_PIPE_CHECK batches=(\d+) values=(\d+) gu_type=(\d+) down_type=(\d+) mismatch=0',text)
  assert checks
  c.write('smoke-check.json',{'checked_values_at_least':max(int(x[1]) for x in checks),'pairs':sorted({(int(x[2]),int(x[3])) for x in checks})})
 return d
def main():
 assert os.environ.get('COMPUTERNAME')=='DESKTOP-LKMLUPC'
 assert not (R/'campaign.json').exists(),'NO_RERUN'
 ns.log.path=R/'controller.log'
 save(task_id='LUNA-20261012-027',task='IO_ARRIVAL_BOUND',phase='PREFLIGHT',controller_pid=os.getpid(),authorization='user2026-10-29 去做; one arrival upper-bound diagnostic; no implementation/deployment')
 stopped=False;error=None
 try:
  c.gate('prebuild',True);c.write('prebuild-verify.json',c.verify())
  patch=json.loads((R/'patch-identity.json').read_text())
  assert all(ns.sha(R/'source'/name)==m['after'] for name,m in patch.items())
  cmd=R/'build.cmd'
  cmd.write_text('@echo off\ncall "C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\BuildTools\\Common7\\Tools\\VsDevCmd.bat" -arch=x64\nif errorlevel 1 exit /b %errorlevel%\n'+
   'cmake -S "'+str(R/'source')+'" -B "'+str(R/'build')+'" -G "NMake Makefiles" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_ARCHITECTURES=89 -DSTRATA_ENABLE_CUDA=ON -DFETCHCONTENT_SOURCE_DIR_STRATA_LLAMACPP="C:\\Users\\User\\Strata-Adrian\\runs\\iq3-campaign-020\\build-v0142\\_deps\\strata_llamacpp-src"\nif errorlevel 1 exit /b %errorlevel%\ncmake --build "'+str(R/'build')+'" --target strata -j 2\nexit /b %errorlevel%\n')
  with (R/'build.log').open('w') as f:
   p=subprocess.Popen(['cmd.exe','/d','/c',str(cmd)],stdout=f,stderr=subprocess.STDOUT,cwd=R,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
   save(phase='BUILD',build_pid=p.pid);code=p.wait()
  assert code==0,('BUILD_FAILED',code)
  exe=R/'build/strata.exe';sha=ns.sha(exe)
  c.write('build-identity.json',{'binary_sha256':sha,'baseline_sha256':ns.EXE_C_SHA,'source_base':'f520bc5e9d31c93caeb296b059e3a3eaa16e493f','patch':patch,'instrumented_diagnostic_only':True})
  c.gate('prestop',True);c.write('prestop-verify.json',c.verify())
  cfg=json.loads(ns.CONFIG.read_text(encoding='utf-8-sig'));audit=[]
  for arm,idx in (('SMOKE',0),('D',1)):
   d=R/'out'/('block-%02d-%s-r0'%(idx,arm));d.mkdir(parents=True)
   env={'STRATA_NATIVE_PIPE':'1','STRATA_CPU_PHASE_DIAG':'1','STRATA_IO_ARRIVAL_DIAG':str(d/'arrivals.csv')}
   if arm=='SMOKE':env['STRATA_NATIVE_PIPE_CHECK']='1'
   _,got=rp.build_cfg(arm,dict(exe=str(exe),env=env,args={}),d)
   want=json.loads(json.dumps(cfg));want.update(exe=str(exe),cwd=str(exe.parent),log=str(d/'engine.log'));want['env'].update(env)
   assert got==want,('CONFIG_DIFF',arm)
   audit.append({'arm':arm,'allowed_differences_only':True,'sha256':ns.sha(d/'config.json')})
   # Remove only our audit-only generated files/directory, so original harness owns creation.
   (d/'config.json').unlink();d.rmdir()
  c.write('config-audit.json',audit)
  c.write('sampling.json',{p:{k:v for k,v in c.make_body(p,512).items() if k not in ('messages','tools')} for p in rp.POINTS})
  c.write('input-identity.json',{p.name:ns.sha(p) for p in rp.REQ_DIR.glob('p*.json')})
  stopped=True;ns.stop_api(R);c.gate('afterstop')
  block(0,'SMOKE',['p01','p05','p08'],128,exe,sha)
  block(1,'D',list(rp.POINTS),512,exe,sha)
  save(verdict='CAPTURED_ANALYSIS_PENDING')
 except BaseException:
  error=traceback.format_exc();save(error=error)
 finally:
  save(phase='RESTORE')
  try:
   if stopped:c.gate('prerestore');restore=ns.restore_api(R)
   else:restore={'restored':True,'not_stopped':True}
  except BaseException:restore={'restored':False,'error':traceback.format_exc()}
  try:v=c.verify()
  except BaseException:v={'verified':False,'error':traceback.format_exc()}
  c.write('restore.json',restore);c.write('final_verify.json',v)
  save(phase='DONE' if error is None and v['verified'] else 'FAILED',restored=restore.get('restored'),verified=v['verified'])
if __name__=='__main__':main()
