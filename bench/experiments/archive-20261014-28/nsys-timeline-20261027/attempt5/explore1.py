import pickle, json, collections, bisect, sys
W='D:/strata/state/nsys-timeline-20261027/attempt5/work/'
d=pickle.load(open(W+'stage1.pkl','rb'))
sym=json.load(open(W+'symres.json'))
BASE=0x7FF764B80000
layers=d['layers']; keep=d['S_kept']; stk=d['stk']; host=d['host']; gpid=d['gpid']
post=[(r[4]-r[3]) for r in layers]
def cls(p):
    return 'short<250us' if p<250e3 else 'mid250-1000' if p<1e6 else 'long>=1ms'
def fn(ip):
    r=ip-BASE
    s=sym.get(str(r))
    return (s[0] or 'unk')+'' if s else 'unk'
agg=collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
tot=collections.defaultdict(collections.Counter)
for sid,(st,tid,li,state) in keep.items():
    who='host' if tid==host else 'worker'
    c=cls(post[li])
    fr=stk.get(sid,[])
    if not fr: continue
    leaf=fr[0]
    key = fn(leaf[1]) if leaf[2]=='strata' else '['+leaf[2]+']'
    # first strata frame
    fs=next((f for f in fr if f[2]=='strata'),None)
    agg[(who,c)]['leaf'][key]+=1
    tot[(who,c)]['n']+=1
    if fs: agg[(who,c)]['first_strata'][fn(fs[1])]+=1
for k in sorted(agg):
    print('=====',k,tot[k]['n'])
    for name,cn in agg[k]['leaf'].most_common(10): print('  leaf %5.1f%% %s'%(100*cn/tot[k]['n'],name[:110]))
    for name,cn in agg[k]['first_strata'].most_common(6): print('  fs   %5.1f%% %s'%(100*cn/tot[k]['n'],name[:110]))
