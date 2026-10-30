# Codex brief — narrow literature search: exact CPU/GPU overlap for batch-1 MoE decode (2026-10-30)

Research only. No SSH, no remote, no paid API, no GitHub writes. Use web search. Write RESULT.md (Traditional Chinese) in this folder.

## Setting
Single user, batch=1 decode of a hybrid MoE model (Qwen-Next-style: attention + GDN layers, 512 experts, top-k ~10) on one RTX 4070 12 GB + i5-12600KF + DDR4-3200 + NVMe. Hot experts live in VRAM; the rest are computed on CPU (IQ3_XXS quant) from RAM, misses read from SSD. Exact speculative decoding with MTP verifies 2-6 tokens per window. Per layer: GPU attention+router -> CPU computes routed experts (GPU spins waiting, ~16 ms per 39 ms window) -> next layer needs this layer's full output.

## Quality definition (strict; read carefully)
"Not lowering quality" here means: SAME weights and quantized values, SAME expert selection per token (same router, same top-k, no skipping/substitution/deferral of any expert), SAME sampling, exact speculative decoding. Only floating-point summation-order differences are allowed. Anything that changes which experts are computed, when their results enter the residual stream, their precision, or the model structure is OUT.

## Already tried or excluded — do NOT report these again
1. Expert prefetch by predicting next-layer routing (SP-MoE, ProMoE, MoE-Infinity, AdapMoE, router lookahead): tested, negative (extra bytes 4.8x the rescued bytes; 0.58 ms lead time).
2. Splitting the verify window into micro-batches and interleaving CPU/GPU across them (Klotski/MoE-Lightning-style, Strata --spec-split): tested, -1.34%.
3. Expert deferral (KTransformers SOSP'25), adding expert results to a later layer: changes math -> OUT.
4. Pre-gating / moving the gate (Pre-gated MoE), retraining: OUT.
5. Low-precision miss experts (HOBBIT), skipping/tail-skip, routing bias: OUT.
6. Throughput-oriented batching methods (multi-request): not applicable.
7. Already deployed: shared expert on GPU concurrent with CPU experts; CPU GU/down pipelining; overlapping SSD reads with resident compute; multi-token CPU kernels.

## Task
Find methods OUTSIDE the list above that reduce the GPU-waits-for-CPU time per layer in batch-1 exact decode. Examples of what would count (if they exist): moving some routed-expert work between CPU and GPU dynamically per layer without changing which experts are computed; splitting a single expert's rows between CPU and GPU; overlapping the NEXT window's draft/MTP or other independent work into the GPU idle time; reducing CPU-GPU handoff latency (doorbells, polling, CUDA graph tricks); asynchronous combine. For each: source link (paper/PR/repo), what exactly it does, whether it satisfies the strict quality definition (yes/no + why), reported speedup and its setting, and whether it plausibly applies to 1 GPU + consumer CPU.
Spend real effort (at least ~15 distinct searches: arXiv 2024-2026, llama.cpp/ik_llama.cpp/KTransformers/Fiddler/PowerInfer/llamafile issues and PRs). A "nothing found" conclusion is acceptable ONLY with the list of queries and sources checked. Partial reports that stop early are not acceptable; your own tool errors are not stops.
