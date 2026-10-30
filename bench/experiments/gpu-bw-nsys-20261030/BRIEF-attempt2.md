# Codex brief — GPU BW via nsys, attempt 2 (2026-10-30). READ FIRST; overrides attempt-1 choices.

Read D:\strata\AGENTS.md and BRIEF.md in this folder (all rules, identity, done/blocked definitions, report format still apply). The user explicitly authorized this re-run on 2026-10-30 ("重跑"): stop the live API once more, run the nsys diagnostic, restore. Attempt 1's evidence: RESULT.attempt1.md, controller.py, stdout.log, nsys-calls.log, trace.sqlite here.

## Why attempt 1 produced nothing (fix all three)
1. Prompt: a short text prompt gave PP 15 tokens and the model stopped after 13 tokens (EOS, "DONE ... stop"). FIX: use the exact prompt the 10/27 nsys run used: ns.PROMPT in the remote 10/27 scripts (neuro.tokens, SHA256 9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA, 28912 tokens; it generated the full 512/1024 tokens; prefill ~56 s). Find it via the remote copy of the 10/27 run (C:\Users\User\Strata-Adrian-control\runs\nsys-timeline-20261027\..., ns.py) and local D:\strata\state\nsys-timeline-20261027\attempt5\nsys_attempt5.py (it writes stdin.txt as 'GEN %d %s\nQUIT\n' % (N, prompt) with prompt = PROMPT.read_text().strip()). Verify the SHA. GEN 512.
2. Capture timing: nsys start was triggered at the first T line, too late → no CUDA events, metrics covered 0.18 s. FIX: do NOT use launch/start/stop. Use a single `nsys profile` that collects from process start to exit: `nsys profile --trace=cuda --cuda-graph-trace=node --sample=none --cpuctxsw=none --gpu-metrics-devices=0 --gpu-metrics-set=<AD10x general set used in attempt 1> --gpu-metrics-frequency=10000 -o <run>\trace <engine list>`. (10 kHz keeps the file manageable over ~70 s; prefill is included and filtered afterwards.) Engine stdin = file, stdout/stderr = files, runner polls stdout and never blocks on nsys.
3. Decode-window identification: timestamp each T line as you poll stdout (record host QPC/wall time), and also record the wall time of READY, first T, DONE. Afterwards align with the trace: the decode segment is from the first decode kernel after prefill to DONE; also cross-check by kernel pattern (prefill kernels are large-batch; decode windows are short repeating sequences). State the alignment method used.

## Sanity gates on the data (report, don't silently pass)
- output tokens must be 512 (or the engine's own DONE count ≥ 500); else retry ONCE with the same settings, then report.
- trace must contain CUPTI_ACTIVITY_KIND_KERNEL rows inside the decode segment and GPU_METRICS samples spanning it. If metrics are missing but kernels exist, still deliver kernel-time tables and mark bandwidth "not measured".

## Analysis (on the exported sqlite; use the decode segment only)
- (i) whole decode segment: GPU busy fraction (union of kernel intervals / wall), mean DRAM Read+Write % (metric ids for "DRAM Read Bandwidth [Throughput %]" / "DRAM Write ...") over samples where GR Active ≥ 90%, converted to GB/s with 504.2 GB/s peak; histogram p10/p50/p90.
- (ii) per family (dense mmvq: *mmvq*; HC: gr_*; attention: attn*; GDN; router/topk; other): kernel ms per window (windows = T lines in segment), and DRAM % averaged over samples whose timestamp falls inside that family's kernel intervals (sample-weighted).
- (iii) top 10 kernels by total time, same columns.
- Verdict per pre-registered rule (≥80% → closed; ≤65% and combined ≥5 ms/window → kernel rewrite worth designing, upper bound ≈ time×(1−eff/0.85)).

## Done
Same as BRIEF.md: restore API in finally (wait until engine process is gone, then restart; verify /metrics loaded, PID, exe A1E6, config 060F, AboveNormal, 3153, idle), unregister your one-shot task, final process gate, RESULT.md (Traditional Chinese) in this folder. Partial reports are not acceptable; your own script errors are not stops.
