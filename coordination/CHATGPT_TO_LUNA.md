# ChatGPT → Luna | Strata task inbox

**Writer:** ChatGPT coordinator only. **Reader/executor:** Codex/Luna running in **laptop** workspace `D:\strata`, controlling the **remote desktop** over SSH (the desktop does not need Codex to be installed).  
**Execution topology:** laptop `D:\strata` (not a Git repository) → SSH → desktop source `C:\Users\User\Strata-Adrian-control`, runtime `C:\Users\User\Strata-IQ3-20261008`. GitHub mailbox commits should be made from a separate, authorized coordination clone on the laptop; never assume GitHub push authentication works on the desktop.
**Current task authored:** 2026-10-09 (Asia/Taipei). **Task mode:** READ-ONLY audit; **no performance run yet**.

## ACTIVE TASK

```text
[CHATGPT_PLAN]
TASK_ID: LUNA-20261009-001
STATUS: NEW (revised after user's historical handoff upload)
PRIORITY: P0 / AUDIT_ONLY
SUPERSEDES: earlier wording of the SAME task LUNA-20261009-001; do not dispatch both revisions
PLAN: coordination/NEXT_STEP_2026-10-09.md on main
HISTORICAL_HANDOFF_BRANCH: codex/strata-handoff-20261009
HISTORICAL_HANDOFF_COMMIT: 685e52b328bf55091a8b9312407ad2b8d4daf21e
FIRST_ACTION: read uploaded 2026-10-09 handoff and workspace layout; acknowledge only after the real remote Luna agent reads this task.
SCOPE: audit and return evidence; no new benchmarks, source edits, deletes, archive moves, merges or force pushes.
```

### Historical files to read first (the branch is NOT yet merged into main)

1. `origin/codex/strata-handoff-20261009:.codex/handoffs/2026-10-09-002151-iq3-overnight-20261009.md`
2. `origin/codex/strata-handoff-20261009:docs/ops/STRATA_WORKSPACE_LAYOUT_20261009.md`
3. `origin/codex/strata-handoff-20261009:AGENTS.md`
4. `origin/codex/strata-handoff-20261009:.codex/handoffs/2026-10-08-001212-rtx4070-full-decode-benchmark-2026-10-08.md`
5. Read other 2026-10-07/06 handoffs on this branch to avoid repeating already falsified optimization ideas.

To read without merging, use an **isolated coordination checkout** and `git fetch origin main codex/strata-handoff-20261009` followed by `git show origin/codex/strata-handoff-20261009:<path>`. Do **not** switch, reset or clean the running benchmark worktree.

### Reconciled evidence from user's historical handoff (reported, not independently verified from raw logs)
- IQ3 SAFE_PRODUCTION: 10×1024 reported VALID; decode tok/s `38.69,36.46,31.31,36.41,32.68,37.12,34.58,31.61,34.72,36.52`; median **35.565**, mean **35.01**; zero reported crash/OOM.
- IQ3 chosen settings: expert cache `3604`, adaptive E3/S16, decay `0.60`, spec `6`, spec-min-p `0.75`, mtp-max-t `3`, 9 workers.
- `CACHE_ONLY vs FINAL_BUNDLE` identity check passed; A and B each `n=0` throughput results. **There is no valid A/B result.**
- The handoff describes an interim C: free-space reading about **3.34 GiB**, but also an archive cleanup and a later about **43 GiB** free. These observations are time-dependent; **check the current disk status read-only** before reaching any safety conclusion.
- Earlier 2026-10-08 47.76 tok/s median is from a different controlled benchmark series. Do not merge those samples or claim direct IQ3 uplift without matching quant/model and all inputs.
- The canonical remote **source repository** is `C:\Users\User\Strata-Adrian-control`; the **active IQ3 runtime** is `C:\Users\User\Strata-IQ3-20261008`. These are intentionally different. The IQ3 command still depends on IQ2 tokenizer/MTP runtime files and an older learned-heart profile; **do not delete/migrate them**.

### Required read-only audit steps
1. From the laptop, check passwordless noninteractive SSH first (`ssh -o BatchMode=yes -o ConnectTimeout=10 <configured-host> hostname`); do not change known_hosts or credentials unattended. If SSH is unavailable or sandbox network permissions block it, report BLOCKED. Then on the remote PC report git worktree/branch/HEAD/dirty state, whether the handoff branch has been fetched locally, free space of all volumes used by the effective IQ3 command, current Strata/llama processes and available RAM. Do not stop other users' jobs.
2. Read the local `overnight-20261009\IQ3_OVERNIGHT_FINAL_20261009.md`, `runner-state-corrected3.json`, `IQ3_BASELINE.json`, `AB_IDENTITY_CHECK.json`, `AB_STATS.json` and `IQ3_CACHE_ONLY_VS_FINAL_AB.md` if present. Check whether any source logs or results contradict the uploaded handoff.
3. Verify 10-run decode statistics from raw evidence, exact engine SHA, effective flags, resident, MTP draft-token acceptance vs GPU expert-cache hit; explain whether the `+35.03%` decay claim or `spec6=24.18` row was based on an incompatible control. State UNKNOWN if raw evidence is not accessible.
4. Confirm that the CACHE_ONLY and FINAL_BUNDLE comparison still has **zero valid throughput pairs**; if additional genuine runs were performed later, supply their hashes and raw paths.
5. Recommend the **single safest next measurement** and state its prerequisites (disk headroom, matched frozen config, idle machine, permissions). **Do not execute** it under TASK_ID LUNA-20261009-001.
6. From the **laptop** (the host running Codex), use a dedicated GitHub coordination checkout, separate from `D:\strata` and the remote source repo, to commit only a compact `[LUNA_ACK]` and then `[LUNA_REPORT]` or `[LUNA_BLOCKED]` into `coordination/LUNA_TO_CHATGPT.md` on `main`. Fetch the latest main before committing and do not overwrite concurrent ChatGPT writes. If push is blocked, preserve a local report and surface the blocker. If the coordinator clone does not yet exist or is unauthenticated, establish it manually before enabling unattended writes.

### Hard limits
- Do not run benchmarks under this task, change source/model/binary, clean/reset, delete old IQ2/v0.1.38 trees, force push, rewrite the user's historical branch or start a concurrent session.
- Do not assume the other branch is present when polling `main`. Fetch it explicitly or use GitHub to read it.
- The intended **laptop Codex desktop-app Scheduled Task** and its SSH permissions have **not** been installed or verified merely by this GitHub file. It requires the laptop to stay awake with the app running. The remote desktop runs Strata; it is not the scheduler host. The pending outbox template is not a real report.
- Later tasks require a **new unique TASK_ID**.

## Delivery history

- 2026-10-09: Task LUNA-20261009-001 initially issued as benchmark audit with conditional candidate runs.
- 2026-10-09: User uploaded five historical handoffs to `codex/strata-handoff-20261009`; task revised to **AUDIT_ONLY** before any additional benchmark.
