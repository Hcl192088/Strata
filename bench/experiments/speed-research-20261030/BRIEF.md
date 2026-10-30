# Codex brief: literature / prior-art search for decode speedups (Strata) — RESEARCH ONLY

You are doing web + local-file research. NO SSH, NO remote operations, NO benchmarks, NO builds, NO GitHub writes. Only read local files under D:\strata and search the web. Write one report.

## The system
- Strata: custom C++/CUDA inference engine (llama.cpp/ggml-derived CPU kernels, own CUDA kernels) for a large MoE model: Qwen3.8-Flash-Next-GSQ-RCO, GGUF IQ3_XXS mix (expert gate/up types IQ3_S, IQ3_XXS, IQ2_XS, IQ2_S, IQ2_XXS; down q2_0/iq4_nl), 48 layers, hundreds of routed experts per layer, hybrid attention (GDN/linear-attention + full attention, hyper-connections "HC"), MTP head used for speculative decoding (draft + verify windows of 2-3 tokens), KV q4_0, context 100k.
- Hardware (FIXED, cannot change): i5-12600KF (6P+4E, AVX2 + AVX-VNNI, no AVX-512), 32 GB DDR4-3200 dual channel (measured ~45.7 GB/s), RTX 4070 12 GB (sm_89), NVMe SSD, Windows 11.
- Placement: dense/attention + ~5.2 GB of hot experts on GPU (adaptive swap), ~20 GiB expert cache in RAM (3153 slots, LRU), the rest of experts.bin (42.9 GB) read from SSD on miss. CPU computes the experts not on GPU with a 9-worker pool. CPU and GPU overlap per layer.
- Decode ~47 tok/s at batch 1 (single user). Per verify window (~38.6 ms): GPU-reach wait ~11.7 ms, CPU expert segment ~21.7 ms (gate/up decode is compute-bound ~3.8 GB/s/core; down is DRAM-bandwidth bound; SSD-miss join ~4.4 ms; LRU admission copy ~0.9 ms), draft ~1.8 ms, other ~1.7 ms.
- Goal: +10% decode tok/s or more on this exact machine.

## "Quality" constraint — read carefully, this is the filter
ALLOWED ("no quality loss" in our sense = the model computes the same function):
- Same weights and same quantization codes/scales (no requantization, no new quant formats that change values).
- Same routing: same experts selected per token, same top-k, no expert skipping/pruning, no routing bias, no "smart expert reduction", no lower top-k.
- Same sampling parameters; speculative decoding only if verification is exact (output distribution identical to the main model).
- Differences in floating-point accumulation ORDER are acceptable (e.g. a different but mathematically equivalent kernel), as long as values are numerically equivalent at fp32 rounding level.
- Anything about scheduling, overlap, caching/prefetch policy, I/O, memory layout (lossless/reversible repacking), threading, kernel implementation, compiler, OS-level software settings, speculative decoding improvements that remain exact.
NOT ALLOWED: hardware changes or overclocking; lower precision for weights/activations/KV than now; approximate attention; token/expert dropping; sparsity that zeroes nonzero values; changing the model; distillation; anything that changes which experts run or what they compute beyond float order.
When a technique is borderline, label it and explain exactly what changes.

## Already tried (do NOT re-propose unless you cite something genuinely new about it)
Read D:\strata\state\EXPERIMENT_LEDGER.md and the plan files D:\strata\state\PLUS10_REVISED_PLAN_20261030.md, R4_PLUS10_PLAN_20261030.md, NEW_BIG_EXACT_DIRECTIONS_20261030.md, switch-inventory-20261029.md first. Summary: ik_llama.cpp R4 interleaved repack (NO_GO), iq256 gather+VNNI single-token kernels (IQ3_S deployed +4.3%; other types +1.4% not significant), LUT dot products, native-layout multi-row kernels, worker count/affinity/SMT/spin, P/E work balancing, SSD cache policies (ARC/LRU-2/Belady bound, per-layer quotas), route-prediction prefetch (insufficient precision), lossless compression of experts, mapped vs direct I/O, CPU/GPU overlap pipeline (deployed), GPU env flags (LFUSE, QFUSE, DF_BRANCH, MMVF_ROWS, DF_QB_Q4, DF_PLE, ATTN_LANECELL, EXPERT_V2, TSUM, GDN_SPLIT: no GPU-segment change), MTP depth/gate/lookup variants, mainline rebase (neutral), power plan already max.

## What to find
Search the web (papers, GitHub repos/issues/PRs/discussions of llama.cpp, ik_llama.cpp, KTransformers, PowerInfer, fiddler, MoE-Lightning, HOBBIT, AdapMoE, Pre-gated MoE, ProMoE, MoE-Infinity, SwapMoE, ExpertFlow, DAOP, llama.cpp --cpu-moe / -ot users, Reddit r/LocalLLaMA benchmarks of hybrid CPU+GPU MoE on consumer hardware, vLLM/SGLang CPU offload, etc.) for techniques that sped up batch-1 decode of hybrid-offloaded MoE models or CPU quantized matmul on AVX2 consumer CPUs, AND satisfy the ALLOWED constraint. Also: speculative-decoding improvements that are exact (e.g., tree drafts, better draft acceptance with MTP, EAGLE-style variants) applicable with an MTP head, and Windows-specific I/O or scheduling tricks.

## Output: D:\strata\state\speed-research-20261030\RESULT.md (Traditional Chinese for prose; keep technique names in English)
For each candidate (aim for 8–15 real ones, quality over quantity):
- name, source links (paper / repo / PR / benchmark post), what it does in one or two sentences;
- which of our time segments it targets and a rough upper-bound estimate in ms/window using the numbers above (show the arithmetic);
- quality class: ALLOWED / BORDERLINE (explain exactly what changes) / NOT ALLOWED (list briefly at the end only);
- whether it is already tried per the ledger (cite the ledger line/date) or genuinely new;
- implementation cost (S/M/L) and what evidence exists that it helps on hardware like ours.
End with a ranked shortlist of the top 3 genuinely-new ALLOWED candidates and why. Be honest if nothing promising is found. Do not invent sources; every claim must have a link.
