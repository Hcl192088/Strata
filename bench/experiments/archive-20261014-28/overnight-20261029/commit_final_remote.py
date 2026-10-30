import json,subprocess,shutil
from pathlib import Path
import controller_roles as c
R=Path(r'C:\Users\User\Strata-Adrian-control');out=R/'bench/experiments/overnight-20261029'
assert c.final_verify()['verified']
allowed={p for _,p,_ in c.ns.api_pids()}|set(c.ns.watch_pids())
assert not [p for p in c.ns.processes() if p['pid'] not in allowed]
def run(*args,**kw):return subprocess.run(['git','-C',str(R),*args],capture_output=True,text=True,**kw)
assert not run('diff','--cached','--name-only').stdout.strip()
for variant,root,controller in [('generic',R/'runs/native-pipeline-20261029','controller_pipeline.py'),('roles',c.ROOT,'controller_roles.py')]:
    d=out/variant;d.mkdir()
    for rel in [controller,'harness/replay_ab_20261027.py','harness/next_steps_ab_20261018.py']:
        p=root/rel;(d/p.name).write_bytes(p.read_bytes())
cmd=R/'runs/unmapped-shadow-20261029/build-shadow.cmd'
(out/'build-command.cmd').write_bytes(cmd.read_bytes())
add=run('add','--','.codex/handoffs/2026-10-29-overnight.md','bench/experiments/overnight-20261029');assert add.returncode==0,add.stderr
staged=run('diff','--cached','--name-only').stdout.splitlines()
assert staged and all(x.startswith('bench/experiments/overnight-20261029/') or x=='.codex/handoffs/2026-10-29-overnight.md' for x in staged)
commit=run('commit','-m','Record overnight CPU phase and native pipeline experiments; keep MT1 best')
assert commit.returncode==0,commit.stderr
sha=run('rev-parse','HEAD').stdout.strip()
receipt={'commit':sha,'branch':run('branch','--show-current').stdout.strip(),'files':staged,'commit_output':commit.stdout,'push_attempts':1}
try:
    push=run('push','origin','main',timeout=60)
    receipt.update(push_exit=push.returncode,push_stdout=push.stdout,push_stderr=push.stderr,pushed=push.returncode==0)
except subprocess.TimeoutExpired:
    receipt.update(push_exit=None,pushed=False,push_error='timeout after 60s; no retry')
receipt['remaining_tracked_dirty']=run('status','--short','--untracked-files=no').stdout
c.write('git-save-receipt.json',receipt)
print(json.dumps(receipt,indent=2))
