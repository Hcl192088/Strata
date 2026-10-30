from pathlib import Path
import subprocess,json,hashlib,sys,shutil
R=Path(__file__).resolve().parent;W=R/'source'
def git(*a):return subprocess.check_output(['git','-C',str(W),*a]).decode().strip()
assert git('branch','--show-current')=='pcie-balance-20261029'
assert git('rev-parse','HEAD')=='f520bc5e9d31c93caeb296b059e3a3eaa16e493f'
subprocess.run(['git','-C',str(W),'diff','--check'],check=True)
files=['docs/DETAILS.md','include/strata/core/expert_source.hpp','include/strata/core/verify.hpp','include/strata/kernels/verify_kernels.hpp','src/core/expert_source.cpp','src/core/verify.cpp','src/kernels/cuda/verify_kernels.cu','src/program/generate.cpp']
assert set(git('diff','--name-only').splitlines())==set(files)
subprocess.run(['git','-C',str(W),'add','--',*files],check=True)
subprocess.run(['git','-C',str(W),'commit','-m','Port opt-in PCIe balance onto native pipeline current best'],check=True)
subprocess.run(['git','-C',str(W),'tag','-a','pcie-balance-port-20261029','-m','PCIE_BALANCE_PORT isolated candidate; no deployment'],check=True)
(R/'ported.patch').write_bytes(subprocess.check_output(['git','-C',str(W),'diff','HEAD^','HEAD']))
sha=lambda p:hashlib.file_digest(open(p,'rb'),'sha256').hexdigest().upper()
d=dict(branch=git('branch','--show-current'),commit=git('rev-parse','HEAD'),tag='pcie-balance-port-20261029',base=git('rev-parse','HEAD^'),dirty=git('status','--short'),binary_sha256=sha(R/'build/strata.exe'),build_cmd_sha256=sha(R/'build.cmd'),upstream_patch_sha256=sha(R/'upstream.patch'),files={f:sha(W/f) for f in files})
(R/'identity.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
