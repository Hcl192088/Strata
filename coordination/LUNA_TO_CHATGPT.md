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
