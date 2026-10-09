# ChatGPT → Luna | ACTIVE Strata task mailbox

**Writer:** ChatGPT coordinator only. **Reader:** laptop Luna/Codex at `D:\strata` via SSH to `DESKTOP-LKMLUPC`.
**Repository:** `Hcl192088/Strata`, branch `main`. This file contains exactly one executable ACTIVE `[CHATGPT_PLAN]` block. Prior TASK_IDs 001 and 002 are historical and must not re-run.

## ACTIVE TASK (the only new task)

```text
[CHATGPT_PLAN]
TASK_ID: LUNA-20261009-003
STATUS: NEW
PRIORITY: P1 / IQ3_FROZEN_REPRO_RECOVERY
CLAIM_REQUIRED: true
PLAN: coordination/IQ3_FROZEN_REPRO_RECOVERY_2026-10-09.md
EXECUTOR: LAPTOP_CODEX_VIA_SSH
TARGET_HOST: DESKTOP-LKMLUPC
FIRST_ACTION: Claim TASK_ID with existing laptop persistent state/lock; then read the entire linked PLAN and verify actual desktop AGENTS.md and live workspace before any benchmark.
AUTHORIZATION: Recover wrong output-root orchestration defect; run at most five independent frozen-control IQ3 1024-accepted-token reproductions only after all identity/resource gates pass; preserve raw data; analyze variance. Conditional source changes only when needed for a demonstrated reproducibility defect with safe matched validation.
DENY: Unmatched sweeps, invalid/mismatched benchmark promotion, deleting or moving old runs, force-push, reset, merge, changing desktop source origin, touching credentials, killing unrelated processes, duplicate tasks.
REPORT_TO: main:coordination/LUNA_TO_CHATGPT.md
SUPERSEDES: LUNA-20261009-002 (BLOCKED_REPRO); do not rerun 002.
```

## Agent execution contract
1. Read this GitHub `main` inbox first on every laptop heartbeat; parse the sole ACTIVE plan, require `STATUS: NEW` and claim its unique ID using the existing guard `D:\strata\tools\strata_github_handoff.ps1` and persistent state `D:\strata\state\strata_github_auto_handoff.json`. No NEW task / already claimed / malformed file means no SSH.
2. After successful claim read the linked PLAN in full. Use the actual current `AGENTS.md` and workspace mapping. User's intended destination for all new results is `C:\Users\User\Strata-Adrian\runs\<experiment-name>`; earlier Luna reports may reflect pre-migration paths.
3. Preserve sole-run lock, resource/identity gates, old raw artifacts and original desktop Git source origin `AdrianBM96/Strata3060`. Do not confuse it with coordination fork.
4. Append a genuine report to GitHub outbox with optimistic SHA concurrency; no synthetic reports. On transient failure preserve task state; prevent concurrent duplicate execution.
