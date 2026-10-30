# Codex brief: search Strata upstream, its PRs/issues and forks for speedups (esp. RTX 4070) — RESEARCH ONLY

NO SSH, no remote ops, no builds, no benchmarks, no GitHub writes of any kind (no comments, stars, forks, PRs). Read public pages only (web search / fetch, unauthenticated HTTP is fine). Do NOT touch the coordination files of Hcl192088/Strata (coordination/*); that repo is our own fork used for task handoff.

## Our baseline
- Our live engine is Strata 0.1.42 lineage, source commit f520bc5 ("native-pipe-generic", our own patches: native CPU GU/down pipeline, MISS_OVERLAP, S2K, MT1=IQ3_S single-token iq256 kernel). Upstream mainline: https://github.com/Niko1221/Strata . Known fork: https://github.com/AdrianBM96/Strata3060 (RTX 3060 tuning). Our fork: https://github.com/Hcl192088/Strata (we published an RTX 4070 IQ2_XS community result there / upstream bench/results/2026-10-08-community-rtx4070-iq2-xs).
- Hardware fixed: RTX 4070 12 GB (sm_89, Ada, Windows WDDM), i5-12600KF (6P+4E, AVX2+AVX-VNNI, no AVX-512), 32 GB DDR4-3200, NVMe. Model Qwen3.8-Flash-Next-GSQ-RCO IQ3_XXS mix, MTP speculative decode, KV q4_0, ~20 GiB RAM expert cache, ~47 tok/s.
- Window ~38.6 ms: GPU-reach wait ~11.7, CPU experts ~21.7 (gate/up compute-bound ~3.8 GB/s/core; down DRAM-bound; SSD join ~4.4; LRU copy ~0.9), draft ~1.8.
- Already compared/tried — read first and do not re-propose without new info: D:\strata\state\UPSTREAM_025_027_COMPARE_20261028.md, LUNA-20261012-027.mainline-rebase-eval-20261018.md, switch-inventory-20261029.md, EXPERIMENT_LEDGER.md (grep), speed-research-20261030\RESULT.md (previous search today). Mainline 0.1.45 + RAM_ADAPT was measured performance-neutral (10/19). All GPU env flags in switch-inventory were tested: no GPU-segment change on 4070.

## Quality rule (filter)
Allowed = computes the same thing as our current best: same weights/quant values, same expert selection as current best (current best uses default ROUTE_TAIL_SKIP=7; do not loosen it), same sampling, exact speculative verification; only float accumulation-order differences allowed. NOT allowed: ROUTE_PRIOR / routing bias, more tail skipping, requantization, lower precision, hardware/overclock. Label borderline items explicitly.

## Find
1. Every upstream release/commit/PR (merged, open, closed) and issue/discussion after 0.1.42 that claims decode speedup, with emphasis on: RTX 4070 / sm_89 / Ada / 12 GB cards / Windows WDDM, Intel hybrid (P/E) CPUs, AVX2/AVX-VNNI CPU expert kernels (i-quant gate/up single-token decode, Q2_0/IQ4_NL down), SSD/RAM tier, MTP. Include upstream bench/results community reports for 4070/4070 Super/4060 Ti/3060 etc. and what config they used.
2. Forks of Niko1221/Strata (GitHub network/forks list; search "Strata" forks, e.g. AdrianBM96/Strata3060) with performance patches not upstream; especially any targeting 4070 or 12 GB cards.
3. For each finding: link, what it changes, claimed gain and on what hardware, whether it is in our f520bc5 baseline (judge from the local compare docs; say "unknown" if you can't tell), quality class, which of our segments it targets with a rough ms/window upper bound (show arithmetic), cost S/M/L.

## Output
D:\strata\state\upstream-search-20261030\RESULT.md, Traditional Chinese prose, technique/flag names in English. Sections: (A) 4070-specific items, (B) other upstream/PR items not yet in our baseline, (C) fork items, (D) already in baseline or already tested (brief), (E) excluded by quality rule (brief). End with top 3 genuinely new, allowed candidates, or say plainly that none were found. Every claim needs a link; do not invent PR numbers.
