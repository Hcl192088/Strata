# Luna → ChatGPT | Strata report outbox

**Writer:** Codex/Luna scheduled agent on the **laptop** only (reads the remote Strata PC via SSH). **Reader:** ChatGPT scheduled review.  
**Execution note:** `D:\\strata` on the laptop is not a Git checkout; use a separate authorized laptop coordination checkout to commit/push this outbox. Raw logs and actual benchmark data remain on the desktop.  
**State as of 2026-10-09:** No real Luna report received. This is an empty mailbox template, not a success acknowledgement.

## Acknowledgements and reports

<!-- Append only genuine remote-agent messages below. Never fabricate measurements or acknowledge tasks before Luna has actually read the inbox. -->

### Pending: LUNA-20261009-001
Expected first acknowledgement:

```text
[LUNA_ACK]
TASK_ID: LUNA-20261009-001
REMOTE_HOST:
TIME (Asia/Taipei):
EXECUTION_STATUS: RUNNING | BLOCKED
```

Expected report summary:

```text
[LUNA_REPORT]
TASK_ID: LUNA-20261009-001
STATUS: COMPLETED | PARTIAL | BLOCKED
TIME (Asia/Taipei):
HOST / WORKTREE / BRANCH / HEAD / DIRTY FILES:
BINARY SHA256; MODEL QUANT/PATHS; FULL BASELINE SETTINGS:
OVERNIGHT SOURCE LOG PATH / CONFIDENCE:
DECAY +35.03% DENOMINATOR:
SPEC6 24.18 TOK/S EXPLANATION:
PER-RUN ACCEPTED TOK/S / MEDIAN / PAIRED % DELTA:
MTP ACCEPTED/PROPOSED; GPU EXPERT HIT; VRAM/RAM:
ERRORS / VALIDITY / STOP REASONS:
RECOMMENDED NEXT TEST:
```

**Only data inserted by the remote Luna process count as an actual report.** Do not have the scheduled ChatGPT reviewer treat this template as a completed job.
