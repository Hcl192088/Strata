# Stage S2 — clang-cl vs MSVC for CPU expert kernels (item 3)

Read D:\strata\state\untested5-20261031\COMMON.md first; all its rules apply. Folder: D:\strata\state\untested5-20261031\s2-clang\.

Background: gate/up expert compute is compute-bound (~9.2–9.6 ms/window per worker). Current build: MSVC 19.44 /O2 /arch:AVX2. Never tested with clang-cl. Production paths: ggml-cpu single-token vec_dot (nt=1) for IQ2_XXS / IQ2_XS / IQ2_S / IQ3_XXS; Strata iq256 for IQ3_S nt=1 (MT1) and all types nt>=2; down via ggml (q2_0 / iq4_nl, DRAM-bound).

1. Install LLVM on the remote with winget (`winget install -e --id LLVM.LLVM --silent --accept-package-agreements --accept-source-agreements`); authorized by the user. If winget fails, try the Visual Studio "C++ Clang tools" component only if no reboot is needed; else report. Record the clang-cl version.
2. Microbench: rebuild the 2026-10-28 IQ all-types harness (D:\strata\state\iq-alltypes-nt1-bench-20261028\ and the remote dir it references) twice from the SAME sources: MSVC (current flags) and clang-cl (/O2 /arch:AVX2, plus -mfma -mf16c -mavxvnni only where the MSVC build effectively uses those paths; same preprocessor defines; no fast-math). Measure all 5 GU types x P-core and E-core x nt=1,2,3 using the paths production uses, plus down (q2_0, iq4_nl) nt=1. Interleave builds, >= 15 repetitions each, single thread BelowNormal; median µs/expert and ratio; output compare clang vs MSVC (float-order differences allowed; report max_abs).
3. Weighted estimate with production layer counts (IQ3_XXS 6, IQ3_S 13, IQ2_XS 10, IQ2_S 10, IQ2_XXS 9) and P/E shares -> ms/window saving.
4. If the weighted P-core GU gain >= 1.05x: build a full strata.exe variant in a NEW build directory with the CPU C/C++ sources compiled by clang-cl (CUDA host compilation may stay MSVC/nvcc; e.g. CMake -T ClangCL or per-target compiler; everything else identical). Verify it runs and compare text vs A1E6 on 2 greedy points (report diffs). Then engine A/B C (A1E6) vs CL with the gpu6-ab harness, 5 rounds rotated, 10 Hermes x 512, capacity gate 3153 / 20.00 GiB / 20479 for both. Report tok/s, CPU ms/w, pool / GU / down if logged, outputs.
5. If < 1.05x, stop after the microbench (no engine build) and say so.

Report RESULT.md (Traditional Chinese): versions, flags, microbench table, weighted estimate, A/B table if run, verdict, API left not running.
