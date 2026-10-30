import sys,os,json,time,re,datetime as dt,difflib,traceback,urllib.request
from pathlib import Path
import psutil
BASE=Path(r'C:\Users\User\Strata-Adrian-control')
ROOT=BASE/'runs/native-pipe-deploy-live-20261029'
sys.path.insert(0,str(BASE/'runs/native-pipeline-po-confirm-20261029/harness'))
import next_steps_ab_20261018 as ns
OLD=BASE/'runs/native-pipe-deploy-prep-20261029'
F=OLD/'build/strata.exe'
FS='A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8'
CS=ns.CONFIG_SHA; OSHA=ns.EXE_C_SHA; OEXE=ns.EXE_C
PREV=BASE/'bench/results/2026-10-28-s2k-mt1/BEST.json'
S={}
def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def write(n,x):
 p=ROOT/n;p.write_text(json.dumps(x,indent=2,ensure_ascii=False),encoding='utf-8')
def save(**kw):
 S.update(kw,utc=now());write('state.json',S)
def gate(label):
 p=ns.processes();a=ns.api_pids();w=ns.watch_pids();allowed={i for _,i,_ in a}|set(w)
 write(label+'.json',dict(processes=p,api=a,watch=w,heavy=ns.heavy_processes()))
 assert not [x for x in p if x['pid'] not in allowed],('unclassified',p)
def verify(new,logtext,require_active=True):
 h=ns.http_json('/health');m=ns.http_json('/metrics');eng=ns.engines();assert len(eng)==1,eng
 p=psutil.Process(eng[0]);e=p.environ();cfg=json.loads(ns.CONFIG.read_bytes())
 sha=ns.sha(Path(p.exe()));assert sha==(FS if new else OSHA)
 assert ns.sha(ns.CONFIG)==(S['new_config_sha256'] if new else CS)
 assert Path(p.cwd()).resolve()==Path(cfg['cwd']).resolve(),p.cwd()
 assert e.get('STRATA_IQ3S_MT1')=='1'
 assert e.get('STRATA_NATIVE_PIPE')==('1' if new else None)
 forbidden={k:v for k,v in e.items() if k.startswith('STRATA_') and any(t in k for t in ('CHECK','DIAG','MT_MIN')) and v not in ('','0')}
 assert not forbidden,forbidden
 assert p.nice()==psutil.ABOVE_NORMAL_PRIORITY_CLASS,p.nice()
 assert h['loaded'] and m['engine']['expert_slots']==3153 and m['engine']['arena_mib']==20479 and m['engine']['pool_workers']==9
 parsed=ns.startup_facts(logtext)
 assert parsed['ram_budget_gib']=='20.00' and parsed['locked_mib']=='20479',parsed
 assert ns.POOL9_ALL in logtext
 assert not re.search(r'NATIVE_PIPE FATAL|NATIVE_PIPE_CHECK MISMATCH',logtext)
 if new and require_active:assert 'NATIVE_PIPE ACTIVE' in logtext
 return dict(verified=True,at=now(),pid=p.pid,binary_sha256=sha,config_sha256=ns.sha(ns.CONFIG),cwd=p.cwd(),env={k:v for k,v in e.items() if k.startswith('STRATA_')},priority=p.nice(),health=h,engine=m['engine'],startup=parsed,affinity='all',command=p.cmdline())
def preflight():
 assert os.environ['COMPUTERNAME']=='DESKTOP-LKMLUPC'
 gate('processes-preflight')
 assert ns.sha(OEXE)==OSHA and ns.sha(ns.CONFIG)==CS and ns.sha(OLD/'live-original.json')==CS and ns.sha(F)==FS
 old=(OLD/'live-original.json').read_bytes();cfg=json.loads(old);expected=json.loads(old)
 expected['exe']=str(F);expected['cwd']=str(F.parent);expected['env']['STRATA_NATIVE_PIPE']='1'
 text=old.decode('utf-8');text=text.replace(json.dumps(cfg['exe']),json.dumps(str(F)),1).replace(json.dumps(cfg['cwd']),json.dumps(str(F.parent)),1)
 text=text.replace('"STRATA_IQ3S_MT1": "1"','"STRATA_IQ3S_MT1": "1",'+ ('\r\n' if '\r\n' in text else '\n')+'        "STRATA_NATIVE_PIPE": "1"',1)
 assert json.loads(text)==expected
 (ROOT/'candidate-live.json').write_bytes(text.encode('utf-8'))
 S['new_config_sha256']=ns.sha(ROOT/'candidate-live.json')
 (ROOT/'config.diff').write_text(''.join(difflib.unified_diff(old.decode().splitlines(True),text.splitlines(True),fromfile='live-original.json',tofile='candidate-live.json')),encoding='utf-8',newline='')
 assert json.loads(PREV.read_bytes())['binary_sha256']==OSHA
 p=psutil.Process(ns.engines()[0]);assert ns.sha(Path(p.exe()))==OSHA
 task=ns.ps('(Get-ScheduledTask -TaskName Strata-Task020-API).Actions | ConvertTo-Json -Compress').stdout
 write('task-before.json',json.loads(task));S['task_action']=task
 lp=BASE/'tools/start_task020_api_s2k_mt1.ps1';S['launcher_sha256']=ns.sha(lp)
 write('preflight.json',dict(verified=True,at=now(),old_config_sha256=CS,new_config_sha256=S['new_config_sha256'],old_binary_sha256=OSHA,new_binary_sha256=FS,backup_sha256=ns.sha(OLD/'live-original.json'),live_pid=p.pid))
 save(phase='PREFLIGHT_PASS')
def start():
 gate('processes-before-start-'+S['phase'])
 ns.ps('Start-ScheduledTask -TaskName Strata-Task020-API');save(start_issued=now())
 t=time.time()
 while time.time()-t<600:
  try:
   if ns.http_json('/health',5).get('loaded'):save(loaded_at=now());return
  except Exception:pass
  time.sleep(3)
 raise RuntimeError('health loaded=true timeout 600s')
def main():
 ns.log.path=ROOT/'controller.log';switched=False;stopped=False
 try:
  preflight()
  if '--preflight' in sys.argv:return
  gate('processes-before-stop');save(phase='WAIT_IDLE')
  stopped=True;ns.stop_api(ROOT);save(phase='STOPPED',stopped_at=now())
  assert ns.sha(ns.CONFIG)==CS
  temp=ns.CONFIG.with_name(ns.CONFIG.name+'.native-pipe.tmp');assert not temp.exists()
  temp.write_bytes((ROOT/'candidate-live.json').read_bytes());assert ns.sha(temp)==S['new_config_sha256']
  assert json.loads(temp.read_bytes())==json.loads((ROOT/'candidate-live.json').read_bytes())
  os.replace(temp,ns.CONFIG);switched=True;save(phase='SWITCHED',replaced_at=now())
  logpath=Path(json.loads(ns.CONFIG.read_bytes())['log']);offset=logpath.stat().st_size
  ns.EXE_C=F
  start();text=logpath.read_bytes()[offset:].decode('utf-8',errors='replace');(ROOT/'startup.log').write_text(text,encoding='utf-8')
  vf=verify(True,text,False);write('verification.json',vf);gate('processes-before-smoke')
  assert ns.http_json('/metrics')['live']['state']=='idle'
  pos=logpath.stat().st_size
  req={'model':json.loads(ns.CONFIG.read_bytes())['model_name'],'messages':[{'role':'user','content':'Write one short sentence about a blue sky.'}],'max_tokens':32,'stream':False}
  body=json.dumps(req).encode();r=urllib.request.Request(ns.API_URL+'/v1/chat/completions',data=body,headers={'Content-Type':'application/json'})
  save(phase='SMOKE',smoke_started=now())
  with urllib.request.urlopen(r,timeout=180) as response:out=json.load(response)
  assert out.get('choices') and out['choices'][0]['message'].get('content'),out
  tail=logpath.read_bytes()[pos:].decode('utf-8',errors='replace');(ROOT/'smoke-engine.log').write_text(tail,encoding='utf-8')
  parsed=ns.parse_request(tail);assert parsed.get('tokens',0)>0 and parsed.get('decode_ms',0)>0,parsed
  assert 'DECODE_TIMING' in tail or 'decode timing' in tail.lower(),tail
  smoke=dict(at=now(),usage=out.get('usage'),finish_reason=out['choices'][0].get('finish_reason'),response=out['choices'][0]['message']['content'],timing=parsed,request_max_tokens=32,temperature_sent=False)
  write('smoke.json',smoke)
  vf=verify(True,text+tail);write('verification-final.json',vf)
  assert ns.ps('(Get-ScheduledTask -TaskName Strata-Task020-API).Actions | ConvertTo-Json -Compress').stdout==S['task_action']
  assert ns.sha(BASE/'tools/start_task020_api_s2k_mt1.ps1')==S['launcher_sha256']
  gate('processes-final')
  manifest=dict(schema_version=1,name='S2K+MT1+NATIVE_PIPE',status='DEPLOYED_VERIFIED',task_id='LUNA-20261012-027',checked_at=now(),authorized_scope='user NATIVE_PIPE_DEPLOY_LIVE / 切換 live; no git/GitHub/push',binary_path=str(F),binary_sha256=FS,config_path=str(ns.CONFIG),config_sha256=S['new_config_sha256'],config=json.loads(ns.CONFIG.read_bytes()),source={'source_repo':'Hcl192088/Strata','commit':'f520bc5e9d31c93caeb296b059e3a3eaa16e493f','annotated_tag':'native-pipe-generic-20261029'},previous_best={'manifest':str(PREV),'sha256':ns.sha(PREV),'binary_sha256':OSHA,'config_sha256':CS},evidence_paths=[str(BASE/'runs'/x) for x in ['native-pipeline-po-confirm-20261029','native-pipe-deploy-prep-20261029','fresh-build-sanity-20261029/attempt-2']],verification=vf,smoke=smoke,launcher_sha256=S['launcher_sha256'],task_action=json.loads(S['task_action']),rollback_config=str(OLD/'live-original.json'),temperature_changed=False,performance_note='One short live smoke only; not a benchmark')
  # New version under ignored run artifacts: preserve remote main/git and historical BEST.
  manifest['manifest_path']=str(ROOT/'BEST.json');write('BEST.json',manifest)
  save(phase='DONE',verdict='DEPLOYED',best_manifest=str(ROOT/'BEST.json'),completed_at=now())
 except BaseException:
  save(error=traceback.format_exc(),phase='FAILED')
  if switched:
   try:
    gate('processes-before-rollback');ns.stop_api(ROOT);save(phase='ROLLBACK_STOPPED')
    ns.CONFIG.write_bytes((OLD/'live-original.json').read_bytes());assert ns.sha(ns.CONFIG)==CS
    ns.EXE_C=OEXE;lp=Path(json.loads(ns.CONFIG.read_bytes())['log']);offset=lp.stat().st_size
    start();txt=lp.read_bytes()[offset:].decode('utf-8',errors='replace');(ROOT/'rollback-startup.log').write_text(txt,encoding='utf-8')
    write('rollback-verification.json',verify(False,txt));gate('processes-final-rollback')
    save(phase='ROLLED_BACK',verdict='FAILED_ROLLED_BACK')
   except BaseException:save(phase='ROLLBACK_FAILED',verdict='ROLLBACK_FAILED',rollback_error=traceback.format_exc())
  elif stopped:
   # stop_api may fail while waiting idle; never start a duplicate API.
   if not ns.engines():start()
   save(verdict='STOPPED_BEFORE_SWITCH')
  else:save(verdict='STOPPED_BEFORE_SWITCH')
  raise
if __name__=='__main__':main()
