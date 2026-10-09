# Strata coordination lifecycle protocol

This file defines coordinator-side task lifecycle semantics. It does **not** replace or modify the parser-visible fields inside `[CHATGPT_PLAN]`.

## Roles
- ChatGPT is the sole writer of `coordination/CHATGPT_TO_LUNA.md`.
- Luna/Codex reads the inbox, claims work through its existing local guard/lock, and writes genuine reports to `coordination/LUNA_TO_CHATGPT.md`.
- Luna does not edit the inbox to mark a task claimed, running, or finished.

## Meaning of inbox STATUS
Inside `[CHATGPT_PLAN]`, `STATUS: NEW` is an **authorization token**, not the authoritative runtime state.

The current task state must be resolved from both files:
1. Read current inbox and obtain TASK_ID.
2. Read the latest genuine outbox report for that same TASK_ID.
3. If no report exists, the task may still be NEW/claimed/running; do not duplicate it.
4. If the latest report for that TASK_ID has `STATUS: COMPLETED`, `STATUS: PARTIAL`, or `STATUS: BLOCKED`, that inbox authorization is **consumed** for coordinator purposes. Do not treat stale `STATUS: NEW` as an active task merely because ChatGPT has not rewritten the inbox yet.
5. Before publishing a successor, re-read both inbox/outbox and latest blob SHAs. Publish only one unique successor TASK_ID and explicitly set `SUPERSEDES` to the consumed task when relevant.
6. A `PARTIAL` or `BLOCKED` report means the reported execution stopped at that checkpoint unless the report explicitly states that a durable controller remains running. If a controller/process may still be running, do not issue a replacement until ownership/process state is resolved.
7. When a successor task is published, it becomes the only executable inbox task. Historical reports remain append-only in the outbox.

## Coordinator automation rule
Scheduled ChatGPT reviewers must compute effective state from **inbox + outbox**, never from inbox STATUS alone. They must:
- avoid duplicate TASK_ID or duplicate experiments;
- regard terminal outbox reports as consuming the corresponding inbox authorization;
- preserve one ACTIVE task at a time;
- use fresh GitHub SHA before writes and abandon the write on a race;
- keep benchmark identity at 1024 accepted output tokens unless the user explicitly changes it.

## Benchmark policy
Primary metric: accepted decode tok/s.
Default comparable identity: same binary/model/quant/prompt/context/runtime/settings with exactly 1024 accepted output tokens. Only the intended single experimental factor may vary in an A/B.
