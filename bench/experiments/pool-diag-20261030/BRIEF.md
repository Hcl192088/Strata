# Codex brief: POOL_INTERNALS_AND_UNTIMED_DIAG (Strata, LUNA-20261012-027 continuation, REPORT_LOCAL)

User authorized (2026-10-30): build a timing-only DIAG binary from the current-best source in an isolated worktree, stop the live API for one short diagnostic run, restore the API. NOT authorized: deployment, changing live config/tasks permanently, modifying existing worktrees/canonical source, pushing, GitHub publication, changing sampling.

## Rules (same as your earlier runs today: see D:\strata\state\nt1ext-ab-20261030\ and gpu6-ab-20261030\ for working controller/launch/preflight scripts — reuse them)
- Read D:\strata\AGENTS.md, remote C:\Users\User\Strata-Adrian-control\AGENTS.md first.
- SSH `ssh User@<desktop-tailscale-ip>` (DESKTOP-LKMLUPC), strict host key; remote shell cmd; scp scripts.
- Disconnect > 10 min continuous -> stop, run local `tailscale status`, report which side, stop.
- Full process gate (inventory to file, copied back) before build and before stop. Only the live API stack allowed. Live exe A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8, config 060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93, source f520bc5e9d31c93caeb296b059e3a3eaa16e493f (worktree C:\Users\User\native-pipe-generic-20261029). Mismatch/unknown process -> stop, don't kill. After building, check for leftover vctip.exe / mspdbsrv.exe from YOUR build (creation time during your build, parent gone) and stop only those before the process gate.
- Build: new worktree from f520bc5 (e.g. C:\Users\User\pooldiag-20261030, branch pooldiag-20261030), same build.cmd as A1E6 (runs\native-pipe-deploy-prep-20261029), BelowNormal, launched via Win32_Process.Create or a scheduled task so SSH disconnect doesn't kill it. Commit the patch locally only.

## Instrumentation (timing only; must not change computation)
Reuse existing DIAG machinery where possible: the 10/29 overnight work added CPU_PHASE_DECODE counters (pipeline_ms, GU/quant/down, join, LRU) and thread-own cacheline counters (see D:\strata\state\overnight-20261029\PIPELINE_NEXT.md, PIPELINE_GENERIC_RESULT.md, analyze_phase.py, analyze_pipeline.py; remote runs\native-pipeline-20261029 and its source/diag patch). Find that diag patch on the remote and port/extend it onto f520bc5 rather than writing from scratch. Everything behind one env switch (e.g. STRATA_POOL_DIAG=1); with it unset the binary must behave identically.
Add, decode-only (exclude prefill), aggregated per window and per layer type:
1. Pool internals for each pool call: host dispatch timestamp; each worker's first-task start, busy time split into GU / quant / down, idle/spin-wait time, last-task end; record P-group vs E-group separately (worker->LP mapping is known); host time waiting for pool completion; completion skew (last worker end - first worker end); time the host spent waiting on GPU while the pool ran (overlap).
2. Decode loop parts currently untimed in the engine's timing line: suffix/lookup draft, apply_pending (adaptive swap), commit and its sub-steps, post-window bookkeeping, plus "remaining unattributed" so that the sum equals ms/window.
Use steady_clock/QPC, per-thread counters on separate cache lines, no allocation or I/O inside timed regions, print one summary line per request (and per-window raw rows to a separate file if cheap).

## Run
- Run dir runs\pooldiag-20261030 (no reuse of old dirs). Arms: C = current best A1E6 (no diag env); D = DIAG binary with STRATA_POOL_DIAG=1. Order C, D, C, D (2 rounds); each block = Hermes p01, p05, p08 x 512 tokens, original sampling (c.make_body). Fresh engine per block, c.gate before each block, capacity 3153/20.00 GiB/20479 MiB, AboveNormal, MT1=1, PIPE=1, MT_MIN absent; config diffs allowed only exe/cwd/log/STRATA_POOL_DIAG.
- Scheduled task priority 2 (read back), same principal as the API task, PT2H; disable afterwards. finally: restore API (ns.restore_api) + c.verify. Then independent post-run verification (single strata.exe A1E6/060F, AboveNormal, loaded, 3153/20479, idle, no leftovers).
- Stop rules: build/identity/gate failure -> stop. No extra prompts or rounds.

## Report: D:\strata\state\pool-diag-20261030\RESULT.md (+ raw summaries, patch, analysis script)
- D vs C ms/window and tok/s (perturbation %; >5% = timing perturbation large, numbers relative only).
- Pool table (ms/window): dispatch latency, GU/quant/down busy (P vs E, per worker avg), idle/spin, skew, host wait, overlap with GPU wait.
- Decode-loop table: draft(MTP), suffix/lookup, apply_pending, commit sub-steps, post-window, unattributed; conservation error vs ms/window (>10% = no conclusion).
- A short list of any concrete exposed cost >= 1 ms/window that looks removable without changing computation, with evidence; or say none.
- Deviations, restore verification. No deployment, no speed claim beyond the diagnostic.

## Attempt 2 (continuation)
Attempt 1 stopped after preflight with STATUS PARTIAL (report kept as RESULT.attempt1-partial.md): it located the old instrumentation at remote runs\native-pipeline-20261029\patched (generate.cpp, pool.cpp, pool.hpp) and runs\native-pipeline-roles-20261029\patched, but did not implement anything. This is not a blocker. Continue now and carry the task through to the end in this session: create the worktree, port/extend the timing patch (diff the old patched files against their base to extract only the timing code), build, quick sanity run of the DIAG binary is part of the C/D run itself, then the C,D,C,D run with restore and verification, then the report. Re-run fresh gates; do not reuse attempt-1 preflight. Only stop early for a real failure (build error you cannot fix within the timing-only scope after 2 attempts, identity mismatch, unknown process, SSH down > 10 min) and report it precisely. Keep the patch timing-only; if a requested counter is hard to add cleanly, skip that counter and list it as not measured rather than stopping.

## Attempt 3 (continuation)
Attempt 2 stopped because YOUR OWN SSH command had a PowerShell quoting bug (CommandNotFoundException) — that is a tooling error, NOT a gate failure. Gate failure means the gate ran and found an unknown process or an identity mismatch. When your own command or script errors, fix it and re-run; do not stop. Use the working scripts from today's runs: D:\strata\state\nt1ext-ab-20261030\inventory.ps1 and preflight.py (scp them and run with `powershell -NoProfile -ExecutionPolicy Bypass -File ...`), never inline nested PowerShell. Then carry the task through to the end as described in Attempt 2.
