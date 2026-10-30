import sys,json,subprocess,hashlib,os
from pathlib import Path
R=Path(r'C:\Users\User\Strata-Adrian-control')
ROOT=R/'runs/native-pipe-deploy-prep-20261029'
W=R.parent/'native-pipe-generic-20261029'
sys.path.insert(0,str(R/'runs/native-pipeline-po-confirm-20261029'))
import controller_confirm as c
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def git(*a):
 p=subprocess.run(['git','-C',str(R),*a],capture_output=True);assert p.returncode==0,p.stderr.decode();return p.stdout
assert os.environ['COMPUTERNAME']=='DESKTOP-LKMLUPC'
assert not ROOT.exists() and not W.exists()
ROOT.mkdir()
def save(n,x):(ROOT/n).write_text(json.dumps(x,indent=2))
save('initial_verify.json',c.final_verify())
ps=c.ns.processes();save('processes-source-pin.json',ps)
allowed={p for _,p,_ in c.ns.api_pids()}|set(c.ns.watch_pids())|{os.getpid()}
assert not [p for p in ps if p['pid'] not in allowed]
before=git('status','--porcelain=v1','--untracked-files=no');save('main-before.json',{'head':git('rev-parse','HEAD').decode().strip(),'status':before.decode(),'dirty_sha':{p:sha(R/p) for p in ['tools/run_mtp_depth_20261014.py','tools/run_task027_ram_lru.py']}})
patch=git('show','2f1e99872969c9b4586a2d41c7f1915f27e4f298:bench/experiments/overnight-20261029/generic.patch');(ROOT/'generic.patch').write_bytes(patch)
manifest=json.loads(git('show','2f1e99872969c9b4586a2d41c7f1915f27e4f298:bench/experiments/overnight-20261029/manifest.json'))
save('original-manifest.json',manifest)
git('worktree','add','-b','native-pipe-generic-20261029',str(W),manifest['base_commit'])
p=subprocess.run(['git','-C',str(W),'apply','--check',str(ROOT/'generic.patch')],capture_output=True);assert p.returncode==0,p.stderr.decode()
p=subprocess.run(['git','-C',str(W),'apply',str(ROOT/'generic.patch')],capture_output=True);assert p.returncode==0,p.stderr.decode()
checks={}
for rel,expected in manifest['variants']['generic']['files_sha256'].items():
 b=(W/rel).read_bytes();checks[rel]={'expected':expected,'actual':sha(W/rel),'bytes':len(b),'crlf':b.count(b'\r\n'),'lf':b.count(b'\n'),'matches':sha(W/rel)==expected}
save('source-comparison.json',checks)
assert all(v['matches'] for v in checks.values()),'SOURCE_HASH_MISMATCH: STOP'
rels=list(checks)
subprocess.run(['git','-C',str(W),'add','--',*rels],check=True)
msg='TASK LUNA-20261012-027: pin generic native pipeline source\n\n'+'\n'.join(k+' SHA256 '+v['actual'] for k,v in checks.items())
subprocess.run(['git','-C',str(W),'commit','-m',msg],check=True)
subprocess.run(['git','-C',str(W),'tag','-a','native-pipe-generic-20261029','-m',msg],check=True)
save('source-pin.json',{'worktree':str(W),'branch':'native-pipe-generic-20261029','commit':subprocess.check_output(['git','-C',str(W),'rev-parse','HEAD'],text=True).strip(),'tag':'native-pipe-generic-20261029'})
assert git('status','--porcelain=v1','--untracked-files=no')==before
print((ROOT/'source-pin.json').read_text())
