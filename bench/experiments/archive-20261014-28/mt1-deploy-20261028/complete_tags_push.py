"""Pin the actual build-source base object, then publish the prepared deployment commit."""
import json
from pathlib import Path
import runpy
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = Path(r'C:\Users\User\Strata-Adrian-control')
SRC = REPO / 'runs/miss-overlap-20261027/source'
BASE = '61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406'
COMMIT = '6251a722f9c98fbfde3465cb5f4639de589a008b'
TAG = 'best-s2k-mt1-20261028'
SOURCE_TAG = 's2k-mt1-source-base-20261028'
def git(*args, cwd=REPO):
    p = subprocess.run(['git', '-C', str(cwd), *args], check=True, capture_output=True)
    return p.stdout.decode('utf-8').strip()
assert git('rev-parse', 'HEAD') == COMMIT
assert git('cat-file', '-t', BASE, cwd=SRC) == 'commit'
assert not git('tag', '--list', TAG) and not git('tag', '--list', SOURCE_TAG)
runpy.run_path(str(HERE / 'verify_deployed.py'), run_name='__audit__')
# The base exists in the actual detached build-source repository, not canonical main's object DB.
# Import that exact recorded object locally; no external source, clone, code or branch replacement.
git('fetch', '--no-tags', str(SRC), BASE)
assert git('cat-file', '-t', BASE) == 'commit'
git('tag', '-a', SOURCE_TAG, BASE, '-m', 'S2K MT1 source base. Deployment BEST.json pins source.patch and the deployed binary SHA; no rebuild certification.')
git('tag', '-a', TAG, COMMIT, '-m', 'Verified S2K+MT1 deployment: exact config, environment, source provenance and preserved S2K rollback.')
m = json.loads((REPO / 'bench/results/2026-10-28-s2k-mt1/BEST.json').read_text(encoding='utf-8'))
result = dict(commit=COMMIT, branch='main', deployment_tag=TAG, source_base_tag=SOURCE_TAG,
              source_patch_sha256=m['source']['patch_sha256'], push_status='NOT_ATTEMPTED',
              source_object_origin=str(SRC), source_object_import='exact BASE fetched from existing remote build-source repo into canonical repo; no branch changes',
              preparation_repairs=['Preserved exact-byte launcher/source patch archives; checked JSON/report whitespace separately.',
                                   'Source base object absent in canonical repository; verified and imported exact base from actual build-source repository.'])
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
