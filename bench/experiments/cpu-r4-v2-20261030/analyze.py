import csv,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
names={16:'IQ2_XXS',17:'IQ2_XS',22:'IQ2_S',18:'IQ3_XXS',21:'IQ3_S'}
for run in ('cpu-r4-v2-20261030','cpu-r4-cost-20261030'):
 R=ROOT/run;rows=[];conv=[];fast=[];numeric=[];bits=[]
 for p in (R/'raw').glob('lp*.log'):
  ls=list(csv.reader(p.read_text().splitlines()));assert any(x[0]=='DONE' for x in ls)
  for x in ls:
   if x[0]=='SUM':
    ty,lp,nt,full,arm=map(int,x[1:6]);a,b,ratio=map(float,x[6:]);rows.append(dict(type=ty,lp=lp,nt=nt,full=full,arm=arm,A_us=a,B_us=b,ratio=a/b))
   elif x[0]=='CONVERT':conv.append(list(map(float,x[1:])))
   elif x[0]=='FAST_CONVERT':fast.append(list(map(float,x[1:])))
   elif x[0]=='NUMERIC':numeric.append(x)
   elif x[0]=='R4_BITS':bits.append(x)
 assert len(bits)==30 and all(x[-1]=='0' for x in bits)
 selected=[x for x in rows if x['full']==1 and x['arm']==(2 if x['lp']==2 else 1)]
 assert len(selected)==30
 summary=dict(run=run,selected=selected,all_rows=rows,old_convert=conv,fast_convert=fast,numeric=numeric,R4_bits_checked_cells=len(bits),selected_positive=sum(x['ratio']>1 for x in selected),best=max(x['ratio'] for x in selected),worst=min(x['ratio'] for x in selected))
 (R/'analysis.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
 print(run,'P:gather/E:scalar VNNI',summary['selected_positive'],'positive of30')
 for ty,n in names.items():
  vals=[next(x['ratio'] for x in selected if x['type']==ty and x['lp']==lp and x['nt']==nt) for lp in (2,15) for nt in (1,2,3)]
  print(n,','.join(f'{(v-1)*100:+.1f}%' for v in vals))
 if fast:
  for f in fast:
   o=next(x for x in conv if x[:2]==f[:2]);print('convert',int(f[0]),int(f[1]),o[2:4],f[2:4])
asm=(ROOT/'cpu-r4-v2-20261030/raw/r4.asm').read_text(errors='replace')
asm_rows=[]
for m in re.finditer(r'^([^\n]+) PROC[^\n]*\n(.*?)^\1 ENDP',asm,re.M|re.S):
 code=m.group(2)
 if 'mul_mat_iq' not in m.group(1):continue
 stack=[line.strip() for line in code.splitlines() if 'YMMWORD PTR' in line and re.search(r'\[(?:r|e)(?:sp|bp)',line)]
 asm_rows.append(dict(function=m.group(1),YMM_stack_instructions=len(stack),examples=stack[:3]))
(ROOT/'cpu-r4-v2-20261030/assembly.json').write_text(json.dumps({'vpdpbusd':asm.count('vpdpbusd'),'vpdpwssd':asm.count('vpdpwssd'),'gather':asm.count('vpgather'),'functions':asm_rows},indent=2),encoding='utf-8')
