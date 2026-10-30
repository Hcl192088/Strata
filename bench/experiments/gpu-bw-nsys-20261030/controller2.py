import os, sys, json, time, subprocess, traceback
from pathlib import Path
import psutil
R=Path(__file__).resolve().parent
sys.path.insert(0,r'C:\Users\User\Strata-Adrian-control\runs\big-exact-20261030')
import base as c
ns=c.ns;c.R=R
N=r'C:\Program Files\NVIDIA Corporation\Nsight Systems 2026.5.1\target-windows-x64\nsys.exe'
S='bw20261030'; stopped=False; p=None; result={}
def save(n,x): (R/n).write_text(json.dumps(x,indent=2,default=str),encoding='utf-8')
def call(args,timeout=300):
 q=subprocess.run([N]+args,capture_output=True,text=True,timeout=timeout,creationflags=subprocess.CREATE_NO_WINDOW)
 with (R/'nsys-calls.log').open('a',encoding='utf-8') as f:f.write('\n'+repr(args)+' rc='+str(q.returncode)+'\n'+q.stdout+'\n'+q.stderr+'\n')
 return q
def main():
 global stopped,p
 try:
  c.identity();c.gate('pre-stop',True);v=c.verify();m=ns.http_json('/metrics',8);assert m['live']['state']=='idle' and m['live']['queued']==0
  eng=next(x for x in psutil.process_iter(['name']) if (x.info['name'] or '').lower()=='strata.exe')
  args=eng.cmdline();env=eng.environ(); expected=json.loads((R/'command.json').read_text(encoding='utf-8-sig'))['engine']
  assert [x.lower() for x in args]==[x.lower() for x in expected], 'live command mismatch'
  assert env.get('STRATA_NATIVE_PIPE')=='1' and env.get('STRATA_IQ3S_MT1')=='1' and 'STRATA_IQ_MT_MIN' not in env
  save('initial.json',{'verify':v,'live':m['live'],'args':args,'strata_env':{k:v for k,v in env.items() if k.startswith('STRATA_')}})
  result['prompt_path']=str(ns.PROMPT);result['prompt_sha256']=ns.sha(ns.PROMPT)
  assert result['prompt_sha256']=='9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA', 'prompt sha mismatch'
  stopped=True;ns.stop_api(R);c.gate('after-stop')
  prompt=[ns.PROMPT.read_text(encoding='utf-8-sig').strip()]
  inp=R/'stdin.txt';out=R/'stdout2.log';err=R/'stderr2.log';inp.write_text('GEN 512 '+','.join(prompt)+'\nQUIT\n',encoding='utf-8')
  cmd=R/'run-gpu-bw-nsys-20261030.cmd'
  cmd.write_text('@echo off\r\ncd /d "'+str(Path(args[0]).parent)+'"\r\n'+subprocess.list2cmdline(args)+' < "'+str(inp)+'" > "'+str(out)+'" 2> "'+str(err)+'"\r\n')
  launch=[N,'profile','--trace=cuda,nvtx','--cuda-graph-trace=node','--sample=none','--cpuctxsw=none','--gpu-metrics-devices=0','--gpu-metrics-set=ad10x','--gpu-metrics-frequency=10000','--stats=false','--force-overwrite=true','-o',str(R/'trace2'),'cmd.exe','/c',str(cmd)]
  result['t0_wall_ns']=time.time_ns();marks=result.setdefault('marks',[])
  save('launch.json',launch)
  with (R/'launch.out').open('w') as o,(R/'launch.err').open('w') as e:
   p=subprocess.Popen(launch,env=env,stdin=subprocess.DEVNULL,stdout=o,stderr=e,creationflags=subprocess.CREATE_NO_WINDOW)
   t=time.monotonic(); started=False; done=False; tokens=0; off=0; buf=''
   while time.monotonic()-t<1500:
    if out.exists():
     with out.open('rb') as f:f.seek(off);chunk=f.read();off+=len(chunk)
     buf+=chunk.decode('utf-8','replace')
     while '\n' in buf:
      line,buf=buf.split('\n',1);line=line.strip()
      if line.startswith(('READY','PP ','T ','DONE ')):marks.append((time.time_ns(),line[:40]))
      if line.startswith('READY'): result['ready']=time.monotonic()-t
      if line.startswith('T '):tokens+=1
      if line.startswith('DONE '):result['done_line']=line;done=True
     if done:break
    if p.poll() is not None and not done:raise RuntimeError('engine/launch exited before DONE rc='+str(p.returncode))
    time.sleep(.05)
   result['T_lines']=tokens
   if not done:raise RuntimeError('engine timeout under nsys')
   try:p.wait(timeout=1800);result['profile_rc']=p.returncode
   except subprocess.TimeoutExpired:result['profile_wait_timeout']=True
  result['status']='CAPTURED'
 except BaseException:
  result['error']=traceback.format_exc()
 finally:
  save('result2.json',result)
  if stopped:
   try:
    for _ in range(60):
     if not ns.engines():break
     time.sleep(1)
    c.gate('pre-restore');result['restore']=ns.restore_api(R)
   except BaseException:result['restore_error']=traceback.format_exc()
  try:result['verify']=c.verify();result['live']=ns.http_json('/metrics',8)['live']
  except BaseException:result['verify_error']=traceback.format_exc()
  save('result2.json',result)
if __name__=='__main__':main()
