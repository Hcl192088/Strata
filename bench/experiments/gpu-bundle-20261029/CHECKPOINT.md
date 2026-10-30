Detached controller running remotely at C:\Users\User\Strata-Adrian-control\runs\gpu-bundle-20261029.
Task Strata-GPU-Bundle-20261029; started once at 13:53 2026-10-29.
Controller has finally restore original API task, no live config writes. Do NOT rerun launch/controller.
Monitor local remote.ps1 -ScriptPath poll.ps1 (PID/name/command inventory first).
After campaign DONE and wrapper.done: upload postprocess.py with fresh process gate, run collect.ps1; download evidence.zip + rows.json; extract raw, run analyze.py, qa.py, write_report.py.
Then re-read ledger and append results under GPU_EXACT_BUNDLE only. No push/source/build/GitHub writes.
