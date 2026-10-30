import os,json,subprocess,time,traceback
from pathlib import Path
import psutil
import base as c
R=Path(__file__).resolve().parent
RUNS=R.parent
PACK=Path(r'C:\Users\User\Strata-IQ3-20261008\packs\iq3_xxs')
S={}
def write(n,v):(R/n).write_text(json.dumps(v,indent=2),encoding='utf-8')
def save(**kw):S.update(kw);write('campaign.json',S)
def gate(tag):
 c.gate(tag,True)
 p=[{'pid':p.pid,'name':p.info['name'],'cmd':p.info['cmdline']} for p in psutil.process_iter(['name','cmdline']) if (p.info['name'] or '').lower() in ('r4bench.exe','io_threads_bench.exe','nativebench.exe','cl.exe','link.exe','nmake.exe')]
 write('extra-processes-'+tag+'.json',p);assert not p,('PROCESS_GATE',p)
 v=c.verify();m=c.ns.http_json('/metrics',8)
 assert m['live']['state']=='idle' and m['live']['queued']==0,('API_BUSY',m['live'])
 write('verify-'+tag+'.json',dict(verify=v,live=m['live'],requests=m['totals']['requests']))
 return v
def build(folder):
 gate('build-'+folder);d=RUNS/folder
 assert not (d/'build.log').exists(),('NO_BUILD_RERUN',folder)
 paths=[p for p in d.iterdir() if p.is_file() and p.suffix in ('.cpp','.inc','.cmd')]
 write('inputs-'+folder+'.json',{str(p):c.ns.sha(p) for p in paths})
 with (d/'build.log').open('w') as f:rc=subprocess.call(['cmd','/c','build.cmd'],cwd=d,stdout=f,stderr=subprocess.STDOUT)
 assert rc==0,('BUILD_FAILED',folder,rc)
def run(tag,folder,exe,args):
 gate(tag);d=RUNS/folder;save(phase='RUN',current=tag)
 e=d/exe;write('binary-'+folder+'.json',dict(path=str(e),sha256=c.ns.sha(e)))
 log=d/(tag+'.log');assert not log.exists(),'NO_CASE_RERUN'
 env=os.environ.copy();env.update(json.loads(c.ns.CONFIG.read_text(encoding='utf-8-sig'))['env'])
 assert 'STRATA_IQ_MT_MIN' not in env and env['STRATA_IQ3S_MT1']=='1'
 with log.open('w') as f:rc=subprocess.call([str(e)]+[str(a) for a in args],cwd=d,env=env,stdout=f,stderr=subprocess.STDOUT)
 assert rc==0,('CASE_FAILED',tag,rc)
 text=log.read_text();assert 'DONE,' in text,('INCOMPLETE',tag)
 S.setdefault('completed',[]).append(dict(tag=tag,folder=folder,path=str(log),sha256=c.ns.sha(log)));save()
 print('CASE_OK '+tag,flush=True)
def main():
 assert os.environ['COMPUTERNAME']=='DESKTOP-LKMLUPC'
 assert not (R/'campaign.json').exists(),'NO_CAMPAIGN_RERUN'
 psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
 before=gate('preflight');save(phase='BUILD',task='LUNA-20261012-027',api_pid=before['pid'],started=time.time())
 assert (PACK/'experts.bin').stat().st_size==42912972800
 assert c.ns.sha(PACK/'native_experts.txt')=='AE28CF7A2A1C9063C4B55D6C8CF86D4D079DCDDCF597F9E8697C9157D462C0EE'
 tail=[PACK/'experts.bin',PACK/'native_experts.txt']
 for folder in ('cpu-r4-tile-20261030','io-threads-screen-20261030','native-kernel-screen-20261030','cpu-r4-lowreg-20261030'):build(folder)
 for mode in ('tile','convert'):
  for lp in (2,15):
   for ty in (16,17,22,18,21):run(f'{mode}-lp{lp}-t{ty}','cpu-r4-tile-20261030','r4bench.exe',[mode,lp,ty]+tail)
 run('io-4-vs8','io-threads-screen-20261030','io_threads_bench.exe',tail)
 for lp in (2,15):
  for i,mode in enumerate(('base','prefetch4096','base','iq2s_nt1')):run(f'native-lp{lp}-{i}-{mode}','native-kernel-screen-20261030','nativebench.exe',[lp,mode]+tail)
 for lp,v in ((2,2),(15,1)):
  for nt in (2,3):run(f'lowreg-lp{lp}-nt{nt}','cpu-r4-lowreg-20261030','r4bench.exe',[lp,nt,v]+tail)
 after=gate('postrun');assert after['pid']==before['pid'],'API_PID_CHANGED'
 save(phase='DONE',seconds=time.time()-S['started'],api_unchanged=True)
if __name__=='__main__':
 try:main()
 except BaseException:
  save(phase='FAILED',error=traceback.format_exc());print(traceback.format_exc(),flush=True)
  try:gate('failure')
  except BaseException:write('postfailure-error.json',dict(error=traceback.format_exc()))
  raise
