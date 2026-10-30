import pickle, json, collections, bisect, sqlite3, csv, statistics
exec(open('explore2.py').read().split("def offs(tid)")[0])
BASE_OFF=134374190870760500
conv=lambda ft:(int(ft)-BASE_OFF)*100-sess[1]+50000
fw=[]
for r in csv.reader(open(W+'etlA.io.csv')):
    if r[0]=='FWRITE': fw.append((conv(r[1]),int(r[5]),int(r[3])))
fw.sort(); ft=[x[0] for x in fw]
print('FWRITE n',len(fw),'MB',sum(x[1] for x in fw)/1e6,'sizes',collections.Counter(x[1] for x in fw).most_common(4),'tids',collections.Counter(x[2] for x in fw).most_common(4))
inr=[x for x in fw if T0<=x[0]<T1]
print('in decode',len(inr),sum(x[1] for x in inr)/1e6,'MB; per window MB',sum(x[1] for x in inr)/1e6/nwin)
ev=c.execute('select start,isSchedIn,threadBlock from SCHED_EVENTS where globalTid=? and start between ? and ? order by start',(host,T0,T1)).fetchall()
offs_=[];cur=None
for t,i,b in ev:
    if i:
        if cur: offs_.append((cur[0],t,cur[1])); cur=None
    elif cur is None: cur=(t,b)
long50=[(a,b) for a,b,r in offs_ if r==50 and b-a>=5e6]
print('host AlertByThreadId stretches >=5ms',len(long50),'total ms',sum(b-a for a,b in long50)/1e6)
def wr_in(a,b):
    i=bisect.bisect_left(ft,a); j=bisect.bisect_left(ft,b); return j-i, sum(x[1] for x in fw[i:j])
w=[wr_in(a,b) for a,b in long50]
print('writes during long50 stretches: mean count',statistics.mean(x[0] for x in w),'mean KB',statistics.mean(x[1] for x in w)/1e3, ' frac stretches with any write',sum(1 for x in w if x[0]>0)/len(w))
# baseline write rate per ms
tot=(T1-T0)/1e6
print('baseline writes per ms',len(inr)/tot)
# long50 durations distribution and times
print('durations ms',sorted(round((b-a)/1e6,1) for a,b in long50)[::max(1,len(long50)//15)])
# are they periodic? print start times of first 25 (s)
print([round(a/1e9,2) for a,b in long50[:30]])
