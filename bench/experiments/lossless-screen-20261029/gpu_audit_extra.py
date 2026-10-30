import importlib.util
import json
import hashlib
from pathlib import Path
import re
HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('screen_gate',HERE/'screen.py')
s=importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)
best=json.loads(s.BEST.read_text(encoding='utf-8-sig'))
out={'pre_gate':s.gate(best),'source':r'C:\Users\User\native-pipe-generic-20261029'}
root=Path(out['source'])
pattern=re.compile(r'\bnative_q6_k_pack\s*\(|\bnative_q6_k_packed_enabled\s*\(')
out['q6_callsite_scan']={'files':0,'bytes':0,'matches':[]}
for base in (root/'src',root/'include'):
    for p in sorted(base.rglob('*')):
        if p.suffix.lower() not in {'.cpp','.hpp','.cu','.cuh','.h','.c'} or not p.is_file():
            continue
        b=p.read_bytes()
        lines=b.decode('utf-8').splitlines()
        out['q6_callsite_scan']['files']+=1
        out['q6_callsite_scan']['bytes']+=len(b)
        for i,line in enumerate(lines,1):
            if pattern.search(line):
                out['q6_callsite_scan']['matches'].append({'path':str(p.relative_to(root)),
                  'line':i,'sha256':hashlib.sha256(b).hexdigest().upper(),
                  'context':{str(j):lines[j-1] for j in range(max(1,i-4),min(len(lines),i+6)+1)}})
path=root/'src/prefill/prefill.cpp'
b=path.read_bytes()
lines=b.decode('utf-8').splitlines()
pat=re.compile(r'native_data|native_type|native_q8|native_mmvq|dequant|native_weight')
chosen=set()
for i,line in enumerate(lines,1):
    if pat.search(line):
        chosen.update(range(max(1,i-3),min(len(lines),i+5)+1))
out['prefill']={'path':str(path),'sha256':hashlib.sha256(b).hexdigest().upper(),
 'total_lines':len(lines),'selected_lines':{str(i):lines[i-1] for i in sorted(chosen)}}
out['post_gate']=s.gate(best)
(HERE/'gpu-source-extra.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out['q6_callsite_scan'],indent=2))
print('PREFILL_EXCERPT_LINES',len(chosen),'OF',len(lines))
