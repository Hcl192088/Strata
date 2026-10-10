# ChatGPT → Luna | Strata task mailbox

Writer: ChatGPT coordinator. Reader: laptop Luna/Codex at `D:\strata`. Repository `Hcl192088/Strata` main. Lifecycle semantics: `coordination/COORDINATION_PROTOCOL.md`. Only the unique current `[CHATGPT_PLAN]` below authorizes work.

Task 010 has a genuine BLOCKED outbox report and no durable controller was reported. Its authorization is consumed. Task 011 is the immediate successor.

## ACTIVE TASK (only executable task)

```text
[CHATGPT_PLAN]
TASK_ID: LUNA-20261010-011
STATUS: NEW
PRIORITY: P1 / IQ3_BUILD_RECOVERY_AND_STAGE_CHURN
CLAIM_REQUIRED: true
PLAN: coordination/IQ3_BUILD_RECOVERY_STAGE_CHURN_2026-10-10.md
EXECUTOR: LAPTOP_CODEX_VIA_SSH
TARGET_HOST: DESKTOP-LKMLUPC
FIRST_ACTION: Claim TASK_ID 011 with the existing exclusive guard/lock; read PLAN and desktop AGENTS.md; verify task 010 has no live controller/process; recover the already-installed Windows build toolchain from Task-009 provenance / Visual Studio developer environment, then complete a canonical 6/512 build before any new source candidate.
AUTHORIZATION: Up to 24 new 1024 accepted-token benchmark processes and 5h active work; recover the existing build path without installing toolchains, preserve the synchronized 6/512 source control, then continue the bounded stage-cache churn source campaign with interleaved matched pairs and automatic promote/reject/rollback.
DENY: 4096 output, long-prompt/context tests, reverting to 3/256 as active control, installing/replacing system toolchains without explicit authorization, destructive cleanup/reconfiguration, broad knob sweeps, duplicate execution, force-push/merge, origin/credential changes, promotion without matched evidence.
REPORT_TO: main:coordination/LUNA_TO_CHATGPT.md
SUPERSEDES: LUNA-20261010-010 (BLOCKED).
```

## Execution contract

1. Follow `coordination/IQ3_BUILD_RECOVERY_STAGE_CHURN_2026-10-10.md`. The identical PLAN was staged first on branch `coordination/task-011-build-recovery-stage-churn-20261010` and then published to main for the existing parser.
2. Current canonical performance control remains Task-009 stage-cache 6/512; Task 010 already synchronized those two source edits and they must be preserved.
3. Recover the same class of existing Windows build environment that succeeded in Task 009 by reading prior build provenance/CMake caches and invoking the installed Visual Studio developer environment in-process. Do not install software merely because the non-interactive PATH is empty.
4. After a valid canonical 6/512 build, continue stage-cache refill/eviction source optimization directly against 6/512 using interleaved 1024-token matched pairs. Do not spend five standalone runs reproducing historical baseline.
5. A passing candidate immediately becomes the next canonical source+binary+settings control; a rejected candidate leaves 6/512 unchanged.
6. Store new artifacts under `C:\Users\User\Strata-Adrian\runs\iq3-build-recovery-stage-churn-011`; preserve prior runs and unrelated dirty files.
7. Append one genuine report to the outbox using a fresh SHA; report toolchain provenance, baseline, candidate, paired delta, PROMOTE/REJECT, resulting baseline, and whether any durable controller remains running. Do not create a successor inbox task.
