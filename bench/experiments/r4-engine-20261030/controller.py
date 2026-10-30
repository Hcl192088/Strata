import os,sys,json,time,traceback,subprocess
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path.insert(0,r'C:\Users\User\Strata-Adrian-control\runs\big-exact-20261030')
import base as c
rp=c.rp;ns=c.ns;c.R=R;rp.make_body=c.make_body

def write(n,v): (R/n).write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
def spec(arm):
 exe=ns.EXE_C if arm=='C' else R/'build'/'strata.exe'
 sha=ns.EXE_C_SHA if arm=='C' else ns.sha(exe)
 return dict(exe=str(exe),sha=sha,serve_dir=rp.SERVE_V0142,env={'STRATA_NATIVE_PIPE':'1'},args={},strict_capacity=True,split=False)
c.spec=spec

def main():
 assert os.environ['COMPUTERNAME']=='DESKTOP-LKMLUPC'
 assert not (R/'campaign.json').exists(),'NO_RERUN'
 ns.log.path=R/'controller.log';c.save(task_id='LUNA-20261012-027',task='R4_ENGINE_CBC',phase='PREFLIGHT',controller_pid=os.getpid())
 stopped=False;error=None
 try:
  c.identity();c.gate('pre-stop',True);write('initial_verify.json',c.verify());m=ns.http_json('/metrics',8);assert m['live']['state']=='idle' and m['live']['queued']==0
  inputs=[R/'source'/'CMakeLists.txt',R/'source'/'src/kernels/cpu/pool.cpp',R/'source'/'src/kernels/cpu/r4_engine.cpp',R/'source'/'include/strata/kernels/cpu/pool.hpp',R/'source'/'src/kernels/cpu/r4_ggml_common.h',R/'build.cmd'];write('inputs.json',{str(p):ns.sha(p) for p in inputs})
  write('sampling.json',{p:{k:v for k,v in c.make_body(p,512).items() if k in ('temperature','top_p','top_k','min_p','seed','max_tokens')} for p in rp.POINTS})
  stopped=True;c.save(phase='STOP_API');ns.stop_api(R);c.gate('after-stop');c.save(phase='BUILD')
  with (R/'build.log').open('w') as f:result=subprocess.run(['cmd','/c',str(R/'build.cmd')],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=2700)
  assert result.returncode==0,('BUILD_FAILED',result.returncode)
  exe=R/'build'/'strata.exe';assert exe.exists();write('binary.json',{'path':str(exe),'sha256':ns.sha(exe)});c.gate('post-build')
  (R/'out').mkdir();blocks=[]
  for idx,arm in enumerate(('C','B','C')):
   c.gate('block-start-%d'%idx);c.save(phase='BLOCK',index=idx,arm=arm)
   d,rows=c.run(idx,0,arm,None,512);blocks.append({'arm':arm,'path':str(d),'rate':c.rate(rows),'rows':rows});write('blocks.json',blocks)
   if arm=='B':
    log=(d/'engine.log').read_text(encoding='utf-8',errors='replace');assert 'R4_ENGINE batch=' in log,'CANDIDATE_NOT_EXERCISED'
  a,b,z=[v['rate'] for v in blocks];write('result.json',{'C1':a,'B':b,'C2':z,'B_over_C1':b/a,'B_over_C2':b/z,'quality':'UNCONFIRMED'})
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
  write('restore.json',restore);write('final_verify.json',v);c.save(phase='DONE' if error is None and v['verified'] else 'FAILED',restored=restore.get('restored'),verified=v['verified'],error=error)
if __name__=='__main__':main()
