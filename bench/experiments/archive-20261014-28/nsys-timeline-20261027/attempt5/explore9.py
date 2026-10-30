import json, csv, collections, pickle
W='D:/strata/state/nsys-timeline-20261027/attempt5/work/'
BASE=0x7FF764B80000; SZ=0x32EB000
io={}
for r in csv.reader(open(W+'etlA.io.csv')):
    if r[0]=='FREAD': io[(int(r[1]))]=(int(r[3]),int(r[5]))
rows=[];rv=set()
for r in csv.reader(open(W+'etlA.stacks.csv')):
    ft=int(r[1]); tid=int(r[2])
    fr=[int(x,16) for x in r[3:] if x.startswith('0x')]
    sz=io.get(ft,(tid,0))[1]
    rows.append((ft,tid,sz,fr))
    for ip in fr:
        if BASE<=ip<BASE+SZ: rv.add(ip-BASE)
print(len(rows),len(rv))
json.dump(sorted(rv),open(W+'rvas_fread.json','w'))
pickle.dump(rows,open(W+'freadstacks.pkl','wb'))
