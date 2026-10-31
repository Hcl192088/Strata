STATUS: DONE (coordinator 2026-10-31 ~08:00; from remote s2\ab\blocks.json → ab-blocks.json)

# S2 clang-cl vs MSVC
- Microbench (Codex, s2-clang/analysis.md): layer-weighted P-core nt=1 1.149x, nt=2 1.019x, nt=3 1.018x; E-core 1.075x / 1.139x / 1.094x; outputs max_abs 1.19e-7.
- Full clang-cl build EF8AF397AA87…C1D7 (CPU sources clang-cl, CUDA via MSVC/nvcc). 2 greedy points ran OK; texts differ slightly from A1E6 (float order expected).
- Engine A/B C (A1E6) vs CL, 5 rounds rotated, 10 Hermes x 512, original sampling, slots 3153 both:
  - per-round paired tok/s: +2.69, +10.34, +4.75, −4.13, +2.08 → mean +3.15%, 95% CI [−3.3, +9.6]
  - block-weighted: CPU 22.01 → 20.00 ms/w, ms/window 39.01 → 36.99, GPU-reach 11.75 = 11.75, draft 1.78 → 1.77, tok/window 1.835 → 1.791
  - per-point paired (n=50): tok/s +0.62% [−3.27, +4.51]; ms/window −1.92% [−6.36, +2.51]; CPU ms −3.47% [−10.12, +3.17]; CPU µs/expert −2.11% [−7.17, +2.94]; tokens/window −3.17% [−5.11, −1.22] (significant)
- Verdict: POSITIVE DIRECTION, NOT CONFIRMED. CPU segment drops ~2 ms/w at block level but per-expert gain (~2%) is far below the microbench 1.15x, and tokens/window is significantly lower (unexplained; not expected from float-order alone). Needs a 10-round confirmation plus a check of why acceptance moved (e.g. greedy C-vs-C vs C-vs-CL token agreement) before any promotion.
