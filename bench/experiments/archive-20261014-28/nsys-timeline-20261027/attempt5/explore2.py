import pickle, json, collections, bisect, sqlite3, csv, statistics
W='D:/strata/state/nsys-timeline-20261027/attempt5/work/'
d=pickle.load(open(W+'stage1.pkl','rb'))
layers=d['layers']; host=d['host']; gpid=d['gpid']; T0,T1=d['T0'],d['T1']; thr=d['thr']; nwin=len(d['wins']); sess=d['sess']
workers=[t for t in thr if t!=host]
print('workers',len(workers),[t-gpid for t in workers])
c=sqlite3.connect('file:'+W+'trace-A.sqlite?mode=ro',uri=True)
class U:
    def __init__(s,iv):
        iv=sorted(iv); out=[]
        for a,b in iv:
            if b<=a: continue
            if out and a<=out[-1][1]:
                if b>out[-1][1]: out[-1][1]=b
            else: out.append([a,b])
        s.u=out; s.st=[x[0] for x in out]; s.cum=[0]
        for a,b in out: s.cum.append(s.cum[-1]+b-a)
    def cov(s,a,b):
        if b<=a or not s.u: return 0
        i=bisect.bisect_right(s.st,a)-1; tot=0
        if i>=0 and s.u[i][1]>a: tot+=min(s.u[i][1],b)-a
        j=i+1; k=bisect.bisect_left(s.st,b)
        if k>j:
            tot+=s.cum[k]-s.cum[j]
            if s.u[k-1][1]>b: tot-=s.u[k-1][1]-b
        return tot
def offs(tid):
    ev=c.execute('select start,isSchedIn,cpu,threadBlock from SCHED_EVENTS where globalTid=? and start between ? and ? order by start',(tid,T0-10**7,T1+10**7)).fetchall()
    out=[];cur=None;res=[]
    for t,isin,cpu,blk in ev:
        if isin:
            if cur: res.append((cur[0],t,cur[1])); cur=None
        else:
            if cur is None: cur=(t,blk)
    return res
BASE_OFF=134374190870760500
conv=lambda ft:(int(ft)-BASE_OFF)*100-sess[1]+50000
rows=collections.defaultdict(list)
for r in csv.reader(open(W+'etlA.io.csv')):
    if r[0] in('FREAD','FEND','HFAULT'): rows[r[0]].append(r)
fend=collections.defaultdict(list)
for r in rows['FEND']: fend[r[4]].append(int(r[1]))
for k in fend: fend[k].sort()
htid=host-gpid
bigr=[]
for r in rows['FREAD']:
    if int(r[3])==htid and int(r[5])>=500000:
        l=fend[r[6]]; j=bisect.bisect_left(l,int(r[1]))
        if j<len(l): bigr.append((conv(r[1]),conv(l[j])))
bigr=[x for x in bigr if T0<=x[0]<T1]
bst=[x[0] for x in bigr]
def has_read(Den,R):
    j=bisect.bisect_left(bst,Den); return j<len(bst) and bst[j]<R
cls=lambda p:'short' if p<250e3 else 'mid' if p<1e6 else 'long'
long_nr=[(l[3],l[4]) for l in layers if cls(l[4]-l[3])=='long' and not has_read(l[3],l[4])]
long_r=[(l[3],l[4]) for l in layers if cls(l[4]-l[3])=='long' and has_read(l[3],l[4])]
print('long no read',len(long_nr),'long with read',len(long_r))
for nm,L in (('long_noread',long_nr),('long_read',long_r)):
    ds=[(b-a)/1e6 for a,b in L]
    print(nm,'post ms mean',statistics.mean(ds),'p50',statistics.median(ds),'p90',sorted(ds)[int(.9*len(ds))])
# worker off reasons inside these layers
for nm,L in (('long_noread',long_nr),('long_read',long_r)):
    tot=sum(b-a for a,b in L)
    print('==',nm,'wall ms/window',tot/1e6/nwin)
    byr=collections.Counter(); hostr=collections.Counter()
    for t in workers:
        o=offs(t)
        byb=collections.defaultdict(list)
        for a,b,blk in o: byb[blk].append((a,b))
        for blk,iv in byb.items():
            u=U(iv)
            byr[blk]+=sum(u.cov(a,b) for a,b in L)
    ho=offs(host); byb=collections.defaultdict(list)
    for a,b,blk in ho: byb[blk].append((a,b))
    for blk,iv in byb.items():
        u=U(iv); hostr[blk]+=sum(u.cov(a,b) for a,b in L)
    print(' workers off-cpu thread-ms/window by reason (sum over %d workers):'%len(workers),{k:round(v/1e6/nwin,2) for k,v in byr.most_common(8)},' (of %.1f thread-ms available)'%(len(workers)*tot/1e6/nwin))
    print(' host off ms/window by reason',{k:round(v/1e6/nwin,2) for k,v in hostr.most_common(6)})
