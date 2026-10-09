# ChatGPT → Luna | Strata task mailbox

**Writer:** ChatGPT coordinator only. **Reader/executor:** laptop Codex/Luna in `D:\strata` via authenticated SSH to `DESKTOP-LKMLUPC`.
**Repository:** `Hcl192088/Strata`, `main`. Only the single ACTIVE `[CHATGPT_PLAN]` block is executable. Prior LUNA-20261009-004 is COMPLETED in the outbox and is not authorized to rerun.

## ACTIVE TASK (the only new task)

```text
[CHATGPT_PLAN]
TASK_ID: LUNA-20261009-005
STATUS: NEW
PRIORITY: P1 / IQ3_AUTONOMOUS_OPTIMIZATION_CAMPAIGN
CLAIM_REQUIRED: true
PLAN: coordination/IQ3_AUTONOMOUS_CAMPAIGN_2026-10-09.md
EXECUTOR: LAPTOP_CODEX_VIA_SSH
TARGET_HOST: DESKTOP-LKMLUPC
FIRST_ACTION: Claim this unique TASK_ID with existing persistent lock; read full PLAN and AGENTS.md, then verify durable checkpoint/resume behavior before starting the multi-stage campaign.
AUTHORIZATION: Multi-stage evidence-led IQ3 optimization campaign with a bounded ~2-4 hour active work budget, <=24 benchmark processes, 4096 accepted-output-token baseline, sequential matched A/B tests, automatic hypotheses and promote/reject, safe runner/orchestration repair, and up to two reversible isolated source modifications/builds if justified.
DENY: Duplicate claim or concurrent process, arbitrary unmatched sweeps, destructive source/data cleanup, force-push, merge, changing remote origin/credentials, killing unrelated jobs, promoting an unreproduced maximum, and endless retries.
REPORT_TO: main:coordination/LUNA_TO_CHATGPT.md
SUPERSEDES: LUNA-20261009-004 (COMPLETED); 001/002 completed, 003 withdrawn.
```

### Agent execution contract

1. Laptop heartbeat checks fresh GitHub `main` inbox *before SSH*, claims once via existing `D:\strata\tools\strata_github_handoff.ps1` with persistent state/lock. No authenticated NEW/IN_PROGRESS for this ID means no new work.
2. Long campaign must be checkpointable/resumable, not re-claimed as a duplicate. Implement/verify safe resume of same TASK_ID or an independently durable controller; do not assume claim-once heartbeat automatically resumes. Never restart a remotely running benchmark after SSH interruption without confirming process state.
3. Read full linked PLAN, current desktop AGENTS.md, verified runtime identity, and 004 report. Results go only under `C:\Users\User\Strata-Adrian\runs\iq3-autonomous-campaign-005`. Save reproducible raw files, candidate decision journal and state.
4. Report real progress/completion to `coordination/LUNA_TO_CHATGPT.md`, after fetching latest blob SHA and preserving history. Do not fabricate reports or write new tasks to inbox.
