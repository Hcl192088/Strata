"""Candidate patch 4 (2026-10-28), on top of patch3: STRATA_MISS_CHUNK=N (with STRATA_MISS_OVERLAP=1) -- the helper reads the missing experts in
chunks of N experts and publishes each chunk when it lands; the dispatch computes the experts of a chunk as soon as it has landed, instead of
joining on the whole batch.  N unset/0: patch3 exactly.  Same rows, same job grouping per expert: only when each expert's job starts differs.
Run from the 'new' directory (orig, i.e. the patch3 source, copied there)."""

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
    s = once(s, "    void prefetch_split_run();\n", r'''    void prefetch_split_run();
    /// STRATA_MISS_CHUNK: the same batch read `chunk` blobs at a time; `landed` is set (release) to the number of chunks whose blobs are all
    /// published after each one.
    void prefetch_split_run_chunked(size_t chunk, std::atomic<int>& landed);
''')
    s = once(s, "    std::vector<Fill> split_todo_;   ///< prefetch_split_begin's batch\n", """    std::vector<Fill> split_todo_;   ///< prefetch_split_begin's batch
    std::vector<Fill> split_chunk_;  ///< prefetch_split_run_chunked's current chunk (helper thread only)
""")
    return s
rw('include/strata/core/expert_source.hpp', f_hpp)

def f_cpp(s):
    s = once(s, "void FileExpertSource::prefetch_split_run() { fill_many(split_todo_); }\n", r'''void FileExpertSource::prefetch_split_run() { fill_many(split_todo_); }

void FileExpertSource::prefetch_split_run_chunked(size_t chunk, std::atomic<int>& landed) {
    int c = 0;
    for (size_t at = 0; at < split_todo_.size(); at += chunk) {
        split_chunk_.assign(split_todo_.begin() + (std::ptrdiff_t) at,
                            split_todo_.begin() + (std::ptrdiff_t) std::min(split_todo_.size(), at + chunk));
        fill_many(split_chunk_);   // overlapped direct reads, merged within the chunk; every blob's publish_stage has run when it returns
        landed.store(++c, std::memory_order_release);
    }
}
''')
    # MissIo: chunk size and landed counter
    s = once(s, """    void start(FileExpertSource* fs) {
        done_.store(false, std::memory_order_relaxed);
""", """    void start(FileExpertSource* fs, int chunk) {
        chunk_ = chunk;
        landed_.store(0, std::memory_order_relaxed);
        done_.store(false, std::memory_order_relaxed);
""")
    s = once(s, "    double read_ms() const { return (double) read_us_.load(std::memory_order_relaxed) / 1000.0; }\n", r'''    // STRATA_MISS_CHUNK: waits until the helper has published `n` chunks (or is done)
    void wait_chunk(int n) {
        uint32_t spins = 0;
        std::chrono::steady_clock::time_point t0{};
        while (landed_.load(std::memory_order_acquire) < n && !done_.load(std::memory_order_acquire)) {
            _mm_pause();
            if ((++spins & 0xffffu) != 0) continue;
            const auto now = std::chrono::steady_clock::now();
            if (spins == 0x10000u) t0 = now;
            else if (now - t0 > std::chrono::seconds(120)) {
                std::fprintf(stderr, "strata: MISS_OVERLAP: the read helper did not publish chunk %d in 120 s\n", n);
                std::fflush(stderr);
                std::abort();
            }
        }
    }
    double read_ms() const { return (double) read_us_.load(std::memory_order_relaxed) / 1000.0; }
    unsigned long long chunks() const { return chunks_.load(std::memory_order_relaxed); }
''')
    s = once(s, "            fs->prefetch_split_run();\n            read_us_", """            if (chunk_ > 0) fs->prefetch_split_run_chunked((size_t) chunk_, landed_);
            else fs->prefetch_split_run();
            read_us_""")
    s = once(s, "    std::atomic<uint64_t> read_us_{0};\n", """    std::atomic<uint64_t> read_us_{0};
    std::atomic<uint64_t> chunks_{0};
    std::atomic<int> landed_{0};   // chunks published so far in this request
    int chunk_ = 0;                // this request's chunk size (written before req_, read after it)
""")
    s = once(s, "            req_.store(nullptr, std::memory_order_release);\n", """            if (chunk_ > 0) chunks_.fetch_add((uint64_t) landed_.load(std::memory_order_relaxed), std::memory_order_relaxed);
            req_.store(nullptr, std::memory_order_release);
""")
    # stats
    s = once(s, "    double join_ms = 0, over_ms = 0;\n", "    double join_ms = 0, over_ms = 0, chunk_wait_ms = 0;\n")
    s = once(s, '''join_wait_ms=%.1f "
                     "check_rows=%llu check_mismatch_rows=%llu\\n", why, split, inline_reads, MissIo::get().read_ms(), over_ms, join_ms, chk_rows, chk_bad);''',
             '''join_wait_ms=%.1f "
                     "chunks_published=%llu chunk_wait_ms=%.1f check_rows=%llu check_mismatch_rows=%llu\\n", why, split, inline_reads, MissIo::get().read_ms(), over_ms,
                     join_ms, MissIo::get().chunks(), chunk_wait_ms, chk_rows, chk_bad);''')
    # dispatch
    s = once(s, """        return (v != nullptr && std::atoi(v) != 0) ? 1 : 0;
    }();
    FileExpertSource* mo_fs = nullptr;
""", r'''        return (v != nullptr && std::atoi(v) != 0) ? 1 : 0;
    }();
    // STRATA_MISS_CHUNK=N (with the overlap): the helper reads the missing experts N at a time, each chunk's experts are computed as it lands
    static const int mo_chunk = [] {
        const char* v = std::getenv("STRATA_MISS_CHUNK");
        const int c = mo_mode != 0 && v != nullptr ? std::min(std::atoi(v), (int) kMaxWindowEntries) : 0;
        if (c > 0) std::fprintf(stderr, "strata: MISS_OVERLAP chunked completion on: STRATA_MISS_CHUNK=%d experts per chunk\n", c);
        return c > 0 ? c : 0;
    }();
    FileExpertSource* mo_fs = nullptr;
''')
    s = once(s, "                    MissIo::get().start(mo_fs);\n", "                    MissIo::get().start(mo_fs, mo_chunk);\n")
    s = once(s, """    auto mo_is_pending = [&](int64_t e) {
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
""", """    auto mo_pend_idx = [&](int64_t e) {   // the place in the read order (= the chunk order) of a pending expert, else -1
        for (int q = 0; q < mo_npend; ++q)
            if (mo_pending[q] == e) return q;
        return -1;
    };
    int njobs = 0, njobs1 = 0;
    double mo_ms = 0.0;
    // passes: 0 = the experts that need no read; then one for all the read ones, or (STRATA_MISS_CHUNK) one per chunk in read order
    const int mo_passes = !mo_split ? 1 : mo_chunk > 0 ? 1 + (mo_npend + mo_chunk - 1) / mo_chunk : 2;
    for (int pass = 0; pass < mo_passes; ++pass) {
      if (pass >= 1) {   // the jobs of the earlier passes run first, while the helper reads on; then this pass waits for its chunk
        const auto ra = std::chrono::steady_clock::now();
        if (njobs > njobs1) {
            if (native) d.pool->run_split_multi_native(lay.fmt[(size_t) d.layers], d.jobs_multi.data() + njobs1, njobs - njobs1);
            else d.pool->run_split_multi(d.jobs_multi.data() + njobs1, njobs - njobs1);
        }
        const auto rb = std::chrono::steady_clock::now();
        if (mo_chunk > 0) MissIo::get().wait_chunk(pass);
        else mo_join.join();
        const auto rc = std::chrono::steady_clock::now();
        njobs1 = njobs;
        g_miss_stats.over_ms += std::chrono::duration<double, std::milli>(rb - ra).count();
        (mo_chunk > 0 ? g_miss_stats.chunk_wait_ms : g_miss_stats.join_ms) += std::chrono::duration<double, std::milli>(rc - rb).count();
        mo_ms += std::chrono::duration<double, std::milli>(rc - ra).count();
      }
""")
    s = once(s, """            if (mo_split && ((kind[i] == -1 && mo_is_pending(e)) != (pass == 1))) continue;   // pass 0: no read needed; pass 1: read
""", """            if (mo_split) {   // pass 0: no read needed; later: the pending experts of this pass's chunk (all of them in pass 1 without STRATA_MISS_CHUNK)
                const int pq = kind[i] == -1 ? mo_pend_idx(e) : -1;
                if ((pq < 0 ? 0 : mo_chunk > 0 ? 1 + pq / mo_chunk : 1) != pass) continue;
            }
""")
    return s
rw('src/core/expert_source.cpp', f_cpp)
print('patch4 applied')
