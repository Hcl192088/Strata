"""Task027 continuation: bounded diagnostic build, 3 on/off pairs, API restore."""
import importlib.util, json, os, re, subprocess, sys, time
from pathlib import Path
import psutil
TOOLS=Path(__file__).parent
spec=importlib.util.spec_from_file_location('base',TOOLS/'run_task027_ram_lru.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
ROOT=TOOLS.parent/'runs/decode-segments-20261015'
SOURCE=TOOLS.parent/'runs/ram-lru-20261013/source'
EXE=Path(b.CFG['exe']); BUILD=EXE.parent
SHA='366A355E0E866B12D1793C9D8BE022925305B4560E1AE7DC47F8716C865015E2'

def build():
    assert not b.processes(),b.processes()
    original=SOURCE/'src/program/generate.cpp'
    assert b.sha(original)=='23B3FBA82C48756A4546F970CA97A7949218BAA482C12CFE4CC528FD6D975553'
    cpp=ROOT/'segments.cpp';cpp.write_bytes(original.read_bytes())
    subprocess.run([sys.executable,str(TOOLS/'prepare_decode_segments.py'),str(cpp)],check=True)
    flags=(BUILD/'CMakeFiles/strata.dir/flags.make').read_text(encoding='utf-8-sig')
    vals=[re.search('^'+k+' = (.*)$',flags,re.M)[1] for k in ('CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS')]
    obj=ROOT/'segments.obj';exe=ROOT/'strata-segments.exe'
    rsp=ROOT/'compile.rsp';rsp.write_text(' '.join(vals)+f' /nologo /c "{cpp}" /Fo"{obj}" /Fd"{ROOT / "compile.pdb"}"')
    make=(BUILD/'CMakeFiles/strata.dir/build.make').read_text(encoding='utf-8-sig')
    link=re.search(r'^ /out:strata.exe .*$',make,re.M)[0]
    link=link.replace('/out:strata.exe',f'/out:"{exe}"').replace('/implib:strata.lib',f'/implib:"{ROOT / "segments.lib"}"')
    link=re.sub(r'/pdb:\S+',f'/pdb:"{(ROOT / "segments.pdb").as_posix()}"',link)
    lrsp=ROOT/'link.rsp';lrsp.write_text(f'"{obj}" '+link)
    cmd=ROOT/'build.cmd';cmd.write_text('@echo off\ncall "C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\BuildTools\\Common7\\Tools\\VsDevCmd.bat" -arch=x64\nif errorlevel 1 exit /b %errorlevel%\n'+f'cd /d "{BUILD}"\ncl @"{rsp}"\nif errorlevel 1 exit /b %errorlevel%\nlink @"{lrsp}"\nexit /b %errorlevel%\n')
    with (ROOT/'build.log').open('w') as f:
        subprocess.run(['cmd','/c',str(cmd)],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=300)
    assert b.sha(EXE)==SHA and b.sha(original)==b.sha(cpp.with_name('segments.cpp.before-segments'))
    print('BUILD_OK '+b.sha(exe),flush=True)
    return exe

def validate(name,enabled):
    d=ROOT/name;raw=(d/'stderr.log').read_text(encoding='utf-8')
    records=[json.loads(x.split('strata segment: ',1)[1]) for x in raw.splitlines() if x.startswith('strata segment: ')]
    tokens=json.loads((d/'tokens.json').read_text())
    assert len(tokens)==1024
    if not enabled:
        assert not records
        return
    ids=[];end=0;windows=offered=accepted=0
    for r in records:
        assert r['start']==end and r['end']>end
        count=r['end']-end;assert count==len(r['output_ids'])==sum(x['tokens'] for x in r['bins'])
        ids+=r['output_ids'];end=r['end']
        for x in r['bins']:
            assert x['suffix_accepted']<=x['suffix_offered'] and x['mtp_accepted']<=x['mtp_offered']
            assert 0<=x['hits']<=x['lookups']
            assert all(x[k]>=0 for k in ('window_ms','pool_ms','jobs_ms','cpu_pool_lru_ms','file_thread_ms','gpu_wait_ms'))
            windows+=x['windows'];offered+=x['suffix_offered']+x['mtp_offered'];accepted+=x['suffix_accepted']+x['mtp_accepted']
    assert end==1024 and ids==tokens
    summary=re.search(r'strata decode timing: (\d+) windows',raw);assert summary and windows==int(summary[1])
    done=re.search(r'drafts accepted (\d+) of (\d+)',raw);assert done and (accepted,offered)==tuple(map(int,done.groups()))
    (d/'segments.json').write_text(json.dumps(records,indent=2))
    print('TELEMETRY_VALIDATED '+name,flush=True)

def main():
    assert b.sha(EXE)==SHA
    assert b.sha(b.PROMPT)=='9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA'
    ROOT.mkdir(exist_ok=False);b.ROOT=ROOT
    cfgfile=b.BASE/'server-task020-8080-v0142.json';cfgsha=b.sha(cfgfile)
    original_env=dict(b.CFG['env']);assert original_env['STRATA_RAM_LRU']=='1'
    # Wait for the live request; never stop a busy API.
    deadline=time.monotonic()+900
    while b.health('/metrics')['live']['state']!='idle':
        assert time.monotonic()<deadline,'API remained busy; no pause performed'
        print('WAITING_API_IDLE',flush=True);time.sleep(10)
    live=b.processes();assert len([p for p in live if p['name'].lower()=='strata.exe'])==1
    assert all('iq3-campaign-020' in ' '.join(p['cmdline'] or []) or str(EXE) in ' '.join(p['cmdline'] or []) for p in live),live
    (ROOT/'identity.json').write_text(json.dumps(dict(task='LUNA-20261012-027 continuation',authorization='2026-10-15 user agreed pause/instrumentation build/first paired tests/restore',baseline_sha=SHA,config_sha=cfgsha,source_sha=b.sha(SOURCE/'src/program/generate.cpp'),processes=live),indent=2))
    paused=False;results=[]
    try:
        assert b.health('/metrics')['live']['state']=='idle'
        paused=True;b.ps('Stop-ScheduledTask -TaskName Strata-Task020-API')
        for item in reversed(live):
            if psutil.pid_exists(item['pid']):
                p=psutil.Process(item['pid']);assert 'iq3-campaign-020' in ' '.join(p.cmdline()) or str(EXE) in ' '.join(p.cmdline());p.terminate()
        time.sleep(2);assert not b.processes(),b.processes()
        diag=build()
        for name,exe,on in [('original',EXE,False),('off-01',diag,False),('on-01',diag,True),('on-02',diag,True),('off-02',diag,False),('off-03',diag,False),('on-03',diag,True)]:
            assert b.sha(EXE)==SHA and not b.processes()
            b.CFG['env']={**original_env,'STRATA_ROUTE_TAIL_SKIP':'7','STRATA_DECODE_SEGMENTS':'1' if on else '0'}
            r=b.run(name,exe,True)
            validate(name,on)
            raw=(ROOT/name/'stderr.log').read_text(encoding='utf-8')
            ram=re.search(r'RAM budget ([\d.]+) GiB',raw);slots=re.search(r'expert cache (\d+) slots',raw)
            assert ram and float(ram[1])==20.0,'ENV_BLOCKED: resident is not20GiB'
            capacity=(int(slots[1]),float(ram[1]))
            if results:assert capacity==tuple(results[0]['capacity']),'ENV_BLOCKED: cache capacity changed'
            r['capacity']=capacity;r['telemetry']=on;r['diagnostic_only']=True
            results.append(r);(ROOT/'results.json').write_text(json.dumps(results,indent=2))
    finally:
        assert b.sha(EXE)==SHA and b.sha(cfgfile)==cfgsha
        if paused:
            assert not b.processes(),b.processes()
            b.ps('Start-ScheduledTask -TaskName Strata-Task020-API')
            for _ in range(90):
                try:
                    if b.health('/health').get('loaded'):
                        print('API_RESTORED loaded=true ORIGINAL_BINARY_UNCHANGED',flush=True);break
                except (OSError,ValueError):pass
                time.sleep(2)
            else:raise RuntimeError('API restore timeout')

if __name__=='__main__':main()
