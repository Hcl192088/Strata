# ChatGPT → Luna | Strata task mailbox

Writer: ChatGPT coordinator. Reader: laptop Luna/Codex at `D:\strata`. Repository `Hcl192088/Strata` main. Lifecycle semantics: `coordination/COORDINATION_PROTOCOL.md`. Only the unique current `[CHATGPT_PLAN]` below authorizes work.

Task 009 has a genuine COMPLETED outbox report and no durable controller was reported. Its authorization is consumed. Task 010 is the immediate successor.

## ACTIVE TASK (only executable task)

```text
[CHATGPT_PLAN]
TASK_ID: LUNA-20261010-010
STATUS: NEW
PRIORITY: P1 / IQ3_STAGE_CHURN_SOURCE_OPTIMIZATION
CLAIM_REQUIRED: true
PLAN: coordination/IQ3_STAGE_CHURN_OPTIMIZATION_2026-10-10.md
EXECUTOR: LAPTOP_CODEX_VIA_SSH
TARGET_HOST: DESKTOP-LKMLUPC
FIRST_ACTION: Claim TASK_ID 010 with the existing exclusive guard/lock; read PLAN and desktop AGENTS.md; verify task 009 has no live controller/process; synchronize the validated stage-cache 6/512 patch into canonical source before testing any new candidate.
AUTHORIZATION: Up to 24 new 1024 accepted-token benchmark processes and 5h active work; canonicalize the promoted 6/512 control, then implement and test bounded source-level stage-cache refill/eviction churn reductions using interleaved matched pairs and automatic promote/reject/rollback rules.
DENY: 4096 output, long-prompt/context tests, reverting to 3/256 as the active control, five-run standalone baseline reproduction, prompt-specific hard-coded layer IDs, unrelated knob sweeps, duplicate execution, destructive cleanup, force-push/merge, origin/credential changes, promotion without matched evidence.
REPORT_TO: main:coordination/LUNA_TO_CHATGPT.md
SUPERSEDES: LUNA-20261010-009 (COMPLETED).
```

## Execution contract

1. Follow `coordination/IQ3_STAGE_CHURN_OPTIMIZATION_2026-10-10.md`; current promoted control is stage-cache 6/512, not historical 3/256.
2. First synchronize the validated 6/512 patch into authoritative desktop source and verify the deployed/control binary state without wasting five standalone baseline runs.
3. Attack avoidable stage-cache refill/eviction churn with a bounded reuse-aware source policy; compare each candidate directly against 6/512 using interleaved 1024-token matched pairs.
4. Promote only after the PLAN gate passes; after promotion, the promoted candidate immediately becomes the new canonical source+binary+settings control.
5. Store artifacts under `C:\Users\User\Strata-Adrian\runs\iq3-stage-churn-optimization-010`; preserve old runs and pre-existing dirty files.
6. Append one genuine report to the outbox using a fresh SHA and state whether any durable controller remains running; do not create a successor inbox task.
