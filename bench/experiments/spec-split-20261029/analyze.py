import json,statistics as st,math
from pathlib import Path
R=Path(__file__).resolve().parent
rows=json.loads((R/'rows.json').read_text(encoding='utf-8'));groups={}
for r in rows:groups.setdefault((r['round'],r['arm']),[]).append(r)
def metrics(rs):
 w=sum(r['windows'] for r in rs);tok=sum(r['m_out_tokens'] for r in rs);ms=sum(r['m_decode_ms'] for r in rs)
 d=dict(tokens=tok,decode_ms=ms,windows=w,pooled_tok_s=1000*tok/ms,ms_window=ms/w,tokens_window=tok/w)
 for k in ['cpu_ms','gpu_wait_ms','cpu_experts_per_layer_window','vram_hits_per_layer_window']:d[k]=sum(r[k]*r['windows'] for r in rs)/w
 return d
def ci(x):
 n=len(x);t={3:4.302652729911275,5:2.7764451051977987,10:2.2621571628540993}[n];m=st.mean(x);e=t*st.stdev(x)/math.sqrt(n)
 return dict(n=n,df=n-1,t=t,mean_pct=m,ci95_pct=[m-e,m+e],deltas_pct=x)
blocks=[dict(round=rd,arm=a,**metrics(rs)) for (rd,a),rs in groups.items()]
rounds=sorted({rd for rd,a in groups if (rd,'C') in groups and (rd,'S') in groups})
primary=ci([100*(metrics(groups[rd,'S'])['pooled_tok_s']/metrics(groups[rd,'C'])['pooled_tok_s']-1) for rd in rounds])
qs=[]
for pid in sorted({r['pid'] for r in rows}):
 rate={a:metrics([r for r in rows if r['arm']==a and r['pid']==pid])['pooled_tok_s'] for a in ['C','S']}
 qs.append(dict(pid=pid,delta_pct=100*(rate['S']/rate['C']-1),rates=rate))
result=dict(blocks=blocks,primary=primary,secondary=dict(**ci([x['delta_pct'] for x in qs]),questions=qs),method='primary paired round percent S/C; secondary pool per-question tokens/time across rounds, paired df9')
result['verdict']='STOPPED' if len(rounds)==3 and (all(x<0 for x in primary['deltas_pct']) or primary['mean_pct'] < -3) else ('CANDIDATE' if primary['mean_pct']>=3 and primary['ci95_pct'][0]>0 else 'NOT_CANDIDATE')
(R/'analysis.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
