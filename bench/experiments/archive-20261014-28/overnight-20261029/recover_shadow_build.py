"""Recover an artifact lost by PowerShell's missing ExitCode; no source/code change."""
import hashlib,json,os,subprocess,time
from pathlib import Path
import psutil

R=Path(r'C:\Users\User\Strata-Adrian-control\runs\unmapped-shadow-20261029')
D=R.parent/'overnight-20261029'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def main():
    assert os.environ['COMPUTERNAME']=='DESKTOP-LKMLUPC'
    assert not (R/'build-recovery.json').exists(),'recovery already attempted'
    assert json.loads((R/'build-progress.json').read_text(encoding='utf-8-sig'))['error']=='BUILD_FAILED exit='
    assert '[100%] Built target strata' in (R/'build.log').read_text(errors='replace')
    assert sha(D/'source/src/core/expert_source.cpp')=='F14DE745C390B78D927A71CA8DEB3863324F5776FEACB9CB362F674F4EAA56BD'
    assert sha(D/'build/strata.exe')==sha(R/'diag-C7F41DF3.exe')=='C7F41DF334092A3CA245D7E0BE92D27A06E5FB34D5923AD78C64A841FAD3FA54'
    assert sha(R.parent/'miss-overlap-20261027/build/strata.exe')=='385EF64EE24BDF3BD4B309264FA811901DF9256B92CE4589BAEC70B3F26B30F5'
    allowed={24860,25048,13308,24020,24912,28968,27736,os.getpid(),os.getppid()}
    for p in psutil.process_iter(['pid','name','cmdline']):
        if (p.info['name'] or '').lower() in ('python.exe','strata.exe','cl.exe','link.exe','cmake.exe','nmake.exe','nvcc.exe','nsys.exe','wpr.exe'):
            assert p.pid in allowed,('unclassified process',p.info)
    state=dict(status='START',reason='Build completed but PowerShell wrapper received null ExitCode and restored old diagnostic exe before artifact capture; force same source recompile to regenerate candidate.')
    def save():(R/'build-recovery.json').write_text(json.dumps(state,indent=2))
    save()
    try:
        (D/'source/src/core/expert_source.cpp').touch()
        with (R/'build-recovery.log').open('w') as out:
            p=subprocess.Popen(['cmd.exe','/c',str(R/'build-shadow.cmd')],stdout=out,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
            state.update(status='BUILD',pid=p.pid,created=psutil.Process(p.pid).create_time());save()
            try:code=p.wait(timeout=600)
            except subprocess.TimeoutExpired:
                for own in psutil.Process(p.pid).children(recursive=True):
                    try:own.terminate()
                    except psutil.NoSuchProcess:pass
                p.terminate();raise
        assert code==0,('BUILD_FAILED',code)
        import shutil
        shutil.copyfile(D/'build/strata.exe',R/'strata-shadow.exe')
        state.update(status='DONE',exit_code=code,binary_sha256=sha(R/'strata-shadow.exe'),source_sha256=sha(D/'source/src/core/expert_source.cpp'));save()
    except BaseException as e:
        state.update(status='FAILED',error=repr(e));save();raise
    finally:
        import shutil
        shutil.copyfile(R/'diag-C7F41DF3.exe',D/'build/strata.exe')
    print(json.dumps(state,indent=2))
if __name__=='__main__':main()
