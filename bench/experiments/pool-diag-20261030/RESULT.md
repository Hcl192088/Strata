[LUNA_REPORT]
TASK_ID: LUNA-20261012-027
STATUS: DONE / REPORT_LOCAL
TASK: POOL_INTERNALS_AND_UNTIMED_DIAG, attempt 4
Authorization: user 2026-10-30, timing-only isolated diagnostic build and C/D/C/D, temporary API stop and restore; no push or publication.

Remote DESKTOP-LKMLUPC, worktree C:\Users\User\pooldiag-20261030, baseline f520bc5e9d31c93caeb296b059e3a3eaa16e493f, patch commit ed0b9d62 (local only), DIAG binary SHA256 DA40C93A594B8A571FA6047057CCB8EC370E7639B0B7EEEDE4CE88F0692D13D3. Baseline binary A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8, live configuration SHA256 060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93. Build used the same Release, NMake, CUDA arch 89, dependency and -j 2 settings as current best; isolated output, BelowNormal. Build succeeded. Before/after gates passed. Build's two orphan compiler services were identified by PID, creation time and absent parent, then stopped as authorized. Patch and raw six lines are saved alongside this report.

## C/D results

Hermes p01/p05/p08, max 512, original c.make_body sampling, fresh engine per block, AboveNormal, MT1=1, PIPE=1, MT_MIN absent, capacity 3153/20.00 GiB/20479 MiB; C,D,C,D. ms/window is weighted by windows within each block; rate is output tokens / decode time. Sampling produces different windows and outputs, so these are observations, not an isolated estimate of instrumentation overhead.

| Block | Arm | Windows | ms/window | tok/s |
|---|---|---:|---:|---:|
| 1 | C | 358 | 43.58 | 39.48 |
| 2 | D | 463 | 38.04 | 43.15 |
| 3 | C | 539 | 42.14 | 41.78 |
| 4 | D | 461 | 39.53 | 42.58 |
| Aggregate | C | 897 | 42.71 | 40.63* |
| Aggregate | D | 924 | 38.79 | 42.86* |

* Arithmetic mean of block rates. D/C: -9.2% in window-weighted ms/window and +5.5% in mean block tok/s. Difference exceeds 5%; timing perturbation/workload variation is large, numbers are relative only. No speed claim.

## Pool (D, window-weighted average)

P worker LPs 2,4,6,8,10; E worker LPs 12–15; entries are summed worker time divided by number of workers in the group and windows, and may overlap across workers. Native-pipeline calls only. Host's own kernel time is not in P group.

| Metric | ms/window per worker unless noted |
|---|---:|
| Pool calls/window | 54.25 |
| P GU / quant / down | 9.149 / 0.012 / 3.834 |
| E GU / quant / down | 9.625 / 0.038 / 3.952 |
| Host wait for done (ms/window) | 0.173 |
| Dispatch latency, idle/spin, completion skew, GPU overlap | Not measured |

## Decode loop (D, ms/window, window weighted)

| Part | ms/window |
|---|---:|
| Verify (includes pool and GPU wait) | 35.429 |
| Commit plus emit | 0.064 |
| MTP draft including draft setup | 1.673 |
| Suffix/lookup and window selection | 0.001 |
| apply_pending | 0.678 |
| Post-window bookkeeping | Not measured separately |
| Remaining unattributed (includes post-window) | 0.940 |
| Total | 38.786 |

Commit sub-steps were not measured separately. Conservation maximum discrepancy among six raw lines is 0.000003% from output rounding. The residual is defined by subtraction, so conservation is an accounting check, not independent validation of coverage. The first decode window is included, as in the existing decode timing. Pool CPU times overlap each other and verify; they must not be added to the decode totals.

No cost >=1 ms/window is established as removable without changing computation by this diagnostic. MTP draft and worker GU/down exceed 1 ms/window, but the measurements do not demonstrate a removable component.

## Restore and coverage

Controller completed all four blocks and reported restored=true, verified=true. Independent preflight confirmed one live strata.exe, baseline SHA and config SHA above, AboveNormal, loaded, 3153 slots, 20.00 GiB/20479 MiB, idle and queue 0. Scheduled task Strata-POOL-DIAG-20261030 was disabled; readback priority 2, PT2H. Final full process inventory was captured; diagnostic inventory command itself appeared in the snapshot. Name/command review found no remaining build or benchmark processes; ordinary OS/vendor processes were not individually attributed. No model sampling change, deployment, push, or GitHub publication. CPU per-kind timing covers the native pipeline worker kernels, not host execution or all possible pool modes. Requested dispatch, idle/spin, first/last start, skew, overlap and commit sub-steps were not instrumented. No per-layer-type breakdown or per-window raw rows was recorded; six request summary lines are available. Perturbation and sampled-output differences limit comparisons.

BENCHMARK_RAW_PATH: C:\Users\User\Strata-Adrian-control\runs\pooldiag-20261030\out
