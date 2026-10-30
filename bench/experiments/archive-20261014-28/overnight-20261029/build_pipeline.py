"""Incremental isolated build. Preserve best and prior diagnostic artifact."""
import hashlib,json,os,shutil,subprocess,time,traceback
from pathlib import Path
import psutil
ROOT=Path(__file__).resolve().parent
D=ROOT.parent/'overnight-20261029'
S=D/'source'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def main():
    assert os.environ.get('COMPUTERNAME')=='DESKTOP-LKMLUPC'
    assert time.time()<1793226600
    assert not (ROOT/'build-progress.json').exists(),'build already attempted'
    state=dict(status='START',pid=os.getpid(),created=psutil.Process().create_time())
    def save():
        t=ROOT/'build-progress.tmp';t.write_text(json.dumps(state,indent=2));t.replace(ROOT/'build-progress.json')
    save()
    actual=[]
    allowed={32084,27860,17028,23376,23300,25496,30620,os.getpid()}|{p.pid for p in psutil.Process().parents()}
    for p in psutil.process_iter(['pid','name','cmdline']):
        if (p.info['name'] or '').lower() in ('python.exe','strata.exe','cl.exe','link.exe','cmake.exe','nmake.exe','nvcc.exe','nsys.exe','wpr.exe'):
            actual.append(p.info);assert p.pid in allowed,('unclassified process',p.info)
    (ROOT/'build-process-gate.json').write_text(json.dumps(actual,indent=2))
    assert sha(ROOT.parent/'miss-overlap-20261027/build/strata.exe')=='385EF64EE24BDF3BD4B309264FA811901DF9256B92CE4589BAEC70B3F26B30F5'
    assert sha(D/'build/strata.exe')=='C7F41DF334092A3CA245D7E0BE92D27A06E5FB34D5923AD78C64A841FAD3FA54'
    restore_source=ROOT.parent/'unmapped-shadow-20261029/before-shadow-expert_source.cpp'
    assert sha(restore_source)=='2294D6B8F007A3D238EE0D68CAA77B888A4491682156B796C869EC07E6163658'
    expected={'src/kernels/cpu/pool.cpp':'4A7AE645E2D494F465772397724EE3290130F1A9CBD56E6D653939D5AF03650A',
        'include/strata/kernels/cpu/pool.hpp':'4255FD01AE6E55A650B2E81316202C5B9206E0AE2271CD9FA81EDC3B27D33C1A',
        'src/program/generate.cpp':'27CCC961B633A13D4B0E359E9505A5CBF3DDC6AB32B4C82B9FDD9084DBA40F5F'}
    identity=json.loads((ROOT/'patched/identity.json').read_text())
    before=ROOT/'before';before.mkdir()
    for rel,original in expected.items():
        p=S/rel;assert sha(p)==original,(rel,'source identity changed')
        patched=ROOT/'patched'/p.name;assert sha(patched)==identity[p.name]
        shutil.copyfile(p,before/p.name);shutil.copyfile(patched,p)
    # Remove only our rejected shadow experiment from this isolated source, restoring diagnostic base.
    assert sha(S/'src/core/expert_source.cpp')=='F14DE745C390B78D927A71CA8DEB3863324F5776FEACB9CB362F674F4EAA56BD'
    shutil.copyfile(restore_source,S/'src/core/expert_source.cpp')
    shutil.copyfile(D/'build/strata.exe',ROOT/'diag-C7F41DF3.exe')
    try:
        with (ROOT/'build.log').open('w') as out:
            p=subprocess.Popen(['cmd.exe','/c',str(ROOT.parent/'unmapped-shadow-20261029/build-shadow.cmd')],stdout=out,stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
            state.update(status='BUILD',build_pid=p.pid,build_created=psutil.Process(p.pid).create_time(),source_sha256=identity);save()
            try:code=p.wait(timeout=1800)
            except subprocess.TimeoutExpired:
                for own in psutil.Process(p.pid).children(recursive=True):
                    try:own.terminate()
                    except psutil.NoSuchProcess:pass
                p.terminate();raise
        assert code==0,('BUILD_FAILED',code)
        (ROOT/'build').mkdir();shutil.copyfile(D/'build/strata.exe',ROOT/'build/strata.exe')
        state.update(status='DONE',exit_code=code,binary_sha256=sha(ROOT/'build/strata.exe'));save()
    except BaseException:
        state.update(status='FAILED',error=traceback.format_exc());save();raise
    finally:shutil.copyfile(ROOT/'diag-C7F41DF3.exe',D/'build/strata.exe')
    print(json.dumps(state,indent=2))
if __name__=='__main__':main()
