import json, math
from pathlib import Path
p=Path(__file__).resolve().parent
r=p.parent/'overnight-20261029'
rows=[x for x in json.loads((r/'rows.json').read_text()) if x['arm']=='D']
ph=json.loads((r/'phases.json').read_text())
assert len(rows)==len(ph)==30
for a,b in zip(rows,ph): assert a['windows']==b['windows']
out=[]
for key in sorted({x['pid'] for x in rows}):
    pairs=[(a,b) for a,b in zip(rows,ph) if a['pid']==key]
    w=sum(b['windows'] for a,b in pairs)
    out.append(dict(point=key,windows=w,ssd_MB=sum(b['useful_bytes'] for a,b in pairs)/w/1e6,ssd_experts=sum(a['m_file_blobs'] for a,b in pairs)/w,cpu_experts_layer=sum(a['cpu_experts_per_layer_window']*b['windows'] for a,b in pairs)/w,lru_ms=sum(b['lru_ms'] for a,b in pairs)/w,copy_ms=sum(b['copy_ms'] for a,b in pairs)/w))
def fit(x,y):
    mx=sum(x)/len(x); my=sum(y)/len(y)
    xx=sum((v-mx)**2 for v in x); yy=sum((v-my)**2 for v in y)
    xy=sum((a-mx)*(b-my) for a,b in zip(x,y))
    slope=xy/xx
    return dict(intercept=my-slope*mx,slope=slope,R2=xy*xy/xx/yy)
fits={y:{x:fit([a[x] for a in out],[a[y] for a in out]) for x in ('ssd_MB','ssd_experts','cpu_experts_layer')} for y in ('lru_ms','copy_ms')}
result=dict(points=out,fits_unweighted_10_point= fits,bytes_vs_misses=fit([a['ssd_experts'] for a in out],[a['ssd_MB'] for a in out]))
(p/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
