# ChatGPT → Luna | Strata task mailbox

Writer: ChatGPT coordinator. Reader: laptop Luna/Codex at `D:\strata`. Repository `Hcl192088/Strata` main. Lifecycle semantics: `coordination/COORDINATION_PROTOCOL.md`; `STATUS: NEW` is authorization, not authoritative runtime state. Only the unique current `[CHATGPT_PLAN]` below authorizes work. Prior 005 reported PARTIAL, host state stopped with no residual process; 006 supersedes 005 for **continuation**, not duplicate execution. Agent must independently confirm no old workload still running before 006 executes.

## ACTIVE TASK (only executable task)

```text
[CHATGPT_PLAN]
TASK_ID: LUNA-20261009-006
STATUS: NEW
PRIORITY: P1 / IQ3_1024_VARIANCE_RECOVERY_CONTINUATION
CLAIM_REQUIRED: true
PLAN: coordination/IQ3_VARIANCE_CONTINUATION_2026-10-09.md
EXECUTOR: LAPTOP_CODEX_VIA_SSH
TARGET_HOST: DESKTOP-LKMLUPC
FIRST_ACTION: Claim unique TASK_ID via existing laptop state/lock; read entire linked PLAN and desktop AGENTS.md; confirm no 005 or other remote benchmark/controller process before resuming experiments.
AUTHORIZATION: Continue IQ3 optimization with exactly 1024 accepted output tokens and matched frozen 28912-token prompt identity. Investigate and automatically recover normal 9-worker runtime/I/O variance; validate 8 vs 9 with up to 5 fresh pairs and proceed to justified one-factor CPU/expert-file-tier/cache tests and reversible source optimization within <=20 new benchmarks and <=4h budget.
DENY: Repeat completed 005 stages, 4096 output tests, extra long-context/input tests, duplicate claim, concurrent benchmark, unpaired promotion driven by anomalous slow control, destructive cleanup/force-push/merge, changing remote origin/credentials, and infinite retries.
REPORT_TO: main:coordination/LUNA_TO_CHATGPT.md
SUPERSEDES: LUNA-20261009-005 (PARTIAL and stopped at final checkpoint; preserve all raw files and do not reclaim 005).
```

## Execution contract

1. Read this GitHub main inbox and full current PLAN before any SSH; use existing laptop claim/guard and durable exclusive lock. Only TASK_ID 006 can be claimed and resumed. Do not start 006 if previous work may still be active.
2. Source/runtime identity and original benchmark artifacts remain unchanged. New output under `C:\Users\User\Strata-Adrian\runs\iq3-variance-continuation-006`. Recoverable test noise triggers next diagnostic stage, **not termination**; no user intervention for ordinary retry.
3. Preserve complete raw evidence and per-stage state. Outbox reports must be genuine, appended with latest blob SHA. If guard detects race, defer instead of duplicate work.
