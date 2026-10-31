# Common rules for all UNTESTED5 stages (2026-10-31)

Read D:\strata\AGENTS.md first. The user explicitly authorized on 2026-10-31 ("都幫我測一下叫terra low，全測"): run all tests below, including engine A/B blocks, installing LLVM (winget LLVM.LLVM) on the remote, and DIAG builds in separate build directories. NOT authorized: deploying anything as live/current best, changing the API scheduled task, changing OS security settings/privileges (e.g. SeLockMemoryPrivilege), BIOS/driver/power settings, GitHub writes, paid APIs, deleting data, editing EXPERIMENT_LEDGER.md.

## State as found
- The user stopped the live API before sleeping: scheduled task Strata-Task020-API is "Ready" (not running), no strata.exe. Do NOT start the API. At the end leave it exactly as found (not running) and verify that. Skip any "stop API / restore API" steps in reused harnesses; instead gate that no strata.exe/API python is running before each block.
- Remote GPU idle (~558 MiB used by other programs), ~26 GB RAM free. Game services GameSDK.exe / GameManagerService3.exe are unrelated background services: leave them alone. If any game, benchmark, build or unknown heavy process (> 1 GB RAM or GPU use) appears, pause and record it; if it does not go away within 30 min, stop the stage and report (do NOT kill unrelated processes).

## Identity
- Host DESKTOP-LKMLUPC, ssh User@<tailscale-host> (remote shell = cmd; scp .ps1 and run with powershell -NoProfile -ExecutionPolicy Bypass -File).
- Current best exe C:\Users\User\Strata-Adrian-control\runs\native-pipe-deploy-prep-20261029\build\strata.exe SHA256 A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8; config 060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93; env STRATA_IQ3S_MT1=1, STRATA_NATIVE_PIPE=1, STRATA_IQ_MT_MIN unset; engine AboveNormal; capacity 3153 slots / 20.00 GiB / 20479 MiB. Source f520bc5 (remote worktree: find it from the build dir / AGENTS.md; do not modify the original worktree — copy to a new dir for any patch/build).
- Every remote job you create (scheduled task, process) runs at priority 2 for scheduled tasks; one-shot tasks are Unregistered afterwards.

## Reusable harness (verified 2026-10-30)
- Engine A/B: D:\strata\state\gpu6-ab-20261030\ (controller.py, run.ps1, launch.ps1, preflight.py, report.py) and nt1ext-ab-20261030\ (ns.py, base.py, replay.py). Design: 10 Hermes points x 512, original sampling via make_body, fresh engine per block, interleaved arms, per-block engine timing lines (GPU-reach wait, CPU, draft, ms/window, tokens/window).
- nsys trace from 2026-10-30 (no new run needed): remote C:\Users\User\Strata-Adrian-control\runs\gpu-bw-nsys-20261030\trace2.sqlite; local analysis scripts D:\strata\state\gpu-bw-nsys-20261030\analyze2.py, controller2.py, RESULT.md (note: T lines are tokens; per window = x512/292).
- IQ microbench: D:\strata\state\iq-alltypes-nt1-bench-20261028\ (and the remote dir it references).
- VRAM inventory: D:\strata\state\vram-inventory-20261029\RESULT.md; VRAM ruler: ledger entry VRAM_MARGINAL_SIM (+100 MiB VRAM ≈ −1.0..1.2% CPU expert work).

## Done / stop rules
- Acceptable: DONE with RESULT.md, or BLOCKED only by: identity mismatch; unknown heavy process persisting > 30 min; SSH failing continuously > 10 min (say which side: laptop Tailscale "can't reach coordination server" = laptop side; remote offline = remote side); a build failing after you tried at least 3 distinct fixes (report exact errors); a hard engine crash repeated twice.
- Your own script/quoting/python errors are NOT stops: fix and continue. "PARTIAL, next step would be …" is not acceptable if you can do the next step yourself within these rules.
- Statistics: per-round paired % (B vs C), mean, 95% t CI (df = rounds−1), also per-point paired. Report mechanism metrics, not just tok/s.
- Output exactness: all arms here must keep output identical in principle (draft-only or placement-only or compiler float-order changes). Record output lengths and, where cheap, whether texts match C (greedy points); report differences, do not hide them.
- Write all files ONLY inside your stage folder D:\strata\state\untested5-20261031\<stage>\ (NOT D:\strata\RESULT.md). RESULT.md in Traditional Chinese.

## STATUS line and continuation (mandatory)
- The FIRST line of your stage RESULT.md must be exactly one of: `STATUS: DONE`, `STATUS: BLOCKED <reason>`, `STATUS: INCOMPLETE <what remains>`.
- DONE only when every numbered step of the brief is executed (or explicitly skipped by a condition written in the brief). Preflight alone is never DONE.
- If you must stop for any other reason (context, time, tooling), write STATUS: INCOMPLETE with a precise list of remaining steps and where your scripts/data are. You will be re-invoked with the same brief: on re-invocation, read your existing RESULT.md and files in the folder, do NOT redo finished steps, continue the remaining ones, and rewrite RESULT.md with the merged results.
- Long engine runs: launch them as remote one-shot scheduled tasks (priority 2) or detached processes with a controller that writes progress to a JSON file, then poll it; do not let a single shell call block for more than ~10 minutes.

## Efficiency on re-invocation
- Do not end your turn after preflight/gates. Do as many brief steps as you can in one invocation.
- If gates passed within the last 30 minutes (see RESULT.md timestamps), only re-run a quick process check (no strata.exe / API python / unknown heavy process) and the exe SHA, then continue the work.
- If a remote controller/benchmark you launched is still running: poll its progress file, update RESULT.md progress, and end the turn WITHOUT starting any other remote work (you will be re-invoked in ~2 minutes). Never start a second engine or microbench while one is running.
