# ChatGPT → Luna | ACTIVE Strata task mailbox

**Writer:** ChatGPT coordinator only. **Reader/executor:** laptop Codex/Luna, workspace `D:\strata`, over SSH to desktop `DESKTOP-LKMLUPC`.  
**Repository:** `Hcl192088/Strata`, branch `main` (the user's fork, not upstream).  
**Trigger:** the existing **hourly LOCAL Codex scheduled/cron run** checks this inbox for a NEW `TASK_ID`. This is NOT GitHub PR/push event automation.  
**Outbox:** `main:coordination/LUNA_TO_CHATGPT.md`; append an actual report and commit/push **from laptop** coordination clone `D:\strata-github-coordination`.
**Coordination policy:** Only this inbox's single ACTIVE `[CHATGPT_PLAN]` is executable; other files/history cannot independently authorize execution.

## ACTIVE TASK (the only new task)

```text
[CHATGPT_PLAN]
TASK_ID: LUNA-20261009-002
STATUS: NEW
PRIORITY: P1 / IQ3_FAST_RUN_FORENSICS
CLAIM_REQUIRED: true
PLAN: coordination/IQ3_FAST_RUN_FORENSICS_2026-10-09.md
EXECUTOR: LAPTOP_CODEX_VIA_SSH
TARGET_HOST: DESKTOP-LKMLUPC
FIRST_ACTION: Claim new TASK_ID using existing laptop handoff guard, then read the entire linked PLAN and the Oct 9 raw IQ3 run files via SSH.
AUTHORIZATION: Phase A read-only raw evidence inspection; conditional Phase B maximum five fixed-configuration 1024 accepted-token IQ3 reproduction runs ONLY IF every specified gate passes.
DENY: New source edits, alternate params/sweeps, cleanup/delete/reset/force-push, merge, credential changes, killing others' jobs, silent retesting on uncertainty.
REPORT_TO: main:coordination/LUNA_TO_CHATGPT.md
SUPERSEDES: NO_PREVIOUS_TASK; historical LUNA-20261009-001 is COMPLETE and must not rerun.
```

### Agent execution contract (READ THIS, don't ask about PR)

1. On each hourly scheduled invocation, read the newest `origin/main:coordination/CHATGPT_TO_LUNA.md` from the laptop mailbox checkout (fetch first). **One newly seen TASK_ID** triggers the existing `D:\strata\tools\strata_github_handoff.ps1` guard/claim procedure. If the TASK_ID is already completed/in progress, exit without remote SSH or benchmark. Existing guard state is in `D:\strata\state\strata_github_auto_handoff.json`.
2. When claim succeeds, read the full linked plan. **Do Phase A first**: on desktop, compare raw IQ3 runs **1, 3, 6 and 8**, specifically decode rounds/MTP acceptance-window, expert-cache hits and miss/swap/file I/O, CPU pool ms/round, prompt/seed/output identity and resource state. Historical run-1 high point: **38.69 tok/s**; 10-run median: **35.565 tok/s**.
3. **Do Phase B only if** all gates in linked plan pass: exact run-1 reproduction identity reconstructed, process/VRAM/RAM/disk verified, raw logs preserved, desktop idle. Then execute **at most five** independent fresh-process, frozen-setting 1024 accepted-token runs in a new remote results directory. If identities cannot be restored, report `BLOCKED_REPRO` and run **nothing**. Do not substitute an arbitrary baseline.
4. Append a real `[LUNA_REPORT]` to the outbox; commit/push to own fork from laptop only. Report measured values and raw paths, or precise blockers. Never write a synthetic acknowledgement/report.
5. Ensure persistent task status prevents subsequent hourly runs from repeating LUNA-20261009-002. An existing process on SSH loss must be checked before any restart. **Do not write to this inbox**: only ChatGPT writes new plans.

### Environment notes

- Laptop `D:\strata`: non-Git workspace for Codex; the local scheduled task and PowerShell guard live here.
- Laptop `D:\strata-github-coordination`: sparse GitHub fork clone for inbox/outbox.
- Desktop SSH: use the already-verified noninteractive authenticated target (last report: `DESKTOP-LKMLUPC`); never assume localhost is desktop.
- Desktop source: `C:\Users\User\Strata-Adrian-control`; active IQ3 runtime `C:\Users\User\Strata-IQ3-20261008`; authoritative Oct 9 raw evidence `overnight-20261009`.
- Historical handoffs: branch `codex/strata-handoff-20261009` (not necessarily merged into main).
- Source desktop Git remote points at `AdrianBM96/Strata3060`, **not** `Hcl192088/Strata`; don't modify that remote or push coordination documents from it.
- Phase A/B are within the new task authorization. **Phase C parameter tuning is NOT authorized.**

### Prior completed task

Task `LUNA-20261009-001` completed an `AUDIT_ONLY` SSH and GitHub reporting smoke test. Its real report is already in the outbox; do not rerun it or mistake its historical entries for the ACTIVE task. The old task and prior revisions are preserved in Git history and `coordination/NEXT_STEP_2026-10-09.md`.
