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
    allowed={7724,25008,15228,15964,32332,5604,26672,os.getpid()}|{p.pid for p in psutil.Process().parents()}
    for p in psutil.process_iter(['pid','name','cmdline']):
        if (p.info['name'] or '').lower() in ('python.exe','strata.exe','cl.exe','link.exe','cmake.exe','nmake.exe','nvcc.exe','nsys.exe','wpr.exe'):
            actual.append(p.info);assert p.pid in allowed,('unclassified process',p.info)
    (ROOT/'build-process-gate.json').write_text(json.dumps(actual,indent=2))
    assert sha(ROOT.parent/'miss-overlap-20261027/build/strata.exe')=='385EF64EE24BDF3BD4B309264FA811901DF9256B92CE4589BAEC70B3F26B30F5'
    assert sha(D/'build/strata.exe')=='C7F41DF334092A3CA245D7E0BE92D27A06E5FB34D5923AD78C64A841FAD3FA54'
    expected={'src/kernels/cpu/pool.cpp':'AF976BB39DE0A47F68B559FDF985677CA46B17D7D83D50F92307A94B194E9453',
        'include/strata/kernels/cpu/pool.hpp':'8B993048979A551B885313F85853C157FED1C13AA4DE5EBA1E9B15D284216351'}
    identity=json.loads((ROOT/'patched/identity.json').read_text())
    before=ROOT/'before';before.mkdir()
    for rel,original in expected.items():
        p=S/rel;assert sha(p)==original,(rel,'source identity changed')
        patched=ROOT/'patched'/p.name;assert sha(patched)==identity[p.name]
        shutil.copyfile(p,before/p.name);shutil.copyfile(patched,p)
    assert sha(S/'src/core/expert_source.cpp')=='2294D6B8F007A3D238EE0D68CAA77B888A4491682156B796C869EC07E6163658'
    assert sha(S/'src/program/generate.cpp')=='1F17C2E537DA102F4E4AA1D58F25C4DC083AEEA853369D979E23D5EB50E1B24B'
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
