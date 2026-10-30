"""Apply the POOL_WORKER_SKEW timing instrumentation to copies of pool.cpp / expert_source.cpp (S2K source).
usage: python patch_wskew.py <src_dir_with_originals> <out_dir>"""
import hashlib, sys
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
EXPECT = {'pool.cpp': '4A7AE645E2D494F465772397724EE3290130F1A9CBD56E6D653939D5AF03650A',
          'expert_source.cpp': 'F51BE9DED69C50CBEAEFEF05A922A3B63D2AF0B4190AE489E519D2C29259E485'}


def once(text, old, new, n=1):
    assert text.count(old) == n, (old[:90], text.count(old))
    return text.replace(old, new)


def sha(b):
    return hashlib.sha256(b).hexdigest().upper()


for k, v in EXPECT.items():
    assert sha((src / k).read_bytes()) == v, k

# ---------------------------------------------------------------- pool.cpp
t = (src / 'pool.cpp').read_bytes().decode('utf-8')
nl = '\r\n' if '\r\n' in t else '\n'
t = t.replace('\r\n', '\n')

t = once(t, '#include "strata/kernels/cpu/expert_layout.hpp"\n',
         '#include "strata/kernels/cpu/expert_layout.hpp"\n#include "wskew_trace.hpp"\n')
t = once(t, 'namespace strata::kernels::cpu {\n', 'namespace wskew { G g; }\n\nnamespace strata::kernels::cpu {\n')
t = once(t, '    threads_.reserve((size_t) n_);\n',
         '''    if (wskew::g.on) {   // POOL_WORKER_SKEW: remember which logical processor each worker is pinned to
        wskew::g.n = (std::min)(n_, wskew::kThr - 1);
        wskew::g.hw = host_works_;
        for (int i = 0; i < wskew::g.n; ++i) wskew::g.lps[i] = i < (int) topo_.worker_cores.size() ? topo_.worker_cores[(size_t) i] : -1;
        wskew::g.lps[wskew::g.n] = topo_.host_core;
    }
    threads_.reserve((size_t) n_);
''')
# drain: per-claim timing
t = once(t, '        const uint32_t i = (uint32_t) ci;\n',
         '''        const uint32_t i = (uint32_t) ci;
        const bool wk = wskew::g.on && mode_ >= 5;
        const int64_t wk_t0 = wk ? wskew::now_ns() : 0;
        int64_t wk_tr = 0, wk_seg = 0;
''')
t = once(t, '                r += r1 - r0;\n',
         '                wk_tr += (int64_t) (r1 - r0) * mjobs_[e].nt; ++wk_seg;\n                r += r1 - r0;\n', n=2)
t = once(t, '''        done_.fetch_add(1, std::memory_order_release);
    }
}

void ExpertPool::run_phase(int mode, int n_tasks) {''',
         '''        if (wk) {
            const int64_t wk_t1 = wskew::now_ns();
            wskew::Slot& s = wskew::g.slots[id >= 0 ? id : n_];
            if (s.ntasks == 0) s.first = wk_t0;
            s.last = wk_t1; s.busy += wk_t1 - wk_t0; ++s.ntasks;
            const int64_t wk_rows = mrows_ * (int64_t) (i + 1) / mtasks_ - mrows_ * (int64_t) i / mtasks_;
            s.rows += wk_rows; s.tokrows += wk_tr; s.segs += wk_seg;
            s.bytes += wk_rows * (int64_t) (mode_ == 5 ? 2 * nfmt_->gu_row : nfmt_->d_row);
        }
        done_.fetch_add(1, std::memory_order_release);
    }
}

void ExpertPool::run_phase(int mode, int n_tasks) {''')
# run_phase
t = once(t, '''void ExpertPool::run_phase(int mode, int n_tasks) {
    wait_parked("before a phase");
    mode_ = mode;
    njobs_ = n_tasks;
    const uint32_t e = begin_batch(n_tasks);
    if (host_works_) drain(-1, host_scratch_, e);
    wait_done(n_tasks);
    wait_parked("after a phase");
    hstate_.store(kIdle, std::memory_order_relaxed);
    hstate_ms_.store(now_ms(), std::memory_order_relaxed);
}
''', '''void ExpertPool::run_phase(int mode, int n_tasks) {
    const bool wk = wskew::g.on && mode >= 5;
    wait_parked("before a phase");
    if (wk) wskew::g.phase_begin();
    mode_ = mode;
    njobs_ = n_tasks;
    const int64_t wk_tp = wk ? wskew::now_ns() : 0;
    const uint32_t e = begin_batch(n_tasks);
    if (host_works_) drain(-1, host_scratch_, e);
    const int64_t wk_td = wk ? wskew::now_ns() : 0;
    wait_done(n_tasks);
    const int64_t wk_tw = wk ? wskew::now_ns() : 0;
    wait_parked("after a phase");
    const int64_t wk_tr = wk ? wskew::now_ns() : 0;
    hstate_.store(kIdle, std::memory_order_relaxed);
    hstate_ms_.store(now_ms(), std::memory_order_relaxed);
    if (wk) wskew::g.phase_end(mode, n_tasks, wk_tp, wk_td, wk_tw, wk_tr, nfmt_->gu_row, nfmt_->d_row);
}
''')
# run_split_multi_native: call-level + micro benchmark
t = once(t, '''    const auto t0 = std::chrono::steady_clock::now();
    // more distinct experts than buffers: run them in batches
''', '''    const auto t0 = std::chrono::steady_clock::now();
    int64_t wk_q_ns = 0;
    // more distinct experts than buffers: run them in batches
''')
t = once(t, '        ms_multi_q += std::chrono::duration<double, std::milli>(c - b).count();\n',
         '        ms_multi_q += std::chrono::duration<double, std::milli>(c - b).count();\n'
         '        wk_q_ns += std::chrono::duration_cast<std::chrono::nanoseconds>(c - b).count();\n')
t = once(t, '    multi_bytes += (int64_t) n * (int64_t) f.bytes;\n    mode_ = 0;\n',
         '''    if (wskew::g.on) {
        int nts[kMaxSplitMulti];
        const int ne = (std::min)(n, kMaxSplitMulti);
        for (int e = 0; e < ne; ++e) nts[e] = jobs[e].nt;
        wskew::g.end_call(ne, nts, (int64_t) n * (int64_t) f.bytes,
                          std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now() - t0).count(), wk_q_ns);
        // single-thread kernel microbenchmark on the host thread (workers parked; outputs untouched: scratch buffers only)
        if (wskew::g.micro && n <= kMaxSplitMulti && wskew::g.ncalls > 2000 && wskew::g.micro_done < wskew::g.micro_max &&
            !q2_native_kernels(f.gu_type) && !q2_native_kernels(f.d_type)) {
            const int want = 1 + (wskew::g.micro_done % 3);
            int e = -1;
            for (int j = 0; j < n; ++j) if (jobs[j].nt == want) { e = j; break; }
            if (e < 0) for (int j = 0; j < n; ++j) if (jobs[j].nt >= 1 && jobs[j].nt <= MAXT) { e = j; break; }
            if (e >= 0) {
                SplitBufMulti& sb = split_multi_[(size_t) e];
                const ExpertJobMulti& jb = jobs[e];
                const int nt = jb.nt;
                float* ff[MAXT];
                const void* hq[MAXT];
                float* op[MAXT];
                static thread_local float outb[MAXT][H];
                for (int t2 = 0; t2 < nt; ++t2) { ff[t2] = sb.ff[t2]; hq[t2] = sb.hq[t2]; op[t2] = outb[t2]; }
                auto flush = [&] { for (size_t o = 0; o < f.bytes; o += 64) _mm_clflush(jb.blob + o); _mm_mfence(); };
                flush();
                const int64_t a0 = wskew::now_ns();
                native_gu_rows(f, jb.blob, jb.nact, nt, ff, 0, FF);
                const int64_t a1 = wskew::now_ns();
                native_gu_rows(f, jb.blob, jb.nact, nt, ff, 0, FF);
                const int64_t a2 = wskew::now_ns();
                flush();
                __m128i acc = _mm_setzero_si128();
                const int64_t b0 = wskew::now_ns();
                for (const uint8_t* base : {jb.blob, jb.blob + f.up_off}) {
                    const uint8_t* end = base + (size_t) FF * f.gu_row;
                    for (const uint8_t* p = base; p + 64 <= end; p += 64) {
                        acc = _mm_xor_si128(acc, _mm_loadu_si128((const __m128i*) p));
                        acc = _mm_xor_si128(acc, _mm_loadu_si128((const __m128i*) (p + 16)));
                        acc = _mm_xor_si128(acc, _mm_loadu_si128((const __m128i*) (p + 32)));
                        acc = _mm_xor_si128(acc, _mm_loadu_si128((const __m128i*) (p + 48)));
                    }
                }
                const int64_t b1 = wskew::now_ns();
                static volatile int sink;
                sink = _mm_cvtsi128_si32(acc);
                flush();
                const int64_t c0 = wskew::now_ns();
                native_down_rows(f, jb.blob, hq, nt, op, 0, H);
                const int64_t c1 = wskew::now_ns();
                wskew::MicroAgg& u = wskew::g.mic[nt];
                ++u.n; u.ns_gu_cold += a1 - a0; u.ns_gu_warm += a2 - a1; u.ns_read_cold += b1 - b0; u.ns_down_cold += c1 - c0;
                u.bytes_gu = (int64_t) (2 * (size_t) FF * f.gu_row); u.bytes_down = (int64_t) ((size_t) H * f.d_row);
                ++wskew::g.micro_done;
            }
        }
    }
    multi_bytes += (int64_t) n * (int64_t) f.bytes;
    mode_ = 0;
''')
(out / 'pool.cpp').write_bytes(t.replace('\n', nl).encode('utf-8'))

# ---------------------------------------------------------------- expert_source.cpp
t = (src / 'expert_source.cpp').read_bytes().decode('utf-8')
nl = '\r\n' if '\r\n' in t else '\n'
t = t.replace('\r\n', '\n')
t = once(t, '#include "strata/kernels/cpu/expert_layout.hpp"\n',
         '#include "strata/kernels/cpu/expert_layout.hpp"\n#include "../kernels/cpu/wskew_trace.hpp"\n')
# pass 1 of the overlap split
t = once(t, '''        if (njobs > 0) {
            if (native) d.pool->run_split_multi_native(lay.fmt[(size_t) d.layers], d.jobs_multi.data(), njobs);''',
         '''        if (njobs > 0) {
            wskew::g.T = (int) n_tok; wskew::g.kind = 1;
            if (native) d.pool->run_split_multi_native(lay.fmt[(size_t) d.layers], d.jobs_multi.data(), njobs);''')
t = once(t, '''    if (njobs > njobs1) {   // njobs1 is 0 unless the overlap split the batch: then these are the experts that were read
''', '''    if (njobs > njobs1) {   // njobs1 is 0 unless the overlap split the batch: then these are the experts that were read
        wskew::g.T = (int) n_tok; wskew::g.kind = mo_split ? 2 : 0;
''')
t = once(t, '''            if (!cj.empty()) {
                if (native) d.pool->run_split_multi_native(lay.fmt[(size_t) d.layers], cj.data(), (int) cj.size());''',
         '''            if (!cj.empty()) {
                wskew::g.T = (int) n_tok; wskew::g.kind = 3;
                if (native) d.pool->run_split_multi_native(lay.fmt[(size_t) d.layers], cj.data(), (int) cj.size());''')
(out / 'expert_source.cpp').write_bytes(t.replace('\n', nl).encode('utf-8'))
print('PATCH_OK', sha((out / 'pool.cpp').read_bytes()), sha((out / 'expert_source.cpp').read_bytes()))
