import json,statistics as st,math
from pathlib import Path
R=Path(__file__).resolve().parent
rows=json.loads((R/'rows.json').read_text());groups={}
for r in rows:groups.setdefault((r['round'],r['arm']),[]).append(r)
def metrics(rs):
 w=sum(r['windows'] for r in rs);tok=sum(r['m_out_tokens'] for r in rs);ms=sum(r['m_decode_ms'] for r in rs)
 d=dict(tokens=tok,decode_ms=ms,windows=w,pooled_tok_s=1000*tok/ms,ms_window=ms/w,tokens_window=tok/w)
 for k in ['cpu_ms','gpu_wait_ms','pcie_per_layer_window','cpu_experts_per_layer_window']:d[k]=sum(r[k]*r['windows'] for r in rs)/w
 return d
blocks=[dict(round=rd,arm=a,**metrics(rs)) for (rd,a),rs in groups.items()]
def ci(x):
 n=len(x);t={3:4.302652729911275,5:2.7764451051977987,10:2.2621571628540993}[n];m=st.mean(x);e=t*st.stdev(x)/math.sqrt(n)
 return dict(n=n,df=n-1,t=t,mean_pct=m,ci95_pct=[m-e,m+e],deltas_pct=x)
comparisons={};secondary={}
for a,b in [('B8','C'),('B8','P8'),('P8','C')]:
 rounds=sorted({rd for rd,arm in groups if (rd,a) in groups and (rd,b) in groups})
 if not rounds:continue
 vals=[100*(metrics(groups[rd,a])['pooled_tok_s']/metrics(groups[rd,b])['pooled_tok_s']-1) for rd in rounds]
 comparisons[a+'/'+b]=ci(vals)
 qs=[]
 for pid in sorted({r['pid'] for r in rows}):
  rate={arm:sum(r['m_out_tokens'] for r in rows if r['arm']==arm and r['pid']==pid)*1000/sum(r['m_decode_ms'] for r in rows if r['arm']==arm and r['pid']==pid) for arm in [a,b]}
  qs.append(dict(pid=pid,delta_pct=100*(rate[a]/rate[b]-1),rates=rate))
 secondary[a+'/'+b]=dict(**ci([x['delta_pct'] for x in qs]),questions=qs)
result=dict(blocks=blocks,comparisons=comparisons,secondary=secondary,secondary_method='per question pool tokens/time across rounds, then paired percent; df9')
if comparisons:
 c=comparisons['B8/C'];result['verdict']='CANDIDATE' if c['n']==5 and c['mean_pct']>=3 and c['ci95_pct'][0]>0 else 'NOT_CANDIDATE'
else:result['verdict']='NOT_MEASURED'
(R/'analysis.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
