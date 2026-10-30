"""Candidate patch 2: STRATA_SSD_HIST=<file>: per (layer, expert) distinct-per-window routing counts (acc) and the part that needed an
SSD read (not in VRAM, not in the RAM tier, not skipped); dumped (cumulative, overwritten) after every request.  Run from 'new'."""

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

def f_hpp(s):
    return once(s, "extern int64_t g_ram_map_size;\n", """extern int64_t g_ram_map_size;
/// STRATA_SSD_HIST=<file>: dump the per-(layer, expert) routing/SSD-read counts (cumulative) to the file
void dump_ssd_hist();
""")
rw('include/strata/core/expert_source.hpp', f_hpp)

def f_cpp(s):
    s = once(s, "const float* g_gate_w = nullptr;\n", """const float* g_gate_w = nullptr;
namespace {
std::vector<int32_t> g_hist_acc, g_hist_ssd, g_hist_ram;
const char* ssd_hist_path() { static const char* p = std::getenv("STRATA_SSD_HIST"); return (p != nullptr && p[0] != 0) ? p : nullptr; }
}
void dump_ssd_hist() {
    const char* p = ssd_hist_path();
    if (p == nullptr || g_hist_acc.empty()) return;
    std::FILE* f = std::fopen(p, "wb");
    if (f == nullptr) return;
    std::fprintf(f, "layer expert acc ram ssd\\n");
    for (size_t i = 0; i < g_hist_acc.size(); ++i)
        if (g_hist_acc[i] != 0) std::fprintf(f, "%zu %zu %d %d %d\\n", i / 512, i % 512, g_hist_acc[i], g_hist_ram[i], g_hist_ssd[i]);
    std::fclose(f);
}
""")
    # counting hook: just before the gate block's condition
    s = once(s, "        if ((gate_tau > 0.0f || gate_count) && g_gate_w != nullptr && d.peer == nullptr && d.remote_count == 0) {\n",
"""        if (ssd_hist_path() != nullptr && d.peer == nullptr && d.remote_count == 0) {
            if (g_hist_acc.empty()) { g_hist_acc.assign(64 * 512, 0); g_hist_ssd.assign(64 * 512, 0); g_hist_ram.assign(64 * 512, 0); }
            auto* fsrc2 = dynamic_cast<FileExpertSource*>(d.src);
            for (int q = 0; q < nd; ++q) {
                const int32_t e = ids[distinct[q]];
                if (e < 0 || e >= d.n_expert || d.layers < 0 || d.layers >= 64) continue;
                const size_t at = (size_t) d.layers * 512 + (size_t) e;
                ++g_hist_acc[at];
                if (skip_d[q]) continue;
                if (d.host_res[(size_t) d.layers * (size_t) d.n_expert + (size_t) e] >= 0) continue;
                if (fsrc2 != nullptr && fsrc2->has_resident(d.layers, e)) ++g_hist_ram[at]; else ++g_hist_ssd[at];
            }
        }
        if ((gate_tau > 0.0f || gate_count) && g_gate_w != nullptr && d.peer == nullptr && d.remote_count == 0) {
""")
    return s
rw('src/core/expert_source.cpp', f_cpp)

def f_g(s):
    return once(s, "            if (drive.d.gc_miss > 0) {   // overnight 20261020", "            strata::core::dump_ssd_hist();\n            if (drive.d.gc_miss > 0) {   // overnight 20261020")
rw('src/program/generate.cpp', f_g)
print('patched2')
