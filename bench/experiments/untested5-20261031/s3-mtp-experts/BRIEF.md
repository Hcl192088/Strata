# Stage S3 — MTP expert residency: routing histogram and hot-subset feasibility (item 1)

Read D:\strata\state\untested5-20261031\COMMON.md first; all its rules apply. Folder: D:\strata\state\untested5-20261031\s3-mtp-experts\.

Background: the MTP draft layer keeps all 512 experts resident in VRAM (675 MiB, q2_0 blobs of 1,382,400 B, mtp.cpp ~298-318). VRAM ruler: +675 MiB for main-model expert slots ≈ −8.0..9.6% CPU expert work (≈1.2–1.5 ms/window). The MTP expert usage distribution was never measured.

1. Read the source: how MTP routing works (top-k, per draft step), where the expert blobs live, whether a host copy exists, how slots are computed from free VRAM.
2. DIAG build (copy source to a new dir; add only logging; separate build dir; never touch the current-best exe): per draft step, log the MTP routed expert ids. Run the 10 Hermes points x 512 once (not a benchmark) with current-best args/env. Also capture draft steps per window.
3. Analysis: histogram over 512 experts; coverage of MTP expert calls by the top-N experts for N = 32, 64, 128, 192, 256, 384; stability: rank on points 1–5, evaluate on 6–10.
4. Cost model for "keep top-N resident; cold experts computed on CPU from a host copy during the draft (pool idle then) or uploaded on demand": cold calls per window x cost per cold call (microbench CPU q2_0 nt=1 expert with the existing ggml path; PCIe upload of 1.38 MB at measured bandwidth) vs VRAM freed (675 MiB x (1 − N/512)) via the ruler -> net ms/window per N. Include the RAM cost if a host copy must live in RAM (reduces the RAM expert cache; estimate extra SSD reads from ram-policy-sim / SSD_JOIN_BOUND data, or state unknown).
5. If the best N gives estimated net >= +1.5% (>= 0.6 ms/window): implement an env-gated (default off) prototype in the copy: top-N MTP experts resident (static list from points 1–5), cold experts -> CPU compute from host copy, or on-demand upload, whichever is simpler and correct. Verify text identity vs A1E6 on 2 greedy points, then engine A/B C vs HOT (gpu6-ab harness, 5 rounds rotated, 10 Hermes x 512; HOT gets more slots — record, do not gate on 3153; gate RAM 20.00 GiB / 20479). If the estimate is < +1.5%, stop after the analysis and say so.

Report RESULT.md (Traditional Chinese): source facts with file:line, histogram/coverage table, cost model, prototype + A/B if run, verdict, API left not running.
