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

## Continuous campaign chaining
A terminal report for one TASK_ID is **task completion**, not a reason for the Strata optimization program to idle.

When the latest genuine outbox report for the current TASK_ID is `COMPLETED`, `PARTIAL`, or `BLOCKED`, the ChatGPT coordinator must, in the **same review run**, do all of the following unless a true global stop rule applies:
1. consume that task authorization;
2. extract the measured result, rejection/promotion, unresolved bottleneck and recommended next hypothesis;
3. decide the highest-value next experiment or source-level intervention;
4. create its PLAN and publish exactly one successor TASK_ID immediately after re-reading fresh inbox/outbox SHAs.

Do **not** wait for the user, the next scheduled review, or a manually triggered conversation merely because the previous task finished. The machine should not become idle between normal campaign stages.

A true global stop is limited to: unsafe/unrecoverable execution state, exhausted explicit overall campaign budget, no remaining actionable hypothesis, or the user explicitly asks to stop. A candidate rejection, noisy result, one task reaching its local run limit, or a `PARTIAL` task report is **not** a global stop.

Successor tasks should be broad enough to carry multiple hypothesis → change → build → benchmark → promote/reject cycles autonomously. Do not fragment the work into a sequence of tiny knob checks when evidence supports a direct source-level or architectural intervention.

## Scheduler persistence rule
The Strata ChatGPT monitoring automations are persistent supervision infrastructure.

- The coordinator must **never disable, pause, delete, or otherwise turn off a Strata monitoring automation on its own**.
- Tool errors, GitHub write failures, race/conflict, stale inbox state, a completed task, a blocked task, or an inability to publish a successor are **not** reasons to disable the schedule.
- On such failures, leave the automation enabled, report the blocker when appropriate, and retry on the next scheduled execution according to the normal retry/race rules.
- Only an explicit user instruction to stop/disable/delete a specific Strata automation authorizes changing its enabled state to false or deleting it.
- Changes to cadence/prompt are allowed when needed, but must preserve enabled=true unless the user explicitly says otherwise.

## Benchmark policy
Primary metric: accepted decode tok/s.
Default comparable identity: same binary/model/quant/prompt/context/runtime/settings with exactly 1024 accepted output tokens. Only the intended single experimental factor may vary in an A/B.
