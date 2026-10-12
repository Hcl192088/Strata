TASK_ID: LUNA-20261012-025
STATUS: NEW
CLAIM_REQUIRED: true
BASELINE: Latest PROMOTED IQ3; Task018 e26d5538/662C7E61 if unchanged; 20GiB.
HYPOTHESIS: v0.1.42 61b3fb5d/803C1EA tail7+PCIe-auto reaches 47-53 tok/s. Promote speed-first; overlap CPU-miss I/O for >55.
BENCH: Reuse 020/023/024 raw; NO tail/PCIe/KL reruns. First 3 interleaved v0142-vs-canonical pairs+2 confirms. Then isolated src/core/expert_source.cpp::expert_pool_dispatch_multi + FileExpertSource::prefetch: async queue distinct CPU misses early; wait at blob use; 3+2 vs NEW control. Frozen IQ3_XXS, prompt SHA93505844 (28912), ctx100k, MTP6, env/profile, 1024 accepted.
GATE: Each stage paired median>=3%, 2 same-control confirms, stable => PROMOTE source+binary+settings; else REJECT. KL diagnostic, NOT blocker.
LIMIT: 28 new runs/8h; exclusive claim; no 4096/sweeps/repeats; retry transients.
RAW: C:\Users\User\Strata-Adrian\runs\iq3-campaign-025
REPORT: main outbox; raw/SHA/activation/pairs/variance/decision/new control.