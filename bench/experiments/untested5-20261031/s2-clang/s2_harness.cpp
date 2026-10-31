#define NOMINMAX
// iq3_nt1_bench.cpp - IQ3_NT1_MICROBENCH: single-thread nt=1 gate/up kernel microbench on real IQ3_XXS GGUF rows.
// CPU only (no CUDA, no strata gguf reader: minimal GGUF v3 scanner here).  Links strata_kernels_cpu.lib + ggml-cpu/base.
//   iq3_nt1_bench <lp,lp,..> <reps> <nlayers> <experts_per_layer> <gguf1> [gguf2 ...]
#include "strata/kernels/cpu/native_expert.hpp"
#include "strata/kernels/cpu/iq_avx2.hpp"
#include "ggml.h"
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
static double pct(std::vector<double> v, double p) {
    std::sort(v.begin(), v.end());
    double x = p * (v.size() - 1); size_t i = (size_t) x; double fr = x - i;
    return i + 1 < v.size() ? v[i] * (1 - fr) + v[i + 1] * fr : v[i];
}

struct Item { uint8_t* blob; int layer; int expert; cpu::NativeFmt fmt; };

int main(int argc, char** argv) {
    setvbuf(stdout, nullptr, _IONBF, 0);
    if (argc < 7) { fprintf(stderr, "usage: <lp,lp> <reps> <nlayers> <experts_per_layer> <gguf...>\n"); return 2; }
    std::vector<int> lps;
    { std::string s = argv[1]; size_t p = 0; while (p < s.size()) { size_t q = s.find(',', p); if (q == std::string::npos) q = s.size(); lps.push_back(atoi(s.substr(p, q - p).c_str())); p = q + 1; } }
    const int reps = atoi(argv[2]), nlayers = atoi(argv[3]), epl = atoi(argv[4]);
    std::vector<TI> tis;
    const int GT = atoi(argv[5]); for (int i = 6; i < argc; ++i) scan(argv[i], i - 6, tis);
    auto find = [&](int l, const char* role) -> const TI* {
        std::string n = "blk." + std::to_string(l) + ".ffn_" + role + "_exps.weight";
        for (auto& t : tis) if (t.name == n) return &t;
        return nullptr;
    };
    auto envs = [](const char* k) { const char* v = getenv(k); return v ? v : "(unset)"; };
    printf("env STRATA_IQ_MT_MIN=%s STRATA_IQ3S_MT1=%s STRATA_NO_IQ256=%s STRATA_IQ256_GATHER=%s STRATA_NO_AVXVNNI=%s\n",
           envs("STRATA_IQ_MT_MIN"), envs("STRATA_IQ3S_MT1"), envs("STRATA_NO_IQ256"), envs("STRATA_IQ256_GATHER"), envs("STRATA_NO_AVXVNNI"));
    printf("iq256_variants()=%d (1=gather, 2=vnni); STRATA_AVXVNNI=1 compiled into iq_avx2.cpp.obj per build.make\n", cpu::iq256_variants());
    std::vector<int> t18;
    printf("layer survey (gate/up/down type):\n");
    int nlay_seen = 0;
    for (int l = 0; l < 512; ++l) {
        const TI *g = find(l, "gate"), *u = find(l, "up"), *d = find(l, "down");
        if (!g) continue;
        ++nlay_seen;
        printf("  L%-3d gate=%s up=%s down=%s dims=[%llu,%llu,%llu]%s\n", l, ggml_type_name((ggml_type) g->type),
               u ? ggml_type_name((ggml_type) u->type) : "-", d ? ggml_type_name((ggml_type) d->type) : "-",
               (unsigned long long) g->dims[0], (unsigned long long) g->dims[1], (unsigned long long) g->dims[2],
               ((int) g->type == GT && u && (int) u->type == GT) ? " [T18]" : "");
        if ((int) g->type == GT && u && (int) u->type == GT && d && (!getenv("S2_DOWN_TYPE") || strcmp(ggml_type_name((ggml_type)d->type), getenv("S2_DOWN_TYPE")) == 0)) t18.push_back(l);
    }
    printf("MoE layers seen=%d, gate&up type18 layers=%zu\n", nlay_seen, t18.size());
    if (t18.empty()) { printf("no type-18 layers\n"); return 4; }
    std::vector<int> chosen;
    { size_t n = std::min<size_t>(nlayers, t18.size()); for (size_t i = 0; i < n; ++i) chosen.push_back(t18[i * t18.size() / n + t18.size() / (2 * n)]); }
    printf("chosen layers:"); for (int l : chosen) printf(" %d", l); printf("\n");
    cpu::NativeFmt f; std::string err;
    {
        const TI* g = find(chosen[0], "gate"); const TI* d = find(chosen[0], "down");
        if (!cpu::native_fmt((int) g->type, (int) d->type, (int64_t) g->dims[0], (int64_t) g->dims[1], f, err)) { printf("native_fmt: %s\n", err.c_str()); return 5; }
    }
    const int H = (int) f.n_embd, FF = (int) f.n_ff;
    const size_t blob_bytes = f.bytes;
    printf("H=%d FF=%d gu_row=%zu B, expert gate+up=%.3f MB, set=%d experts = %.1f MB\n", H, FF, f.gu_row, blob_bytes / 1e6,
           (int) chosen.size() * epl, chosen.size() * epl * blob_bytes / 1e6);
    std::vector<Item> items;
    for (int l : chosen) {
        const TI *g = find(l, "gate"), *u = find(l, "up"), *d = find(l, "down");
        cpu::NativeFmt lf; if (!cpu::native_fmt((int)g->type, (int)d->type, (int64_t)g->dims[0], (int64_t)g->dims[1], lf, err)) return 5;
        const uint64_t NE = g->dims[2];
        std::vector<int> used;
        for (int k = 0; k < epl; ++k) {
            int e = (int) ((k * 37 + 11 + l * 5) % NE);
            while (std::find(used.begin(), used.end(), e) != used.end()) e = (e + 1) % (int) NE;
            used.push_back(e);
            uint8_t* b = (uint8_t*) _aligned_malloc(lf.bytes, 64);
            read_at(*g, (uint64_t) e * lf.up_off, b, lf.up_off);
            read_at(*u, (uint64_t) e * lf.up_off, b + lf.up_off, lf.up_off);
            read_at(*d, (uint64_t) e * lf.d_row * H, b + lf.down_off, lf.d_row * H);
            items.push_back({b, l, e, lf});
        }
    }
    {   // interleave layers
        std::vector<Item> ord;
        for (int k = 0; k < epl; ++k) for (size_t c = 0; c < chosen.size(); ++c) ord.push_back(items[c * epl + k]);
        items = ord;
    }
    const int NI = (int) items.size();
    std::mt19937 rng(12345); std::normal_distribution<float> nd(0.f, 1.f);
    const int nt = getenv("S2_NT") ? atoi(getenv("S2_NT")) : 1;
    const bool down = getenv("S2_DOWN") && atoi(getenv("S2_DOWN"));
    if (nt < 1 || nt > 3 || (down && nt != 1)) return 6;
    std::vector<std::vector<float>> x(nt, std::vector<float>(down ? FF : H));
    std::vector<std::vector<uint8_t>> acts(nt, std::vector<uint8_t>((down ? f.h_bytes : f.act_bytes) + 64));
    std::vector<std::vector<float>> outputs(nt, std::vector<float>(down ? H : FF));
    const void* ap[3]; float* op[3];
    for (int t=0; t<nt; ++t) {
        for (auto& v : x[t]) v = nd(rng);
        if (down) cpu::native_quant_h(f, x[t].data(), acts[t].data());
        else cpu::native_quant_act(f, x[t].data(), acts[t].data());
        ap[t]=acts[t].data(); op[t]=outputs[t].data();
    }
    auto run = [&](int i) {
        if (down) cpu::native_down_rows(items[i].fmt, items[i].blob, ap, nt, op, 0, H);
        else cpu::native_gu_rows(items[i].fmt, items[i].blob, ap, nt, op, 0, FF);
    };
    const char* dump = getenv("S2_OUTPUT");
    if (dump) {
        FILE* fo=fopen(dump,"wb"); if (!fo) return 7;
        for (int i=0; i<NI; ++i) { run(i); for (int t=0; t<nt; ++t) fwrite(outputs[t].data(), sizeof(float), outputs[t].size(), fo); }
        fclose(fo);
    }
    for (int lp : lps) {
        if (!SetThreadAffinityMask(GetCurrentThread(), (DWORD_PTR)1 << lp)) return 8;
        SetThreadPriority(GetCurrentThread(), THREAD_PRIORITY_BELOW_NORMAL);
        for (int r=0; r<reps; ++r) {
            double start=now_us(); for (int i=0; i<NI; ++i) run(i);
            printf("RAW lp=%d type=%d down_type=%d nt=%d down=%d rep=%d us_per_expert=%.6f\n",lp,GT,f.d_type,nt,down,r,(now_us()-start)/NI);
        }
    }
    return 0;
}
