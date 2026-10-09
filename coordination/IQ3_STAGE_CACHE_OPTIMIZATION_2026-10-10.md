# LUNA-20261010-008 — IQ3 stage-cache admission/churn optimization

## Mission
Continue immediately from completed task 007. Maximize stable measured **accepted decode tok/s** by attacking the mechanism still supported by matched evidence: excessive file-tier expert traffic and the associated CPU expert-pool latency. Task 007 rejected page-only lookahead, RouterLookahead staged prefetch, and disabling PrefetchVirtualMemory; do not repeat those candidates.

All benchmark comparisons keep the frozen workload identity:
- accepted output tokens: **1024 only**
- prompt_tokens: 28912
- max_context: 100000
- same model/quant/tokenizer/prompt/sampling/spec/profile/runtime settings except the single controlled candidate
- stable historical reference: task 002 median 35.76 tok/s, CV ~1.64%
- control binary SHA256: E67EB500C2F43B0E75D3956A17BA71C425830B6D56E2C7C5C7A96559CDEEFA74 unless a source candidate is intentionally built

No 4096-output runs, long-prompt/context-capacity experiments, worker-count sweeps, resident-budget sweeps, PVM-off rerun, lookahead rerun, cosmetic refactors, or unrelated telemetry exercises.

## Evidence entering task 008
Task 007 completed 18 valid matched benchmark processes:
- STRATA_LOOKAHEAD=1: paired median -6.39%; file-tier/pool generally worsened.
- RouterLookahead warm->prefetch source candidate: paired median -4.94%; file-tier/pool generally worsened.
- STRATA_FETCH_PVM=0: paired median -11.40%; file-tier/pool worsened.
Prior task 004 measured r(speed,pool_ms)=-0.94608 and r(speed,file_tier_MB)=-0.94701.
Therefore the next target is **why experts are still reaching file tier repeatedly**, especially admission refusal, static-profile misses, cache churn, duplicate reads, or failure to reuse already-hot experts.

## Mandatory external reconnaissance before editing source
Do a short, bounded code/PR/fork review first and record what is actually reusable. At minimum inspect:
1. Niko1221/Strata issue #831: profile-seeded cache can leave capacity unusable and compulsory-miss admission is unreachable in serve/profile paths; inspect the cited ExpertCache/generate admission paths against the current Adrian source.
2. Niko1221/Strata issue #369 and related cache/per-layer fixes for concrete admission/fill bugs that may already have solved adjacent churn/residency problems.
3. spideytznn/Strata, especially its expert residency/tiering changes and relevant diffs, for reusable ideas around RAM-constrained expert ownership/residency. Do not port old code blindly; compare with the current source first.
4. ggml-org/llama.cpp discussion #25779 explicit-read MoE prefetch only as a mechanism reference. Task 007 already showed naive Strata lookahead/prefetch is harmful, so only reuse ideas such as exact routed-expert dedup/range coalescing if the current trace shows duplicate/small reads.

Also search recent upstream Strata PRs/forks/issues for expert-cache admission, eviction, residency, file-tier fetch, duplicate-read, and prefetch changes. Prefer a proven upstream/fork fix over reimplementing the same mechanism. Record exact PR/issue/commit/repo references used.

## Workspace / ownership
Laptop executor: D:\strata using the existing authenticated handoff guard/lock.
Desktop: DESKTOP-LKMLUPC.
Canonical root: C:\Users\User\Strata-Adrian
- source: repo\Strata-Adrian-control
- runtime: env\IQ3-20261008
- new output: runs\iq3-stage-cache-optimization-008

Preserve previous runs read-only. Confirm no task-007 process/controller remains before launch. Use durable campaign_state.json and resume safely under the same TASK_ID.

## Phase 0 — trace the actual miss/admission/churn path
Use existing logs/source first. Add narrowly scoped instrumentation only where existing counters are insufficient.

For decode-time expert requests, obtain enough accounting to distinguish:
- GPU-cache hit
- RAM resident hit
- file-tier fetch
- repeated file-tier fetch of the same layer/expert within the same run
- admission attempted / admitted / refused and refusal reason
- eviction count and victim identity where applicable
- resident/cache occupancy over time
- per-layer miss concentration
- read count, bytes and time, not only aggregate MB
- whether multiple requested experts map to duplicate/overlapping file ranges that could be coalesced

Instrumentation must be cheap, off by default where practical, and isolated/reversible. One instrumented 1024-token control is allowed if existing data cannot answer the mechanism question. If instrumentation overhead is material, compare it against an instrumentation-off control and do not use its tok/s as a promotion baseline.

Output a ranked causal table showing which small set of experts/layers/events account for file-tier bytes and whether traffic is compulsory, repeated, churn-driven, or policy-refused.

## Phase 1 — first mechanism candidate
Choose the highest-evidence intervention from Phase 0 plus the external reconnaissance. Preferred order:

1. **Profile-seeded hybrid admission** if the current serve/profile path statically refuses useful compulsory misses despite available cache capacity or replaceable cold entries.
2. **Hot-expert promotion / cold-victim replacement** within a fixed memory budget if repeated file-tier experts are observed and the existing policy cannot adapt to the actual prompt routing.
3. **Duplicate-read elimination / exact request coalescing** if the trace shows repeated or overlapping file reads for experts already requested in the same decode window.
4. **Targeted stage-cache reuse** if data is fetched but discarded/reloaded across nearby rounds.
5. A recent upstream/fork patch that directly solves the measured mechanism.

Do not change total memory budget as the primary intervention. The goal is better use/reuse/admission of the same available memory, not another resident-budget sweep.

## Source-change contract
When source changes are justified:
- use an isolated reversible worktree/branch/build;
- preserve known-good binary;
- record exact diff, source HEAD, build flags, candidate binary SHA;
- no destructive reset/clean/merge/force-push;
- do not modify unrelated source;
- if porting from a PR/fork, record provenance and adapt only the minimal relevant diff.

Up to **three sequential source candidates** may be implemented within this task. A rejected candidate is not a reason to stop; proceed to the next highest-evidence mechanism while budget remains.

## Benchmark design
For every meaningful candidate:
- exactly 1024 accepted tokens;
- matched contemporaneous control;
- minimum 3 valid interleaved pairs;
- accepted decode tok/s is the primary metric;
- record CPU pool ms/round, file-tier read count/MB/time, GPU/RAM cache hit/residency, admission/eviction/repeat-fetch metrics relevant to the mechanism;
- rotate order where practical;
- reject invalid runs rather than counting them.

Promotion requires:
- paired median accepted tok/s >= +3%;
- improvement not explained by one anomalously slow control;
- candidate stable enough to interpret;
- no OOM/error/headroom regression;
- file-tier/pool/admission mechanism metrics move in the expected direction;
- if only proxy metrics improve but tok/s does not, reject.

If promoted, independently validate the winner and use it as the local baseline for the next candidate.

## Autonomous continuation / stop rules
Run multiple hypothesis -> change/port -> build -> benchmark -> promote/reject cycles without waiting for the user.

Automatically recover and continue after:
- one rejected candidate;
- high variance;
- recoverable build error;
- wrapper/path/output-root error;
- transient SSH/GitHub conflict;
- one local phase reaching its sample target.

Task-local budget:
- <= 30 newly launched benchmark processes
- <= 5h active work

Stop task 008 only for:
- unsafe/unrecoverable state;
- task-local process/time budget exhausted;
- no actionable stage-cache/admission/file-tier hypothesis remains after the required external reconnaissance;
- or a sufficiently validated winner is established and additional work within this task has low expected value.

Do **not** stop the overall Strata optimization program at task completion. Report the best next architectural hypothesis for the coordinator to chain immediately.

## Final report
Append one genuine [LUNA_REPORT] for task 008 with:
- exact process/run count;
- external PR/fork/issues inspected and which mechanism was borrowed/rejected;
- causal trace summary: compulsory vs repeated/churn/refused file-tier traffic;
- candidate table with per-run tok/s and paired deltas;
- file-tier read count/MB/time and CPU pool deltas;
- admission/eviction/repeat-fetch deltas;
- promoted/rejected source diffs and binary hashes;
- best stable 1024-token median;
- raw output paths;
- next highest-value hypothesis.

Do not create the successor inbox task yourself.
