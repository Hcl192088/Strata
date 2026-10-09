# LUNA-20261009-005 — IQ3 sustained autonomous optimization campaign

## Mission and evidence

**Owner correction (2026-10-09):** User requires **1024 accepted output tokens only**, with no extra long-context or long-output tests. This correction supersedes any older copy of this campaign plan. If this TASK_ID was already claimed, refresh this PLAN before starting another benchmark; let any already-running process terminate normally and preserve its logs. Do not relaunch or count mismatched-length runs as valid 1024 controls.

**Objective:** Maximize measured, reproducible **accepted decode tok/s** on the fixed desktop RTX 4070 12GB, 32GB DDR4, i5-12600KF, using controlled tests with persistent autonomous continuation. One task encompasses multiple hypothesis → benchmark → compare → promote/reject cycles, not one isolated five-run test.

**Confirmed prior reports:** 002 matched five-run IQ3 1024-accepted-token median 35.76 tok/s (CV approximately 1.65%). 004 completed retrospective 15-run investigation: Pearson r(speed, pool_ms)=-0.94608, r(speed, file_tier_MB)=-0.94701, r(speed, GPU expert hit)=0.81473, r(speed, MTP accepted)=0.19002. These are correlations, NOT causal demonstrations. Old fastest 38.69 tok/s is not a stable baseline.

**Frozen benchmark identity for every comparison:** max_context=100000, actual input prompt_tokens=28912, and exactly **1024 accepted output tokens**. Never change output length or prompt length in this campaign. All promotions are against matched 1024-token controls.

## Workspace and campaign state

- Laptop Codex/Luna: `D:\strata`, using existing GitHub inbox claim+state/lock; desktop via authenticated SSH to `DESKTOP-LKMLUPC`.
- GitHub fork coordination: `Hcl192088/Strata`, `main`, one ACTIVE task. Don't change desktop source origin or confuse the fork with an upstream/source remote.
- Canonical desktop workspace: `C:\Users\User\Strata-Adrian` with source `repo\Strata-Adrian-control`, environment `env\IQ3-20261008`, output `runs\iq3-autonomous-campaign-005`, archive `archive`. Revalidate actual `AGENTS.md` and available paths before any change.
- Preserve old runs as read-only. Keep durable `campaign_state.json`, `manifest.json`, hypotheses log, per-run `command.json`, `result.json`, raw stdout/stderr, system-state snapshots, SHA256 identities, build artifacts and chronological decisions. All NEW artifacts under unique `runs\iq3-autonomous-campaign-005` children. On reboot/interruption continue from state; do not overwrite or silently count a partial run.

## Work budget and autonomy

- This is a **multi-stage ~2–4 hour campaign work budget**, not a request to waste time. Stop earlier if hypotheses are exhausted or evidence says further tests would be invalid. **Ceiling: 4 hours cumulative actively supervised measurement/analysis and up to 24 benchmark processes**, whichever binds first. Track actual elapsed work/runs in state. Do not exceed resources, poll indefinitely or inflate work just to meet a quota.
- Important: a laptop ten-minute heartbeat that only claims `STATUS: NEW` may not resume a claimed task. Before launch, verify an actual durable continuation mechanism: (a) same validated TASK_ID can resume from a persisted IN_PROGRESS state under single exclusive lock and fresh GitHub inbox verification without re-claiming/restarting; or (b) a safe detached benchmark controller actually persists across SSH session termination with explicit PID, output, lock and cleanup checks. Where necessary, make a minimal **laptop guard/orchestration change** to add safe `resume` support while preserving existing claim, state, read-before-SSH and no-duplicate semantics. Never assume a schedule or detached job exists merely because state says ACTIVE.
- At each heartbeat/continuation, check that GitHub still has *this* ACTIVE TASK_ID, existing process/lock and desktop host identity, and safely resume from the last completed stage. If ownership is uncertain or the process may still be running, **do not launch a replacement**; preserve artifacts and report the blocker. A transient SSH/path/wrapper failure with proven idle state may be retried a limited number of times with documented attempts; no new user permission needed.
- Source-level Strata optimization is authorized when a hypothesis requires it. Use trackable isolated branch/worktree and separate build path, preserve a known-good binary, record complete diff/hash and build flags. No destructive reset/clean/merge, no force push. Do not rewrite production source without reversible isolation.

## Phase 0: verify and freeze reference

1. Read actual desktop AGENTS.md and Luna 002/004 raw output, verify new workspace and active processes/resources, inspect baseline `command.json` and exact model/quant/shard/tokenizer/MTP/profile/binary/input. Do not infer effective flags from Markdown alone.
2. Freeze prompt and relevant identities: historical binary SHA256 `E67EB500C2F43B0E75D3956A17BA71C425830B6D56E2C7C5C7A96559CDEEFA74`, prompt SHA256 `9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA`, old control 3604 cache, E3/S16 decay .60, pool workers 9, 100000 max ctx, actual 28912 prompt tokens, 1024 output. Capture anything that differs in current host runtime. Check actual effective settings for every run.
3. Validate accepted-token and decode-timing attribution; capture tokens streamed/output digest if available. A changed code build implies separate binary identity and must be compared deliberately against same frozen input/control, not pooled into baseline stats.

## Phase 1: preserve existing 1024-token baseline; no redundant long-output tests

1. Use the already validated 002 five-run baseline (median 35.76 accepted decode tok/s; 1024 output) as the historical reference. Do **not** spend three extra processes re-baselining before any candidate. To account for time drift, include a fresh **matched 1024-token control** interleaved in actual candidate A/B trials.
2. Verify exact binary, model/quant, prompt 28912 tokens, max_context 100000, sampling, cache/residency, workers, and target **1024 accepted output tokens** before comparing. Keep all unchanged except the single optimization under test.
3. No long-output, long-prompt, context-capacity feasibility, per-block 4096-output instrumentation, or other auxiliary benchmark. Collect existing CPU pool/file-tier/cache and accepted-output metrics only; add instrumentation solely if indispensable for the optimization hypothesis, measure overhead separately.

## Phase 2: multiple sequential evidence-led A/B candidates

1. Form a ranked hypothesis list primarily around (a) file-tier traffic/residency/prefetch/caching; (b) CPU expert-pool scheduling/latency; (c) GPU cache pressure and expert hit rate; then MTP only if new evidence supports it.
2. Test **one factor per candidate**. Start with a safe, existing runtime knob with measurable hypothesized effect (e.g. small expert-cache/residency policy change within memory headroom); avoid speculative hard-coded values until preflight verifies feasible bounds. For each candidate, run matched **interleaved baseline/candidate comparisons with at least 3 pairs** at exactly 1024 accepted output tokens when feasible. Rotate run order to avoid warm-up bias. Include effective memory and thermal/I/O state snapshots and correct per-run accepted-token accounting.
3. **Promotion rule** (prospective threshold): candidate paired median improvement >=3% in accepted decode tok/s, no invalid run or quality regression, stable memory headroom, and supporting evidence across pairs rather than a single fastest run. If variance is too large (e.g. control sample CV >5%), prioritize variance isolation and avoid promotions until reliable. Below threshold → REJECT or label exploratory; record rejected settings to avoid repeats.
4. If a credible source hypothesis remains and runtime controls alone cannot address it, implement **up to two isolated source-level candidates** (expert file-tier/prefetch or CPU scheduling), compile separately and test matched baseline vs modified binary with identical other settings. Record source commit/diff, instrumentation overhead, build hashes, revert on safety or performance regression. Do not silently roll candidate changes into other tests.
5. Use remaining budget on the next promising **non-duplicate** hypothesis or an independent validation of the strongest promoted candidate. Do not loop the same unproductive trial simply to occupy the computer.

## Gate / stop / recovery logic

- Verify idle machine, no other Strata experiment, source/build and model identity, sufficient disk/RAM/VRAM headroom, logs and access before each stage. OOM/driver faults, wrong model, invalid accepted-token accounting, corrupted output, prolonged resource contention or ambiguous concurrent process → STOP that stage, preserve evidence and report. Do not kill unrelated tasks.
- Wrapper/output-path errors, transient SSH and individual clearly-ended process failures may be repaired and retried with traceable logs and finite limits. Do not automatically restart a run if it may still be alive.
- Do not alter the effective baseline unknowingly. If source changes or dependency identities differ, create a separate test group and matched comparison.
- If resources/time budget run out or evidence is sufficient, checkpoint final state, provide a concise conclusion and recommended next campaign; do not leave orphan processes. A run limit is a ceiling, not a goal.
- Any median/paired improvement remains *local experimental evidence* until independently revalidated. Prefer measured accepted decode tok/s, report per-run values, sample sizes, paired percentages, CV and uncertainty. Do not add separate output-length or prompt-length benchmarks.

## Reporting

At completion (or recoverable interruption that cannot safely resume) append a genuine `[LUNA_REPORT]` to `main:coordination/LUNA_TO_CHATGPT.md`, latest blob SHA/optimistic concurrency, including `TASK_ID: LUNA-20261009-005`, STATUS, elapsed duration, actual process count, state/resume proof, phase summaries, candidate table with paired data and rejection/promotion, source diffs/build hashes, best stable 1024-output median accepted tok/s, log paths, validity/stop reasons and recommended next autonomous campaign. Preserve incomplete campaign state for continuation and do not issue a second task yourself. During long running time the state file on desktop is the source of truth; don't mark COMPLETED merely because a single heartbeat ends.
