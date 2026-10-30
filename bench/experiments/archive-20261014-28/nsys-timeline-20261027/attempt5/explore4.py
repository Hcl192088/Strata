import pickle, json, collections, bisect, sqlite3, csv, statistics
exec(open('explore2.py').read().split("def offs(tid)")[0])   # reuse loaders (workers, U, c, thr...)
sym=json.load(open(W+'symres.json')); BASE=0x7FF764B80000
keep=d['S_kept']; stk=d['stk']
nm=lambda ip:(sym.get(str(ip-BASE)) or ['unk'])[0] if ip>=BASE else 'unk'
isc={}
def compute_sample(sid):
    r=isc.get(sid)
    if r is None:
        r=False
        for f in stk.get(sid,[]):
            if f[2]=='strata':
                n=nm(f[1])
                if n.startswith('ggml_') or 'vnni' in n or 'rows<' in n:
                    r=True;break
        isc[sid]=r
    return r
# host on intervals
ev=c.execute('select start,isSchedIn from SCHED_EVENTS where globalTid=? and start between ? and ? order by start',(host,T0-10**7,T1+10**7)).fetchall()
on=[];cur=None
for t,i in ev:
    if i: cur=t
    elif cur is not None: on.append((cur,t));cur=None
Uon=U(on)
# sample rate r (samples per on-cpu ns) for host
BASE_OFF=134374190870760500
conv=lambda ft:(int(ft)-BASE_OFF)*100-sess[1]+50000
rows=collections.defaultdict(list)
for r in csv.reader(open(W+'etlA.io.csv')):
    if r[0] in('FREAD','FEND'): rows[r[0]].append(r)
fend=collections.defaultdict(list)
for r in rows['FEND']: fend[r[4]].append(int(r[1]))
for k in fend: fend[k].sort()
htid=host-gpid
bigr=[]
for r in rows['FREAD']:
    if int(r[3])==htid and int(r[5])>=500000:
        l=fend[r[6]]; j=bisect.bisect_left(l,int(r[1]))
        if j<len(l):
            a,b=conv(r[1]),conv(l[j])
            if T0<=a<T1: bigr.append((a,b,int(r[5])))
bigr.sort(); bst=[x[0] for x in bigr]
hs=[(v[0],v[2]) for s,v in keep.items() if v[1]==host]
hon=sum(Uon.cov(l[3],l[4]) for l in layers)
rate=len(hs)/hon
print('host sample rate per on-cpu ms',rate*1e6)
wsamp=[(v[0],s) for s,v in keep.items() if v[1]!=host and v[1] in workers]
wsamp.sort(); wst=[x[0] for x in wsamp]
nW=9
seg=collections.defaultdict(lambda:[0,0.0,0])  # wall ns, compute samples, n layers
for li,l in enumerate(layers):
    Den,R=l[3],l[4]
    p=R-Den
    if p<1e6: continue
    j=bisect.bisect_left(bst,Den)
    rs=[]
    while j<len(bigr) and bigr[j][0]<R: rs.append(bigr[j]); j+=1
    if len(rs)!=1: continue
    a,b,_=rs[0]
    b=min(b,R); a=max(a,Den)
    for name,(x,y) in (('before_read',(Den,a)),('during_read',(a,b)),('after_read',(b,R))):
        if y<=x: continue
        i0=bisect.bisect_left(wst,x); i1=bisect.bisect_left(wst,y)
        cs=sum(1 for t,s in wsamp[i0:i1] if compute_sample(s))
        tot=i1-i0
        sg=seg[name]; sg[0]+=y-x; sg[1]+=cs; sg[2]+=1
        seg[name+'_all'][1]+=tot
        seg[name+'_all'][0]+=y-x
nl=sum(1 for l in layers)
for name in ('before_read','during_read','after_read'):
    wall,cs,n=seg[name]
    tot=seg[name+'_all'][1]
    thr_ms=cs/rate/1e6
    print('%-12s layers=%d wall_ms_sum=%.1f  mean_wall_us=%.0f  worker_compute_thread_ms=%.1f  => utilisation of %d workers = %.1f%% ; all-running-samples share compute=%.1f%%'%(name,n,wall/1e6,wall/n/1e3,thr_ms,nW,100*thr_ms/(nW*wall/1e6),100*cs/max(1,tot)))
