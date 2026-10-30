[LUNA_REPORT]
TASK_ID: LUNA-20261012-027
STATUS: REPORT_LOCAL / COMPLETED
Authorization: 2026-10-30 GPU6 bundle C/B A/B, temporary live API stop and restore.
Remote: DESKTOP-LKMLUPC; strict SSH host key.
BENCHMARK_RAW_PATH: C:\Users\User\Strata-Adrian-control\runs\gpu6-ab-20261030\out

Both arms current-best A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8; live config 060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93. Both STRATA_NATIVE_PIPE=1, STRATA_IQ3S_MT1=1, STRATA_IQ_MT_MIN absent; B adds DF_BRANCH, MMVF_ROWS, DF_QB_Q4, DF_PLE, ATTN_LANECELL, EXPERT_V2 (all STRATA_ prefix, value 1). Config and effective environment audited each block. Forbidden switches absent. Per-block gate, 3153 slots / 20.00 GiB / 20479 MiB and AboveNormal passed. Original sampling via c.make_body, 10 Hermes points x 512 maximum. Scheduled task priority 2, same User interactive principal, PT3H.

Window-weighted timings in ms/window; output lengths are completion tokens p01–p10. No request errors, fatal/CUDA errors, or detected B consecutive repetition loop.

| # | Round | Arm | tok/s | tokens | windows | GPU wait | CPU | draft | ms/window | output lengths | errors |
|---:|---:|:---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 0 | 1 | C | 47.83 | 1875 | 1059.0 | 11.57 | 20.33 | 1.72 | 37.02 | 103, 112, 67, 164, 486, 157, 241, 100, 237, 208 | none |
| 1 | 1 | B | 46.33 | 1761 | 997.0 | 11.53 | 21.36 | 1.80 | 38.13 | 103, 112, 67, 164, 486, 216, 104, 102, 203, 204 | none |
| 2 | 2 | B | 47.49 | 1878 | 1039.0 | 11.53 | 21.32 | 1.81 | 38.06 | 103, 112, 67, 164, 484, 253, 98, 117, 182, 298 | none |
| 3 | 2 | C | 45.12 | 1868 | 975.0 | 11.75 | 25.25 | 1.83 | 42.46 | 103, 107, 123, 204, 488, 171, 103, 119, 135, 315 | none |
| 4 | 3 | C | 46.77 | 1918 | 1048.0 | 11.59 | 22.43 | 1.77 | 39.13 | 103, 112, 67, 168, 450, 207, 104, 216, 101, 390 | none |
| 5 | 3 | B | 47.25 | 2128 | 1154.0 | 11.65 | 22.12 | 1.93 | 39.03 | 103, 112, 67, 164, 486, 171, 86, 304, 123, 512 | none |
| 6 | 4 | B | 45.92 | 2361 | 1331.0 | 11.55 | 21.82 | 1.81 | 38.63 | 103, 112, 67, 164, 486, 512, 78, 118, 468, 253 | none |
| 7 | 4 | C | 46.53 | 1953 | 1125.0 | 11.54 | 20.49 | 1.70 | 37.30 | 103, 112, 67, 164, 486, 171, 99, 120, 119, 512 | none |
| 8 | 5 | C | 43.72 | 1654 | 937.0 | 11.55 | 23.57 | 1.73 | 40.37 | 103, 112, 67, 164, 486, 173, 75, 125, 122, 227 | none |
| 9 | 5 | B | 44.27 | 1828 | 930.0 | 11.72 | 27.41 | 1.94 | 44.40 | 103, 112, 67, 168, 316, 196, 161, 275, 122, 308 | none |

| Round | B/C change | B − C GPU-reach wait (ms/window) |
|---:|---:|---:|
| 1 | -3.14% | -0.044 |
| 2 | +5.25% | -0.214 |
| 3 | +1.02% | +0.058 |
| 4 | -1.32% | +0.013 |
| 5 | +1.25% | +0.168 |

Mean paired B/C +0.61%; 95% t CI (df=4) [-3.31%, +4.53%]. Early stop did not trigger.

Output lengths: C 9268 total, 185.36 per request; B 9956 total, 199.12 per request; B − C 688 total, +13.76 per request. Semantic quality not assessed.

Restore: controller restore.json restored=true and final_verify.json verified=true. Independent SSH verification: one strata.exe PID 22184, AboveNormal, matching binary/config hashes, loaded, 3153 slots / 20479 MiB / 20.00 GiB, idle queued 0. Full process inventory saved; relevant process gate found no leftover controller/benchmark/build. Test task disabled, priority 2, PT3H.

Deviations: initial preflight invocation used system Python and failed to import psutil; reran using the existing harness virtual environment before stopping the API. Task wrapper did not disable the test task automatically; independently disabled it after completion and verified readback. Cause of wrapper exit before disable not established. Fatal/CUDA log checks ran at response/health boundaries and after blocks; they were not continuously monitored during a pending HTTP request. Full inventories retained locally; inspection focused on Strata, Python, build and diagnostic process names/commands, with ordinary OS services not individually attributed. No deployment, rebuild, source change, push, publication, or quality claim.
