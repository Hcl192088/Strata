"""Candidate patch 1 (overnight 20261020) on current-best source 61b3fb5d + RAM-LRU dirty files.
Adds (all opt-in by env, default behaviour unchanged):
  STRATA_GATE_COUNT=1       count CPU-computed misses by max routing weight (and whether the RAM tier held them); no output change
  STRATA_GATE_SKIP=tau      additionally skip (zero contribution, NO renormalisation) a missed expert whose max weight over the
                            window's tokens is < tau and that is never rank 0 (top-1) of any token
  STRATA_ROUTE_BIAS=lam     cache-conditional routing with VRAM+RAM tier bonus, unbiased top-1 always kept
                            (STRATA_ROUTE_BIAS_VRAM=x overrides the VRAM-tier bonus)
Run from the 'new' directory.
"""
import re

def rw(path, fn):
    s = open(path, newline='').read()
    crlf = '\r\n' in s
    s = s.replace('\r\n', '\n')
    s2 = fn(s)
    assert s2 != s, path
    if crlf:
        s2 = s2.replace('\n', '\r\n')
    open(path, 'w', newline='').write(s2)

def once(s, old, new):
    assert s.count(old) == 1, (s.count(old), old[:70])
    return s.replace(old, new)

# ---------------- expert_source.hpp
def f_hpp(s):
    s = once(s, "struct ExpertDispatch {\n",
"""/// overnight 20261020: the routing weights of the verify window being served (set by Verifier around the pool call, null
/// otherwise), and the host mirror of the RAM tier's residency (STRATA_ROUTE_BIAS; mapped, read by the router kernel)
extern const float* g_gate_w;
extern int32_t* g_ram_map;
extern int64_t g_ram_map_size;

struct ExpertDispatch {
""")
    s = once(s, "    int64_t tail_experts = 0;\n",
"""    int64_t tail_experts = 0;
    /// overnight 20261020 STRATA_GATE_COUNT / STRATA_GATE_SKIP: CPU-computed missed experts (distinct per window), of them
    /// not in the RAM tier (an SSD read), binned by max routing weight (edges in gate_edges), and the skipped ones
    int64_t gc_miss = 0, gc_ssd = 0, gc_bin[12] = {0}, gc_bin_ssd[12] = {0};
    int64_t gate_skip_experts = 0, gate_skip_ssd = 0, gc_rank0 = 0;
""")
    return s
rw('include/strata/core/expert_source.hpp', f_hpp)

# ---------------- expert_source.cpp
def f_cpp(s):
    s = once(s, "namespace {\n// STRATA_ROUTE_TAIL_SKIP: the rank from which",
"""const float* g_gate_w = nullptr;
int32_t* g_ram_map = nullptr;
int64_t g_ram_map_size = 0;

namespace {
// STRATA_ROUTE_TAIL_SKIP: the rank from which""")
    # gate counting/skipping after the tail skip block
    old = """        const bool pcie_ok = d.pcie_num > 0 && d.src->pcie_layer(d.layers);
        const int m = pcie_ok ? (nmiss * d.pcie_num) >> 8 : 0;"""
    new = """        // overnight 20261020: STRATA_GATE_COUNT=1 counts, STRATA_GATE_SKIP=tau skips (zero contribution, no renormalisation) the
        // missed experts whose largest routing weight over the window is < tau and that are rank 0 (top-1) of no token.
        static const float gate_tau = [] { const char* v = std::getenv("STRATA_GATE_SKIP"); return v ? (float) std::atof(v) : 0.0f; }();
        static const bool gate_count = [] { const char* v = std::getenv("STRATA_GATE_COUNT"); return v != nullptr && std::atoi(v) != 0; }();
        static const float gate_edges[11] = {0.0025f, 0.005f, 0.01f, 0.015f, 0.02f, 0.03f, 0.05f, 0.075f, 0.1f, 0.15f, 0.25f};
        if (g_ram_map != nullptr) {      // STRATA_ROUTE_BIAS: seed the mapped RAM-tier table once (ram_lru_complete keeps it current)
            static bool ram_seeded = false;
            if (!ram_seeded) {
                if (auto* fs = dynamic_cast<FileExpertSource*>(d.src)) {
                    for (int64_t l = 0; l * d.n_expert < g_ram_map_size; ++l)
                        for (int64_t e = 0; e < d.n_expert; ++e) g_ram_map[l * d.n_expert + e] = fs->has_resident(l, e) ? 1 : 0;
                    ram_seeded = true;
                }
            }
        }
        if ((gate_tau > 0.0f || gate_count) && g_gate_w != nullptr && d.peer == nullptr && d.remote_count == 0) {
            float maxw[kMaxWindowEntries];
            int minr2[kMaxWindowEntries];
            for (int q = 0; q < nd; ++q) { maxw[q] = 0.0f; minr2[q] = 99; }
            for (int64_t i = 0; i < n; ++i) {
                int q = 0;
                while (q < nd && distinct[q] != first_of[i]) ++q;
                if (q < nd) { maxw[q] = std::max(maxw[q], g_gate_w[i]); minr2[q] = std::min(minr2[q], (int) (i % k)); }
            }
            auto* fsrc = dynamic_cast<FileExpertSource*>(d.src);
            for (int q = 0; q < nd; ++q) {
                const int32_t e = ids[distinct[q]];
                if (skip_d[q] || e < 0 || e >= d.n_expert) continue;
                if (d.host_res[(size_t) d.layers * (size_t) d.n_expert + (size_t) e] >= 0) continue;   // resident in VRAM
                const bool in_ram = fsrc != nullptr && fsrc->has_resident(d.layers, e);
                int b = 0;
                while (b < 11 && maxw[q] >= gate_edges[b]) ++b;
                ++d.gc_miss; ++d.gc_bin[b];
                if (!in_ram) { ++d.gc_ssd; ++d.gc_bin_ssd[b]; }
                if (minr2[q] == 0) ++d.gc_rank0;
                if (gate_tau > 0.0f && minr2[q] > 0 && maxw[q] < gate_tau) {
                    skip_d[q] = true;
                    --nmiss;
                    ++d.gate_skip_experts;
                    if (!in_ram) ++d.gate_skip_ssd;
                }
            }
        }
        const bool pcie_ok = d.pcie_num > 0 && d.src->pcie_layer(d.layers);
        const int m = pcie_ok ? (nmiss * d.pcie_num) >> 8 : 0;"""
    s = once(s, old, new)
    # RAM map refresh at the end of ram_lru_complete
    old = """    if (layer == n_layers_ - 1 && ram_lru_clock_ % (48 * 128) == 0)
        std::fprintf(stderr, "RAM_LRU admissions"""
    new = """    if (g_ram_map != nullptr && (layer + 1) * n_expert_ <= g_ram_map_size)      // STRATA_ROUTE_BIAS: keep the mirror current
        for (int64_t e = 0; e < n_expert_; ++e) g_ram_map[(size_t) base + (size_t) e] = complement_offsets_[base + (size_t) e] != kNoComplement ? 1 : 0;
    if (layer == n_layers_ - 1 && ram_lru_clock_ % (48 * 128) == 0)
        std::fprintf(stderr, "RAM_LRU admissions"""
    s = once(s, old, new)
    return s
rw('src/core/expert_source.cpp', f_cpp)

# ---------------- verify.hpp
def f_vhpp(s):
    return once(s, "    float* h_w_ = nullptr;       float* m_w_ = nullptr;         // T * k\n",
"""    float* h_w_ = nullptr;       float* m_w_ = nullptr;         // T * k
    int32_t* h_ram_ = nullptr;   int32_t* m_ram_ = nullptr;     // overnight 20261020 STRATA_ROUTE_BIAS: RAM-tier residency [n_layers * n_expert]
""")
rw('include/strata/core/verify.hpp', f_vhpp)

# ---------------- verify.cpp
def f_v(s):
    # allocation
    s = once(s, """    if (!ok) { err = "verify: mapped staging allocation failed"; return false; }
""", """    if (!ok) { err = "verify: mapped staging allocation failed"; return false; }
    if (const char* rb = std::getenv("STRATA_ROUTE_BIAS"); rb != nullptr && std::atof(rb) > 0.0) {   // overnight 20261020
        const size_t cnt = (size_t) g.n_layers * (size_t) g.n_expert;
        if (!mapped(cnt * 4, (void**) &h_ram_, (void**) &m_ram_)) { err = "verify: RAM-tier map allocation failed"; return false; }
        std::memset(h_ram_, 0, cnt * 4);
        strata::core::g_ram_map = h_ram_;
        strata::core::g_ram_map_size = (int64_t) cnt;
    }
""")
    # route bias after route prior
    s = once(s, """        if (route_resident_cfg().margin > 0.0f && NE == 512 && K == 10 && hits_.d_res != nullptr) {
            // STRATA_ROUTE_RESIDENT: after the router""", """        // overnight 20261020 STRATA_ROUTE_BIAS=lambda: VRAM and RAM tier bonus on the selection logits, unbiased top-1 kept,
        // router weights unchanged (route_prior.cu, route_bias_k)
        static const float route_bias = [] { const char* v = std::getenv("STRATA_ROUTE_BIAS"); return v ? (float) std::atof(v) : 0.0f; }();
        static const float route_bias_vram = [] { const char* v = std::getenv("STRATA_ROUTE_BIAS_VRAM"); return v ? (float) std::atof(v) : route_bias; }();
        if (route_bias > 0.0f && NE == 512 && K == 10 && hits_.d_res != nullptr && m_ram_ != nullptr)
            route_bias_top10(logits_ + tb * NE, hits_.d_res + l * g.n_expert, m_ram_ + l * g.n_expert, route_bias_vram, route_bias,
                             ids_ + tb * K, w_ + tb * K, n, cs);
        if (route_resident_cfg().margin > 0.0f && NE == 512 && K == 10 && hits_.d_res != nullptr) {
            // STRATA_ROUTE_RESIDENT: after the router""")
    # publish with weights
    old = """                doorbell_publish_res(xm, ids_ + tb * K, layer_res, (int) g.n_expert, (int64_t) n * N, (int64_t) n * K,
                                     m_x_ + tb * N, m_ids_ + tb * K, m_seq_, cs);"""
    new = """                static const bool gate_w_on = [] {   // overnight 20261020: publish the routing weights too
                    const char* a = std::getenv("STRATA_GATE_COUNT"); const char* b = std::getenv("STRATA_GATE_SKIP");
                    return (a != nullptr && std::atoi(a) != 0) || (b != nullptr && std::atof(b) > 0.0);
                }();
                if (gate_w_on)
                    doorbell_publish_res_w(xm, ids_ + tb * K, w_ + tb * K, layer_res, (int) g.n_expert, (int64_t) n * N, (int64_t) n * K,
                                           m_x_ + tb * N, m_ids_ + tb * K, m_w_ + tb * K, m_seq_, cs);
                else
                doorbell_publish_res(xm, ids_ + tb * K, layer_res, (int) g.n_expert, (int64_t) n * N, (int64_t) n * K,
                                     m_x_ + tb * N, m_ids_ + tb * K, m_seq_, cs);"""
    s = once(s, old, new)
    # pool call sites
    s = once(s, """        if (pool != nullptr)
            pool(user, h_x_ + (size_t) tb * g.n_embd, h_ids_ + (size_t) tb * ss.k, n, ss.k,
                 h_ymiss_ + (size_t) tb * ss.k * g.n_embd, l);
        if (remote_opt_) remote_opt_->end();""", """        if (pool != nullptr) {
            strata::core::g_gate_w = h_w_ + (size_t) tb * ss.k;
            pool(user, h_x_ + (size_t) tb * g.n_embd, h_ids_ + (size_t) tb * ss.k, n, ss.k,
                 h_ymiss_ + (size_t) tb * ss.k * g.n_embd, l);
            strata::core::g_gate_w = nullptr;
        }
        if (remote_opt_) remote_opt_->end();""")
    s = once(s, "        if (pool != nullptr) pool(user, h_x_, h_ids_, S, ss_->k, h_ymiss_, l);\n",
             "        if (pool != nullptr) { strata::core::g_gate_w = h_w_; pool(user, h_x_, h_ids_, S, ss_->k, h_ymiss_, l); strata::core::g_gate_w = nullptr; }\n")
    s = once(s, "        if (pool != nullptr) pool(user, h_x_, h_ids_, S, ss_->k, h_ymiss_, lb_ + b_k_);\n",
             "        if (pool != nullptr) { strata::core::g_gate_w = h_w_; pool(user, h_x_, h_ids_, S, ss_->k, h_ymiss_, lb_ + b_k_); strata::core::g_gate_w = nullptr; }\n")
    s = once(s, """        if (pool != nullptr)
            pool(user, h_x_ + (size_t) tb * g.n_embd, h_ids_ + (size_t) tb * ss.k, n, ss.k,
                 h_ymiss_ + (size_t) tb * ss.k * g.n_embd, l);
        if (g_trace) trace_ev(*(volatile uint32_t*) h_flagA_ == want ? "SERVED" : "SERVED-NO-PLAN-YET", fl_k_, l,""",
"""        if (pool != nullptr) {
            strata::core::g_gate_w = h_w_ + (size_t) tb * ss.k;
            pool(user, h_x_ + (size_t) tb * g.n_embd, h_ids_ + (size_t) tb * ss.k, n, ss.k,
                 h_ymiss_ + (size_t) tb * ss.k * g.n_embd, l);
            strata::core::g_gate_w = nullptr;
        }
        if (g_trace) trace_ev(*(volatile uint32_t*) h_flagA_ == want ? "SERVED" : "SERVED-NO-PLAN-YET", fl_k_, l,""")
    return s
rw('src/core/verify.cpp', f_v)

# ---------------- generate.cpp (stats line)
def f_g(s):
    return once(s, """            // the resident RAM mode, cumulative: experts read from experts.bin since the copy was made (what the plain""",
"""            if (drive.d.gc_miss > 0) {   // overnight 20261020 STRATA_GATE_COUNT / STRATA_GATE_SKIP, cumulative
                std::fprintf(stderr, "strata serve: GATECOUNT misses %lld ssd %lld rank0 %lld skipped %lld skipped_ssd %lld tail_skipped %lld bins(edges .0025 .005 .01 .015 .02 .03 .05 .075 .1 .15 .25 inf)",
                             (long long) drive.d.gc_miss, (long long) drive.d.gc_ssd, (long long) drive.d.gc_rank0,
                             (long long) drive.d.gate_skip_experts, (long long) drive.d.gate_skip_ssd, (long long) drive.d.tail_experts);
                std::fprintf(stderr, " all");
                for (int b = 0; b < 12; ++b) std::fprintf(stderr, " %lld", (long long) drive.d.gc_bin[b]);
                std::fprintf(stderr, " ssd");
                for (int b = 0; b < 12; ++b) std::fprintf(stderr, " %lld", (long long) drive.d.gc_bin_ssd[b]);
                std::fprintf(stderr, "\\n");
            }
            // the resident RAM mode, cumulative: experts read from experts.bin since the copy was made (what the plain""")
rw('src/program/generate.cpp', f_g)
print('patched')
