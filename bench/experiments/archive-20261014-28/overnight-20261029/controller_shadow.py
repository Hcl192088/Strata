"""User-authorized Task027 overnight continuation. Hard deadline 07:00 Taipei."""
import ctypes
import datetime as dt
import json
import os
from pathlib import Path
import re
import statistics as st
import sys
import threading
import time
import traceback
import psutil

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'harness'))
import replay_ab_20261027 as rp
ns=rp.ns
EXE=ROOT/'build/strata.exe'
EXE_SHA='9268FAD812CB2C970D021EC7EAF29A2C6E137593A47F07BB2061F5FCBC858C42'
SHADOW=ROOT/'first-shard.direct'
OUT=ROOT/'out'
DEADLINE=dt.datetime(2026,10,28,23,tzinfo=dt.timezone.utc).timestamp()
CUTOFF=DEADLINE-600
STATE={}; ABORT=threading.Event();ROWS=[];PHASES=[]

def save(**kw):
    STATE.update(kw,updated_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    tmp=ROOT/'campaign.tmp';tmp.write_text(json.dumps(STATE,indent=2));tmp.replace(ROOT/'campaign.json')
def write(name,value):
    p=ROOT/name;t=ROOT/(name+'.tmp');t.write_text(json.dumps(value,indent=2));t.replace(p)
def identity():
    assert time.time()<CUTOFF-900 and not ABORT.is_set(),'deadline margin exhausted'
    assert ns.sha(ns.EXE_C)==ns.EXE_C_SHA and ns.sha(ns.CONFIG)==ns.CONFIG_SHA,'current best mismatch'
    assert ns.sha(EXE)==EXE_SHA,'candidate mismatch'
    receipt=json.loads((ROOT/'copy.json').read_text())
    assert receipt['status']=='DONE' and receipt['source_sha256']==receipt['shadow_prefix_sha256']=='219ea929900dfa9ef091f3aa473fdba6874b65fcb36526d7d851ac9e95856d15'
    assert SHADOW.stat().st_size==47039860736 and SHADOW.stat().st_mtime_ns==STATE['shadow_mtime_ns'],'shadow changed'
def gate():
    identity();other=rp.foreign_processes();assert not other,('process gate',other)
def watchdog():
    while not ABORT.wait(10):
        if time.time()>=CUTOFF:
            save(deadline_triggered=True)
            for p in psutil.Process().children(recursive=True):
                try:
                    if p.name().lower() in ('strata.exe','python.exe'):p.terminate()
                except psutil.NoSuchProcess:pass
            return
def spec(arm):
    shadow=arm in ('S','SD','CHK','BAD_PATH')
    env={'STRATA_DIRECT_SHADOW_FIRST':str(ROOT/'absent.never-create') if arm=='BAD_PATH' else str(SHADOW) if shadow else None,
         'STRATA_CPU_PHASE_DIAG':'1' if arm in ('OD','SD','CHK') else None,
         'STRATA_MISS_OVERLAP_CHECK':'1' if arm=='CHK' else None}
    return dict(exe=str(ns.EXE_C if arm=='C' else EXE),sha=ns.EXE_C_SHA if arm=='C' else EXE_SHA,
        serve_dir=r'C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\upstream-v0142',env=env,args={},strict_capacity=True)
def phases(text,rows):
    out=[]
    for line in text.splitlines():
        if not line.startswith('CPU_PHASE_DECODE '):continue
        d={k:float(v) for k,v in (x.split('=',1) for x in line.split()[1:])}
        assert d['windows']>0 and all(v>=-.001 for v in d.values())
        d['cpu_residual_ms']=d['cpu_ms']-sum(d[k] for k in ('gu_ms','quant_ms','down_ms','join_ms','lru_ms'))
        assert d['cpu_residual_ms']>=-max(.1,.003*d['cpu_ms'])
        assert d['issued_bytes']>=d['useful_bytes'] and d['direct_ms']+.5>=d['copy_ms']+d['issue_wait_ms']
        out.append(d)
    assert len(out)==len(rows)
    for d,r in zip(out,rows):
        assert d['windows']==r['windows'] and abs(d['cpu_ms']/d['windows']-r['cpu_ms'])<=.011
    return out
def run(index,rd,arm,points=None,tokens=512):
    gate();save(phase='MEASURE',current=dict(index=index,round=rd,arm=arm))
    old=rp.POINTS
    if points is not None:rp.POINTS=points
    try:meta,rows=rp.run_block(OUT,index,rd,arm,spec(arm),tokens)
    finally:rp.POINTS=old
    d=OUT/('block-%02d-%s-r%d'%(index,arm,rd));text=(d/'engine.log').read_text(encoding='utf-8',errors='replace')
    if arm=='BAD_PATH':
        assert meta['status']=='ERROR' and 'DIRECT_SHADOW FATAL open error=' in text,'fail-closed negative test did not refuse bad path'
        assert 'DIRECT_SHADOW ACTIVE' not in text and not rows
    else:
        assert meta['status']=='OK' and len(rows)==len(points or rp.POINTS) and all(not r.get('error') for r in rows),(arm,meta)
        assert meta['priority_gate']['priority']==psutil.ABOVE_NORMAL_PRIORITY_CLASS
        assert 'DIRECT_SHADOW FATAL' not in text
        if arm in ('S','SD','CHK'):
            assert 'DIRECT_SHADOW ACTIVE' in text
            counters=re.findall(r'DIRECT_SHADOW progress requests=(\d+) shadow_bytes=(\d+) total_bytes=(\d+)',text)
            assert counters and max(int(x[1]) for x in counters)>0,'shadow opened but no reads'
            write('last-shadow-counters.json',dict(arm=arm,round=rd,last=counters[-1],scope='whole engine including startup/prompt; not decode-only'))
        else:assert 'DIRECT_SHADOW ACTIVE' not in text
        if arm=='CHK':
            checks=re.findall(r'check_rows=(\d+) check_mismatch_rows=(\d+)',text)
            assert checks and max(int(x[0]) for x in checks)>=100 and all(int(x[1])==0 for x in checks)
            assert 'MISMATCH' not in text
        if arm in ('OD','SD','CHK'):
            ph=phases(text,rows);write('phase-'+arm+'.json',ph)
            for p,r in zip(ph,rows):PHASES.append(dict(arm=arm,pid=r['pid'],**p))
            write('phase-rows.json',PHASES)
    STATE.setdefault('completed',[]).append(dict(index=index,round=rd,arm=arm,rows=len(rows),status=meta['status'],path=str(d)))
    if arm in ('C','O','S'):ROWS.extend(rows);write('rows.json',ROWS)
    write('all-blocks.json',STATE['completed']);save()
    return rows
def round_rates():
    out={}
    for r in ROWS:out.setdefault((r['round'],r['arm']),[]).append(r)
    return {k:sum(r.get('m_out_tokens') or r['tokens'] for r in rs)*1000/sum(r.get('m_decode_ms') or r['decode_ms'] for r in rs) for k,rs in out.items()}
def summarize():
    rates=round_rates();res={}
    for a,b in [('S','O'),('S','C'),('O','C')]:
        vals=[(rates[(rd,a)]/rates[(rd,b)]-1)*100 for rd in range(1,6) if (rd,a) in rates and (rd,b) in rates]
        if not vals:continue
        n=len(vals);mean=st.mean(vals)
        t={2:12.706205,3:4.302653,4:3.182446,5:2.776445}.get(n)
        ci=[mean-t*st.stdev(vals)/n**.5,mean+t*st.stdev(vals)/n**.5] if t else None
        res[a+'_vs_'+b]=dict(n=n,mean_pct=mean,paired_round_deltas_pct=vals,paired_ci95_pct=ci)
    result=dict(round_rates={str(k):v for k,v in rates.items()},comparisons=res,not_promoted=True)
    write('comparison.json',result);return result
def final_verify():
    h=ns.http_json('/health',8);m=ns.http_json('/metrics',8)
    engines=[p for p in psutil.process_iter(['name']) if p.info['name'].lower()=='strata.exe']
    assert len(engines)==1
    p=engines[0];e=p.environ()
    assert ns.sha(Path(p.exe()))==ns.EXE_C_SHA and ns.sha(ns.CONFIG)==ns.CONFIG_SHA
    assert e.get('STRATA_IQ3S_MT1')=='1' and not any(e.get(k) for k in ('STRATA_IQ_MT_MIN','STRATA_CPU_PHASE_DIAG','STRATA_DIRECT_SHADOW_FIRST'))
    assert p.nice()==psutil.ABOVE_NORMAL_PRIORITY_CLASS
    assert h['loaded'] and str(m['engine']['expert_slots'])=='3153' and str(m['engine']['arena_mib'])=='20479'
    return dict(verified=True,pid=p.pid,health=h,engine=m['engine'],binary_sha256=ns.EXE_C_SHA,config_sha256=ns.CONFIG_SHA)
def main():
    ctypes.windll.kernel32.SetErrorMode(0x8003)
    assert os.environ['COMPUTERNAME']=='DESKTOP-LKMLUPC'
    assert not (ROOT/'campaign.json').exists(),'campaign already started; do not duplicate'
    assert not OUT.exists()
    STATE.update(task_id='LUNA-20261012-027',authorization='direct user overnight continuation',controller_pid=os.getpid(),controller_created=psutil.Process().create_time(),deadline_utc='2026-10-28T23:00:00Z',shadow_mtime_ns=SHADOW.stat().st_mtime_ns,completed=[])
    ns.log.path=ROOT/'controller.log';save(phase='START');OUT.mkdir()
    threading.Thread(target=watchdog,daemon=True).start()
    error=None
    try:
        identity()
        allowed={pid for _,pid,_ in ns.api_pids()}|set(ns.watch_pids())
        other=[p for p in ns.processes() if p['pid'] not in allowed]
        assert not other,('pre-stop process gate',other)
        write('pre-stop-classified.json',dict(api=ns.api_pids(),memory_policy_watch=ns.watch_pids()))
        ns.stop_api(ROOT);gate()
        run(0,0,'BAD_PATH',[],0)
        run(1,0,'CHK',['p01','p05','p08'],128)
        run(2,0,'OD');run(3,0,'SD')
        idx=3
        schedules=[['C','O','S'],['O','S','C'],['S','C','O'],['C','S','O'],['S','O','C']]
        for rd,arms in enumerate(schedules,1):
            for arm in arms:idx+=1;run(idx,rd,arm)
            result=summarize()
            if rd==3:
                changes=result['comparisons']['S_vs_O']['paired_round_deltas_pct']
                if all(x<0 for x in changes) or st.mean(changes)<-3:
                    save(early_stop_reason='pre-registered three-round negative gate');break
        save(phase='MEASURE_COMPLETE',formal_requests=len(ROWS))
    except BaseException:
        error=traceback.format_exc();save(phase='ERROR',error=error)
    finally:
        save(before_restore_phase=STATE.get('phase'),phase='RESTORE')
        restore=ns.restore_api(ROOT)
        try:vf=final_verify()
        except BaseException:vf=dict(verified=False,error=traceback.format_exc())
        write('final_verify.json',vf)
        save(phase='DONE' if error is None and vf['verified'] else 'FAILED',restored=restore.get('restored'),verified=vf['verified'])
        ABORT.set()
if __name__=='__main__':main()
