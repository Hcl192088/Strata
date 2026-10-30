import json,shutil
from pathlib import Path
R=Path(r'C:\Users\User\Strata-Adrian-control');N=R/'runs/native-pipe-deploy-prep-20261029';O=R/'runs/native-pipeline-20261029';W=Path(json.loads((N/'source-pin.json').read_text())['worktree'])
assert not (N/'controller_prep.py').exists()
shutil.copytree(O/'harness',N/'harness')
s=(O/'controller_pipeline.py').read_text();s=s[:s.index('def main():')]
s=s.replace("assert time.time()<CUTOFF-900 and not ABORT.is_set(),'deadline margin exhausted'","assert not ABORT.is_set()")
s=s.replace("assert checks and max(int(x[0]) for x in checks)>=100 and max(int(x[1]) for x in checks)>=100000","assert checks")
s+='''def main():
    import subprocess
    ctypes.windll.kernel32.SetErrorMode(0x8003)
    assert os.environ['COMPUTERNAME']=='DESKTOP-LKMLUPC'
    assert not (ROOT/'campaign.json').exists()
    STATE.update(task_id='LUNA-20261012-027',authorization='user 準備部署 pipeline NATIVE_PIPE_DEPLOY_PREP',controller_pid=os.getpid(),completed=[])
    ns.log.path=ROOT/'controller.log';save(phase='BUILD_PREFLIGHT')
    stopped=False;error=None
    try:
        allowed={p for _,p,_ in ns.api_pids()}|set(ns.watch_pids())
        inv=ns.processes();write('processes-build.json',inv)
        assert not [p for p in inv if p['pid'] not in allowed]
        write('pre-build-live.json',final_verify())
        assert ns.sha(ROOT.parent/'native-pipeline-20261029/build/strata.exe')==EXE_SHA
        save(phase='BUILD')
        with (ROOT/'build.log').open('w') as log:
            code=subprocess.call(['cmd.exe','/c',str(ROOT/'build.cmd')],stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
        write('build-result.json',dict(exit_code=code,binary_sha256=ns.sha(EXE) if EXE.exists() else None,original_binary_sha256=EXE_SHA))
        assert code==0,('build failed',code)
        global EXE_SHA
        EXE_SHA=ns.sha(EXE)
        identity()
        inv=ns.processes();write('processes-pre-stop.json',inv)
        allowed={p for _,p,_ in ns.api_pids()}|set(ns.watch_pids())
        assert not [p for p in inv if p['pid'] not in allowed]
        write('pre-stop-live.json',final_verify())
        OUT.mkdir();stopped=True;ns.stop_api(ROOT);gate()
        run(0,0,'SMOKE',['p01','p05','p08'],128)
        run(1,0,'CHK',None,128)
        save(phase='CHECK_COMPLETE')
    except BaseException:
        error=traceback.format_exc();save(phase='ERROR',error=error)
    finally:
        if stopped:
            save(before_restore_phase=STATE.get('phase'),phase='RESTORE')
            restore=ns.restore_api(ROOT)
        else:restore=dict(restored=False,reason='API not stopped')
        try:vf=final_verify()
        except BaseException:vf=dict(verified=False,error=traceback.format_exc())
        write('final_verify.json',vf)
        save(phase='DONE' if error is None and vf['verified'] else 'FAILED',restored=restore.get('restored'),verified=vf['verified'])
if __name__=='__main__':main()
'''
s=s.replace('def main():\n    import subprocess','def main():\n    global EXE_SHA\n    import subprocess').replace('        global EXE_SHA\n','')
(N/'controller_prep.py').write_text(s)
compile(s,'controller_prep.py','exec')
cmd=(R/'runs/overnight-20261029/build.cmd').read_text()
cmd=cmd.replace(str((R/'runs/overnight-20261029/source').resolve()),str(W)).replace(str((R/'runs/overnight-20261029/build').resolve()),str(N/'build'))
assert 'overnight-20261029' not in cmd
cmd=cmd.replace('cmake -S','cl 2> "'+str(N/'compiler-version.log')+'"\nnvcc --version > "'+str(N/'cuda-version.log')+'"\ncmake --version > "'+str(N/'cmake-version.log')+'"\ncmake -S')
(N/'build.cmd').write_text(cmd)
print(cmd)
