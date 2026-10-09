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
