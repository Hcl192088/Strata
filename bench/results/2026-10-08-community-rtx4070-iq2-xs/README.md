# Community benchmark (preliminary): Flash-Next IQ2_XS on RTX 4070 12 GB / 32 GB DDR4

**Status: draft; measurements transcribed from the operator's contemporaneous benchmark-session records, not yet independently revalidated against the original per-run JSON/logs.** This is a benchmark report, not an engine patch.

Measured **2026-10-08** by [Hcl192088](https://github.com/Hcl192088), on one consumer GPU with 12 GB installed VRAM and 32 GB DDR4 system RAM. The most interesting result is a **48.23 accepted-decode-tok/s median over five runs** for one adaptive-cache candidate. A separate, previously frozen `CURRENT_BEST` configuration reportedly had a **47.76 tok/s median over five runs**. Neither number should be interpreted as end-to-end request speed or as a universal hardware ranking.

## Hardware

| Item | Recorded value |
| --- | --- |
| GPU | NVIDIA GeForce RTX 4070, **12 GB installed VRAM**, single GPU |
| CPU | Intel Core i5-12600KF |
| RAM | 32 GB DDR4-3200 |
| OS | Windows; precise release/build not yet extracted from run logs |
| Storage, PCIe, GPU driver, power limits | Not yet verified |
| VRAM consumption during inference | **Not yet verified**. Installed VRAM capacity is *not* a measurement of peak VRAM use. |

**Memory terminology:** The local experiments also refer to approximately 18–20 **GiB of resident host RAM** for expert tiers. This is **system memory**, **not 18–20 GiB VRAM**. Do not infer GPU memory usage from that number.

## Engine, model, and configuration

- Model family / quantization: Qwen3.8-Flash-Next, **IQ2_XS**, native/packed execution with MTP. Exact GGUF filenames, repository revision, pack and tokenizer hashes are **pending extraction** from the archived run commands.
- Engine: locally built **Adrian-derived Strata** executable; exact source commit, full binary SHA-256, compiler and CUDA versions **not yet pinned to the five-run evidence**. It must not be presented as an unmodified upstream release.
- Benchmark objective: **accepted decode tokens per second**, not speculative proposals/s, prompt throughput, or total request tok/s.
- The contemporaneous test-session report records **1,024 generated/accepted output tokens** and exit code 0 with no residual engine processes for each of the five E4/S24 candidate runs. **1,024 is the output length, not the configured context window.**
- During this optimization campaign the working configuration used `q4_0` KV, CPU affinity `all`, an enabled host worker, and `STRATA_LOOKAHEAD=0`; the full effective settings must still be checked against each `command.json`. Do not treat this abbreviated list as an exact launch command.
- Adaptive-cache notation **E4/S24** means `--adapt-every 4 --adapt-swaps 24`. The comparison candidate E5/S32 uses `--adapt-every 5 --adapt-swaps 32`.
- Exact prompt bytes/hash, actual prompt length, context limit, sampling state, cache warm/cold policy, active resident memory policy, expert slots, and full environment remain **not verified for these archived five-run samples**.

## Method and observed measurements

The operator's recorded workflow ran separate sequential `strata.exe` processes, captured standard output/error and exit status, and checked for leftover engine processes. The source artifacts were recorded locally under working directories including `strata_current_best_phases_20261008` and `rtx4070_exact_benchmark_20261008`. These paths are **provenance leads**, not public links or independently verified artifact hashes.

All per-run numbers below are **as reported by the experiment agent**. See [transcribed-runs.csv](transcribed-runs.csv), which intentionally identifies its source as a *transcript*, not as raw telemetry.

| Test phase / configuration | Accepted decode tok/s, each run | n | Median | Mean | Interpretation |
| --- | --- | ---: | ---: | ---: | --- |
| Later E/S sweep: E4/S24 | 48.23, 47.98, 49.44, 48.83, 46.92 | 5 | **48.23** | 48.28 | Best observed candidate in this sweep, **not promoted** |
| Later E/S sweep: E5/S32 | 47.32, 48.23, 49.37, 46.57, 46.84 | 5 | 47.32 | 47.67 | Comparison candidate |
| Earlier adaptive sweep: E4/S32 | 46.71, 46.39, 48.97 | 3 | 46.71 | 47.36 | Different optimization phase; do not combine with later sweep |
| Earlier adaptive sweep: E8/S96 | 46.24, 44.97, 46.92 | 3 | 46.24 | 46.04 | Earlier phase only |

A separately maintained `CURRENT_BEST` was reported as **median 47.76 tok/s (n=5)** at the time of the E/S sweep, but the full five-point vector is **not present in the transcript source used for this draft**. It therefore has **not** been added to the per-run CSV. E4/S24's median advantage is **+0.98%** relative to that historical reference, below the campaign's **+1% promotion rule**. The control configuration remained E4/S32; it is incorrect to announce E4/S24 as a promoted production winner.

A single candidate run reached **49.53 tok/s** during a later adaptive-decay screen (`decay=0.50`), but **n=1 is not a reproducible performance result** and it is excluded from the summary above.

### What these results do and do not show

- They show reported **decode** performance close to 48 accepted tok/s on a PC with **12 GB physical VRAM and 32 GB DDR4**.
- They **do not** establish a 48 tok/s speed at any particular full prompt/context size until the original command metadata is recovered. Context capacity and actual processed prompt length must be stated separately.
- They **do not** establish model-answer quality or a general performance advantage versus another GPU or a newer upstream release.
- They are **not** evidence that 48 tok/s is a stable minimum: the five-run E4/S24 range was **46.92–49.44 tok/s**.

## Evidence still required before this PR is ready for review

1. Recover the specific five-run `command.json`, `stdout.log`, `stderr.log`, `exit.txt`, and any `result.json` for E4/S24 and frozen CURRENT_BEST. Validate metric extraction, actual token count, exit status and cache/residency state against the original bytes, and attach **sanitized per-run JSON or CSV**.
2. Pin the complete binary SHA-256, source commit/build provenance, driver/CUDA versions, exact IQ2_XS model/pack/MTP/tokenizer/profile hashes, CLI arguments and environment.
3. Publish the measured prompt length and hash or a redistributable synthetic replacement, configured context limit, context already reused, KV type/residency, expert cache size, and *measured* peak RAM/VRAM if available.
4. Distinguish cold and warm cache experiments, and repeat with an independently reproducible prompt only if the original evidence cannot establish comparability. Preserve raw unsuccessful runs as failures.
5. Update this report, then mark the PR ready. Keep benchmarking documentation **separate** from any source-code optimization PR.

The submitted numbers are **historical experiment-session reports**; this preliminary draft does not contain all provenance needed for a fully reproducible benchmark. Please review the limitations rather than treating the figures as confirmed upstream benchmarks.
