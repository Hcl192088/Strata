import difflib,hashlib,json,subprocess,sys
from pathlib import Path
import controller_roles as c
R=Path(r'C:\Users\User\Strata-Adrian-control')
assert c.os.environ['COMPUTERNAME']=='DESKTOP-LKMLUPC'
vf=c.final_verify()
allowed={p for _,p,_ in c.ns.api_pids()}|set(c.ns.watch_pids())
procs=c.ns.processes();assert not [p for p in procs if p['pid'] not in allowed]
state=json.loads((c.ROOT/'campaign.json').read_text());assert state['phase']=='FAILED' and state['verified']
assert not c.psutil.pid_exists(state['controller_pid'])
def git(*a):return subprocess.check_output(['git','-C',str(R),*a])
assert git('rev-parse','HEAD').decode().strip()=='6251a722f9c98fbfde3465cb5f4639de589a008b'
assert not git('diff','--cached','--name-only').strip(),'unrelated staged files'
out=R/'bench/experiments/overnight-20261029';assert not out.exists();out.mkdir(parents=True)
base='61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406'
paths=['src/kernels/cpu/pool.cpp','include/strata/kernels/cpu/pool.hpp','src/program/generate.cpp','src/core/expert_source.cpp','include/strata/core/expert_source.hpp','include/strata/core/cpu_phase_diag.hpp']
manifest={'promoted':False,'base_commit':base,'source_scope':'six explicitly modified files; not a full source or dependency audit','variants':{},'live':vf}
S=R/'runs/overnight-20261029/source'
for arm,root in [('generic',R/'runs/native-pipeline-20261029'),('roles',c.ROOT)]:
    patch=[];ident={}
    for rel in paths:
        p=S/rel
        if 'pool.' in p.name:p=root/'patched'/p.name
        b=p.read_bytes();ident[rel]=hashlib.sha256(b).hexdigest().upper()
        old=subprocess.run(['git','-C',str(R),'show',base+':'+rel],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        assert old.returncode==0 or rel.endswith('cpu_phase_diag.hpp')
        a=old.stdout.decode().replace('\r\n','\n').splitlines(True);z=b.decode().replace('\r\n','\n').splitlines(True)
        patch.extend(difflib.unified_diff(a,z,fromfile='a/'+rel if old.returncode==0 else '/dev/null',tofile='b/'+rel))
    (out/(arm+'.patch')).write_text(''.join(patch),encoding='utf-8',newline='\n')
    manifest['variants'][arm]={'files_sha256':ident,'binary_sha256':c.ns.sha(root/'build/strata.exe'),'raw_path':str(root)}
for name in ['comparison.json','audit.json','final_verify.json']:
    (out/('generic-'+name)).write_bytes((R/'runs/native-pipeline-20261029'/name).read_bytes())
(out/'roles-campaign.json').write_bytes((c.ROOT/'campaign.json').read_bytes())
(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
h=R/'.codex/handoffs/2026-10-29-overnight.md';assert not h.exists();h.parent.mkdir(parents=True,exist_ok=True)
h.write_bytes((c.ROOT/'OVERNIGHT_RESULTS_20261029.md').read_bytes())
(out/'RESULT.md').write_bytes(h.read_bytes())
c.write('closing-verify.json',dict(verified=vf,processes=procs))
print(json.dumps({'saved':str(out),'handoff':str(h),'live_pid':vf['pid']}))
