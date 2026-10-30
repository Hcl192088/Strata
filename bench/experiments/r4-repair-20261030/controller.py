import os,sys,json,time,traceback,subprocess,hashlib
from pathlib import Path
import psutil
R=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(r'C:\Users\User\Strata-Adrian-control\runs\big-exact-20261030')))
import base as c

def write(n,v): (R/n).write_text(json.dumps(v,indent=2),encoding='utf-8')
def gate(tag):
 c.gate(tag,True)
 extra=[{'pid':p.pid,'name':p.info['name'],'cmd':p.info['cmdline']} for p in psutil.process_iter(['name','cmdline']) if (p.info['name'] or '').lower() in ('r4bench.exe','cl.exe','link.exe','nmake.exe')]
 write('extra-'+tag+'.json',extra); assert not extra,extra
 v=c.verify(); m=c.ns.http_json('/metrics',8); assert m['live']['state']=='idle' and m['live']['queued']==0,m['live'];write('verify-'+tag+'.json',v);return v

def main():
 assert os.environ['COMPUTERNAME']=='DESKTOP-LKMLUPC'
 assert not (R/'campaign.json').exists()
 psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
 before=gate('prebuild');pack=Path(r'C:\Users\User\Strata-IQ3-20261008\packs\iq3_xxs')
 assert (pack/'experts.bin').stat().st_size==42912972800
 assert c.ns.sha(pack/'native_experts.txt')=='AE28CF7A2A1C9063C4B55D6C8CF86D4D079DCDDCF597F9E8697C9157D462C0EE'
 inputs=[R/n for n in ('r4.cpp','bench.cpp','build.cmd','inverse.inc','conversion_fast.inc')]; best=c.ns.EXE_C.parent
 inputs += [best/'strata_kernels_cpu.lib',best/'ggml/src/ggml-cpu.lib',best/'ggml/src/ggml-base.lib']
 write('inputs.json',{str(p):c.ns.sha(p) for p in inputs});write('campaign.json',{'phase':'BUILD'})
 with (R/'build.log').open('w') as f: rc=subprocess.call(['cmd','/c','build.cmd'],cwd=R,stdout=f,stderr=subprocess.STDOUT)
 assert rc==0,('BUILD_FAILED',rc)
 write('binary.json',{'sha256':c.ns.sha(R/'r4bench.exe')})
 env=os.environ.copy();env.update(json.loads(c.ns.CONFIG.read_text(encoding='utf-8-sig'))['env']);assert env['STRATA_IQ3S_MT1']=='1' and 'STRATA_IQ_MT_MIN' not in env
 done=[]
 for lp,nt,variant in ((2,2,2),(2,3,2),(15,2,1),(15,3,1)):
  tag=f'lp{lp}-nt{nt}';gate(tag);write('campaign.json',{'phase':'BENCH','cell':tag,'done':done})
  with (R/(tag+'.log')).open('w') as f: rc=subprocess.call([str(R/'r4bench.exe'),str(lp),str(nt),str(variant),str(pack/'experts.bin'),str(pack/'native_experts.txt')],cwd=R,env=env,stdout=f,stderr=subprocess.STDOUT)
  assert rc==0,('RUN_FAILED',tag,rc)
  assert f'DONE,{lp},{nt},{variant}' in (R/(tag+'.log')).read_text();done.append(tag)
 after=gate('postrun'); assert before['pid']==after['pid'];write('campaign.json',{'phase':'DONE','done':done,'api_unchanged':True})
if __name__=='__main__':
 try:main()
 except BaseException:
  write('failure.json',{'error':traceback.format_exc()})
  try:gate('failure')
  except BaseException:write('postfailure-error.json',{'error':traceback.format_exc()})
  raise
