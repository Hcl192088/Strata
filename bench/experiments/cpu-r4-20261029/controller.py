import json,os,subprocess,time,traceback,shutil,hashlib
from pathlib import Path
import psutil
import base as c
R=Path(__file__).resolve().parent
def write(n,x): (R/n).write_text(json.dumps(x,indent=2),encoding='utf-8')
def gate(tag):
 c.gate(tag,True)
 p=[{'pid':p.pid,'name':p.info['name'],'cmd':p.info['cmdline']} for p in psutil.process_iter(['name','cmdline']) if (p.info['name'] or '').lower() in ('r4bench.exe','cl.exe','link.exe','nmake.exe')]
 write('extra-processes-'+tag+'.json',p);assert not p,('PROCESS_GATE_EXTRA',p)
 v=c.verify();write('verify-'+tag+'.json',v)
 m=c.ns.http_json('/metrics',8)
 write('idle-'+tag+'.json',{'live':m['live'],'totals':m['totals']})
 assert m['live']['state']=='idle' and m['live']['queued']==0,('BUSY',m['live'])
 return v
def main():
 assert os.environ['COMPUTERNAME']=='DESKTOP-LKMLUPC'
 assert not (R/'campaign.json').exists(),'NO_RERUN'
 psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
 before=gate('prebuild');write('campaign.json',{'phase':'BUILD','task':'LUNA-20261012-027','pid':os.getpid()})
 pack=Path(r'C:\Users\User\Strata-IQ3-20261008\packs\iq3_xxs')
 assert (pack/'experts.bin').stat().st_size==42912972800
 assert c.ns.sha(pack/'native_experts.txt')=='AE28CF7A2A1C9063C4B55D6C8CF86D4D079DCDDCF597F9E8697C9157D462C0EE'
 for n in ('native_experts.txt','index.txt'):shutil.copy2(pack/n,R/n)
 paths=[R/'r4.cpp',R/'inverse.inc',R/'bench.cpp',R/'build.cmd']
 best=c.ns.EXE_C.parent
 paths +=[best/'strata_kernels_cpu.lib',best/'ggml/src/ggml-cpu.lib',best/'ggml/src/ggml-base.lib']
 write('build-inputs.json',{str(p):{'sha256':c.ns.sha(p),'bytes':p.stat().st_size} for p in paths})
 with (R/'build.log').open('w') as f:
  rc=subprocess.call(['cmd','/c','build.cmd'],cwd=R,stdout=f,stderr=subprocess.STDOUT)
 assert rc==0,('BUILD_FAILED',rc)
 write('binary.json',{'sha256':c.ns.sha(R/'r4bench.exe'),'bytes':(R/'r4bench.exe').stat().st_size})
 env=os.environ.copy();env.update(json.loads(c.ns.CONFIG.read_text(encoding='utf-8-sig'))['env']);assert env['STRATA_IQ3S_MT1']=='1' and 'STRATA_IQ_MT_MIN' not in env
 start=time.monotonic();completed=[]
 for lp in (2,15):
  for ty in (16,17,22,18,21):
   assert time.monotonic()-start<600,'CAMPAIGN_BUDGET'
   tag=f'lp{lp}-t{ty}';gate(tag)
   write('campaign.json',{'phase':'BENCH','cell':tag,'completed':completed})
   with (R/(tag+'.log')).open('w') as f:
    rc=subprocess.call([str(R/'r4bench.exe'),str(lp),str(ty),str(pack/'experts.bin'),str(pack/'native_experts.txt')],cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT)
   assert rc==0,('BENCH_FAILED',tag,rc)
   text=(R/(tag+'.log')).read_text();assert f'DONE,{ty},{lp}' in text
   completed.append(tag)
 after=gate('postrun');assert before['pid']==after['pid'],'API_PID_CHANGED'
 write('campaign.json',{'phase':'DONE','completed':completed,'seconds':time.monotonic()-start,'api_unchanged':True})
if __name__=='__main__':
 try:main()
 except BaseException:
  write('failure.json',{'error':traceback.format_exc()});print(traceback.format_exc(),flush=True)
  try:write('independent-after-failure.json',gate('failure'))
  except BaseException:write('postfailure-error.json',{'error':traceback.format_exc()})
  raise
