from pathlib import Path
import json,csv,hashlib
R=Path(__file__).resolve().parent
p1=[];p2=[]
for p in (R/'raw').glob('lp*.log'):
 rows=list(csv.reader(p.read_text().splitlines()));assert any(x[0]=='DONE' for x in rows)
 assert len([x for x in rows if x[0]=='P1_BITS'])==3
 for x in rows:
  if x[0]=='SUM':
   ty,lp,nt,full,arm=map(int,x[1:6]);a,b,ratio=map(float,x[6:]);p1.append(dict(lp=lp,nt=nt,full=full,rows=2 if arm==1 else 4,A_us=a,B_us=b,ratio=a/b))
for p in (R.parent/'big-lut-20261030/raw').glob('lp*.log'):
 rows=list(csv.reader(p.read_text().splitlines()));assert any(x[0]=='DONE' for x in rows)
 assert len([x for x in rows if x[0]=='P2_BITS'])==2
 for x in rows:
  if x[0]=='P2_SUM':
   lp,nt,ne,full=map(int,x[1:5]);a,b,ratio=map(float,x[5:]);p2.append(dict(lp=lp,nt=nt,batch_experts=ne,full=full,A_us=a,B_us=b,ratio=a/b))
assert len(p1)==24 and len(p2)==24
summary=dict(P1=p1,P2=p2,P1_full_best=max(x['ratio'] for x in p1 if x['full']),P1_full_worst=min(x['ratio'] for x in p1 if x['full']),P2_full_best=max(x['ratio'] for x in p2 if x['full']),P2_full_worst=min(x['ratio'] for x in p2 if x['full']),status='P1_P2_TESTED_NO_PROMOTION_P3_P4_PENDING_API_STOP_APPROVAL')
(R/'analysis.json').write_text(json.dumps(summary,indent=2))
for name,rows in [('P1',p1),('P2',p2)]:
 print(name)
 for x in rows:
  if x['full']:print(x)
manifest={}
for root in (R,R.parent/'big-lut-20261030'):
 for p in (root/'raw').glob('*'):
  if p.is_file():manifest[str(p.relative_to(R.parent))]=dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
(R/'raw-manifest.json').write_text(json.dumps(manifest,indent=2))
