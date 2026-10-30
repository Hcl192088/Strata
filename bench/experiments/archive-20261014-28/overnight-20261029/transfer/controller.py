"""Detached overnight diagnostic. Deadline 2026-10-29 07:00 Taipei. Durable progress, no inference fallback."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
import traceback

import psutil

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'harness'))
import replay_ab_20261027 as rp
ns=rp.ns
DEADLINE=dt.datetime(2026,10,28,23,0,tzinfo=dt.timezone.utc).timestamp()
NEW_RUN_CUTOFF=DEADLINE-600
SOURCE=ns.CONTROL_ROOT/r'runs\miss-overlap-20261027\source'
BUILD=ROOT/'build'
EXE=BUILD/'strata.exe'
OUT=ROOT/'out'
STATE={}
ABORT=threading.Event()
def save(**items):
    STATE.update(items)
    STATE['updated_at']=dt.datetime.now(dt.timezone.utc).isoformat()
    p=ROOT/'progress.json'; temp=p.with_suffix('.tmp')
    temp.write_text(json.dumps(STATE,indent=2,default=str),encoding='utf-8'); os.replace(temp,p)
def gate():
    left=rp.foreign_processes()
    if left: raise RuntimeError('PROCESS_GATE_STOP '+json.dumps(left))
    assert ns.sha(ns.EXE_C)==ns.EXE_C_SHA
    assert ns.sha(ns.CONFIG)==ns.CONFIG_SHA
def kill_own_tree(p):
    if p.poll() is None: rp.kill_tree(p)
def watchdog():
    while not ABORT.wait(10):
        if time.time()>=NEW_RUN_CUTOFF:
            ABORT.set(); save(deadline_watchdog=True)
            # Only the controller's verified descendants; no unrelated process termination.
            for p in psutil.Process().children(recursive=True):
                try:
                    if p.name().lower() in ('strata.exe','python.exe','cl.exe','nvcc.exe','nmake.exe','cmake.exe','link.exe'):
                        p.terminate()
                except psutil.NoSuchProcess: pass
            return
def build():
    gate()
    assert time.time()<NEW_RUN_CUTOFF-1800
    assert subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip()=='61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406'
    identity=json.loads((ROOT/'patch_identity.json').read_text())
    for name,relative in [('expert_source.cpp','src/core/expert_source.cpp'),('generate.cpp','src/program/generate.cpp')]:
        assert ns.sha(SOURCE/relative)==identity['original_sha256'][name]
    src=ROOT/'source'
    assert not src.exists() and not BUILD.exists()
    def ignore(path,names):
        return [n for n in names if n in ('.git','runs','__pycache__','.venv') or ((Path(path)/n).is_dir() and (n=='build' or n.startswith('build-')))]
    save(phase='COPY_SOURCE')
    shutil.copytree(SOURCE,src,ignore=ignore)
    for name,relative in [('expert_source.cpp','src/core/expert_source.cpp'),('generate.cpp','src/program/generate.cpp'),('cpu_phase_diag.hpp','include/strata/core/cpu_phase_diag.hpp')]:
        p=ROOT/'patched'/name
        assert ns.sha(p)==identity['patched_sha256'][name]
        shutil.copyfile(p,src/relative)
    text='''@echo off
call "C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\BuildTools\\Common7\\Tools\\VsDevCmd.bat" -arch=x64
if errorlevel 1 exit /b %errorlevel%
cmake -S "{src}" -B "{bld}" -G "NMake Makefiles" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_ARCHITECTURES=89 -DSTRATA_ENABLE_CUDA=ON -DFETCHCONTENT_SOURCE_DIR_STRATA_LLAMACPP="C:\\Users\\User\\Strata-Adrian\\runs\\iq3-campaign-020\\build-v0142\\_deps\\strata_llamacpp-src"
if errorlevel 1 exit /b %errorlevel%
cmake --build "{bld}" --target strata -j 2
exit /b %errorlevel%
'''.format(src=src,bld=BUILD)
    (ROOT/'build.cmd').write_text(text,encoding='utf-8')
    gate()
    with (ROOT/'build.log').open('w',encoding='utf-8') as log:
        p=subprocess.Popen(['cmd.exe','/c',str(ROOT/'build.cmd')],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
        save(phase='BUILD',build_pid=p.pid,build_created_at=psutil.Process(p.pid).create_time())
        try: code=p.wait(timeout=2100)
        except subprocess.TimeoutExpired:
            kill_own_tree(p); raise RuntimeError('BUILD_TIMEOUT')
    assert code==0 and EXE.exists(),'BUILD_FAILED rc=%d'%code
    save(phase='BUILD_DONE',diag_sha256=ns.sha(EXE))
def read_diag(path):
    lines=[l for l in path.read_text(encoding='utf-8',errors='replace').splitlines() if l.startswith('CPU_PHASE_DECODE ')]
    out=[]
    for line in lines:
        d={k:float(v) for k,v in (x.split('=',1) for x in line.split()[1:])}
        assert d['windows']>0 and all(v>=-0.001 for v in d.values())
        accounted=sum(d[k] for k in ('gu_ms','quant_ms','down_ms','join_ms','lru_ms'))
        d['cpu_accounted_ms']=accounted; d['cpu_residual_ms']=d['cpu_ms']-accounted
        assert d['cpu_residual_ms']>=-max(.1,.003*d['cpu_ms']),('CPU conservation',d)
        assert d['issued_bytes']>=d['useful_bytes']
        assert d['direct_ms']+.5>=d['copy_ms']+d['issue_wait_ms']
        out.append(d)
    return out
def spec(exe,on):
    return dict(exe=str(exe),sha=ns.sha(exe),serve_dir=r'C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\upstream-v0142',
                env={'STRATA_CPU_PHASE_DIAG':'1' if on else None},args={},strict_capacity=True)
def run(index,rd,arm,points=None,tokens=512):
    assert time.time()<NEW_RUN_CUTOFF-900 and not ABORT.is_set(),'not enough deadline margin'
    gate()
    oldpoints=rp.POINTS
    if points is not None: rp.POINTS=points
    save(phase='MEASURE',current=dict(index=index,round=rd,arm=arm))
    try:
        sp=spec(ns.EXE_C if arm=='C' else EXE,arm in ('D','PROBE'))
        meta,rows=rp.run_block(OUT,index,rd,arm,sp,tokens)
    finally: rp.POINTS=oldpoints
    assert meta['status']=='OK',(arm,meta)
    assert all(not r.get('error') for r in rows)
    d=OUT/('block-%02d-%s-r%d'%(index,arm,rd))
    phases=read_diag(d/'engine.log')
    assert len(phases)==(len(rows) if arm in ('D','PROBE') else 0),(arm,len(rows),len(phases))
    (d/'cpu_phase.json').write_text(json.dumps(phases,indent=2),encoding='utf-8')
    STATE.setdefault('completed',[]).append(dict(index=index,round=rd,arm=arm,rows=len(rows),phases=len(phases),path=str(d)))
    save()
    return rows,phases
def final_verify():
    h=ns.http_json('/health',8); m=ns.http_json('/metrics',8)
    eng=[p for p in psutil.process_iter(['pid','name']) if (p.info['name'] or '').lower()=='strata.exe']
    assert len(eng)==1 and ns.sha(eng[0].exe())==ns.EXE_C_SHA
    e=eng[0].environ(); assert e.get('STRATA_IQ3S_MT1')=='1' and not e.get('STRATA_IQ_MT_MIN') and not e.get('STRATA_CPU_PHASE_DIAG')
    assert eng[0].nice()==psutil.ABOVE_NORMAL_PRIORITY_CLASS
    assert ns.sha(ns.CONFIG)==ns.CONFIG_SHA
    assert h['loaded'] and str(m['engine']['expert_slots'])=='3153' and str(m['engine']['arena_mib'])=='20479'
    return dict(verified=True,health=h,pid=eng[0].pid,engine=m['engine'],config_sha256=ns.sha(ns.CONFIG),binary_sha256=ns.sha(ns.EXE_C))
def main():
    assert os.environ.get('COMPUTERNAME','').upper()==ns.HOSTNAME
    assert not (ROOT/'progress.json').exists(),'controller already used; no duplicate execution'
    OUT.mkdir(exist_ok=False)
    STATE.update(task_id='LUNA-20261012-027',authorized_by='direct user overnight instruction',deadline_UTC='2026-10-28T23:00:00Z',
        controller_pid=os.getpid(),controller_created_at=psutil.Process().create_time(),completed=[])
    save(phase='START')
    ns.log.path=ROOT/'controller.log'
    threading.Thread(target=watchdog,daemon=True).start()
    error=None
    try:
        gate()
        build()
        run(0,0,'PROBE',['p01','p05','p08'],128)
        allrows=[];allph=[];idx=0
        for rd,arms in [(1,['C','O','D']),(2,['O','D','C']),(3,['D','C','O'])]:
            for arm in arms:
                idx+=1
                rows,ph=run(idx,rd,arm)
                allrows+=rows; allph+=ph
                (ROOT/'rows.json').write_text(json.dumps(allrows,indent=2),encoding='utf-8')
                (ROOT/'phases.json').write_text(json.dumps(allph,indent=2),encoding='utf-8')
        save(phase='DIAGNOSTIC_COMPLETE',rows=len(allrows),phase_requests=len(allph))
    except Exception:
        error=traceback.format_exc();save(phase='ERROR',error=error)
    finally:
        # Restore the existing user-approved best through its unchanged task lifecycle.
        save(before_restore_phase=STATE.get('phase'),phase='RESTORE')
        restore=ns.restore_api(ROOT)
        try: vf=final_verify()
        except Exception: vf=dict(verified=False,error=traceback.format_exc())
        (ROOT/'final_verify.json').write_text(json.dumps(vf,indent=2),encoding='utf-8')
        save(phase='DONE' if not error and vf['verified'] else 'FAILED',restored=restore.get('restored'),verified=vf['verified'])
        ABORT.set()
if __name__=='__main__': main()
