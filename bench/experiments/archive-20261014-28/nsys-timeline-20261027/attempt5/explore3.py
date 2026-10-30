import pickle, json, collections
W='D:/strata/state/nsys-timeline-20261027/attempt5/work/'
d=pickle.load(open(W+'stage1.pkl','rb'))
sym=json.load(open(W+'symres.json')); BASE=0x7FF764B80000
layers=d['layers']; keep=d['S_kept']; stk=d['stk']; host=d['host']
cls=lambda p:'short' if p<250e3 else 'mid' if p<1e6 else 'long'
nm=lambda ip:(sym.get(str(ip-BASE)) or ['unk'])[0] if ip>=BASE else 'unk'
sig=collections.Counter(); tot=0
rd=collections.Counter(); rdn=0
chain=collections.Counter()
for sid,(st,tid,li,state) in keep.items():
    if tid!=host: continue
    l=layers[li]
    if cls(l[4]-l[3])!='long': continue
    fr=stk.get(sid,[])
    tot+=1
    hasstrata=any(f[2]=='strata' for f in fr)
    if not hasstrata:
        sig[tuple(f[2] for f in fr[:4])+(len(fr),)]+=1
    else:
        names=[nm(f[1]) for f in fr if f[2]=='strata']
        if any('read_direct' in n for n in names):
            rdn+=1
            i=[k for k,n in enumerate(names) if 'read_direct' in n][0]
            chain[' <- '.join(n[:48] for n in names[i:i+4])]+=1
            rd[tuple(f[2] for f in fr[:3])]+=1
print('host long samples',tot)
print('no strata frames: top signatures (module of frames 0..3, depth)'); 
for k,v in sig.most_common(8): print(' ',v,k)
print('read_direct samples',rdn); 
for k,v in rd.most_common(6): print(' leaf modules',v,k)
for k,v in chain.most_common(8): print(' chain',v,k)
print('---- full chains above prefetch')
ch2=collections.Counter()
for sid,(st,tid,li,state) in keep.items():
    if tid!=host: continue
    fr=stk.get(sid,[])
    names=[nm(f[1]) for f in fr if f[2]=='strata']
    if any('read_direct' in n for n in names):
        i=[k for k,n in enumerate(names) if 'prefetch' in n]
        if i:
            ch2[' <- '.join(n.split('::')[-2]+'::'+n.split('::')[-1] if '::' in n else n for n in [x[:60] for x in names[i[0]:i[0]+6]])]+=1
for k,v in ch2.most_common(6): print(v,k)
# also: other prefetch/fill_many callers in the whole host stack population (all classes)
