# Codex brief — GPU_KERNEL_BW_DIAG via Nsight Systems GPU metrics, 2026-10-30

Read D:\strata\AGENTS.md first (rules apply). The user explicitly authorized THIS run on 2026-10-30 ("改用nsys"): stop the live API once, run a profiling-only diagnostic with nsys, restore the API. No source change, no build, no deploy, no GitHub write, no paid API, no driver/BIOS/OS setting change, no download/install.

## What counts as done
ONLY acceptable outcomes:
(a) DONE: bandwidth tables produced, API restored and independently verified, RESULT.md written; or
(b) BLOCKED by a real stop ONLY: binary/config SHA mismatch; unknown Strata/bench/build/diagnostic process in the process gate; SSH failing continuously > 10 min (say which side: laptop network/Tailscale "can't reach coordination server" = laptop; remote offline = remote); nsys reports GPU metrics unsupported/permission denied even when run elevated (report the exact message); the engine stalls/crashes under nsys twice with different settings (report both).
A "PARTIAL / next step would be…" report is NOT acceptable. Your own script/quoting/python errors are not stops: fix and continue. If the per-kernel alignment is hard, still deliver the whole-busy-period numbers and mark the rest "not measured".

## Lessons from the failed ncu attempt today (D:\strata\state\gpu-bw-20261030\RESULT.md, controller.py)
- Pass engine args as a proper list (attempt 1 broke a comma-separated token into a long prompt).
- The controller misjudged "engine still running" right after it exited and did not auto-restore: restore must be in finally and must wait/poll for the engine process to be gone (up to 60 s) before restarting the API; never leave the API down.
- Engine stdout/stderr to files; detect READY / T lines / DONE by polling; do not block on the profiler process.

## Identity (before stopping the API and after restore)
- Host DESKTOP-LKMLUPC, ssh User@<desktop-tailscale-ip> (remote cmd; scp .ps1, run with powershell -NoProfile -ExecutionPolicy Bypass -File).
- Exe C:\Users\User\Strata-Adrian-control\runs\native-pipe-deploy-prep-20261029\build\strata.exe SHA256 A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8; config SHA256 060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93; env MT1=1, PIPE=1, MT_MIN unset; AboveNormal. Engine command/args: reuse D:\strata\state\gpu-bw-20261030\command.json "engine" list (verified today) — re-check against the live process command line.

## Working references
- D:\strata\state\nsys-timeline-20261027\attempt5\ (nsys_attempt5.py, launch5.ps1, wrap.ps1, analyze_timeline_attempt5.py, stats-A-*.csv): the run that WORKED on this box with nsys 2026.5.1 (C:\Program Files\NVIDIA Corporation\Nsight Systems 2026.5.1\target-windows-x64\nsys.exe): engine stdin from a FILE ("GEN 512 <prompt>" then "QUIT"), elevated one-shot scheduled task (RunLevel Highest, priority 2, Unregistered afterwards; never change the API task itself), nsys launch + start/stop around decode. Reuse it.
- API stop/restore/process gate/independent verify: D:\strata\state\gpu-bw-20261030\ (controller.py, run.ps1, launch.ps1) and nt1ext-ab-20261030\.
- Slots: under profiler injection the engine came up with 3135 (10/27) / 3127 (today). Record it; do NOT gate on it.
- Use a short prompt (Hermes p01 text) so prefill is short.

## Run
1. Process gate; confirm /metrics idle; stop API like controller.py; everything after in try/finally restoring the API.
2. `nsys status -e`, `nsys profile --help` → confirm the GPU metrics option names in this version (`--gpu-metrics-devices`, `--gpu-metrics-set`, `--gpu-metrics-frequency`). List sets with `nsys profile --gpu-metrics-set=help` (or equivalent) and pick the Ada (AD10x) general set that includes DRAM read/write bandwidth.
3. Capture: trace=cuda (add nvtx if cheap), `--cuda-graph-trace=node` if graphs used, `--gpu-metrics-devices=0 --gpu-metrics-frequency=20000` (lower to 10000 if it errors), no CPU sampling needed (`--sample=none --cpuctxsw=none`). Collect only the decode phase (start after prefill, stop at DONE), 512 tokens.
4. Export with `nsys stats`/`nsys export --type sqlite`; Python (remote venv C:\Users\User\Strata\archive\legacy\20261009\Strata-lm-run-2026-09-28\.venv\Scripts\python.exe or local) on the sqlite:
   - GPU_METRICS table: DRAM read and write bandwidth (% of peak and/or bytes/s) samples.
   - Kernel table (CUPTI_ACTIVITY_KIND_KERNEL + StringIds): for each sample, which kernel was running.
   - Report: (i) whole decode capture: GPU busy fraction, mean DRAM BW while any kernel runs (GB/s and % of 504.2 GB/s); (ii) per kernel family — dense mmvq (native_mmvq_il/multi, native_q5_k/q6_k_mmvq, any *mmvq*), HC (gr_up_multi, gr_down_staged, gr_*), attention (attn_*), GDN, router/topk, other: total kernel time per window, sample-weighted mean DRAM GB/s, % of peak; (iii) top 10 kernels by total time with the same columns. Windows count = T lines in engine stdout; give ms/window.
5. Stop engine (QUIT), finally restore API, verify (/metrics loaded, PID, exe A1E6, config 060F, AboveNormal, 3153 slots, idle), unregister your task, final process gate.
6. Verdict per pre-registered rule: main families ≥80% peak → GPU kernel direction closed; ≤65% and combined ≥5 ms/window → kernel rewrite worth designing (upper bound ≈ time×(1−eff/0.85)). Mention caveat that trace overhead affects wall, not in-kernel bandwidth.

## Report
D:\strata\state\gpu-bw-nsys-20261030\RESULT.md in Traditional Chinese: identity, nsys version, metrics set and frequency, slots under nsys, tables (i)(ii)(iii), verdict, API restore evidence, process actions. Copy scripts, stats CSVs and analysis JSON there (not the multi-GB report unless < 200 MB). Do not edit EXPERIMENT_LEDGER.md.
