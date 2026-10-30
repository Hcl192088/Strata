# R4 actual pool with per-four-row conversion

LUNA-20261012-027 direct-user continuation; 2026-10-30; TESTED / NO_GO for this tile-conversion implementation / REPORT_LOCAL. User explicitly authorized the candidate and API pause/restore. API remained running and no restoration was needed.

The isolated candidate modifies a copy of f520bc5 pool.cpp: for IQ3_S and nt2/3, groups original GU rows in fours, uses fast pack into 8192-byte per-thread temporary scratch, calls existing lowreg for gate and up, writes SwiGLU to the original split buffer, and runs the existing native pipeline quant/down, including type42 act_quant_any/q2_rows_any. Other nt/types use their explicit existing dispatch. GU task partition is changed to 4-row groups, covering each row once; no second resident expert copy or GPU/prefill format change. Scratch allocated at most 10×8192=81920 bytes plus g/u stack, and every group repack occurs inside measured pool time. Original blob and down remain native. No failure-triggered fallback.

Actual ExpertPool 9 pinned workers + host, all affinity, AboveNormal, pipeline active, existing 3-task-per-thread geometry. One real layer 8, 18 expert blobs of 1,868,800 bytes each, IQ3_S/down type42; nt2 and nt3, nb1/4/8/16, one warmup each arm and five alternating A/B passes per cell on identical inputs. The 18 are resident only for this bounded pool sample, not the model's live routing distribution. API was idle; pool benchmark runs with model already resident, CPU and cache contention within the pool included. Timing includes conversion, GU, intermediate quantization, native down, worker synchronization, cache and pipeline scheduling. SSD/GPU/transfer are outside this CPU-only test, and would be additional costs; no whole-model claim. Five passes with first arm receiving one more first-position pass is screening, not a confidence interval. n=1,4,8,16 are deliberately bounded choices, not measured distribution.

| nt | nb | native us median | tile us median | candidate throughput change |
|---:|---:|---:|---:|---:|
|2|1|68.900|81.400|−15.36%|
|2|4|209.100|256.000|−18.32%|
|2|8|412.500|512.600|−19.53%|
|2|16|985.100|1199.300|−17.86%|
|3|1|84.500|95.300|−11.33%|
|3|4|251.800|293.900|−14.32%|
|3|8|539.400|587.600|−8.20%|
|3|16|1233.900|1406.300|−12.26%|

All tested medians favor native. Pool actual output differs from native (4,256–101,238 float bit differences per cell; maximum absolute down difference 5.96046448e-8); this is local numerical evidence, not semantic noninferiority or evidence of quality loss. Across all 18 sampled blobs, all 640 rows, gate and up, nt2/3 and both ISA variants, fast packed bytes matched original R4 pack and lowreg dot outputs matched old R4 bitwise. This does not prove full pool intermediate parity with old R4 nor language quality. The screen tested output finiteness; no teacher forced logits/loss, A/A or task evaluation.

Stop gate: measured pool cost is worse in all eight cells, so engine C/B/C is DEFERRED; no interpretation as engine speed or global impossibility. Semantic quality QUALITY_UNCONFIRMED. No deployment or sampling change. This conclusion applies only to 4-row repack-on-every-invocation under tested source, samples and settings; other arrangements untested.

Baseline is exact same isolated source compiled with candidate arm disabled and linked to current-best CPU/ggml libs; it is not an invocation of A1E6 full engine binary. Control build includes a branch and different pool compilation; therefore pool relative result is screen only. Before build and run current-best manifest binary/config hashes and live environment/idle/process gate were checked; source f520bc5 clean. Executable SHA256 034B45B923987E94CA33F331F38B13A6B08A69CCB63608E7B23730AA5F9DE579; pool.cpp AC25D873E467C92C84B3860384F3419C1C4918709FD07C309AA170290B36739A; bench.cpp C5675BCA9CA7449891C3B4E4717B3EF454480023E91FE45E95AEFD16339C12CE; pool.log D99407D588A62CC3E149AE0CD366076CBA589E03AEDECB80A475F340CB7F3BF2. Full source and library hashes in inputs.json. Raw remote C:\Users\User\Strata-Adrian-control\runs\r4-actual-pool-20261030.

Independent final receipt C:\Users\User\Strata-Adrian-control\runs\r4-actual-pool-20261030\independent-final.json SHA256 9984BD6DFE7435E7981C23F7EE21E62C2C542ABF7BEE9F8A3FB0BE8A4063ACC7: live PID32568, A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8, config 060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93, loaded/idle/queued0, AboveNormal, configured env, 3153 slots and 20479 MiB; process gate no remaining relevant test/build. API never stopped; no restore required. GitHub publication remains prohibited by existing concrete approval rejection.

## Parent final acceptance
2026-10-30：交付後只作最後驗收，沒有重跑測試。核對 harness 確實呼叫 ExpertPool::run_split_multi_native；raw PARITY、八筆 SUM 與 DONE 完整，pool.log 與 independent-final.json SHA 符合報告。fresh strict-host SSH 確認 host、binary/config/receipt hash，API PID32568 loaded/idle/queued0、3153slots/20479MiB，僅已分類 API/watch、無相關 bench/build。接納本次單層18experts、八格、含逐四列轉換的 pool NO_GO；不外推整個R4家族或整機。沒有 engine tok/s 或語意品質結論。父層抽驗實作入口、原始摘要與operational receipt，未重算每筆timing或全面審核新source。
