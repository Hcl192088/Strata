import sys,json,hashlib
from pathlib import Path
from array import array
from collections import Counter
root=Path(r'C:\Users\User\Strata-Adrian-control')
sys.path.insert(0,str(root/'tools'))
import strata_tokenizer as ST
import draft_vocab as DV
out=root/'runs'/'untested5-20261031'/'s1'
out.mkdir(parents=True,exist_ok=True)
gguf=Path(r'C:\Users\User\Strata-IQ3-20261008\models\IQ3_XXS\Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf')
basepath=Path(r'C:\Users\User\Strata-v0.1.34-mtp-test-20261002\mtp\rt\draft_vocab.bin')
corpus=[root/'docs'/'DETAILS.md',root/'docs'/'AI_SETUP.md']
tok=ST.Tokenizer.from_gguf(gguf)
base=list(array('i',basepath.read_bytes()))
assert len(base)==106299 and len(set(base))==len(base)
counts=DV.corpus_counts(tok,corpus)
special={i for i in base if tok.token_types and tok.token_types[i] in (3,4)} | (set(tok.special_ids.values()) & set(base))
rank=sorted((i for i in base if i not in special),key=lambda i:(-counts[i],i))
responses=sorted((root/'runs'/'gpu6-ab-20261030'/'out').glob('block-*/resp-p*.json'))
assert responses
observed=Counter()
for path in responses:
 data=json.loads(path.read_text(encoding='utf-8'))
 for choice in data['choices']:
  m=choice['message']
  for k in ('reasoning_content','content'):
   if isinstance(m.get(k),str): observed.update(tok.encode(m[k]))
assert sum(observed.values())
result={'corpus':[str(x) for x in corpus],'corpus_tokens':sum(counts.values()),'response_files':len(responses),'responses_root':str(root/'runs'/'gpu6-ab-20261030'/'out'),'response_text_tokens_reencoded':sum(observed.values()),'special_count':len(special),'base':str(basepath),'base_sha256':hashlib.sha256(basepath.read_bytes()).hexdigest(),'gguf':str(gguf),'coverage_kind':'retokenized content and reasoning, not original emitted token ids','variants':{}}
for size in (65536,32768,106299):
 selected=set(base) if size==len(base) else special | set(rank[:size-len(special)])
 ids=[i for i in base if i in selected]
 assert len(ids)==size and special <= selected
 cov=sum(n for i,n in observed.items() if i in selected)/sum(observed.values())
 item={'size':size,'coverage':cov}
 if size!=len(base):
  p=out/('draft_vocab_v%d.bin'%(size//1024)); p.write_bytes(array('i',ids).tobytes()); item.update(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 result['variants'][str(size)]=item
(out/'vocab-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
