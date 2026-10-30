from pathlib import Path
import shutil
R=Path(__file__).resolve().parent
H=R/'pipeline-harness';H.mkdir(exist_ok=True)
shutil.copyfile(R/'shadow-harness/next_steps_ab_20261018.py',H/'next_steps_ab_20261018.py')
t=(R/'shadow-harness/replay_ab_20261027.py').read_text()
t=t.replace("'DIRECT_SHADOW FATAL'", "'NATIVE_PIPE FATAL'")
t=t.replace("DIRECT_SHADOW FATAL: candidate refused source/read; no fallback", "NATIVE_PIPE FATAL: scheduler failure; no fallback")
old="            assert effective.get('STRATA_DIRECT_SHADOW_FIRST') == (spec.get('env') or {}).get('STRATA_DIRECT_SHADOW_FIRST')"
assert t.count(old)==1
t=t.replace(old,"            assert effective.get('STRATA_NATIVE_PIPE') == (spec.get('env') or {}).get('STRATA_NATIVE_PIPE')\n            assert effective.get('STRATA_NATIVE_PIPE_CHECK') == (spec.get('env') or {}).get('STRATA_NATIVE_PIPE_CHECK')")
(H/'replay_ab_20261027.py').write_text(t)
t=(R/'controller_shadow.py').read_text()
def change(old,new):
    global t
    assert t.count(old)==1,(old[:60],t.count(old))
    t=t.replace(old,new)
change("EXE_SHA='9268FAD812CB2C970D021EC7EAF29A2C6E137593A47F07BB2061F5FCBC858C42'","EXE_SHA='3F98913EDB0B01D5D5DD3282412725141C298BF5CC9E890DD286AA0720C27230'")
change("SHADOW=ROOT/'first-shard.direct'","EXPECTED_FORMATS={(17,20),(16,42),(17,42),(21,42),(22,42),(18,20),(18,42),(22,20),(21,20),(16,20)}  # replaced from actual descriptor before launch")
start=t.index("    receipt=json.loads((ROOT/'copy.json').read_text())")
end=t.index('\ndef gate():',start)
t=t[:start]+t[end:]
start=t.index('def spec(arm):');end=t.index('\ndef phases(',start)
t=t[:start]+'''def spec(arm):
    env={'STRATA_NATIVE_PIPE':'1' if arm in ('P','PD','CHK','SMOKE') else None,
         'STRATA_NATIVE_PIPE_CHECK':'1' if arm in ('CHK','SMOKE') else None,
         'STRATA_CPU_PHASE_DIAG':'1' if arm in ('OD','PD','CHK','SMOKE') else None,
         'STRATA_MISS_OVERLAP_CHECK':None}
    return dict(exe=str(ns.EXE_C if arm=='C' else EXE),sha=ns.EXE_C_SHA if arm=='C' else EXE_SHA,
        serve_dir=r'C:\\Users\\User\\Strata-Adrian\\runs\\iq3-campaign-020\\upstream-v0142',env=env,args={},strict_capacity=True)
'''+t[end:]
change("('gu_ms','quant_ms','down_ms','join_ms','lru_ms')","('gu_ms','quant_ms','down_ms','pipeline_ms','join_ms','lru_ms')")
start=t.index("    if arm=='BAD_PATH':");end=t.index("    STATE.setdefault('completed',[])",start)
t=t[:start]+'''    assert meta['status']=='OK' and len(rows)==len(points or rp.POINTS) and all(not r.get('error') for r in rows),(arm,meta)
    assert meta['priority_gate']['priority']==psutil.ABOVE_NORMAL_PRIORITY_CLASS
    assert 'NATIVE_PIPE FATAL' not in text and 'NATIVE_PIPE_CHECK MISMATCH' not in text
    if arm in ('P','PD','CHK','SMOKE'):
        assert 'NATIVE_PIPE ACTIVE' in text
        counters=re.findall(r'NATIVE_PIPE progress calls=(\\d+) overlap_down_tiles=(\\d+) down_tiles=(\\d+) pool_ms=([\\d.]+)',text)
        assert counters and max(int(x[1]) for x in counters)>0,'no actual GU/down overlap'
        write('last-pipeline-counters.json',dict(arm=arm,round=rd,last=counters[-1],scope='whole engine including prompt'))
    else:assert 'NATIVE_PIPE ACTIVE' not in text
    if arm in ('CHK','SMOKE'):
        checks=re.findall(r'NATIVE_PIPE_CHECK batches=(\\d+) values=(\\d+) gu_type=(\\d+) down_type=(\\d+) mismatch=0',text)
        assert checks and max(int(x[0]) for x in checks)>=100 and max(int(x[1]) for x in checks)>=100000
        seen={(int(x[2]),int(x[3])) for x in checks}
        write('check-format-coverage-'+arm+'.json',dict(seen=sorted(seen),expected=sorted(EXPECTED_FORMATS),missing=sorted(EXPECTED_FORMATS-seen)))
        if arm=='CHK':assert EXPECTED_FORMATS<=seen,('independent reference format coverage incomplete',EXPECTED_FORMATS-seen)
    if arm in ('OD','PD','CHK','SMOKE'):
        ph=phases(text,rows);write('phase-'+arm+'.json',ph)
        for p,r in zip(ph,rows):PHASES.append(dict(arm=arm,pid=r['pid'],**p))
        write('phase-rows.json',PHASES)
'''+t[end:]
change("if arm in ('C','O','S'):ROWS.extend(rows);write('rows.json',ROWS)","if arm in ('C','O','P'):ROWS.extend(rows);write('rows.json',ROWS)")
change("[('S','O'),('S','C'),('O','C')]","[('P','O'),('P','C'),('O','C')]")
change("('STRATA_IQ_MT_MIN','STRATA_CPU_PHASE_DIAG','STRATA_DIRECT_SHADOW_FIRST')","('STRATA_IQ_MT_MIN','STRATA_CPU_PHASE_DIAG','STRATA_NATIVE_PIPE','STRATA_NATIVE_PIPE_CHECK')")
change(",shadow_mtime_ns=SHADOW.stat().st_mtime_ns,completed=[]",",completed=[]")
change("        run(0,0,'BAD_PATH',[],0)\n        run(1,0,'CHK',['p01','p05','p08'],128)\n        run(2,0,'OD');run(3,0,'SD')", "        run(0,0,'SMOKE',['p01','p05','p08'],128)\n        run(1,0,'CHK',None,128)\n        run(2,0,'OD');run(3,0,'PD')")
change("[['C','O','S'],['O','S','C'],['S','C','O'],['C','S','O'],['S','O','C']]","[['C','O','P'],['O','P','C'],['P','C','O'],['C','P','O'],['P','O','C']]")
change("result['comparisons']['S_vs_O']","result['comparisons']['P_vs_O']")
assert 'SHADOW' not in t and 'SD' not in t and 'BAD_PATH' not in t
(R/'controller_pipeline.py').write_text(t)
print('prepared pipeline controller and priority-gated harness; expected formats must come from descriptor')
