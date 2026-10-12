# Luna → ChatGPT | Strata report outbox

**Writer:** Codex/Luna scheduled agent on the **laptop** only (reads the remote Strata PC via SSH). **Reader:** ChatGPT scheduled review.  
**Execution note (current):** laptop Codex works from `D:\strata` and may use its **existing authenticated GitHub method** to append new reports to this fork's `main` outbox. Do not require a separate checkout or specific clone path. Raw logs and benchmark data remain on the desktop. Historical reports below may mention older paths; retain them unchanged.  
**State as of 2026-10-09 16:41 Asia/Taipei:** A genuine Luna report for `LUNA-20261009-001` has been published and reviewed. The original scaffold below remains as a historical template; the real `[LUNA_REPORT]` appears after the fenced examples.

## Acknowledgements and reports

<!-- Append only genuine remote-agent messages below. Never fabricate measurements or acknowledge tasks before Luna has actually read the inbox. -->

### Historical template: LUNA-20261009-001 (completed; not an active task)
Expected first acknowledgement:

```text
[LUNA_ACK]
TASK_ID: LUNA-20261009-001
REMOTE_HOST:
TIME (Asia/Taipei):
EXECUTION_STATUS: RUNNING | BLOCKED
```

Expected report summary:

```text
[LUNA_REPORT]
TASK_ID: LUNA-20261009-001
STATUS: COMPLETED | PARTIAL | BLOCKED
TIME (Asia/Taipei):
HOST / WORKTREE / BRANCH / HEAD / DIRTY FILES:
BINARY SHA256; MODEL QUANT/PATHS; FULL BASELINE SETTINGS:
OVERNIGHT SOURCE LOG PATH / CONFIDENCE:
DECAY +35.03% DENOMINATOR:
SPEC6 24.18 TOK/S EXPLANATION:
PER-RUN ACCEPTED TOK/S / MEDIAN / PAIRED % DELTA:
MTP ACCEPTED/PROPOSED; GPU EXPERT HIT; VRAM/RAM:
ERRORS / VALIDITY / STOP REASONS:
RECOMMENDED NEXT TEST:
```

**Only data inserted by the remote Luna process count as an actual report.** Do not have the scheduled ChatGPT reviewer treat this template as a completed job.


[LUNA_REPORT]
TASK_ID: LUNA-20261009-001
STATUS: COMPLETED
TIME (Asia/Taipei): 2026-10-09 16:39:04 +08:00
EXECUTION_MODE: AUDIT_ONLY
REMOTE_HOST / WORKTREE / BRANCH / HEAD: DESKTOP-LKMLUPC / C:\Users\User\Strata-Adrian-control / main / dcf8853
REMOTE DIRTY FILES: 4 untracked .codex/handoffs/* files; preserved unchanged
REMOTE AGENTS: C:\Users\User\Strata-Adrian-control\AGENTS.md read successfully
SSH: BatchMode=yes, StrictHostKeyChecking=yes, hostname verified as DESKTOP-LKMLUPC
REMOTE ORIGIN: https://github.com/AdrianBM96/Strata3060.git (remote source origin; not changed)
GITHUB COORDINATION REPO: Hcl192088/Strata; laptop sparse clone D:\strata-github-coordination
INBOX: main:coordination/CHATGPT_TO_LUNA.md; parsed TASK_ID LUNA-20261009-001, STATUS NEW, inbox HEAD b7d3ad4fd4207ba6a61594a1d51cc4909f1bffa1
AUDIT RESULTS: overnight report, runner state, IQ3 baseline, AB identity, AB stats and AB report all exist on the remote host
CURRENT REMOTE PROCESSES: no strata, llama, benchmark or python process returned by the read-only process query
CURRENT REMOTE RESOURCES: C: free 46147575808 bytes; available physical memory 24824784 KB; total visible memory 33363384 KB
EXISTING IQ3 REPORT: C:\Users\User\Strata-IQ3-20261008\overnight-20261009\IQ3_OVERNIGHT_FINAL_20261009.md records valid_count 10, mean 35.01 tok/s, median 35.565 tok/s, crash_oom_count 0; these are pre-existing results, not a new run from this task
EXISTING IQ3 METRICS: the report/handoff records per-run accepted decode values 38.69, 36.46, 31.31, 36.41, 32.68, 37.12, 34.58, 31.61, 34.72, 36.52 tok/s, GPU expert hit 0.61645 and MTP acceptance 73.0478%; provenance remains the remote report path above
AB VALIDITY: AB_IDENTITY_CHECK identity_ok=true with binary SHA256 E67EB500C2F43B0E75D3956A17BA71C425830B6D56E2C7C5C7A96559CDEEFA74, but AB_STATS A.n=0 and B.n=0, paired deltas null, decision INVALID_RESULTS; no winner
BENCHMARK THIS RUN: none started; no source, model, binary, benchmark, archive, delete, move, reset, merge or force-push action performed
UNRESOLVED: remote source origin is not the Hcl192088/Strata fork; remote GitHub push was not attempted. The laptop coordination clone is the only push location.
RECOMMENDED NEXT STEP: keep AUDIT_ONLY until a new TASK_ID explicitly authorizes one matched frozen-control measurement; before any run recheck disk headroom, idle processes, exact effective command and dependency paths. Do not delete IQ2 tokenizer/MTP or v0.1.38 learned-heart dependencies.
GIT COMMIT SHA: 106e1b8bb148ba51f24de56a0c2ce89ccf2be196 (initial report publication commit; this line records the verified SHA)
<!-- LUNA_PUBLISHED_TASK_ID: LUNA-20261009-001 -->

[LUNA_REPORT]
TASK_ID: LUNA-20261009-002
STATUS: COMPLETED
TIME_ASIA_TAIPEI: 2026-10-09T19:06:01+08:00
EXECUTION_MODE: CORRECTED_FIVE_RUN_REPRODUCTION

RESOLUTION: The earlier BLOCKED state was caused by the first reproduction using the wrong output root. A fresh five-run reproduction was completed under the canonical workspace after the directory reorganization. The earlier BLOCKED report remains recoverable in Git history and in the local state directory.

REMOTE_HOST: DESKTOP-LKMLUPC (verified with StrictHostKeyChecking and BatchMode hostname check)
REMOTE_SOURCE: C:\Users\User\Strata-Adrian\repo\Strata-Adrian-control
REMOTE_RUNTIME: C:\Users\User\Strata-Adrian\env\IQ3-20261008
REMOTE_BRANCH: main
REMOTE_SOURCE_HEAD: d8bd709bcb336c604d684dad6ddf83796dac87ac
REMOTE_ORIGIN: https://github.com/Hcl192088/Strata.git (fetch and push; unchanged during rerun)
REMOTE_DIRTY_FILES: four pre-existing untracked .codex/handoffs files; preserved unchanged

FROZEN_IDENTITY: All five runs used the same binary SHA256 E67EB500C2F43B0E75D3956A17BA71C425830B6D56E2C7C5C7A96559CDEEFA74 and prompt SHA256 9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA. The effective IQ3/IQ2/MTP/profile/argument/environment identity was copied from the verified baseline command.json.
OUTPUT_ROOT: C:\Users\User\Strata-Adrian\runs\LUNA-20261009-002-rerun\phase0-baseline-corrected2\control

RUN_RESULTS:
- run-01: valid=true, exit=0, timeout=false, 36.51 tok/s
- run-02: valid=true, exit=0, timeout=false, 35.08 tok/s
- run-03: valid=true, exit=0, timeout=false, 35.76 tok/s
- run-04: valid=true, exit=0, timeout=false, 35.41 tok/s
- run-05: valid=true, exit=0, timeout=false, 36.26 tok/s
- Mean: 35.80 tok/s; median: 35.76 tok/s; min/max: 35.08/36.51 tok/s; sample CV: 1.64%

OUTPUT_INTEGRITY: Five run directories were found; each contains candidate.json, command.json, process-before.json, process-after.json, stdout.log, stderr.log, and result.json.
PROCESS_CHECK: No strata, llama, benchmark, or related test process remained after the rerun.
SOURCE_CHANGE: None. No source, model, binary, Git reset/clean/merge/rebase, or benchmark tuning change was performed.
UNRESOLVED: None for this reproduction task.
NEXT_STEP: Treat LUNA-20261009-002 as COMPLETED; do not claim or rerun it again.
<!-- LUNA_PUBLISHED_TASK_ID: LUNA-20261009-002 -->

[LUNA_REPORT]
TASK_ID: LUNA-20261009-004
STATUS: COMPLETED
TIME_ASIA_TAIPEI: 2026-10-09T19:39:20+08:00
EXECUTION_MODE: PHASE_A_READ_ONLY_IQ3_VARIANCE_FORENSICS

RESOLUTION: Phase A read-only analysis covered the requested old 10-run and new 5-run datasets. The large old variance is strongly associated with measured CPU pool and file-tier work, while MTP acceptance metrics are weakly associated. Binary and prompt identity were constant across all 15 valid runs. Phase B was not needed and was not run.

REMOTE_HOST: DESKTOP-LKMLUPC (verified with StrictHostKeyChecking, BatchMode, and hostname check)
REMOTE_ROOT: C:\Users\User\Strata-Adrian
REMOTE_SOURCE: C:\Users\User\Strata-Adrian\repo\Strata-Adrian-control
REMOTE_RUNTIME: C:\Users\User\Strata-Adrian\env\IQ3-20261008
REMOTE_BRANCH: main
REMOTE_SOURCE_HEAD: d8bd709bcb336c604d684dad6ddf83796dac87ac
REMOTE_DIRTY_FILES: four pre-existing untracked .codex/handoffs files; preserved unchanged

FROZEN_IDENTITY: All 15 runs were valid and used binary SHA256 E67EB500C2F43B0E75D3956A17BA71C425830B6D56E2C7C5C7A96559CDEEFA74 and prompt SHA256 9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA. Checked effective output_tokens=1024, prompt_tokens=28912, max_context=100000, expert_cache=3604, adaptive cadence every 3/swaps16/decay0.60, and pool workers=9; no identity-changing difference was found in the inspected command/result/candidate fields.

RAW_PROVENANCE:
- Old 10-run root: C:\Users\User\Strata-Adrian\env\IQ3-20261008\overnight-20261009\phase9-soak\safe\run-01..run-10
- New 5-run root: C:\Users\User\Strata-Adrian\runs\LUNA-20261009-002-rerun\phase0-baseline-corrected2\control\run-01..run-05
- A second old-root mirror under C:\Users\User\Strata-IQ3-20261008\overnight-20261009\phase9-soak\safe was compared by command/result/candidate SHA256 and was byte-identical; it was not counted as another 10 samples.

GROUP_SUMMARY:
- Old n=10: mean 35.01 tok/s; median 35.565; min/max 31.31/38.69; sample CV 7.08%; mean pool 29.565 ms/round; mean file tier 11085.45 MB; mean GPU hit 0.61294.
- New n=5: mean 35.804 tok/s; median 35.76; min/max 35.08/36.51; sample CV 1.65%; mean pool 28.4242 ms/round; mean file tier 9754.38 MB; mean GPU hit 0.61004.
- Across all 15 rows, Pearson r(speed, pool_ms)=-0.94608, r(speed, file_mb)=-0.94701, r(speed, gpu_hit)=0.81473, r(speed, swaps)=0.41004, r(speed, spec_windows)=0.40556, r(speed, mtp_accepted)=0.19002, and r(speed, mtp_offered)=0.17901.
- Extremes are consistent with this pattern: old run-01=38.69 tok/s with pool=23.641 ms and file=6620.2 MB; old run-03=31.31 tok/s with pool=36.357 ms and file=17605.7 MB. The new five remain in a narrower pool/file range and therefore do not reproduce the old extremes.

OUTPUT_ACCOUNTING:
- Every run ended with output_tokens=1024 and valid=true; 1024 is decode output length, not context length.
- stdout.log was 23 lines and approximately 169-170 KB per run. It contains aggregate speculation/draft acceptance and pool/adaptive-tier summaries. Accepted ratios overlap across groups (approximately 0.826-0.884), so they do not explain the speed spread by themselves.
- No output-token hash, output hash, or per-token timestamp was present in the targeted stdout scan for any of the 15 runs. These fields remain UNKNOWN; stdout.log file identity is not a substitute for token-stream identity.

HYPOTHESIS: The observed 38.69 tok/s point is a favorable runtime/I/O state, not evidence of a stable code-path throughput level. Within this fixed identity, increased CPU expert-pool time and file-tier traffic move with lower decode speed. The old 10-run set sampled a wider runtime state than the new five; GPU-hit and MTP aggregates do not support treating MTP acceptance as the primary cause.

PHASE_B_DECISION: Not run. Phase A extracted all available per-run identity and aggregate metrics, found no missing field that required the plan's conditional three-run diagnostic campaign, and already supplies a testable dominant correlate. No benchmark, sweep, restart, process stop, source change, model change, or fallback was performed.

NEXT_CONTROLLED_TEST: If later authorized, use one matched-control comparison that holds binary/prompt/flags/output length and resident policy fixed, records pool/file-tier timings and machine state, and adds output-token identity/timestamp instrumentation. Do not infer causality from this retrospective correlation alone.

OUTPUT_ROOT: C:\Users\User\Strata-Adrian\runs\LUNA-20261009-004-iq3-variance-root-cause
OUTPUT_FILES: per_run_summary.csv (15 rows), stdout_log_scan.csv (15 rows), provenance.txt

COVERAGE: Full requested 15-run command/result/candidate summary and identity comparison; duplicate old mirror collapsed after byte-identical SHA check. Targeted stdout.log scan covered all 15 files for accepted/output-token/hash/timestamp keywords and 64-hex hash-like values. Large logs were processed server-side by byte/line counts and regex samples, not loaded wholesale into the report. process-before/process-after metadata was available in every run, but no full stderr/protocol semantic audit was performed. Remaining blind spots are missing per-token identity/timing and unmeasured causal variables outside the recorded fields.

SOURCE_CHANGE: None. No remote source, model, binary, Git state, or process was modified.
<!-- LUNA_PUBLISHED_TASK_ID: LUNA-20261009-004 -->

[LUNA_REPORT]
TASK_ID: LUNA-20261009-005
STATUS: PARTIAL
TIME_ASIA_TAIPEI: 2026-10-09T21:43:06+08:00
EXECUTION_MODE: PHASED_1024_ONLY_MATCHED_AB

RESOLUTION: The amended owner plan was re-read and applied. The original 4096-output stages were allowed to terminate normally, preserved under the campaign output root, and excluded from the amended 1024-token evidence. Two 1024-token runtime candidates were tested. resident-budget-gib=21 was rejected. pool-workers=8 showed a raw +8.09% paired-median label, but promotion was blocked because the frozen-control sample CV was 9.75%, above the plan's 5% variance gate. No candidate is promoted.

REMOTE_HOST: DESKTOP-LKMLUPC (verified with StrictHostKeyChecking, BatchMode, and hostname checks)
REMOTE_SOURCE: C:\Users\User\Strata-Adrian\repo\Strata-Adrian-control
REMOTE_RUNTIME: C:\Users\User\Strata-Adrian\env\IQ3-20261008
REMOTE_OUTPUT_ROOT: C:\Users\User\Strata-Adrian\runs\iq3-autonomous-campaign-005
REMOTE_BRANCH / HEAD: main / d8bd709bcb336c604d684dad6ddf83796dac87ac
REMOTE_AGENTS: C:\Users\User\Strata-Adrian\repo\Strata-Adrian-control\AGENTS.md read; source AGENTS SHA256 6F10971D9DC14BD7BE42DABF8C83C32BB7BD01894F5A791F0940AEB8E87607CC
REMOTE_DIRTY_FILES: four pre-existing untracked .codex/handoffs files; preserved unchanged
PLAN_SHA256: cb29ed13147fd8275899d9b875ce829ab79b6bb0
INBOX_SHA256: 54298770b85968b21e9b84952299c25cb1d3290a
OUTBOX_SHA256_BEFORE_APPEND: 27529a5c1f1cd4d7393d28007beab656572a7b1a

FROZEN_IDENTITY: All valid amended-plan runs used binary SHA256 E67EB500C2F43B0E75D3956A17BA71C425830B6D56E2C7C5C7A96559CDEEFA74, prompt SHA256 9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA, prompt_tokens=28912, max_context=100000, and accepted output_tokens=1024. The tested control kept expert-cache=3604, pool-workers=9, adapt-every=3, adapt-swaps=16, adapt-decay=0.60, spec=6, spec-min-p=0.75, and resident-budget-gib=20 unless the single factor was changed.

RESUME_AND_PROCESS_PROOF: The laptop guard's same-task resume action was exercised after each idle checkpoint. Remote controller locks and read-only process checks prevented replacement launches. Total preserved command.json files under the campaign root: 22; result.json files: 21; one partial raw run without result.json was preserved after an isolated post-run evidence-kind KeyError in the old 4096 controller. At final report checkpoint, remote process count was 0. The 4096 runs are not counted as valid amended-plan controls.

AMENDED_1024_PHASE_RESULTS:
- H3 resident-budget-gib=21 vs 20, 3 matched pairs, all six valid with exit=0 and decode_tokens=1024.
  - Control: 35.14, 36.10, 37.54 tok/s; median 36.10.
  - Candidate: 36.68, 32.55, 31.06 tok/s; median 32.55.
  - Paired deltas: +4.38%, -9.83%, -17.26%; median delta -9.83%.
  - Decision: REJECT_OR_HOLD.
  - Decision path: C:\Users\User\Strata-Adrian\runs\iq3-autonomous-campaign-005\phase3-1024\resident-budget-21-vs-20\decision.json
- H4 pool-workers=8 vs 9, 3 matched pairs, all six valid with exit=0 and decode_tokens=1024.
  - Control: 32.50, 37.11, 30.80 tok/s; median 32.50; sample CV 9.75%.
  - Candidate: 35.01, 35.13, 35.25 tok/s; median 35.13.
  - Raw paired deltas: +7.72%, -5.34%, +14.45%; raw median delta +8.09%.
  - Decision: REJECT_OR_HOLD because the control CV exceeds the 5% promotion gate; the controller's initial promote label was preserved in decision.controller_original.json and corrected in decision.json.
  - Decision path: C:\Users\User\Strata-Adrian\runs\iq3-autonomous-campaign-005\phase4-1024-pool-workers\pool-workers-8-vs-9\decision.json

REFERENCE: The previously validated 002 five-run 1024-token reference remains median 35.76 tok/s with approximately 1.64% CV. The amended 005 candidate results do not establish a new stable improvement over that reference.

BEST_STABLE_1024_MEDIAN: 35.76 tok/s from the existing validated 002 reference. No 005 candidate was promoted.
QUALITY: Existing runner does not assess output quality regression; no quality claim is made.
SOURCE_CHANGE: None. No remote Strata source, model, production binary, origin, branch, Git state, temperature, unrelated process, or unrelated data was changed. Only isolated campaign controllers/metadata were added under the authorized campaign output root; the local handoff guard already contained the minimal resume support.

STOP_REASON: Evidence is sufficient to reject resident-budget=21 and to hold pool-workers=8 pending variance isolation. The amended plan's 1024-only requirement was satisfied for the valid comparison runs. No source-level candidate was justified before resolving control variance.
RECOMMENDED_NEXT_AUTONOMOUS_CAMPAIGN: Keep output_tokens=1024 and frozen identity. First isolate the control-side runtime/I/O variance that produced 9.75% CV, then independently validate pool-workers=8 with at least three matched pairs before any promotion. Do not treat the raw +8.09% as causal or stable.

COVERAGE: Full command/result/candidate metadata was enumerated for all 22 attempted benchmark processes under the campaign root; 21 completed result.json files were summarized and the one partial raw run was identified and preserved. Per-run stdout/stderr and process snapshots remain at their phase directories; large logs were not loaded wholesale into this report. The runner has no output-token digest or quality evaluator, so token-stream identity and quality remain unverified.

OUTPUT_PATHS:
- C:\Users\User\Strata-Adrian\runs\iq3-autonomous-campaign-005\campaign_state.json
- C:\Users\User\Strata-Adrian\runs\iq3-autonomous-campaign-005\phase1-long-output\summary.json (legacy 4096 stage; excluded from amended evidence)
- C:\Users\User\Strata-Adrian\runs\iq3-autonomous-campaign-005\phase3-1024\resident-budget-21-vs-20\decision.json
- C:\Users\User\Strata-Adrian\runs\iq3-autonomous-campaign-005\phase4-1024-pool-workers\pool-workers-8-vs-9\decision.json

<!-- LUNA_PUBLISHED_TASK_ID: LUNA-20261009-005 -->

[LUNA_REPORT]
TASK_ID: LUNA-20261009-006
STATUS: COMPLETED
TIME_ASIA_TAIPEI: 2026-10-09 22:41

## Result

Task 006 completed the authorized fresh-process 1024-token worker-variance validation. No source, binary, model, temperature, or remote Git state was changed. The worker8 candidate is rejected/held; no promotion is authorized.

- Remote host: `DESKTOP-LKMLUPC` (`User@100.126.147.41`)
- Remote source/worktree: `C:\Users\User\Strata-Adrian\repo\Strata-Adrian-control`
- Source HEAD: `d8bd709bcb336c604d684dad6ddf83796dac87ac`
- Remote source worktree: dirty only in four pre-existing untracked `.codex/handoffs/*` files; no task source files changed
- Remote AGENTS SHA256: `6F10971D9DC14BD7BE42DABF8C83C32BB7BD01894F5A791F0940AEB8E87607CC`
- Active binary SHA256: `E67EB500C2F43B0E75D3956A17BA71C425830B6D56E2C7C5C7A96559CDEEFA74`
- Workload identity: frozen prompt 28,912 tokens, max context 100,000, accepted output 1,024 tokens, control `pool-workers=9`, candidate `pool-workers=8`
- Fresh validation: 5 interleaved matched pairs, 10 valid processes total; all 10 outputs passed the 1,024-token validity check

## Measured evidence

Pair results (`control -> candidate`, decode tok/s; candidate delta):

1. `24.83 -> 28.22` (`+13.65%`)
2. `26.71 -> 27.09` (`+1.42%`)
3. `22.06 -> 18.97` (`-14.01%`)
4. `23.36 -> 20.34` (`-12.93%`)
5. `22.33 -> 16.75` (`-24.99%`)

- Control median: `23.36 tok/s`; sample CV: `8.09%`
- Candidate median: `20.34 tok/s`; sample CV: `22.86%`
- Paired median delta: `-12.93%`
- Historical task 002 baseline median: `35.76 tok/s`
- Decision: `REJECT_OR_HOLD`
- Promotion blocked by the variance/historical-reference gate: both CVs exceed 5%, candidate median is below the historical baseline, and paired median delta is negative

Original remote evidence:

- Decision: `C:\Users\User\Strata-Adrian\runs\iq3-variance-continuation-006\phase1-worker8-validation\pool-workers-8-vs-9\decision.json`
- Phase root: `C:\Users\User\Strata-Adrian\runs\iq3-variance-continuation-006\phase1-worker8-validation`
- Durable checkpoint: `C:\Users\User\Strata-Adrian\runs\iq3-variance-continuation-006\campaign_state.json`
- Preserved preflight evidence: `C:\Users\User\Strata-Adrian\runs\iq3-variance-continuation-006\preflight_previous_evidence.json`

## Limits and next step

The existing runner did not assess quality regression, and task 006 did not capture temperature or power telemetry. Those are unresolved measurement limits, not grounds to promote the candidate. The next step is to await a new explicit GitHub plan; do not rerun task 006 or promote worker8 from this evidence.
<!-- LUNA_PUBLISHED_TASK_ID: LUNA-20261009-006 -->

[LUNA_REPORT]
TASK_ID: LUNA-20261009-007
STATUS: COMPLETED
TIME_ASIA_TAIPEI: 2026-10-10T00:10:26+08:00
EXECUTION_MODE: PHASED_IQ3_HOTPATH_SOURCE_AND_RUNTIME_VALIDATION

RESOLUTION: The authorized 1024-token campaign completed three sequential mechanism candidates and did not promote any candidate. The measured slowdown is consistently associated with higher file-tier traffic and CPU expert-pool time. Page-only lookahead, staged blob prefetch, and disabling Windows PrefetchVirtualMemory all failed the paired speed gate. No production source, active binary, model, temperature, or main source Git state was changed.

REMOTE_HOST: DESKTOP-LKMLUPC (User@100.126.147.41; strict host-key and hostname identity verified)
REMOTE_ROOT: C:\Users\User\Strata-Adrian
REMOTE_SOURCE: C:\Users\User\Strata-Adrian\repo\Strata-Adrian-control
REMOTE_SOURCE_AGENTS: C:\Users\User\Strata-Adrian\repo\Strata-Adrian-control\AGENTS.md (read)
REMOTE_BRANCH / HEAD: main / d8bd709bcb336c604d684dad6ddf83796dac87ac
REMOTE_SOURCE_DIRTY_FILES: four pre-existing untracked .codex/handoffs/* files; preserved unchanged
ISOLATED_SOURCE_WORKTREE: C:\Users\User\Strata-Adrian\runs\iq3-hotpath-optimization-007\source-lookahead-stage
ISOLATED_SOURCE_CHANGE: one-line RouterLookahead warm -> prefetch change, built and tested only in the isolated worktree; not promoted or merged

FROZEN_IDENTITY: All 18 new matched benchmark processes used prompt_tokens=28912, max_context=100000, accepted output_tokens=1024, the same model/quant/tokenizer/sampling/spec/profile identity, and the frozen baseline runtime arguments. Control binary SHA256 was E67EB500C2F43B0E75D3956A17BA71C425830B6D56E2C7C5C7A96559CDEEFA74. The isolated source candidate binary SHA256 was 14C4C0CD3F35E26F10DACE3B674B9AE7C5610DB322BA81D8EEA0E75F457A67E3. Prompt SHA256 was 9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA.

MEASURED_RESULTS:
- Phase 1 runtime lookahead: 3 matched pairs, all six valid. Candidate STRATA_LOOKAHEAD=1 paired deltas were -11.18%, -6.39%, +2.07%; median -6.39%. Candidate file-tier MB for the three pairs was 14878.2, 15955.2, 8016.3 versus control 7219.7, 8732.4, 9866.4; candidate CPU pool ms was 34.892, 32.460, 25.382 versus control 24.820, 25.964, 30.338. Decision: reject.
- Phase 2 isolated source candidate: 3 matched pairs, all six valid. RouterLookahead::run used prefetch instead of warm in the isolated binary. Paired deltas were -16.37%, -2.75%, -4.94%; median -4.94%. Candidate file-tier MB was 19847.3, 10785.0, 15189.5 versus control 8248.8, 8770.9, 14824.7; candidate CPU pool ms was 36.664, 26.337, 34.969 versus control 27.487, 24.688, 34.603. Decision: reject; no source promotion.
- Phase 3 runtime mechanism control: 3 matched pairs, all six valid. Candidate STRATA_FETCH_PVM=0 paired deltas were -5.92%, -12.73%, -11.40%; median -11.40%. Candidate file-tier MB was 10315.6, 15111.7, 13469.1 versus control 8340.0, 8489.0, 8255.5; candidate CPU pool ms was 31.001, 33.460, 34.287 versus control 27.756, 26.815, 29.109. Decision: reject.

ROOT_CAUSE_EVIDENCE: The prior read-only 15-run analysis measured Pearson r(speed, cpu_pool_ms)=-0.94608 and r(speed, file_tier_MB)=-0.94701. The new matched tests reproduce the same direction: the approximately 30 tok/s rows coincide with high file-tier traffic and higher pool time. The lookahead/prefetch candidates increased or failed to reduce those quantities, so the current evidence supports file-tier/stage-cache traffic or admission/churn as the active slowdown mechanism. The PVM-off result makes PVM hint overhead alone an insufficient root cause. The exact lower-level admission/churn cause remains unresolved; no causal claim beyond these matched measurements is made.

DECISION: No candidate reached the plan's >=3% stable paired improvement gate. No binary or source change was promoted. The best stable reference remains the prior corrected five-run baseline median 35.76 tok/s (LUNA-20261009-002); this task's controls were intentionally interleaved and are not substituted for that reference.

ORIGINAL_REMOTE_EVIDENCE:
- Phase 1 durable state/results: C:\Users\User\Strata-Adrian\runs\iq3-hotpath-optimization-007\campaign_state.json and C:\Users\User\Strata-Adrian\runs\iq3-hotpath-optimization-007\phase1_lookahead_results.json
- Phase 1 raw run root: C:\Users\User\Strata-Adrian\runs\iq3-hotpath-optimization-007\phase1-lookahead-1024
- Phase 2 durable state/results: C:\Users\User\Strata-Adrian\runs\iq3-hotpath-optimization-007\phase2_prefetch_stage_state.json and C:\Users\User\Strata-Adrian\runs\iq3-hotpath-optimization-007\phase2_prefetch_stage_results.json
- Phase 2 raw run root: C:\Users\User\Strata-Adrian\runs\iq3-hotpath-optimization-007\phase2-prefetch-stage-1024
- Phase 2 source worktree/build: C:\Users\User\Strata-Adrian\runs\iq3-hotpath-optimization-007\source-lookahead-stage and C:\Users\User\Strata-Adrian\runs\iq3-hotpath-optimization-007\build-lookahead-stage
- Phase 3 durable state/results: C:\Users\User\Strata-Adrian\runs\iq3-hotpath-optimization-007\phase3_fetch_pvm_state.json and C:\Users\User\Strata-Adrian\runs\iq3-hotpath-optimization-007\phase3_fetch_pvm_results.json
- Phase 3 raw run root: C:\Users\User\Strata-Adrian\runs\iq3-hotpath-optimization-007\phase3-fetch-pvm-1024

PROCESS_AND_STATE_CHECK: Final remote process query found no strata.exe or python.exe process. Main source remained on main at d8bd709; only the four pre-existing handoff files were dirty. No process was stopped.

COVERAGE: Full task-plan Phase 0 evidence review covered the relevant 002/004/005/006 reports and raw command/result identity. The new candidate scope covered all 18 attempted benchmark processes, all 18 valid result.json files, all three 3-pair matched phases, source audit/build evidence, and final process/Git checks. Source inspection covered the relevant ExpertSource warm/prefetch/fill_many, RouterLookahead, and expert_pool_dispatch_multi paths; it was not a full repository audit. Large stdout/stderr logs were not loaded wholesale; runner-produced result.json and machine snapshots were used. Not audited in this cycle: full stderr semantics, per-token output identity/timestamps, quality regression, power/thermal telemetry, and a complete admission/churn causal trace.

NEXT_STEP: Await a new explicit plan targeting stage-cache admission/churn instrumentation or a narrowly specified cache policy experiment. Do not promote or rerun any rejected candidate from this task.
<!-- LUNA_PUBLISHED_TASK_ID: LUNA-20261009-007 -->

[LUNA_REPORT]
TASK_ID: LUNA-20261010-008
STATUS: COMPLETED
TIME_ASIA_TAIPEI: 2026-10-10 00:42:57 +08:00
EXECUTION_MODE: PHASE0_STAGE_CACHE_TRACE_AND_THREE_PAIRED_CANDIDATE_TESTS

RESOLUTION: Phase 0 traced the active file-tier/stage path, then tested one narrowly scoped isolated candidate. Extending stage-buffer reuse from 3 to 6 layer epochs and from 256 to 512 assemblies passed the plan gate: all three paired deltas were positive and the paired-median decode improvement was +6.56%. The candidate is accepted as the next source candidate, but the production main source and active binary were not changed or merged in this cycle.

REMOTE_HOST: DESKTOP-LKMLUPC (hostname and SSH identity verified)
REMOTE_ROOT: C:\Users\User\Strata-Adrian
REMOTE_SOURCE: C:\Users\User\Strata-Adrian\repo\Strata-Adrian-control
REMOTE_BRANCH / HEAD: main / d8bd709bcb336c604d684dad6ddf83796dac87ac
REMOTE_SOURCE_DIRTY_FILES: four pre-existing untracked .codex/handoffs/* files; preserved unchanged
ISOLATED_SOURCE_WORKTREE: C:\Users\User\Strata-Adrian\runs\iq3-stage-cache-optimization-008\source-trace
ISOLATED_BUILD: C:\Users\User\Strata-Adrian\runs\iq3-stage-cache-optimization-008\build-trace-cuda
ISOLATED_CANDIDATE_BINARY: C:\Users\User\Strata-Adrian\runs\iq3-stage-cache-optimization-008\build-trace-cuda\Release\strata.exe
ISOLATED_CANDIDATE_BINARY_SHA256: 819e22066f2103ea5f9a79fe8f9debe1f3e69f8be67522f308921df22461d963
ISOLATED_BASELINE_BINARY: C:\Users\User\Strata-Adrian\runs\iq3-stage-cache-optimization-008\strata-baseline-trace.exe
ISOLATED_BASELINE_BINARY_SHA256: 354a5366b0c98e2e8980cadc0f74681d1e62fb5dbfa7b7d9551a6d51ff9ec7f5

FROZEN_WORKLOAD: prompt_tokens=28912; max_context=100000; output_tokens=1024; same IQ3_XXS model/quant/tokenizer/prompt/sampling/spec/profile identity; spec=6; spec-min-p=0.75; kv=q4_0; kv-resident=20480; expert-cache=3604; pool-workers=9; resident-budget-gib=20; prefill=auto; suffix-draft=3; mtp-max-t=3; pool-affinity=all; adapt-every=3; adapt-swaps=16; adapt-decay=0.60. Environment was STRATA_FETCH_ADMIT=0, STRATA_RESIDENT_HEADROOM_GIB=3, STRATA_ADAPT_IF_MISS=1, STRATA_EXPERT_FILE_CACHE=1, STRATA_PF_FUSED=1, STRATA_LOOKAHEAD=0, plus STRATA_EXPERT_TRACE=1 for both baseline and candidate.

SOURCE_CANDIDATE: isolated-only change to FileExpertSource stage reuse eligibility: kStageAge 3 -> 6 and kStageSeq 256 -> 512. Diagnostic instrumentation was off by default and used identically in both paired binaries. Isolated diff stat was 3 files, 84 insertions and 3 deletions; the product candidate logic is the two reuse-window constants. Source file SHA256: include/strata/core/expert_source.hpp=8d88533e78090c1678143eecce604d6750a43e6d86dc9a9efad81c46b0537aa3; src/core/expert_source.cpp=6451e2c151f24f70d0afeedc5e76f1f4a0b4227d9c12315eecf9c017569a987a; src/program/generate.cpp=69abdc72b2abf562921876cb7220054435156bb892c1eceec99a1e35e1d8c27c.

PHASE0_CAUSAL_TRACE: the static profile/cache was already full at resident=3148/3148. All traced runs reported R4 admission trace attempted=0, refused=0, full=0, quota=0. Therefore R4 cache_refused is a CPU/graph miss aggregate, not ExpertCache::admit refusal in this workload. The active stage path had waits=0, so the measured issue is not stage-fill thread waiting. The trace-on control showed claims=29592, hits=19557, fills=10035, refills=4311, stage_evictions=9779, waits=0, bytes=17760332800; this is whole-process prompt+decode trace. Refill rate was 42.98% of fills and stage replacement was 97.45% of fills. Highest refill layers were 42, 45, 47, 46, 38, 37, 43, 41, 44 and 39. The trace summary's microsecond field was fixed for the candidate runs; existing decode-only file timing remains the comparison metric.

EXTERNAL_RECONNAISSANCE:
- https://github.com/Niko1221/Strata/issues/831: profile-seeded hybrid admission is relevant in general, but rejected for this run because the current static cache was full and had zero dynamic admission attempts.
- https://github.com/Niko1221/Strata/issues/369: per-layer cursor/fill issues are already fixed in the current source; not repeated.
- https://github.com/Niko1221/Strata/pull/1237: pinned stage buffers were inspected; not borrowed because this trace showed no H2D/fill wait signal.
- spideytznn/Strata: RAMPromotion and ExpertSource residency mechanisms were inspected; no exact transplant identified, and the current trace pointed more directly to stage reuse churn.
- https://github.com/ggml-org/llama.cpp/discussions/25779: merged explicit-read mechanism was inspected; current Strata already has same-layer dispatch deduplication and nearby-range merging, so no blind port was made.

PAIRED_RESULTS: all six paired runs completed with full decode/file/trace output and no OOM, CUDA error, crash, or validation failure. Candidate is stage reuse 6/512; control is 3/256.

| Pair | Control decode tok/s | Candidate decode tok/s | Delta | Control file MB | Candidate file MB | Control file ms/round | Candidate file ms/round | Control refills -> candidate | Control evictions -> candidate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 36.43 | 36.69 | +0.71% | 11191.0 | 8797.3 | 7.8 | 6.4 | 5017 -> 3573 | 10682 -> 9199 |
| 2 | 32.58 | 36.48 | +11.97% | 13542.5 | 7233.9 | 10.2 | 5.6 | 6029 -> 3068 | 12079 -> 8369 |
| 3 | 34.78 | 37.06 | +6.56% | 10194.8 | 7285.6 | 7.5 | 5.6 | 4404 -> 2954 | 10308 -> 8444 |

SUMMARY_STATISTICS: control median=34.78 tok/s; candidate median=36.69 tok/s; paired median delta=+6.56%; all three deltas positive. Median file-tier MB delta=-28.54%; median refill delta=-32.92%; median stage-eviction delta=-18.08%. Candidate stage_buffers=512 and emitted 1.11 GiB in-use assembled blobs; control stage_buffers=256. Candidate available-RAM readings were 23.33, 23.40 and 23.45 GiB before the fixed 20 GiB resident allocation, with no OOM or process failure. The candidate mechanism moved in the expected direction and crossed the plan's >=3% stable paired gate.

OUTPUT_ROOTS:
- C:\Users\User\Strata-Adrian\runs\iq3-stage-cache-optimization-008\control-off
- C:\Users\User\Strata-Adrian\runs\iq3-stage-cache-optimization-008\control-on
- C:\Users\User\Strata-Adrian\runs\iq3-stage-cache-optimization-008\pair1-control
- C:\Users\User\Strata-Adrian\runs\iq3-stage-cache-optimization-008\pair1-candidate
- C:\Users\User\Strata-Adrian\runs\iq3-stage-cache-optimization-008\pair2-control
- C:\Users\User\Strata-Adrian\runs\iq3-stage-cache-optimization-008\pair2-candidate
- C:\Users\User\Strata-Adrian\runs\iq3-stage-cache-optimization-008\pair3-control
- C:\Users\User\Strata-Adrian\runs\iq3-stage-cache-optimization-008\pair3-candidate

FINAL_MACHINE_CHECK: no strata process remained after the runs; RTX 4070 reported 605 MiB used, 11406 MiB free, 0% utilization and 41 C; free physical RAM was 25.79 GiB; C: free space was 41.06 GiB; KIOXIA-EXCERIA PRO SSD HealthStatus was Healthy. No process was stopped. The run output roots remain on the remote host; no cleanup was performed.

COVERAGE: Mandatory external references in the active plan were inspected. Relevant active source paths were traced in ExpertCache, FileExpertSource stage claim/fill/read paths, and expert dispatch deduplication; this was not a full repository audit. Phase 0 used two isolated controls (trace off/on) and the candidate validation used three sequential interleaved pairs, six new benchmark processes. All benchmark logs were scanned for decode, file-tier, trace, OOM/error and validation markers; large logs were not pasted wholesale. Remaining blind spots are output quality regression, per-token timing/output identity, and power telemetry; they were not required by this plan and no quality claim is made.

SOURCE_CHANGE: no production source, active binary, model, temperature, remote main branch, or existing dirty file was changed. The accepted candidate remains isolated for the next explicitly authorized promotion/deployment step.
NEXT_STEP: use the isolated 6/512 candidate as the production-promotion candidate in a separately authorized source/deployment step; do not repeat the rejected lookahead, prefetch, PVM, per-layer-cache, or profile-admission tests without a new causal question.
<!-- LUNA_PUBLISHED_TASK_ID: LUNA-20261010-008 -->

[LUNA_REPORT]
TASK_ID: LUNA-20261010-009
task_id: LUNA-20261010-009
status: COMPLETED
generated_at_utc: 2026-10-10T02:17:47.471Z

## Result

Clean validation of the stage-cache reuse candidate completed in an isolated reversible worktree. The candidate passed the performance gate and was deployed locally through a reversible backup. One independent post-deploy smoke run completed successfully. No fallback was used, and the main source remained unchanged.

## Source and binaries

- Remote host: `DESKTOP-LKMLUPC` (`User@100.126.147.41`).
- Authoritative main source: `C:\Users\User\Strata-Adrian\repo\Strata-Adrian-control`.
- Main source SHA: `d8bd709bcb336c604d684dad6ddf83796dac87ac`.
- Main source status remained limited to the four pre-existing `.codex/handoffs/*` untracked files; no main source file was changed.
- Isolated worktree: `C:\Users\User\Strata-Adrian\runs\iq3-stage-cache-promotion-009\source-clean`.
- Candidate source-only change in the isolated worktree:
  - `include/strata/core/expert_source.hpp`: `kStageAge 3 -> 6`.
  - `src/core/expert_source.cpp`: `kStageSeq 256 -> 512`.
- Clean baseline binary SHA256: `5f03f4616237f84f7307716134a8fe7be706266387becb5140db49b7e153c59f`.
- Candidate binary SHA256: `59292d5ccbcd200bd209ae04ee59e795da979b6affd175c870e673f9ffaecec3`.

## Benchmark identity

Five interleaved matched pairs were run with the same accepted 1024-token IQ3 identity used by task 008. Both binaries were built from the same main SHA, with diagnostic tracing explicitly cleared for every run. Environment was:

`STRATA_FETCH_ADMIT=0`, `STRATA_RESIDENT_HEADROOM_GIB=3`, `STRATA_ADAPT_IF_MISS=1`, `STRATA_EXPERT_FILE_CACHE=1`, `STRATA_PF_FUSED=1`, `STRATA_LOOKAHEAD=0`, `STRATA_EXPERT_TRACE=`.

The command used the IQ3 pack, the two IQ3 native shards, the existing MTP runtime, `--spec 6 --spec-min-p 0.75 --max-context 100000 --kv q4_0 --kv-resident 20480`, the existing learned-heart profile, `--expert-cache 3604 --pool-workers 9 --prefill auto --stats --max-new 1024 --suffix-draft 3 --resident-budget-gib 20 --mtp-max-t 3 --pool-affinity all --adapt-every 3 --adapt-swaps 16 --adapt-decay 0.60`, and the existing neuro token file. Temperature was not changed.

## Paired results

| Pair | Control tok/s | Candidate tok/s | Decode delta | File MB delta | File-read ms/round delta | Blob-read delta | CPU pool-call delta | Resident RAM delta |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 35.37 | 37.93 | +7.24% | -35.24% | -36.00% | -14.09% | -15.30% | +0.17 GiB |
| 2 | 35.72 | 38.07 | +6.58% | -30.15% | -35.21% | -18.38% | -9.49% | -0.13 GiB |
| 3 | 37.13 | 35.55 | -4.26% | +5.00% | +3.28% | +37.60% | +9.17% | -0.27 GiB |
| 4 | 31.93 | 37.31 | +16.85% | -51.36% | -53.04% | -25.68% | -26.71% | 0.00 GiB |
| 5 | 36.98 | 39.01 | +5.49% | -18.37% | -30.19% | +11.58% | -22.17% | 0.00 GiB |

Paired medians: decode `+6.58%`; file-tier traffic `-30.15%`; file-read time `-35.21%`; file blob reads `-14.09%`; CPU pool-call time `-15.30%`. Pair 3 regressed, so the conclusion is a positive paired median with measurable run-to-run variance, not a claim that every run improves.

## Correctness, stability, and memory

- All 10 runs returned SSH/process success.
- All 10 stdout logs contained a 1024-token decode line and exactly 1024 output tokens.
- All 10 stderr logs captured the six 1/2/3/4/5/6-token verification windows with upload/sync `no error`.
- Unexpected fatal/crash/abort/CUDA/invalid/failed/unknown errors: 0/10. The only out-of-memory text was the known expected page-locking refusal followed by working-set minimum plus `VirtualLock`; every run completed normally.
- Candidate resident RAM was 19.49–20.00 GiB versus control 19.32–20.00 GiB; paired maximum increase was +0.17 GiB. Candidate available RAM before mapping was 22.55–23.19 GiB across the runs. No memory regression was observed in this sample.
- Output token sequences are sampled and differed across runs; exact token-stream equality was not used as the correctness criterion. The built-in six-window verification and complete 1024-token output were used instead.

Raw logs are preserved locally under `D:\strata\work\task009_pair1_control.stdout.log` through `task009_pair5_candidate.stderr.log` and remotely under `C:\Users\User\Strata-Adrian\runs\iq3-stage-cache-promotion-009\pair*-{control,candidate}\`.

## Deployment status

The verified target was `C:\Users\User\Strata-Adrian-control-build\strata.exe`. Immediately before deployment, no `strata.exe` or `python.exe` process was present. The original target was backed up to `C:\Users\User\Strata-Adrian\runs\iq3-stage-cache-promotion-009\target-strata-predeploy-20261010T0155Z.exe` with SHA256 `E67EB500C2F43B0E75D3956A17BA71C425830B6D56E2C7C5C7A96559CDEEFA74`, then the candidate was copied to the target. Target and candidate SHA256 both verified as `59292D5CCBCD200BD209AE04EE59E795DA979B6AFFD175C870E673F9FFAECEC3`.

The independent post-deploy smoke run used the same IQ3 model, prompt, sampling, runtime and environment identity as the paired validation, with diagnostic tracing cleared, and wrote to `C:\Users\User\Strata-Adrian\runs\iq3-stage-cache-promotion-009\postdeploy-smoke-20261010T0155Z`. It exited 0, produced 1024 output tokens, and reported `decode 1024 tokens in 29164.3 ms -> 35.11 tok/s`. No fatal/crash/abort/invalid/unknown/CUDA error marker was found, no `strata.exe` or `python.exe` process remained afterward, and rollback was not needed.

## Upstream context and scope

The strongest related prior references already inspected for the predecessor were Niko issue #831 (profile-seeded cache capacity/admission), issue #369 (per-layer cache bug), PR #1237 (pinned stage buffers), `spideytznn/Strata` `plan_ram_promotions`, and llama.cpp discussion #25779 (explicit-read prefetch). The rejected lookahead/PVM candidates were not repeated. This cycle did not re-fetch those references live.

Coverage: 10/10 requested clean benchmark runs completed and all 20 raw stdout/stderr logs were parsed for throughput, file-tier traffic, pool latency, resident RAM, output length, verification windows, and unexpected errors. The main source was inspected at the verified SHA and remained unchanged. Live deployment verification and a fresh upstream refetch were not completed; final hardware telemetry after the runs was also not re-collected because the remote-shell approval layer timed out.

Controller state: no `strata.exe` or `python.exe` process was present in the last successful process check; no benchmark/controller process was intentionally stopped.

Next action: publish this completed report once through the guard, then run the final inspect. Do not rebuild, redeploy, or repeat the 10 paired runs unless the checkpoint or target changes.
<!-- LUNA_PUBLISHED_TASK_ID: LUNA-20261010-009 -->

[LUNA_BLOCKED]
TASK_ID: LUNA-20261010-010
STATUS: BLOCKED
TASK_SOURCE: main
TASK_BRANCH: main
TASK_COMMIT_SHA: 6708ad5ec3a8f9b2960a76958c582a7e50b94a2d
PLAN_SHA: fe0d0379e6193f1cced650634d05a1da849be662
TIME_ASIA_TAIPEI: 2026-10-10

REMOTE_HOST: DESKTOP-LKMLUPC (SSH BatchMode and strict host-key identity verified)
REMOTE_SOURCE: C:\Users\User\Strata-Adrian\repo\Strata-Adrian-control
REMOTE_HEAD: d8bd709bcb336c604d684dad6ddf83796dac87ac
REMOTE_DIRTY_FILES: the four pre-existing .codex/handoffs/* files plus the two Task 010 source files listed below; unrelated files preserved

PHASE_0: The authoritative source initially contained kStageAge=3 and kStageSeq=256. The exact validated Task 009 patch was applied with unique-anchor checks only: include/strata/core/expert_source.hpp now has kStageAge=6 and src/core/expert_source.cpp now has kStageSeq=512. Existing deployed control binary C:\Users\User\Strata-Adrian-control-build\strata.exe remained SHA256 59292D5CCBCD200BD209AE04EE59E795DA979B6AFFD175C870E673F9FFAECEC3.

BLOCKER_LAYER: BUILD_TOOLCHAIN
BLOCKER: cmake --build C:\Users\User\Strata-Adrian-control-build --config Release --parallel 8 failed before compilation because the configured generator is NMake Makefiles and the remote execution environment returned `no such file or directory` while invoking `nmake -f Makefile /nologo`. `where nmake`, `where ninja`, `where msbuild`, and `where cl` found no executable. Therefore the source-to-binary canonicalization could not be reproduced in this cycle.

BENCHMARK_RAW_PATH: NONE
BENCHMARK: No new process was started because Phase 0 build reproduction failed; no benchmark, source-level churn candidate, deployment, temperature change, or process stop was performed.
REMOTE_PROCESS_CHECK: final tasklist queries found no strata.exe or python.exe process.
SOURCE_CHANGE: Only the authorized 6/512 synchronization was written to the two authoritative source files; no churn policy or other optimization was attempted. The source changes remain uncommitted pending a valid build/toolchain check.
NEXT_STEP: Resume only after the existing remote build toolchain can invoke the configured NMake build, or after a new explicit plan authorizes a different build procedure. Do not start Phase 1 or benchmarks before a successful 6/512 canonical build is verified.

COVERAGE: Read the locked Task 010 plan, remote AGENTS.md, both candidate source paths, remote Git HEAD/status, source diff/check, configured CMake build directory, build failure output, existing binary SHA256, GPU state, and final process state. Did not run Phase 1 source inspection, benchmarks, upstream fetch, deployment, or full repository audit because the required Phase 0 build gate failed.
<!-- LUNA_PUBLISHED_TASK_ID: LUNA-20261010-010 -->


[LUNA_REPORT]
TASK_ID: LUNA-20261010-011
STATUS: COMPLETED
TIME_ASIA_TAIPEI: 2026-10-10 12:29:27 +08:00
EXECUTION_MODE: BUILD_RECOVERY_AND_STAGE_CHURN_VALIDATION

RESULT: The Task 010 6/512 source state was rebuilt successfully with the recovered Visual Studio generator/toolchain. The clean canonical smoke passed, then the scoped second-chance stage-churn candidate was tested in an isolated build. The candidate did not meet the performance gate and was rolled back; no candidate binary was deployed.

REMOTE_HOST: DESKTOP-LKMLUPC (SSH BatchMode, strict host-key checking, and hostname identity verified)
REMOTE_SOURCE: C:\Users\User\Strata-Adrian\repo\Strata-Adrian-control
REMOTE_BRANCH / HEAD: main / d8bd709bcb336c604d684dad6ddf83796dac87ac
REMOTE_DIRTY_FILES: four pre-existing untracked .codex/handoffs/* files; preserved unchanged
TASK_SOURCE_BRANCH: main
TASK_COMMIT_SHA: fd7893d6f2a74cc272d3df34fa794b039e31df64
PLAN_SHA: 66f284b2caaf9d3b9e5e5dc08d2c43758d635eb5

TOOLCHAIN_RECOVERY: The old configured NMake build was not usable from the noninteractive shell. Task 009 CMakeCache and vswhere identified Visual Studio 17 2022 BuildTools 17.14.37216.2, MSVC 14.44.35207, CUDA 13.2.78, and CUDA architecture 89. A new isolated Visual Studio 17 2022/x64 build was configured with CMAKE_CUDA_ARCHITECTURES=89 and built successfully.
CANONICAL_BUILD: C:\Users\User\Strata-Adrian\runs\iq3-build-recovery-stage-churn-011\build-canonical-cuda
CANONICAL_BINARY_SHA256: 94543312607ECDEA791F434813C64123E55D017BE0F095E5D0C7448D2DC5A1A7
CANONICAL_SMOKE_RAW: C:\Users\User\Strata-Adrian\runs\iq3-build-recovery-stage-churn-011\canonical-smoke
CANONICAL_SMOKE: exit 0; prefill 32767 tokens at 1003.69 tok/s; decode exactly 1024 tokens at 20.91 tok/s; verification windows completed without CUDA/correctness failure.

FROZEN_IDENTITY: prompt_tokens=28912; max_context=100000; output_tokens=1024; IQ3_XXS pack and two native GGUF shards; existing learned-heart profile; spec=6; spec-min-p=0.75; kv=q4_0; kv-resident=20480; expert-cache=3604; pool-workers=9; prefill=auto; resident-budget-gib=20; mtp-max-t=3; adapt-every=3; adapt-swaps=16; adapt-decay=0.60. Environment and temperature were unchanged.
STAGE_CHURN_CANDIDATE: Added a bounded second-chance reference bit on top of eligible LRU for FileExpertSource staged blobs. The candidate source was built separately; candidate binary SHA256 3B8DAD89080E09DDF570F311C0DEAB49261C0C0F43AE4F5D32CEFC23F96EAC22.
ISOLATED_CANDIDATE_BUILD: C:\Users\User\Strata-Adrian\runs\iq3-build-recovery-stage-churn-011\build-stage-churn-candidate

PAIRED_RESULTS (decode tok/s; candidate delta):
- pair01: control 21.96 -> candidate 21.60 (-1.64%); prefill 943.51 -> 1004.77 tok/s.
- pair02: control 21.85 -> candidate 21.92 (+0.32%); prefill 963.51 -> 986.19 tok/s.
- pair03: control 21.76 -> candidate 21.85 (+0.41%); prefill 953.14 -> 1016.28 tok/s.
- Candidate/control median decode: 21.85 / 21.85 tok/s; median paired decode delta approximately +0.32%.
- Decision: REJECTED. The plan requires median decode improvement >=3%; no confirmation pairs were run.

BENCHMARK_RAW_ROOT: C:\Users\User\Strata-Adrian\runs\iq3-build-recovery-stage-churn-011\matched-pairs
BENCHMARK_RAW_CONTENT: six interleaved run directories, each with stdout.log, stderr.log, command.txt, and status.txt; all six contained a decode line for exactly 1024 tokens.
VALIDITY: No CUDA error, mismatch, assert, abort, segmentation, device-side, or illegal-memory marker was found. The known nonfatal resident-mode page-locking refusal appeared in all runs and each run completed normally. No strata process remained after the campaign.

SOURCE_AFTER_ROLLBACK: The candidate-only stage_ref change was removed. Verified remote git diff contains only the pre-existing Task 010 synchronization: kStageAge=6 and kStageSeq=512. No production source commit, active binary deployment, model, benchmark identity, temperature, or unrelated process was changed.
ACTIVE_DEPLOYMENT: unchanged; the isolated canonical/candidate binaries were not copied to C:\Users\User\Strata-Adrian-control-build.
NEXT_STEP: Await a new explicit plan; do not promote or rerun this rejected candidate.

COVERAGE: Full locked plan and remote AGENTS were read; toolchain caches, source diff, clean build, one canonical smoke, three interleaved matched pairs, all six raw stdout/stderr completion metrics, failure markers, source rollback, and final process state were checked. Large logs were parsed by targeted regex rather than pasted wholesale. Not audited: full repository semantics, output-token equality/quality, power telemetry, and a full causal trace.
<!-- LUNA_PUBLISHED_TASK_ID: LUNA-20261010-011 -->

[LUNA_BLOCKED]
TASK_ID: LUNA-20261010-012
STATUS: BLOCKED
TASK_SOURCE: branch
TASK_BRANCH: coordination/task-012-file-tier-batch-20261010
TASK_COMMIT_SHA: c14bb36c0adf172fc58f23b30097dd379e31c72e
PLAN_SHA: 37c4792e944b3d2f84c1c031d82b6c364b37e82e
TIME_ASIA_TAIPEI: 2026-10-10

REMOTE_HOST: DESKTOP-LKMLUPC (BatchMode, strict host-key checking, hostname verified)
REMOTE_SOURCE: C:\Users\User\Strata-Adrian-control
REMOTE_HEAD: d8bd709bcb336c604d684dad6ddf83796dac87ac
REMOTE_BRANCH: main
REMOTE_DIRTY_FILES: the two pre-existing 6/512 source edits plus four pre-existing .codex/handoffs/* files; preserved unchanged
DEPLOYED_BINARY_SHA256: 59292D5CCBCD200BD209AE04EE59E795DA979B6AFFD175C870E673F9FFAECEC3
CANDIDATE_BINARY_SHA256: 94543312607ECDEA791F434813C64123E55D017BE0F095E5D0C7448D2DC5A1A7

EXECUTION: Phase A completed three interleaved control/candidate pairs under C:\Users\User\Strata-Adrian\runs\iq3-file-tier-012\phase-a. All six status files report exit_code=0. No Task 012 process remained at final inspection.

MEASURED_PAIRS (decode tok/s; file MB; CPU pool ms/token):
- pair01: control 21.47 / 26678.3 / 38.276; candidate 21.09 / 24385.2 / 36.456; paired decode delta -1.77%
- pair02: control 21.32 / 24967.2 / 38.475; candidate 22.27 / 23266.3 / 37.571; paired decode delta +4.46%
- pair03: control 20.37 / 25782.3 / 37.315; candidate 20.82 / 22524.1 / 36.804; paired decode delta +2.21%
- Median paired decode delta: +2.21%; control median 21.32 tok/s; candidate median 21.09 tok/s. This does not meet the plan's >=3% promotion gate.

BLOCKER_LAYER: BENCHMARK_IDENTITY
BLOCKER: The locked plan specifies prompt 28912, but all Phase A command.txt files use C:\Users\User\Strata-IQ3-20261008\overnight-202609\phase8-prompts\prompt-32k.tokens and the raw logs report prefill 32767 tokens. The control/candidate pairs are internally matched, but they are not the authorized 28912-token identity. Do not use them to enter Phase B, promote the candidate, or compare against the 28912-token current-best evidence.

BENCHMARK_RAW_PATH: C:\Users\User\Strata-Adrian\runs\iq3-file-tier-012
SOURCE_CHANGE: None for Task 012. No temperature change, deployment, cleanup, process stop, or fallback was performed.
NEXT_STEP: Obtain an explicit corrected plan or authorization, then repeat only the required Phase A identity with the 28912-token prompt before considering file-tier batching. Preserve these mismatched-prompt raw runs as non-promotable evidence.

COVERAGE: Fresh GitHub connector snapshot and guard inspect/resume; locked plan; remote hostname, source HEAD/status, deployed binary hash, Task 012 process state; all six status files; all six command/environment files; targeted decode/file-tier/pool/verification lines from all twelve stdout/stderr files. Large logs were not loaded wholesale. Full output-token quality/equality and complete stderr semantic audit were not performed.
<!-- LUNA_PUBLISHED_TASK_ID: LUNA-20261010-012 -->

[LUNA_FOLLOWUP]
TASK_ID: LUNA-20261010-012
STATUS: FOLLOWUP_RECORDED
TIME_ASIA_TAIPEI: 2026-10-10
REASON: User-authorized continuation after no new coordination task. This follow-up supplements the original BLOCKED report; it does not replace or reclassify the invalid 32k Phase A evidence.

REMOTE_REPO / SOURCE: C:\Users\User\Strata-Adrian-control / origin https://github.com/Hcl192088/Strata.git
FOLLOWUP_SCOPE: Record the later direct-009 and binary-comparison measurements that were run after the original Task 012 report, with their identity limitations.

VERIFIED_CURRENT_BEST_32K:
- RAW: C:\Users\User\Strata-Adrian\runs\direct-009-32k-20261010T095309933Z
- exit_code=0; binary SHA256 59292D5CCBCD200BD209AE04EE59E795DA979B6AFFD175C870E673F9FFAECEC3; prompt SHA256 F5A83C7B874F0B7A486A066C371118F215A347A5B10318C1A096C5522C6D6F76
- logged prefill 32767 tokens, output 1024 tokens, decode 28.60 tok/s, CPU expert pool 53.823 ms/token, file-tier read 25932.1 MB
- This is a direct current-best identity check at the 32k prompt, not an authorized 28912-token Task 012 measurement.

EXPLORATORY_28911_LOGGED_PREFILL:
- binary-compare-exploratory-20261010-009: RAW C:\Users\User\Strata-Adrian\runs\binary-compare-exploratory-20261010-009; output 1024; logged prefill 28911; decode 35.27 tok/s; CPU pool 28.513 ms/token; file-tier read 9682.5 MB; R4 hit 0.6214.
- binary-compare-exploratory-20261010-v5: RAW C:\Users\User\Strata-Adrian\runs\binary-compare-exploratory-20261010-v5; output 1024; logged prefill 28911; decode 36.30 tok/s; CPU pool 27.029 ms/token; file-tier read 9710.5 MB; R4 hit 0.6223. The associated campaign build artifact `C:\Users\User\Strata-Adrian\runs\iq3-stage-cache-promotion-009\rebuild-source-clean-cuda-v5\Release\strata.exe` hashes to 6403DD22B1E1A0F557FCE3B80F882D759AE05FCEFED10CA830C66364A91D6501.
- binary-compare-exploratory-20261010-v6: RAW C:\Users\User\Strata-Adrian\runs\binary-compare-exploratory-20261010-v6; output 1024; logged prefill 28911; decode 36.86 tok/s; CPU pool 29.803 ms/token; file-tier read 7780.3 MB; R4 hit 0.5951. The associated campaign build artifact `C:\Users\User\Strata-Adrian\runs\iq3-stage-cache-promotion-009\rebuild-source-clean-cuda-v6\Release\strata.exe` hashes to 501F34123E107D7E1D4ADC1258C29A87D0D633B97F5052CDEBA8449D5FAAA8EA.

FOLLOWUP_LIMITATION: The three exploratory run folders contain stdout.log/stderr.log but no command.json or persisted run-to-executable binding. The executable hashes above are verified at the labelled v5/v6 build paths, but are not asserted as fully provenance-complete bindings for every log. No candidate is promoted. The 32k current-best result and the 28911 logged-prefill exploratory results must not be pooled as one controlled Task 012 comparison.
FOLLOWUP_CONCLUSION: The later evidence records a large workload/runtime identity effect: the current-best binary at logged 32767 prefill produced 28.60 tok/s with materially higher CPU-pool/file-tier work, while the exploratory logged-28911 runs produced 35.27/36.30/36.86 tok/s. This is diagnostic evidence only; it does not validate the original Task 012 gate or prove a binary-only causal effect.
FOLLOWUP_CHANGES: No source, binary deployment, temperature, process stop, cleanup, or fallback was performed for this follow-up.
FOLLOWUP_COVERAGE: Targeted the four later raw run folders' metadata/stdout/stderr and the labelled v5/v6 executable SHA256 files. Large prompt/output lines and full build logs were not loaded wholesale. Full output-token equality, complete stderr semantics, and exact per-run executable binding remain unverified.

<!-- LUNA_FOLLOWUP_TASK_ID: LUNA-20261010-012 -->

[LUNA_REPORT]
TASK_ID: LUNA-20261010-013
STATUS: COMPLETED
TASK_SOURCE: branch
TASK_BRANCH: coordination/task-013-ram-adapt-guardfix-20261010-v2
TASK_COMMIT_SHA: 666fd19b8da91f9b1faa7ed9b3372bdebf9de6fc
PLAN_SHA: cc4169e15ea42e95d9653d32762502a0065c46e6
TIME_ASIA_TAIPEI: 2026-10-10

REMOTE_HOST: DESKTOP-LKMLUPC (BatchMode, strict host-key checking, hostname verified)
REMOTE_SOURCE: C:\Users\User\Strata-Adrian-control
REMOTE_BRANCH: main
REMOTE_HEAD: ba6e5b5d2fb55597f9dfbfdb58ed33e291dc571e
DEPLOYED_CURRENT_BEST_SHA256: 59292D5CCBCD200BD209AE04EE59E795DA979B6AFFD175C870E673F9FFAECEC3
CANDIDATE_BINARY_SHA256: C2890861FEF066A337B437E7DC8B3C1722C26D71885B6F215F84819F9AA7607A

DECISION: REJECT_CANDIDATE_KEEP_CURRENT_BEST
DECISION_REASON: The candidate did not meet the plan gate of paired median decode improvement >=3%; current-best remains deployed and untouched.

BUILD:
- Candidate was built in isolation at C:\Users\User\Strata-Adrian\runs\iq3-ram-adapt-013\build-candidate\Release\strata.exe.
- Release x64 build used MSVC 19.44.35226.0/toolset 14.44.35207, CUDA 13.2.78, and CUDA arch 89. No candidate deployment occurred.
- Candidate source implemented bounded decode-fed STRATA_RAM_ADAPT=8 residency replacement. Build completed and git diff --check passed.

BENCHMARK_IDENTITY:
- Prompt/tokens: C:\Users\User\Strata-v0.1.38-ab-20261003\work-note-transfer-chat-20261005\neuro.tokens; 28,912 tokens; SHA256 9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA; 1,024 generated tokens.
- Same IQ3 pack, native/PLE shards, MTP runtime, learned-heart profile, expert-cache 3604, pool-workers 9, spec 6, max-context 100000, kv q4_0, kv-resident 20480, resident-budget 20 GiB, MTP max T 3, adapt-every 3, adapt-swaps 16, adapt-decay 0.60, and unchanged environment for all valid runs.
- Candidate-only environment: STRATA_RAM_ADAPT=8. Temperature was not changed.

MEASURED_PAIRS_DECODE_TOK_S:
- pair-01: control 33.13; candidate 30.11; paired delta -9.12%
- pair-02: control 35.59; candidate 35.81; paired delta +0.62%
- pair-03: control 36.52; candidate 36.54; paired delta +0.05%
- Control median: 35.59 tok/s
- Candidate median: 35.81 tok/s
- Paired median delta: +0.62% (gate requires >=3%)

CANDIDATE_RUNTIME:
- RAM_ADAPT moved 787, 679, and 519 file-tier experts in the three candidate runs; all reported failed=0.
- Candidate decode file-tier reads were 10,812.8 MB, 8,455.5 MB, and 7,475.0 MB. The first pair nevertheless raised CPU pool time from 30.079 to 39.318 ms/round and reduced decode throughput.
- All six valid benchmark processes exited 0. No Strata process remained after the final run.

RESTORE:
- After rejection, the three candidate source files were restored from C:\Users\User\Strata-Adrian-control\runs\iq3-ram-adapt-013\source-backup.
- Post-restore candidate marker count was 0; git diff --check passed; the pre-existing Task 010 6/512 edits (kStageAge=6 and kStageSeq=512) remained. Current-best binary SHA remained unchanged.

BENCHMARK_RAW_PATH: C:\Users\User\Strata-Adrian\runs\iq3-ram-adapt-013

INVALID_WRAPPER_ATTEMPTS: Two pre-launch PowerShell wrapper syntax failures and one stderr-capture wrapper failure were not counted as benchmark runs; they left no active Strata process. The six listed runs used separated native stdout/stderr capture and have exit_code=0.

COVERAGE: Fresh GitHub connector snapshot and guard state; locked Task 013 plan; remote hostname/source branch/status; current-best and candidate SHA256; candidate build completion; source restore; six benchmark metadata/logs; targeted decode/speculation/expert-tier/prefill/RAM_ADAPT lines from all six logs. Large logs were not loaded wholesale. Full generated-token semantic equality, complete stderr audit, and a byte-for-byte rebuild provenance comparison were not performed. No deployment, temperature change, process stop, fallback, or unrelated source cleanup was performed.
<!-- LUNA_PUBLISHED_TASK_ID: LUNA-20261010-013 -->

[LUNA_REPORT]
TASK_ID: LUNA-20261010-014
STATUS: REJECT
TASK_SOURCE: branch
TASK_BRANCH: coordination/task-014-decode-lru-campaign-20261010
TASK_COMMIT_SHA: 7222246f4107f437b2b1e8e49c4acfcd532bb0bd
PLAN_SHA: 2b99a9757298e713736c9a7a6b55f24457503ad7

## Decision

Rejected the minimal fork-compatible decode-fed stage-LRU candidate. The three interleaved pairs had paired decode deltas of +2.1%, +8.5%, and -3.4%; paired median +2.1% is below the task's >=3% promotion gate. Current-best was preserved and not overwritten.

## Frozen identity

- Host: `DESKTOP-LKMLUPC`
- Active source: `C:\Users\User\Strata-Adrian-control`
- Active source HEAD: `ba6e5b5d2fb55597f9dfbfdb58ed33e291dc571e`
- Active source dirty files: `include/strata/core/expert_source.hpp`, `src/core/expert_source.cpp` (pre-existing canonical 6/512 edits; preserved)
- Control executable: `C:\Users\User\Strata-Adrian-control-build\strata.exe`
- Control/current-best SHA256: `59292D5CCBCD200BD209AE04EE59E795DA979B6AFFD175C870E673F9FFAECEC3`
- Candidate source worktree: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-014\source-upstream1324`
- Candidate source branch: `task014-upstream1324`
- Candidate build: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-014\build-minimal-lru\Release\strata.exe`
- Candidate SHA256: `B7AEC6832054C4B8BA65C4409415B8073F98D43E73A07D6FB13FFF339A750E60`
- Candidate change: fork-compatible minimal stage LRU; `STRATA_STAGE_KEEP_MIB=1024`; no active deployment change
- Prompt file: `C:\Users\User\Strata-v0.1.38-ab-20261003\work-note-transfer-chat-20261005\neuro.tokens`
- Prompt SHA256: `9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA`
- Prompt tokens: 28912
- Accepted output: 1024
- Model/pack/MTP/args: same frozen 013 identity; candidate-only environment was `STRATA_STAGE_KEEP_MIB=1024`

## Measured decode results

| Pair | Candidate tok/s | Control tok/s | Delta |
|---|---:|---:|---:|
| 01 | 35.04 | 34.31 | +2.1% |
| 02 | 37.82 | 34.85 | +8.5% |
| 03 | 36.62 | 37.90 | -3.4% |

Prefill was not used for the gate; it remained workload-identical at 28911 prompt tokens. All six runs exited normally with accepted output 1024. The candidate showed file-tier read variation and no correctness failure was observed in the captured logs, but no correctness claim beyond normal completion is made.

## Raw evidence

BENCHMARK_RAW_PATH: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-014\bench`

`C:\Users\User\Strata-Adrian\runs\iq3-campaign-014\bench`

Logs: `pair-01-candidate.*`, `pair-01-control.*`, `pair-02-candidate.*`, `pair-02-control.*`, `pair-03-candidate.*`, `pair-03-control.*`.

The full upstream #1324 patch did not apply cleanly to this fork; the measured candidate was the isolated minimal fork-compatible patch, not a claim that the upstream patch was reproduced verbatim.

## Next step

Keep current-best SHA `59292D5C...` deployed. Do not promote this candidate. Return to the controller for the next highest-value untested source route; do not repeat this rejected route without a materially different hypothesis.
<!-- LUNA_PUBLISHED_TASK_ID: LUNA-20261010-014 -->

[LUNA_REPORT]

TASK_ID: LUNA-20261010-015
STATUS: COMPLETED
TASK_SOURCE: branch
TASK_BRANCH: coordination/task-015-source-campaign-20261010
TASK_COMMIT_SHA: e146b54592fa3c2ac8f8c57121d9f6cee01298ef
TASK_SOURCE_SHA: e146b54592fa3c2ac8f8c57121d9f6cee01298ef
PLAN_PATH: coordination/TASK_015_CAMPAIGN.md
PLAN_SHA: 29fb310c843512692280204b43840fcfd5e8cb92
BENCHMARK_RAW_PATH: C:\Users\User\Strata-Adrian\runs\iq3-cpu-campaign-015
HOST: DESKTOP-LKMLUPC (User@100.126.147.41)

DECISION

- Current-best unchanged; no candidate promoted.
- Candidate A (PR1087 pool tasks, isolated worktree) REJECTED: paired decode deltas +8.14%, +2.82%, -13.37%; median +2.82%, below the >=3% gate.
- Candidate B (fork-aware PR863 Intel P-core gather/AVX-VNNI port, isolated worktree) REJECTED: paired decode deltas -2.90%, +3.20%, +0.05%; median +0.05%, below the >=3% gate. No confirmation pairs were authorized by the plan after the gate failed.
- Candidate C (per-expert Down pipeline) SKIPPED: A and B logs showed no barrier-idle trigger; every valid run had pool wait-park 0.000 and re-park 0.000 ms/token.

LOCKED BASELINE AND IDENTITY

- Current-best executable: C:\Users\User\Strata-Adrian-control-build\strata.exe
- Current-best SHA256: 59292D5CCBCD200BD209AE04EE59E795DA979B6AFFD175C870E673F9FFAECEC3
- Final B candidate executable: C:\Users\User\Strata-Adrian\runs\iq3-pool-tasks-015\build-pr863\Release\strata.exe
- Final B candidate SHA256: 6242341445934157CE6E343FB7974CF90F1363C7411C7CE78A8BF0BF798BE44B
- Candidate B was rebuilt after applying the two active Task009 current-best source diffs (include/strata/core/expert_source.hpp and src/core/expert_source.cpp) to the isolated PR863 worktree. A-only src/program/generate.cpp and pool changes were not included in B.
- Final B build: CUDA enabled, CUDA 13.2.78, MSVC toolset 14.44.35207/14.44.35226, x64, CUDA arch 89, Release, tests off; build exit 0.
- Final B worktree base HEAD: ba6e5b5d2fb55597f9dfbfdb58ed33e291dc571e; isolated worktree C:\Users\User\Strata-Adrian\runs\iq3-pool-tasks-015\source-pr863.

FROZEN RUN IDENTITY

- Prompt: C:\Users\User\Strata-v0.1.38-ab-20261003\work-note-transfer-chat-20261005\neuro.tokens
- Prompt SHA256: 9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA
- Prompt tokens: 28912; output: 1024 accepted tokens
- Pack: C:\Users\User\Strata-IQ3-20261008\packs\iq3_xxs
- Native/Ple shards: C:\Users\User\Strata-IQ3-20261008\models\IQ3_XXS\Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf and ...-00002-of-00002.gguf
- MTP: C:\Users\User\Strata-v0.1.34-mtp-test-20261002\mtp\rt
- Learned profile: C:\Users\User\Strata-v0.1.38-ab-20261003\work-note-transfer-chat-20261005\learned-heart.bin
- Args: --spec 6 --spec-min-p 0.75 --max-context 100000 --kv q4_0 --kv-resident 20480 --expert-cache 3604 --pool-workers 9 --prefill auto --stats --max-new 1024 --suffix-draft 3 --resident-budget-gib 20 --mtp-max-t 3 --pool-affinity all --adapt-every 3 --adapt-swaps 16 --adapt-decay 0.60
- Environment: STRATA_FETCH_ADMIT=0, STRATA_RESIDENT_HEADROOM_GIB=3, STRATA_ADAPT_IF_MISS=1, STRATA_EXPERT_FILE_CACHE=1, STRATA_PF_FUSED=1, STRATA_LOOKAHEAD=0. B did not set STRATA_IQ256_GATHER; PR863 auto-selected the CPU-supported path.

MEASURED RESULTS

Candidate A, raw C:\Users\User\Strata-Adrian\runs\iq3-cpu-campaign-015\phase-a-pool192-v2:

| pair | candidate tok/s | control tok/s | delta | candidate pool ms/token | control pool ms/token | candidate file MB | control file MB |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 36.27 | 33.54 | +8.14% | 28.315 | 30.953 | 9208.5 | 12440.1 |
| 2 | 35.78 | 34.80 | +2.82% | 30.471 | 29.160 | 11759.4 | 12642.5 |
| 3 | 29.35 | 33.88 | -13.37% | 34.953 | 33.027 | 21319.5 | 11497.2 |

Candidate B, raw C:\Users\User\Strata-Adrian\runs\iq3-cpu-campaign-015\phase-b-pr863-v2:

| pair | candidate tok/s | control tok/s | delta | candidate pool ms/token | control pool ms/token | candidate file MB | control file MB |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 36.23 | 37.31 | -2.90% | 27.862 | 24.344 | 8872.0 | 6619.4 |
| 2 | 38.44 | 37.25 | +3.20% | 24.402 | 28.358 | 6698.8 | 7534.4 |
| 3 | 38.95 | 38.93 | +0.05% | 24.072 | 23.506 | 5942.1 | 6836.3 |

CORRECTNESS AND PROCESS EVIDENCE

- Final B parity executable: C:\Users\User\Strata-Adrian\runs\iq3-pool-tasks-015\build-pr863\Release\iq_avx2_parity.exe; run result `iq_avx2_parity: 0 failures`.
- On the host, the parity test reported AVX2=1, AVX512=0, and variants `gather+vnni`; all IQ2/IQ3/IQ4/Q2 variant checks were 0 rows differing across 1..8 tokens. Maximum reported relative error was 1.61e-7.
- All twelve valid A/B campaign runs exited 0, accepted 1024 tokens, and left zero Strata/Llama processes. Current-best was re-hashed after the campaign and remained the exact locked SHA above.
- The first B attempt in raw `phase-b-pr863-v1` is preserved as invalid evidence: the wrapper incorrectly passed A-only `--pool-tasks 192` to B, and the candidate correctly returned `unknown argument`. It is excluded from all statistics. The wrapper was then corrected and B was rebuilt from the proper baseline before `phase-b-pr863-v2`.

COVERAGE AND REMAINING RISK

- Required campaign coverage: A and B each received 3 interleaved candidate/control pairs under the frozen 28912-token prompt, 1024 output, IQ3_XXS, MTP and environment; 12 valid model runs total, plus the B parity check.
- Not run: 2 confirmation pairs for either candidate (both failed the first three-pair median gate), C route (no barrier-idle trigger), 4096 prompt, knob sweeps, and promotion/deployment.
- Raw logs include command identity, binary hashes, stdout/stderr, GPU before/after, process before/after, result JSON, summary JSON, and build logs under C:\Users\User\Strata-Adrian\runs\iq3-cpu-campaign-015. The invalid v1 stage and PR port repair artifacts are retained.
- Remaining risk: parity proves the isolated CPU kernel variants against their references, but the campaign gate did not prove a >=3% end-to-end improvement; current-best therefore remains the only promoted control.

<!-- LUNA_PUBLISHED_TASK_ID: LUNA-20261010-015 -->

[LUNA_REPORT]
TASK_ID: LUNA-20261010-016
STATUS: COMPLETED
TASK_SOURCE: branch
TASK_BRANCH: coordination/task-016-source-campaign-20261010
TASK_COMMIT_SHA: e55ac628f6f3601119c95cf780420fa093cc6db5
PLAN_PATH: coordination/TASK_016_CAMPAIGN.md
PLAN_SHA: e0361d36330d071e58451583dda9e1031772ff63
TIME_ASIA_TAIPEI: 2026-10-11

DECISION: REJECT_ALL_CANDIDATES_KEEP_CURRENT_BEST
RESULT: Three isolated source routes were tested under the Task 016 limit. None met the paired-median >=3% promotion gate. No candidate was deployed or promoted; canonical source and current-best binary remain unchanged.

REMOTE:
- HOST: DESKTOP-LKMLUPC (strict host-key checking, BatchMode, hostname verified)
- SOURCE: C:\Users\User\Strata-Adrian-control
- BRANCH / HEAD: main / ba6e5b5d2fb55597f9dfbfdb58ed33e291dc571e
- PRE-EXISTING DIRTY FILES: include/strata/core/expert_source.hpp, src/core/expert_source.cpp (canonical 6/512 edits), four untracked .codex/handoffs files, and runs/; preserved
- RAW_ROOT: C:\Users\User\Strata-Adrian\runs\iq3-cpu-campaign-016
BENCHMARK_RAW_PATH: C:\Users\User\Strata-Adrian\runs\iq3-cpu-campaign-016

LOCKED CURRENT-BEST:
- BINARY: C:\Users\User\Strata-Adrian-control-build\strata.exe
- SHA256: 59292D5CCBCD200BD209AE04EE59E795DA979B6AFFD175C870E673F9FFAECEC3
- SOURCE CONTROL: kStageAge=6 and kStageSeq=512
- BUILD IDENTITY: Release x64, MSVC 19.44.35226 / toolset 14.44.35207, CUDA 13.2.78, CUDA arch 89, STRATA_ENABLE_CUDA=ON, GGML_CUDA=OFF

FROZEN BENCHMARK IDENTITY:
- PROMPT: C:\Users\User\Strata-v0.1.38-ab-20261003\work-note-transfer-chat-20261005\neuro.tokens
- PROMPT SHA256: 9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA
- PROMPT TOKENS: 28912
- ACCEPTED OUTPUT: 1024
- Same IQ3 pack/native/PLE/MTP/profile, args and environment as the Task 015 control. No temperature change.

CANDIDATE A — UNGUARDED BEGIN-LAYER PREFETCH:
- BUILD: C:\Users\User\Strata-Adrian\runs\iq3-cpu-campaign-016\candidate-build-cuda3\strata.exe
- SHA256: BCACF778570AF220D73FD9089A897F148E1DC107D8EEB2472EC5D6DB3BFCB88C
- CHANGE: single-token FileExpertSource::begin_layer deduplication plus prefetch on every call.
- RAW: C:\Users\User\Strata-Adrian\runs\iq3-cpu-campaign-016\phase-a-begin-layer-prefetch
- PAIRED DECODE TOK/S (candidate / control): 5.47 / 35.35, 5.81 / 37.16, 5.17 / 31.63
- PAIRED DELTAS: -84.526%, -84.365%, -83.655%; MEDIAN: -84.365%
- BOTTLENECK: candidate pool 272.48, 267.328, 281.182 ms/token versus control 30.429, 28.044, 33.174; candidate file-tier reads were 368369.9, 347748.8, 355695.7 MB versus control 8978.4, 8286.8, 13377.4 MB.
- DECISION: REJECT. The unguarded per-call prefetch caused repeated massive file reads.

CANDIDATE B — FIRST-CALL-PER-LAYER CORRECTION:
- BUILD: C:\Users\User\Strata-Adrian\runs\iq3-cpu-campaign-016\candidate-build-cuda-b\strata.exe
- SHA256: D90BE4C0187CC40B3FC3A889BAD8616C7CE81AAE85EEE8D747638A44CDE6FDC7
- CHANGE: same route corrected to prefetch only on the first call after a layer change.
- RAW: C:\Users\User\Strata-Adrian\runs\iq3-cpu-campaign-016\phase-b-begin-layer-prefetch-corrected
- PAIRED DECODE TOK/S (candidate / control): 36.29 / 37.38, 35.48 / 33.17, 33.82 / 34.12
- PAIRED DELTAS: -2.916%, +6.964%, -0.879%; MEDIAN: -0.879%
- DECISION: REJECT. The corrected route did not produce a reliable improvement.

CANDIDATE C — WINDOWS HOST CORE LAST:
- BUILD: C:\Users\User\Strata-Adrian\runs\iq3-cpu-campaign-016\candidate-build-cuda-c\strata.exe
- SHA256: 17D99F3399AD51CCBDF70C47C0B36744A87D50C082E555646FCFF653AEA61361
- CHANGE: isolated upstream F12 host-core route; g_host_core default changed from HostCore::First to HostCore::Last, with canonical 6/512 source edits preserved.
- RAW: C:\Users\User\Strata-Adrian\runs\iq3-cpu-campaign-016\phase-c-host-core-last
- PAIRED DECODE TOK/S (candidate / control): 37.80 / 37.95, 36.18 / 36.51, 34.37 / 35.10
- PAIRED DELTAS: -0.395%, -0.904%, -2.080%; MEDIAN: -0.904%
- DECISION: REJECT. The route was stable but below the promotion gate.

VALIDITY AND RESTORE:
- 18 model processes total: 3 candidates x 3 interleaved candidate/control pairs, all exit_code=0 and accepted_output=1024.
- All candidate/control runs have preserved command, process-before/after, GPU-before/after, stdout, stderr and result evidence under the raw root. No residual Strata/Llama process remained after the campaign.
- Canonical source and deployed current-best binary were never overwritten. No rollback was needed, no process was stopped, and no cleanup or fallback was used.
- The initial CPU-only configure and the overlapping-build permission failure were build diagnostics only; neither was benchmarked or included in these results.

COVERAGE / REMAINING RISK:
- Coverage: all three allowed candidates, three interleaved pairs each, 18/18 benchmark processes valid; candidate source diffs, build completion and CUDA cache identity were checked; canonical git diff --check and final remote status were checked.
- Large logs/build logs were retained and inspected through structured summaries/targeted metrics rather than loaded wholesale. Full semantic audit of every stderr/stdout line and generated-token equality beyond the accepted 1024 count was not performed.
- No candidate passed the gate, so no confirmation pairs were authorized. The Task 016 candidate budget is exhausted; the next source route requires a new task/plan and must not repeat these rejected hypotheses without materially new evidence.

NEXT BASELINE / NEXT ROUTE:
- Keep current-best SHA256 59292D5CCBCD200BD209AE04EE59E795DA979B6AFFD175C870E673F9FFAECEC3 and canonical 6/512 source unchanged.
- No route is selected from Task 016. Await a new unique task plan for any further optimization.
<!-- LUNA_PUBLISHED_TASK_ID: LUNA-20261010-016 -->

[LUNA_REPORT]
TASK_ID: LUNA-20261010-017
STATUS: COMPLETED
TASK_SOURCE: branch
TASK_BRANCH: coordination/task-017-source-campaign-20261011
TASK_COMMIT_SHA: c44a194f6166a570d16782406ef7fc50e326b22c
PLAN_SHA: c5bb3e6aa34add6c6ad5db899f15f303c281916a
DECISION: REJECT candidate; paired median did not meet the +3% promotion gate. Current 6/512 baseline remains unchanged.

REMOTE_HOST: DESKTOP-LKMLUPC (strict host-key SSH identity verified)
REMOTE_CANONICAL_SOURCE: C:\Users\User\Strata-Adrian-control
REMOTE_CANONICAL_BRANCH: main
REMOTE_CANONICAL_HEAD: ba6e5b5d2fb55597f9dfbfdb58ed33e291dc571e
REMOTE_CANONICAL_DIRTY_FILES: pre-existing include/strata/core/expert_source.hpp and src/core/expert_source.cpp edits (6/512), four untracked .codex/handoffs files, and runs/; preserved unchanged.
REMOTE_ISOLATED_WORKTREE: C:\Users\User\Strata-Adrian\runs\iq3-campaign-017\source-hot-second-chance
REMOTE_ISOLATED_BASE: ba6e5b5d2fb55597f9dfbfdb58ed33e291dc571e

HYPOTHESIS: Add a bounded second-chance hotness counter to stage-buffer victim selection so repeatedly reused staged blobs are protected from the first eviction pass while retaining the existing oldest-eligible fallback.
SOURCE_CHANGE: Isolated worktree only. Added bounded stage_hot_ state; stage hits saturate at 3, the first victim pass selects only zero-hot eligible buffers, and the fallback still selects the oldest eligible buffer when all candidates are protected. Canonical kStageAge=6 and kStageSeq=512 were preserved. No deployment or canonical source modification was made.

BUILD: Isolated Release CUDA build succeeded with the recovered existing environment: Visual Studio developer environment 17.14.31, MSVC 14.44.35207, CUDA 13.2.78, CUDA architecture 89, NMake generator, native experts enabled, and the Task-009/011 build configuration. Candidate executable: C:\Users\User\Strata-Adrian\runs\iq3-campaign-017\build-hot-second-chance\strata.exe
CURRENT_BEST_SHA256: 59292D5CCBCD200BD209AE04EE59E795DA979B6AFFD175C870E673F9FFAECEC3
CANDIDATE_SHA256: C4705E1E402EC6994D638E9FF8F53A3C8A47AAEAD4FBB4E2B79343711F4A7300

BENCHMARK_IDENTITY: Same frozen IQ3 identity for all runs: prompt SHA256 9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA (28912 prompt tokens), 1024 output tokens, max-context 100000, same model shards, MTP runtime, expert profile, command arguments, environment and temperature. The control binary was the current-best SHA256 above; the candidate was run only in the isolated authorized comparison.
BENCHMARK_RUNS: 3 interleaved matched pairs, 6 total processes. All 6 exited 0, accepted 1024 tokens, reported decode and pool metrics, and left residual_process_count=0.

| Pair | Control decode tok/s | Candidate decode tok/s | Paired delta |
|---:|---:|---:|---:|
| 1 | 38.89 | 35.10 | -9.75% |
| 2 | 30.66 | 37.56 | +22.51% |
| 3 | 36.90 | 36.48 | -1.14% |

PAIRED_MEDIAN: Candidate 36.48 tok/s vs control 36.90 tok/s; paired median delta -1.14%, below the required +3% gate. Candidate/control means were 36.38/35.48 tok/s, but the gate is paired-median based and the run-to-run variance is too large to support promotion. Candidate CPU expert-pool metrics were 29.003/29.102/27.587 ms per token; control was 28.145/38.169/28.309 ms per token. File-tier reads were variable as well, so no stable causal improvement was demonstrated.
CORRECTNESS_STABILITY: The runner marked all 6 runs VALID; no process remained after any run. This establishes clean execution and the required accepted length, not output-semantic equivalence. No memory, crash, CUDA or temperature change was observed in the controlled run.

BENCHMARK_RAW_PATH: C:\Users\User\Strata-Adrian\runs\iq3-campaign-017\bench-second-chance
BENCHMARK_RUNNER: C:\Users\User\Strata-Adrian\runs\iq3-campaign-017\task017_bench.ps1
EVIDENCE: summary.json and each pair directory's command.json, result.json, stdout.log, stderr.log, GPU snapshots, and process-before/after.json under the raw path above. The build artifact and isolated source diff remain under the Task-017 run root.

NEXT_STEP: Keep the 6/512 current-best source and binary as the control. Do not promote or deploy the rejected second-chance candidate. A future task may select one substantially different untested route within the campaign budget; this task's authorized candidate is complete and requires no rerun.
COVERAGE: Completed the plan's first candidate gate: exact branch/plan identity, remote host/source/process preflight, isolated source diff, recovered toolchain build, candidate SHA, and all 3 interleaved matched pairs. Large compiler output was not copied into the report; raw build/run evidence remains on the remote host. No full repository audit, output semantic comparison, or promotion/deployment was performed.
<!-- LUNA_PUBLISHED_TASK_ID: LUNA-20261010-017 -->

[LUNA_REPORT]

TASK_ID: LUNA-20261010-018
STATUS: COMPLETED
TASK_SOURCE: branch
TASK_BRANCH: coordination/task-018-source-campaign-20261011
TASK_COMMIT_SHA: a1e136d65f82fbab52989ca5bc29c805aeb12b0f
PLAN_PATH: coordination/TASK_018_CAMPAIGN.md
PLAN_SHA: bfceffef3f544ec6d1965d65b3ea2c978bc27a13

DECISION: PROMOTE

HYPOTHESIS / CANDIDATE
- Replaced the bounded key->slot std::unordered_map lookup in FileExpertSource::claim_stage with direct indexing into a layer*expert-sized stage_slot_ vector under the existing stage mutex.
- Preserved the current canonical 6/512 source changes (kStageAge=6 and kStageSeq=512); no other source route was changed.
- Candidate worktree: C:\Users\User\Strata-Adrian\runs\iq3-campaign-018\source-direct-slot-index
- Candidate build: C:\Users\User\Strata-Adrian\runs\iq3-campaign-018\build-direct-slot-index\strata.exe
- Candidate SHA256: 662C7E6103B29538EAF530FB2657BE0C384730F76D9805987695327C11967D71
- Previous current-best control SHA256: 59292D5CCBCD200BD209AE04EE59E795DA979B6AFFD175C870E673F9FFAECEC3

FROZEN IDENTITY
- Host: DESKTOP-LKMLUPC (User@100.126.147.41)
- Canonical source: C:\Users\User\Strata-Adrian-control
- Canonical source commit after promotion: e26d5538b450ebf57942697f96242927dacfab77
- Canonical source retains unrelated untracked .codex/handoffs/* and runs/; only expert_source.hpp/.cpp were staged and committed.
- Prompt: C:\Users\User\Strata-v0.1.38-ab-20261003\work-note-transfer-chat-20261005\neuro.tokens
- Prompt SHA256: 9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA
- Prompt tokens: 28912; accepted output: 1024
- Pack: C:\Users\User\Strata-IQ3-20261008\packs\iq3_xxs
- Native shard: C:\Users\User\Strata-IQ3-20261008\models\IQ3_XXS\Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf
- PLE shard: C:\Users\User\Strata-IQ3-20261008\models\IQ3_XXS\Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf
- MTP: C:\Users\User\Strata-v0.1.34-mtp-test-20261002\mtp\rt
- Expert profile: C:\Users\User\Strata-v0.1.38-ab-20261003\work-note-transfer-chat-20261005\learned-heart.bin
- Runtime args: --spec 6 --spec-min-p 0.75 --max-context 100000 --kv q4_0 --kv-resident 20480 --expert-cache 3604 --pool-workers 9 --prefill auto --stats --max-new 1024 --suffix-draft 3 --resident-budget-gib 20 --mtp-max-t 3 --pool-affinity all --adapt-every 3 --adapt-swaps 16 --adapt-decay 0.60
- Environment: STRATA_FETCH_ADMIT=0, STRATA_RESIDENT_HEADROOM_GIB=3, STRATA_ADAPT_IF_MISS=1, STRATA_EXPERT_FILE_CACHE=1, STRATA_PF_FUSED=1, STRATA_LOOKAHEAD=0

BENCHMARK
- Runner: C:\Users\User\Strata-Adrian\runs\iq3-campaign-018\task018_bench.ps1
BENCHMARK_RAW_PATH: C:\Users\User\Strata-Adrian\runs\iq3-campaign-018\bench-direct-slot-index
- Three interleaved candidate/control pairs; all six runs VALID, exit code 0, accepted_tokens=1024, residual_process_count=0.
- Candidate decode tok/s: 37.92, 36.71, 37.83; median 37.83.
- Control decode tok/s: 33.79, 36.03, 33.81; median 33.81.
- Paired decode deltas: +12.22%, +1.89%, +11.89%; paired median +11.89%, above the declared +3% gate.
- CPU expert-pool medians: candidate 26.265 ms/token vs control 29.271 ms/token.
- File-read medians: candidate 7103.5 MB vs control 12757.9 MB; this is a bottleneck-specific observation, not a separate acceptance criterion.
- Summary: C:\Users\User\Strata-Adrian\runs\iq3-campaign-018\bench-direct-slot-index\summary.json

PROMOTION
- The tested candidate source was copied into the canonical source and committed as e26d5538b450ebf57942697f96242927dacfab77.
- The versioned candidate executable remains the promoted baseline at C:\Users\User\Strata-Adrian\runs\iq3-campaign-018\build-direct-slot-index\strata.exe; the prior control executable was not overwritten.
- Remote post-run process check found no strata, llama-server, or llama-cli process.
- Normal remote git push was attempted once and failed at the credential layer: wincredman could not persist credentials and Git could not read the HTTPS username. No fallback, force-push, merge, or credential workaround was used.

NEXT ROUTE
- No additional route was selected in this task. Use the promoted binary SHA above as the next current-best control identity and wait for the next unique task plan.
<!-- LUNA_PUBLISHED_TASK_ID: LUNA-20261010-018 -->

[LUNA_REPORT]
TASK_ID: LUNA-20261011-019
STATUS: COMPLETED
TASK_SOURCE: branch
TASK_BRANCH: coordination/task-019-ssd-cost-placement-20261011
TASK_COMMIT_SHA: 342a3a4a9cbfc7157dc941e6f58d4494f0c62518
PLAN_PATH: coordination/TASK_019_CAMPAIGN.md
PLAN_SHA: 44fd94dd6ecd5bdd4c7d9e1ffa1941340ee8b98e
TIME_ASIA_TAIPEI: 2026-10-11

DECISION: REJECT_CANDIDATE_KEEP_CURRENT_BEST

SUMMARY

- The independent-trace SSD-placement simulation passed its pre-edit gate: predicted SSD bytes fell from 39,680,000 to 0 (100.0% reduction) on the 48-record, 480-route-entry trace.
- The real first-stage end-to-end gate failed: three interleaved matched pairs had paired-median decode delta +0.16%, below the required +3%. No confirmation pairs were authorized, no source edit was made, and no candidate was promoted.
- Current-best remains the Task-018 binary SHA256 662C7E6103B29538EAF530FB2657BE0C384730F76D9805987695327C11967D71 with the existing learned-heart profile.

REMOTE IDENTITY

- HOST: remote Windows execution host; strict host-key SSH and hostname verified
- CANONICAL_SOURCE: remote canonical Strata source root (verified)
- CANONICAL_BRANCH / HEAD: main / e26d5538b450ebf57942697f96242927dacfab77
- CANONICAL_STATUS: pre-existing untracked .codex/handoffs/* and runs/; preserved unchanged. No canonical source edit, reset, cleanup, or process stop.
- ISOLATED_WORKTREE: task-scoped isolated worktree (verified clean)
- ISOLATED_BASE / STATUS: e26d5538b450ebf57942697f96242927dacfab77 / clean

BINARY / PROFILE IDENTITY

- BINARY_USED_FOR_BOTH_ARMS: Task-018 promoted binary
- BINARY_SHA256: 662C7E6103B29538EAF530FB2657BE0C384730F76D9805987695327C11967D71
- CONTROL_PROFILE: Task-018 learned-heart profile
- CONTROL_PROFILE_SHA256: AA28BA0800A598DE0D83EBD83E918E2736BB2F4AB6750DB8AA72461E5829510F
- CANDIDATE_PROFILE: Task-019 cost-ranked profile
- CANDIDATE_PROFILE_SHA256: 5063B5F17B35F37E127D8A0C6E78B25ABA72D04194BF424CD5E34D9444E97D56
- Candidate profile preserved the first 3148 profile pairs (the verified GPU prefix) and reordered only the complement by descending trace_frequency(layer, expert) * native_experts blob_bytes[layer], with profile-order tie breaking.

PLAN / SOURCE DRIFT

- The branch plan names `generate.cpp::rank_all`, but no `rank_all` symbol exists in the locked source. The verified implementation loads a `profile` vector in `src/program/generate.cpp` and passes it to `FileExpertSource::pin_cache_complement`.
- To test the hypothesis without inventing a new runtime path, the equivalent host-complement rank was supplied through the existing `--expert-profile` input. This was a profile-only candidate; no source edit or rebuild was performed.

INDEPENDENT TRACE SIMULATION

- TRACE: task-scoped routing trace (remote raw evidence)
- TRACE_SHA256: 6647C1A60FEB4C49C642470469AA332A329626230295D588EAC04E30BD5AD4D4
- SIMULATION: task-scoped simulation artifact (remote raw evidence)
- NATIVE_COSTS: task-scoped native expert costs; SHA256 AE28CF7A2A1C9063C4B55D6C8CF86D4D079DCDDCF597F9E8697C9157D462C0EE
- Profile pairs: 24,576; layers/experts: 48/512; GPU slots: 3,148.
- Requested resident cap: 20 GiB; replay-observed effective cap: 19.74 GiB.
- Existing profile rank: 12,290 host pairs; predicted SSD bytes 39,680,000.
- SSD-cost rank: 12,288 host pairs; predicted SSD bytes 0; predicted reduction 100.0%, passing the required 15% pre-edit gate.
- This trace is a separate non-benchmark `--dump-routing` replay with `--max-new 1`; its predicted result was therefore treated only as the plan's pre-edit admission test, not as a performance result.

FROZEN BENCHMARK IDENTITY

- Prompt: task-scoped frozen prompt artifact (remote raw evidence)
- Prompt SHA256: 9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA
- Prompt tokens: 28,912; accepted output: 1,024
- IQ3_XXS pack, native/PLE shards, MTP runtime, max-context 100000, spec 6, kv q4_0, kv-resident 20480, expert-cache 3604, pool-workers 9, resident-budget-gib 20, MTP max 3 and adaptive settings were held constant.
- Environment: STRATA_FETCH_ADMIT=0, STRATA_RESIDENT_HEADROOM_GIB=3, STRATA_ADAPT_IF_MISS=1, STRATA_EXPERT_FILE_CACHE=1, STRATA_PF_FUSED=1, STRATA_LOOKAHEAD=0.
- No temperature change.

MEASURED FIRST-STAGE RESULTS

| Pair | Candidate tok/s | Control tok/s | Paired delta | Candidate pool ms/token | Control pool ms/token | Candidate file MB | Control file MB |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 36.62 | 38.07 | -3.81% | 25.625 | 28.030 | 6537.9 | 8299.3 |
| 2 | 38.07 | 38.01 | +0.16% | 24.956 | 27.138 | 6120.4 | 6750.9 |
| 3 | 37.36 | 36.19 | +3.23% | 28.588 | 26.925 | 6607.9 | 7785.4 |

- Candidate decode median: 37.36 tok/s; control median: 38.01 tok/s.
- Paired deltas: -3.81%, +0.16%, +3.23%; paired median: +0.16%.
- All 6 runs were VALID, exit_code=0, accepted_tokens=1024, and residual_process_count=0.
BENCHMARK_RAW_PATH: task-scoped remote benchmark evidence directory
- RUNNER: task-scoped benchmark runner
- RUNNER_SHA256: 2169BAA0EEBA23D4B827061E103A71A0B2614122E39F84815712DD1C1D1A116B

VALIDITY / COVERAGE

- Fresh @GitHub connector discovery covered main inbox/outbox, 12 coordination/task-* branch heads, their branch trees and parser-relevant inbox/plan files; the locked plan and branch commit were claimed and resumed through the local guard.
- Remote coverage included strict host identity, canonical source HEAD/status, isolated worktree status, current-best binary/profile hashes, candidate profile hash, prompt hash, cost-file hash, trace hash, process-before/after evidence and all six structured run result files. Absolute host and filesystem identifiers are intentionally omitted from this public report; the original evidence remains on the execution host.
- Large stdout/stderr/build artifacts remain on the remote host and were inspected through targeted structured metrics; no full semantic audit of every log line and no output-token equality comparison was performed.
- The simulation used one short independent routing trace. Its 100% predicted reduction did not survive the first three-pair performance gate; no confirmation pairs were run.

NEXT STEP

Keep the 018 current-best binary/profile as control. Do not promote or deploy the cost-ranked profile. The task is complete at the first-stage reject gate; any future source route requires a new unique plan with a materially different hypothesis.
<!-- LUNA_PUBLISHED_TASK_ID: LUNA-20261011-019 -->

[LUNA_REPORT]
TASK_ID: LUNA-20261011-020
STATUS: COMPLETED
TASK_SOURCE: branch
TASK_BRANCH: coordination/task-020-upstream-v0142-20261011
TASK_COMMIT_SHA: befb373ea474247aee34b1bf7aa7f400165fe4d8
PLAN_PATH: coordination/TASK_020_CAMPAIGN.md
PLAN_SHA: 3cb03049f48e6d8238d66f03284d68e22c76fe8d
TIME_ASIA_TAIPEI: 2026-10-11

DECISION: REJECT_PORT_CANDIDATE_KEEP_CURRENT_BEST

SUMMARY

- The official v0.1.42 tail-skip and PcieAuto behavior was ported into an isolated worktree based on the promoted 018 source. Canonical source and the promoted binary were not modified.
- The first isolated build failed only because the inserted PcieAuto object was in the prompt-path scope while the decode loop was in a separate scope. The compiler diagnostics were extracted from the preserved build log; two minimal scope fixes were applied only in the isolated worktree.
- The corrected Release CUDA build succeeded. No benchmark was started until the candidate SHA and current-best control SHA were rechecked.
- Three interleaved port/control pairs were run. All six were valid, but the paired median was -5.53%, below the +3% gate. No confirmation pairs, promotion, canonical sync, or process stop were performed.

REMOTE / SOURCE IDENTITY

- HOST: DESKTOP-LKMLUPC (verified by strict BatchMode SSH hostname check)
- CANONICAL_SOURCE: C:\Users\User\Strata-Adrian-control
- CANONICAL_HEAD: e26d5538b450ebf57942697f96242927dacfab77
- ISOLATED_WORKTREE: C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\port-018
- ISOLATED_BASE: e26d5538b450ebf57942697f96242927dacfab77
- UPSTREAM_FEATURE_SOURCE: 61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406
- ISOLATED_DIFF: include/strata/core/expert_source.hpp, src/core/expert_source.cpp, src/program/generate.cpp only; git diff --check passed.
- The isolated source was not committed or copied into canonical after the failed performance gate.

BUILD

- BUILD_DIR: C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\build-port-018
- BUILD_CONFIG: Release, NMake Makefiles, CUDA enabled, CUDA architecture 89
- TOOLCHAIN: Visual Studio 17.14.31 / MSVC 14.44.35207 / CUDA 13.2.78
- CANDIDATE_BINARY: C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\build-port-018\strata.exe
- CANDIDATE_SHA256: A69AD06808589F4200E10E6213C59CDD9DBCCB05958050529487B4A25ADC8EC9
- CURRENT_BEST_BINARY: C:\Users\User\Strata-Adrian\runs\iq3-campaign-018\build-direct-slot-index\strata.exe
- CURRENT_BEST_SHA256: 662C7E6103B29538EAF530FB2657BE0C384730F76D9805987695327C11967D71

FROZEN BENCHMARK IDENTITY

- Prompt: C:\Users\User\Strata-v0.1.38-ab-20261003\work-note-transfer-chat-20261005\neuro.tokens
- Prompt SHA256: 9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA
- Prompt tokens: 28,912; accepted output: 1,024
- IQ3_XXS pack, native/PLE shards, MTP runtime, max-context 100000, spec 6, KV q4_0, KV resident 20480, expert-cache 3604, pool-workers 9, resident-budget-gib 20, adaptive settings, profile and environment were held constant.
- No temperature change.

PORT BENCHMARK

- Runner: C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\TASK_020_port_bench.ps1
BENCHMARK_RAW_PATH: C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\stage-e-port-018
- Six processes total, three interleaved pairs; every run exit_code=0, accepted_tokens=1024, status VALID, residual_process_count=0.

| Pair | Port decode tok/s | Current-best decode tok/s | Paired delta | Port pool ms/token | Control pool ms/token | Port file MB | Control file MB |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 34.05 | 38.20 | -10.86% | 29.114 | 26.924 | 11914.4 | 6592.9 |
| 2 | 35.90 | 38.00 | -5.53% | 26.936 | 26.747 | 8044.7 | 6699.5 |
| 3 | 37.15 | 35.82 | +3.71% | 26.920 | 28.273 | 6417.3 | 8276.2 |

- Port median: 35.90 tok/s; current-best median: 38.00 tok/s.
- Paired median: -5.53%. This fails the required >=3% first-stage gate; confirmation pairs were not authorized.
- Port pool median: 26.936 ms/token; control pool median: 26.924 ms/token.
- Port file-read median: 8044.7 MB; control file-read median: 6699.5 MB.
- Port quality evidence: all six runs had the same accepted length and clean exit. The port emitted PCIe probe default 0.55 and PcieAuto share updates to 0.35 in all three candidate logs. The expected tail-skip startup line was not present in the captured stdout/stderr files, so tail-skip activation is an evidence gap and is not claimed as verified here.
- Output semantic equality was not established; accepted length is the validity criterion used by this bounded gate.

RUN ACCOUNTING / STATE

- Prior Task020 valid benchmark processes: 22.
- This port stage: 6 valid processes.
- Total valid benchmark processes: 28 / 30 plan limit.
- Remote final process query found no strata, llama, benchmark or related process. No process was stopped.
- Current-best remains the Task018 018-source promoted binary and canonical source. The rejected port binary remains versioned under the Task020 raw root and was not deployed.

COVERAGE / LIMITATIONS

- Connector coverage this cycle: main inbox/outbox, all 13 coordination/task-* branch heads, exact-head coordination trees, parser-relevant inbox/protocol/TASK plan files, and the locked Task020 plan were refreshed or SHA-verified through the connected GitHub connector. The connector snapshot was refreshed before guard inspection/resume.
- Remote coverage: strict host identity, durable Task020 checkpoint, process state, isolated source diff, build identity, candidate/control SHA256, prompt SHA256, all six structured results, command files, stdout/stderr, GPU snapshots, and process-before/after evidence.
- Large build and run logs remain on the remote host and were inspected through targeted error/metric/quality extraction; no full semantic audit of every log line or generated-token equality was performed.
- Tail-skip startup evidence is absent from the captured six-run logs; this is explicitly unresolved, not inferred from the source patch.

NEXT STEP

Keep the Task018 current-best binary/source unchanged. Do not promote the Task020 port. The campaign is complete at the first-stage reject gate; no further benchmark is justified under the remaining two-process budget.
<!-- LUNA_PUBLISHED_TASK_ID: LUNA-20261011-020 -->

[LUNA_REPORT]
TASK_ID: LUNA-20261011-021
STATUS: PARTIAL
TASK_SOURCE: branch
TASK_BRANCH: coordination/task-021-iq3xxs-nt1-20261011
TASK_COMMIT_SHA: 652b36d1311c295a00a757fcd928050dc33d2c4b
BENCHMARK_RAW_PATH: C:\Users\User\Strata-Adrian\runs\iq3-campaign-021

# LUNA-20261011-021 — IQ3_XXS NT=1 AVX2 route

## Decision

**REJECT / do not promote.** The route-share gate passed, and numerical parity passed, but the required one-token AVX2 microbench gate failed: IQ3_XXS gate+up was **248 us** with the AVX2 kernel versus **235 us** with ggml `vec_dot` (AVX2 is **5.53% slower** by elapsed time, not >=10% faster). Per the plan, no full A/B benchmark was run.

## Locked task identity

- TASK_ID: `LUNA-20261011-021`
- Source: `coordination/task-021-iq3xxs-nt1-20261011`
- Source branch commit: `652b36d1311c295a00a757fcd928050dc33d2c4b`
- Plan: `coordination/TASK_021_CAMPAIGN.md`
- Plan SHA: `b3ebc7562d4e00f3b321520290bb2acf409d80e8`
- Base source HEAD: `e26d5538b450ebf57942697f96242927dacfab77`

## Verified evidence

### Route census

One frozen 28,912-token / 1,024-output run was executed only with an isolated diagnostic binary, not as a performance comparison:

- Diagnostic binary: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-021\build-instrument-nt1\strata.exe`
- Diagnostic binary SHA256: `26EFAC0FE22CC1AE2B50CB34C4FAD01D6F47659B6D96B50A2067EFBDBE6E8BCB`
- Prompt SHA256: `9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA`
- `native_gu_rows` call counts: NT1 `864716`; NT>1 `74142`; total `938858`
- NT1 call share: `92.103%` (call-count share, not token- or row-weighted)
- Raw evidence: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-021\instrument-nt1-run\stdout.txt` and `stderr.txt`

The same diagnostic run reported decode `34.90 tok/s`, but that number is intentionally **not** used for comparison because its binary is not current-best.

### Candidate microbench and parity

The candidate was built in an isolated worktree with only this source change: allow `nt == 1 && avx2 && f.gu_type == 18` to enter the existing `iq256_gu_rows` path; all other route conditions were preserved.

- Candidate binary: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-021\build-candidate-nt1\strata.exe`
- Candidate binary SHA256: `0C2AE14A01ED1780A564FA62D4DA4002B612324294FF782BDC11BF7696E768E1`
- Existing current-best SHA256 reverified: `662C7E6103B29538EAF530FB2657BE0C384730F76D9805987695327C11967D71`
- Toolchain: MSVC `19.44.35226.0` / toolset `14.44.35207`; CUDA `13.2.78`; CMake `4.3`
- Existing parity tool: `native_expert_parity --synthetic iq3_xxs/q8_0`
- Parity: `0 failures`; IQ3 gate rel `3.15e-08`; width invariance `0` differing gate/up or down rows; q8_0 down `0/36` token sets differing; GPU decode-once/per-entry bitwise equal
- Microbench: AVX2 `248 us` vs ggml `235 us`; `+5.53%` elapsed time for AVX2, therefore gate failed
- Raw evidence: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-021\candidate-parity\synthetic-iq3-xxs-q8-0.txt`

## Scope and remaining state

- Canonical source was not modified.
- Current-best remains the Task018 binary `662C7E...`.
- No full candidate A/B, promotion, rollback, or benchmark claim was made.
- No relevant Strata/Luna process remained after validation.
<!-- LUNA_PUBLISHED_TASK_ID: LUNA-20261011-021 -->

[LUNA_REPORT]
TASK_ID: LUNA-20261011-022
STATUS: BLOCKED
TASK_SOURCE: branch
TASK_BRANCH: coordination/task-022-tail-skip-isolated-20261011
TASK_COMMIT_SHA: ceec34c41dbf18310afdce5aa368f24d57a42016
PLAN_PATH: coordination/TASK_022_CAMPAIGN.md
PLAN_SHA: c58c9ed75175cdde120f12e9bf93ecee2e42c2b5
TIME_ASIA_TAIPEI: 2026-10-11

DECISION: BLOCKED_BEFORE_TAIL_SKIP_BY_SKIP0_PARITY_GATE

SUMMARY

- Task022's authorized tail-skip hypothesis was not performance-tested. The mandatory skip0 preflight did not establish token parity with the 018 current-best control, so the harness stopped before STRATA_ROUTE_TAIL_SKIP=7.
- No candidate was promoted, deployed, copied into canonical, or used to infer a tail-skip improvement. Current-best remains the 018 binary.
- The preflight also exposed a reproducibility issue in the gate itself: the same 018 current-best binary produced different output-token SHA256 values in two otherwise equivalent control runs. The command records contain no explicit --seed or --temp argument; no temperature or seed setting was changed.

REMOTE IDENTITY

- HOST: DESKTOP-LKMLUPC (User@100.126.147.41; hostname verified)
- CANONICAL_SOURCE: C:\Users\User\Strata-Adrian-control
- CANONICAL_BRANCH / HEAD: main / e26d5538b450ebf57942697f96242927dacfab77
- CANONICAL_STATUS: pre-existing untracked .codex/handoffs/* and runs/ only; preserved unchanged
- ISOLATED_WORKTREE: C:\Users\User\Strata-Adrian\runs\iq3-campaign-022\source-tail-skip
- ISOLATED_BASE: e26d5538b450ebf57942697f96242927dacfab77
- ISOLATED_DIRTY_FILES: include/strata/core/expert_source.hpp, src/core/expert_source.cpp, src/program/generate.cpp; git diff --check passed
- No relevant strata, llama, or benchmark process remained in the final read-only tasklist check.

BUILD IDENTITY

- CONFIG: Release, NMake Makefiles, CUDA enabled, CUDA architecture 89
- TOOLCHAIN: Visual Studio 17.14.31 / MSVC toolset 14.44.35207 / compiler 19.44.35226.0 / CUDA 13.2.78
- LLAMACPP_DEPENDENCY_COMMIT: 3cf03257f219afbe7334045ff7c6a06ac68c627d (same in 018 and candidate dependency trees)
- CURRENT_BEST_BINARY: C:\Users\User\Strata-Adrian\runs\iq3-campaign-018\build-direct-slot-index\strata.exe
- CURRENT_BEST_SHA256: 662C7E6103B29538EAF530FB2657BE0C384730F76D9805987695327C11967D71
- REBUILT_CANDIDATE_BINARY: C:\Users\User\Strata-Adrian\runs\iq3-campaign-022\build-tail-skip\strata.exe
- REBUILT_CANDIDATE_SHA256: 5AF5A933EDD3C3344826516A1C9546467C64A4ECA366F49FAC09511D801D9E97
- An earlier candidate built against the unmodified e26 stage-cache shape was 83D2DE9533E657182E50F45F75F2A8B3ED6C1C0A984239958CA1E12786AE2096; it is retained only as failed preliminary evidence.
- The candidate source includes the isolated upstream tail-skip port plus the source-shape adjustment tested against the 018 worktree; canonical source was never changed.

FROZEN BENCHMARK IDENTITY

- Prompt: C:\Users\User\Strata-v0.1.38-ab-20261003\work-note-transfer-chat-20261005\neuro.tokens
- Prompt SHA256: 9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA
- Prompt tokens: 28,912; accepted output: 1,024
- IQ3_XXS pack/native/PLE, MTP runtime, max-context 100000, spec 6, kv q4_0, kv-resident 20480, expert-cache 3604, pool-workers 9, resident-budget-gib 20, MTP max 3, adaptive every 3/swaps 16/decay 0.60, and learned-heart profile were held constant.
- Environment: STRATA_FETCH_ADMIT=0, STRATA_RESIDENT_HEADROOM_GIB=3, STRATA_ADAPT_IF_MISS=1, STRATA_EXPERT_FILE_CACHE=1, STRATA_PF_FUSED=1, STRATA_LOOKAHEAD=0. No temperature change.

PARITY EVIDENCE

- Raw benchmark root: C:\Users\User\Strata-Adrian\runs\iq3-campaign-022
- Initial preflight: C:\Users\User\Strata-Adrian\runs\iq3-campaign-022\stage-a-parity. Candidate 83D2: 32.76 tok/s and 13,564.7 MB file reads; control 662C: 37.47 tok/s and 6,793.5 MB. Both accepted 1,024 and exited cleanly, but output-token SHA256 differed.
- Rebuilt preflight: C:\Users\User\Strata-Adrian\runs\iq3-campaign-022\stage-a-parity-rebuilt\summary.json. Candidate 5AF5: 36.91 tok/s, pool 25.575 ms/token, file reads 7,908.5 MB. Control 662C: 36.12 tok/s, pool 29.188 ms/token, file reads 8,797.3 MB. Both were VALID, exit=0, accepted_tokens=1024, residual_process_count=0, and first-logit KL=0, but output-token SHA256 differed: candidate 98BECF3E1A62397F71F8815C9D9362F89D2D3B0797DA0C9807A49ADDE4A0CE47 versus control C9B9C150B7880DD6144810078F8773E1B11702C0851279B5EEF14B296D170AC7.
- The earlier control output SHA256 was A61B281E7CE50595B0B4D2B3DCB99AF726BB8F6D6D23A3AC54EE3FDE2599388F under the same 662C binary in the initial preflight. This control-to-control difference means exact token parity is not a reliable gate without an explicit deterministic sampling identity.
- STRATA_ROUTE_TAIL_SKIP=7 was not run. tail_experts/tail_skipped are therefore unmeasured, not zero.

COMMAND / ENVIRONMENT PROVENANCE

- Both preflight arms used the task harness common command recorded in each raw command.json: same model shards, MTP, profile, prompt, --spec 6, --spec-min-p 0.75, --max-context 100000, --kv-resident 20480, --expert-cache 3604, --pool-workers 9, --max-new 1024, --resident-budget-gib 20 and adaptive settings above.
- Candidate skip0 explicitly set STRATA_ROUTE_TAIL_SKIP=0; the control did not set that variable. Both arms removed the PcieAuto/fraction override variables before launch; logs reported the fixed PCIe default 0.55. No PcieAuto experiment was run.

COVERAGE / LIMITATIONS

- Verified through the fresh @GitHub connector snapshot: main inbox/outbox, 15 coordination/task-* heads, exact Task022 branch plan and plan SHA. The locked task identity was preserved.
- Remote coverage included strict host identity, canonical source HEAD/status, isolated source status/diff check, CMake cache comparison, dependency commit, candidate/control SHA256, both parity summaries, both command/result JSON files, accepted-token counts, pool/file metrics, first-logit KL and final process-name check.
- Large stdout/stderr/build logs were not loaded wholesale; only structured result summaries and targeted identity/performance lines were used. Generated-token semantic equality beyond the recorded SHA values was not audited.

NEXT STEP

Keep the 018 current-best binary unchanged. A future task must define a deterministic sampling identity (or replace the exact token-parity gate with a justified numerical/quality gate) before another tail-skip A/B; do not treat the 36.91 versus 36.12 single-run difference as evidence of an improvement.

BENCHMARK_RAW_PATH: C:\Users\User\Strata-Adrian\runs\iq3-campaign-022
<!-- LUNA_PUBLISHED_TASK_ID: LUNA-20261011-022 -->

[LUNA_REPORT]
TASK_ID: LUNA-20261011-020
STATUS: PARTIAL
TASK_SOURCE: branch
TASK_BRANCH: coordination/task-020-upstream-v0142-20261011
TASK_COMMIT_SHA: befb373ea474247aee34b1bf7aa7f400165fe4d8
PLAN_PATH: coordination/TASK_020_CAMPAIGN.md
PLAN_SHA: 3cb03049f48e6d8238d66f03284d68e22c76fe8d
TIME_ASIA_TAIPEI: 2026-10-11
CORRECTION_TYPE: SUPPLEMENTAL_FOLLOW_UP

CORRECTION_REASON

The original published Task020 report retained only the final port-back-to-018 rejection and omitted valid intermediate measurements. This append-only follow-up restores those measurements without changing the final gate decision.

RESTORED INTERMEDIATE RESULTS

- stage-b-tail-old, tail-0: 37.71 / 34.16 / 34.13 tok/s.
- stage-b-tail-old, tail-7: 44.64 / 49.61 / 49.88 tok/s.
- stage-c-pcie, pcie-auto: 51.03 / 52.69 / 48.67 tok/s.
- stage-c-pcie, pcie-old: 48.54 / 47.88 / 46.33 tok/s.
- These recorded arms were VALID, accepted 1024 tokens and exited cleanly.

FINAL GATE REMAINS UNCHANGED

- The final stage-e port-back-to-018 paired results were candidate 34.05 / 35.90 / 37.15 versus current-best 38.20 / 38.00 / 35.82 tok/s.
- Paired deltas were -10.86%, -5.53% and +3.71%; paired median was -5.53% against the required >= +3% gate.
- Tail-skip activation evidence was absent from the captured stage-e logs, so the intermediate 50+ results cannot be treated as proof that the tail-skip change caused the final outcome.
- Therefore this follow-up restores evidence only; it does not promote the candidate or change the rejection/current-best decision.

EVIDENCE

- REMOTE_HOST: DESKTOP-LKMLUPC
BENCHMARK_RAW_PATH: C:\Users\User\Strata-Adrian\runs\iq3-campaign-020
- Original local report: D:\strata\state\LUNA-20261011-020.report.md
- This follow-up is append-only and references the original Task020 identity.

<!-- LUNA_FOLLOWUP_TASK_ID: LUNA-20261011-020 -->


[LUNA_REPORT]
TASK_ID: LUNA-20261011-020
TASK_SOURCE: branch
TASK_BRANCH: coordination/task-020-upstream-v0142-20261011
TASK_COMMIT_SHA: befb373ea474247aee34b1bf7aa7f400165fe4d8
CORRECTION_TYPE: SUPPLEMENTAL_FOLLOW_UP
STATUS: PARTIAL
TASK_PLAN_PATH: coordination/TASK_020_CAMPAIGN.md
TASK_PLAN_SHA: 3cb03049f48e6d8238d66f03284d68e22c76fe8d
BENCHMARK_RAW_PATH: C:\Users\User\Strata-Adrian\runs\iq3-campaign-020

SCOPE

Evidence-only supplement. No benchmark, build, source edit, canonical change, Task 020 re-claim, or Task 023 change was performed.

1. 50+ VERSION IDENTITY

The 50+ stage-b/c runs are the same captured v0.1.42 identity:

- Source: `upstream-v0142`, Git `61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406`, `git describe = v0.1.42`, clean worktree. The build cache has `CMAKE_HOME_DIRECTORY = ...\runs\iq3-campaign-020\upstream-v0142`.
- Executable: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\build-v0142\strata.exe`; it still exists; SHA256 `803C1EA975038328716FD4AD37BD9A21268A66AC60EB1F5C26171074A14CEF39`.
- Build cache: Release, NMake Makefiles, CUDA `v13.2.78`, MSVC `14.44.35207` (`cl.exe` path in `build-v0142\CMakeCache.txt`). This is the recorded build identity; it is not the earlier `14.44.35226` value.
- Model: IQ3_XXS, native pack `C:\Users\User\Strata-IQ3-20261008\packs\iq3_xxs`; GGUF shards are `Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf` SHA256 `219EA929900DFA9EF091F3AA473FDBA6874B65FCB36526D7D851AC9E95856D15` and `...00002-of-00002.gguf` SHA256 `316B46F3A2DBD68C900F43136AB9449F9DCC3725DFD8C794847C204BC161E113`.
- Prompt: `C:\Users\User\Strata-v0.1.38-ab-20261003\work-note-transfer-chat-20261005\neuro.tokens`, 28,912 prompt tokens, SHA256 `9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA`.
- Expert profile: `...\learned-heart.bin`, SHA256 `AA28BA0800A598DE0D83EBD83E918E2736BB2F4AB6750DB8AA72461E5829510F`.
- Common command identity in the captured `command.json` files: `--pack C:\Users\User\Strata-IQ3-20261008\packs\iq3_xxs --native C:\Users\User\Strata-IQ3-20261008\models\IQ3_XXS\Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf --ple-gguf C:\Users\User\Strata-IQ3-20261008\models\IQ3_XXS\Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf --mtp C:\Users\User\Strata-v0.1.34-mtp-test-20261002\mtp\rt --spec 6 --spec-min-p 0.75 --max-context 100000 --kv q4_0 --kv-resident 20480 --expert-profile C:\Users\User\Strata-v0.1.38-ab-20261003\work-note-transfer-chat-20261005\learned-heart.bin --expert-cache 3604 --pool-workers 9 --prefill auto --stats --tokens-file C:\Users\User\Strata-v0.1.38-ab-20261003\work-note-transfer-chat-20261005\neuro.tokens --max-new 1024 --suffix-draft 3 --resident-budget-gib 20 --mtp-max-t 3 --pool-affinity all --adapt-every 3 --adapt-swaps 16 --adapt-decay 0.60`, with the per-run environment and full argv retained in each `command.json`.
- Runtime evidence: engine `0.1.42`, KV `20480/100000`, 20.00 GiB expert RAM mode, 3,141 GPU-cache experts, clean exit and no residual process in all stage-b/c result records.
- Not fully portable/rebuild-complete: the native-pack directory and MTP `rt` directory do not have a single recorded tree SHA in the run manifest. The executable, source commit, model shard hashes, prompt/profile hashes, build cache and runtime arguments are preserved.

2. STAGE-B/C SETTINGS AND 12-RUN RECONSTRUCTION

Stage-b `tail-0` and `tail-7` use identical source, binary, model, prompt, argv and common environment. The captured change is only `STRATA_ROUTE_TAIL_SKIP=0` versus `7`; both also set `STRATA_PCIE_FRAC_DEFAULT=old`. Stage-c `pcie-old` and `pcie-auto` both fix `STRATA_ROUTE_TAIL_SKIP=7`; the only captured policy change is `STRATA_PCIE_FRAC_DEFAULT=old` versus the variable being unset (auto).

Every row below is `VALID`, accepted 1,024, exit code 0, residual process count 0. For each `RUN_DIR`, the original files are exactly `RUN_DIR\result.json`, `RUN_DIR\command.json`, `RUN_DIR\stdout.log`, `RUN_DIR\stderr.log`, `RUN_DIR\gpu-before.txt`, and `RUN_DIR\gpu-after.txt` under `BENCHMARK_RAW_PATH`.

| stage | run / UTC start | binary | decode tok/s | pool ms/token | file MB | raw run directory |
|---|---|---|---:|---:|---:|---|
| b | pair-01-tail-0 / 07:55:55.202Z | V0142 | 37.71 | 24.763 | 7648.8 | `stage-b-tail-old\pair-01-tail-0` |
| b | pair-01-tail-7 / 07:57:18.176Z | V0142 | 44.64 | 19.000 | 7270.1 | `stage-b-tail-old\pair-01-tail-7` |
| b | pair-02-tail-0 / 07:58:40.153Z | V0142 | 34.16 | 34.081 | 15947.5 | `stage-b-tail-old\pair-02-tail-0` |
| b | pair-02-tail-7 / 08:00:10.208Z | V0142 | 49.61 | 16.718 | 3941.0 | `stage-b-tail-old\pair-02-tail-7` |
| b | pair-03-tail-0 / 08:01:32.154Z | V0142 | 34.13 | 32.452 | 15809.3 | `stage-b-tail-old\pair-03-tail-0` |
| b | pair-03-tail-7 / 08:03:01.217Z | V0142 | 49.88 | 16.991 | 3668.4 | `stage-b-tail-old\pair-03-tail-7` |
| c | pair-01-pcie-old / 08:04:17.148Z | V0142 | 48.54 | 17.357 | 4055.9 | `stage-c-pcie\pair-01-pcie-old` |
| c | pair-01-pcie-auto / 08:05:35.038Z | V0142 | 51.03 | 18.496 | 3173.9 | `stage-c-pcie\pair-01-pcie-auto` |
| c | pair-02-pcie-old / 08:06:55.004Z | V0142 | 47.88 | 17.680 | 4481.0 | `stage-c-pcie\pair-02-pcie-old` |
| c | pair-02-pcie-auto / 08:08:14.975Z | V0142 | 52.69 | 12.783 | 2265.8 | `stage-c-pcie\pair-02-pcie-auto` |
| c | pair-03-pcie-old / 08:09:31.934Z | V0142 | 46.33 | 17.056 | 5882.1 | `stage-c-pcie\pair-03-pcie-old` |
| c | pair-03-pcie-auto / 08:10:50.908Z | V0142 | 48.67 | 16.720 | 3842.4 | `stage-c-pcie\pair-03-pcie-auto` |

Paired deltas, candidate minus control: stage-b tail-7 vs tail-0 = `+18.38%, +45.23%, +46.15%`, median `+45.23%`; stage-c auto vs old = `+5.13%, +10.05%, +5.05%`, median `+5.13%`. The stage-b/c logs show the same startup model/KV/RAM/cache identity and greedy generation; no separate semantic correctness artifact is present.

Tail/PCIe activation evidence is incomplete. `command.json` proves the requested environment values, but the stage-b/c stdout/stderr and `result/summary.json` do not contain `tail_experts`, `tail_skipped`, `STRATA_ROUTE_TAIL_SKIP=... is ON`, or a PCIe-share update counter. They contain the PCIe probe (`pcie_frac 0.55`) and expert tier/file-read counters only. Thus the A/B variable assignment is verified, while runtime tail activation and the auto-share update are not.

3. STAGE-E DIFFERENCE AND SLOWDOWN

Stage-e is not the stage-c binary ported transparently:

- Stage-c: clean v0.1.42 source `61b3fb5...`, binary V0142 `803C1EA...`, `STRATA_ROUTE_TAIL_SKIP=7`, auto policy unset.
- Stage-e control: existing Task 018 executable `C:\Users\User\Strata-Adrian\runs\iq3-campaign-018\build-direct-slot-index\strata.exe`, SHA `662C7E6103B29538EAF530FB2657BE0C384730F76D9805987695327C11967D71`; `source_commit` is null in its result record.
- Stage-e candidate: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\build-port-018\strata.exe`, SHA `A69AD06808589F4200E10E6213C59CDD9DBCCB05958050529487B4A25ADC8EC9`; source tree `port-018` is `e26d5538b450ebf57942697f96242927dacfab77-dirty`, with 3 modified files (`include/strata/core/expert_source.hpp`, `src/core/expert_source.cpp`, `src/program/generate.cpp`), diff stat 137 insertions/3 deletions. Its build cache points to `port-018`, with the same recorded Release/NMake/CUDA 13.2.78/MSVC 14.44.35207 toolchain.
- The captured port diff adds tail counters/defaulting and PcieAuto code. However, stage-e candidate `command.json` does not set `STRATA_ROUTE_TAIL_SKIP`; its logs contain no tail ON/counter marker. It does contain direct PCIe-share markers: `pcie_frac 0.35 (was 0.55)` with CPU-pool measurements 70/77/72 us per missed expert. This is a runtime identity difference, not proof of a causal slowdown.
- Stage-e candidate vs current-best decode is `34.05 / 35.90 / 37.15` vs `38.20 / 38.00 / 35.82`, paired deltas `-10.86%, -5.53%, +3.71%`, median `-5.53%`. Existing evidence directly supports binary/source/settings mismatch and missing tail activation proof; it does not isolate which source/runtime difference caused the loss.

4. ALL 28 VALID EXECUTIONS

The raw tree contains exactly 28 stage result records: stage-a 6, stage-b 6, stage-c 6, stage-d 4, stage-e 6; all are `VALID`. The 10 previously unitemized executions are therefore stage-a and stage-d, not missing runs. `NOT_RUN` is not assigned to any record; inaccessible/unrecorded fields are marked below as INCONCLUSIVE rather than treated as non-execution.

| stage | run directories under raw root | binary(s) | decode tok/s | status / evidence |
|---|---|---|---|---|
| a-defaults | `stage-a-defaults\pair-01-control-018`, `pair-01-v0142-default`, `pair-02-control-018`, `pair-02-v0142-default`, `pair-03-control-018`, `pair-03-v0142-default` | current-best `662C7E...` / V0142 `803C1E...` | control `33.91, 33.39, 36.63`; V0142 `36.54, 39.07, 38.30` | VERIFIED run/result/command/stdout/stderr paths; 1,024 accepted each |
| b-tail-old | `stage-b-tail-old\pair-01-tail-0`, `pair-01-tail-7`, `pair-02-tail-0`, `pair-02-tail-7`, `pair-03-tail-0`, `pair-03-tail-7` | V0142 `803C1E...` | `37.71, 44.64, 34.16, 49.61, 34.13, 49.88` in chronological order | VERIFIED; settings differ only in captured tail env |
| c-pcie | `stage-c-pcie\pair-01-pcie-old`, `pair-01-pcie-auto`, `pair-02-pcie-old`, `pair-02-pcie-auto`, `pair-03-pcie-old`, `pair-03-pcie-auto` | V0142 `803C1E...` | `48.54, 51.03, 47.88, 52.69, 46.33, 48.67` in chronological order | VERIFIED; both arms tail=7; auto runtime update INCONCLUSIVE |
| d-confirm | `stage-d-confirm\pair-01-v0142-tail7-auto`, `pair-01-control-018`, `pair-02-v0142-tail7-auto`, `pair-02-control-018` | V0142 `803C1E...` / current-best `662C7E...` | candidate `47.33, 52.62`; control `35.28, 34.30` | VERIFIED runs; 2 confirm pairs. `result.json` prompt_tokens/output_tokens are null, while accepted=1,024 and command files exist: identity field completeness INCONCLUSIVE |
| e-port-018 | `stage-e-port-018\pair-01-port-018-default`, `pair-01-control-018`, `pair-02-port-018-default`, `pair-02-control-018`, `pair-03-port-018-default`, `pair-03-control-018` | port `A69AD0...` / current-best `662C7E...` | candidate `34.05, 35.90, 37.15`; control `38.20, 38.00, 35.82` | VERIFIED run/result/command/stdout/stderr paths; promotion rebench failed median gate |

Execution order was interleaved within each pair: stage-a v0142 then control for pairs 1-3; stage-b tail-0 then tail-7 for pairs 1-3; stage-c old then auto for pairs 1-3; stage-d v0142 then control for pairs 1-2; stage-e port then control for pairs 1-3. No separate quality/correctness evaluator file was found under the five stage directories; existing evidence is clean exit, accepted output length, startup/runtime lines and preserved stdout/stderr, so semantic quality remains INCONCLUSIVE.

5. DECISIONS

1. **Comparable workload: YES, with identity caveat.** Stage-c is IQ3_XXS, 28,912-token prompt, 1,024 accepted output, context 100,000, MTP 6, q4_0 KV with 20,480 resident cells, 20 GiB expert RAM and the same model/prompt/profile paths used by the Task 018 comparison. It is comparable as a workload/settings measurement, but not binary-equivalent to Task 018 current-best.
2. **Preserved direct candidate: YES; canonical candidate: NO.** The v0.1.42 source, clean build directory, binary SHA, model shard hashes, prompt/profile hashes, build cache, command files and raw logs still exist and are sufficient for same-host direct deployment. It is not canonical: the Task 020 port-back candidate is a different dirty source/binary and failed its own rebench gate; current-best remains `662C7E...`.
3. **Overall promotion gate: NOT SATISFIED.** Stage-c has three positive paired comparisons (median `+5.13%`) and stage-d has two positive confirmation pairs (`+34.16%, +53.41%`), but the required port-back-to-018 rebench is `-5.53%` median, and the required tail activation/quality evidence is absent. The missing/failed items are: successful >=3% port-back median, verified tail counters/activation, and an independent output-quality/correctness check.

COVERAGE

Checked: the locked Task 020 plan at branch commit `befb373ea474247aee34b1bf7aa7f400165fe4d8` / plan blob `3cb03049f48e6d8238d66f03284d68e22c76fe8d`; local original report `D:\strata\state\LUNA-20261011-020.report.md` SHA256 `60C48AF225FB95802547659FDD74862039814E975918370FD417823F5167B738`; the remote stage-a/b/c/d/e manifest tree, all 28 `result.json` and `command.json` records, associated stdout/stderr/gpu files, the two source worktrees, both build caches, binary hashes, model/prompt/profile hashes, and targeted tail/PCIe marker scans. Large stdout files were scanned for targeted activation/error markers, not semantically reread line-by-line. No files were modified remotely and no new benchmark/build was run.

<!-- LUNA_EVIDENCE_SUPPLEMENT_TASK_ID: LUNA-20261011-020 -->



---

[LUNA_BLOCKED]

TASK_ID: LUNA-20261011-023
REPORT_TYPE: STAGE_A_QUALITY_BLOCK
TASK_SOURCE: branch
SOURCE_BRANCH: coordination/task-023-v0142-overnight-20261012
SOURCE_BRANCH_SHA: 9d22fb6424bc98f958b96aa2a6356fad90903429
TASK_BRANCH: coordination/task-023-v0142-overnight-20261012
TASK_COMMIT_SHA: 9d22fb6424bc98f958b96aa2a6356fad90903429
PLAN_PATH: coordination/TASK_023_CAMPAIGN.md
PLAN_SHA: bf1bb30c72b1e10a0ae62ae938140bc4952bc77e
LINKED_PLAN_PATH: coordination/TASK_023_OVERNIGHT.md
LINKED_PLAN_SHA: c43e6dc72560207827e21efd86a6f814a068e631
HOST: DESKTOP-LKMLUPC

## Decision

Stage A is blocked before Stage B/C promotion. The new diagnostic proves that the tail-skip path executed, but the preserved v0.1.42 candidate fails the deterministic quality gate against the Task 018 control: first-token logit KL is `0.0248568353`, above the locked `0.006` bound. The runtime policy counter reports `pcie share 141/256`, but distinct PCIe expert reads remain `0.00`; this proves policy/counter activation, not actual PCIe expert data movement. Under the locked 023 plan, no interleaved comparison or promotion is authorized with this candidate.

## Verified provenance

- Task 020 v0.1.42 source: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\upstream-v0142`, commit `61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406`, clean detached worktree.
- Task 020 v0.1.42 binary: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\build-v0142\strata.exe`, SHA256 `803c1ea975038328716FD4AD37BD9A21268A66AC60EB1F5C26171074A14CEF39`.
- Task 018 current-best reference binary remains `C:\Users\User\Strata-Adrian\runs\iq3-campaign-018\build-direct-slot-index\strata.exe`, SHA256 `662c7e6103b29538eaf530fb2657be0c384730f76d9805987695327c11967d71`; it was not replaced or promoted.
- Diagnostic worktree: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-023\diagnostic-v0142`, base commit `61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406`, isolated diff is 24 added lines in `src\program\generate.cpp` only, guarded by `STRATA_TASK023_DIAGNOSTIC`.
- Diagnostic binary: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-023\build-diagnostic-v0142\strata.exe`, SHA256 `D9A9064AFDCE24AD64F5DE2ACA16F48489CBFC761CC8DAC6B95574F04200EFA9`. It is diagnostic-only, not a canonical candidate.

## Stage A evidence

The existing Task 020 raw campaign contains 28 valid campaign result manifests (6 stage-a, 6 stage-b, 6 stage-c, 4 stage-d, 6 stage-e), each with 1024 accepted output. The two `result.json` files under the upstream benchmark tree were excluded as unrelated. Existing stage-c PCIe-auto reported 51.03/52.69/48.67 tok/s, but its raw logs did not contain a tail activation marker or a nonzero PCIe expert counter.

The new single diagnostic run used the exact Task 020 stage-c PCIe-auto model, prompt, 1024 output, KV/MTP, resident, cache, profile, and environment settings, with only the diagnostic binary changed:

- Raw directory: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-023\diagnostic-v0142-run-pcie-auto`
- Command: `command.json`; stdout: `stdout.log`; stderr: `stderr.log`; result: `result.json`; GPU/process snapshots: `gpu-before.txt`, `gpu-after.txt`, `process-before.txt`, `process-after.txt`.
- Environment included `STRATA_ROUTE_TAIL_SKIP=7`; `STRATA_PCIE_FRAC_DEFAULT` was unset, so PCIe auto selected probe-derived `pcie_frac 0.48`.
- Process status: exit 0, `VALID` diagnostic execution, 1024 accepted, 44.30 tok/s, CPU expert pool 18.318 ms/token, 5902.0 MB file reads, resident RAM 18.33 GiB.
- Runtime output: `pcie experts 0.00 distinct experts per layer read over PCIe (share 124/256 of the misses)`.
- A later rebuild of the same isolated diagnostic worktree added a final marker without changing canonical source. Its raw run is `C:\Users\User\Strata-Adrian\runs\iq3-campaign-023\diagnostic-v0142-run-pcie-auto-final`; binary SHA256 `0F505B6DC48FF1F4BEB6EC3670E30DC05D7A2449AB760AE76E61F0C3626321D2`. It exited 0 with 1024 accepted and 43.54 tok/s. `stderr.log` records `TASK023_DIAGNOSTIC_FINAL tail_env=7 pcie_default_env=<unset> tail_experts=60752 tail_skipped=62492 pcie_experts=0 pcie_num=141`, while stdout records `pcie experts 0.00 ... (share 141/256 ...)`. This proves tail-skip counters and policy activation for the diagnostic build; it does not prove nonzero PCIe expert reads.

The deterministic quality-prefix check then ran three new short executions under `C:\Users\User\Strata-Adrian\runs\iq3-campaign-023\quality-prefix` with the same prompt SHA `9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA`, context 100000, KV q4_0, MTP max 3, resident budget 20 GiB, profile, expert cache, pool workers, and adaptive settings. Only the binary/source arm and `STRATA_ROUTE_TAIL_SKIP` differed:

- `control-01` and `control-02`: binary `662C7E6103B29538EAF530FB2657BE0C384730F76D9805987695327C11967D71`, source `e26d5538b450ebf57942697f96242927dacfab77`, no tail-skip variable.
- `v0142-01`: binary `803C1EA975038328716FD4AD37BD9A21268A66AC60EB1F5C26171074A14CEF39`, source `61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406`, `STRATA_ROUTE_TAIL_SKIP=7`.
- All three exited 0 and emitted 993280-byte `first_logits.bin`; `summary.json` reports baseline noise KL `0`, candidate KL `0.024856835304406362`, quality bound `0.006`, decision `QUALITY_FAIL`.
- Raw paths: `control-01\\command.json`, `control-01\\stdout.log`, `control-01\\stderr.log`, `control-01\\result.json`; equivalent files under `control-02` and `v0142-01`.

## What was not run

- No Stage B interleaved control-v0142 pairs because the candidate failed the quality gate.
- No Stage B confirmation pairs.
- No Stage C source experiment.
- No source change was made in the canonical worktree; no canonical binary/settings were changed.
- No process was stopped.

## Coverage and remaining gap

Coverage is complete for the requested existing Task 020 campaign manifest set (28 campaign `result.json` files), the two linked 023 plan files, the targeted v0.1.42 source locations, the relevant Task 020 stage-c command/log/result artifacts, the isolated activation diagnostic, and the three quality-prefix runs. A prior broad recursive source scan was not used for conclusions because its shell wildcard scope was invalid; only the exact worktree files and run paths above support this report. Remaining gap: explain or repair the source/binary identity difference that produces the measured KL failure before any Stage B gate comparison. The 023 plan permits an isolated repair only after a defensible source-level hypothesis; this report does not claim one.

BENCHMARK_RAW_PATH: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-023\diagnostic-v0142-run-pcie-auto`
REPORT_LOCAL: `D:\strata\state\LUNA-20261011-023.report.md`
<!-- LUNA_PUBLISHED_TASK_ID: LUNA-20261011-023 -->

---

[LUNA_BLOCKED]
TASK_ID: LUNA-20261012-024
STATUS: BLOCKED
TASK_SOURCE: branch
TASK_BRANCH: coordination/task-024-v0142-quality-layer-mask-20261012
TASK_COMMIT_SHA: c02382b0170cb8b74a4c119ad7634b2245216b26
PLAN_PATH: coordination/TASK_024_CAMPAIGN.md
PLAN_SHA: f2db53af0b5f01da28207fc4f788e1a8e5f5de91

OUTCOME: REJECT_QUALITY; no canonical promotion.

REMOTE: DESKTOP-LKMLUPC / desktop-lkmlupc\\user. Canonical source is C:\Users\User\Strata-Adrian-control, branch main, HEAD e26d5538b450ebf57942697f96242927dacfab77. The canonical worktree was not modified by Task 024; its reported dirty state remains limited to the pre-existing untracked .codex/handoffs and runs paths. No Strata/Llama process remained after any run.

IDENTITY:
- Existing v0.1.42 candidate: C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\build-v0142\strata.exe, SHA256 803c1ea975038328716fd4ad37bd9a21268a66ac60eb1f5c26171074a14cef39, source 61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406.
- Isolated diagnostic worktree: C:\Users\User\Strata-Adrian\runs\iq3-campaign-024\diagnostic-tail-norm, detached at source 61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406; canonical source untouched.
- Instrumented profile binary: C:\Users\User\Strata-Adrian\runs\iq3-campaign-024\build-tail-norm-profile\strata.exe, SHA256 bc4b02fe80aac005730f1fdb3cf2a2e0c3254333bfcb0ef30eb52a6b73dd6a90.
- Profile-derived layer-mask binary: same isolated build path after the mask patch, SHA256 7cdf23e36cddb5ee85e7e9482ae8e778dcd6ab85158c949d00ea6c81d037eba3.

QUALITY EVIDENCE:
- Frozen Task 023 control vs existing v0.1.42 tail7 prefix: control noise KL 0; tail7 candidate KL 0.024856835304406362; bound 0.006; existing tail7 is QUALITY_FAIL.
- Task 024 v0.1.42 tail0 prefix, same IQ3 pack/model/MTP/prompt/context/KV/20 GiB settings and STRATA_ROUTE_TAIL_SKIP unset: tail0 KL 0; bound 0.006; QUALITY_PASS. Raw: C:\Users\User\Strata-Adrian\runs\iq3-campaign-024\quality-tail0-prefix.
- One instrumented tail7 omitted-output norm profile, STRATA_TASK024_TAIL_NORM_PROFILE=1, raw: C:\Users\User\Strata-Adrian\runs\iq3-campaign-024\tail-norm-profile. The marker covered layers 0-47. The measured RMS showed a low-norm cluster through layer 29 (layer 29 RMS 1.4029444; layer 30 RMS 2.57113895), so the isolated mask selected layers 0-29 for tail skipping and evaluated layers 30-47 normally. This is the only profile-derived mask tested; no rank sweep was run.
- Mask-prefix quality run used STRATA_ROUTE_TAIL_SKIP=7 and STRATA_TASK024_LAYER_MASK=1, where layers 0-29 retain tail7 skip and layers 30-47 compute the omitted tail expert. Captured 248320 logits (993280 bytes); KL vs the existing control was 0.052673740368450093, bound 0.006, QUALITY_FAIL. Raw: C:\Users\User\Strata-Adrian\runs\iq3-campaign-024\tail-layer-mask-prefix.
- The norm profile and mask source/build logs are retained under C:\Users\User\Strata-Adrian\runs\iq3-campaign-024\build-tail-norm-profile (build.log and build-mask.log). All four Task 024 quality/diagnostic processes exited 0 with residual process count 0.

FROZEN SETTINGS FOR THE QUALITY RUNS: IQ3_XXS pack; native and PLE GGUF shards; MTP rt; prompt C:\Users\User\Strata-v0.1.38-ab-20261003\work-note-transfer-chat-20261005\neuro.tokens SHA256 9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA; context 100000; KV q4_0 with 20480 MiB resident; expert profile learned-heart.bin; expert cache 3604; pool workers 9; prefill auto; greedy max-new 1; resident budget 20 GiB; MTP max t 3; pool affinity all; adapt every 3/swaps 16/decay 0.60. Base environment: STRATA_FETCH_ADMIT=0, STRATA_RESIDENT_HEADROOM_GIB=3, STRATA_ADAPT_IF_MISS=1, STRATA_EXPERT_FILE_CACHE=1, STRATA_PF_FUSED=1, STRATA_LOOKAHEAD=0. Tail7 runs set STRATA_ROUTE_TAIL_SKIP=7; tail0 left it unset.

BENCHMARK_RAW_PATH: C:\Users\User\Strata-Adrian\runs\iq3-campaign-024

GATE: The prefix quality gate did not pass for the one profile-derived layer mask (KL 0.052673740368450093 > 0.006). Therefore the required 3 interleaved pairs and 2 confirmation pairs were not authorized/executed, no speed median is claimed, and no source/binary/settings are promoted. Next step would require a new explicit task/plan with a different quality-preserving mask rule; this task has no promotable candidate.

[LUNA_REPORT] LUNA-20261012-025

TASK_ID: LUNA-20261012-025
CORRECTION_TYPE: TASK_EXECUTION_REPORT
TASK_SOURCE: branch
TASK_BRANCH: coordination/task-025-v0142-speed-first-async-miss-20261012
TASK_COMMIT_SHA: 1b8c7e49cb80d80eec14330b484a9e95ec35c002
SOURCE_BRANCH: coordination/task-025-v0142-speed-first-async-miss-20261012
SOURCE_BRANCH_SHA: 1b8c7e49cb80d80eec14330b484a9e95ec35c002
PLAN_PATH: coordination/TASK_025_CAMPAIGN.md
PLAN_SHA: 6f545ed3d4f9b4aba95b14e95b7c126e9befe936
REMOTE_HOST: DESKTOP-LKMLUPC
RAW_ROOT: C:\Users\User\Strata-Adrian\runs\iq3-campaign-025

## Result

DECISION: PARTIAL_SPEED_PASS_PROMOTION_BLOCKED
STAGE_A_GATE: PASS
STAGE_A_PAIRED_MEDIAN_DELTA: 28.14%
STAGE_B_GATE: PASS
STAGE_B_PAIRED_MEDIAN_DELTA: 38.81%
CONFIRM_PAIRS: pairs 4 and 5 in both stages; all paired deltas >= 3%
QUALITY_GATE: INCONCLUSIVE_FOR_PROMOTION
PROMOTION: NOT_APPLIED

The plan-authorized speed gates passed. The candidate source is not promoted into the canonical checkout because the exact v0.1.42 patch does not apply cleanly to the canonical e26d5538 source (`git apply --check` failed at `src/core/expert_source.cpp:3741`). No canonical source, canonical binary, or canonical settings were changed, and no push was made.

## Verified identities

Canonical source checkout:

- `C:\Users\User\Strata-Adrian-control`
- branch `main`, HEAD `e26d5538b450ebf57942697f96242927dacfab77`
- pre/post status contained only pre-existing untracked `.codex/handoffs/` and `runs/`; no tracked canonical change

Baseline v0.1.42 candidate:

- binary: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\build-v0142\strata.exe`
- SHA256: `803C1EA975038328716FD4AD37BD9A21268A66AC60EB1F5C26171074A14CEF39`
- source: preserved `upstream-v0142` worktree at `C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\upstream-v0142`, HEAD `61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406`

Canonical control:

- binary: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-018\build-direct-slot-index\strata.exe`
- SHA256: `662C7E6103B29538EAF530FB2657BE0C384730F76D9805987695327C11967D71`
- control source identity used in the locked manifest: `e26d5538b450ebf57942697f96242927dacfab77`

Async-miss isolated candidate:

- worktree: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-025\source-async-miss`
- base HEAD: `61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406`
- modified file only: `src/core/expert_source.cpp`
- patch: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-025\task025_async.patch`
- patch SHA256: `BA592A98D9804F48E772B13CB9F8BB1472B65AC713ED8AA45DEB4C0263B49169`
- binary: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-025\build-async-miss\strata.exe`
- SHA256: `E3FA77FE1C7BA9AD957F3EE61F195DAED433CA46C1E523C4B7E9E487498C27FB`
- build manifest: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-025\task025_build_async.cmd`
- build: Release, NMake Makefiles, CUDA arch 89, `STRATA_ENABLE_CUDA=ON`, VS 2022 MSVC 14.44.35207, CUDA 13.2.78

The isolated patch moves the distinct CPU-miss `prefetch()` enqueue before GPU/remote launch while retaining blob access as the wait point. The original post-quantization prefetch block was removed; the existing `c2` timing measurement was retained after the quantization block.

## Fixed benchmark identity

Model/pack:

- IQ3_XXS pack: `C:\Users\User\Strata-IQ3-20261008\packs\iq3_xxs`
- native shard: `C:\Users\User\Strata-IQ3-20261008\models\IQ3_XXS\Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00001-of-00002.gguf`
- PLE shard: `C:\Users\User\Strata-IQ3-20261008\models\IQ3_XXS\Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS-00002-of-00002.gguf`
- prompt: `C:\Users\User\Strata-v0.1.38-ab-20261003\work-note-transfer-chat-20261005\neuro.tokens`
- prompt SHA256: `9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA`
- prompt tokens: 28912; accepted output: 1024
- context: 100000; MTP: 6; KV: q4_0; KV resident: 20480 MiB; resident budget: 20 GiB
- profile: `C:\Users\User\Strata-v0.1.38-ab-20261003\work-note-transfer-chat-20261005\learned-heart.bin`

Common args (both stages): `--pack <iq3_xxs> --native <shard-00001> --ple-gguf <shard-00002> --mtp C:\Users\User\Strata-v0.1.34-mtp-test-20261002\mtp\rt --spec 6 --spec-min-p 0.75 --max-context 100000 --kv q4_0 --kv-resident 20480 --expert-profile <learned-heart.bin> --expert-cache 3604 --pool-workers 9 --prefill auto --stats --tokens-file <neuro.tokens> --max-new 1024 --suffix-draft 3 --resident-budget-gib 20 --mtp-max-t 3 --pool-affinity all --adapt-every 3 --adapt-swaps 16 --adapt-decay 0.60`

Base environment: `STRATA_FETCH_ADMIT=0`, `STRATA_RESIDENT_HEADROOM_GIB=3`, `STRATA_ADAPT_IF_MISS=1`, `STRATA_EXPERT_FILE_CACHE=1`, `STRATA_PF_FUSED=1`, `STRATA_LOOKAHEAD=0`.

Candidate-only runtime setting: `STRATA_ROUTE_TAIL_SKIP=7` (PCIe Auto remained selected by leaving `STRATA_PCIE_FRAC_DEFAULT` unset). Canonical control left both override variables unset.

## Paired raw results

All rows were `VALID`: exit code 0, 1024 accepted tokens, and zero residual Strata/Llama processes. Delta is `(candidate / canonical - 1) * 100`.

Stage A raw summary: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-025\stage-a-baseline\summary.json`

| pair | candidate tok/s | control tok/s | delta | candidate pool ms/token | control pool ms/token |
|---:|---:|---:|---:|---:|---:|
| 1 | 42.62 | 30.86 | 38.08% | 20.103 | 34.583 |
| 2 | 35.62 | 31.17 | 14.28% | 24.670 | 35.834 |
| 3 | 47.10 | 29.23 | 61.14% | 18.581 | 35.913 |
| 4 confirm | 43.49 | 36.29 | 19.84% | 17.310 | 28.252 |
| 5 confirm | 39.66 | 30.95 | 28.14% | 26.339 | 34.185 |
| median | 42.62 | 30.95 | 28.14% | — | — |

Stage B raw summary: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-025\stage-b-async-miss\summary.json`

| pair | async candidate tok/s | new control tok/s | delta | candidate pool ms/token | control pool ms/token |
|---:|---:|---:|---:|---:|---:|
| 1 | 41.15 | 35.90 | 14.62% | 22.141 | 25.205 |
| 2 | 49.45 | 34.60 | 42.92% | 15.667 | 28.576 |
| 3 | 49.83 | 34.96 | 42.53% | 13.198 | 29.556 |
| 4 confirm | 50.26 | 38.64 | 30.07% | 14.280 | 27.274 |
| 5 confirm | 46.89 | 33.78 | 38.81% | 16.684 | 32.141 |
| median | 49.45 | 34.96 | 38.81% | — | — |

Stage B run directory also contains each `command.json`, `stdout.log`, `stderr.log`, `result.json`, GPU before/after capture, and process-before/after capture under the pair directories. Runner logs: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-025\async-runner.stdout.log` and `C:\Users\User\Strata-Adrian\runs\iq3-campaign-025\async-runner.stderr.log`.

## Quality and limitations

- Existing quality evidence was reused as required; no new tail/PCIe/KL run was performed. Relevant preserved files include `C:\Users\User\Strata-Adrian\runs\iq3-campaign-024\quality-tail0-prefix\command.json`, `result.json`, `first_logits.bin`, `stdout.log`, and `stderr.log`.
- The 20 new speed rows all reached 1024 accepted tokens, exited cleanly, and left zero residual processes. Output token-count/hash fields are recorded in each result; hashes vary between runs, so this report does not claim exact-output equivalence or semantic-quality equivalence.
- KL remains diagnostic per TASK_025 and was not used as a blocker. A semantic quality evaluator for the new async candidate was not available in this run, and the source identity mismatch blocks canonical promotion until the equivalent patch is ported and separately verified on canonical base.
- No canonical source/binary/settings were changed. No Strata process remained active after the runs.

BENCHMARK_RAW_PATH: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-025`
REPORT_LOCAL: `D:\strata\state\LUNA-20261012-025.report.md`

<!-- LUNA_PUBLISHED_TASK_ID: LUNA-20261012-025 -->

[LUNA_REPORT]
TASK_ID: LUNA-20261012-026
STATUS: PARTIAL
TASK_SOURCE: branch
TASK_BRANCH: coordination/task-026-direct-v0142-async-promote-20261012
TASK_COMMIT_SHA: 44c8348befdc2d62fe9c679c2cc67da38d863b26
PLAN_PATH: coordination/TASK_026_CAMPAIGN.md
PLAN_SHA: 9e42540b58bcd46fa55a3bbbf4a73e9d5e878fce

REMOTE_HOST: DESKTOP-LKMLUPC
REMOTE_SOURCE: C:\Users\User\Strata-Adrian-control
REMOTE_SOURCE_BRANCH: main
REMOTE_SOURCE_HEAD: e26d5538b450ebf57942697f96242927dacfab77
REMOTE_SOURCE_DIRTY: only untracked .codex/handoffs/* and runs/ observed; no canonical source file change.

CANDIDATE_SOURCE: detached run checkout 61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406 + task025_async.patch
CANDIDATE_PATCH_SHA256: BA592A98D9804F48E772B13CB9F8BB1472B65AC713ED8AA45DEB4C0263B49169
CANDIDATE_BINARY: C:\Users\User\Strata-Adrian\runs\iq3-campaign-026\build-causal-fix\strata.exe
CANDIDATE_BINARY_SHA256: 77F5DA99126BC166E48B4A87519E80DFD618BCA917AB393F6C3473FC8644C84F
CONTROL_BINARY: C:\Users\User\Strata-Adrian\runs\iq3-campaign-026\promoted-v0142\strata.exe
CONTROL_BINARY_SHA256: E3FA77FE1C7BA9AD957F3EE61F195DAED433CA46C1E523C4B7E9E487498C27FB

PROMPT_SHA256: 9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA
PROMPT_TOKENS: 28912
OUTPUT_TOKENS: 1024
BENCHMARK_RAW_PATH: C:\Users\User\Strata-Adrian\runs\iq3-campaign-026\stage-c-causal-fix
RAW_EVIDENCE_PATH: C:\Users\User\Strata-Adrian\runs\iq3-campaign-026\stage-c-causal-fix
RAW_SUMMARY_SHA256: E812929599EBAF6CBCE1F54D98FA339BDBA929B9FDB642CB045E66348EC6B542

BENCHMARK_RESULT: 5/5 matched pairs VALID; all runs accepted 1024 tokens, exit code 0, and left no residual Strata process.
PAIR_DECODE_TOK_S: causal-fix [30.65,31.69,32.89,32.35,28.88]; control [24.40,24.53,21.96,19.14,14.50]
PAIR_DELTA_PERCENT: [25.61,29.19,49.77,69.02,99.17]
MEDIAN_DELTA_PERCENT: 49.77
GATE: PASS (median exceeds 3% and five same-control confirmations are valid).

ABSOLUTE_SPEED_NOTE: The current candidate is 28.88-32.89 tok/s, below the prior Task025 v0142 stage-B 41.15-50.26 tok/s. Current candidate file-tier reads were 28.97-38.56 GiB-equivalent MB values, versus prior 2.70-10.08 GiB-equivalent MB values; this explains the observed direction of the slowdown, but the between-campaign cause is not isolated. The paired causal-fix versus promoted-control result is still positive in every pair.

PROMOTION_STATUS: NOT_DEPLOYED
BLOCKER: The plan requires an atomic source+binary+settings promotion with rollback. The candidate source is a detached run checkout whose origin is Niko1221/Strata, while the canonical main worktree is e26d5538; no safe canonical promotion target or rollback manifest was established in this cycle. Candidate binary and raw evidence are preserved; no active runtime was overwritten.
NEXT_STEP: Explicitly identify the authorized atomic promotion target and rollback artifact, then commit/deploy the exact source patch and re-verify the resulting binary identity.
<!-- LUNA_PUBLISHED_TASK_ID: LUNA-20261012-026 -->
