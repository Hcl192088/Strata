# DirectFile issuing-thread screen:4 vs8

Task LUNA-20261012-027 continuation; user authorized a complete +10% plan and untried candidates. This executable is a narrowly bounded mechanism screen, not an actual miss replay or engine throughput measurement. Status LOCAL_READY_NOT_COMPILED. Parent owns source/binary identity, process/API gates, staging, actual build and execution.

## Hypothesis and limits

Increasing STRATA_IO_THREADS from4 to8 may reduce multi-request batch latency if issuing-worker availability limits submission. In current Windows DirectFile it sets the issuing pool, not a hard device queue depth: requests can remain overlapped beyond the issuing-thread count. Batch1/2/4 may therefore show no benefit. No prediction of +10% engine gain follows from isolated read acceleration.

Known baseline path/flags below are parent-provided and must be revalidated. Source is f520bc5e9d31c93caeb296b059e3a3eaa16e493f; include strata/platform/direct_file.hpp, namespace strata::platform. Build links the current-best strata_engine/core/kernels_cpu libraries. A concrete link error should be diagnosed from its actual symbols; no alternate backend or cached-read performance fallback is implemented.

## Fixed sample and resource budgets

- Read actual experts.bin size42912972800 and actual native_experts.txt first five fields. Verify all five GU types16/17/22/18/21 are present.
- Per type, choose its middle metadata layer, then experts17/257/509; interleave types by expert index, and add type16 expert101:16 fixed ranges.
- Each range covers the first1MiB of its actual expert blob, plus alignment prefix/suffix: offset rounded down4096 and length rounded up4096. It is **not** a complete expert blob. Whole-blob16-range oracle plus batch8 buffers would exceed the32MiB buffer budget. All positions/lengths/original blob bounds are printed, preserving this sample limitation.
- Keep all16 ordinary-read oracle byte arrays and eight reusable4096-aligned buffers. Runtime asserts total≤32MiB. No model copy or full43GB hash. The regular fread bytes are the exact byte oracle only; all performance measurements use actual DirectFile. Read failure aborts rather than selecting another read method.
- Four batch sizes1/2/4/8 over the same ranges/order/bytes. Each16-range pass≤16×(1MiB+4096); all four sizes per setting≤100MiB. Oracle1pass + two batch8 warmup passes +72 measured passes stays≤2GiB; actual budgets printed and asserted before DirectFile work. Metadata and filesystem bookkeeping are negligible and not counted as data I/O.
- BelowNormal process; single benchmark parent thread; no affinity or power-plan change.120s campaign boundary checked before every arm,20s per pending batch,wait timeout1000ms. A hung open is not forcibly terminated by this executable; parent retains its process gate/authorization contract.

## Experiment

1. Ordinary fread reads every declared range once and saves exact expected bytes.
2. One DirectFile batch8 warmup per setting4/8, with completion lengths/tags/status and memcmp checks.
3. Nine pairs per batch size; round0 order4→8, round1 order8→4, alternating. Each arm sets the explicit environment value and constructs/opens a new DirectFile after the previous one has no pending requests and has closed.
4. Every batch submits the same range sequence, waits for exactly one successful full completion per tag, then compares all bytes outside its timing interval. Any missing/duplicate/short/failed completion or mismatch aborts, with no backend switch.
5. Output ARM fields:round,issuing,batch,warmup,total_us(sum of submit-to-all-complete batch intervals),wall_us(including between-batch byte comparisons),p50_batch_us,p95_batch_us,bytes,mismatches0,env_readback,process_threads_before_open/opened/closed. Thread counts provide direct pool-creation/join evidence; before/after equality is asserted. Source inspection is still required to attribute opened thread delta to issuing workers; environment readback alone does not prove worker count.
6. SUMMARY per batch reports median4-thread total_us,median8-thread total_us,median paired4/8 speed ratio.72 measured arms,1152 measured requests, plus two warmups. Batch8 p95 comes from only two batches per arm and is descriptive, not a reliable tail-latency estimate. No formal engine CI claim.

## Gates and interpretation

Parent must freeze current-best/BEST/config hashes and native metadata identity, verify the active runtime/source and classify all remote processes before staging/build/run. Keep API idle; this program never stops it. Original temperature and live configuration stay untouched.

All byte/completion gates must pass. Only a clear multi-request mechanism improvement justifies an engine screen, and current observed batch-size/miss/work weights must be used before estimating gain. Small single-run differences are noise. This screen does not reproduce live SSD cache state, concurrent CPU/GPU work, real request offsets, thousands of unique experts, production queue overlap or the observed distribution dominated by single-expert misses. Do not promote the environment setting from this result alone. Parent reports raw paths, binary/source identity, actual coverage, unmeasured parts and runtime restoration verification.
