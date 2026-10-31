STATUS: DONE (coordinator 2026-10-31 ~06:00)

# S3 MTP expert residency — routing histogram + cost model
DIAG exe 4C0F2F8C… (patch s3-mtp-experts/mtp.diag2.cpp: graph-captured copy of the MTP routed ids to a pinned host buffer, printed after draft sync). First Codex DIAG patch (exe A721AB5D…) was invalid (sync + pageable copy inside graph capture) and was replaced.
Run: 10 Hermes points x 512, 1 block (remote s3\diag\out\block-01-DIAG-r1\engine.log): 1198 drafts, 1924 draft steps (1.61 steps/draft ≈ per window), 19,240 expert calls, 493/512 experts used.

| top-N resident | coverage of calls | cold calls / window | VRAM freed MiB | ruler CPU-work saving ms/w (−1.0..1.2%/100 MiB of 15.41) |
|---:|---:|---:|---:|---:|
| 128 | 65.1% | 5.6 | 506 | 0.78–0.94 |
| 192 | 78.1% | 3.5 | 422 | 0.65–0.78 |
| 256 | 86.7% | 2.1 | 337 | 0.52–0.62 |
| 384 | 97.1% | 0.47 | 169 | 0.26–0.31 |

Costs (serial inside the draft chain): cold expert via PCIe upload 1.38 MB ≈ 70–90 µs each → N=256 ≈ 0.17 ms/w, N=192 ≈ 0.3, N=128 ≈ 0.5; plus a host copy of the cold MTP experts in RAM (169–506 MiB of the 20 GiB RAM cache, 0.8–2.5%) → extra SSD join ≈ 0.05–0.15 ms/w.
Net best ≈ +0.3 ms/w (N=192–256) ≈ +0.8%, below the pre-registered 0.6 ms/w threshold. Additional risk seen in S1: VRAM freed by a smaller MTP head did NOT turn into expert slots (slots stayed 3153), so even the gross saving is not guaranteed without changing slot sizing.
Coverage is in-sample (10 points); train/test split not computed. Verdict: NO_GO, prototype/A-B (S3.4–S3.6) skipped by the brief's threshold rule.
