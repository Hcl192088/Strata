#define NOMINMAX
#include "strata/kernels/cpu/native_expert.hpp"
#include "strata/kernels/cpu/iq_avx2.hpp"
#include "strata/kernels/cpu/expert_layout.hpp"
#include <windows.h>
#include <bcrypt.h>
#include <malloc.h>
#include <algorithm>
#include <array>
#include <climits>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <random>
#include <sstream>
#include <string>
#include <vector>

namespace cpu = strata::kernels::cpu;
constexpr int H = 2560, FF = 640;
static void require(bool ok, const char* message) {
    if (!ok) { std::fprintf(stderr, "FAIL %s\n", message); std::exit(3); }
}
static double now_us() {
    static LARGE_INTEGER f{};
    if (!f.QuadPart) QueryPerformanceFrequency(&f);
    LARGE_INTEGER t; QueryPerformanceCounter(&t);
    return 1e6 * double(t.QuadPart) / double(f.QuadPart);
}
static double median(std::vector<double> x) {
    std::sort(x.begin(), x.end()); return x[x.size() / 2];
}

// Provenance only. Never called inside a timed pass.
class Sha256 {
    BCRYPT_ALG_HANDLE alg_ = nullptr;
    BCRYPT_HASH_HANDLE hash_ = nullptr;
    std::vector<UCHAR> object_;
public:
    Sha256() {
        require(BCryptOpenAlgorithmProvider(&alg_, BCRYPT_SHA256_ALGORITHM, nullptr, 0) == 0,
                "sha256_provider");
        DWORD n = 0, got = 0;
        require(BCryptGetProperty(alg_, BCRYPT_OBJECT_LENGTH, (PUCHAR)&n, sizeof(n), &got, 0) == 0,
                "sha256_object_length");
        object_.resize(n);
        require(BCryptCreateHash(alg_, &hash_, object_.data(), n, nullptr, 0, 0) == 0,
                "sha256_create");
    }
    ~Sha256() { if (hash_) BCryptDestroyHash(hash_); if (alg_) BCryptCloseAlgorithmProvider(alg_, 0); }
    void add(const void* data, size_t bytes) {
        require(bytes <= ULONG_MAX, "sha256_chunk_size");
        require(BCryptHashData(hash_, (PUCHAR)data, (ULONG)bytes, 0) == 0, "sha256_update");
    }
    std::string finish() {
        UCHAR digest[32];
        require(BCryptFinishHash(hash_, digest, sizeof(digest), 0) == 0, "sha256_finish");
        static const char hex[] = "0123456789abcdef";
        std::string out(64, '0');
        for (int i = 0; i < 32; ++i) { out[2*i] = hex[digest[i] >> 4]; out[2*i+1] = hex[digest[i] & 15]; }
        return out;
    }
};
static std::string sha(const void* data, size_t bytes) { Sha256 h; h.add(data, bytes); return h.finish(); }

struct Layer { int layer, gu, down; unsigned long long offset, bytes; };
struct Item { unsigned char* blob; cpu::NativeFmt fmt; int layer, expert; unsigned long long offset; };
struct Group { int type; size_t bytes = 0, gu_bytes = 0; std::vector<Item> items; };

int main(int argc, char** argv) {
    setvbuf(stdout, nullptr, _IONBF, 0);
    require(argc == 5, "args: lp base|prefetch4096|iq2s_nt1 experts.bin native_experts.txt");
    const int lp = std::atoi(argv[1]);
    const std::string mode = argv[2];
    require(lp >= 0 && lp < 64, "lp_range");
    require(mode == "base" || mode == "prefetch4096" || mode == "iq2s_nt1", "mode");
    require(SetPriorityClass(GetCurrentProcess(), BELOW_NORMAL_PRIORITY_CLASS) != 0, "priority");
    require(GetPriorityClass(GetCurrentProcess()) == BELOW_NORMAL_PRIORITY_CLASS, "priority_readback");
    require(SetThreadAffinityMask(GetCurrentThread(), DWORD_PTR(1) << lp) != 0, "pin");
    require(GetCurrentProcessorNumber() == (DWORD)lp, "pin_readback");
    const char* mt1 = std::getenv("STRATA_IQ3S_MT1");
    require(mt1 && std::string(mt1) == "1", "original_MT1_must_be_1");
    require(std::getenv("STRATA_IQ_MT_MIN") == nullptr, "original_MT_MIN_must_be_absent");
    // Set before native_fmt, quantization, or any Strata feature/variant cache is first touched.
    if (mode == "prefetch4096") require(_putenv_s("STRATA_IQ_PREFETCH", "4096") == 0, "set_prefetch");
    const char* pf = std::getenv("STRATA_IQ_PREFETCH");
    std::printf("ENV,%s,%d,MT1=1,MT_MIN=absent,IQ_PREFETCH=%s\n", mode.c_str(), lp, pf ? pf : "unset_default2048");

    std::ifstream metadata(argv[4]);
    require(metadata.good(), "open_metadata");
    std::vector<Layer> all;
    std::string line;
    while (std::getline(metadata, line)) {
        if (line.empty() || line[0] == '#') continue;
        Layer x{}; std::istringstream s(line);
        require(bool(s >> x.layer >> x.gu >> x.down >> x.offset >> x.bytes), "metadata_row");
        all.push_back(x);
    }
    require(all.size() == 48, "actual_48_layers");
    FILE* file = std::fopen(argv[3], "rb"); require(file != nullptr, "open_native");
    std::vector<Group> groups;
    const int types[] = {16, 17, 22, 18, 21};
    size_t total_bytes = 0, total_experts = 0;
    for (int type : types) {
        if (mode == "iq2s_nt1" && type != 22) continue;
        std::vector<Layer> layers;
        for (const auto& x : all) if (x.gu == type) layers.push_back(x);
        require(layers.size() >= 6, "six_layers_per_type");
        Group group; group.type = type;
        for (int li = 0; li < 6; ++li) {
            const auto& l = layers[li * layers.size() / 6 + layers.size() / 12];
            cpu::NativeFmt fmt; std::string err;
            require(cpu::native_fmt(type, l.down, H, FF, fmt, err), "native_fmt");
            require(fmt.bytes == l.bytes, "native_geometry_bytes");
            for (int j = 0; j < 3; ++j) {
                const int expert = (11 + 37*j + 5*l.layer) % 512;
                const auto offset = l.offset + (unsigned long long)expert * l.bytes;
                auto* blob = (unsigned char*)_aligned_malloc(fmt.bytes, 64);
                require(blob != nullptr, "sample_allocation");
                require(_fseeki64(file, offset, SEEK_SET) == 0, "sample_seek");
                require(std::fread(blob, 1, fmt.bytes, file) == fmt.bytes, "sample_read");
                group.items.push_back({blob, fmt, l.layer, expert, offset});
                group.bytes += fmt.bytes; group.gu_bytes += fmt.down_off;
                std::printf("ITEM,%s,%d,%d,%d,%d,%d,%llu,%zu,%s\n", mode.c_str(), type, lp,
                            l.layer, expert, l.down, offset, fmt.bytes, sha(blob, fmt.bytes).c_str());
            }
        }
        std::vector<Item> interleaved;
        for (int j = 0; j < 3; ++j) for (int l = 0; l < 6; ++l) interleaved.push_back(group.items[l*3+j]);
        group.items = std::move(interleaved);
        require(group.items.size() == 18 && group.bytes > 20ull*1024*1024, "full_expert_working_set_over20MiB");
        total_bytes += group.bytes; total_experts += group.items.size();
        groups.push_back(std::move(group));
    }
    std::fclose(file);
    std::printf("COVER,%s,%d,%zu,%zu,%zu,%d,%d,auto_variant=%d,target_variant=%d\n", mode.c_str(), lp,
                groups.size(), total_experts, total_bytes, H, FF, cpu::iq256_variant(), cpu::kIq256Vnni);
    if (mode == "iq2s_nt1") require((cpu::iq256_variants() & cpu::kIq256Vnni) != 0, "VNNI_required_no_fallback");

    std::mt19937 gen(12345); std::normal_distribution<float> nd(0, 1);
    std::vector<float> x(3*H); for (auto& v : x) v = nd(gen);
    std::printf("INPUT_SHA256,%s,%d,%s\n", mode.c_str(), lp, sha(x.data(), x.size()*sizeof(float)).c_str());
    std::vector<unsigned char> acts(3*cpu::kNativeActBytes), hq(3*cpu::kNativeHBytes);
    std::vector<float> h(3*FF), out(3*H), ref_h(3*FF), ref_out(3*H);
    const void* ap[3]; const void* hp[3]; float* fp[3]; float* op[3];
    cpu::ActQ qa[3]; const cpu::ActQ* qap[3] = {&qa[0], &qa[1], &qa[2]};
    for (int t = 0; t < 3; ++t) {
        ap[t] = acts.data() + t*cpu::kNativeActBytes;
        hp[t] = hq.data() + t*cpu::kNativeHBytes;
        fp[t] = h.data() + t*FF; op[t] = out.data() + t*H;
    }
    for (const auto& group : groups) {
        const int type = group.type;
        const auto& fmt = group.items[0].fmt;
        std::fill(acts.begin(), acts.end(), 0);
        for (int t = 0; t < 3; ++t) cpu::native_quant_act(fmt, x.data() + t*H, (void*)ap[t]);
        std::printf("WORKING_SET,%s,%d,%d,%zu,%zu\n", mode.c_str(), type, lp, group.bytes, group.gu_bytes);
        std::printf("ACT_SHA256,%s,%d,%d,%s\n", mode.c_str(), type, lp, sha(acts.data(), acts.size()).c_str());
        auto run = [&](int arm, const Item& item, int nt, bool full) {
            if (arm == 1 && type == 22 && nt == 1) {
                cpu::iq256_gu_rows_v(cpu::kIq256Vnni, 22, item.blob, item.fmt.gu_row, item.fmt.up_off,
                                    H, ap, nt, fp, 0, FF);
            } else {
                cpu::native_gu_rows(item.fmt, item.blob, ap, nt, fp, 0, FF);
            }
            if (full) {
                if (cpu::q2_native_kernels(item.fmt.d_type)) {
                    for (int t = 0; t < nt; ++t) cpu::act_quant_any(fp[t], FF, qa[t]);
                    cpu::q2_rows_any(item.blob + item.fmt.down_off, item.fmt.d_row, FF/64, qap, nt, op, 0, H);
                } else {
                    require(item.fmt.d_type == 20, "actual_down_type20_or42");
                    for (int t = 0; t < nt; ++t) cpu::native_quant_h(item.fmt, fp[t], (void*)hp[t]);
                    cpu::native_down_rows(item.fmt, item.blob, hp, nt, op, 0, H);
                }
            }
        };
        const int arms = mode == "iq2s_nt1" ? 2 : 1;
        for (int nt = 1; nt <= 3; ++nt) {
            double max_h = 0, max_dh = 0, max_o = 0, max_do = 0;
            size_t different_h = 0, different_o = 0;
            Sha256 hh[2], oh[2];
            // Numeric/hash work is outside every timed region. For prefetch, true cross-env
            // parity is the parent's comparison of the emitted base/4096/base hashes.
            for (const auto& item : group.items) {
                run(0, item, nt, true);
                std::copy_n(h.data(), nt*FF, ref_h.data());
                std::copy_n(out.data(), nt*H, ref_out.data());
                hh[0].add(h.data(), nt*FF*sizeof(float)); oh[0].add(out.data(), nt*H*sizeof(float));
                run(arms == 2 ? 1 : 0, item, nt, true);
                hh[1].add(h.data(), nt*FF*sizeof(float)); oh[1].add(out.data(), nt*H*sizeof(float));
                for (int k = 0; k < nt*FF; ++k) {
                    require(std::isfinite(h[k]) && std::isfinite(ref_h[k]), "finite_h");
                    max_h = std::max(max_h, std::fabs(double(ref_h[k])));
                    max_dh = std::max(max_dh, std::fabs(double(h[k])-ref_h[k]));
                    if (std::memcmp(&h[k], &ref_h[k], sizeof(float))) ++different_h;
                }
                for (int k = 0; k < nt*H; ++k) {
                    require(std::isfinite(out[k]) && std::isfinite(ref_out[k]), "finite_out");
                    max_o = std::max(max_o, std::fabs(double(ref_out[k])));
                    max_do = std::max(max_do, std::fabs(double(out[k])-ref_out[k]));
                    if (std::memcmp(&out[k], &ref_out[k], sizeof(float))) ++different_o;
                }
            }
            std::printf("NUMERIC,%s,%d,%d,%d,%.9g,%.9g,%zu,%.9g,%.9g,%zu\n",
                        mode.c_str(), type, lp, nt, max_h, max_dh, different_h, max_o, max_do, different_o);
            for (int arm = 0; arm < 2; ++arm)
                std::printf("HASH,%s,%d,%d,%d,%d,%s,%s\n", mode.c_str(), type, lp, nt, arm,
                            hh[arm].finish().c_str(), oh[arm].finish().c_str());
            require(max_dh <= 1e-4*std::max(1., max_h), "h_numeric_screen_not_quality_proof");
            if (arms == 1 || nt != 1) require(different_h == 0 && different_o == 0, "unchanged_path_bitwise");
            for (int full = 0; full < 2; ++full) {
                std::vector<double> times[2];
                for (int arm = 0; arm < arms; ++arm) times[arm].reserve(5);
                for (int arm = 0; arm < arms; ++arm)
                    for (const auto& item : group.items) run(arm, item, nt, full != 0);
                for (int pass = 0; pass < 5; ++pass) for (int k = 0; k < arms; ++k) {
                    const int arm = arms == 2 && pass%2 ? 1-k : k;
                    const double t0 = now_us();
                    for (const auto& item : group.items) run(arm, item, nt, full != 0);
                    const double us = (now_us()-t0) / group.items.size();
                    times[arm].push_back(us);
                    std::printf("RAW,%s,%d,%d,%d,%d,%d,%d,%.6f\n", mode.c_str(), type, lp, nt, full, pass, arm, us);
                }
                for (int arm = 0; arm < arms; ++arm)
                    std::printf("SUM,%s,%d,%d,%d,%d,%d,%.6f\n", mode.c_str(), type, lp, nt, full, arm, median(times[arm]));
            }
        }
    }
    for (auto& group : groups) for (auto& item : group.items) _aligned_free(item.blob);
    std::printf("DONE,%s,%d\n", mode.c_str(), lp);
    return 0;
}
