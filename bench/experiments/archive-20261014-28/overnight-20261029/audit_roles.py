"""Bounded audit of all 19 completed blocks; private prompts/responses never printed."""
import hashlib,json,os,re,time
from pathlib import Path
import psutil
R=Path(__file__).resolve().parent
BEST='385EF64EE24BDF3BD4B309264FA811901DF9256B92CE4589BAEC70B3F26B30F5'
CAND='165059E7A5F528B80D5B029C487741AD652E0F0C38F4B6E112F99F4AAC61A110'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
s=json.loads((R/'campaign.json').read_text());assert s['phase']=='DONE' and s['verified'] and len(s['completed'])==19
assert not psutil.pid_exists(s['controller_pid']),'controller PID still exists; inspect creation before proceeding'
rows=json.loads((R/'rows.json').read_text());assert len(rows)==150
assert len({(r['arm'],r['round'],r['pid']) for r in rows})==150
assert all(not r.get('error') and not r.get('m_error') for r in rows)
baseline_args=None;baseline_env=None;meta_all=[];bytes_read=0;lines_read=0;checked_values=0;seen_pairs=set()
for block in s['completed']:
    d=Path(block['path']);meta=json.loads((d/'meta.json').read_text());cfg=json.loads((d/'config.json').read_text())
    arm=block['arm'];assert meta['status']=='OK' and meta['rows']==(3 if arm=='SMOKE' else 10)
    assert meta['binary_sha256']==(BEST if arm=='C' else CAND)
    assert meta['priority_gate']['priority']==psutil.ABOVE_NORMAL_PRIORITY_CLASS and meta['priority_gate']['before_first_request']
    f=meta['startup'];assert str(f['slots'])=='3153' and str(f['ram_budget_gib'])=='20.00' and str(f['locked_mib'])=='20479'
    env=cfg['env'];assert env.get('STRATA_IQ3S_MT1')=='1' and not env.get('STRATA_IQ_MT_MIN')
    assert env.get('STRATA_NATIVE_PIPE')==('1' if arm in ('G','GD','R','RD','CHK','SMOKE') else None)
    assert env.get('STRATA_NATIVE_PIPE_ROLES')==('1' if arm in ('R','RD','CHK','SMOKE') else None)
    assert env.get('STRATA_NATIVE_PIPE_CHECK')==('1' if arm in ('CHK','SMOKE') else None)
    assert env.get('STRATA_CPU_PHASE_DIAG')==('1' if arm in ('GD','RD','CHK','SMOKE') else None)
    common={k:v for k,v in env.items() if k not in ('STRATA_NATIVE_PIPE_ROLES','STRATA_NATIVE_PIPE','STRATA_NATIVE_PIPE_CHECK','STRATA_CPU_PHASE_DIAG')}
    if baseline_args is None:baseline_args=cfg['args'];baseline_env=common
    assert cfg['args']==baseline_args and common==baseline_env,'unexpected runtime difference'
    raw=(d/'engine.log').read_bytes();text=raw.decode('utf-8',errors='replace');bytes_read+=len(raw);lines_read+=len(text.splitlines())
    assert all(x not in text for x in ('NATIVE_PIPE FATAL','NATIVE_PIPE_CHECK MISMATCH','MISS_OVERLAP_CHECK MISMATCH'))
    if arm in ('CHK','SMOKE'):
        checks=re.findall(r'NATIVE_PIPE_CHECK batches=(\d+) values=(\d+) gu_type=(\d+) down_type=(\d+) mismatch=0',text)
        assert checks;checked_values+=max(int(x[1]) for x in checks);seen_pairs|={(int(x[2]),int(x[3])) for x in checks}
    meta_all.append(dict(block=block,meta=meta,engine_log_sha256=sha(d/'engine.log'),config_sha256=sha(d/'config.json')))
expected={tuple(x) for x in json.loads((R/'pipeline-format-identity.json').read_text())['expected_pairs']}
assert expected<=seen_pairs
vf=json.loads((R/'final_verify.json').read_text());assert vf['verified']
p=psutil.Process(vf['pid']);assert sha(Path(p.exe()))==BEST and p.nice()==psutil.ABOVE_NORMAL_PRIORITY_CLASS
env=p.environ();assert env.get('STRATA_IQ3S_MT1')=='1' and not any(env.get(k) for k in ('STRATA_NATIVE_PIPE_ROLES','STRATA_NATIVE_PIPE','STRATA_NATIVE_PIPE_CHECK','STRATA_CPU_PHASE_DIAG','STRATA_IQ_MT_MIN'))
req=R.parent/'overnight-20261020-inputs/requests'
inputs={p.name:dict(sha256=sha(p),bytes=p.stat().st_size,mtime=p.stat().st_mtime) for p in req.glob('*.json')}
assert len(inputs)==10 and all(x['mtime']<s['controller_created'] for x in inputs.values())
result=dict(verified=True,formal_requests=150,total_requests=183,blocks=19,engine_logs=19,engine_log_bytes=bytes_read,engine_log_lines=lines_read,
    checked_values_at_least=checked_values,expected_pairs=sorted(expected),observed_pairs=sorted(seen_pairs),priority_capacity_all_pass=True,
    common_args=baseline_args,common_env=baseline_env,inputs=inputs,restored_api_pid=p.pid,restored_binary_sha256=BEST,
    coverage='All 19 meta/config/full engine logs, all 150 formal row records; bounded diagnostic phase/format files checked by controller. Natural language responses/private prompts not read; no full source audit.',
    completed_meta=meta_all)
(R/'audit.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k not in ('completed_meta','inputs','common_args','common_env')},indent=2))
