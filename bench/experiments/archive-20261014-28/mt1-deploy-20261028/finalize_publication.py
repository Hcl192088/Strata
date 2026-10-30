"""Complete the prepared deployment commit; exact-byte archives are hash-checked."""
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = Path(r'C:\Users\User\Strata-Adrian-control')
TAG = 'best-s2k-mt1-20261028'
SOURCE_TAG = 's2k-mt1-source-base-20261028'
BASE = '61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406'
paths = ['bench/results/2026-10-28-s2k-mt1', '.codex/handoffs/2026-10-28-s2k-mt1-deployed.md', 'tools/start_task020_api_s2k_mt1.ps1']
def git(*args):
    p = subprocess.run(['git', '-C', str(REPO), *args], capture_output=True)
    if p.returncode:
        raise RuntimeError(p.stdout.decode('utf-8', errors='replace') + p.stderr.decode('utf-8', errors='replace'))
    return p.stdout.decode('utf-8').strip()
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()
assert git('branch', '--show-current') == 'main'
assert git('rev-parse', 'HEAD') == 'e42e96ce1f2368835f466ebb67fd3189719b5dc3'
assert not git('tag', '--list', TAG) and not git('tag', '--list', SOURCE_TAG)
runpy.run_path(str(HERE / 'verify_deployed.py'), run_name='__audit__')
d = REPO / paths[0]
m = json.loads((d / 'BEST.json').read_text(encoding='utf-8'))
assert sha(d / 'source.patch') == m['source']['patch_sha256']
assert sha(d / 'rollback-s2k.launcher.ps1') == m['previous_best']['launcher_sha256']
assert sha(d / 'rollback-s2k.config.json') == m['previous_best']['config_sha256']
assert sha(REPO / paths[2]) == m['launcher_sha256']
assert sha(d / 'server-task020-8080-v0142-s2k-mt1.json') == m['config_sha256']
# Source patch and original launcher bytes are archival evidence, not authored text changes.
git('diff', '--cached', '--check', '--', str(d / 'BEST.json'),
    str(d / 'server-task020-8080-v0142-s2k-mt1.json'), str(d / 'rollback-s2k.config.json'), paths[1])
staged = set(git('diff', '--cached', '--name-only').splitlines())
expected = {paths[1], paths[2]} | {paths[0] + '/' + f for f in ('BEST.json', 'source.patch', 'rollback-s2k.config.json', 'rollback-s2k.launcher.ps1', 'server-task020-8080-v0142-s2k-mt1.json')}
assert staged == expected, 'unexpected staged files: %r' % (staged - expected)
git('commit', '--only', '-m', 'Record verified S2K MT1 deployment and current best', '--', *paths)
commit = git('rev-parse', 'HEAD')
git('tag', '-a', SOURCE_TAG, BASE, '-m', 'S2K MT1 source base. Deployment BEST.json records the additional dirty source.patch and binary SHA.')
git('tag', '-a', TAG, commit, '-m', 'Verified S2K+MT1 deployment: config, environment, source patch and preserved S2K rollback.')
result = dict(commit=commit, branch='main', deployment_tag=TAG, source_base_tag=SOURCE_TAG,
              source_patch_sha256=m['source']['patch_sha256'], push_status='NOT_ATTEMPTED',
              whitespace_check='JSON/report checked; exact-byte launcher/source-patch archives verified by SHA instead of normalizing them')
receipt = HERE / 'out/publication.json'
receipt.write_text(json.dumps(result, indent=2), encoding='utf-8')
try:
    p = subprocess.run(['git', '-C', str(REPO), 'push', '--atomic', 'origin', 'HEAD:refs/heads/main',
                        'refs/tags/' + TAG, 'refs/tags/' + SOURCE_TAG], capture_output=True, text=True, timeout=60)
    result.update(push_status='PUSHED' if p.returncode == 0 else 'FAILED', exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr)
except subprocess.TimeoutExpired:
    result.update(push_status='UNCONFIRMED_TIMEOUT', exit_code=124)
receipt.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result))
if result['exit_code']:
    sys.exit(result['exit_code'])
