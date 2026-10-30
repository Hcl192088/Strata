"""Generate a timing-only patch from freshly copied S2K sources, with unique-anchor checks."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
SRC=ROOT/'src'; OUT=ROOT/'patched'; OUT.mkdir(exist_ok=True)
def edit(name): return (SRC/name).read_text(encoding='utf-8').replace('\r\n','\n')
def once(s,a,b):
    assert s.count(a)==1,(a[:100],s.count(a))
    return s.replace(a,b)
header='''#pragma once
#include <cstdint>
namespace strata::core {
struct CpuPhaseDiag {
    double helper_ms=0, join_ms=0, ready_ms=0, inline_ms=0, lru_ms=0;
    double direct_ms=0, copy_ms=0, issue_wait_ms=0;
    uint64_t issued_bytes=0, useful_bytes=0, splits=0, inlines=0;
};
bool cpu_phase_diag_enabled();
CpuPhaseDiag cpu_phase_diag_snapshot();
}
'''
(OUT/'cpu_phase_diag.hpp').write_text(header,encoding='utf-8')
s=edit('expert_source.cpp')
assert hashlib.sha256((SRC/'expert_source.cpp').read_bytes()).hexdigest().upper()=='F51BE9DED69C50CBEAEFEF05A922A3B63D2AF0B4190AE489E519D2C29259E485'
s=once(s,'#include "strata/core/expert_source.hpp"','#include "strata/core/expert_source.hpp"\n#include "strata/core/cpu_phase_diag.hpp"')
anchor='namespace strata::core {\n'
insert='''namespace strata::core {
namespace {
struct PhaseIoCounters {
    std::atomic<uint64_t> direct_ns{0}, copy_ns{0}, issue_wait_ns{0}, inline_ns{0}, lru_ns{0};
    std::atomic<uint64_t> issued_bytes{0}, useful_bytes{0};
};
PhaseIoCounters phase_io;
struct PhaseTimer {
    std::atomic<uint64_t>& dst;
    bool on;
    std::chrono::steady_clock::time_point begin{};
    explicit PhaseTimer(std::atomic<uint64_t>& d):dst(d),on(cpu_phase_diag_enabled()) {
        if(on) begin=std::chrono::steady_clock::now();
    }
    ~PhaseTimer() { if(on) dst.fetch_add((uint64_t)std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-begin).count(),std::memory_order_relaxed); }
};
}
bool cpu_phase_diag_enabled() {
    static const bool on=[] { const char* p=std::getenv("STRATA_CPU_PHASE_DIAG"); return p && std::atoi(p)!=0; }();
    return on;
}
'''
assert s.count(anchor)==2
s=s.replace(anchor,insert,1)
s=once(s,'bool FileExpertSource::read_direct(const Fill* fills, size_t n) const {\n','bool FileExpertSource::read_direct(const Fill* fills, size_t n) const {\n    PhaseTimer phase_direct(phase_io.direct_ns);\n')
s=once(s,'    // every request in flight before the first wait: the drive sees the whole batch as one queue\n',
'''    if(cpu_phase_diag_enabled()) {
        uint64_t useful=0; for(const auto& x:sc.win) useful+=x.n;
        phase_io.issued_bytes.fetch_add(total,std::memory_order_relaxed);
        phase_io.useful_bytes.fetch_add(useful,std::memory_order_relaxed);
    }
    {
    PhaseTimer phase_wait(phase_io.issue_wait_ns);
    // every request in flight before the first wait: the drive sees the whole batch as one queue
''')
# issued/ok/got must stay in outer scope for the copy validation.
s=s.replace('    {\n    PhaseTimer phase_wait(phase_io.issue_wait_ns);\n    // every request', '    // every request',1)
s=once(s,'    size_t issued = 0;\n    bool ok = true;\n','    size_t issued = 0;\n    bool ok = true;\n    std::vector<DWORD>& got = sc.got;\n    {\n    PhaseTimer phase_wait(phase_io.issue_wait_ns);\n')
s=once(s,'    std::vector<DWORD>& got = sc.got;\n    got.assign(sc.req.size(), 0);\n','    got.assign(sc.req.size(), 0);\n')
s=once(s,'    if (!ok || issued < sc.req.size()) return false;\n    for (const Window& x : sc.win) {\n','    }\n    if (!ok || issued < sc.req.size()) return false;\n    PhaseTimer phase_copy(phase_io.copy_ns);\n    for (const Window& x : sc.win) {\n')
s=once(s,'                    mo_fs->prefetch_split_run();   // nothing to overlap with: read here, as prefetch() does',
'''                    PhaseTimer phase_inline(phase_io.inline_ns);
                    mo_fs->prefetch_split_run();   // nothing to overlap with: read here, as prefetch() does''')
s=once(s,'    if (auto* file_source = dynamic_cast<FileExpertSource*>(d.src))\n        file_source->ram_lru_complete(d.layers, ids, kind, n_tok * k, d.host_res, d.job_of.data(), d.jobs_multi.data());',
'''    if (auto* file_source = dynamic_cast<FileExpertSource*>(d.src)) {
        PhaseTimer phase_lru(phase_io.lru_ns);
        file_source->ram_lru_complete(d.layers, ids, kind, n_tok * k, d.host_res, d.job_of.data(), d.jobs_multi.data());
    }''')
s=once(s,'MissStats g_miss_stats;\n}  // namespace\n','''MissStats g_miss_stats;
}  // namespace
CpuPhaseDiag cpu_phase_diag_snapshot() {
    CpuPhaseDiag p;
    p.helper_ms=MissIo::get().read_ms(); p.join_ms=g_miss_stats.join_ms; p.ready_ms=g_miss_stats.over_ms;
    p.inline_ms=(double)phase_io.inline_ns.load()/1e6; p.lru_ms=(double)phase_io.lru_ns.load()/1e6;
    p.direct_ms=(double)phase_io.direct_ns.load()/1e6; p.copy_ms=(double)phase_io.copy_ns.load()/1e6;
    p.issue_wait_ms=(double)phase_io.issue_wait_ns.load()/1e6;
    p.issued_bytes=phase_io.issued_bytes.load(); p.useful_bytes=phase_io.useful_bytes.load();
    p.splits=g_miss_stats.split; p.inlines=g_miss_stats.inline_reads;
    return p;
}
''')
(OUT/'expert_source.cpp').write_text(s,encoding='utf-8')
s=edit('generate.cpp')
s=once(s,'#include "strata/core/expert_source.hpp"','#include "strata/core/expert_source.hpp"\n#include "strata/core/cpu_phase_diag.hpp"')
s=once(s,'            const DecSnap ds0 = dec_snap();\n','''            const DecSnap ds0 = dec_snap();
            const bool cpd_on=strata::core::cpu_phase_diag_enabled();
            const auto cpd0=cpd_on?strata::core::cpu_phase_diag_snapshot():strata::core::CpuPhaseDiag{};
            const double cpd_gu0=pool.ms_multi_gu, cpd_q0=pool.ms_multi_q, cpd_down0=pool.ms_multi_down;
''')
s=once(s,'                const DecSnap d1 = dec_snap();\n','''                const DecSnap d1 = dec_snap();
                if(cpd_on) {
                    const auto z=strata::core::cpu_phase_diag_snapshot();
                    std::fprintf(stderr,"CPU_PHASE_DECODE windows=%lld cpu_ms=%.6f jobs_ms=%.6f gu_ms=%.6f quant_ms=%.6f down_ms=%.6f join_ms=%.6f ready_ms=%.6f inline_ms=%.6f lru_ms=%.6f helper_ms=%.6f direct_ms=%.6f copy_ms=%.6f issue_wait_ms=%.6f issued_bytes=%llu useful_bytes=%llu splits=%llu inlines=%llu\\n",
                        (long long)dec_windows,d1.run-ds0.run,d1.jobs-ds0.jobs,pool.ms_multi_gu-cpd_gu0,pool.ms_multi_q-cpd_q0,pool.ms_multi_down-cpd_down0,
                        z.join_ms-cpd0.join_ms,z.ready_ms-cpd0.ready_ms,z.inline_ms-cpd0.inline_ms,z.lru_ms-cpd0.lru_ms,z.helper_ms-cpd0.helper_ms,
                        z.direct_ms-cpd0.direct_ms,z.copy_ms-cpd0.copy_ms,z.issue_wait_ms-cpd0.issue_wait_ms,
                        (unsigned long long)(z.issued_bytes-cpd0.issued_bytes),(unsigned long long)(z.useful_bytes-cpd0.useful_bytes),
                        (unsigned long long)(z.splits-cpd0.splits),(unsigned long long)(z.inlines-cpd0.inlines));
                }
''')
(OUT/'generate.cpp').write_text(s,encoding='utf-8')
manifest={'base_source_head':'61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406','original_sha256':{},'patched_sha256':{}}
for name in ('expert_source.cpp','generate.cpp'):
    manifest['original_sha256'][name]=hashlib.sha256((SRC/name).read_bytes()).hexdigest().upper()
for p in OUT.iterdir(): manifest['patched_sha256'][p.name]=hashlib.sha256(p.read_bytes()).hexdigest().upper()
(ROOT/'patch_identity.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest))
