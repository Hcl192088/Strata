import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parent;S=R/'source'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def once(s,a,b):
 assert s.count(a)==1,(a[:100],s.count(a))
 return s.replace(a,b)
def windows_first(s,a,b):
 assert s.count(a)==2 and s.index(a)<s.index('#elif defined(__linux__)',s.index('bool FileExpertSource::read_direct'))
 return s.replace(a,b,1)
manifest={}
e=S/'src/core/expert_source.cpp';s=e.read_text(encoding='utf-8');manifest[str(e.relative_to(S))]={'before':sha(e)}
assert sha(e)=='2294D6B8F007A3D238EE0D68CAA77B888A4491682156B796C869EC07E6163658'
code=r'''
namespace {
std::atomic<uint64_t> iad_seq{0},iad_request{0};
std::atomic<bool> iad_active{false};
bool iad_on() { static const bool on=std::getenv("STRATA_IO_ARRIVAL_DIAG")!=nullptr; return on && iad_active.load(std::memory_order_acquire); }
uint64_t iad_now() {return (uint64_t)std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
FILE* iad_file() {
 static FILE* f=[] { const char* p=std::getenv("STRATA_IO_ARRIVAL_DIAG"); if(!p)return (FILE*)nullptr; FILE* q=std::fopen(p,"wb"); if(!q)std::abort(); std::setvbuf(q,nullptr,_IOFBF,1<<20);return q;}();return f;
}
void iad_write(const std::string& s) { static std::mutex m; std::lock_guard<std::mutex> g(m); FILE* f=iad_file();if(!f || std::fwrite(s.data(),1,s.size(),f)!=s.size())std::abort(); }
}
void io_arrival_decode(bool on) {
 if(std::getenv("STRATA_IO_ARRIVAL_DIAG")==nullptr)return;
 if(on)iad_request.fetch_add(1);
 iad_active.store(on,std::memory_order_release);
 std::ostringstream o;o<<(on?"B":"E")<<','<<iad_request.load()<<','<<iad_now()<<'\n';iad_write(o.str());
 if(!on)std::fflush(iad_file());
}
'''
s=once(s,'bool cpu_phase_diag_enabled() {',code+'\nbool cpu_phase_diag_enabled() {')
s=once(s,'    // every request in flight before the first wait: the drive sees the whole batch as one queue',r'''    const bool iad=iad_on();
    const uint64_t iad_batch=iad?iad_seq.fetch_add(1)+1:0,iad_req=iad_request.load();
    std::vector<uint64_t> iad_submit(iad?sc.req.size():0),iad_lo(iad?sc.req.size():0),iad_hi(iad?sc.req.size():0);
    if(iad && sc.req.size()>MAXIMUM_WAIT_OBJECTS) {std::fprintf(stderr,"IO_ARRIVAL_DIAG LIMIT requests=%zu\n",sc.req.size());std::abort();}
    // every request in flight before the first wait: the drive sees the whole batch as one queue''')
s=once(s,'        if (!ReadFile(r.h, sc.buf + r.pos, (DWORD) r.size, nullptr, &o)',
'''        if(iad)iad_submit[q]=iad_lo[q]=iad_now();
        if (!ReadFile(r.h, sc.buf + r.pos, (DWORD) r.size, nullptr, &o)''')
old='''    for (size_t q = 0; q < issued; ++q)
        if (!GetOverlappedResult(sc.req[q].h, &sc.ov[q], &got[q], TRUE)) ok = false;'''
new=r'''    if(iad && ok && issued==sc.req.size()) {
        size_t left=issued;
        while(left) {
            std::vector<HANDLE> pending;
            for(size_t q=0;q<issued;++q) if(!iad_hi[q]) {
                const uint64_t before=iad_now();
                const DWORD state=WaitForSingleObject(sc.ev[q],0);
                const uint64_t now=iad_now();
                if(state==WAIT_OBJECT_0) {
                    iad_hi[q]=now;--left;
                    if(!GetOverlappedResult(sc.req[q].h,&sc.ov[q],&got[q],FALSE))ok=false;
                }else if(state==WAIT_TIMEOUT) {iad_lo[q]=before;pending.push_back(sc.ev[q]);}
                else {std::fprintf(stderr,"IO_ARRIVAL_DIAG event failure\n");std::abort();}
            }
            if(left) {
                const DWORD v=WaitForMultipleObjects((DWORD)pending.size(),pending.data(),FALSE,INFINITE);
                if(v<WAIT_OBJECT_0 || v>=WAIT_OBJECT_0+pending.size()) {std::fprintf(stderr,"IO_ARRIVAL_DIAG wait failure\n");std::abort();}
            }
        }
    }else {
        for (size_t q = 0; q < issued; ++q)
            if (!GetOverlappedResult(sc.req[q].h, &sc.ov[q], &got[q], TRUE)) ok = false;
    }'''
s=once(s,old,new)
s=once(s,'    PhaseTimer phase_copy(phase_io.copy_ns);\n    for (const Window& x : sc.win) {',
'''    const uint64_t iad_copy_begin=iad?iad_now():0;
    PhaseTimer phase_copy(phase_io.copy_ns);
    for (const Window& x : sc.win) {''')
s=windows_first(s,'''        std::memcpy(x.dst + x.at, sc.buf + sc.req[x.req].pos + x.in_req + x.skip, (size_t) x.n);
    }
    return true;''',r'''        std::memcpy(x.dst + x.at, sc.buf + sc.req[x.req].pos + x.in_req + x.skip, (size_t) x.n);
    }
    if(iad) {
        const uint64_t end=iad_now();std::ostringstream o;
        o<<"I,"<<iad_req<<','<<iad_batch<<','<<issued<<','<<n<<','<<iad_copy_begin<<','<<end<<'\n';
        for(size_t q=0;q<issued;++q)o<<"Q,"<<iad_req<<','<<iad_batch<<','<<q<<','<<sc.req[q].size<<','<<iad_submit[q]<<','<<iad_lo[q]<<','<<iad_hi[q]<<'\n';
        for(const Window& x:sc.win)o<<"W,"<<iad_req<<','<<iad_batch<<','<<(uintptr_t)x.dst<<','<<x.req<<','<<x.at<<','<<x.n<<'\n';
        iad_write(o.str());
    }
    return true;''')
s=once(s,'    FileExpertSource* mo_fs = nullptr;',
'''    const bool iad_dispatch=iad_on();
    const uint64_t iad_dstart=iad_dispatch?iad_now():0,iad_first_batch=iad_seq.load();
    uint64_t iad_ready_end=iad_dstart,iad_bulk_ready=iad_dstart;
    FileExpertSource* mo_fs = nullptr;''')
s=once(s,'        const auto rb = std::chrono::steady_clock::now();\n        mo_join.join();',
'''        const auto rb = std::chrono::steady_clock::now();
        if(iad_dispatch)iad_ready_end=iad_now();
        mo_join.join();
        if(iad_dispatch)iad_bulk_ready=iad_now();''')
s=once(s,'    pt("run", njobs);\n    if (njobs > njobs1)',
'''    pt("run", njobs);
    const uint64_t iad_cold_begin=iad_dispatch?iad_now():0;
    if (njobs > njobs1)''')
s=once(s,'    mo_join.join();\n    if (d.remote_count > 0)',r'''    if(iad_dispatch) {
        const uint64_t end=iad_now();std::ostringstream o;
        o<<"D,"<<iad_request.load()<<','<<d.layers<<','<<iad_first_batch<<','<<iad_seq.load()<<','<<iad_dstart<<','<<iad_ready_end<<','<<iad_bulk_ready<<','<<iad_cold_begin<<','<<end<<','<<njobs1<<','<<(njobs-njobs1)<<','<<mo_npend<<','<<(mo_split?1:0)<<'\n';iad_write(o.str());
    }
    mo_join.join();
    if (d.remote_count > 0)''')
e.write_text(s,encoding='utf-8');manifest[str(e.relative_to(S))]['after']=sha(e)
h=S/'include/strata/core/cpu_phase_diag.hpp';s=h.read_text();manifest[str(h.relative_to(S))]={'before':sha(h)}
s=once(s,'bool cpu_phase_diag_enabled();','void io_arrival_decode(bool on);\nbool cpu_phase_diag_enabled();');h.write_text(s);manifest[str(h.relative_to(S))]['after']=sha(h)
g=S/'src/program/generate.cpp';s=g.read_text(encoding='utf-8');manifest[str(g.relative_to(S))]={'before':sha(g)}
s=once(s,'            const DecSnap ds0 = dec_snap();','            strata::core::io_arrival_decode(true);\n            const DecSnap ds0 = dec_snap();')
s=once(s,'                const DecSnap d1 = dec_snap();','                strata::core::io_arrival_decode(false);\n                const DecSnap d1 = dec_snap();')
g.write_text(s,encoding='utf-8');manifest[str(g.relative_to(S))]['after']=sha(g)
(R/'patch-identity.json').write_text(json.dumps(manifest,indent=2))
p=subprocess.run(['git','-C',str(S),'diff','--check'],capture_output=True,text=True);assert p.returncode==0,p.stdout+p.stderr
(R/'diag.patch').write_text(subprocess.check_output(['git','-C',str(S),'diff'],text=True),encoding='utf-8')
print(json.dumps(manifest,indent=2))
