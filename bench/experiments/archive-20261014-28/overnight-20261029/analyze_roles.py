"""Analyze completed blocks only; independent point and block pairing, no promotion mutation."""
import json,math,statistics as st,sys
from pathlib import Path

ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent/'roles-results'
T95={1:12.706205,2:4.302653,3:3.182446,4:2.776445,5:2.570582,6:2.446912,7:2.364624,8:2.306004,9:2.262157}
def interval(vals):
    n=len(vals);mean=st.mean(vals)
    t=T95.get(n-1)
    return dict(n=n,mean=mean,ci95=[mean-t*st.stdev(vals)/math.sqrt(n),mean+t*st.stdev(vals)/math.sqrt(n)] if t else None)
def tok(r):return r.get('m_out_tokens') or r['tokens']
def ms(r):return r.get('m_decode_ms') or r['decode_ms']
def rate(rows):return sum(tok(r) for r in rows)*1000/sum(ms(r) for r in rows)
rows=json.loads((ROOT/'rows.json').read_text()) if (ROOT/'rows.json').exists() else []
assert all(r['arm'] in ('C','G','R') and not r.get('error') and ms(r)>0 and tok(r)>0 for r in rows)
assert len({(r['arm'],r['round'],r['pid']) for r in rows})==len(rows)
groups={}
for r in rows:groups.setdefault((r['round'],r['arm']),[]).append(r)
assert all(len(rs)==10 and len({r['pid'] for r in rs})==10 for rs in groups.values())
rates={k:rate(rs) for k,rs in groups.items()}
res=dict(formal_requests=len(rows),complete_blocks=len(groups),round_rates={str(k):v for k,v in sorted(rates.items())},comparisons={},phase_diagnostics={})
for a,b in [('R','G'),('R','C'),('G','C')]:
    paired_rounds=sorted({rd for rd,arm in groups if arm==a and (rd,b) in groups})
    if not paired_rounds:continue
    deltas=[(rates[(rd,a)]/rates[(rd,b)]-1)*100 for rd in paired_rounds]
    point_means={}
    for pid in sorted({r['pid'] for r in rows}):
        vals=[]
        for rd in paired_rounds:
            ar=[r for r in groups[(rd,a)] if r['pid']==pid][0]
            br=[r for r in groups[(rd,b)] if r['pid']==pid][0]
            vals.append(((tok(ar)/ms(ar))/(tok(br)/ms(br))-1)*100)
        point_means[pid]=st.mean(vals)
    res['comparisons'][a+'_vs_'+b]=dict(
        paired_round_pct=interval(deltas),round_deltas_pct=deltas,
        paired_point_pct=interval(list(point_means.values())),point_mean_deltas_pct=point_means,
        note='Point CI clusters repetitions within each prompt; round CI treats complete ten-prompt blocks as independent. Output length/window mix may differ.')
for arm in ('C','G','R'):
    rs=[r for r in rows if r['arm']==arm]
    if rs:
        res.setdefault('arm_summary',{})[arm]=dict(requests=len(rs),pooled_tok_s=rate(rs),round_rate=interval([v for (rd,a),v in rates.items() if a==arm]),
            output_tokens=sum(tok(r) for r in rs),windows=sum(r['windows'] for r in rs),tokens_per_window=sum(tok(r) for r in rs)/sum(r['windows'] for r in rs),
            decode_MB=sum(r['m_file_mb'] for r in rs),decode_blobs=sum(r['m_file_blobs'] for r in rs))
for arm in ('GD','RD'):
    p=ROOT/('phase-'+arm+'.json')
    if not p.exists():continue
    records=json.loads(p.read_text());assert len(records)==10
    windows=sum(r['windows'] for r in records)
    keys=('cpu_ms','gu_ms','quant_ms','down_ms','pipeline_ms','join_ms','lru_ms','cpu_residual_ms')
    vals={k:sum(r[k] for r in records)/windows for k in keys}
    res['phase_diagnostics'][arm]=dict(requests=10,windows=windows,ms_window=vals,
        combined_pool_ms_window=vals['gu_ms']+vals['quant_ms']+vals['down_ms']+vals['pipeline_ms'],
        separate_overlapping_ms_window={k:sum(r[k] for r in records)/windows for k in ('helper_ms','direct_ms','copy_ms','issue_wait_ms','ready_ms')},
        note='One diagnostic block per arm, changed outputs/window mix; not a statistical speed verdict.')
res['notes']=['SMOKE/CHK/reference-recompute speed excluded. No current-best mutation.',
    'Formal promotion requires preregistered >=3% gain and positive paired CI; partial rounds cannot establish success.',
    'Absolute >50 pooled tok/s is not evidence that all workloads or runs exceed 50.']
(ROOT/'analysis.json').write_text(json.dumps(res,indent=2)+'\n')
print(json.dumps(res,indent=2))
