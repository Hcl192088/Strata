# Adapt-async historical pair reanalysis — 2026-10-18 04:31 +08:00

Fresh read-only inspection found 24 existing artifacts under the remote `iq3-ram-adapt-013\bench` directory: three control/candidate pairs with JSON metadata and raw stdout/stderr/log files. The earlier local conclusion “no raw log” was too strong; the correct conclusion is “raw historical pairs exist, but the candidate executable is missing now and the pair binaries are not the current controlled IQ3 binary.”

Observed historical decode values:

- Pair 1: control 33.13, candidate 30.11 tok/s, −9.115%.
- Pair 2: control 35.59, candidate 35.81 tok/s, +0.618%.
- Pair 3: control 36.52, candidate 36.54 tok/s, +0.055%.
- Mean: control 35.08 vs candidate 34.153 tok/s (−2.642%); median: control 35.59 vs candidate 35.81 (+0.618%).

The candidate binary SHA was `C2890861...F9AA7607A` and no longer exists. The historical control was `59292D5C...FFAECEC3`; the current controlled IQ3 binary is `366A355E...865015E2`. Pair metadata also does not carry full effective temperature/sampling/context/KV/model identity or output/token parity. Logs record page-locking refusal (“out of memory”) while processes still exited 0.

Decision: diagnostic-only historical evidence, not a current IQ3 result and not eligible for promotion. No process was launched or stopped, and no parameter changed.
