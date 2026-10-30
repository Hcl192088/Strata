"""Analyze actual decode-boundary CPU_PHASE_DECODE receipts; no proxy prefill subtraction."""
import json
import statistics as st
import sys
from pathlib import Path

root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
rows=json.loads((root/'rows.json').read_text())
ph=json.loads((root/'phases.json').read_text())
drows=[r for r in rows if r['arm']=='D']
assert len(ph)==len(drows) and ph
for d,r in zip(ph,drows):
    assert d['windows']==r['windows']
    assert abs(d['cpu_ms']/d['windows']-r['cpu_ms'])<=.011
tot={k:sum(d[k] for d in ph) for k in ph[0]}
w=tot['windows'];cpu=tot['cpu_ms']
parts=('gu_ms','quant_ms','down_ms','join_ms','lru_ms','cpu_residual_ms')
res=dict(requests=len(ph),windows=w,
    CPU_ms_window=cpu/w,
    components_ms_window={k:tot[k]/w for k in parts},
    components_CPU_fraction={k:tot[k]/cpu for k in parts},
    separate_overlapping_ms_window={k:tot[k]/w for k in ('helper_ms','direct_ms','copy_ms','issue_wait_ms','ready_ms','inline_ms')},
    issued_GB=tot['issued_bytes']/1e9,useful_GB=tot['useful_bytes']/1e9,
    read_amplification=tot['issued_bytes']/tot['useful_bytes'] if tot['useful_bytes'] else None,
    inline_calls=tot['inlines'],splits=tot['splits'],
    notes=['GU/down are full pool phase wall time, including worker imbalance/memory stalls, not pure instructions.',
           'helper/direct/copy/issue_wait are overlapping thread work; do not add them to components.',
           'issue_wait includes issue and GetOverlappedResult duration, not isolated SSD device service time.',
           'Existing active MT1 source/config/temperature were not changed; this is a diagnostic build.'])
bypt={}
for p in sorted({r['pid'] for r in drows}):
    pairs=[(d,r) for d,r in zip(ph,drows) if r['pid']==p]
    win=sum(d['windows'] for d,r in pairs)
    bypt[p]=dict(requests=len(pairs),windows=win,**{k:sum(d[k] for d,r in pairs)/win for k in ('cpu_ms',)+parts+('helper_ms','inline_ms','issue_wait_ms','copy_ms')})
res['by_point']=bypt
rounds=sorted({r['round'] for r in rows})
by={}
for arm in ('C','O','D'):
    by[arm]={}
    for rd in rounds:
        a=[r for r in rows if r['arm']==arm and r['round']==rd]
        if a:
            by[arm][rd]=dict(rate=sum(r.get('m_out_tokens') or r['tokens'] for r in a)*1000/sum(r.get('m_decode_ms') or r['decode_ms'] for r in a),requests=len(a))
res['speed_by_round_not_promotion']=by
res['speed_excluded_rounds']={1:'C ran Normal; O changed Normal to AboveNormal mid-block. No priority-matched comparison.'}
res['paired_diagnostic_deltas']={}
for a,b in [('O','C'),('D','O')]:
    v=[(by[a][r]['rate']/by[b][r]['rate']-1)*100 for r in rounds if r>=2 and r in by[a] and r in by[b]]
    if v:res['paired_diagnostic_deltas'][a+'_vs_'+b]=dict(n=len(v),mean_pct=st.mean(v),deltas=v,
        note='Small diagnostic sample; changed outputs/window mix; not a candidate promotion test.')
res['next_decision_inputs']=dict(
    GU_time_reduction_20pct_ms_window=tot['gu_ms']/w*.2,
    eliminate_join_upper_ms_window=tot['join_ms']/w,
    eliminate_copy_thread_time_not_speedup_ms_window=tot['copy_ms']/w,
    residual_fraction=tot['cpu_residual_ms']/cpu)
(root/'phase_analysis.json').write_text(json.dumps(res,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({k:res[k] for k in ('requests','windows','CPU_ms_window','components_ms_window','components_CPU_fraction','separate_overlapping_ms_window','read_amplification','paired_diagnostic_deltas','next_decision_inputs')},indent=2))
