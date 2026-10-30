from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parent
H=R/'roles-harness';H.mkdir(exist_ok=True)
shutil.copyfile(R/'pipeline-harness/next_steps_ab_20261018.py',H/'next_steps_ab_20261018.py')
h=(R/'pipeline-harness/replay_ab_20261027.py').read_text()
needle="            assert effective.get('STRATA_NATIVE_PIPE_CHECK') == (spec.get('env') or {}).get('STRATA_NATIVE_PIPE_CHECK')"
assert h.count(needle)==1
h=h.replace(needle,needle+"\n            assert effective.get('STRATA_NATIVE_PIPE_ROLES') == (spec.get('env') or {}).get('STRATA_NATIVE_PIPE_ROLES')")
(H/'replay_ab_20261027.py').write_text(h)
t=(R/'controller_pipeline.py').read_text()
build=json.loads((R/'roles-build-progress.json').read_text());assert build['status']=='DONE'
t=t.replace('3F98913EDB0B01D5D5DD3282412725141C298BF5CC9E890DD286AA0720C27230',build['binary_sha256'])
# Exact quoted arm names and result keys; preserve ordinary Python identifiers.
for old,new in [('PD','RD'),('OD','GD'),('P','R'),('O','G')]:t=t.replace("'"+old+"'","'"+new+"'")
t=t.replace("'P_vs_O'","'R_vs_G'")
t=t.replace("('R','RD','CHK','SMOKE')","('G','GD','R','RD','CHK','SMOKE')")
t=t.replace("    env={'STRATA_NATIVE_PIPE':", "    env={'STRATA_NATIVE_PIPE_ROLES':'1' if arm in ('R','RD','CHK','SMOKE') else None,\n         'STRATA_NATIVE_PIPE':")
t=t.replace("'STRATA_NATIVE_PIPE_CHECK'))","'STRATA_NATIVE_PIPE_CHECK','STRATA_NATIVE_PIPE_ROLES'))")
t=t.replace("time.time()<CUTOFF-900","time.time()<CUTOFF-240")
needle="    if arm in ('CHK','SMOKE'):\n        checks="
assert t.count(needle)==1
t=t.replace(needle,"    if arm in ('R','RD','CHK','SMOKE'):assert 'NATIVE_PIPE_ROLES ACTIVE' in text\n    else:assert 'NATIVE_PIPE_ROLES ACTIVE' not in text\n"+needle)
(R/'controller_roles.py').write_text(t)
(R/'wrap_roles.ps1').write_text((R/'wrap_pipeline.ps1').read_text().replace('controller_pipeline.py','controller_roles.py'))
compile(t,'controller_roles.py','exec');compile(h,'replay.py','exec')
print(build['binary_sha256'])
