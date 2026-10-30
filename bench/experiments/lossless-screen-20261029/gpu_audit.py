"""Read-only targeted audit of the exact live build source."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('screen_gate',HERE/'screen.py')
screen=importlib.util.module_from_spec(spec)
spec.loader.exec_module(screen)
best=json.loads(screen.BEST.read_text(encoding='utf-8-sig'))
pre=screen.gate(best)
source=Path(r'C:\Users\User\native-pipe-generic-20261029')
targets={
 'src/core/native_dense.cpp': [(100,114),(275,322),(350,465)],
 'src/kernels/cuda/native_mmvq.cu': [(1863,1899),(1934,1975),(2298,2308)],
 'src/core/prefill.cpp': [],
 'src/core/verify.cpp': [],
 'src/core/mtp.cpp': [],
 'include/strata/core/native_dense.hpp': [],
}
pattern=re.compile(r'native_q6_k_pack\(|native_q6_k_unpack\(|native_q8_0_packed_|native_data|native_packed|native_qtype|dequant|WARPS\s*=')
out={'source':str(source),'source_commit':best['source']['commit'],
     'binary_sha256':best['binary_sha256'],'pre_gate':pre,'files':{}}
for rel,ranges in targets.items():
    path=source/rel
    if not path.is_file():
        out['files'][rel]={'missing':True}
        continue
    data=path.read_bytes()
    lines=data.decode('utf-8').splitlines()
    selected=set()
    for a,b in ranges:
        selected.update(range(a,min(b,len(lines))+1))
    hits=[]
    for i,line in enumerate(lines,1):
        if pattern.search(line):
            hits.append(i)
            selected.update(range(max(1,i-3),min(len(lines),i+4)+1))
    out['files'][rel]={'sha256':hashlib.sha256(data).hexdigest().upper(),
      'line_count':len(lines),'hit_lines':hits,
      'selected_lines':{str(i):lines[i-1] for i in sorted(selected)}}
out['post_gate']=screen.gate(best)
(HERE/'gpu-source-audit.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
for rel,info in out['files'].items():
    print(rel,info.get('sha256'),info.get('line_count'), 'hits',info.get('hit_lines'))
print('AUDIT_SAVED')
