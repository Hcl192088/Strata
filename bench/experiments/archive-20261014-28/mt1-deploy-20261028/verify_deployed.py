"""Read-only deployed MT1 identity audit; no requests, stops, or fallback."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psutil

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'harness'))
import next_steps_ab_20261018 as ns

receipt = json.loads((ROOT / 'out' / 'deploy_receipt.json').read_text())
assert receipt.get('result') == 'DEPLOYED_MT1', 'deployment not complete'
assert receipt['verify_mt1']['verified'] and all(x['ok'] for x in receipt['smoke'])
cfgpath = Path(receipt['new_config']['path'])
cfg = json.loads(cfgpath.read_text(encoding='utf-8-sig'))
old = json.loads(ns.CONFIG.read_text(encoding='utf-8-sig'))
expected = dict(old)
expected['env'] = dict(old['env'], STRATA_IQ3S_MT1='1')
expected['log'] = cfg['log']
assert cfg == expected, 'unexpected config difference'
assert ns.sha(cfgpath) == receipt['new_config']['sha']
assert ns.sha(ns.CONFIG) == ns.CONFIG_SHA
assert ns.sha(ns.EXE_C) == ns.EXE_C_SHA
engines = []
parents = {p.pid for p in psutil.Process().parents()}
inventory = []
for p in psutil.process_iter(['pid', 'name', 'cmdline']):
    if p.pid == os.getpid() or p.pid in parents:
        continue
    n = (p.info['name'] or '').lower()
    if any(x in n for x in ('strata', 'llama', 'python', 'cmake', 'ninja', 'nvcc', 'msbuild', 'nsys', 'wpr')) or n in ('cl.exe', 'link.exe'):
        inventory.append(p.info)
    if n == 'strata.exe':
        env = p.environ()
        engines.append(dict(pid=p.pid, exe=p.exe(), sha256=ns.sha(p.exe()), command=p.cmdline(),
                            priority=str(p.nice()), created_at=p.create_time(),
                            env={k: env.get(k) for k in tuple(cfg['env']) + ('STRATA_IQ_MT_MIN',)}))
assert len(engines) == 1
e = engines[0]
assert e['sha256'] == ns.EXE_C_SHA and '--serve' in e['command']
assert e['env']['STRATA_IQ3S_MT1'] == '1' and not e['env']['STRATA_IQ_MT_MIN']
assert psutil.Process(e['pid']).nice() == psutil.ABOVE_NORMAL_PRIORITY_CLASS
assert all(e['env'].get(k) == v for k, v in cfg['env'].items())
bad = []
for p in inventory:
    cl = ' '.join(p['cmdline'] or []).lower()
    if p['pid'] == e['pid']:
        continue
    if p['name'].lower().startswith('python') and (
        (cfgpath.name.lower() in cl and ('serve.server' in cl or 'strata_memory_policy.py' in cl)) or
        ('strata_memory_policy.py' in cl and '--watch' in cl)):
        continue
    bad.append(p)
assert not bad, 'unclassified processes: %r' % bad
task = ns.ps("$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $t=Get-ScheduledTask -TaskName 'Strata-Task020-API'; [pscustomobject]@{name=$t.TaskName;state=[string]$t.State;execute=$t.Actions[0].Execute;arguments=$t.Actions[0].Arguments;priority=$t.Settings.Priority;xml=(Export-ScheduledTask -TaskName 'Strata-Task020-API')} | ConvertTo-Json -Compress", check=True)
t = json.loads(task.stdout)
assert t['state'] == 'Running' and t['priority'] == 2
assert t['arguments'].endswith(receipt['new_launcher']['path'])
health = ns.http_json('/health')
assert health['loaded']
metrics = ns.http_json('/metrics')
facts = ns.startup_facts(Path(cfg['log']).read_text(encoding='utf-8', errors='replace'))
assert facts['slots'] == '3153' and facts['ram_budget_gib'] == '20.00' and facts['locked_mib'] == '20479'
gitroot = ns.CONTROL_ROOT
def git(*args):
    return subprocess.run(['git', '-C', str(gitroot), *args], check=True, capture_output=True, text=True).stdout.strip()
src = gitroot / r'runs\miss-overlap-20261027\source'
sourcehead = subprocess.run(['git', '-C', str(src), 'rev-parse', 'HEAD'], check=True, capture_output=True, text=True).stdout.strip()
out = dict(verified=True, checked_at=time.strftime('%Y-%m-%dT%H:%M:%S%z'), hostname=os.environ['COMPUTERNAME'],
           config_path=str(cfgpath), config_sha256=ns.sha(cfgpath), config=cfg,
           launcher_path=receipt['new_launcher']['path'], launcher_sha256=ns.sha(receipt['new_launcher']['path']),
           engines=engines, inventory=inventory, task=t, health=health, live=metrics.get('live'),
           capacity={k: facts[k] for k in ('slots', 'ram_budget_gib', 'locked_mib')},
           canonical_source_head=git('rev-parse', 'HEAD'), branch=git('branch', '--show-current'),
           build_source_head=sourcehead, old_config_unchanged=ns.sha(ns.CONFIG) == ns.CONFIG_SHA,
           old_launcher_unchanged=ns.sha(gitroot / 'tools' / ns.LAUNCHER_NAME) == '50B9D745E980409E397FCBF18A94B87AC97B49F56DD12B5F4CA80A0AD60B42CB',
           available_ram_bytes=psutil.virtual_memory().available)
assert out['old_launcher_unchanged']
(ROOT / 'out' / 'final_state.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
print(json.dumps({k: out[k] for k in ('verified', 'checked_at', 'hostname', 'config_sha256', 'launcher_sha256', 'capacity', 'canonical_source_head', 'build_source_head', 'old_config_unchanged', 'old_launcher_unchanged')}))
