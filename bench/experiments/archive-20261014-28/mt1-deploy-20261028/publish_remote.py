"""Commit only the verified deployment manifest/handoff/launcher; preserve other work."""
import hashlib
import json
import runpy
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = Path(r'C:\Users\User\Strata-Adrian-control')
TARGET = REPO / 'bench/results/2026-10-28-s2k-mt1'
REPORT = REPO / '.codex/handoffs/2026-10-28-s2k-mt1-deployed.md'
SRC = REPO / 'runs/miss-overlap-20261027/source'
BASE = '61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406'
TAG = 'best-s2k-mt1-20261028'
SOURCE_TAG = 's2k-mt1-source-base-20261028'

def git(*args, cwd=REPO):
    return subprocess.run(['git', '-C', str(cwd), *args], check=True, capture_output=True)

def txt(*args, cwd=REPO):
    return git(*args, cwd=cwd).stdout.decode('utf-8').strip()

def sha(b):
    return hashlib.sha256(b).hexdigest().upper()

assert txt('branch', '--show-current') == 'main'
assert txt('rev-parse', 'HEAD') == 'e42e96ce1f2368835f466ebb67fd3189719b5dc3'
assert txt('rev-parse', 'HEAD', cwd=SRC) == BASE
assert not TARGET.exists() and not REPORT.exists(), 'publication targets already exist'
assert not txt('tag', '--list', TAG) and not txt('tag', '--list', SOURCE_TAG), 'tag already exists'
# Fresh read-only runtime/process gate in this process (ancestors are excluded).
runpy.run_path(str(HERE / 'verify_deployed.py'), run_name='__audit__')
manifest = json.loads((HERE / 'BEST.json').read_text(encoding='utf-8'))
manifest['deployment_tag'] = TAG
manifest['source']['base_annotated_tag'] = SOURCE_TAG
manifest['source']['source_repo'] = 'Hcl192088/Strata'
dirty = txt('diff', '--name-only', 'HEAD', cwd=SRC).splitlines()
expected = ['include/strata/core/expert_source.hpp', 'src/core/expert_source.cpp']
assert sorted(dirty) == expected, 'unexpected build-source modifications'
patch = git('diff', '--binary', 'HEAD', '--', *expected, cwd=SRC).stdout
assert patch
manifest['source']['patch_path'] = 'bench/results/2026-10-28-s2k-mt1/source.patch'
manifest['source']['patch_sha256'] = sha(patch)
manifest['source']['base_tag_scope'] = 'Tag pins source BASE; apply recorded source.patch for the dirty build tree. This is not a rebuilt binary certification.'
manifest['performance_evidence']['report_sha256'] = sha((HERE / 'MT1_DEPLOYMENT_20261028.md').read_bytes())
TARGET.mkdir(parents=True)
(TARGET / 'source.patch').write_bytes(patch)
for dst, source in [
    ('server-task020-8080-v0142-s2k-mt1.json', Path(manifest['config_path'])),
    ('rollback-s2k.config.json', HERE / 'out/s2k-config.before.json'),
    ('rollback-s2k.launcher.ps1', HERE / 'out/s2k-launcher.before.ps1'),
]:
    (TARGET / dst).write_bytes(source.read_bytes())
assert sha((TARGET / 'server-task020-8080-v0142-s2k-mt1.json').read_bytes()) == manifest['config_sha256']
manifest['rollback']['versioned_config'] = 'bench/results/2026-10-28-s2k-mt1/rollback-s2k.config.json'
manifest['rollback']['versioned_launcher'] = 'bench/results/2026-10-28-s2k-mt1/rollback-s2k.launcher.ps1'
(TARGET / 'BEST.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
REPORT.write_bytes((HERE / 'MT1_DEPLOYMENT_20261028.md').read_bytes())
paths = ['bench/results/2026-10-28-s2k-mt1', '.codex/handoffs/2026-10-28-s2k-mt1-deployed.md', 'tools/start_task020_api_s2k_mt1.ps1']
git('add', '--', *paths)
git('diff', '--cached', '--check', '--', *paths)
git('commit', '--only', '-m', 'Record verified S2K MT1 deployment and current best', '--', *paths)
commit = txt('rev-parse', 'HEAD')
git('tag', '-a', SOURCE_TAG, BASE, '-m', 'S2K MT1 build source base; deployment manifest pins the additional source.patch and binary SHA.')
git('tag', '-a', TAG, commit, '-m', 'Verified S2K+MT1 deployment; config/environment identity and rollback preserved in BEST.json.')
result = dict(commit=commit, branch='main', deployment_tag=TAG, source_base_tag=SOURCE_TAG,
              source_patch_sha256=manifest['source']['patch_sha256'], push_status='NOT_ATTEMPTED')
receipt = HERE / 'out/publication.json'
receipt.write_text(json.dumps(result, indent=2), encoding='utf-8')
# One normal push; no credentials change, force, merge, retry, or fallback.
p = subprocess.run(['git', '-C', str(REPO), 'push', '--atomic', 'origin', 'HEAD:refs/heads/main',
                    'refs/tags/' + TAG, 'refs/tags/' + SOURCE_TAG], capture_output=True, text=True, timeout=60)
result.update(push_status='PUSHED' if p.returncode == 0 else 'FAILED', exit_code=p.returncode,
              stdout=p.stdout, stderr=p.stderr)
receipt.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result))
if p.returncode:
    sys.exit(p.returncode)
