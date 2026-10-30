import json,csv,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent
names={16:'IQ2_XXS',17:'IQ2_XS',22:'IQ2_S',18:'IQ3_XXS',21:'IQ3_S'}
rows=[];numeric=[];parity=[];convert=[];raw=[];items=[]
for p in sorted((R/'raw').glob('lp*.log')):
 data=list(csv.reader(p.read_text().splitlines()))
 assert any(x[0]=='DONE' for x in data),p
 for x in data:
  if x[0]=='SUM':
   ty,lp,nt,full=map(int,x[1:5]);a,b,ratio=map(float,x[5:]);assert full==1
   rows.append(dict(type=ty,core='P' if lp==2 else 'E',nt=nt,A_us=a,B_us=b,speedup_percent=100*(a/b-1)))
  elif x[0]=='PARITY':parity.append([int(y) for y in x[1:]])
  elif x[0]=='NUMERIC':numeric.append(dict(type=int(x[1]),lp=int(x[2]),nt=int(x[3]),max_h=float(x[4]),max_diff_h=float(x[5]),different_h=int(x[6]),max_out=float(x[7]),max_diff_out=float(x[8]),different_out=int(x[9])))
  elif x[0]=='CONVERT':convert.append(dict(type=int(x[1]),lp=int(x[2]),pack_us=float(x[3]),unpack_us=float(x[4])))
  elif x[0]=='RAW':raw.append(x)
  elif x[0]=='ITEM':items.append(x)
assert len(rows)==30 and len(numeric)==30 and len(parity)==10 and len(raw)==540 and len(items)==360
assert all(x[-2:]==[0,0] for x in parity)
out=dict(status='NO_GO_BOUNDED_SCREEN',quality='NOT_ESTABLISHED_FLOAT_OUTPUT_DIFFERS',rows=rows,numeric=numeric,conversion=convert,
 coverage=dict(cells=10,expert_instances=360,unique_experts=180,selected_layers=30,total_layers=48,types=5,nt=[1,2,3],pairs_per_cell=9,AB_pairs=270,byte_roundtrip_bytes_including_both_cores=sum(x[2] for x in parity),decoded_values_including_both_cores=sum(x[3] for x in parity)),
 best_percent=max(x['speedup_percent'] for x in rows),worst_percent=min(x['speedup_percent'] for x in rows),positive=sum(x['speedup_percent']>0 for x in rows),negative=sum(x['speedup_percent']<0 for x in rows))
(R/'analysis.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
lines=['| Format | P nt1 | P nt2 | P nt3 | E nt1 | E nt2 | E nt3 |','|---|---:|---:|---:|---:|---:|---:|']
for ty,name in names.items():
 vals=[next(x['speedup_percent'] for x in rows if x['type']==ty and x['core']==core and x['nt']==nt) for core in ('P','E') for nt in (1,2,3)]
 lines.append('| '+name+' | '+' | '.join(f'{v:+.1f}%' for v in vals)+' |')
print('\n'.join(lines));print(json.dumps({k:v for k,v in out.items() if k not in ('rows','numeric','conversion')},indent=2))
manifest={str(p.relative_to(R)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (R/'raw').rglob('*') if p.is_file()}
(R/'raw-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
