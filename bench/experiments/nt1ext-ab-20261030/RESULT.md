[LUNA_REPORT]
TASK_ID: LUNA-20261012-027
STATUS: REPORT_LOCAL / COMPLETED
Authorization: 2026-10-30 phase 2 C/B only; temporary API stop and restoration.
Remote: DESKTOP-LKMLUPC; strict host-key SSH; run directory: C:\Users\User\Strata-Adrian-control\runs\nt1ext-ab-20261030
BENCHMARK_RAW_PATH: C:\Users\User\Strata-Adrian-control\runs\nt1ext-ab-20261030\out

Gates: full process inventories saved locally; fresh pre-stop c.gate and every block gate passed. Current-best BEST manifest and live binary SHA A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8, config SHA 060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93, candidate SHA FD272B491C4498D4F6F31546B5E1E26BAAD744DE837174F6A507B98718FC129A verified. No build. All blocks 3153 slots / 20.00 GiB / 20479 MiB and AboveNormal, MT1=1, MT_MIN absent, NT1_EXT active exactly on B. Config differences constrained to exe/cwd/log/NT1_EXT; original request sampling preserved. Task Strata-NT1EXT-AB-20261030 used API User interactive principal, priority 2 readback, PT3H; now Disabled.

10 points per block, max 512 output tokens; rates aggregate engine-generated tokens / decode time. Segment values are window-weighted ms/window from engine decode timing; output lengths are completion tokens per point p01–p10.

| # | Round | Arm | tok/s | tokens | windows | GPU wait | CPU | draft | total ms/window | output lengths | errors |
|---:|---:|:---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 0 | 1 | C | 47.35 | 1939 | 1044 | 11.62 | 22.41 | 1.83 | 39.22 | 103, 112, 67, 168, 304, 512, 87, 179, 124, 283 | none |
| 1 | 1 | B | 49.91 | 2125 | 1203 | 11.67 | 18.66 | 1.77 | 35.40 | 54, 75, 69, 190, 512, 127, 109, 264, 424, 301 | none |
| 2 | 2 | B | 47.22 | 2028 | 1083 | 11.64 | 22.86 | 1.79 | 39.65 | 96, 43, 67, 158, 340, 194, 76, 341, 201, 512 | none |
| 3 | 2 | C | 48.33 | 1980 | 1103 | 11.61 | 20.44 | 1.74 | 37.14 | 103, 112, 67, 168, 512, 161, 159, 109, 233, 356 | none |
| 4 | 3 | C | 48.67 | 2246 | 1208 | 11.67 | 21.40 | 1.78 | 38.20 | 103, 112, 67, 164, 484, 486, 277, 233, 135, 185 | none |
| 5 | 3 | B | 47.47 | 1861 | 1094 | 11.61 | 19.14 | 1.70 | 35.83 | 187, 68, 67, 194, 512, 228, 127, 111, 109, 258 | none |
| 6 | 4 | B | 46.71 | 1774 | 932 | 11.70 | 23.78 | 1.80 | 40.76 | 105, 111, 66, 159, 512, 182, 130, 132, 130, 247 | none |
| 7 | 4 | C | 44.49 | 2132 | 1104 | 11.77 | 26.12 | 1.83 | 43.40 | 103, 112, 67, 168, 339, 299, 196, 159, 323, 366 | none |
| 8 | 5 | C | 45.16 | 2144 | 1240 | 11.66 | 21.50 | 1.72 | 38.28 | 103, 112, 67, 164, 484, 338, 139, 129, 133, 475 | none |
| 9 | 5 | B | 45.89 | 1601 | 852 | 11.72 | 24.02 | 1.78 | 40.95 | 50, 124, 59, 139, 215, 190, 77, 283, 118, 346 | none |

| Round | B/C change | B minus C CPU ms/window |
|---:|---:|---:|
| 1 | +5.39% | -3.74 |
| 2 | -2.30% | +2.42 |
| 3 | -2.45% | -2.27 |
| 4 | +4.97% | -2.35 |
| 5 | +1.62% | +2.52 |

Mean paired B/C +1.44%; 95% t CI (df=4) [-3.25%, +6.14%]. Mean paired CPU difference -0.68 ms/window. Three-round early-stop was not triggered.
Output lengths: C total 10441, mean 208.82; B total 9389, mean 187.78; B minus C -1052 total, -21.04 per request. Different sampling outcomes mean these lengths do not establish semantic quality.

Restore: controller reported restored and verified; separate SSH verification found single strata.exe PID 21760, current-best SHA and config SHA as above, AboveNormal, loaded, 3153 slots / 20479 MiB / 20.00 GiB, metrics idle queued 0. Final full inventory found no leftover controller or benchmark processes. Test task disabled priority 2. See restore.json, final_verify.json, preflight.json, task-disabled.json, process-inventory-final.json.

Deviation: initial task registration failed before launch because Windows returned principal as User rather than SID; no API stop occurred. Corrected using actual task principal; full process gate repeated before launch. Quality: float-order-only change; semantic equivalence unconfirmed. No deployment or publication.
