import pickle, json, collections, bisect, sqlite3, csv, statistics
exec(open('explore2.py').read().split("def offs(tid)")[0])
sym=json.load(open(W+'symres.json')); BASE=0x7FF764B80000
keep=d['S_kept']; stk=d['stk']
nm=lambda ip:(sym.get(str(ip-BASE)) or ['unk'])[0] if ip>=BASE else 'unk'
role=collections.defaultdict(collections.Counter)
for sid,(st,tid,li,state) in keep.items():
    for f in stk.get(sid,[]):
        if f[2]=='strata':
            n=nm(f[1])
            if 'ExpertPool::worker' in n: role[tid]['pool_worker']+=1;break
            if 'Verifier::run' in n: role[tid]['host']+=1;break
tr={}
for t in workers+[host]:
    r=role[t]; tr[t]=('host' if t==host else 'pool' if r['pool_worker']>0 else 'other')
print({t-gpid:tr[t] for t in tr})
pool=[t for t in workers if tr[t]=='pool']
print('pool workers',len(pool))
def sched(tid):
    return c.execute('select start,isSchedIn,threadBlock,cpu from SCHED_EVENTS where globalTid=? and start between ? and ? order by start',(tid,T0-10**7,T1+10**7)).fetchall()
S={t:sched(t) for t in pool+[host]}
def intervals(ev):
    on=[];off=[];cur_in=None;cur_out=None
    for t,i,b,cpu in ev:
        if i:
            if cur_out: off.append((cur_out[0],t,cur_out[1])); cur_out=None
            cur_in=t
        else:
            if cur_in is not None: on.append((cur_in,t)); cur_in=None
            if cur_out is None: cur_out=(t,b)
    return on,off
I={t:intervals(S[t]) for t in S}
hon,hoff=I[host]
long50=[(a,b) for a,b,r in hoff if r==50 and b-a>=5e6 and T0<=a<T1]
print('stretches',len(long50))
# during stretch: pool worker on-cpu fraction, count of workers fully asleep
rows=[]
for a,b in long50:
    L=b-a
    onfrac=[]
    for t in pool:
        u=U(I[t][0]); onfrac.append(u.cov(a,b)/L)
    # last worker sched-in before host wake (within 100us)
    last=None
    for t in pool:
        for s,i,bl,cpu in S[t]:
            if i and b-200e3<=s<=b+20e3: last=(t,(s-b)/1e3)
    rows.append((L/1e6,sum(onfrac)/len(onfrac),sum(1 for x in onfrac if x<0.02),last))
print('mean worker on-cpu fraction during stalls',statistics.mean(r[1] for r in rows),' mean # of 9 pool workers with <2% on-cpu',statistics.mean(r[2] for r in rows))
print('stalls where a pool worker was scheduled in <=200us before host wake:',sum(1 for r in rows if r[3]),'of',len(rows))
for r in rows[:12]: print(' dur_ms %.1f worker_on_frac %.2f idle_workers %d last %s'%r)
# reasons of pool workers' off-CPU in the stalls
rc=collections.Counter()
for a,b in long50:
    for t in pool:
        for s0,s1,blk in I[t][1]:
            if s1>a and s0<b: rc[blk]+=min(s1,b)-max(s0,a)
tot=sum(rc.values()); print({k:round(100*v/tot,1) for k,v in rc.most_common(6)})
