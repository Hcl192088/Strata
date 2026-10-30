# Codex brief — POOL DIAG, attempt 4 (final). READ THIS FIRST; it overrides earlier attempt notes.

## What counts as done
The ONLY acceptable outcomes of this session:
(a) DONE: timing patch written, built, committed locally, C/D/C/D run finished, API restored and verified, RESULT.md with the tables; or
(b) BLOCKED by one of these real safety stops ONLY: identity/SHA mismatch, an unknown Strata/bench/build process in the gate, SSH down > 10 minutes, or a build error you could not fix after 3 genuine fix attempts.
A "PARTIAL / not yet implemented / needs extraction" report is NOT acceptable. Attempts 1–3 all ended that way without hitting any safety stop. Your own command/quoting/script/python-env errors are not stops: fix and continue. Uncertainty about how to add a counter is not a stop: add a simpler counter or mark that counter "not measured" and continue.

## State you start from (verified by attempt 3, re-gate before build and before stopping the API)
- Remote worktree C:\Users\User\pooldiag-20261030, branch pooldiag-20261030, at f520bc5, unmodified.
- Local copies of the old 10/29 instrumentation: D:\strata\state\pool-diag-20261030\before\{generate.cpp,pool.cpp,pool.hpp} and ...\patched\{generate.cpp,pool.cpp,pool.hpp}. diff them; that diff mixes pipeline logic with timing. You do NOT need to port it wholesale. Use it only as reference for counter style (thread-own cacheline counters, CPU_PHASE_DECODE print).
- The full original requirements are in BRIEF.md (same folder) sections "Instrumentation", "Run", "Report". Working scripts: D:\strata\state\nt1ext-ab-20261030\ (inventory.ps1, preflight.py, controller.py, launch.ps1) and gpu6-ab-20261030\. Remote venv python: C:\Users\User\Strata\archive\legacy\20261009\Strata-lm-run-2026-09-28\.venv\Scripts\python.exe.

## Minimal patch to write (timing only, behind env STRATA_POOL_DIAG=1; when unset, zero behaviour change)
Write it fresh in the worktree's src (find the files: pool.cpp/pool.hpp under src/kernels/cpu, and generate.cpp under the program dir):
1. pool.cpp — in the worker loop: per worker, on its own 64-byte-aligned struct, accumulate (QueryPerformanceCounter or steady_clock) busy time per task kind if the task kind is visible (GU / quant / down), else total busy; idle/spin time; first-start and last-end timestamps per pool call. In the host's wait-for-completion: accumulate host wait time. Expose a function to read+reset totals.
2. generate.cpp — in the decode loop, around the existing timing markers (search for the printf that prints the decode timing / ms per window; tw0..tw3 markers): add timers around the currently untimed parts: suffix/lookup draft, apply_pending, commit, post-window bookkeeping. At end of each request print ONE line starting with "POOL_DIAG" with per-window averages: pool calls, P-group busy, E-group busy (worker->LP mapping: workers on LP 12-15 are E-cores), idle, host wait, skew, plus the decode-loop parts and an "unattributed" = ms_window − sum.
Keep it small. Correctness of the numbers matters more than coverage.

## Then
Build (same build.cmd as A1E6; detached; BelowNormal), clean up only your own leftover vctip/mspdbsrv, gate, run C,D,C,D (Hermes p01,p05,p08 x512, original sampling, priority-2 task, finally restore), verify, write RESULT.md as specified in BRIEF.md. Commit the patch locally on branch pooldiag-20261030 (no push). Copy the patch and raw POOL_DIAG lines to D:\strata\state\pool-diag-20261030\.
