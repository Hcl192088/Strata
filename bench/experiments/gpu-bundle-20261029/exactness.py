import sys,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent
sys.path.insert(0,r'C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\upstream-v0142\tools')
import strata_tokenizer as ST
T=Path(r'C:\Users\User\Strata-IQ3-20261008\packs\iq3_xxs\tokenizer')
v=json.loads((T/'vocab.json').read_text(encoding='utf-8'));tokens=[None]*len(v)
for t,i in v.items():tokens[i]=t
tok=ST.Tokenizer(tokens,(T/'merges.txt').read_text(encoding='utf-8').split('\n'),json.loads((T/'token_type.json').read_text()))
rows=json.loads((R/'rows.json').read_text());groups={}
for row in rows:groups.setdefault((row['round'],row['pid']),{})[row['arm']]=row
out=[]
for (rd,pid),g in sorted(groups.items()):
 if set(g)!={'C','G'}:continue
 msgs={}
 for a,r in g.items():
  d=R/'out'/('block-%02d-%s-r%d'%(r['block'],a,rd));msgs[a]=json.loads((d/('resp-'+pid+'.json')).read_text(encoding='utf-8'))['choices'][0]['message']
 fields={}
 for field in ['reasoning_content','content']:
  text={a:msgs[a].get(field) or '' for a in ['C','G']};ids={a:tok.encode(s) for a,s in text.items()};c,s=ids['C'],ids['G'];idx=next((i for i,(x,y) in enumerate(zip(c,s)) if x!=y),min(len(c),len(s)) if len(c)!=len(s) else None)
  fields[field]=dict(identical=text['C']==text['G'],first_differing_token_index_0based=idx,C_tokens=len(c),G_tokens=len(s),C_token_id=c[idx] if idx is not None and idx<len(c) else None,G_token_id=s[idx] if idx is not None and idx<len(s) else None,C_token_text=tok.decode([c[idx]]) if idx is not None and idx<len(c) else None,G_token_text=tok.decode([s[idx]]) if idx is not None and idx<len(s) else None)
 out.append(dict(round=rd,pid=pid,identical=all(f['identical'] for f in fields.values()),fields=fields))
result=dict(method='Compare exact API reasoning_content and content strings independently, retokenized with same server tokenizer; indices zero-based per field. Original engine token IDs and stripped control tokens were not retained by harness.',tokenizer_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest().upper() for p in T.iterdir() if p.is_file()},pairs=out)
(R/'exactness.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(dict(pairs=len(out),identical=sum(x['identical'] for x in out))))
