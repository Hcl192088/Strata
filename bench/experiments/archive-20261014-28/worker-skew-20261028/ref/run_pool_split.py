"""Task027 bounded pool/LRU decomposition; original API always restored."""
import importlib.util,json,re,subprocess,sys,time
from pathlib import Path
import psutil
TOOLS=Path(__file__).parent
spec=importlib.util.spec_from_file_location('segments_base',TOOLS/'run_decode_segments_20261015.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
b=p.b;CHECK='--check-anchors' in sys.argv
ROOT=TOOLS.parent/'runs'/('pool-split-20261015-prepare' if CHECK else 'pool-split-20261015-r3')
SOURCE=p.SOURCE;BUILD=p.BUILD;EXE=p.EXE;SHA=p.SHA
NAMES=['park_before_ms','dispatch_ms','host_drain_ms','completion_wait_ms','park_after_ms','native_gu_ms','native_quant_ms','native_down_ms','pool_call_ms','lru_total_ms','lru_memcpy_ms','lru_bytes','lru_admissions','phases','expert_jobs','unused']

def once(text,old,new):
    assert text.count(old)==1,(old[:100],text.count(old))
    return text.replace(old,new,1)

def build():
    if not CHECK:assert not b.processes(),b.processes()
    header=ROOT/'split_trace.hpp'
    header.write_text('''#pragma once
#include <array>
#include <chrono>
#include <cstdlib>
#include <cstring>
struct StrataSplitTrace {
    bool on=[] { const char* p=std::getenv("STRATA_POOL_SPLIT"); return p && std::strcmp(p,"1")==0; }();
    std::array<double,16> v{};
};
extern StrataSplitTrace strata_split_trace;
inline double strata_split_ms(auto a,auto b) { return std::chrono::duration<double,std::milli>(b-a).count(); }
''')
    include=f'#include "{header.as_posix()}"\n'
    paths={'pool':SOURCE/'src/kernels/cpu/pool.cpp','expert':SOURCE/'src/core/expert_source.cpp','generate':SOURCE/'src/program/generate.cpp'}
    expected={'pool':'4A7AE645E2D494F465772397724EE3290130F1A9CBD56E6D653939D5AF03650A','expert':'A44FCDAA21092DC3824A5F388EB6E9CFCDA03723408B019297555D5A69A180A6','generate':'23B3FBA82C48756A4546F970CA97A7949218BAA482C12CFE4CC528FD6D975553'}
    for k,f in paths.items():assert b.sha(f)==expected[k],k
    pool=paths['pool'].read_text(encoding='utf-8')
    start=pool.index('void ExpertPool::run_phase(int mode, int n_tasks) {');end=pool.index('\nvoid ExpertPool::run_split(',start)
    old=pool[start:end];body=old[old.index('{')+1:old.rfind('}')]
    new='''void ExpertPool::run_phase(int mode, int n_tasks) {
    if (!strata_split_trace.on) { BODY return; }
    using TraceClock=std::chrono::steady_clock;
    const auto a=TraceClock::now();
    wait_parked("before a phase");
    const auto b=TraceClock::now();
    mode_=mode; njobs_=n_tasks;
    const uint32_t e=begin_batch(n_tasks);
    const auto c=TraceClock::now();
    if (host_works_) drain(-1,host_scratch_,e);
    const auto d=TraceClock::now();
    wait_done(n_tasks);
    const auto f=TraceClock::now();
    wait_parked("after a phase");
    const auto g=TraceClock::now();
    hstate_.store(kIdle,std::memory_order_relaxed);
    hstate_ms_.store(now_ms(),std::memory_order_relaxed);
    auto& v=strata_split_trace.v;
    v[0]+=strata_split_ms(a,b);v[1]+=strata_split_ms(b,c);v[2]+=strata_split_ms(c,d);
    v[3]+=strata_split_ms(d,f);v[4]+=strata_split_ms(f,g);v[13]+=1;
}
'''.replace('BODY',body)
    pool=pool[:start]+new+pool[end:]
    anchor='        ms_multi_down += std::chrono::duration<double, std::milli>(d - c).count();'
    pool=once(pool,anchor,anchor+'''
        if (strata_split_trace.on) {
            auto& v=strata_split_trace.v;
            v[5]+=strata_split_ms(a,b);v[6]+=strata_split_ms(b,c);v[7]+=strata_split_ms(c,d);
        }
''')
    pool=include+'StrataSplitTrace strata_split_trace;\n'+pool
    expert=paths['expert'].read_text(encoding='utf-8')
    anchor='    if (njobs > 0) {\n        if (native) d.pool->run_split_multi_native'
    expert=once(expert,anchor,'    const auto split_pool_start = strata_split_trace.on ? std::chrono::steady_clock::now() : std::chrono::steady_clock::time_point{};\n'+anchor)
    anchor='        else d.pool->run_split_multi(d.jobs_multi.data(), njobs);\n    }\n    if (d.remote_count > 0) {'
    expert=once(expert,anchor,'''        else d.pool->run_split_multi(d.jobs_multi.data(), njobs);
    }
    if (strata_split_trace.on) {
        strata_split_trace.v[8]+=strata_split_ms(split_pool_start,std::chrono::steady_clock::now());
        strata_split_trace.v[14]+=njobs;
    }
    if (d.remote_count > 0) {
''')
    anchor='    if (auto* file_source = dynamic_cast<FileExpertSource*>(d.src))\n        file_source->ram_lru_complete(d.layers, ids, kind, n_tok * k, d.host_res, d.job_of.data(), d.jobs_multi.data());'
    expert=once(expert,anchor,'''    const auto split_lru_start = strata_split_trace.on ? std::chrono::steady_clock::now() : std::chrono::steady_clock::time_point{};
'''+anchor+'''
    if (strata_split_trace.on) strata_split_trace.v[9]+=strata_split_ms(split_lru_start,std::chrono::steady_clock::now());
''')
    anchor='        std::memcpy(destination, jobs[job].blob, (size_t)bytes);'
    expert=once(expert,anchor,'''        const auto split_copy_start = strata_split_trace.on ? std::chrono::steady_clock::now() : std::chrono::steady_clock::time_point{};
'''+anchor+'''
        if (strata_split_trace.on) {
            strata_split_trace.v[10]+=strata_split_ms(split_copy_start,std::chrono::steady_clock::now());
            strata_split_trace.v[11]+=(double)bytes;strata_split_trace.v[12]+=1;
        }
''')
    expert=include+expert
    cpp=ROOT/'generate.cpp';cpp.write_bytes(paths['generate'].read_bytes())
    subprocess.run([sys.executable,str(TOOLS/'prepare_decode_segments.py'),str(cpp)],check=True)
    gen=cpp.read_text(encoding='utf-8')
    gen=once(gen,'            struct SegBin {','            struct SegBin {\n                std::array<double,16> split{};')
    gen=once(gen,'                const DecSnap seg_before = seg_on ? dec_snap() : DecSnap{};','                const auto split_before=strata_split_trace.v;\n                const DecSnap seg_before = seg_on ? dec_snap() : DecSnap{};')
    gen=once(gen,'                    ++b.windows; b.tokens+=produced_n-seg_n0;','                    for(size_t j=0;j<16;++j) b.split[j]+=strata_split_trace.v[j]-split_before[j];\n                    ++b.windows; b.tokens+=produced_n-seg_n0;')
    gen=once(gen,'                    comma=true;', '''                    std::fprintf(stderr," ");
                    comma=true;''') # JSON whitespace is legal; split records emitted separately below
    anchor='                std::fprintf(stderr, "],\\\"output_ids\\\":[");'
    assert anchor in gen
    extra='''                std::fprintf(stderr, "],\\\"split_by_T\\\":[");
                bool split_comma=false;
                for(size_t t=1;t<seg_bins.size();++t) {
                    const auto& b=seg_bins[t];if(!b.windows) continue;
                    std::fprintf(stderr,"%s{\\\"T\\\":%d,\\\"values\\\":[",split_comma ? "," : "",(int)t);
                    for(size_t j=0;j<16;++j) std::fprintf(stderr,"%s%.9f",j ? "," : "",b.split[j]);
                    std::fprintf(stderr,"]}");split_comma=true;
                }
'''
    gen=once(gen,anchor,extra+anchor)
    gen=include+gen
    for name,src in [('pool',pool),('expert',expert),('generate',gen)]:
        (ROOT/(name+'.cpp')).write_text(src,encoding='utf-8')
    (ROOT/'source-identity.json').write_text(json.dumps(dict(original=expected,patched={k:b.sha(ROOT/(k+'.cpp')) for k in paths},fields=NAMES),indent=2))
    compile_lines=[];objects=[]
    for name,target in [('pool','strata_kernels_cpu'),('expert','strata_engine'),('generate','strata')]:
        raw=(BUILD/f'CMakeFiles/{target}.dir/flags.make').read_text(encoding='utf-8-sig')
        vals=[re.search('^'+k+' = (.*)$',raw,re.M)[1] for k in ('CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS')]
        obj=ROOT/(name+'.obj');rsp=ROOT/(name+'.rsp')
        rsp.write_text(' '.join(vals)+f' /I"{paths[name].parent}" /nologo /c "{ROOT/(name+".cpp")}" /Fo"{obj}" /Fd"{ROOT/(name+".pdb")}"')
        objects.append(f'"{obj}"');compile_lines+=[f'cl @"{rsp}"','if errorlevel 1 exit /b %errorlevel%']
    raw=(BUILD/'CMakeFiles/strata.dir/build.make').read_text(encoding='utf-8-sig')
    link=re.search(r'^ /out:strata.exe .*$',raw,re.M)[0]
    exe=ROOT/'strata-pool-split.exe'
    link=link.replace('/out:strata.exe',f'/out:"{exe}"').replace('/implib:strata.lib',f'/implib:"{ROOT/"split.lib"}"')
    link=re.sub(r'/pdb:\S+',f'/pdb:"{(ROOT/"split.pdb").as_posix()}"',link)
    lrsp=ROOT/'link.rsp';lrsp.write_text(' '.join(objects)+' '+link)
    cmd=ROOT/'build.cmd';cmd.write_text('@echo off\ncall "C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\BuildTools\\Common7\\Tools\\VsDevCmd.bat" -arch=x64\nif errorlevel 1 exit /b %errorlevel%\n'+f'cd /d "{BUILD}"\n'+'\n'.join(compile_lines)+f'\nlink @"{lrsp}"\nexit /b %errorlevel%\n')
    if CHECK:
        print('ALL_SPLIT_ANCHORS_VALIDATED source/binary/API unchanged',flush=True);return exe
    with (ROOT/'build.log').open('w') as f:subprocess.run(['cmd','/c',str(cmd)],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=300)
    assert b.sha(EXE)==SHA
    print('SPLIT_BUILD_OK '+b.sha(exe),flush=True);return exe

def main():
    assert b.sha(EXE)==SHA and b.sha(b.PROMPT)=='9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA'
    ROOT.mkdir(exist_ok=False);b.ROOT=ROOT;p.ROOT=ROOT
    cfgfile=b.BASE/'server-task020-8080-v0142.json';cfgsha=b.sha(cfgfile);env=dict(b.CFG['env'])
    deadline=time.monotonic()+900
    while b.health('/metrics')['live']['state']!='idle':
        assert time.monotonic()<deadline,'API remained busy';print('WAITING_API_IDLE',flush=True);time.sleep(10)
    live=b.processes();assert len([x for x in live if x['name'].lower()=='strata.exe'])==1
    assert all('iq3-campaign-020' in ' '.join(x['cmdline'] or []) or str(EXE) in ' '.join(x['cmdline'] or []) for x in live),live
    (ROOT/'identity.json').write_text(json.dumps(dict(task='LUNA-20261012-027 continuation',authorization='User said go ahead with CPU/worker/LRU decomposition on2026-10-15',baseline_sha=SHA,config_sha=cfgsha,processes=live),indent=2))
    paused=False;results=[]
    try:
        assert b.health('/metrics')['live']['state']=='idle';paused=True;b.ps('Stop-ScheduledTask -TaskName Strata-Task020-API')
        for x in reversed(live):
            if psutil.pid_exists(x['pid']):
                proc=psutil.Process(x['pid']);assert 'iq3-campaign-020' in ' '.join(proc.cmdline()) or str(EXE) in ' '.join(proc.cmdline());proc.terminate()
        time.sleep(2);assert not b.processes(),b.processes();diag=build()
        for name,exe,on in [('original',EXE,False),('split-01',diag,True),('split-02',diag,True),('split-03',diag,True)]:
            assert not b.processes() and b.sha(EXE)==SHA
            b.CFG['env']={**env,'STRATA_ROUTE_TAIL_SKIP':'7','STRATA_DECODE_SEGMENTS':'1' if on else '0','STRATA_POOL_SPLIT':'1' if on else '0'}
            r=b.run(name,exe,True);p.validate(name,on)
            raw=(ROOT/name/'stderr.log').read_text(encoding='utf-8');ram=re.search(r'RAM budget ([\d.]+) GiB',raw);slots=re.search(r'expert cache (\d+) slots',raw)
            assert ram and slots and float(ram[1])==20,'ENV_BLOCKED resident'
            cap=(int(slots[1]),float(ram[1]));assert not results or tuple(results[0]['capacity'])==cap,'ENV_BLOCKED cache'
            r.update(capacity=cap,telemetry=on,diagnostic_only=True);results.append(r)
            if on:
                for rec in json.loads((ROOT/name/'segments.json').read_text()):
                    assert {x['T'] for x in rec['bins']}=={x['T'] for x in rec['split_by_T']}
                    for row in rec['split_by_T']:
                        v=row['values'];assert len(v)==16 and all(x>=0 for x in v)
                        assert v[10]<=v[9]+0.1,'memcpy outside LRU total'
                        assert sum(v[:5])<=v[8]+1.0,'phase accounting exceeds pool'
            (ROOT/'results.json').write_text(json.dumps(results,indent=2))
    finally:
        assert b.sha(EXE)==SHA and b.sha(cfgfile)==cfgsha
        if paused:
            assert not b.processes(),b.processes();b.ps('Start-ScheduledTask -TaskName Strata-Task020-API')
            for _ in range(90):
                try:
                    if b.health('/health').get('loaded'):print('API_RESTORED loaded=true ORIGINAL_BINARY_UNCHANGED',flush=True);break
                except (OSError,ValueError):pass
                time.sleep(2)
            else:raise RuntimeError('API restoration timeout')

if __name__=='__main__':
    if CHECK:ROOT.mkdir(exist_ok=False);build()
    else:main()
