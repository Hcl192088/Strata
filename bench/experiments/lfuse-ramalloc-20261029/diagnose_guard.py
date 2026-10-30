import json,re
from pathlib import Path
R=Path(r'C:\Users\User\Strata-Adrian-control\runs\lfuse-ab-20261029')
log=R/'out/block-00-C-r0/engine.log'
responses=[]
for p in (R/'out/block-00-C-r0').glob('resp-*.json'):
 j=json.loads(p.read_text(encoding='utf-8'))
 m=j['choices'][0]['message']
 responses.append((p.name,(m.get('reasoning_content') or '')+'\n'+(m.get('content') or '')))
out=[]
for i,line in enumerate(log.read_text(encoding='utf-8',errors='replace').splitlines(),1):
 for match in re.finditer(r'(?i)(NATIVE_PIPE FATAL|CUDA error|CUDA_ERROR|fatal error|MISMATCH)',line):
  context=line[max(0,match.start()-20):min(len(line),match.end()+20)]
  out.append({'line':i,'term':match.group(),'context_present_in_response':any(context in t for _,t in responses),
   'response_files_with_same_context':[p for p,t in responses if context in t],
   'line_starts_strata_diagnostic':line.startswith(('strata:','strata ')),
   'specific_kernel_error':bool(re.search(r'(?i)(NATIVE_PIPE FATAL|CUDA error|CUDA_ERROR|fatal error|NATIVE_PIPE_CHECK MISMATCH)',line))})
print(json.dumps(out,indent=2))
(R/'guard-diagnosis.json').write_text(json.dumps(out,indent=2))
