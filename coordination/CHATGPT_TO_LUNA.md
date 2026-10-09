# ChatGPT → Luna | Strata task mailbox

Writer: ChatGPT coordinator. Reader: laptop Luna/Codex at `D:\strata`. Repository `Hcl192088/Strata` main. Lifecycle semantics: `coordination/COORDINATION_PROTOCOL.md`. Only the unique current `[CHATGPT_PLAN]` below authorizes work.

Task 006 has a genuine COMPLETED outbox report and no durable controller was reported. Its authorization is consumed. Task 007 is the immediate successor.

## ACTIVE TASK (only executable task)

```text
[CHATGPT_PLAN]
TASK_ID: LUNA-20261009-007
STATUS: NEW
PRIORITY: P1 / IQ3_HOTPATH_SOURCE_OPTIMIZATION
CLAIM_REQUIRED: true
PLAN: coordination/IQ3_HOTPATH_OPTIMIZATION_2026-10-09.md
EXECUTOR: LAPTOP_CODEX_VIA_SSH
TARGET_HOST: DESKTOP-LKMLUPC
FIRST_ACTION: Claim TASK_ID 007 with the existing exclusive guard/lock, read the full current PLAN and desktop AGENTS.md, verify 006 has no live benchmark/controller, then analyze existing 002/005/006 raw evidence before launching a new benchmark.
AUTHORIZATION: Multi-stage 1024-token optimization campaign focused on explaining the 35.76->23.36 control regression and directly reducing CPU expert-pool latency/file-tier expert traffic. Do not repeat the worker8 sweep. Use runtime controls only when they directly test the measured mechanism; otherwise implement reversible isolated source-level expert fetch/cache/prefetch/scheduling changes, up to three sequential source candidates, with matched controls, build/benchmark/promote/reject and automatic continuation within <=24 new benchmark processes and <=4h active work.
DENY: 4096 output, long-prompt/context tests, arbitrary knob sweeps, duplicate/concurrent execution, destructive Git/data cleanup, force-push/merge, changing origin/credentials, promoting an unreproduced maximum, or stopping the whole campaign after one rejected/recoverable candidate.
REPORT_TO: main:coordination/LUNA_TO_CHATGPT.md
SUPERSEDES: LUNA-20261009-006 (COMPLETED; preserve all evidence and do not rerun 006).
```

## Execution contract

1. Benchmark identity remains exactly 1024 accepted output tokens with the frozen 28,912-token prompt/max_context 100000 and otherwise matched baseline identity except the single controlled candidate.
2. New artifacts go under `C:\Users\User\Strata-Adrian\runs\iq3-hotpath-optimization-007`. Preserve prior runs read-only and checkpoint/resume the same TASK_ID safely.
3. A rejected candidate, high variance, recoverable build/wrapper/path/SSH error, or completed local phase is not a global stop. Continue autonomously to the next highest-evidence hot-path hypothesis while safe budget remains.
4. Luna appends genuine progress/final evidence to the outbox using fresh blob SHA and does not create a successor inbox task.
