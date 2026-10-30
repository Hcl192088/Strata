# Codex brief: search for faster AVX2/AVX-VNNI CPU kernels for i-quant single-token gate/up (Strata) — RESEARCH ONLY

NO SSH, no remote ops, no builds, no benchmarks, no GitHub writes. Read local files under D:\strata and public web pages only.

## The bottleneck
- CPU: i5-12600KF (6 P-cores with HT + 4 E-cores; AVX2, FMA, F16C, AVX-VNNI (VEX dpbusd/dpwssd); NO AVX-512). DDR4-3200 dual channel, measured 45.7 GB/s.
- Strata (llama.cpp/ggml-derived) computes MoE experts on CPU, batch-1 decode, mostly nt=1 token per expert (sometimes 2-3 in speculative verify windows). Activations quantized to Q8_K (292-byte blocks, no extra float sum).
- Expert gate/up weight types and layer counts: IQ3_S 13 layers, IQ3_XXS 6, IQ2_XS 10, IQ2_S 10, IQ2_XXS 9. Down: q2_0 (type 42) or iq4_nl.
- gate/up is COMPUTE-bound at ~3.8 GB/s per core (pure read on same core 27.7 GB/s); codebook/grid lookup + sign handling dominates. Amdahl bound if gate/up became DRAM-bound: about +11% end-to-end; 1.2x kernel ≈ +4.7%, 1.3x ≈ +6.5%. down is already DRAM-bound (44 of 45.7 GB/s) — down speedups don't count.
- Current kernels: nt=1 uses ggml-cpu vec_dot (AVX2) for IQ2_*/IQ3_XXS; IQ3_S nt=1 and all nt>=2 use Strata "iq256" (P-core: gather + AVX-VNNI; E-core: VNNI without gather). Single-core measured speedups of iq256 over ggml at nt=1: IQ3_S 1.78-1.90x (deployed), IQ2_S 1.26x, IQ2_XS 1.24x (P only), IQ3_XXS 1.17x (P only), IQ2_XXS 1.085x. Extending to these four types gave only +1.44% end-to-end (not significant).
- Built with MSVC 19.44 /O2 /arch:AVX2 (ggml FindSIMD under MSVC only detects AVX/AVX2/AVX512). Compiler choice (clang-cl) is untested.

## Already tried — do NOT re-propose unless you cite something genuinely new
Read D:\strata\state\EXPERIMENT_LEDGER.md (grep R4, LUT, NR2, NR4, lowreg, prefetch, gather, VNNI, iq256, MT1, NT1_EXT), D:\strata\state\PLUS10_REVISED_PLAN_20261030.md, R4_PLUS10_PLAN_20261030.md, cpu-r4-v2-20261030\KERNEL_NOTES.md, speed-research-20261030\RESULT.md, upstream-search-20261030\RESULT.md.
Tried: ik_llama.cpp R4 interleaved repack at commit d4c1f75533ec897f54944f2734ea0d0e89e4fe01 (all variants NO_GO), activation-dependent codebook LUT (13.8-25.1% of baseline throughput), native-layout multi-row NR2/NR4 kernels (slower), software prefetch distance, gather+VNNI (deployed/extended), sign lookup tables for IQ2 (slower), lossless compression.

## Quality rule
Same weights and quant values (no requantization, no new quant types that change values, no expanded/dequantized resident copies that change capacity), same expert selection and sampling. Only float accumulation-order differences allowed. A repack is only acceptable if it is lossless/reversible AND doesn't need a second resident copy (RAM capacity is fixed at 20 GiB of expert cache).

## Search targets
1. ik_llama.cpp commits/PRs AFTER d4c1f755 touching iqk kernels for IQ2_XXS/IQ2_XS/IQ2_S/IQ3_XXS/IQ3_S on AVX2 / AVX-VNNI, especially single-row/nt=1 (non-repacked) paths, and their claimed gains on non-AVX512 CPUs.
2. llama.cpp ggml-cpu x86 PRs (merged/open, 2025-2026) improving IQ2/IQ3 vec_dot on AVX2/AVX-VNNI (e.g. like #26348 for Q2_0), and anything about MSVC vs clang performance of ggml-cpu on Windows.
3. llamafile / tinyBLAS, KTransformers CPU backend (AVX2 path, llamafile-based MoE kernels), T-MAC/bitnet.cpp only if applicable to IQ codebook formats without requantization, Intel Neural Speed / xFasterTransformer if relevant.
4. Evidence on clang-cl vs MSVC codegen for intrinsics-heavy ggml kernels (register spills, ymm stack traffic) on Windows.
5. Any technique to speed up E-core (Gracemont) execution of these kernels specifically.

## Output: D:\strata\state\cpu-kernel-search-20261030\RESULT.md (Traditional Chinese prose; technique names in English)
For each finding: link (commit/PR/issue/paper), what it changes, which types and nt, claimed speedup and on what CPU, whether it needs AVX-512 (exclude if so), quality class, overlap with what we tried (cite ledger), and a rough end-to-end estimate using: gate/up ≈ 8.8 ms/window of a 38.6 ms window, end-to-end gain = 38.6/(38.6 − saved) − 1 (show arithmetic, with per-type layer weights if possible). End with top 3 genuinely new allowed candidates, or say plainly none. Every claim must have a link; do not invent commit hashes or PR numbers. State coverage gaps honestly.
