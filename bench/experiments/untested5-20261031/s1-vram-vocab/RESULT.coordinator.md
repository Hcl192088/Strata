STATUS: DONE (coordinator analysis 2026-10-31 04:2x from remote s1\ab\blocks.json, copied to ab-blocks.json)

# S1 draft vocab A/B (C vs V64 vs V32), 5 rounds rotated, 10 Hermes x 512, original sampling, exe A1E6
| arm | paired tok/s vs C (per round) | mean | 95% CI (df=4) | tok/window | draft ms/w | CPU ms/w | GPU-reach ms/w | ms/window | slots |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| C | — | — | — | 1.786 | 1.76 | 20.01 | 11.68 | 36.89 | 3153 |
| V64 | +1.80, −2.64, −1.91, −5.06, +2.40 | −1.08% | [−5.54, +3.38] | 1.781 | 1.49 | 20.52 | 11.69 | 37.24 | 3153 |
| V32 | −1.23, −5.81, −3.53, −3.68, +1.88 | −2.47% | [−6.64, +1.69] | 1.726 | 1.29 | 19.93 | 11.71 | 36.55 | 3153 |

- Mechanism: V64 cuts draft 0.27 ms/w with tokens/window unchanged (−0.3%) → theoretical max ≈ +0.7%, below noise; tok/s mean −1.08% is CPU-segment noise (CPU 20.52 vs 20.01). V32 cuts draft 0.47 ms/w but tokens/window −3.4% → net negative.
- Slots stayed 3153 in all arms: the ~73–124 MiB freed by the smaller head was NOT turned into expert slots (slot count is fixed before/independent of the MTP head allocation), so the VRAM half of the hypothesis did not happen.
- Coverage (S1.1): prior Hermes output tokens inside current 96.24%, V64 95.88%, V32 88.84%.
- Verdict: NO_GO. Smaller draft vocab gives ≤0.7% even in theory on this workload.
- S1.2 (trace split) skipped; S1.3 VRAM itemization partial (see RESULT.md); Part C: SSH account has no SeLockMemoryPrivilege (read-only check).
