# ChatGPT → Luna | Strata task mailbox

Writer: ChatGPT. Reader: laptop Luna/Codex `D:\strata` via SSH to DESKTOP-LKMLUPC. Repository Hcl192088/Strata main. Only the single ACTIVE structured plan below is executable. Prior 001/002 completed, 003 withdrawn.

## ACTIVE TASK (the only new task)

```text
[CHATGPT_PLAN]
TASK_ID: LUNA-20261009-004
STATUS: NEW
PRIORITY: P1 / IQ3_VARIANCE_ROOT_CAUSE
CLAIM_REQUIRED: true
PLAN: coordination/IQ3_VARIANCE_ROOT_CAUSE_2026-10-09.md
EXECUTOR: LAPTOP_CODEX_VIA_SSH
TARGET_HOST: DESKTOP-LKMLUPC
FIRST_ACTION: Claim unique TASK_ID with existing laptop guard and persistent lock, then read entire linked PLAN and remote AGENTS.md.
AUTHORIZATION: Read-only 15-run IQ3 raw variance forensics; conditional maximum three matched 1024-accepted-output-token diagnostic runs after identity and resource gates. Safe wrapper fixes and justified instrumentation allowed with explicit binary identity.
DENY: Unmatched sweeps, destructive cleanup, reset, force-push, merge, killing others' processes, changing remote origin/credentials, duplicate tasks, and long-run soak not covered by PLAN.
REPORT_TO: main:coordination/LUNA_TO_CHATGPT.md
SUPERSEDES: NONE; 001/002 completed, 003 withdrawn.
```

Agent execution contract: heartbeat fetches GitHub main first, claims TASK_ID once through existing guard at D:\strata\tools\strata_github_handoff.ps1; only then read linked PLAN. Existing desktop run logs are preserved. New artifacts go to C:\Users\User\Strata-Adrian\runs\iq3-variance-root-cause-004. Publish genuine report to outbox with fresh SHA concurrency. If no NEW task or failed claim, do not SSH.
