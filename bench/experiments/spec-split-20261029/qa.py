from pathlib import Path
import json,hashlib,re
R=Path('state/spec-split-20261029');raw=R/'raw'
manifest=json.loads((raw/'raw-manifest.json').read_text())
for f in manifest:
 p=raw/f['path'];assert p.stat().st_size==f['bytes'];assert hashlib.sha256(p.read_bytes()).hexdigest().upper()==f['sha256']
audit=json.loads((raw/'config-audit.json').read_text());base=next(x['config'] for x in audit if x['arm']=='C');result=[]
for d in sorted((raw/'out').iterdir()):
 c=json.loads((d/'config.json').read_text());meta=json.loads((d/'meta.json').read_text());text=(d/'engine.log').read_text(encoding='utf-8');cmd=json.loads((d/'command.json').read_text());a=meta['arm']
 expected=json.loads(json.dumps(base));expected['log']=c['log'];expected['cwd']=c['cwd']
 if a!='C':expected['args'].append('--spec-split')
 if a in ['SMOKE','CHK']:expected['env']['STRATA_NATIVE_PIPE_CHECK']='1'
 assert expected==c
 assert meta['status']=='OK' and meta['priority_gate']['priority']==32768
 assert meta['startup']['capacity_ok'] and meta['startup']['slots']=='3153' and meta['startup']['locked_mib']=='20479' and meta['startup']['ram_budget_gib']=='20.00'
 assert ('--spec-split' in meta['engine_cmdline'])==(a!='C')
 assert 'NATIVE_PIPE ACTIVE' in text and 'NATIVE_PIPE FATAL' not in text and 'NATIVE_PIPE_CHECK MISMATCH' not in text
 mismatches=[int(x) for x in re.findall(r'NATIVE_PIPE_CHECK[^\n]*mismatch=(\d+)',text)];assert all(x==0 for x in mismatches)
 result.append(dict(block=d.name,rows=meta['rows'],capacity=True,priority=True,config_diff_allowed=True,pipe=True,nonzero_check_mismatches=sum(x!=0 for x in mismatches),graph_node_lines=len(re.findall('window graph has',text))))
ex=json.loads((raw/'exactness.json').read_text(encoding='utf-8'))
assert len(ex['pairs'])==50
q=dict(manifest_files_verified=len(manifest),blocks=result,formal_rows=len(json.loads((R/'rows.json').read_text())),exact_pairs=len(ex['pairs']),identical_pairs=sum(x['identical'] for x in ex['pairs']))
(R/'qa.json').write_text(json.dumps(q,indent=2))
print(json.dumps(q,indent=2));print(json.dumps(ex['pairs'][:3],ensure_ascii=False,indent=2))
