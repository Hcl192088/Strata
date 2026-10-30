import re,json,hashlib,itertools
from pathlib import Path
R=Path(__file__).resolve().parent
p=Path(r'C:\Users\User\native-pipe-generic-20261029\third_party\ggml\ggml-common.h')
s=p.read_text();rows=[]
for name,n,nb in [('iq2xxs_grid',256,8),('iq2xs_grid',512,8),('iq2s_grid',1024,8),('iq3xxs_grid',256,4),('iq3s_grid',512,4)]:
 m=re.search(r'GGML_TABLE_BEGIN\(uint(?:32|64)_t,\s*'+name+r',\s*'+str(n)+r'\)(.*?)GGML_TABLE_END',s,re.S);assert m,name
 vals=[int(x,16) for x in re.findall(r'0x([0-9a-fA-F]+)',m[1])];assert len(vals)==n
 chunks={tuple(v.to_bytes(nb,'little')[j:j+4]) for v in vals for j in range(0,nb,4)}
 patterns={tuple(x*(-1 if signs&(1<<i) else 1) for i,x in enumerate(ch)) for ch in chunks for signs in range(16)}
 P=len(patterns)
 rows.append(dict(name=name,entries=n,unique_unsigned4=len(chunks),unique_signed4=P,tile32_bytes_per_token=8*P*4,full_H_bytes_per_token=640*P*4,full_H_bytes_nt3=3*640*P*4,
  build_dot4_fraction_of_GU_for_nexperts={str(ne):P/(1280*ne) for ne in (1,4,8,16)},warning='Operation-count ratio only; LUT indexing/loads/build/cache omitted, not a speed forecast.'))
(R/'p2-patterns.json').write_text(json.dumps(dict(source=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),rows=rows),indent=2))
print(json.dumps(rows,indent=2))
