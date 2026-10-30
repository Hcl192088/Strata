#define NOMINMAX
// nt1ext_check.cpp (adapted from iq_alltypes_bench.cpp) - NT1_EXT parity + timing through the real native_gu_rows.
// CPU only.  Links the NEW build's strata_kernels_cpu.lib + ggml-cpu/base.  Reads GGUF expert blobs read-only.
//   dump:  nt1ext_check dump <out.bin> <lp,lp> <GT> <nlayers> <epl> <gguf...>
//   cmp:   nt1ext_check cmp <ref.bin> <new.bin>
//   time:  nt1ext_check time <lp,lp> <reps> <GT> <nlayers> <epl> <gguf...>   (ggml loop vs native_gu_rows nt=1)
// Each LP runs on its own freshly created pinned thread (cpu_gather_fast_here / iq256_variant cache per thread).
#include "strata/kernels/cpu/native_expert.hpp"
#include "strata/kernels/cpu/iq_avx2.hpp"
#include "strata/kernels/cpu/expert_layout.hpp"
#include "ggml.h"
#include "ggml-cpu.h"
#include <windows.h>
#include <malloc.h>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <random>
#include <string>
#include <thread>
#include <vector>

namespace cpu = strata::kernels::cpu;

struct TI { std::string name; uint32_t type; uint64_t dims[4]; uint32_t nd; uint64_t off; int file; uint64_t data0; };
static std::vector<FILE*> g_files;

static uint64_t rd64(FILE* f) { uint64_t v; if (fread(&v, 8, 1, f) != 1) { fprintf(stderr, "eof\n"); exit(3); } return v; }
static uint32_t rd32(FILE* f) { uint32_t v; if (fread(&v, 4, 1, f) != 1) { fprintf(stderr, "eof\n"); exit(3); } return v; }
static std::string rdstr(FILE* f) { uint64_t n = rd64(f); std::string s(n, 0); if (n && fread(&s[0], 1, n, f) != n) exit(3); return s; }
static void skipval(FILE* f, uint32_t t) {
    static const int sz[] = {1, 1, 2, 2, 4, 4, 4, 1, 0, 0, 8, 8, 8};
    if (t == 8) { uint64_t n = rd64(f); _fseeki64(f, (long long) n, SEEK_CUR); return; }
    if (t == 9) {
        uint32_t et = rd32(f); uint64_t n = rd64(f);
        if (et == 8) { for (uint64_t i = 0; i < n; ++i) skipval(f, 8); }
        else _fseeki64(f, (long long) (n * sz[et]), SEEK_CUR);
        return;
    }
    _fseeki64(f, sz[t], SEEK_CUR);
}
static void scan(const char* path, int idx, std::vector<TI>& out) {
    FILE* f = fopen(path, "rb");
    if (!f) { fprintf(stderr, "cannot open %s\n", path); exit(2); }
    setvbuf(f, nullptr, _IOFBF, 1 << 20);
    g_files.push_back(f);
    char m[4];
    if (fread(m, 1, 4, f) != 4 || memcmp(m, "GGUF", 4)) { fprintf(stderr, "not gguf\n"); exit(2); }
    rd32(f);
    uint64_t nt = rd64(f), nkv = rd64(f);
    uint32_t align = 32;
    for (uint64_t i = 0; i < nkv; ++i) {
        std::string k = rdstr(f); uint32_t t = rd32(f);
        if (k == "general.alignment" && t == 4) align = rd32(f); else skipval(f, t);
    }
    size_t base = out.size();
    for (uint64_t i = 0; i < nt; ++i) {
        TI ti{}; ti.name = rdstr(f); ti.nd = rd32(f);
        for (uint32_t d = 0; d < ti.nd; ++d) ti.dims[d] = rd64(f);
        ti.type = rd32(f); ti.off = rd64(f); ti.file = idx; out.push_back(ti);
    }
    long long pos = _ftelli64(f);
    uint64_t d0 = ((uint64_t) pos + align - 1) / align * align;
    for (size_t i = base; i < out.size(); ++i) out[i].data0 = d0;
}
static void read_at(const TI& t, uint64_t extra, void* dst, size_t n) {
    FILE* f = g_files[t.file];
    _fseeki64(f, (long long) (t.data0 + t.off + extra), SEEK_SET);
    if (fread(dst, 1, n, f) != n) { fprintf(stderr, "short read %s\n", t.name.c_str()); exit(3); }
}
static double now_us() {
    static LARGE_INTEGER fq;
    if (!fq.QuadPart) QueryPerformanceFrequency(&fq);
    LARGE_INTEGER c; QueryPerformanceCounter(&c);
    return 1e6 * (double) c.QuadPart / (double) fq.QuadPart;
}
static double median(std::vector<double> v) { std::sort(v.begin(), v.end()); size_t n = v.size(); return n % 2 ? v[n / 2] : 0.5 * (v[n / 2 - 1] + v[n / 2]); }

struct Item { uint8_t* blob; int layer; int expert; };

static std::vector<int> parse_lps(const char* a) {
    std::vector<int> lps; std::string s = a; size_t p = 0;
    while (p < s.size()) { size_t q = s.find(',', p); if (q == std::string::npos) q = s.size(); lps.push_back(atoi(s.substr(p, q - p).c_str())); p = q + 1; }
    return lps;
}

struct Setup {
    std::vector<TI> tis; std::vector<Item> items; cpu::NativeFmt f; int H = 0, FF = 0; int GT = 0;
    std::vector<std::vector<uint8_t>> actq;   // 3 distinct activations
};

static int setup(Setup& S, int GT, int nlayers, int epl, int gfirst, int argc, char** argv) {
    S.GT = GT;
    for (int i = gfirst; i < argc; ++i) scan(argv[i], i - gfirst, S.tis);
    auto find = [&](int l, const char* role) -> const TI* {
        std::string n = "blk." + std::to_string(l) + ".ffn_" + role + "_exps.weight";
        for (auto& t : S.tis) if (t.name == n) return &t;
        return nullptr;
    };
    std::vector<int> ok;
    for (int l = 0; l < 512; ++l) {
        const TI *g = find(l, "gate"), *u = find(l, "up"), *d = find(l, "down");
        if (g && u && d && (int) g->type == GT && (int) u->type == GT) ok.push_back(l);
    }
    if (ok.empty()) { printf("no layers of type %d\n", GT); return 4; }
    std::vector<int> chosen;
    { size_t n = std::min<size_t>(nlayers, ok.size()); for (size_t i = 0; i < n; ++i) chosen.push_back(ok[i * ok.size() / n + ok.size() / (2 * n)]); }
    std::string err;
    {
        const TI* g = find(chosen[0], "gate"); const TI* d = find(chosen[0], "down");
        if (!cpu::native_fmt((int) g->type, (int) d->type, (int64_t) g->dims[0], (int64_t) g->dims[1], S.f, err)) { printf("native_fmt: %s\n", err.c_str()); return 5; }
    }
    S.H = (int) S.f.n_embd; S.FF = (int) S.f.n_ff;
    const size_t blob_bytes = 2 * S.f.up_off;
    std::vector<Item> items;
    for (int l : chosen) {
        const TI *g = find(l, "gate"), *u = find(l, "up");
        const uint64_t NE = g->dims[2];
        std::vector<int> used;
        for (int k = 0; k < epl; ++k) {
            int e = (int) ((k * 37 + 11 + l * 5) % NE);
            while (std::find(used.begin(), used.end(), e) != used.end()) e = (e + 1) % (int) NE;
            used.push_back(e);
            uint8_t* b = (uint8_t*) _aligned_malloc(blob_bytes, 64);
            read_at(*g, (uint64_t) e * S.f.up_off, b, S.f.up_off);
            read_at(*u, (uint64_t) e * S.f.up_off, b + S.f.up_off, S.f.up_off);
            items.push_back({b, l, e});
        }
    }
    for (int k = 0; k < epl; ++k) for (size_t c = 0; c < chosen.size(); ++c) S.items.push_back(items[c * epl + k]);
    std::mt19937 rng(12345); std::normal_distribution<float> nd(0.f, 1.f);
    for (int t = 0; t < 3; ++t) {
        std::vector<float> x(S.H); for (auto& v : x) v = nd(rng);
        S.actq.emplace_back(S.f.act_bytes + 64);
        cpu::native_quant_act(S.f, x.data(), S.actq.back().data());
    }
    printf("type %d: layers", GT); for (int l : chosen) printf(" %d", l);
    printf("; H=%d FF=%d items=%zu blob=%.2f MB\n", S.H, S.FF, S.items.size(), blob_bytes / 1e6);
    return 0;
}

static void pin(int lp) {
    SetThreadAffinityMask(GetCurrentThread(), (DWORD_PTR) 1 << lp);
    Sleep(20);
}

int main(int argc, char** argv) {
    setvbuf(stdout, nullptr, _IONBF, 0);
    SetPriorityClass(GetCurrentProcess(), BELOW_NORMAL_PRIORITY_CLASS);
    if (argc >= 4 && !strcmp(argv[1], "cmp")) {
        FILE *a = fopen(argv[2], "rb"), *b = fopen(argv[3], "rb");
        if (!a || !b) { printf("cannot open\n"); return 2; }
        int hdr[4], hdr2[4];
        if (fread(hdr, 4, 4, a) != 4 || fread(hdr2, 4, 4, b) != 4 || memcmp(hdr, hdr2, 16)) { printf("header mismatch\n"); return 2; }
        const int GT = hdr[0], NI = hdr[1], FF = hdr[2], nl = hdr[3];
        std::vector<int> lps(nl);
        fread(lps.data(), 4, nl, a); fread(lps.data(), 4, nl, b);
        for (int li = 0; li < nl; ++li) {
            int hf; fread(&hf, 4, 1, a); fread(&hf, 4, 1, b);   // gather_fast_here flag of the dump thread
            for (int nt = 1; nt <= 3; ++nt) {
                size_t n = (size_t) NI * nt * FF;
                std::vector<float> ra(n), rb(n);
                fread(ra.data(), 4, n, a); fread(rb.data(), 4, n, b);
                double mx = 0, ma = 0, mr = 0; size_t nd2 = 0; bool fin = true;
                for (size_t i = 0; i < n; ++i) {
                    if (!std::isfinite(ra[i]) || !std::isfinite(rb[i])) fin = false;
                    mx = std::max(mx, (double) std::fabs(ra[i]));
                    double d = std::fabs((double) ra[i] - rb[i]);
                    if (memcmp(&ra[i], &rb[i], 4) != 0) ++nd2;
                    ma = std::max(ma, d);
                    mr = std::max(mr, d / (std::fabs((double) ra[i]) + 1e-6));
                }
                printf("PARITY type=%d lp=%d core=%s nt=%d bitwise=%s differing=%zu/%zu max_abs=%.3e max_abs/max|ref|=%.3e max_rel=%.3e max|ref|=%.4g finite=%s\n", GT, lps[li],
                       hf ? "P" : "E", nt, nd2 == 0 ? "YES" : "NO", nd2, n, ma, mx > 0 ? ma / mx : 0.0, mr, mx, fin ? "YES" : "NO");
            }
        }
        return 0;
    }
    if (argc >= 8 && !strcmp(argv[1], "dump")) {
        const char* outp = argv[2]; auto lps = parse_lps(argv[3]);
        const int GT = atoi(argv[4]), nlayers = atoi(argv[5]), epl = atoi(argv[6]);
        Setup S; if (int rc = setup(S, GT, nlayers, epl, 7, argc, argv)) return rc;
        FILE* o = fopen(outp, "wb");
        const int NI = (int) S.items.size();
        int hdr[4] = {GT, NI, S.FF, (int) lps.size()};
        fwrite(hdr, 4, 4, o); fwrite(lps.data(), 4, lps.size(), o);
        for (int lp : lps) {
            std::vector<float> res[3];
            int hf = -1;
            std::thread th([&] {
                pin(lp);
                hf = cpu::cpu_gather_fast_here() ? 1 : 0;
                for (int nt = 1; nt <= 3; ++nt) {
                    res[nt - 1].assign((size_t) NI * nt * S.FF, 0.f);
                    const void* act[3] = {S.actq[0].data(), S.actq[1].data(), S.actq[2].data()};
                    for (int i = 0; i < NI; ++i) {
                        float* ffp[3];
                        for (int t = 0; t < nt; ++t) ffp[t] = &res[nt - 1][((size_t) i * nt + t) * S.FF];
                        cpu::native_gu_rows(S.f, S.items[i].blob, act, nt, ffp, 0, S.FF);
                    }
                }
            });
            th.join();
            fwrite(&hf, 4, 1, o);
            for (int nt = 1; nt <= 3; ++nt) fwrite(res[nt - 1].data(), 4, res[nt - 1].size(), o);
            printf("dumped lp=%d core=%s\n", lp, hf ? "P" : "E");
        }
        fclose(o);
        return 0;
    }
    if (argc >= 8 && !strcmp(argv[1], "time")) {
        auto lps = parse_lps(argv[2]);
        const int reps = atoi(argv[3]), GT = atoi(argv[4]), nlayers = atoi(argv[5]), epl = atoi(argv[6]);
        Setup S; if (int rc = setup(S, GT, nlayers, epl, 7, argc, argv)) return rc;
        const int NI = (int) S.items.size();
        const ggml_vec_dot_t dot = ggml_get_type_traits_cpu((ggml_type) S.f.gu_type)->vec_dot;
        for (int lp : lps) {
            std::thread th([&] {
                pin(lp);
                const int hf = cpu::cpu_gather_fast_here() ? 1 : 0;
                std::vector<float> out(S.FF);
                const void* act[1] = {S.actq[0].data()};
                auto run_g = [&](const uint8_t* blob) {   // the old (ggml) path, as native_gu_rows' fallback loop
                    for (int r = 0; r < S.FF; ++r) {
                        const uint8_t* gr = blob + (size_t) r * S.f.gu_row;
                        const uint8_t* ur = blob + S.f.up_off + (size_t) r * S.f.gu_row;
                        float g = 0.f, u = 0.f;
                        dot(S.H, &g, 0, gr, 0, act[0], 0, 1);
                        dot(S.H, &u, 0, ur, 0, act[0], 0, 1);
                        out[r] = (g / (1.f + std::exp(-g))) * u;
                    }
                };
                auto run_n = [&](const uint8_t* blob) { float* ffp[1] = {out.data()}; cpu::native_gu_rows(S.f, blob, act, 1, ffp, 0, S.FF); };
                auto pass = [&](int a) {
                    double t0 = now_us();
                    for (int i = 0; i < NI; ++i) { if (a == 0) run_g(S.items[i].blob); else run_n(S.items[i].blob); }
                    return (now_us() - t0) / NI;
                };
                for (int w = 0; w < 2; ++w) { pass(0); pass(1); }
                std::vector<double> t[2];
                for (int r = 0; r < reps; ++r) for (int a = 0; a < 2; ++a) t[a].push_back(pass(a));
                const double mg = median(t[0]), mn = median(t[1]);
                printf("TIME type=%d lp=%d core=%s ggml_median_us=%.2f native_gu_rows_median_us=%.2f speedup=%.3f (reps=%d)\n", GT, lp, hf ? "P" : "E", mg, mn, mg / mn, reps);
            });
            th.join();
        }
        return 0;
    }
    fprintf(stderr, "usage: see header\n");
    return 2;
}
