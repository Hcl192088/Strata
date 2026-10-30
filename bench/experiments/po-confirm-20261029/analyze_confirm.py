import json,statistics as st,math
from pathlib import Path
R=Path(__file__).resolve().parent
old=json.loads((R.parent/'overnight-20261029/pipeline-results/rows.json').read_text())
new=json.loads((R/'rows.json').read_text());rows=[r for r in old if r['arm'] in ('O','P')]+new
def tok(r):return r.get('m_out_tokens') or r['tokens']
def ms(r):return r.get('m_decode_ms') or r['decode_ms']
def rate(rs):return 1000*sum(map(tok,rs))/sum(map(ms,rs))
def ci(v,t):
 m=st.mean(v);h=t*st.stdev(v)/math.sqrt(len(v));return dict(n=len(v),df=len(v)-1,mean_pct=m,ci95_pct=[m-h,m+h])
groups={}
for r in rows:groups.setdefault((r['round'],r['arm']),[]).append(r)
assert all(len(rs)==10 and len({r['pid'] for r in rs})==10 for rs in groups.values())
rates={k:rate(v) for k,v in groups.items()};rounds=sorted({rd for rd,a in groups})
deltas=[100*(rates[rd,'P']/rates[rd,'O']-1) for rd in rounds]
primary=ci(deltas,{7:2.446911851,8:2.364624252}[len(rounds)])
point_pooled={pid:100*(rate([r for r in rows if r['pid']==pid and r['arm']=='P'])/rate([r for r in rows if r['pid']==pid and r['arm']=='O'])-1) for pid in sorted({r['pid'] for r in rows})}
point_mean={pid:st.mean([100*((tok(next(r for r in groups[rd,'P'] if r['pid']==pid))/ms(next(r for r in groups[rd,'P'] if r['pid']==pid)))/(tok(next(r for r in groups[rd,'O'] if r['pid']==pid))/ms(next(r for r in groups[rd,'O'] if r['pid']==pid)))-1) for rd in rounds]) for pid in point_pooled}
drift={}
length={}
for arm in ['O','P']:
 ov=[v for (rd,a),v in rates.items() if a==arm and rd<=5];nv=[v for (rd,a),v in rates.items() if a==arm and rd>5]
 drift[arm]=dict(old_round_mean=st.mean(ov),new_round_mean=st.mean(nv),change_pct=100*(st.mean(nv)/st.mean(ov)-1))
 for label,rr in [('old',old),('new',new),('combined',rows)]:
  rs=[r for r in rr if r['arm']==arm];length[label+'_'+arm]=dict(requests=len(rs),tokens=sum(map(tok,rs)),windows=sum(r['windows'] for r in rs),pooled_tok_s=rate(rs),tokens_per_window=sum(map(tok,rs))/sum(r['windows'] for r in rs))
blocks=[dict(round=rd,arm=a,pooled_tok_s=v,tokens=sum(map(tok,groups[rd,a])),decode_ms=sum(map(ms,groups[rd,a])),windows=sum(r['windows'] for r in groups[rd,a])) for (rd,a),v in sorted(rates.items())]
result=dict(primary=primary,round_deltas_pct=deltas,blocks=blocks,secondary_point_pooled=ci(list(point_pooled.values()),2.262157163),point_pooled_deltas_pct=point_pooled,secondary_original_method=ci(list(point_mean.values()),2.262157163),point_mean_deltas_pct=point_mean,drift=drift,length=length,sequential_look='依預註冊在第7輪檢視一次，必要時第8輪終止；標稱95% t-CI未校正 sequential look，型一錯誤略升。')
(R/'analysis.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(result,indent=2,ensure_ascii=False))
