# Codex brief — GPU_KERNEL_BW_DIAG (Nsight Compute), 2026-10-30

Read D:\strata\AGENTS.md and D:\strata\tools\STRATA_GITHUB_AUTO_HANDOFF.md first (rules apply). The user explicitly authorized this run on 2026-10-30 ("兩個都做"): stop the live API, run a profiling-only diagnostic, restore the API. No source change, no build, no deploy, no GitHub write, no paid API, no hardware/driver/BIOS/OS setting change.

## What counts as done
ONLY acceptable outcomes:
(a) DONE: per-kernel table produced, API restored and independently verified, RESULT.md written; or
(b) BLOCKED by one of these real stops ONLY: binary/config SHA mismatch; an unknown Strata/bench/build/diagnostic process in the process gate; SSH failing continuously > 10 minutes (then say which side is down: laptop network / Tailscale "can't reach coordination server" = laptop side; remote offline = remote side); ncu not installed on the remote (do NOT download/install anything); ncu refuses with ERR_NVGPUCTRPERM even when run from an elevated (RunLevel Highest) one-shot task (that needs a user-side driver setting: report it).
A "PARTIAL / next step would be…" report is NOT acceptable. Your own command/quoting/script/python errors are not stops: fix and continue. If one metric is unavailable, drop it, mark "not measured", continue.

## Identity (check before stopping the API and again after restore)
- Host DESKTOP-LKMLUPC, ssh User@<desktop-tailscale-ip> (remote shell is cmd; scp .ps1 and run with powershell -NoProfile -ExecutionPolicy Bypass -File).
- Live exe C:\Users\User\Strata-Adrian-control\runs\native-pipe-deploy-prep-20261029\build\strata.exe SHA256 A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8; config SHA256 060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93. Live env MT1=1, PIPE=1, MT_MIN unset; AboveNormal; capacity 3153 slots / 20.00 GiB / 20479 MiB. Take the exact args/env from the live process command line + the existing API launcher, do not guess.
- Profile THIS exe with THESE args/env only.

## Working references (reuse, don't reinvent)
- D:\strata\state\nt1ext-ab-20261030\ and pool-diag-20261030\: inventory.ps1 (process gate), preflight.py, controller.py (stop API → run → finally restore API), launch.ps1 (priority-2 detached scheduled task), independent verify, disable task afterwards.
- D:\strata\state\nsys-timeline-20261027\ + LUNA-20261012-027.nsys-timeline-20261027.md: how a profiler-wrapped engine was run on this box: engine stdin from a FILE ("GEN 512 <prompt>" then "QUIT"), stdout to file polled every 50 ms for READY / T lines / DONE; runner must not block on the profiler process (use Popen/detached). Admin was needed for profiler counters: a one-shot scheduled task with RunLevel Highest, Unregistered by the wrapper afterwards (that is the diagnostic task only; never change the API task's run level).
- Precedent: under profiler injection VRAM drops and the engine came up with 3135 slots instead of 3153; the user accepted that for traced runs. Here: record the slot count, do not gate on it (per-kernel bandwidth is not affected by slot count). Use a short prompt (e.g. Hermes p01 text) so prefill is short.
- Remote venv python: C:\Users\User\Strata\archive\legacy\20261009\Strata-lm-run-2026-09-28\.venv\Scripts\python.exe.

## Steps
1. Process gate (PID, name, command line, purpose). Only the known API stack allowed. Also kill only your OWN leftovers if you create any.
2. Locate ncu: `where ncu`, C:\Program Files\NVIDIA Corporation\Nsight Compute*\ncu.exe, CUDA toolkit v12.1/v13.2 folders. Record version. No install.
3. Confirm /metrics live.state=idle, stop the API exactly like controller.py does. All remaining work inside try/finally that restores the API.
4. Run the engine under ncu, priority-2 task (elevated one-shot if needed for counters), e.g.:
   ncu --target-processes all --clock-control none --cache-control none --replay-mode kernel \
       --kernel-name regex:"mmvq|gr_up|gr_down|attn|q5_k|q6_k|gdn|router|topk" \
       --launch-skip <skip prefill+first windows> --launch-count 400 \
       --metrics gpu__time_duration.sum,dram__bytes_read.sum,dram__bytes_write.sum,dram__throughput.avg.pct_of_peak_sustained_elapsed,sm__throughput.avg.pct_of_peak_sustained_elapsed,launch__grid_size,launch__block_size \
       -o <run dir>\bw <strata.exe + live args>
   --clock-control none is REQUIRED (default locks base clock and distorts duration). Pick launch-skip so captured kernels are from decode windows (after prefill: use the stdout T lines / or skip by count after a first calibration run with --launch-count small; one calibration run is fine). Adjust the regex to the real kernel names you see (list them with a quick `ncu --list-sets`-free short capture or from 10/27 nsys analysis: native_mmvq_il, native_mmvq_multi, gr_up_multi, gr_down_staged, native_q5_k_mmvq, native_q6_k_mmvq, attn_chunk). If kernel replay fails for memory save/restore (VRAM nearly full), reduce metrics so one pass suffices (gpu__time_duration + dram__bytes_read/write), then retry.
5. Export: ncu --import bw.ncu-rep --csv --page raw > bw.csv. Stop engine (QUIT), finally restore API, verify (/metrics loaded, PID, exe SHA A1E6, config 060F, AboveNormal, 3153 slots, idle), disable/unregister your tasks, final process gate.
6. Analysis (python): group by kernel name; for each: count, total and mean duration (us), bytes read+write, achieved GB/s = bytes/duration, % of peak (RTX 4070 peak 504.2 GB/s; also report ncu's dram pct_of_peak), sm throughput %. Also per decode window estimate: kernel-time share. Duration-weighted achieved GB/s for: dense projections (mmvq family), HC (gr_*), attention, other.
7. Interpretation per pre-registered rule (ledger GPU_KERNEL_BW_DIAG): main kernels ≥80% peak → GPU kernel direction closed; ≤65% and their combined time ≥5 ms/window → kernel rewrite worth designing (upper bound ≈ time×(1−eff/0.85)). Note ncu serializes kernels; report single-kernel metrics only, not wall time.

## Report
D:\strata\state\gpu-bw-20261030\RESULT.md (Traditional Chinese): identity, ncu version, elevated or not, slot count under ncu, the per-kernel table, the family summary, the rule verdict, API restore evidence, any process actions. Copy bw.csv and your scripts into D:\strata\state\gpu-bw-20261030\. Do not edit EXPERIMENT_LEDGER.md (the coordinator does).
