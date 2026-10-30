import json,statistics as st,math,sys
from collections import defaultdict
T={1:12.706,2:4.303,3:3.182,4:2.776,5:2.571,6:2.447,7:2.365,8:2.306,9:2.262}
def load(f): return json.load(open(f))
def blockstats(rows):
    b=defaultdict(lambda:[0,0.0,{}])
    for r in rows:
        if r.get('error') or not r.get('m_decode_ms'): continue
        k=(r['arm'],r['round']); b[k][0]+=r['m_out_tokens'] or 0; b[k][1]+=r['m_decode_ms']
        b[k][2][r['pid']]=r['m_decode_tok_s']
    return b
def paired(vals):
    n=len(vals);m=st.mean(vals);s=st.stdev(vals) if n>1 else float('nan');h=T[n-1]*s/math.sqrt(n)
    return m,s,m-h,m+h,n-1
def report(rows,pairs,label):
    b=blockstats(rows)
    print('==',label)
    arms=sorted({k[0] for k in b})
    for a in arms:
        v=[b[(a,r)][0]/b[(a,r)][1]*1000 for r in range(1,6) if (a,r) in b]
        print(a,'pooled tok/s per round',[round(x,1) for x in v],'mean',round(st.mean(v),2))
    for x,y in pairs:
        d=[];dp=[]
        for r in range(1,6):
            if (x,r) in b and (y,r) in b:
                px=b[(x,r)][0]/b[(x,r)][1]*1000;py=b[(y,r)][0]/b[(y,r)][1]*1000
                d.append((px/py-1)*100)
        m,s,lo,hi,df=paired(d)
        print(f'{x} vs {y} pooled-by-round: mean {m:+.2f}% sd {s:.2f} 95%CI [{lo:+.2f},{hi:+.2f}] df={df} diffs',[round(v,1) for v in d])
        # per-point: mean over rounds of tok/s per point, paired over 10 points
        pts=sorted({p for k in b for p in b[k][2]})
        dpt=[]
        for p in pts:
            ax=[b[(x,r)][2][p] for r in range(1,6) if (x,r) in b and p in b[(x,r)][2]]
            ay=[b[(y,r)][2][p] for r in range(1,6) if (y,r) in b and p in b[(y,r)][2]]
            if ax and ay: dpt.append((st.mean(ax)/st.mean(ay)-1)*100)
        m,s,lo,hi,df=paired(dpt)
        print(f'   per-point: mean {m:+.2f}% sd {s:.2f} CI [{lo:+.2f},{hi:+.2f}] df={df}')
report(load('out/rows-AB.json'),[('M','D0'),('M','C0'),('D0','C0')],'AB')
sp=load('out/rows-SPIN.json')
for r in sp:
    pass
b=blockstats(sp);print([k for k in b])
report(sp,[('S2K','M'),('S100K','M')],'SPIN (rounds 1-3)')
