import json,re
from pathlib import Path
p=Path(__file__).resolve().parent
blocks=json.loads((p/'blocks.json').read_text())
for b in blocks:
 print(b['index'],b['arm'],b['rate'],b['ms_window'],b['windows'])
lines=[l for b in blocks for l in b['pool_diag']]
(p/'POOL_DIAG.raw.txt').write_text('\n'.join(lines)+'\n')
rows=[]
for l in lines:
 vals=dict(re.findall(r'(\w+)=([\d.]+)',l));rows.append({k:float(v) for k,v in vals.items()})
keys=['ms_window','calls','p_gu','p_down','p_quant','e_gu','e_down','e_quant','host_wait','suffix','apply','verify','commit_emit','draft','unattributed']
tot=sum(r['windows'] for r in rows)
for k in keys: print(k,round(sum(r[k]*r['windows'] for r in rows)/tot,6))
for arm in 'CD':
 bs=[b for b in blocks if b['arm']==arm]; n=sum(b['windows'] for b in bs)
 print(arm,'weighted_ms',sum(b['ms_window']*b['windows'] for b in bs)/n,'mean_rate',sum(b['rate'] for b in bs)/len(bs))
print('conservation_max',max(abs(r['ms_window']-sum(r[k] for k in ['suffix','apply','verify','commit_emit','draft','unattributed']))/r['ms_window']*100 for r in rows))
