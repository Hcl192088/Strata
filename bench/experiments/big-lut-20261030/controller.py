import json,os,subprocess,time,traceback
from pathlib import Path
import psutil
import base as c
R=Path(__file__).resolve().parent
def write(n,x):(R/n).write_text(json.dumps(x,indent=2),encoding='utf-8')
def gate(tag):
 c.gate(tag,True)
 extra=[dict(pid=p.pid,name=p.info['name'],cmd=p.info['cmdline']) for p in psutil.process_iter(['name','cmdline']) if (p.info['name'] or '').lower() in ('p2bench.exe','r4bench.exe','nativebench.exe','io_threads_bench.exe','cl.exe','link.exe','nmake.exe')]
 write('extra-'+tag+'.json',extra);assert not extra,('PROCESS_GATE',extra)
 v=c.verify();m=c.ns.http_json('/metrics',8);assert m['live']['state']=='idle' and m['live']['queued']==0
 write('verify-'+tag+'.json',dict(verify=v,live=m['live']));return v
def main():
 assert not (R/'campaign.json').exists(),'NO_RERUN'
 before=gate('prebuild');write('campaign.json',dict(phase='BUILD',pid=os.getpid()))
 subprocess.check_call([os.sys.executable,'prepare.py'],cwd=R)
 with (R/'build.log').open('w') as f:rc=subprocess.call(['cmd','/c','build.cmd'],cwd=R,stdout=f,stderr=subprocess.STDOUT)
 assert rc==0,('BUILD_FAILED',rc)
 write('binary.json',dict(sha256=c.ns.sha(R/'p2bench.exe')))
 env=os.environ.copy();env.update(json.loads(c.ns.CONFIG.read_text(encoding='utf-8-sig'))['env'])
 completed=[]
 for lp in (2,15):
  gate('lp'+str(lp))
  with (R/f'lp{lp}.log').open('w') as f:rc=subprocess.call([str(R/'p2bench.exe'),str(lp),'16',r'C:\Users\User\Strata-IQ3-20261008\packs\iq3_xxs\experts.bin',r'C:\Users\User\Strata-IQ3-20261008\packs\iq3_xxs\native_experts.txt'],cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT)
  assert rc==0,('CASE_FAILED',lp,rc)
  assert 'DONE,16,' in (R/f'lp{lp}.log').read_text()
  completed.append(lp);write('campaign.json',dict(phase='BENCH',completed=completed))
 after=gate('postrun');assert before['pid']==after['pid']
 write('campaign.json',dict(phase='DONE',completed=completed,api_unchanged=True))
if __name__=='__main__':
 try:main()
 except BaseException:
  write('failure.json',dict(error=traceback.format_exc()));print(traceback.format_exc(),flush=True)
  try:gate('failure')
  except BaseException:write('verify-error.json',dict(error=traceback.format_exc()))
  raise
