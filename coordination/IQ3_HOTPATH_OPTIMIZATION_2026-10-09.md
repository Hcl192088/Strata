# LUNA-20261009-007 — IQ3 hot-path optimization campaign

## Mission
Continue immediately from completed task 006. Maximize stable measured **accepted decode tok/s**. Do not spend this campaign on another worker-count sweep. The main problem to solve is the large regression of the contemporaneous 9-worker control to median 23.36 tok/s versus the validated historical 35.76 tok/s, together with the previously measured strong relationship between throughput and CPU expert-pool latency / file-tier traffic.

All benchmark comparisons use the frozen workload identity:
- accepted output tokens: **1024 only**
- prompt_tokens: 28912
- max_context: 100000
- same model/quant/tokenizer/prompt/sampling/spec/profile/runtime flags unless the single controlled optimization factor requires an explicit change
- historical binary SHA256: E67EB500C2F43B0E75D3956A17BA71C425830B6D56E2C7C5C7A96559CDEEFA74
- historical prompt SHA256: 9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA

No 4096-output experiment, long-prompt/context-capacity test, unrelated telemetry exercise, filesystem cleanup, or cosmetic refactor.

## Existing evidence
- Task 002 validated median 35.76 tok/s, CV ~1.64%, workers=9.
- Task 004 across 15 runs: r(speed,pool_ms)=-0.946, r(speed,file-tier_MB)=-0.947, r(speed,GPU-hit)=+0.815, while MTP acceptance correlations were weak.
- Task 005: resident-budget 21 rejected; workers8 evidence inconclusive/no promotion.
- Task 006 completed 5 fresh 1024-token pairs. workers9 median 23.36 tok/s, workers8 median 20.34 tok/s, paired median delta -12.93%. workers8 is rejected/held. Do not retest workers8/9 unless a later source change specifically requires a contemporaneous control.

## Workspace / ownership
Laptop executor: D:\strata using existing authenticated GitHub handoff guard/lock.
Desktop: DESKTOP-LKMLUPC.
Canonical root: C:\Users\User\Strata-Adrian
- source: repo\Strata-Adrian-control
- runtime: env\IQ3-20261008
- new output: runs\iq3-hotpath-optimization-007
Preserve every previous run read-only. Confirm no 006 process/controller remains before starting. Use durable campaign_state.json and resume safely under the same TASK_ID.

## Phase 0 — explain the 35.76 -> 23.36 regression from existing evidence
Do this from existing raw logs first; do not burn benchmark runs just to rediscover it.

Compare task 002, task 005 controls and all task 006 controls/candidates for:
- exact effective command/environment identity
- CPU expert-pool ms/round and relevant queue/wait/dispatch counters already emitted
- file-tier bytes/read count/time
- GPU expert hit/cache/residency/swap/adaptive-tier metrics
- prefill vs decode separation
- process-start order / warm-vs-cold state
- RAM/VRAM headroom and any captured process/resource state
- any changed wrapper/controller behavior that could affect file cache or process lifetime

Produce a concise ranked causal hypothesis list. If a concrete identity regression is found, correct that accidental difference and validate with matched 1024 controls. If identity is matched, treat pool/file-tier behavior itself as the hot path.

## Phase 1 — direct hot-path intervention
Choose the highest-evidence mechanism that can reduce CPU-pool time or file-tier work. Do not start with arbitrary parameter sweeps.

Priority:
1. expert file-tier fetch avoidance / duplicate-read elimination / resident-data reuse;
2. expert prefetch timing or admission/routing changes that reduce synchronous file reads;
3. expert-cache churn reduction where it lowers file-tier traffic;
4. CPU expert-pool scheduling / dispatch / wait reduction.

If an existing runtime control directly tests the chosen mechanism, one controlled candidate is allowed. Otherwise **move directly to source-level optimization**.

Source changes are expected when justified:
- use isolated reversible worktree/branch/build;
- preserve known-good binary;
- record source diff, commit/worktree identity, build flags and candidate binary SHA;
- no destructive reset/clean/merge/force-push;
- no unrelated refactor.

Up to **three distinct source candidates** may be implemented sequentially if each is motivated by measured evidence and the prior candidate is promoted or rejected before the next one starts.

## Benchmark design
For each meaningful candidate:
- exactly 1024 accepted tokens;
- matched contemporaneous control;
- minimum 3 valid interleaved pairs;
- collect accepted tok/s plus the mechanism metrics (pool_ms, file-tier bytes/time, cache/hit/residency as applicable);
- rotate order where practical;
- reject invalid runs rather than silently counting them.

Promotion:
- paired median accepted tok/s improvement >=3%;
- not driven by one anomalously slow control;
- candidate stable enough for interpretation;
- no OOM/error/memory-headroom regression;
- mechanism metric should move in the expected direction when the hypothesis is mechanistic.

If a candidate improves proxy metrics but not tok/s, reject it.
If a candidate is promoted, independently validate it and use it as the local baseline for the next source candidate.

## Autonomous continuation / stop logic
This task should run multiple hypothesis -> change -> build -> benchmark -> promote/reject cycles without waiting for the user.

Do not end the task merely because:
- one candidate is rejected;
- variance is high;
- one build fails but is recoverable;
- one wrapper/path/SSH problem occurs;
- a local phase reaches its sample target.

Automatically recover finite, clearly safe failures and continue to the next highest-value hypothesis.

Stop the whole task only if:
- unsafe/unrecoverable state;
- <=4h active work budget or <=24 newly launched benchmark processes is exhausted;
- no actionable hot-path hypothesis remains;
- or a sufficiently validated winner is established and further work has low expected value.

At completion append one genuine [LUNA_REPORT] for TASK_ID 007 with:
- exact process/run count;
- regression diagnosis;
- candidate table with per-run tok/s and paired deltas;
- pool/file-tier mechanism deltas;
- promoted/rejected source diffs and binary hashes;
- best stable 1024-token median;
- output paths;
- next highest-value hypothesis if the overall optimization program should continue.
Do not issue a successor task yourself.
