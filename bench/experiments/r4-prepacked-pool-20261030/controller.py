import os,sys,json,subprocess,traceback,time
from pathlib import Path
import psutil
R=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(r'C:\Users\User\Strata-Adrian-control\runs\big-exact-20261030')))
import base as c
def write(n,v): (R/n).write_text(json.dumps(v,indent=2),encoding='utf-8')
def gate(tag):
 c.gate(tag,True);extra=[{'pid':p.pid,'name':p.info['name'],'cmd':p.info['cmdline']} for p in psutil.process_iter(['name','cmdline']) if (p.info['name'] or '').lower() in ('r4bench.exe','cl.exe','link.exe','nmake.exe')];write('extra-'+tag+'.json',extra);assert not extra,extra
 v=c.verify();m=c.ns.http_json('/metrics',8);assert m['live']['state']=='idle' and m['live']['queued']==0;write('verify-'+tag+'.json',v);return v
def main():
 assert os.environ['COMPUTERNAME']=='DESKTOP-LKMLUPC' and not (R/'campaign.json').exists()
 before=gate('prebuild');pack=Path(r'C:\Users\User\Strata-IQ3-20261008\packs\iq3_xxs');assert (pack/'experts.bin').stat().st_size==42912972800 and c.ns.sha(pack/'native_experts.txt')=='AE28CF7A2A1C9063C4B55D6C8CF86D4D079DCDDCF597F9E8697C9157D462C0EE'
 best=c.ns.EXE_C.parent;files=[R/n for n in ('r4.cpp','pool.cpp','bench.cpp','build.cmd','inverse.inc','conversion_fast.inc')]+[best/'strata_kernels_cpu.lib',best/'ggml/src/ggml-cpu.lib',best/'ggml/src/ggml-base.lib']
 write('inputs.json',{str(p):c.ns.sha(p) for p in files});write('campaign.json',{'phase':'BUILD'})
 with (R/'build.log').open('w') as f: rc=subprocess.call(['cmd','/c','build.cmd'],cwd=R,stdout=f,stderr=subprocess.STDOUT)
 assert rc==0,('BUILD_FAILED',rc);write('binary.json',{'sha256':c.ns.sha(R/'r4bench.exe')})
 gate('pretest');write('campaign.json',{'phase':'TEST'});env=os.environ.copy();env.update(json.loads(c.ns.CONFIG.read_text(encoding='utf-8-sig'))['env']);assert env['STRATA_IQ3S_MT1']=='1' and env['STRATA_NATIVE_PIPE']=='1' and 'STRATA_IQ_MT_MIN' not in env
 with (R/'pool.log').open('w') as f:
  proc=subprocess.Popen([str(R/'r4bench.exe'),str(pack/'experts.bin'),str(pack/'native_experts.txt')],cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT); peak_ws=0;peak_private=0
  while proc.poll() is None:
   try:
    mem=psutil.Process(proc.pid).memory_full_info();peak_ws=max(peak_ws,mem.rss);peak_private=max(peak_private,mem.private)
   except (psutil.NoSuchProcess,psutil.AccessDenied): pass
   time.sleep(.02)
  rc=proc.returncode
 write('memory.json',{'sample_period_ms':20,'peak_working_set_bytes':peak_ws,'peak_private_bytes':peak_private})
 assert rc==0,('RUN_FAILED',rc);assert '\nDONE' in (R/'pool.log').read_text();after=gate('postrun');assert before['pid']==after['pid'];write('campaign.json',{'phase':'DONE','api_unchanged':True})
if __name__=='__main__':
 try:main()
 except BaseException:
  write('failure.json',{'error':traceback.format_exc()})
  try:gate('failure')
  except BaseException:write('postfailure-error.json',{'error':traceback.format_exc()})
  raise
