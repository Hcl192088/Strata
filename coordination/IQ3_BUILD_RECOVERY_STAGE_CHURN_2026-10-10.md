# Task 011: recover canonical Windows build path and continue stage-churn optimization

Predecessor: LUNA-20261010-010 (BLOCKED).

Task 010 already synchronized the validated promoted control into authoritative source:
- `include/strata/core/expert_source.hpp`: `kStageAge=6`
- `src/core/expert_source.cpp`: `kStageSeq=512`
The deployed control binary remains SHA256 `59292D5CCBCD200BD209AE04EE59E795DA979B6AFFD175C870E673F9FFAECEC3`.
Do not revert to 3/256.

## Phase 0 — recover the existing successful build environment

The blocker was not source correctness. The remote non-interactive shell could not find `nmake`, `cl`, `ninja`, or `msbuild`, while Task 009 had already built a valid Windows candidate on this same machine.

1. Inspect Task 009 build artifacts/logs and all relevant `CMakeCache.txt` files before changing anything. Recover the exact successful compiler/generator/CUDA provenance if available.
2. Inspect the configured canonical build directory and record at least:
   - `CMAKE_GENERATOR`
   - `CMAKE_MAKE_PROGRAM`
   - C/C++ compiler paths
   - CUDA compiler/toolkit paths
   - build type and CUDA architecture.
3. Locate the installed Visual Studio Build Tools using `vswhere.exe` or the existing recorded path. Prefer invoking the existing developer environment in the same command as the build, e.g. `VsDevCmd.bat` / `vcvars64.bat`, rather than installing or modifying system software.
4. Re-run the canonical 6/512 build using the recovered existing toolchain. If the existing build directory is stale or bound to a missing generator, create a new isolated build directory with the verified Task-009 configuration; do not destructively rewrite old build metadata.
5. Preserve the two authorized 6/512 source edits and the pre-existing `.codex/handoffs/*` files. Do not reset or clean unrelated files.
6. A byte-identical binary is desirable but not required if compiler timestamps/build metadata differ. Require instead: verified source/config identity, successful build, clean startup/1024-token execution, and no correctness/CUDA failure. Use matched controls below for performance validation; do not spend five standalone runs reproducing baseline.

Upstream Windows documentation confirms that source builds should run inside a Visual Studio developer environment; recent community Windows CUDA builds use Visual Studio Build Tools plus Ninja. Use this only as build-environment guidance, not as a reason to change the frozen benchmark identity.

If no existing installed toolchain can be recovered after checking Task-009 provenance, report BLOCKED with exact paths/probes and stop before source experimentation. Do not install toolchains autonomously.

## Phase 1 — continue the stage-cache churn campaign

Once the canonical 6/512 control can be built, continue the source-level hypothesis authorized by Task 010. Current evidence:
- Task 009 candidate median: 37.93 tok/s.
- 6/512 vs 3/256 paired median decode gain: +6.58%.
- file-tier traffic median: -30.15%.
- file-read time median: -35.21%.
- CPU pool-call time median: -15.30%.
- Task 008 trace still showed substantial refill/eviction churn.

First candidate: add a cheap reuse-frequency/second-chance component to stage-buffer victim selection, layered on top of the current eligible-LRU behavior. Use runtime hit/re-reference history already available or a small bounded per-buffer hotness counter; do not hard-code prompt-specific layers. The purpose is to avoid evicting entries that are slightly old by recency but repeatedly reused, while keeping scan/selection overhead negligible.

Instrument only enough to measure:
- stage hits/fills/refills/evictions,
- file-tier bytes/read time,
- CPU pool-call time,
- stage-buffer count/RAM,
- accepted decode tok/s.

Run 3 interleaved matched pairs against canonical 6/512 control. If paired median accepted decode gain is >=3% with no correctness/stability/memory regression, run 2 additional confirmation pairs. Promote only if the confirmed paired median remains >=3%.

Reject early if:
- first 3-pair median <=0%, or
- file-tier traffic / CPU pool time materially worsens without throughput compensation, or
- memory/stability/correctness regresses.

If this candidate fails, use remaining budget for one substantially different stage-churn source hypothesis supported by trace data. Do not repeat Task-007 lookahead/PVM experiments and do not degrade this into a broad knob sweep.

## Promotion rule

Current canonical control is 6/512. Any candidate that passes the gate becomes the new canonical source+binary+settings control immediately. Synchronize source and deployed binary before reporting PROMOTE. A rejected candidate leaves 6/512 unchanged.

## Frozen benchmark identity

Use the Task-009 IQ3 identity unchanged:
- prompt_tokens=28912
- max_context=100000
- accepted output_tokens=1024
- same model/quant/tokenizer/sampling/profile/MTP/runtime/settings.

Store new artifacts under:
`C:\Users\User\Strata-Adrian\runs\iq3-build-recovery-stage-churn-011`

Budget: up to 24 new benchmark processes and 5 hours active work. Preserve raw logs. Report current baseline, candidate, paired delta, PROMOTE/REJECT, resulting baseline, toolchain provenance, and whether any durable controller remains running.
