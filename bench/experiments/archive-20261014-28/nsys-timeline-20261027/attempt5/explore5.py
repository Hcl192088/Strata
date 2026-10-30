import pickle, json, collections, bisect, sqlite3, csv, statistics
exec(open('explore2.py').read().split("def offs(tid)")[0])
BASE_OFF=134374190870760500
conv=lambda ft:(int(ft)-BASE_OFF)*100-sess[1]+50000
htid=host-gpid
rows=collections.defaultdict(list)
for r in csv.reader(open(W+'etlA.io.csv')):
    if r[0] in('FREAD','FEND','HFAULT'): rows[r[0]].append(r)
fend=collections.defaultdict(list)
for r in rows['FEND']: fend[r[4]].append(int(r[1]))
for k in fend: fend[k].sort()
reads=[]
for r in rows['FREAD']:
    if int(r[3])==htid and int(r[5])>=500000:
        l=fend[r[6]]; j=bisect.bisect_left(l,int(r[1]))
        if j<len(l): reads.append((conv(r[1]),conv(l[j])))
reads.sort(); bst=[x[0] for x in reads]
hfw=[(conv(r[4]),conv(r[1]),int(r[8],16)) for r in rows['HFAULT'] if int(r[8],16)!=htid]
hfh=[(conv(r[4]),conv(r[1]),int(r[8],16)) for r in rows['HFAULT'] if int(r[8],16)==htid]
Uhfw=U([(a,b) for a,b,_ in hfw]); Uhfh=U([(a,b) for a,b,_ in hfh])
cls=lambda p:'short' if p<250e3 else 'mid' if p<1e6 else 'long'
def has_read(Den,R):
    j=bisect.bisect_left(bst,Den); return j<len(bst) and bst[j]<R
# host off intervals with reasons
ev=c.execute('select start,isSchedIn,threadBlock from SCHED_EVENTS where globalTid=? and start between ? and ? order by start',(host,T0-10**7,T1+10**7)).fetchall()
offs_=[];cur=None
for t,i,b in ev:
    if i:
        if cur: offs_.append((cur[0],t,cur[1])); cur=None
    elif cur is None: cur=(t,b)
off50=U([(a,b) for a,b,r in offs_ if r==50]); 
print('layers noread long: ',)
nr=[l for l in layers if cls(l[4]-l[3])=='long' and not has_read(l[3],l[4])]
x=sum(1 for l in nr if Uhfw.cov(l[3],l[4])>100e3)
print(len(nr),'with worker hardfault >100us overlap',x,' worker HF overlap total ms/window',sum(Uhfw.cov(l[3],l[4]) for l in nr)/1e6/nwin)
print('host hf overlap in noread long (ms/window)',sum(Uhfh.cov(l[3],l[4]) for l in nr)/1e6/nwin)
# host off50 stretch durations in noread long
st=[]
for l in nr:
    for a,b,r in offs_:
        if r==50 and a<l[4] and b>l[3]: st.append((min(b,l[4])-max(a,l[3]))/1e3)
print('host AlertByThreadId stretches in noread-long: n',len(st),'mean us',statistics.mean(st),'p50',statistics.median(st),'p90',sorted(st)[int(.9*len(st))],'sum ms/window',sum(st)/1e3/nwin)
# distribution of noread-long layers by post duration bucket
b=collections.Counter()
for l in nr:
    p=(l[4]-l[3])/1e6
    b['1-2ms' if p<2 else '2-5ms' if p<5 else '5-10ms' if p<10 else '10+ms']+=p
print({k:round(v/nwin,2) for k,v in b.items()})
# per-window: T of the graph (variant) vs. long noread layers
gv=collections.Counter(); gl=collections.Counter()
wgid={w[0]:w[3] for w in d['wins']}
for l in layers: gl[wgid[l[0]]]+=1
for l in nr: gv[wgid[l[0]]]+=1
print({g:(gv[g],gl[g],round(100*gv[g]/gl[g],1)) for g in gl})
# time position within window (layer index)
li=collections.Counter(l[1] for l in nr)
print('long-noread by layer idx (top)',li.most_common(8))
