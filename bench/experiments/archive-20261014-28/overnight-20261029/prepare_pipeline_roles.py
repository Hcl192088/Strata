import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent
O=R/'roles-patched';O.mkdir(exist_ok=True)
def read(name,sha):
    b=(R/'pipeline-patched'/name).read_bytes();assert hashlib.sha256(b).hexdigest().upper()==sha
    return b.decode().replace('\r\n','\n')
c=read('pool.cpp','AF976BB39DE0A47F68B559FDF985677CA46B17D7D83D50F92307A94B194E9453')
h=read('pool.hpp','8B993048979A551B885313F85853C157FED1C13AA4DE5EBA1E9B15D284216351')
def sub(t,a,b):assert t.count(a)==1,(a[:70],t.count(a));return t.replace(a,b)
h=sub(h,'    NativePipeExpert pipe_expert_[kMaxSplitMulti];',r'''    struct alignas(64) NativePipeWorker {
        uint64_t gu_tiles=0, down_tiles=0, gu_ns=0, down_ns=0;
        int cpu=-1;
    };
    std::vector<NativePipeWorker> pipe_worker_; // each slot is written by exactly one worker/host, read after park
    NativePipeExpert pipe_expert_[kMaxSplitMulti];''')
c=sub(c,'namespace strata::kernels::cpu {',r'''namespace strata::kernels::cpu {
namespace {
bool native_pipe_roles() {
    static const bool on=[] {const char* p=std::getenv("STRATA_NATIVE_PIPE_ROLES");return p&&std::atoi(p)!=0;}();return on;
}
bool native_pipe_worker_stats() {
    static const bool on=[] {const char* p=std::getenv("STRATA_CPU_PHASE_DIAG");return p&&std::atoi(p)!=0;}();return on;
}
}''')
c=sub(c,'    split_multi_.resize((size_t) kMaxSplitMulti);','    split_multi_.resize((size_t) kMaxSplitMulti);\n    pipe_worker_.resize((size_t)n_+1);')
start=c.index('void ExpertPool::drain_native_pipe(int id) {');end=c.index('\nvoid ExpertPool::run_native_pipe(',start)
part=c[start:end]
old=r'''        int task=pipe_gu_next_.load(std::memory_order_relaxed);
        while(task<gu_total && !pipe_gu_next_.compare_exchange_weak(task,task+1,std::memory_order_relaxed)){}
        if(task<gu_total) {
            const int e=task/pipe_gu_parts_,part=task%pipe_gu_parts_;
            native_pipe_rows(true,e,FF*part/pipe_gu_parts_,FF*(part+1)/pipe_gu_parts_);
            pipe_gu_done_.fetch_add(1,std::memory_order_release);
            if(pipe_expert_[e].gu_left.fetch_sub(1,std::memory_order_acq_rel)==1) {
                for(int t=0;t<mjobs_[e].nt;++t)
                    if(q2_native_kernels(nfmt_->d_type))act_quant_any(split_multi_[(size_t)e].ff[t],FF,split_multi_[(size_t)e].a2[t]);
                    else native_quant_h(*nfmt_,split_multi_[(size_t)e].ff[t],split_multi_[(size_t)e].hq[t]);
                pipe_expert_[e].ready.store(true,std::memory_order_release);
            }
            continue;
        }'''
assert part.count(old)==1
part=part.replace(old,'        if(try_gu())continue;')
setup=r'''    const bool roles=native_pipe_roles(),stats=native_pipe_worker_stats();
    auto& ws=pipe_worker_[(size_t)(id+1)];
    if(roles||stats) {
#if defined(_WIN32)
        PROCESSOR_NUMBER pn{};GetCurrentProcessorNumberEx(&pn);
        const int actual=(int)pn.Group*64+(int)pn.Number;
#else
        const int actual=-1;
#endif
        ws.cpu=actual;
        if(roles) {
            const int expected=id<0?topo_.host_core:topo_.worker_cores[(size_t)id];
            if(actual!=expected){std::fprintf(stderr,"NATIVE_PIPE FATAL role pin id=%d actual=%d expected=%d\n",id,actual,expected);std::abort();}
        }
    }
    const bool prefer_gu=roles&&(id<0 || id<topo_.p_cores-1);
    auto try_gu=[&]() {
        int task=pipe_gu_next_.load(std::memory_order_relaxed);
        while(task<gu_total && !pipe_gu_next_.compare_exchange_weak(task,task+1,std::memory_order_relaxed)){}
        if(task>=gu_total)return false;
        const int e=task/pipe_gu_parts_,part=task%pipe_gu_parts_;
        std::chrono::steady_clock::time_point begin{};if(stats)begin=std::chrono::steady_clock::now();
        native_pipe_rows(true,e,FF*part/pipe_gu_parts_,FF*(part+1)/pipe_gu_parts_);
        if(stats){++ws.gu_tiles;ws.gu_ns+=(uint64_t)std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-begin).count();}
        pipe_gu_done_.fetch_add(1,std::memory_order_release);
        if(pipe_expert_[e].gu_left.fetch_sub(1,std::memory_order_acq_rel)==1) {
            for(int t=0;t<mjobs_[e].nt;++t)
                if(q2_native_kernels(nfmt_->d_type))act_quant_any(split_multi_[(size_t)e].ff[t],FF,split_multi_[(size_t)e].a2[t]);
                else native_quant_h(*nfmt_,split_multi_[(size_t)e].ff[t],split_multi_[(size_t)e].hq[t]);
            pipe_expert_[e].ready.store(true,std::memory_order_release);
        }
        return true;
    };
'''
part=sub(part,'    uint32_t idle=0;int last_done=-1;',setup+'    uint32_t idle=0;int last_done=-1;')
part=sub(part,'        bool worked=false;','        if(prefer_gu&&try_gu())continue;\n        bool worked=false;')
part=sub(part,'                native_pipe_rows(false,e,H*part/pipe_down_parts_,H*(part+1)/pipe_down_parts_);',r'''                std::chrono::steady_clock::time_point begin{};if(stats)begin=std::chrono::steady_clock::now();
                native_pipe_rows(false,e,H*part/pipe_down_parts_,H*(part+1)/pipe_down_parts_);
                if(stats){++ws.down_tiles;ws.down_ns+=(uint64_t)std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-begin).count();}''')
c=c[:start]+part+c[end:]
old='''    const int threads=n_+(host_works_?1:0);
    static bool announced=false;'''
new=r'''    const int threads=n_+(host_works_?1:0);
    if(native_pipe_roles() && (!topo_.is_hybrid || affinity_!=PoolAffinity::All || topo_.p_cores<2 || topo_.e_cores<1 ||
        n_!=(int)topo_.worker_cores.size() || n_!=topo_.p_cores+topo_.e_cores-1 || topo_.host_core<0)) {
        std::fprintf(stderr,"NATIVE_PIPE FATAL unsupported role topology p=%d e=%d workers=%d\n",topo_.p_cores,topo_.e_cores,n_);std::abort();
    }
    static bool announced=false;'''
c=sub(c,old,new)
old='''if(!announced){std::fprintf(stderr,"NATIVE_PIPE ACTIVE workers=%d down_limit=%d exact_row_kernels=1\\n",threads,(std::max)(1,threads/3));announced=true;}'''
new=r'''if(!announced){
        std::fprintf(stderr,"NATIVE_PIPE ACTIVE workers=%d down_limit=%d exact_row_kernels=1\n",threads,(std::max)(1,threads/3));
        if(native_pipe_roles())std::fprintf(stderr,"NATIVE_PIPE_ROLES ACTIVE p=%d e=%d host_cpu=%d down_limit=%d p_gu_priority=1\n",topo_.p_cores,topo_.e_cores,topo_.host_core,(std::max)(1,threads/3));
        announced=true;
    }'''
c=sub(c,old,new)
needle='''        (unsigned long long)pipeline_calls,(unsigned long long)pipeline_overlap_tiles,(unsigned long long)pipeline_down_tiles,ms_multi_pipeline);
}'''
replace=r'''        (unsigned long long)pipeline_calls,(unsigned long long)pipeline_overlap_tiles,(unsigned long long)pipeline_down_tiles,ms_multi_pipeline);
    if(native_pipe_worker_stats() && ((pipeline_calls&1023u)<2u)) {
        for(int w=0;w<=n_;++w) {
            const auto& v=pipe_worker_[(size_t)w];if(v.cpu<0)continue;
            const char* cls=!topo_.is_hybrid?"U":(w==0 || w-1<topo_.p_cores-1)?"P":"E";
            std::fprintf(stderr,"NATIVE_PIPE_WORKER scope=engine roles=%d calls=%llu id=%d cpu=%d class=%s gu_tiles=%llu down_tiles=%llu gu_ns=%llu down_ns=%llu\n",
                native_pipe_roles()?1:0,(unsigned long long)pipeline_calls,w-1,v.cpu,cls,(unsigned long long)v.gu_tiles,(unsigned long long)v.down_tiles,
                (unsigned long long)v.gu_ns,(unsigned long long)v.down_ns);
        }
    }
}'''
c=sub(c,needle,replace)
c=sub(c,'    if(check&&!pipe){','    if(native_pipe_roles()&&!pipe){std::fprintf(stderr,"NATIVE_PIPE FATAL roles require pipe\\n");std::abort();}\n    if(check&&!pipe){')
identity={}
for name,t in [('pool.cpp',c),('pool.hpp',h)]:
    p=O/name;p.write_bytes(t.replace('\n','\r\n').encode());identity[name]=hashlib.sha256(p.read_bytes()).hexdigest().upper()
(O/'identity.json').write_text(json.dumps(identity,indent=2));print(json.dumps(identity,indent=2))
