import pickle, json, collections, bisect, sqlite3, csv, statistics
exec(open('explore2.py').read().split("def offs(tid)")[0])
BASE_OFF=134374190870760500
conv=lambda ft:(int(ft)-BASE_OFF)*100-sess[1]+50000
htid=host-gpid
BASE=0x7FF764B80000
hf=[]
for r in csv.reader(open(W+'etlA.io.csv')):
    if r[0]=='HFAULT' and int(r[8],16)==htid:
        hf.append((conv(r[4]),conv(r[1]),int(r[9])))
hf=[h for h in hf if T0<=h[0]<T1]
posts=sorted((l[3],l[4]) for l in layers); ps=[p[0] for p in posts]
wins=d['wins']; ws=[w[1] for w in wins]
cnt=collections.Counter(); tm=collections.Counter()
for a,b,by in hf:
    j=bisect.bisect_right(ps,a)-1
    ph='between'
    if j>=0 and a<posts[j][1]: ph='post'
    else:
        k=bisect.bisect_right(ws,a)-1
        if k>=0 and a<wins[k][2]: ph='in-window(pre/head/tail)'
    cnt[ph]+=1; tm[ph]+=b-a
print({k:(cnt[k],round(tm[k]/1e6/nwin,2)) for k in cnt},'total ms/window',sum(tm.values())/1e6/nwin)
# stacks for HFAULT
rv=set()
rows=[]
for r in csv.reader(open(W+'etlA.stacks.csv')):
    if r[0]=='HFAULT' and int(r[2])==htid:
        fr=[int(x,16) for x in r[3:] if x.startswith('0x')]
        rows.append((int(r[1]),fr))
        for ip in fr:
            if BASE<=ip<BASE+0x32EB000: rv.add(ip-BASE)
print('HFAULT stacks host',len(rows),'unique strata rvas',len(rv))
json.dump(sorted(rv),open(W+'rvas_hf.json','w'))
pickle.dump(rows,open(W+'hfstacks.pkl','wb'))
