import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parent
OUT=R/'pipeline-patched';OUT.mkdir(exist_ok=True)
def load(path,expected):
    raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest().upper()==expected
    return raw.decode().replace('\r\n','\n')
cpp=load(R/'src/pool.cpp','4A7AE645E2D494F465772397724EE3290130F1A9CBD56E6D653939D5AF03650A')
hpp=load(R/'src/pool.hpp','4255FD01AE6E55A650B2E81316202C5B9206E0AE2271CD9FA81EDC3B27D33C1A')
gen=load(R/'patched/generate.cpp','27CCC961B633A13D4B0E359E9505A5CBF3DDC6AB32B4C82B9FDD9084DBA40F5F')
def change(text,old,new):
    assert text.count(old)==1,(old[:90],text.count(old))
    return text.replace(old,new)
hpp=change(hpp,'double ms_multi_gu = 0, ms_multi_q = 0, ms_multi_down = 0;',
    'double ms_multi_gu = 0, ms_multi_q = 0, ms_multi_down = 0, ms_multi_pipeline = 0;\n    uint64_t pipeline_calls = 0, pipeline_overlap_tiles = 0, pipeline_down_tiles = 0;')
hpp=change(hpp,'    const NativeFmt* nfmt_ = nullptr;',r'''    struct alignas(64) NativePipeExpert {
        std::atomic<int> gu_left{0}, down_next{0};
        std::atomic<bool> ready{false};
    };
    NativePipeExpert pipe_expert_[kMaxSplitMulti];
    alignas(64) std::atomic<int> pipe_gu_next_{0};
    alignas(64) std::atomic<int> pipe_gu_done_{0};
    alignas(64) std::atomic<int> pipe_down_done_{0};
    alignas(64) std::atomic<int> pipe_down_active_{0};
    alignas(64) std::atomic<int> pipe_overlap_{0};
    int pipe_nb_=0, pipe_gu_parts_=1, pipe_down_parts_=1, pipe_down_limit_=1;
    void native_pipe_rows(bool gu, int e, int r0, int r1);
    void drain_native_pipe(int id);
    void run_native_pipe(const NativeFmt& f, ExpertJobMulti* jobs, int n);
    const NativeFmt* nfmt_ = nullptr;''')
cpp=change(cpp,'#include <cstdlib>','#include <cstdlib>\n#include <cstring>')
cpp=change(cpp,'        } else if (mode_ >= 5) {','        } else if (mode_ == 7) {\n            drain_native_pipe(id);\n        } else if (mode_ >= 5) {')
insert=r'''
// The same row kernels as phases 5/6. No arithmetic is fused or requantized differently.
void ExpertPool::native_pipe_rows(bool gu, int e, int r0, int r1) {
    SplitBufMulti& sb=split_multi_[(size_t)e];
    if (gu && q2_native_kernels(nfmt_->gu_type)) {
        thread_local float gbuf[MAXT][FF],ubuf[MAXT][FF];
        float* gp[MAXT];float* up[MAXT];
        for(int t=0;t<mjobs_[e].nt;++t){gp[t]=gbuf[t];up[t]=ubuf[t];}
        const int nbk=(int)(nfmt_->n_embd/64);
        q2_rows_any(mjobs_[e].blob,nfmt_->gu_row,nbk,mjobs_[e].act,mjobs_[e].nt,gp,r0,r1);
        q2_rows_any(mjobs_[e].blob+nfmt_->up_off,nfmt_->gu_row,nbk,mjobs_[e].act,mjobs_[e].nt,up,r0,r1);
        for(int t=0;t<mjobs_[e].nt;++t)for(int r=r0;r<r1;++r)
            sb.ff[t][r]=(gbuf[t][r]/(1.f+std::exp(-gbuf[t][r])))*ubuf[t][r];
    } else if(gu) {
        float* ff[MAXT];for(int t=0;t<mjobs_[e].nt;++t)ff[t]=sb.ff[t];
        native_gu_rows(*nfmt_,mjobs_[e].blob,mjobs_[e].nact,mjobs_[e].nt,ff,r0,r1);
    } else if(q2_native_kernels(nfmt_->d_type)) {
        const ActQ* a2[MAXT];for(int t=0;t<mjobs_[e].nt;++t)a2[t]=&sb.a2[t];
        q2_rows_any(mjobs_[e].blob+nfmt_->down_off,nfmt_->d_row,(int)(nfmt_->n_ff/64),a2,mjobs_[e].nt,mjobs_[e].out,r0,r1);
    } else {
        const void* hq[MAXT];for(int t=0;t<mjobs_[e].nt;++t)hq[t]=sb.hq[t];
        native_down_rows(*nfmt_,mjobs_[e].blob,hq,mjobs_[e].nt,mjobs_[e].out,r0,r1);
    }
}

void ExpertPool::drain_native_pipe(int id) {
    const int gu_total=pipe_nb_*pipe_gu_parts_,down_total=pipe_nb_*pipe_down_parts_;
    const int threads=n_+(host_works_?1:0);
    const int start=(id+1)%pipe_nb_;
    uint32_t idle=0;int last_done=-1;
    auto last_progress=std::chrono::steady_clock::now();
    while(pipe_down_done_.load(std::memory_order_acquire)<down_total) {
        bool worked=false;
        // Keep GU workers progressing while down uses only a bounded bandwidth share.
        const int limit=pipe_gu_next_.load(std::memory_order_relaxed)<gu_total?pipe_down_limit_:threads;
        int active=pipe_down_active_.load(std::memory_order_relaxed);
        if(active<limit && pipe_down_active_.compare_exchange_strong(active,active+1,std::memory_order_acq_rel)) {
            for(int scan=0;scan<pipe_nb_;++scan) {
                const int e=(start+scan)%pipe_nb_;
                auto& state=pipe_expert_[e];
                if(!state.ready.load(std::memory_order_acquire))continue;
                int part=state.down_next.load(std::memory_order_relaxed);
                while(part<pipe_down_parts_ && !state.down_next.compare_exchange_weak(part,part+1,std::memory_order_relaxed)){}
                if(part>=pipe_down_parts_)continue;
                if(pipe_gu_done_.load(std::memory_order_acquire)<gu_total)pipe_overlap_.fetch_add(1,std::memory_order_relaxed);
                native_pipe_rows(false,e,H*part/pipe_down_parts_,H*(part+1)/pipe_down_parts_);
                pipe_down_done_.fetch_add(1,std::memory_order_release);
                worked=true;break;
            }
            pipe_down_active_.fetch_sub(1,std::memory_order_release);
        }
        if(worked)continue;
        int task=pipe_gu_next_.load(std::memory_order_relaxed);
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
        }
        _mm_pause();
        if((++idle&4095u)==0) {
            const int done=pipe_down_done_.load(std::memory_order_acquire);
            const auto now=std::chrono::steady_clock::now();
            if(done!=last_done){last_done=done;last_progress=now;}
            else if(now-last_progress>std::chrono::seconds(5)) {
                std::fprintf(stderr,"NATIVE_PIPE FATAL stalled down=%d/%d gu=%d/%d\n",done,down_total,pipe_gu_done_.load(),gu_total);std::abort();
            }
        }
    }
}

void ExpertPool::run_native_pipe(const NativeFmt& f,ExpertJobMulti* jobs,int n) {
    const auto begin=std::chrono::steady_clock::now();
    const int threads=n_+(host_works_?1:0);
    static bool announced=false;
    if(!announced){std::fprintf(stderr,"NATIVE_PIPE ACTIVE workers=%d down_limit=%d exact_row_kernels=1\n",threads,std::max(1,threads/3));announced=true;}
    for(int b0=0;b0<n;b0+=kMaxSplitMulti) {
        wait_parked("before pipeline setup");
        const int nb=std::min(kMaxSplitMulti,n-b0);
        mjobs_=jobs+b0;nfmt_=&f;pipe_nb_=nb;
        pipe_gu_parts_=std::min(FF,std::max(1,(phase_tasks((int64_t)nb*FF)+nb-1)/nb));
        pipe_down_parts_=std::min(H,std::max(1,(phase_tasks((int64_t)nb*H)+nb-1)/nb));
        pipe_down_limit_=std::max(1,threads/3);
        pipe_gu_next_.store(0);pipe_gu_done_.store(0);pipe_down_done_.store(0);pipe_down_active_.store(0);pipe_overlap_.store(0);
        for(int e=0;e<nb;++e){pipe_expert_[e].gu_left.store(pipe_gu_parts_);pipe_expert_[e].down_next.store(0);pipe_expert_[e].ready.store(false);}
        run_phase(7,threads);
        if(pipe_gu_done_.load()!=nb*pipe_gu_parts_ || pipe_down_done_.load()!=nb*pipe_down_parts_ || pipe_down_active_.load()!=0) {
            std::fprintf(stderr,"NATIVE_PIPE FATAL completion accounting\n");std::abort();
        }
        pipeline_overlap_tiles+=(uint64_t)pipe_overlap_.load();pipeline_down_tiles+=(uint64_t)(nb*pipe_down_parts_);++pipeline_calls;
    }
    const double elapsed=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-begin).count();
    ms_multi_pipeline+=elapsed;ms_drain_+=elapsed;multi_bytes+=(int64_t)n*(int64_t)f.bytes;mode_=0;
    if((pipeline_calls&127u)<2u)std::fprintf(stderr,"NATIVE_PIPE progress calls=%llu overlap_down_tiles=%llu down_tiles=%llu pool_ms=%.6f\n",
        (unsigned long long)pipeline_calls,(unsigned long long)pipeline_overlap_tiles,(unsigned long long)pipeline_down_tiles,ms_multi_pipeline);
}

'''
insert=insert.replace('std::min(FF,','std::min((int)FF,').replace('std::min(H,','std::min((int)H,')
insert=insert.replace('std::min(', '(std::min)(').replace('std::max(', '(std::max)(')
cpp=change(cpp,'void ExpertPool::run_split_multi_native(const NativeFmt& f, ExpertJobMulti* jobs, int n) {',insert+'void ExpertPool::run_split_multi_native(const NativeFmt& f, ExpertJobMulti* jobs, int n) {')
old='''void ExpertPool::run_split_multi_native(const NativeFmt& f, ExpertJobMulti* jobs, int n) {
    if (n <= 0) return;
    const auto t0'''
new=r'''void ExpertPool::run_split_multi_native(const NativeFmt& f, ExpertJobMulti* jobs, int n) {
    if (n <= 0) return;
    static const bool pipe=[] {const char* p=std::getenv("STRATA_NATIVE_PIPE");return p&&std::atoi(p)!=0;}();
    static const bool check=[] {const char* p=std::getenv("STRATA_NATIVE_PIPE_CHECK");return p&&std::atoi(p)!=0;}();
    static thread_local bool reference=false;
    if(check&&!pipe){std::fprintf(stderr,"NATIVE_PIPE FATAL check requires pipe\n");std::abort();}
    if(pipe&&!reference) {
        run_native_pipe(f,jobs,n);
        if(check) {
            std::vector<float> expected;
            for(int e=0;e<n;++e)for(int t=0;t<jobs[e].nt;++t)expected.insert(expected.end(),jobs[e].out[t],jobs[e].out[t]+H);
            reference=true;run_split_multi_native(f,jobs,n);reference=false;
            size_t at=0;
            for(int e=0;e<n;++e)for(int t=0;t<jobs[e].nt;++t) {
                if(std::memcmp(expected.data()+at,jobs[e].out[t],(size_t)H*sizeof(float))!=0) {
                    for(int r=0;r<H;++r)if(std::memcmp(expected.data()+at+r,jobs[e].out[t]+r,sizeof(float))!=0){
                        std::fprintf(stderr,"NATIVE_PIPE_CHECK MISMATCH gu=%d down=%d expert=%d token=%d row=%d pipe=%.9g reference=%.9g\n",f.gu_type,f.d_type,e,t,r,expected[at+r],jobs[e].out[t][r]);break;}
                    std::abort();
                }
                at+=H;
            }
            static uint64_t checked=0,values=0;++checked;values+=expected.size();
            if(checked<=48 || (checked&127u)==1)std::fprintf(stderr,"NATIVE_PIPE_CHECK batches=%llu values=%llu gu_type=%d down_type=%d mismatch=0\n",
                (unsigned long long)checked,(unsigned long long)values,f.gu_type,f.d_type);
        }
        return;
    }
    const auto t0'''
cpp=change(cpp,old,new)
gen=change(gen,'const double cpd_gu0=pool.ms_multi_gu, cpd_q0=pool.ms_multi_q, cpd_down0=pool.ms_multi_down;',
    'const double cpd_gu0=pool.ms_multi_gu, cpd_q0=pool.ms_multi_q, cpd_down0=pool.ms_multi_down, cpd_pipe0=pool.ms_multi_pipeline;')
gen=change(gen,'down_ms=%.6f join_ms=%.6f','down_ms=%.6f pipeline_ms=%.6f join_ms=%.6f')
gen=change(gen,'pool.ms_multi_down-cpd_down0,','pool.ms_multi_down-cpd_down0,pool.ms_multi_pipeline-cpd_pipe0,')
gen=change(gen,'pool.ms_multi_gu + pool.ms_multi_down),','pool.ms_multi_gu + pool.ms_multi_down + pool.ms_multi_pipeline),')
identity={}
for name,text in [('pool.cpp',cpp),('pool.hpp',hpp),('generate.cpp',gen)]:
    p=OUT/name;p.write_bytes(text.replace('\n','\r\n').encode());identity[name]=hashlib.sha256(p.read_bytes()).hexdigest().upper()
(OUT/'identity.json').write_text(json.dumps(identity,indent=2));print(json.dumps(identity,indent=2))
