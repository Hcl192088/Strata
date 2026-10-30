# Next research candidate: same-size row-interleaved CPU IQ kernels

Status: PROPOSAL_ONLY. User asks for the next idea; no new engine run, build, model conversion or deployment authorized/executed in this turn. Read-only remote checks confirm DESKTOP-LKMLUPC, current-best A1E6...91AD8, only classified API/watch processes.

## Concrete hypothesis

Interleave four output rows inside each expert's gate/up matrix and compute them together. Keep every original code,scale and sign; no re-quantization, omitted experts, changed routing, expanded int8 weights or extra resident copy. Reuse input activation loads and prepare SIMD sign/scale lanes with fewer repeated operations. The source reference exists for all five actual GU types, not just IQ3_XXS's six layers.

Primary reference pinned today: ikawrakow/ik_llama.cpp d4c1f75533ec897f54944f2734ea0d0e89e4fe01.
- ggml/src/ggml-common.h:474/489/507/523/543 static_assert R4 block size = four original blocks for IQ2_XXS,IQ2_XS,IQ2_S,IQ3_XXS,IQ3_S.
- ggml/src/iqk/iqk_quantize.cpp:8588,8683,8765,8850,8945 are direct original-block repackers; do not call float-to-quant conversion wrappers.
- ggml/src/iqk/iqk_gemm_iquants.cpp:1119 onward has AVX2 non-HAVE_FANCY_SIMD path, alongside AVX512 specializations. Source availability is not a performance or quality result on 12600KF.
- Actual Strata src/kernels/cpu/iq_avx2.cpp describes decoding32-value chunks reused across tokens; R4 changes layout and sharing across output rows. Confirmed current remote source still decodes original formats with per-chunk sign/scale/codebook handling.

## Budget and numerical contract

R4 structural bytes parity solves the previous int8-expansion objection at format level only. Runtime memory parity is unproven: CPU resident/stage and GPU admission share original expert blobs, so packed CPU data may require repack on SSD admission and inverse transform for GPU transfer. These costs and scratch/metadata bytes must be charged; do not silently keep two copies or change GPU residency/tail-skip contribution sets.

Same weight values do not prove same dot-product output. Existing reference uses different accumulation paths for nt=1/2 and IQ3_S MT1. Check bitwise where claiming exactness; otherwise record numeric differences and use the existing quality gate before any integration/promotion. No quality-parity claim now. Preserve model temperature and original request settings.

## Mechanism-first next unit

Standalone CPU-only microbenchmark against the CURRENT native kernel path on original expert bytes. Test actual five GU types, P/E cores, nt1/2/3, representative rows/working set; exact repack/decode roundtrip, declared output numerical contract and actual bytes. Measure conversion time per miss and inverse conversion per GPU admission, plus GU/down-combined costs; GU-only speed cannot be labeled whole-pipeline gain. No full-pack conversion, live API stop, runtime source integration or full Strata rebuild for the first screen.

Use observed format/nt/core weights if available; identify missing weights explicitly. Only if net gain after unchanged down, exposed I/O wait and conversion costs plausibly reaches3.37ms/window should a small whole-engine candidate be considered. An improvement confined to one format does not pass this gate. No preset extra rounds or flag sweep.

## Checklist answers

1. Latest same-binary control47.316tok/s, +10% target52.048. New diagnostic48.098 is instrumentation-only, not a replacement baseline.
2. Today's instrumented same-source pipeline14.6818ms/window, join4.4068, LRU.9114; GU/down subcounters0 under pipeline, so exact per-component share remains unmeasured. Older fine-grained GU/down timings are stale.
3. New local fixed-I/O model over all53472 captured dispatches: scaling ALL existing compute1.3x saves2.7643ms/window (~8.06%);1.4x saves3.4192(~10.16%);1.5x3.9864(~12.05%). This optimistically scales the ready prefix and cold compute, preserves observed per-layer I/O offsets, leaves GPU/other costs fixed and excludes new packing costs. It is a feasibility target, not a speed forecast. R4 GU-only must beat this all-compute requirement after unchanged down is included. Source: CPU_R4_ORACLE_20261029.json.
4. Structural CPU representation/kernel work, not another GPU flag/worker sweep. Earlier CPU flag results do not establish an R4 gain.
5. Do not rerun MT1/MT_MIN/gather/affinity/pinned/spec/SSD-arrival experiments; their evidence is retained.
6. Miss prediction/quota/compression and placement have measured limits; SSD-arrival cold compute only.64ms/w; GPU path remains an alternative but has no selected validated fusion site; mainline existing row-interleaved IQ code is the specific reusable mechanism inspected now.
7. Last failure diagnosed: most miss batches have one expert and little cold compute, so read-ready scheduling cannot hide enough work. New candidate attacks the remaining14.68ms compute pipeline; no assumption that raw CPU20.33ms is all IQ arithmetic.

## Coverage

Full latest10-request phase lines aggregated; full53472 dispatch records used by fixed-I/O model. Targeted remote native_expert/iq_avx2 source and relevant prior microbench/report/ledger passages read, not a full repository audit. External three IQ files and common block structs fetched from one exact commit; selected repack bodies/AVX2 path/dispatch/size assertions inspected, not all kernel variants or dependency behavior. No R4 performance, full decoded-value parity, integration, new memory footprint or quality test performed.

Completion: see RESULT.md. Corrected combined dispatch only rerun; initial scalar-Q2 combined excluded. NO_GO_BOUNDED_SCREEN.
