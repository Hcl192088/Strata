from pathlib import Path
import json,re,hashlib
R=Path(__file__).resolve().parent
lines=json.loads((R/'raw/gpu2-profile-lines.json').read_text())
assert len(lines)==3
rows=[]
for point,line in zip(('p01','p05','p08'),lines):
 a,b=line.split(' | QSA layers:');b,total=b.split(' | total ')
 rows.append(dict(point=point,reported_total_ms=float(total.split()[0]),windows=int(re.search(r'over (\d+)',total)[1])))
# Preserve labels with embedded digits via a name-guided extraction.
names=['q8+qkv/q-idx gemv','z','out-proj','q8+kv-idx','k/v+norm-rope','q+q-idx','conv','ab','rec','gate','shared+quant','copy+combine','hc-read1+router','hc0 norm','hc0 down','hc0 up','waitCPU']
for row,line in zip(rows,lines):
 a,b=line.split(' | QSA layers:');b=b.split(' | total ')[0]
 def get(s,name):
  m=re.search(re.escape(name)+r' ([0-9.]+)(?:\s|$)',s);return float(m[1]) if m else 0.0
 row['GDN']={n:get(a,n) for n in names};row['QSA']={n:get(b,n) for n in names}
 row['waitCPU_ms']=get(a,'waitCPU')+get(b,'waitCPU')
 row['broad_projection_ms']=sum(get(a,n) for n in ['q8+qkv/q-idx gemv','z','out-proj'])+sum(get(b,n) for n in ['q8+kv-idx','k/v+norm-rope','q+q-idx','out-proj'])
 row['copy_combine_ms']=get(a,'copy+combine')+get(b,'copy+combine')
 row['shared_quant_ms']=get(a,'shared+quant')+get(b,'shared+quant')
 row['hc0_ms']=sum(get(a,n)+get(b,n) for n in ['hc0 norm','hc0 down','hc0 up'])
out=dict(status='COST_DIAG_COMPLETED_P3_P4_KERNELS_NOT_MEASURED',rows=rows,limits=['profile disables shared side stream and DF_BRANCH','not uninstrumented critical path','broad projections include non-Q6 work','no new kernel or quality parity measurement'])
(R/'gpu-analysis.json').write_text(json.dumps(out,indent=2))
manifest={p.name:dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in (R/'raw').glob('gpu*') if p.is_file()}
(R/'gpu-raw-manifest.json').write_text(json.dumps(manifest,indent=2))
for r in rows:print(r['point'],{n:r[n] for n in ['windows','waitCPU_ms','broad_projection_ms','copy_combine_ms','shared_quant_ms','hc0_ms']})
