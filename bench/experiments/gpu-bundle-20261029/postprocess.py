import sys,json
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R));import controller as c
c.gate('collect',True);c.write('independent_verify.json',c.verify())
assert json.loads((R/'campaign.json').read_text())['phase']=='DONE'
import exactness as ex
out=[]
for pid in ['p01','p05','p08']:
 msgs={a:json.loads((R/'out'/d/('resp-'+pid+'.json')).read_text(encoding='utf-8'))['choices'][0]['message'] for a,d in [('C','block-01-C-r1'),('G','block-00-SMOKE-r0')]}
 fields={}
 for f in ['reasoning_content','content']:
  cs={a:msgs[a].get(f) or '' for a in ['C','G']};ids={a:ex.tok.encode(cs[a]) for a in cs};ci,gi=ids['C'],ids['G'];idx=next((i for i,(x,y) in enumerate(zip(ci,gi)) if x!=y),min(len(ci),len(gi)) if len(ci)!=len(gi) else None)
  fields[f]=dict(identical=cs['C']==cs['G'],first_differing_token_index_0based=idx)
 out.append(dict(pid=pid,fields=fields,identical=all(x['identical'] for x in fields.values())))
c.write('smoke-exactness.json',dict(comparison='G SMOKE versus C round1; not a same-round pair',pairs=out))
print('independent live verification, exactness and smoke comparison done')
