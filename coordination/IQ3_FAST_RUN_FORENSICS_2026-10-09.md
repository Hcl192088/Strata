# IQ3 Fast-Run Forensics & Reproduction — Task LUNA-20261009-002

**Task ID:** LUNA-20261009-002  
**Owner:** ChatGPT coordinator  
**Executor:** Luna/Codex on laptop `D:\strata` via SSH to desktop `DESKTOP-LKMLUPC`  
**Task status:** NEW / CLAIM_REQUIRED  
**Authorized:** Phase A read-only forensic investigation, then **at most five** controlled IQ3 1024-accepted-token reproduction runs in Phase B if every go/no-go gate below passes.  
**NOT authorized:** source/binary/model edits, new parameter sweeps, optimizer promotion, unsafe cleanup, remote source Git changes, force-push, merge, deletion, or any Phase C tuning.

## 0. Why this experiment comes before more tuning

The existing IQ3 SAFE_PRODUCTION overnight soak reports 10 valid, independent 1024-accepted-token decode runs:

`38.69, 36.46, 31.31, 36.41, 32.68, 37.12, 34.58, 31.61, 34.72, 36.52` tok/s.

Reported mean = **35.01 tok/s**, median = **35.565 tok/s**, sample CV = **7.0793%**, max = **38.69**, min = **31.31**. No crash/OOM was reported. The maximum is ~8.8% above the median; it is a **single observed extreme**, not yet a sustainable improvement.

The same IQ3 run summary reports aggregate GPU expert hit `0.61645` and MTP acceptance `73.0478%`. **These are aggregate statistics, not per-run 38.69 measurements.** Do not attribute the fast run to them before recovering per-run evidence.

A different **Oct 8 experiment** observed 53.77 tok/s with ~520 rounds versus slower ~615/627-round runs, apparently related to MTP acceptance/window. This is a hypothesis generator only; it is **not IQ3 evidence**. Do not pool Oct 8/Oct 9 results.

The prior `CACHE_ONLY vs FINAL_BUNDLE` A/B check had identity success but **A.n=0 and B.n=0** and must not be presented as a performance comparison.

**Question:** Why did IQ3 run 1 reach 38.69, and can the same frozen input/configuration repeatedly approach that speed without sacrificing correctness?

## 1. Topology and source-of-truth

- Laptop Codex application/workspace: `D:\strata` (**not** a Git repository).
- Laptop GitHub mailbox clone: `D:\strata-github-coordination` (owner fork `Hcl192088/Strata`), not the remote source repo.
- Desktop accessed through already-proven **noninteractive SSH** using the configured IP/identity. Expected hostname: `DESKTOP-LKMLUPC`. Revalidate StrictHostKeyChecking/BatchMode and hostname; do not weaken SSH checks or change keys.
- Desktop source: `C:\Users\User\Strata-Adrian-control`; runtime: `C:\Users\User\Strata-IQ3-20261008`.
- Desktop historical overnight folder: `C:\Users\User\Strata-IQ3-20261008\overnight-20261009`.
- Historical handoff is on fork branch `codex/strata-handoff-20261009`, not necessarily on `main`.
- Main mailbox: `coordination/CHATGPT_TO_LUNA.md` → read; `coordination/LUNA_TO_CHATGPT.md` → append real result and push.
- Desktop remote source Git origin `AdrianBM96/Strata3060` is intentionally not the mailbox fork: **do not change origin or push from the desktop source**.

Before executing, read remote `AGENTS.md`, the historical Oct 9 IQ3 handoff, and the existing frozen baseline/state; do not guess test commands from this Markdown.

## 2. Phase A — READ-ONLY raw-run forensics (MANDATORY FIRST)

A1. Use the laptop guard helper (`D:\strata\tools\strata_github_handoff.ps1`) and its persistent state to claim this exact new TASK_ID **once**. Maintain exclusive lock: no overlapping executions. Do not mark it COMPLETED before reporting.

A2. Via SSH, verify hostname and check remote Strata/llama/benchmark processes, GPU utilization/memory, available physical RAM and free space on all drives touched by IQ3. Preserve all unrelated jobs. Verify source branch/HEAD/dirty/untracked state read-only.

A3. Read (read-only) these *existing remote* items:
- `IQ3_OVERNIGHT_FINAL_20261009.md`
- `runner-state-corrected3.json`
- `IQ3_BASELINE.json`
- `iq3_overnight_runner.py`
- relevant `phase9-soak` raw per-run command, stdout, stderr, result/metrics, GPU snapshots and original prompt/token artifacts
- `AB_IDENTITY_CHECK.json`, `AB_STATS.json` only to ensure they remain invalid as speed evidence.

A4. For **runs 1, 3, 6 and 8**, create a forensic comparison table with, wherever actually recorded:
- decode accepted tok/s, actual accepted-token count and decode time; number of decode/model rounds; accepted tokens per round;
- speculative MTP draft proposed/accepted/rejected, acceptance rate and accepted-length/window histogram; distinguish final accepted output tokens from speculative draft tokens;
- GPU expert-cache hit, misses, swaps, experts fetched, file-tier read bytes/I/O time;
- CPU pool ms/round and CPU scheduling, GPU utilization/VRAM, resident RAM, memory headroom;
- input prompt hash and token count, sampling seed, output token hash and length, exact command args/env and benchmark runner version;
- process start-up/warm/cold state and whether the test order may be confounded with warm-up.

A5. Identify exact authoritative binary SHA256, pack/native/PLE-GGUF paths, model quant, tokenizer/MTP runtime, learned-heart profile dependencies, context/KV, expert-cache/adaptive E3/S16/decay0.60, spec6/spec-min-p0.75/mtp-max-t3, pool workers9, resident settings and all effective environment variables. An old IQ2 tokenizer/MTP or v0.1.38 profile path may still be a LIVE dependency. Do not delete/move it.

A6. Separate observations from inferences. Test these candidate explanations using within-IQ3-run evidence: (i) fewer decode rounds/higher MTP accepted per round, (ii) better expert-cache hit/fewer file loads, (iii) lower CPU pool cost, (iv) prompt/output differences, (v) transient hardware/OS/system state. Mark anything missing as `UNKNOWN`. Do not claim causation from correlation or the single maximum.

**Phase A output:** a compact table of run 1/3/6/8, raw file paths, authoritative run identity and a short ranked list of plausible causes. If run 1 or its exact command/input/seed/runner state cannot be reconstructed, report the missing items before deciding on a reproduction; never invent them.

## 3. Phase B — only if all gates pass: FIVE frozen-condition reproduction runs

**Gate B0** (ALL mandatory):
1. Phase A identifies the exact **run-1** effective command + environment, prompt/token input, sampling seed (or documented deterministic output mechanism), binary hash, model/quant, KV/context and dependency paths. Verify hashes and that artifacts still exist.
2. Runner itself is trustworthy: known 1024 **accepted** output token accounting, raw metrics capture, no stale cached result or mixing of prefill and decode; no hidden runner flags modified across runs.
3. Desktop hostname authenticated over SSH; the benchmark machine is idle (no conflicting experiment), and no unowned process is terminated.
4. Available disk capacity on the output drive is safely above expected log/runtime growth (at least **10 GiB free** as a conservative gate); sufficient RAM and **>=512 MiB GPU headroom** at the relevant startup phase with no OOM; verify actual memory readings rather than relying on historic numbers. If a run might load a different model or collide with another service, STOP.
5. A dedicated new output directory, e.g. `C:\Users\User\Strata-IQ3-20261008\fast-run-repro-20261009`, does not overwrite anything. Store all raw logs/config/command/exit/metrics there. No source tree, model, profile, tokenizer, binary, or previously captured experiment is modified.
6. Running is consistent with remote `AGENTS.md` and the user's no-destructive-operations rule. The scheduled job has usable SSH permissions and sufficient time to finish safely.

If **any** gate fails or exact replay identity cannot be recovered, **do not run a substitute benchmark**. Report `BLOCKED_REPRO` with precise missing evidence. In particular, a different seed, prompt, binary, quant, or tokenizer is a new condition, not a successful reproduction of 38.69.

If gates all pass:
- Use one frozen snapshot of the old run-1 inputs/settings; initiate **5 new independent fresh processes**, each targeting **1024 accepted tokens**. Do not change *any* performance variable between runs.
- Preserve per-run full command/env hash, prompt hash, seed, output-token hash, raw stdout/stderr, actual exit code, accepted token count, duration, first-token/prefill metrics, MTP accepted/proposed and rounds, GPU expert hit/swaps, CPU pool timings, file I/O, RAM/VRAM utilization. Classify invalid runs and do not silently replace them.
- Capture a consistent warm/cold protocol: record whether the original run was cold, use the same preflight/reset policy for all repetitions **without clearing OS caches or deleting files**, and distinguish any unavoidable differences.
- Compare the five-run median, range, CV and number of runs **>=38.0 tok/s** against historical IQ3 run-1 max 38.69 and soak median 35.565, explicitly as an observational comparison, not a contemporaneous randomized A/B. Calculate actual percentage deltas. If the output token hash is stable, measure speed variability of matched content; if output differs, quantify MTP and routing variability and say that exact output reproduction failed.
- On OOM, wrong binary/model, unexpected output, invalid token accounting, runner crash, resource contention or SSH failure of uncertain state: stop, preserve diagnostic logs, do not automatically retry or kill a still-running process.

Do **not** immediately begin `CACHE_ONLY vs FINAL_BUNDLE`, spec-min-p sweep, cache-size sweep, or any new optimization. Phase C requires a **separate** task and explicit authorization based on the forensic findings.

## 4. Reporting and GitHub publication

Append one genuinely executed task result to `main:coordination/LUNA_TO_CHATGPT.md` using the **laptop coordination clone only**. Preserve existing reports; fetch latest main and handle conflicts without force-push/reset. Do not write the ChatGPT inbox yourself.

Use exactly this machine-readable block **outside fenced examples**, with real values:

```text
[LUNA_REPORT]
TASK_ID: LUNA-20261009-002
STATUS: COMPLETED | PARTIAL | BLOCKED
PHASE_A: PASS | PARTIAL | BLOCKED
PHASE_B: PASS | SKIPPED | BLOCKED | PARTIAL
REMOTE_HOST:
REMOTE_SOURCE_HEAD:
RUNS_ANALYZED: 1,3,6,8
RAW_PATHS:
BINARY_SHA256:
MODEL_QUANT_AND_PATH_HASHES:
PROMPT_HASH / SEED / OUTPUT_HASH_PER_RUN:
RUN_1_3_6_8_COMPARISON:
MTP_ROUNDS_AND_ACCEPTANCE:
GPU_EXPERT_HIT_AND_SWAPS:
CPU_POOL_AND_FILE_IO:
REPRO_5_TOK_PER_SEC:
REPRO_MEDIAN_RANGE_CV:
REPRO_COUNT_GE_38:
REPRO_EXIT_1024_AND_RESOURCE_GATES:
KEY_FINDING_AND_UNCERTAINTY:
BLOCKER_IF_ANY:
RECOMMENDED_ONE_FACTOR_FOLLOWUP:
GITHUB_REPORT_COMMIT:
```

Treat this block as a **format specification**; never write synthetic data or claim Run now occurred when it did not. If scheduled work is cut off by its runtime limit, report `PARTIAL` with remaining state and **do not launch a second concurrent run**.

## 5. What counts as done

- Real raw evidence for run 1 vs runs 3/6/8 has been inspected and summarized, with unsupported fields marked UNKNOWN.
- Either FIVE authorized, valid frozen-condition runs have completed **with real raw artifacts**, or an explicit documented `BLOCKED_REPRO` prevents Phase B.
- Result published to user's fork from laptop; provide exact commit link.
- Local guard records task state and no duplicate execution occurs on subsequent cron invocations.

**Do not ask whether the intended trigger is PR or push. It is neither:** the already configured **hourly local Codex cron guard** reads the `main` mailbox for a new TASK_ID; this new task is `LUNA-20261009-002`.