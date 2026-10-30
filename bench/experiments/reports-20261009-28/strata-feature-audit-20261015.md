# Strata live feature audit — 2026-10-15

STATUS: AUDIT_ONLY_COMPLETED. No source/config/runtime change, build, restart, process stop, benchmark, generation request or GitHub write. Only a small local report and read-only evidence snapshot were saved.

## Live identity and baseline

- Host verified by strict SSH: DESKTOP-LKMLUPC, User@<desktop-tailscale-ip>.
- Active engine PID7592; API Python6092 / venv launcher24292. One engine, no competing benchmark/build/Python process in relevant inventory.
- Binary: C:\Users\User\Strata-Adrian-control\runs\ram-lru-20261013\build\strata.exe
- SHA256: **366A355E0E866B12D1793C9D8BE022925305B4560E1AE7DC47F8716C865015E2**.
- Canonical root is a junction to C:\Users\User\Strata-Adrian\repo\Strata-Adrian-control; resolved process image uses that target. This is the same artifact, not another deployment.
- Actual build source: C:\Users\User\Strata-Adrian-control\runs\ram-lru-20261013\source, HEAD **61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406**, plus dirty existing include/strata/core/expert_source.hpp and src/core/expert_source.cpp (RAM LRU). It is not clean upstream main. Exact current hashes of six relevant source/header files retained in evidence JSON.
- CMakeCache and build.cmd point at that source, Release/CUDA89, existing llama dependency. Canonical coordination checkout HEAD1b90d1cdc7193874440e7c684f40c8ae7808b496 is not the engine source commit.
- Config: C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\server-task020-8080-v0142.json
- Config SHA256: **C805B1206CDD23B22EE3CC66A80C52014EF9904CDB4314A6C6A17B8E00FFEA18**.
- Startup launcher: canonical tools/start_task020_api.ps1, existing scheduled task Strata-Task020-API, legacy20261009 venv. Launcher runs Python serve.server from iq3-campaign-020/upstream-v0142; server engine exe comes from config above.
- Current startup evidence begins at log marker2026-10-15 21:08:32 in runs/ram-lru-20261013/user-lru-api.engine.log. Corresponding PID creation checked. Logs confirm3153GPUslots,9workers LP2,4,6,8,10,12,13,14,15,hostLP0,30tasks,20.00GiBresident,20479MiBVirtualLock,CUDA pinned0.00GiB. Blocking adaptive swaps enabled every3windows/up to16.

Full live argv, config, relevant actual process environment, binary/source hashes and startup excerpts are in **strata-feature-audit-20261015.evidence.json**. Process environment was read from the running PID via psutil.environ; it is not inferred only from config. Only STRATA_*,CUDA_VISIBLE_DEVICES,OMP_NUM_THREADS,MKL_NUM_THREADS were selected, to avoid unrelated credentials.

Actual STRATA environment (complete selected set): STRATA_ADAPT_IF_MISS=1, STRATA_DECODE_TIMING=1, STRATA_EXPERT_FILE_CACHE=1, STRATA_FETCH_ADMIT=0, STRATA_LOOKAHEAD=0, STRATA_PF_FUSED=1, STRATA_RAM_LRU=1, STRATA_RAM_LRU_CHECK=0, STRATA_RESIDENT_HEADROOM_GIB=3. None of the nine audited switches' environment overrides is present. Absence does not mean default features are off.

Full effective engine arguments:

```text
--serve
--pack C:\Users\User\Strata-IQ3-20261008\packs\iq3_xxs
--native C:\Users\User\Strata-IQ3-20261008\models\IQ3_XXS\Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf
--ple-gguf C:\Users\User\Strata-IQ3-20261008\models\IQ3_XXS\Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf
--mtp C:\Users\User\Strata-v0.1.34-mtp-test-20261002\mtp\rt
--spec 6 --spec-min-p 0.75 --max-context 100000 --kv q4_0 --kv-resident 20480
--expert-profile C:\Users\User\Strata-v0.1.38-ab-20261003\work-note-transfer-chat-20261005\learned-heart.bin
--expert-cache 3604 --pool-workers 9 --prefill auto --stats --max-new 1024 --suffix-draft 3
--resident-budget-gib 20 --mtp-max-t 3 --pool-affinity all --adapt-every 3 --adapt-swaps 16 --adapt-decay 0.60
--ple-io direct --mtp-hnorm stream
```

Historical CURRENT_BEST differs from DEPLOYED_CANONICAL: Task025 report lists async-miss E3FA77FE1C7BA9AD957F3EE61F195DAED433CA46C1E523C4B7E9E487498C27FB,49.45tok/s median, isolated source source-async-miss. The recorded build-async-miss/strata.exe is absent, and a targeted recursive strata.exe search under iq3-campaign-025 returned none. Therefore this audit cannot certify that historical optimization control reproducible today. Its async-miss source optimization is NOT --adapt-async. Current366A deployment is a verified causal-isolation baseline, not a newly proven global fastest binary. Future formal promotion against historical CURRENT_BEST must first resolve that build identity; do not compare historical49.45 to today's changed stream/LRU workload as if matched.

## Upstream comparison snapshot

Connected GitHub main resolved to Niko1221/Strata **296b59d2f73c8f04a805df29c2fa97655adace78**; fork Hcl192088/Strata main to **2d967ac1a8ac25ac63d3a685a90594d63438ae23**. Neither equals live engine source. Read upstream files at the pinned main SHA, not a moving ref:

- src/program/generate.cpp blobba00f94d75121b8d4c7cbfdafd8daeb8d12e0be5
- src/core/expert_source.cpp blob4878c111310f94df4fedf6366c9a699184e357b8
- src/kernels/cpu/pool.cpp blob3bf8c93f651acd107d91cc00b651cba4e7e79ae7
- include/strata/platform/aux_cpus.hpp blob3a56031604c82b03d8c843d49f951556a3779a9c

## Classification

"Compiled" combines actual image string search, corresponding source/build provenance, and available live log evidence; string presence alone is not proof of execution. Linux-only aux backend is specifically excluded from functional Windows support.

| Feature | Live binary support | Configuration/default | Runtime execution evidence | Applicability to current RAM mode | Existing tests found / decision |
|---|---|---|---|---|---|
|--adapt-async|Yes, parser and resident implementation present|Absent; adapt_async default0|Not active: flag absent/default0, blocking tier startup, no ajob activation|Potentially yes. Pageable/VirtualLock complement is accepted using pinned bounce buffers, but reserve_exchanges(32) and exchange_pinned must succeed. Full20GiB CUDA pin is not required|No dedicated A/B found in inspected records. Priority1 conditional candidate; custom RAM-LRU integration unvalidated|
|STRATA_POOL_SPIN_US|Yes|Unset; default20ms=20000us|Default policy selected by constructor; live per-worker sleep/spin transitions not traced|Yes, CPU park/wakeup policy independent of resident pin|No dedicated sweep found. Historical park overhead tiny; defer until a sleep/wakeup bottleneck is measured|
|--aux-cpus / STRATA_AUX_CPUS|CLI/env names present; functional backend Linux-only|Absent; no placement requested|Windows set_topology returns not available; exact startup message present|Unavailable on Windows, irrespective of20GiB mode; current upstream main also Linux-only|No useful Windows A/B possible on this binary. Do not test a no-op or port it in this scope|
|--pool-tasks|Yes|Unset=0 auto;30tasks/phase|Startup explicitly30automatic,10participants|Yes|Task015192task median+2.82% failedgate; current30vs60 finalmedian-0.03%; simple linearnt-1.28%. Do not repeat|
|--host-core|Yes|Unset; defaultfirst, env STRATA_HOST_CORE absent|Startup hostLP0 and worker CPUs explicit; actual first-core placement selected|Yes; last topology remap condition excludes detected hybrid layouts in this source|Task016last median-0.904% on older baseline. Already rejected; no new candidate|
|STRATA_ADAPT_OVERLAP|Not found in live source or binary|Unset|Cannot execute this named feature in current image|New upstream resident path requires extra STRATA_ADAPT_OVERLAP_RESIDENT=1; incompatible with adapt-async and subject to other gates|No local exact-feature A/B found. Current upstream documents Windows IQ3_XXS no gain and other regressions; out of current-binary scope|
|STRATA_PIN_BY_NEED|Not found|Unset|Not executing|Upstream arena_src pin-selection path; does not convert this resident VirtualLock complement into CUDA mapped/pinned memory|No A/B found. Exclude: unavailable and would address a different RAM path|
|STRATA_PCIE_MIN1|Not found|Unset|Not executing; recent actual PCIe expert count0.00/layer|Even new implementation requires pcie_ok/device_alias and pinned blob; current CUDA pinned0GiB fails eligibility|No A/B found. Exclude without changing pin mode, which is prohibited|
|STRATA_ADAPT_CALLBACK_WARMUP|Not found|Unset|Not executing|Upstream0.1.43.1 default-on implementation is inside __linux__; Windows CPU Sets inheritance issue does not apply|No local A/B found. Exclude Windows|

Actual source references: generate.cpp defaults424/585, parser1841+/1954, host/env2132+, async gates6500+/6653+/8330+; pool.cpp440 constructor,508-523 spin/sleep; pool.hpp215-216/277 default; aux_cpus.hpp18,150,350-357 non-Linux stubs. Upstream refs: generate.cpp1389-1404(overlap opt-in),4917-4935(arena pin-by-need),5034-5049(Linux warmup),8738-8758(overlap eligibility); expert_source.cpp3770-3776(MIN1 eligibility).

## CPU-positive share and spin decision

Current deployment has no per-layer CPU-positive or worker sleep-count telemetry. Mean CPU-experts/layer and GPU waitCPU are not substitutes for an exact positive-layer fraction or OS wake latency.

Existing pool-split raw/aggregate evidence can provide a historical diagnostic proxy without a new run. Verified instrumentation increments phases once per run_phase; native GU and Down each call it once, quantization serial, and kMaxSplitMulti96 exceeds possible distinct routed experts forT1-3. Thus phases/(2*48) yields CPU-positive layer-window proportion in that old pooled diagnostic: T1~81.4%(1179windows),T2~93.5%(448),T3~98.4%(342). It is not the current stream workload's live census.

Same diagnostic: total phase-boundary cost~0.0193/0.0215/0.0230ms/window atT1/2/3; pre/post-park alone~0.0104/0.0110/0.0119ms/window. T3 completion_wait5.669ms contains useful worker computation, not OS wake overhead. Current GPU-profile waitCPU17.37ms also waits useful CPU work and is not evidence that longer spin fixes it. Default20ms already stays awake far longer than many inter-layer gaps. Therefore neither shrinking nor increasing spin is justified as the next latency experiment. Reconsider only with measured mid-request sleeping, wake latency and CPU-positive gaps; do not infer it from total CPU wait.

## Concrete A/B proposal (NOT executed)

Only ready conditional candidate: existing deployed binary with --adapt-async0 versus1, in isolated native --serve processes. Not CLI one-shot, which explicitly does not support async. Keep original MTP+stream,Tmax3,suffix3,model,temperature,20GiBVirtualLock,workers9,30tasks,hostfirst,all adaptive parameters unchanged. Do not combine with overlap/spin/aux.

1. Recheck host/process ownership, binary/config/artifact hashes and formal current-best identity. If testing366A causal isolation explicitly label it; it is not proof against historical Task025 currentbest. Only after new authorization pause idle API; no current audit side effects.
2. Candidate startup gate:20.00GiBresident,20479MiBlocked,3153slots; asynchronous startup line required; no "adapt-async1 is off" reason. Exchange buffer capacity doubles from16 to32 expert blobs; bytes depend on the largest per-layer expert blob, and these buffers must be CUDA-pinned. Small bounce pin success is still unconfirmed and requires restart-bound validation. If unavailable, record NOT_APPLICABLE and stop; do not silently measure blocking fallback.
3. Three interleaved matched pairs on frozen neuro28912/1024,normal non-profiled execution. Same prompt/request/runtime identity; record output hashes and variation because async CPU/GPU residency changes are not necessarily bitwise deterministic. Check clean finish, accepted counts, errors, request-boundary drain, no mutation races with custom RAMLRU. A positive speed result alone is insufficient for correctness.
4. Metrics: tok/s,window ms,tokens/window,CPU jobs+pool,adaptive rounds/swaps/start-to-flip,host waiting/draft join,file-tierbytes,hit rate,available RAM. No GPU profiler in timed gate because it disables normal overlap. Async stats/actual swaps must show work occurred; a requested flag alone is not enough.
5. If pairedmedian>=3% and controls/environment healthy,2confirmation pairs; otherwise reject. Any resident/cache/memory-mode mismatch or explicit async disable fails the gate. Stop only owned processes and restore original stream API afterward. No automatic promotion under an unresolved currentbest identity or unverified output quality.

Aux auto is not candidate2 on Windows. Spin is deferred, not a sweep. New upstream overlap/arena pin/warmup features would require an explicitly authorized later version/source campaign, and are not this audit's next A/B.

## Evidence coverage and limits

Complete requested9 feature-name checks in actual six source/header files and image, actual live argv/relevant environment/config/startup, source/build provenance, pinned upstream four-file comparison. All local state Markdown reports and canonical remote .codex/handoffs Markdown were keyword-searched for existing feature benchmarks; relevant Task015/016/025, GU weighted/tasks, pool-split and GPU-profile reports read. Initial overly broad JSON search produced huge/truncated output; it was excluded as conclusive evidence and repeated as bounded Markdown searches. Large original logs were filtered by current-startup marker/feature lines; source contexts inspected, not every generated token or all historical logs. Missing recorded025 binary is a reproducibility gap, not proof no copy exists anywhere on the PC. No whole-disk scan, all upstream PR review, dynamic thread tracing, per-request aux override history or exchange-pinning introspection. No claim of universal absence of older tests beyond checked coverage.

The live process remained running throughout; no runtime path requiring a restart was tested. Current runtime execution conclusions are based only on observable startup/counters plus proven source gates, with unobserved states explicitly pending.
