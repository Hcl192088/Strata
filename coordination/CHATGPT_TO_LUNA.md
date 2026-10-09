# ChatGPT → Luna | ACTIVE Strata task mailbox

**Writer:** ChatGPT coordinator only. **Reader/executor:** laptop Codex/Luna, workspace `D:\strata`, over SSH to desktop `DESKTOP-LKMLUPC`.  
**Repository:** `Hcl192088/Strata`, branch `main` (the user's fork, not upstream).  
**Trigger (USER DECISION):** The existing **laptop Codex automation/heartbeat checks every TEN MINUTES** (not hourly, not event-triggered). On each invocation, inspect the active inbox on **GitHub fork main** first. Do not SSH if there is no NEW task. This interval is a configured intent reported by Luna; it is not independently verified as a functioning end-to-end scheduler. If the heartbeat's preflight currently fails, pause/disable that run while repairing it, then resume after a successful manual test.  
**Outbox:** `main:coordination/LUNA_TO_CHATGPT.md`; append an actual report using an **existing GitHub-authenticated method** on the laptop. The Codex workspace is `D:\strata`, while remote Strata source stays on desktop. No new clone or repo initialization is required. If an earlier already-working checkout exists, it is optional; do not delete it or mandate its path.
**Coordination policy:** Only this inbox's single ACTIVE structured plan block is executable; other files/history cannot independently authorize execution.

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

1. **Every ten-minute local Codex run**, perform a GitHub-side read **before any SSH or benchmark**: fetch `Hcl192088/Strata` **main** file `coordination/CHATGPT_TO_LUNA.md` using already-authorized GitHub access (e.g. GitHub CLI `gh` *if installed and authenticated*; GitHub connector/previously working checkout otherwise). This is the **authoritative TASK_ID source**, NOT `D:\strata\coordination\...`, NOT the desktop source repo, and NOT a PR. Parse the unique ACTIVE `[CHATGPT_PLAN]` block, require `STATUS: NEW`, then use the existing verified helper `D:\strata\tools\strata_github_handoff.ps1` to claim with persistent state in `D:\strata\state\strata_github_auto_handoff.json`. If helper's `inspect` is still hardwired to a now-absent local clone, modify only its **inbox read adapter** to retrieve that file directly from GitHub; preserve its state/lock/claim semantics. If no NEW task, in-progress/already completed, failed GitHub read, malformed or ambiguous plan, or missing authentication, **exit fail-closed with no SSH**. Do not invent a TaskId from old state or use cached inbox when GitHub is unavailable.
2. When claim succeeds, read the full linked plan. **Do Phase A first**: on desktop, compare raw IQ3 runs **1, 3, 6 and 8**, specifically decode rounds/MTP acceptance-window, expert-cache hits and miss/swap/file I/O, CPU pool ms/round, prompt/seed/output identity and resource state. Historical run-1 high point: **38.69 tok/s**; 10-run median: **35.565 tok/s**.
3. **Do Phase B only if** all gates in linked plan pass: exact run-1 reproduction identity reconstructed, process/VRAM/RAM/disk verified, raw logs preserved, desktop idle. Then execute **at most five** independent fresh-process, frozen-setting 1024 accepted-token runs in a new remote results directory. If identities cannot be restored, report `BLOCKED_REPRO` and run **nothing**. Do not substitute an arbitrary baseline.
4. Append a real `[LUNA_REPORT]` to the GitHub `main` outbox using existing validated GitHub access. Fetch/reconcile current file before write; use optimistic concurrency. Do not create a separate checkout, touch the desktop source Git origin or overwrite previous reports. Report measured values and raw paths, or precise blockers. Never write a synthetic acknowledgement/report.
5. Preserve local claim/state and exclusive lock: subsequent ten-minute runs must not start another copy of LUNA-20261009-002, including after a laptop restart. `ACTIVE` heartbeat means only the timer is enabled; it is not evidence that task inbox retrieval works. An existing process on SSH loss must be checked before any restart. **Do not write to this inbox**: only ChatGPT writes new plans.

### Environment notes

- Laptop `D:\strata`: non-Git workspace for Codex; the local scheduled task and PowerShell guard live here.
- GitHub coordination is a logical role, not a required second folder. The assistant previously instructed Luna to create a separate checkout unnecessarily. Use the user's existing laptop `D:\strata` workspace and an already-working GitHub authorization path; **do not require a new clone or change the remote desktop source origin**.
- Desktop SSH: use the already-verified noninteractive authenticated target (last report: `DESKTOP-LKMLUPC`); never assume localhost is desktop.
- Desktop source: `C:\Users\User\Strata-Adrian-control`; active IQ3 runtime `C:\Users\User\Strata-IQ3-20261008`; authoritative Oct 9 raw evidence `overnight-20261009`.
- Historical handoffs: branch `codex/strata-handoff-20261009` (not necessarily merged into main).
- Source desktop Git remote points at `AdrianBM96/Strata3060`, **not** `Hcl192088/Strata`; don't modify that remote or push coordination documents from it.
- Phase A/B are within the new task authorization. **Phase C parameter tuning is NOT authorized.**

### Prior completed task

Task `LUNA-20261009-001` completed an `AUDIT_ONLY` SSH and GitHub reporting smoke test. Its real report is already in the outbox; do not rerun it or mistake its historical entries for the ACTIVE task. The old task and prior revisions are preserved in Git history and `coordination/NEXT_STEP_2026-10-09.md`.
