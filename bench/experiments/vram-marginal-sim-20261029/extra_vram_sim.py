import struct,sys
from collections import Counter,defaultdict
trace,nexp=sys.argv[1],sys.argv[2]
L={}
for line in open(nexp):
    if line.startswith('#'):continue
    p=line.split();L[int(p[0])]=(int(p[1]),int(p[2]),int(p[4]))
n=1638400;dbpw={20:4.5,42:2.25}
gu_us={18:247.1,21:227.6,17:244.7,22:207.1,16:217.7}
def cost(l): g,d,b=L[l];return gu_us[g]+n*dbpw[d]/8/4.9/1e3
data=open(trace,'rb').read();pos=0;last=-1;wins=[];cur=None
while pos<len(data):
    layer,k=struct.unpack_from('<ii',data,pos);ids=struct.unpack_from('<%di'%k,data,pos+8)
    if pos==0 or (layer==0 and last==47): cur=defaultdict(list);wins.append(cur)
    cur[layer].append(ids);last=layer;pos+=8+8*k   # stored order taken as rank order (inferred)
def uses(ws):
    a=Counter();r7=Counter()
    for W in ws:
        for l,t in W.items():
            for e in set(e for x in t for e in x):a[(l,e)]+=1
            for e in set(e for x in t for e in x[:7]):r7[(l,e)]+=1
    return a,r7
def pick(score,budget):
    s=0;sel=set()
    for x,v in sorted(score.items(),key=lambda kv:-kv[1]):
        b=L[x[0]][2]
        if s+b>budget: continue
        s+=b;sel.add(x)
    return sel
def ev(sel,ws):
    cpu=0.0;tail=tailskip=0;u_all=h_all=0;n7=h7=0
    for W in ws:
        for l,t in W.items():
            u=set(e for x in t for e in x);k7=set(e for x in t for e in x[:7])
            u_all+=len(u);h_all+=sum((l,e) in sel for e in u)
            n7+=len(k7);h7+=sum((l,e) in sel for e in k7)
            cpu+=sum(cost(l) for e in k7 if (l,e) not in sel)
            for x in t:
                for e in x[7:]:
                    tail+=1;tailskip+=(l,e) not in sel and e not in set(y for z in t for y in z[:7])
    return dict(cpu_ms=round(cpu/len(ws)/1e3,2),hit_all=round(h_all/u_all,4),hit_r7=round(h7/n7,4),tail_routes_skipped=round(tailskip/tail,4))
h=len(wins)//2
for name,tr,te in (('in-sample',wins,wins),('held-out',wins[:h],wins[h:])):
    a,r7=uses(tr)
    for extra in (0,178,563,675,563+675):
        B=(5245+extra)*2**20;r=ev(pick(a,B),te)
        print(name,'+%d MiB'%extra,r)
