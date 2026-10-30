import json,os,traceback,re,time
from pathlib import Path
import psutil
import base as c
import importlib.util
R=Path(__file__).resolve().parent
rp,ns=c.rp,c.ns
original=R/'harness/replay_ab_20261027.py'
source=original.read_text(encoding='utf-8')
needle="    assert 'STRATA_VERIFY_PROFILE' not in env"
assert source.count(needle)==1
copy=R/'harness/replay_profile_authorized.py'
copy.write_text(source.replace(needle,"    assert arm == 'PROFILE' and env.get('STRATA_VERIFY_PROFILE') == '1'"),encoding='utf-8')
module_spec=importlib.util.spec_from_file_location('replay_profile_authorized',copy)
rp=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(rp)
rp.make_body=c.make_body
def write(n,x):(R/n).write_text(json.dumps(x,indent=2),encoding='utf-8')
def main():
 assert not (R/'gpu2-campaign.json').exists(),'NO_RERUN'
 ns.log.path=R/'gpu2-controller.log'
 c.gate('gpu2-prestop',True);write('gpu2-before.json',c.verify())
 m=ns.http_json('/metrics',8);assert m['live']['state']=='idle' and m['live']['queued']==0
 write('gpu2-campaign.json',dict(phase='PREFLIGHT',pid=os.getpid(),sampling='original Hermes unchanged except max_tokens128'))
 stopped=False;error=None
 try:
  for point in ('p01','p05','p08'):
   b=c.make_body(point,128);assert b['temperature']==1 and b['seed']==1000+int(point[1:])
  (R/'gpu2-out').mkdir()
  audit=R/'gpu2-config-audit';audit.mkdir()
  spec=c.spec('C');spec['env']['STRATA_VERIFY_PROFILE']='1'
  _,cfg=rp.build_cfg('PROFILE',spec,audit)
  expected=json.loads(ns.CONFIG.read_text(encoding='utf-8-sig'))
  expected['cwd']=str(ns.EXE_C.parent);expected['log']=str(audit/'engine.log');expected['env']['STRATA_VERIFY_PROFILE']='1'
  assert cfg==expected,'CONFIG_DIFF'
  write('gpu2-inputs.json',dict(original_harness_sha=ns.sha(original),profile_harness_sha=ns.sha(copy),controller_sha=ns.sha(Path(__file__)),requests={p:ns.sha(rp.REQ_DIR/(p+'.json')) for p in ('p01','p05','p08')}))
  c.gate('gpu2-stop',True);stopped=True;ns.stop_api(R);c.gate('gpu2-stopped')
  old=rp.POINTS;rp.POINTS=['p01','p05','p08']
  spec=c.spec('C');spec['env']['STRATA_VERIFY_PROFILE']='1'
  try:meta,rows=rp.run_block(R/'gpu2-out',0,1,'PROFILE',spec,128)
  finally:rp.POINTS=old
  write('gpu2-meta.json',meta);write('gpu2-rows.json',rows)
  assert meta['status']=='OK' and len(rows)==3,meta
  log=R/'gpu2-out/block-00-PROFILE-r1/engine.log'
  text=log.read_text(encoding='utf-8',errors='replace')
  assert not re.search(r'CUDA error|CUDA_ERROR|NATIVE_PIPE FATAL|fatal error',text,re.I)
  lines=[l for l in text.splitlines() if 'GDN layers:' in l and 'QSA layers:' in l]
  assert len(lines)>=3,('PROFILE_NOT_CAPTURED',len(lines))
  write('gpu2-profile-lines.json',lines)
 except BaseException:error=traceback.format_exc();write('gpu2-error.json',dict(error=error))
 finally:
  try:
   c.gate('gpu2-prerestore');restore=ns.restore_api(R) if stopped else dict(restored=True,not_stopped=True)
   write('gpu2-restore.json',restore);v=c.verify();write('gpu2-after.json',v)
   write('gpu2-campaign.json',dict(phase='DONE' if not error else 'FAILED',error=error,verified=v['verified'],restored=restore.get('restored')))
  except BaseException:write('gpu2-restore-error.json',dict(error=traceback.format_exc()));raise
  if error:raise RuntimeError(error)
if __name__=='__main__':main()

