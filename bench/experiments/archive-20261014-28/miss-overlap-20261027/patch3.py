"""Candidate patch 3 (2026-10-27): STRATA_MISS_OVERLAP=1 -- start the CPU experts that need no SSD read while the missing ones are read.
STRATA_MISS_OVERLAP_CHECK=1 (implies the overlap path): after every split call, recompute the CPU rows in one batch (the original
way) into a scratch buffer and memcmp them with the rows the overlap path wrote.  Run from the 'new' directory (orig copied there)."""

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
    assert s.count(old) == 1, (s.count(old), old[:80])
    return s.replace(old, new)

def f_hpp(s):
    s = once(s, "    void prefetch(int64_t layer, const int64_t* experts, int64_t n) override;\n", """    void prefetch(int64_t layer, const int64_t* experts, int64_t n) override;
    /// STRATA_MISS_OVERLAP: `prefetch` in two halves (unbuffered reads only).  `prefetch_split_begin` claims the stage buffers of the
    /// blobs that have to come from the drive and keeps that batch; `pending` receives their expert ids.  False: not applicable
    /// (nothing was claimed; call `prefetch`).  `prefetch_split_run` reads the kept batch - on any thread, while `blob()` of
    /// experts that are not pending is called on another.
    bool prefetch_split_begin(int64_t layer, const int64_t* experts, int64_t n, int32_t* pending, int& npending);
    void prefetch_split_run();
""")
    s = once(s, "    void fill_many(const std::vector<Fill>& todo);\n", """    void fill_many(const std::vector<Fill>& todo);
    std::vector<Fill> split_todo_;   ///< prefetch_split_begin's batch
""")
    return s
rw('include/strata/core/expert_source.hpp', f_hpp)

HELPER = r'''namespace {
// STRATA_MISS_OVERLAP: one helper thread that reads a layer's missing experts from the drive (prefetch_split_run) while the pool
// computes the experts that need no read.  After a job it spins (like the pool's parked workers, whose condition-variable wake-ups
// were measured to be late) and sleeps once idle for STRATA_MISS_OVERLAP_SPIN_US (default 20 ms).
class MissIo {
public:
    static MissIo& get() { static MissIo* m = new MissIo(); return *m; }   // never destroyed: the thread is detached
    void start(FileExpertSource* fs) {
        done_.store(false, std::memory_order_relaxed);
        req_.store(fs, std::memory_order_seq_cst);
        if (sleeping_.load(std::memory_order_seq_cst)) {
            std::lock_guard<std::mutex> lk(mu_);
            cv_.notify_one();
        }
    }
    void wait() {
        uint32_t spins = 0;
        std::chrono::steady_clock::time_point t0{};
        while (!done_.load(std::memory_order_acquire)) {
            _mm_pause();
            if ((++spins & 0xffffu) != 0) continue;
            const auto now = std::chrono::steady_clock::now();
            if (spins == 0x10000u) t0 = now;
            else if (now - t0 > std::chrono::seconds(120)) {
                std::fprintf(stderr, "strata: MISS_OVERLAP: the read helper did not finish in 120 s\n");
                std::fflush(stderr);
                std::abort();
            }
        }
    }
    double read_ms() const { return (double) read_us_.load(std::memory_order_relaxed) / 1000.0; }
private:
    MissIo() {
        const char* v = std::getenv("STRATA_MISS_OVERLAP_SPIN_US");
        spin_ = std::chrono::microseconds(v != nullptr ? std::atoll(v) : 20000);
        std::thread([this] { loop(); }).detach();
    }
    void loop() {
        for (;;) {
            FileExpertSource* fs = nullptr;
            const auto idle = std::chrono::steady_clock::now();
            uint32_t spins = 0;
            while ((fs = req_.load(std::memory_order_acquire)) == nullptr) {
                _mm_pause();
                if ((++spins & 1023u) != 0) continue;
                if (std::chrono::steady_clock::now() - idle < spin_) continue;
                std::unique_lock<std::mutex> lk(mu_);
                sleeping_.store(true, std::memory_order_seq_cst);
                cv_.wait(lk, [&] { return req_.load(std::memory_order_seq_cst) != nullptr; });
                sleeping_.store(false, std::memory_order_relaxed);
            }
            const auto t0 = std::chrono::steady_clock::now();
            fs->prefetch_split_run();
            read_us_.fetch_add((uint64_t) std::chrono::duration<double, std::micro>(std::chrono::steady_clock::now() - t0).count(),
                               std::memory_order_relaxed);
            req_.store(nullptr, std::memory_order_release);
            done_.store(true, std::memory_order_release);
        }
    }
    std::atomic<FileExpertSource*> req_{nullptr};
    std::atomic<bool> done_{true};
    std::atomic<bool> sleeping_{false};
    std::atomic<uint64_t> read_us_{0};
    std::mutex mu_;
    std::condition_variable cv_;
    std::chrono::microseconds spin_{20000};
};
// waits for the helper on every way out of the dispatch
struct MissIoJoin {
    bool armed = false;
    void join() { if (armed) { MissIo::get().wait(); armed = false; } }
    ~MissIoJoin() { join(); }
};
struct MissStats {
    unsigned long long split = 0, inline_reads = 0, chk_rows = 0, chk_bad = 0;
    double join_ms = 0, over_ms = 0;
    void print(const char* why) const {
        std::fprintf(stderr, "MISS_OVERLAP %s: split_calls=%llu inline_reads=%llu helper_read_ms=%.1f compute_while_read_ms=%.1f join_wait_ms=%.1f "
                     "check_rows=%llu check_mismatch_rows=%llu\n", why, split, inline_reads, MissIo::get().read_ms(), over_ms, join_ms, chk_rows, chk_bad);
        std::fflush(stderr);
    }
};
MissStats g_miss_stats;
}  // namespace

void expert_pool_dispatch_multi(ExpertDispatch& d, const float* x_f, const int32_t* ids, int64_t n_tok, int64_t k,
'''

def f_cpp(s):
    s = once(s, "#include <deque>\n", "#include <condition_variable>\n#include <deque>\n#include <immintrin.h>\n")
    s = once(s, "void FileExpertSource::prefetch_pairs(const std::pair<int32_t, int32_t>* pairs, int64_t n) {\n", r'''bool FileExpertSource::prefetch_split_begin(int64_t layer, const int64_t* experts, int64_t n, int32_t* pending, int& npending) {
    npending = 0;
    split_todo_.clear();
    if (!staged() || direct_.empty() || io_pf_ || n <= 0 || layer < 0 || layer >= n_layers_) return false;   // the unbuffered path only
    std::lock_guard<std::mutex> lk(stage_mu_);
    for (int64_t i = 0; i < n; ++i) {   // the claim half of prefetch(), unchanged
        const int64_t e = experts[i];
        if (e < 0 || e >= n_expert_) continue;
        const size_t index = (size_t) layer * (size_t) n_expert_ + (size_t) e;
        if (complement_ready_ && resident_blob(index) != nullptr)
            continue;                                     // in the RAM copy
        if (!override_.empty() && override_[index] != nullptr) continue;
        size_t v = 0;
        bool fill = false;
        if (!claim_stage(layer * n_expert_ + e, v, fill) && fill) {
            split_todo_.push_back({v, layer, e, stage_buf_[v].get()});
            if (warm_stamp_) {
                const uint32_t st = warm_stamp_[index].load(std::memory_order_relaxed);
                if (st != 0 && (uint64_t) st + 3 >= epoch_ + 1) warm_hits_.fetch_add(1, std::memory_order_relaxed);
            }
        }
    }
    for (const Fill& f : split_todo_) pending[npending++] = (int32_t) f.e;
    return true;
}

void FileExpertSource::prefetch_split_run() { fill_many(split_todo_); }

void FileExpertSource::prefetch_pairs(const std::pair<int32_t, int32_t>* pairs, int64_t n) {
''')
    s = once(s, "void expert_pool_dispatch_multi(ExpertDispatch& d, const float* x_f, const int32_t* ids, int64_t n_tok, int64_t k,\n", HELPER)
    # (a) the prefetch
    s = once(s, """    if (any_cpu) {   // CS-T: the experts the CPU computes, fetched together (the GGUF in place reads them on several threads)
        static thread_local std::vector<int64_t> miss;
        miss.clear();
        for (int64_t i = 0; i < n_tok * k; ++i)
            if (kind[i] == -1 && ids[i] >= 0 && ids[i] < d.n_expert &&
                std::find(miss.begin(), miss.end(), (int64_t) ids[i]) == miss.end())
                miss.push_back(ids[i]);
        d.src->prefetch(d.layers, miss.data(), (int64_t) miss.size());
    }
    int njobs = 0;
    for (int64_t t = 0; t < n_tok; ++t)
        for (int64_t j = 0; j < k; ++j) {
            const int64_t i = t * k + j;
            const int64_t e = ids[i];
            float* row = out + (size_t) i * H;
""", """    // STRATA_MISS_OVERLAP=1: the CPU experts that need no read run while the missing ones are read (output unchanged: only when each
    // expert's job starts differs).  STRATA_MISS_OVERLAP_CHECK=1: the same, and every split call is recomputed the original way and compared.
    static const int mo_mode = [] {
        const char* c = std::getenv("STRATA_MISS_OVERLAP_CHECK");
        if (c != nullptr && std::atoi(c) != 0) return 2;
        const char* v = std::getenv("STRATA_MISS_OVERLAP");
        return (v != nullptr && std::atoi(v) != 0) ? 1 : 0;
    }();
    FileExpertSource* mo_fs = nullptr;
    int32_t mo_pending[kMaxWindowEntries];
    int mo_npend = 0;
    bool mo_split = false;
    MissIoJoin mo_join;
    if (any_cpu) {   // CS-T: the experts the CPU computes, fetched together (the GGUF in place reads them on several threads)
        static thread_local std::vector<int64_t> miss;
        miss.clear();
        for (int64_t i = 0; i < n_tok * k; ++i)
            if (kind[i] == -1 && ids[i] >= 0 && ids[i] < d.n_expert &&
                std::find(miss.begin(), miss.end(), (int64_t) ids[i]) == miss.end())
                miss.push_back(ids[i]);
        if (mo_mode != 0 && (mo_fs = dynamic_cast<FileExpertSource*>(d.src)) != nullptr &&
            mo_fs->prefetch_split_begin(d.layers, miss.data(), (int64_t) miss.size(), mo_pending, mo_npend)) {
            if (mo_npend > 0) {
                bool ready = false;   // is there a CPU expert that needs no read?
                for (int64_t i = 0; i < n_tok * k && !ready; ++i)
                    if (kind[i] == -1 && ids[i] >= 0 && ids[i] < d.n_expert) {
                        bool pend = false;
                        for (int q = 0; q < mo_npend; ++q)
                            if (mo_pending[q] == ids[i]) { pend = true; break; }
                        ready = !pend;
                    }
                if (ready) {
                    mo_split = true;
                    mo_join.armed = true;
                    MissIo::get().start(mo_fs);
                } else {
                    mo_fs->prefetch_split_run();   // nothing to overlap with: read here, as prefetch() does
                    ++g_miss_stats.inline_reads;
                }
            }
        } else {
            d.src->prefetch(d.layers, miss.data(), (int64_t) miss.size());
        }
    }
    auto mo_is_pending = [&](int64_t e) {
        for (int q = 0; q < mo_npend; ++q)
            if (mo_pending[q] == e) return true;
        return false;
    };
    int njobs = 0, njobs1 = 0;
    double mo_ms = 0.0;
    for (int pass = 0; pass < (mo_split ? 2 : 1); ++pass) {
      if (pass == 1) {   // the experts that needed no read are done first, while the helper reads the rest
        const auto ra = std::chrono::steady_clock::now();
        if (njobs > 0) {
            if (native) d.pool->run_split_multi_native(lay.fmt[(size_t) d.layers], d.jobs_multi.data(), njobs);
            else d.pool->run_split_multi(d.jobs_multi.data(), njobs);
        }
        const auto rb = std::chrono::steady_clock::now();
        mo_join.join();
        const auto rc = std::chrono::steady_clock::now();
        njobs1 = njobs;
        g_miss_stats.over_ms += std::chrono::duration<double, std::milli>(rb - ra).count();
        g_miss_stats.join_ms += std::chrono::duration<double, std::milli>(rc - rb).count();
        mo_ms = std::chrono::duration<double, std::milli>(rc - ra).count();
      }
    for (int64_t t = 0; t < n_tok; ++t)
        for (int64_t j = 0; j < k; ++j) {
            const int64_t i = t * k + j;
            const int64_t e = ids[i];
            if (mo_split && ((kind[i] == -1 && mo_is_pending(e)) != (pass == 1))) continue;   // pass 0: no read needed; pass 1: read
            float* row = out + (size_t) i * H;
""")
    s = once(s, """            ++jb.nt;
            ++d.multi_entries;
        }
    const auto c3 = std::chrono::steady_clock::now();
    pt("run", njobs);
    if (njobs > 0) {
        if (native) d.pool->run_split_multi_native(lay.fmt[(size_t) d.layers], d.jobs_multi.data(), njobs);
        else d.pool->run_split_multi(d.jobs_multi.data(), njobs);
    }
""", """            ++jb.nt;
            ++d.multi_entries;
        }
    }
    const auto c3 = std::chrono::steady_clock::now();
    pt("run", njobs);
    if (njobs > njobs1) {   // njobs1 is 0 unless the overlap split the batch: then these are the experts that were read
        if (native) d.pool->run_split_multi_native(lay.fmt[(size_t) d.layers], d.jobs_multi.data() + njobs1, njobs - njobs1);
        else d.pool->run_split_multi(d.jobs_multi.data() + njobs1, njobs - njobs1);
    }
    mo_join.join();
""")
    s = once(s, """    if (auto* file_source = dynamic_cast<FileExpertSource*>(d.src))
        file_source->ram_lru_complete(d.layers, ids, kind, n_tok * k, d.host_res, d.job_of.data(), d.jobs_multi.data());
""", """    if (mo_split) {
        ++g_miss_stats.split;
        if (mo_mode == 2) {   // STRATA_MISS_OVERLAP_CHECK: the CPU rows again, in ONE batch in the original job order, into scratch rows
            static thread_local std::vector<float> chk;
            static thread_local std::vector<ExpertJobMulti> cj;
            static thread_local std::vector<int> cmap;
            chk.assign((size_t) n * (size_t) H, 0.0f);
            cj.clear();
            cmap.assign((size_t) njobs, -1);
            for (int64_t t = 0; t < n_tok; ++t)
                for (int64_t j = 0; j < k; ++j) {
                    const int64_t i = t * k + j;
                    if (kind[i] != -1) continue;
                    const int jo = d.job_of[(size_t) ids[i]];
                    if (cmap[(size_t) jo] < 0) {
                        cmap[(size_t) jo] = (int) cj.size();
                        cj.emplace_back();
                        cj.back().blob = d.jobs_multi[(size_t) jo].blob;
                        cj.back().nt = 0;
                    }
                    ExpertJobMulti& cb = cj[(size_t) cmap[(size_t) jo]];
                    cb.act[cb.nt] = &d.act_multi[(size_t) t];
                    cb.nact[cb.nt] = native ? d.nact_multi.data() + (size_t) t * kNativeActBytes : nullptr;
                    cb.out[cb.nt] = chk.data() + (size_t) i * (size_t) H;
                    ++cb.nt;
                }
            if (!cj.empty()) {
                if (native) d.pool->run_split_multi_native(lay.fmt[(size_t) d.layers], cj.data(), (int) cj.size());
                else d.pool->run_split_multi(cj.data(), (int) cj.size());
            }
            unsigned long long bad = 0;
            for (int64_t i = 0; i < n; ++i) {
                if (kind[i] != -1) continue;
                ++g_miss_stats.chk_rows;
                if (std::memcmp(chk.data() + (size_t) i * (size_t) H, out + (size_t) i * H, (size_t) H * sizeof(float)) != 0) {
                    ++g_miss_stats.chk_bad;
                    ++bad;
                }
            }
            if (bad != 0 && g_miss_stats.chk_bad <= 20)
                std::fprintf(stderr, "MISS_OVERLAP_CHECK MISMATCH layer %lld: %llu of the CPU rows differ\\n", (long long) d.layers, bad);
        }
        if ((g_miss_stats.split & 63u) == 1) g_miss_stats.print("progress");
    }
    if (auto* file_source = dynamic_cast<FileExpertSource*>(d.src))
        file_source->ram_lru_complete(d.layers, ids, kind, n_tok * k, d.host_res, d.job_of.data(), d.jobs_multi.data());
""")
    s = once(s, "    d.ms_jobs += ms(c2, c3);\n", "    d.ms_jobs += ms(c2, c3) - mo_ms;\n")
    s = once(s, "    d.ms_run += ms(c3, c4);\n", "    d.ms_run += ms(c3, c4) + mo_ms;\n")
    return s
rw('src/core/expert_source.cpp', f_cpp)
print('patch3 applied')
