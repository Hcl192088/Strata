[LUNA_REPORT]
TASK_ID: LUNA-20261012-027
STATUS: COMPLETED / NO_GO_UNCHANGED_WORK_STREAMING_BOUND / REPORT_LOCAL
TASK_SOURCE: branch continuation; user2026-10-29 去做
TASK_BRANCH: coordination/task-027-file-tier-reuse-20261012
TASK_COMMIT_SHA: da28699a382304ec8afc87a547f9c37123985f77
BENCHMARK_RAW_PATH: C:\Users\User\Strata-Adrian-control\runs\io-arrival-20261029

# SSD arrival streaming: not worth implementation for a 10% target

Ten captured Hermes requests ×max512, original temperature1.0/top_p.95/top_k20/min_p0/seeds1001..1010, one fresh-engine diagnostic capture; three128-token smoke requests before it. No multi-round A/B, deployment, full streaming implementation or live configuration change.

Observed optimistic unchanged-work overlap ceiling **0.610765 ms/window**; completion-interval conservative optimistic ceiling, with full time credited for two outside-dispatch reads, **0.620503 ms/window**. Diagnostic mean **37.065530 ms/window**, so +10% needs **3.369594 ms/window**. Conditional maximum from this model **+1.703%**, not a measured speedup. Also below prior same-day C reference threshold~3.505ms/window. Gate fails; do not implement arrival-streaming for this target.

Mechanism: 7688 miss dispatches, 5484 (71.33%) have only one expert destination. Their arrival spread is zero. Remaining miss-batch compute totals only 0.639156ms/window; even making ALL of this compute free, plus both outside-dispatch I/O intervals entirely free, gives 0.641054ms/window or about +1.760%. Existing ready-expert compute is already overlapped with I/O; the remaining cold compute is too small to hide several milliseconds of residual read wait. This diagnoses the arrival-streaming hypothesis, not every possible I/O or compute improvement.

|Point|Windows|Conservative optimistic ms/w|Observed optimistic ms/w|10% threshold ms/w|
|---|---:|---:|---:|---:|
|p01|67|1.277|1.276|4.202|
|p02|70|0.427|0.400|3.167|
|p03|29|1.971|1.963|5.047|
|p04|84|0.860|0.859|3.690|
|p05|154|0.571|0.553|3.472|
|p06|173|0.543|0.532|3.024|
|p07|94|1.008|0.998|4.013|
|p08|54|0.591|0.579|3.517|
|p09|77|0.526|0.526|3.297|
|p10|312|0.305|0.305|2.934|

## Method and validation

Pinned source f520bc5e9d31c93caeb296b059e3a3eaa16e493f; isolated detached worktree runs/io-arrival-20261029/source, three modified files only (expert_source.cpp,generate.cpp,cpu_phase_diag.hpp). Original generic source and live binary untouched. Same existing VS14.44/CUDA13.2/sm89/NMake Release and existing llama.cpp dependency path; source patch identities/build cmd/log preserved. DIAG binary 2EE75897E9DB9B467D669E6770A76485C9A2308F2029AD75089C46A0D9BF821C; current-best A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8/config060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93 revalidated before build, stop, blocks and restoration. The different diagnostic SHA is intentional, never substituted as a performance control.

Win32 read submissions/bytes/destinations remain original; enabled diagnostic waits for completion events in ready order but still copies ALL buffers only after ALL reads complete, then follows original compute order. No observer thread, new inference algorithm or changed weights/routes. Trace records request submission, last-unsignaled/first-signaled time bounds, destination-to-request mapping, bulk copy and per-layer ready/cold intervals. Event observation is not device completion time. Largest recorded completion interval 7.2619ms; using its optimistic edge still fails the gate. Diagnostic callback/logging/wakeup perturbation is not measured by a control A/B; diagnostic tok/s (48.098) is descriptive only.

Model grants the whole existing cold-batch compute duration immediately when the first expert could be ready, ignores early-expert copy cost, later-expert availability, CPU contention, publication and pool limits. Per dispatch upper=min(cold compute duration,cold-start minus first expert-ready), clipped at0. This is deliberately optimistic under unchanged compute/read work, not a universal engine/Amdahl bound. It excludes kernel work reduction, different I/O submissions/layout, future-route prediction, reading matrix tiles before a whole expert arrives, cross-layer scheduling and reduced read volume; the separate free-all-cold-compute check supports the negative conclusion for hiding existing cold compute.

Smoke native PIPE_CHECK compared at least 246,407,680 floats with zero mismatches; observed 9 GU/down format pairs, not an all-format or semantic-quality proof. Capture CHECK off, runtime/capacity/priority/repetition guards all passed. Actual env/config audit permits only exe/cwd/log and diagnostic env differences; original sampling preserved. AboveNormal,3153 GPU slots,20GiB/20479MiB resident,9workers/all maintained.

## Coverage and engineering issues

All10 requests,1114 windows,**53,472/53,472 layer-windows**,all7,691 recorded I/O batches/11,430 OS requests fully parsed. Every dispatch-associated I/O batch assigned once; per-request trace windows agree with decode phase counters. Raw CSV/log sizes and SHA in raw-manifest.json. No sampling of trace rows or truncation of large trace during analysis. Private prompts/responses not published or included in this report; repetition check only, no semantic review. Source audit limited to changed functions and associated call sites, not full repository/dependency audit.

Parser initially rejected two unassigned single-request reads. Both are strictly between layer47 and next layer0, outside every traced CPU dispatch. Their exact callers remain NOT_IDENTIFIED; do not label them as confirmed adaptive reads. Retained in analysis.json with their ENTIRE combined2.1151ms credited as further recoverable benefit (0.001899ms/window), so they cannot silently improve a rejection by omission. No new engine run or replacement data. Patch generator initially found the same memcpy anchor in Windows/Linux; rejected before writing source, then explicitly scoped to Windows. Original default source contains historical error fallback branches; diagnostic encountered no reported read failure and did not add a fallback.

## Restoration and publication

20:15:12 original API restored; independent fresh process/identity/health/env/capacity gate verified PID27640,AboveNormal,loaded,current-bestA1E6/config060F,3153slots/20479MiB. Only classified API/watch stack remained, no diagnostic/build process. No live/source-main/config/model/temperature changes or unrelated process stops. Completed one-shot scheduled task retained Ready.

Report/data/source patch remain local and in the same remote run directory. REPORT_LOCAL: earlier report commit/push automatic approval rejection is still unresolved; no retry/alternate publication or coordination-state rewrite. No source promotion.
