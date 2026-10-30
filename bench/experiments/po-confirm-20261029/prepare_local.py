from pathlib import Path
p=Path('state/overnight-20261029/controller_pipeline.py')
s=p.read_text()
s=s.replace("EXE=ROOT/'build/strata.exe'", "OLD=ROOT.parent/'native-pipeline-20261029'\nEXE=OLD/'build/strata.exe'")
s=s.replace("assert time.time()<CUTOFF-900 and not ABORT.is_set(),'deadline margin exhausted'", "assert not ABORT.is_set()")
a=s.index('def main():')
s=s[:a]+'''def compatibility():
    audit=json.loads((OLD/'audit.json').read_text())
    assert audit['verified']
    for name,info in audit['inputs'].items():
        assert ns.sha(rp.REQ_DIR/name)==info['sha256'],'request changed'
    evidence=[]
    for b in json.loads((OLD/'campaign.json').read_text())['completed']:
        if b['arm'] not in ('O','P'):continue
        d=Path(b['path']);old=json.loads((d/'config.json').read_text())
        scratch=ROOT/('compat-'+str(b['index']));scratch.mkdir()
        _,new=rp.build_cfg(b['arm'],spec(b['arm']),scratch)
        old.pop('log');new.pop('log')
        assert old==new,('config difference',b)
        m=json.loads((d/'meta.json').read_text())
        assert m['binary_sha256']==EXE_SHA and m['status']=='OK'
        evidence.append(dict(index=b['index'],equal_except_log=True))
    write('compatibility.json',dict(verified=True,blocks=evidence,harness_sha256={p.name:ns.sha(p) for p in (ROOT/'harness').glob('*.py')}))

def summarize_confirm():
    old=json.loads((OLD/'rows.json').read_text())
    allrows=[r for r in old if r['arm'] in ('O','P')]+ROWS
    groups={}
    for r in allrows:groups.setdefault((r['round'],r['arm']),[]).append(r)
    rates={k:sum(r.get('m_out_tokens') or r['tokens'] for r in rs)*1000/sum(r.get('m_decode_ms') or r['decode_ms'] for r in rs) for k,rs in groups.items()}
    rounds=sorted({rd for rd,arm in groups if (rd,'O') in groups and (rd,'P') in groups})
    vals=[100*(rates[(rd,'P')]/rates[(rd,'O')]-1) for rd in rounds]
    n=len(vals);mean=st.mean(vals);t={7:2.446911851,8:2.364624252}[n]
    margin=t*st.stdev(vals)/n**.5
    result=dict(n=n,df=n-1,mean_pct=mean,ci95_pct=[mean-margin,mean+margin],round_deltas_pct=vals,round_rates={str(k):v for k,v in rates.items()})
    write('comparison.json',result);return result

def main():
    ctypes.windll.kernel32.SetErrorMode(0x8003)
    assert os.environ['COMPUTERNAME']=='DESKTOP-LKMLUPC'
    assert not (ROOT/'campaign.json').exists(),'already started'
    STATE.update(task_id='LUNA-20261012-027',authorization='user 同意 NATIVE_PIPE_PO_CONFIRM',controller_pid=os.getpid(),started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),completed=[])
    ns.log.path=ROOT/'controller.log';save(phase='START');OUT.mkdir()
    error=None;stopped=False
    try:
        identity()
        allowed={pid for _,pid,_ in ns.api_pids()}|set(ns.watch_pids())
        inventory=ns.processes();write('pre-stop-processes.json',inventory)
        other=[p for p in inventory if p['pid'] not in allowed]
        assert not other,('pre-stop process gate',other)
        write('initial_verify.json',final_verify())
        compatibility()
        write('pre-stop-classified.json',dict(api=ns.api_pids(),memory_policy_watch=ns.watch_pids()))
        stopped=True;ns.stop_api(ROOT);gate()
        idx=0
        for rd,arms in [(6,['O','P']),(7,['P','O'])]:
            for arm in arms:idx+=1;run(idx,rd,arm)
        result=summarize_confirm()
        if result['mean_pct']>=3 and result['ci95_pct'][0]>0:outcome='PASS'
        elif all(x<0 for x in result['round_deltas_pct'][-2:]):outcome='FAIL'
        else:
            for arm in ['O','P']:idx+=1;run(idx,8,arm)
            result=summarize_confirm();outcome='FINAL'
        save(phase='MEASURE_COMPLETE',outcome=outcome,round8_ran=len(ROWS)==60,formal_requests=len(ROWS))
    except BaseException:
        error=traceback.format_exc();save(phase='ERROR',error=error)
    finally:
        save(before_restore_phase=STATE.get('phase'),phase='RESTORE')
        restore=ns.restore_api(ROOT) if stopped else dict(restored=True,not_stopped=True)
        try:vf=final_verify()
        except BaseException:vf=dict(verified=False,error=traceback.format_exc())
        write('final_verify.json',vf)
        save(phase='DONE' if error is None and vf['verified'] else 'FAILED',restored=restore.get('restored'),verified=vf['verified'],ended_utc=dt.datetime.now(dt.timezone.utc).isoformat())
if __name__=='__main__':main()
'''
Path('state/po-confirm-20261029/controller_confirm.py').write_text(s,encoding='utf-8')
