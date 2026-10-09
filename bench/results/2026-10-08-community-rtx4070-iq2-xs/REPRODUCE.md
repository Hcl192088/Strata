# Reproduce the RTX 4070 12 GB / 32 GB DDR4 IQ2_XS result

**Scope:** Windows 11, NVIDIA RTX 4070 12 GB, 32 GB DDR4-3200, i5-12600KF.
Historical measurement: 2026-10-08; five independent CLI processes; 28,912 prompt
tokens, 1,024 generated tokens; median **48.23 accepted decode tok/s** (E4/S24).

This is a **reproduction package**, not a claim that any 4070 gets 48.23 tok/s.
Workload content, disk/PCIe characteristics, runtime cache state, compiler
toolchain, and the 20 GiB resident-memory policy can affect performance.
The reference engine is a modified Adrian-derived build, **not stock Strata**.

## 1. Exact source code (published, full source tree)

Source: [Hcl192088/Strata, pinned IQ2 benchmark engine snapshot](https://github.com/Hcl192088/Strata/tree/benchmark-iq2-source-9ec3806)

Immutable source commit:

```text
9ec3806058cf32ab27a55e4377daf7cf0d087dec
```

A full GitHub archive is also available from
`https://github.com/Hcl192088/Strata/archive/9ec3806058cf32ab27a55e4377daf7cf0d087dec.zip`.
The commit is from the [AdrianBM96/Strata3060](https://github.com/AdrianBM96/Strata3060)
line. The source branch above is a **verbatim tree pinned to that historical
commit**, not a reconstruction based on latest upstream and not a cherry-pick.
It is deliberately kept separate from this benchmark-data PR, to avoid
improperly presenting Adrian's engine modifications as new upstream patches.

On Windows PowerShell:

```powershell
git clone --single-branch --branch benchmark-iq2-source-9ec3806 https://github.com/Hcl192088/Strata.git .\strata-iq2-source
cd .\strata-iq2-source
git rev-parse HEAD
# Must print 9ec3806058cf32ab27a55e4377daf7cf0d087dec.
```

The source's `setup.py` pins a llama.cpp dependency commit
`3cf03257f219afbe7334045ff7c6a06ac68c627d`, Hugging Face model revision
`ed59f92082b1e93c0e96d60a8b11aab089b52f09`, and Python dependency
versions through `requirements.txt`.

## 2. Build and prepare the model

On a similar Windows/NVIDIA PC with sufficient free SSD storage, Git,
Python 3.10+, Windows Visual Studio Build Tools, and NVIDIA CUDA Toolkit,
the historical source has its own installer/build and pack-generation pipeline:

```powershell
py -3 setup.py --family qwen --model IQ2_XS --context 100000 --low-ram resident --build --no-start --yes
```

This invokes the pinned source's own `build_engine` and model setup logic. For
RTX 4070 the target compute capability is `sm_89`. The build uses CMake/Ninja,
CUDA and llama.cpp/ggml. The official full-model GGUF is fetched by the source
setup from the pinned ISTA-DASLab repository revision. Its `iq_pack.py` can
generate `packs/iq2_xs` including `experts.bin`; the source's
`mtp_fetch.py`, `mtp_pack.py`, `mtp_rt.py` prepare `mtp/rt`.

**Important:** This setup produces a *candidate*, not an attested byte-for-byte
replica of the measurement. Verify every SHA-256 in `provenance.json`; on
mismatch, inspect toolchain/pack provenance rather than claiming an exact run.
The historical binary's Windows compiler, CUDA toolkit and build flags were
not captured sufficiently to promise identical executable bytes.

## 3. File layout and non-redistributable / missing evidence

The public `provenance.json` specifies every expected relative path, byte
count, and SHA-256 for the two GGUF shards; pack files; tokenizer; MTP tensors;
expert profile; and pretokenized prompt.

Use **one data root** containing these paths:

```text
<data-root>/
  models/IQ2_XS/<two original GGUF shards>
  packs/iq2_xs/...
  mtp/rt/...
  profiles/learned-heart.bin
  prompts/neuro.tokens
```

The setup program may place these resources in a neighboring
`Strata-data` directory. Place/copy/link the resources so the paths above
resolve under the selected `--data-root`. Do not inadvertently duplicate the
large GGUF files if disk space is tight.

**Current public evidence boundary:**

| Required to match the *exact historical run* | Public availability |
| --- | --- |
| Complete modified engine source at exact commit | **Yes**, pinned source branch above |
| Model repository + revision and download/preparation code | **Yes** |
| Full run command and environment | **Yes**, provenance manifest |
| Per-file hashes and sizes | **Yes**, provenance manifest |
| Original `learned-heart.bin` expert-cache profile bytes | **Not uploaded** (hash only) |
| Original 28,912-token `neuro.tokens` prompt bytes | **Not uploaded** (hash only) |
| Exact prebuilt `strata.exe` bytes | **Not uploaded** (hash only; can rebuild from source) |
| Original per-run stdout/stderr/command JSON files | **Not uploaded** (retained on test machine) |
| GPU in-run peak VRAM telemetry | **Not measured** |

The private prompt may include sensitive content; **do not publish or upload it
without review**. A different prompt or profile can benchmark the same engine
and hardware but **does not replicate the reported 48.23 tok/s workload**.
A successful source build plus hardware match is not by itself an exact-speed
reproduction.

## 4. Validate inputs and run five measurements

The companion [reproduce.py](reproduce.py) requires only Python's standard
library. It does not download or upload files. Run it from this report's directory
(or use its full path). Provide the absolute paths to the installed engine and
the assembled data root.

```powershell
$Data = "D:\strata-iq2-data"
$Exe = "D:\strata-iq2-source\engine\strata.exe"
$Src = "D:\strata-iq2-source"

# Full SHA-256 preflight. Run separately from timed benchmarks: hashing
# ~100 GB immediately beforehand can heat the operating-system disk cache.
py -3 .\reproduce.py check --data-root $Data --engine $Exe --source-root $Src

# After a controlled cache-state reset, run five sequential processes.
# Every attempt retains its own stdout/stderr, exit code and GPU snapshots.
py -3 .\reproduce.py run --data-root $Data --engine $Exe --source-root $Src --runs 5 --out "D:\strata-iq2-runs\repeat01"
```

Both actions **stop on missing or mismatched artifacts**. If your locally
compiled executable has a different binary SHA-256 even though the Git source
commit matches, you may add `--allow-binary-mismatch`, but that is then a
**same-source recompile**, not a byte-identical engine run. This distinction
will be printed and retained in the run output. `run` uses size-only asset
checks by default so it does not heat all files right before measuring. Use the
separate full-hash `check` command beforehand.

The harness applies *exactly* the CLI argument vector and six environment
overrides recorded under `primary_command` in `provenance.json`, rather
than guessing current defaults. It collects:

- `run-XX/command.json`: invoked command and environment overrides
- `run-XX/stdout.log` / `stderr.log`: full engine telemetry
- `run-XX/gpu-before.csv` / `gpu-after.csv`: run-boundary snapshots, **not peak VRAM**
- `run-XX/summary.json`: parsed `decode` line, token count, exit code
- `report.json`: valid-run count, mean/median/range and historical reference

All results remain local. The stdout contains token IDs from the full prompt
and answer and **must be reviewed before public upload**.

## 5. Comparison rule

Compare *accepted decode tok/s*, using the `decode ... tok/s` line emitted
by this exact engine; do not combine prompt processing time or speculative
proposals into the denominator. Use the per-run data and report the number of
valid samples, median and range. Any early termination, nonzero exit or output
token count different from 1,024 is reported as a failed run, not silently
excluded as a fast result.

Reference E4/S24 vector: `48.23, 47.98, 49.44, 48.83, 46.92` tok/s;
median `48.23` tok/s. The frozen E4/S32 reference median is `47.76` tok/s.
The E4/S24 improvement (`+0.98%`) **did not pass** the original `+1%`
promotion criterion.

**Before claiming independent exact reproduction**, make the missing prompt and
profile available (or document a deterministic procedure yielding the same
SHA-256), match the remaining artifact hashes, capture the build toolchain and
cache-state rules, and execute this package independently. Until then this is
a **reproducible source/build/test *procedure* with an explicit original-data
availability gap**, not a fully independently reproducible benchmark.
