import json,hashlib,re
from pathlib import Path
R=Path(__file__).resolve().parent;raw=R/'raw'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
manifest=read(raw/'raw-manifest.json')
for f in manifest:
 p=raw/f['path'];assert p.stat().st_size==f['bytes'];assert hashlib.sha256(p.read_bytes()).hexdigest().upper()==f['sha256']
audit=read(raw/'config-audit.json');base=next(x['config'] for x in audit if x['arm']=='C');keys=['STRATA_'+x for x in ['DF_QB_Q4','DF_BRANCH','GDN_SPLIT','LFUSE','QFUSE','TSUM','MMVF_ROWS','ATTN_LANECELL']];result=[]
for d in sorted((raw/'out').iterdir()):
 c=read(d/'config.json');m=read(d/'meta.json');text=(d/'engine.log').read_text(encoding='utf-8');a=m['arm']
 expected=json.loads(json.dumps(base));expected['log']=c['log'];expected['cwd']=c['cwd']
 if a!='C':expected['env'].update({k:'1' for k in keys})
 assert c==expected and m['status']=='OK' and m['priority_gate']['priority']==32768
 assert m['startup']['capacity_ok'] and m['startup']['slots']=='3153' and m['startup']['locked_mib']=='20479' and m['startup']['ram_budget_gib']=='20.00'
 assert '--spec-split' not in m['engine_cmdline'] and 'NATIVE_PIPE ACTIVE' in text
 assert not re.search(r'(?i)(NATIVE_PIPE FATAL|CUDA error|CUDA_ERROR|fatal error)',text)
 assert 'STRATA_NATIVE_PIPE_CHECK' not in c['env']
 for k in keys:assert m['effective_env'].get(k)==('1' if a!='C' else None)
 assert m['effective_env']['STRATA_NATIVE_PIPE']=='1' and m['effective_env']['STRATA_IQ3S_MT1']=='1'
 result.append(dict(block=d.name,rows=m['rows'],capacity=True,priority=True,config_diff_allowed=True,effective_env=True,pipe=True,log_switch_lines=[l for l in text.splitlines() if any(k in l for k in keys)]))
rows=read(R/'rows.json');n=len({r['round'] for r in rows});assert len(rows)==20*n
ex=read(raw/'exactness.json');assert len(ex['pairs'])==10*n
assert read(raw/'final_verify.json')['verified'] and read(raw/'independent_verify.json')['verified']
q=dict(manifest_files_verified=len(manifest),blocks=result,formal_rows=len(rows),exact_pairs=len(ex['pairs']),identical_pairs=sum(x['identical'] for x in ex['pairs']))
(R/'qa.json').write_text(json.dumps(q,indent=2),encoding='utf-8');print(json.dumps(q,indent=2))
