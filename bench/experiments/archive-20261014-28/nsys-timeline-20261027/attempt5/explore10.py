import pickle, json, collections, bisect, sqlite3, csv, statistics
exec(open('explore2.py').read().split("def offs(tid)")[0])
BASE_OFF=134374190870760500
conv=lambda ft:(int(ft)-BASE_OFF)*100-sess[1]+50000
htid=host-gpid; BASE=0x7FF764B80000
sym=json.load(open(W+'symres.json'))
hf=[]
for r in csv.reader(open(W+'etlA.io.csv')):
    if r[0]=='HFAULT' and int(r[8],16)==htid:
        a=conv(r[4]); b=conv(r[1])
        if T0<=a<T1: hf.append((a,b))
posts=sorted((l[3],l[4]) for l in layers); ps=[p[0] for p in posts]
btw=[]
for a,b in hf:
    j=bisect.bisect_right(ps,a)-1
    if not (j>=0 and a<posts[j][1]): btw.append((a,b))
print('between-window HF',len(btw))
S=[(st,sid) for sid,st in c.execute('select id,start from COMPOSITE_EVENTS where globalTid=? and start>=? and start<?',(host,T0,T1))]
S.sort(); st_=[x[0] for x in S]
need={}
for a,b in btw:
    j=bisect.bisect_right(st_,a)-1
    if j>=0 and a-st_[j]<1.5e6: need[S[j][1]]=1
print('samples needed',len(need))
names=dict(c.execute('select id,value from StringIds').fetchall())
stk=collections.defaultdict(list); mod={}
for sid,symid,m,dep in c.execute('select id,symbol,module,stackDepth from SAMPLING_CALLCHAINS'):
    if sid in need:
        v=names.get(symid,''); ip=int(v,16) if v.startswith('0x') else -1
        p=names.get(m,'').lower()
        stk[sid].append((dep,ip,'strata' if p.endswith('strata.exe') else p.split(chr(92))[-1]))
agg=collections.Counter(); agg2=collections.Counter()
for sid,fr in stk.items():
    fr.sort()
    st=[f for f in fr if f[2]=='strata']
    if st:
        r=sym.get(str(st[0][1]-BASE)); 
        nm=(r[0] if r else None) or 'unk(%x)'%(st[0][1]-BASE)
        agg[nm]+=1
        # chain
        chain=[]
        for f in st[:5]:
            rr=sym.get(str(f[1]-BASE)); chain.append(((rr[0] if rr else '?') or '?').split('::')[-1][:40])
        agg2[' < '.join(chain)]+=1
    else: agg['(no strata frame) leaf '+fr[0][2]]+=1
print(agg.most_common(10)); 
for k,v in agg2.most_common(6): print(v,k)
