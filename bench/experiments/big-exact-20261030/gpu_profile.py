import json,os,traceback,re,time
from pathlib import Path
import psutil
import base as c
R=Path(__file__).resolve().parent
rp,ns=c.rp,c.ns
def write(n,x):(R/n).write_text(json.dumps(x,indent=2),encoding='utf-8')
def main():
 assert not (R/'gpu-campaign.json').exists(),'NO_RERUN'
 ns.log.path=R/'gpu-controller.log'
 c.gate('gpu-prestop',True);write('gpu-before.json',c.verify())
 m=ns.http_json('/metrics',8);assert m['live']['state']=='idle' and m['live']['queued']==0
 write('gpu-campaign.json',dict(phase='PREFLIGHT',pid=os.getpid(),sampling='original Hermes unchanged except max_tokens128'))
 stopped=False;error=None
 try:
  for point in ('p01','p05','p08'):
   b=c.make_body(point,128);assert b['temperature']==1 and b['seed']==1000+int(point[1:])
  (R/'gpu-out').mkdir()
  c.gate('gpu-stop',True);stopped=True;ns.stop_api(R);c.gate('gpu-stopped')
  old=rp.POINTS;rp.POINTS=['p01','p05','p08']
  spec=c.spec('C');spec['env']['STRATA_VERIFY_PROFILE']='1'
  try:meta,rows=rp.run_block(R/'gpu-out',0,1,'PROFILE',spec,128)
  finally:rp.POINTS=old
  write('gpu-meta.json',meta);write('gpu-rows.json',rows)
  assert meta['status']=='OK' and len(rows)==3,meta
  log=R/'gpu-out/block-00-PROFILE-r1/engine.log'
  text=log.read_text(encoding='utf-8',errors='replace')
  assert not re.search(r'CUDA error|CUDA_ERROR|NATIVE_PIPE FATAL|fatal error',text,re.I)
  lines=[l for l in text.splitlines() if 'GDN layers:' in l and 'QSA layers:' in l]
  assert len(lines)>=3,('PROFILE_NOT_CAPTURED',len(lines))
  write('gpu-profile-lines.json',lines)
 except BaseException:error=traceback.format_exc();write('gpu-error.json',dict(error=error))
 finally:
  try:
   c.gate('gpu-prerestore');restore=ns.restore_api(R) if stopped else dict(restored=True,not_stopped=True)
   write('gpu-restore.json',restore);v=c.verify();write('gpu-after.json',v)
   write('gpu-campaign.json',dict(phase='DONE' if not error else 'FAILED',error=error,verified=v['verified'],restored=restore.get('restored')))
  except BaseException:write('gpu-restore-error.json',dict(error=traceback.format_exc()));raise
  if error:raise RuntimeError(error)
if __name__=='__main__':main()
