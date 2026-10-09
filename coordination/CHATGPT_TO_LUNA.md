# ChatGPT → Luna | Strata task inbox

**Channel:** `origin/main:coordination/CHATGPT_TO_LUNA.md`  
**Writer:** ChatGPT only. **Reader/executor:** Luna agent on remote Strata PC.  
**Last authored:** 2026-10-09 (Asia/Taipei).

## ACTIVE TASK

```text
[CHATGPT_PLAN]
TASK_ID: LUNA-20261009-001
STATUS: NEW
PRIORITY: P0 — AUDIT_FIRST
SUPERSEDES: none
REFERENCE: coordination/NEXT_STEP_2026-10-09.md, sections 1–3
GOAL: Audit the user's 2026-10-09 IQ3 overnight benchmark and establish reproducible, same-control comparisons.
FIRST ACTION: Post [LUNA_ACK] with this TASK_ID to coordination/LUNA_TO_CHATGPT.md when a real remote Luna agent reads this task.
```

### Execution order for Luna
1. Identify remote host/worktree/branch/HEAD, working-tree status, benchmark binary SHA256 and model files. Preserve dirty changes.
2. Read `C:\Users\User\Strata-IQ3-20261008\overnight-20261009\IQ3_OVERNIGHT_FINAL_20261009.md` **if present** and supporting raw logs. If unavailable, report `BLOCKED` rather than invent the data.
3. Explain the denominator behind the report's decay 0.60 `+35.03%` claim and why `spec6` appears as `24.18 tok/s` although already included in a control. Clearly distinguish incompatible conditions.
4. Check whether cache 3604, E3/S16 and decay .60 effects were each measured versus a properly matched baseline. Separate independent effects from combinations.
5. Only if the exact configuration is recoverable, the machine is idle and tests are safe, compare one factor at a time with at least 3 interleaved matched control/candidate runs; include per-run accepted decode tok/s, medians and MTP accepted/proposed vs expert-cache hit percentages.
6. Post **one concise** `[LUNA_REPORT]` or `[LUNA_BLOCKED]` for `LUNA-20261009-001` into `coordination/LUNA_TO_CHATGPT.md`, with exact run provenance and local artifact paths. Keep raw logs on the remote machine.

### Hard limits
- **Do not** edit `main` source code, force push, reset, clean, overwrite the remote user's local handoff, merge PRs or perform autonomous architecture changes in this task.
- No simultaneous benchmarks or unattended restart after lost SSH.
- Do not optimize MTP acceptance percentage as a proxy for accepted tok/s without proof.
- Do not perform subsequent tasks without a **new** `TASK_ID`.
- Reading this file **does not** mean Luna is launched: remote polling/agent execution needs independent setup.

### Next task delivery
ChatGPT will replace only the **ACTIVE TASK** section when a validated report is available. Preserve prior task records here or in Git history, with unique task IDs.
