import pickle, json, collections, bisect, csv
exec(open('explore2.py').read().split("def offs(tid)")[0])
sym=json.load(open(W+'symres.json')); BASE=0x7FF764B80000
keep=d['S_kept']; stk=d['stk']
BASE_OFF=134374190870760500
conv=lambda ft:(int(ft)-BASE_OFF)*100-sess[1]+50000
htid=host-gpid
rows=collections.defaultdict(list)
for r in csv.reader(open(W+'etlA.io.csv')):
    if r[0] in('FREAD','FEND'): rows[r[0]].append(r)
fend=collections.defaultdict(list)
for r in rows['FEND']: fend[r[4]].append(int(r[1]))
for k in fend: fend[k].sort()
iv=[]
for r in rows['FREAD']:
    if int(r[3])==htid and int(r[5])>=500000:
        l=fend[r[6]]; j=bisect.bisect_left(l,int(r[1]))
        if j<len(l): iv.append((conv(r[1]),conv(l[j])))
Uio=U(iv)
cls=lambda p:'short' if p<250e3 else 'mid' if p<1e6 else 'long'
tot=collections.Counter(); inio=collections.Counter()
for sid,(st,tid,li,state) in keep.items():
    if tid!=host: continue
    l=layers[li]
    if cls(l[4]-l[3])!='long': continue
    fr=stk.get(sid,[])
    has=any(f[2]=='strata' for f in fr)
    cat='kernel-only' if not has else 'strata'
    tot[cat]+=1
    if Uio.cov(st,st+1)>0: inio[cat]+=1
print({k:(tot[k],inio[k],round(100*inio[k]/tot[k],1)) for k in tot})
# kernel-only samples: module signature of deeper frames (any non-ntoskrnl modules)
mods=collections.Counter()
for sid,(st,tid,li,state) in keep.items():
    if tid!=host or cls(layers[li][4]-layers[li][3])!='long': continue
    fr=stk.get(sid,[])
    if any(f[2]=='strata' for f in fr): continue
    mods[tuple(sorted(set(f[2] for f in fr)))]+=1
print(mods.most_common(6))
