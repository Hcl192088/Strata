import sqlite3, json, sys, bisect, subprocess, statistics as st, collections
from pathlib import Path
R=Path(__file__).resolve().parent
N=r'C:\Program Files\NVIDIA Corporation\Nsight Systems 2026.5.1\target-windows-x64\nsys.exe'
db=R/'trace2.sqlite'
if not db.exists():
    subprocess.run([N,'export','--type','sqlite','--force-overwrite','true','-o',str(db),str(R/'trace2.nsys-rep')],check=True)
res=json.loads((R/'result2.json').read_text(encoding='utf-8'))
c=sqlite3.connect(str(db))
t0=c.execute("select utcEpochNs from TARGET_INFO_SESSION_START_TIME").fetchone()[0]
marks=[(w-t0,l) for w,l in res['marks']]
pp=[w for w,l in marks if l.startswith('PP ')]; done=[w for w,l in marks if l.startswith('DONE')]
Tn=sum(1 for w,l in marks if l.startswith('T '))
a=pp[-1]; b=done[0]
names=dict(c.execute("select id,value from StringIds"))
K=[(s,e,names.get(n,str(n))) for s,e,n in c.execute("select start,end,shortName from CUPTI_ACTIVITY_KIND_KERNEL where end>? and start<? order by start",(a,b))]
# refine segment: first kernel after PP mark to DONE
a=K[0][0]; b=min(b,K[-1][1])
def fam(n):
    l=n.lower()
    if 'mmvq' in l: return 'dense_mmvq'
    if l.startswith('gr_') or '_gr_' in l: return 'hc_gr'
    if 'attn' in l: return 'attention'
    if 'gdn' in l or 'delta' in l: return 'gdn'
    if 'router' in l or 'topk' in l: return 'router'
    return 'other'
mid={v:k for k,v in c.execute("select metricId,metricName from TARGET_INFO_GPU_METRICS")}
def m(prefix): return [k for v,k in mid.items() if v.startswith(prefix)][0]
GR,RD,WR=m('GR Active [Throughput'),m('DRAM Read Bandwidth'),m('DRAM Write Bandwidth')
S=collections.defaultdict(dict)
for ts,mi,v in c.execute("select timestamp,metricId,value from GPU_METRICS where timestamp between ? and ? and metricId in (?,?,?)",(a,b,GR,RD,WR)):
    S[ts][mi]=v
ts=sorted(S)
starts=[k[0] for k in K]
def kernel_at(t):
    i=bisect.bisect_right(starts,t)-1
    return K[i] if i>=0 and K[i][1]>=t else None
PEAK=504.2
busy=[]; famS=collections.defaultdict(list); kS=collections.defaultdict(list)
for t in ts:
    d=S[t]; bw=d.get(RD,0)+d.get(WR,0)
    k=kernel_at(t)
    if d.get(GR,0)>=90: busy.append(bw)
    if k: famS[fam(k[2])].append(bw); kS[k[2]].append(bw)
# union busy time
u=0; ce=a
for s,e,_ in K:
    s=max(s,ce); 
    if e>s: u+=e-s; ce=e
famT=collections.defaultdict(float); kT=collections.defaultdict(float); kC=collections.Counter()
for s,e,n in K: famT[fam(n)]+=e-s; kT[n]+=e-s; kC[n]+=1
W=Tn
def q(x,p): x=sorted(x); return x[int(p*(len(x)-1))] if x else None
out={'segment_s':(b-a)/1e9,'tokens':W,'ms_per_token':(b-a)/1e6/W,'kernels':len(K),'samples':len(ts),
 'gpu_busy_frac':u/(b-a),'kernel_ms_per_token':u/1e6/W,
 'busy_GR90':{'n':len(busy),'dram_pct_mean':st.mean(busy) if busy else None,'p10':q(busy,.1),'p50':q(busy,.5),'p90':q(busy,.9)},
 'family':{f:{'ms_per_token':famT[f]/1e6/W,'n_samples':len(famS[f]),'dram_pct_mean':st.mean(famS[f]) if famS[f] else None} for f in famT},
 'top10':[{'kernel':n,'count':kC[n],'ms_per_token':kT[n]/1e6/W,'mean_us':kT[n]/kC[n]/1e3,'n_samples':len(kS[n]),'dram_pct_mean':st.mean(kS[n]) if kS[n] else None} for n in sorted(kT,key=kT.get,reverse=True)[:10]]}
for blk in [out['busy_GR90']]+list(out['family'].values())+out['top10']:
    if blk.get('dram_pct_mean') is not None: blk['GBps']=blk['dram_pct_mean']/100*PEAK
(R/'analysis2.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
