# HOBBIT IQ3 miss-path feasibility — 2026-10-18

Status: `PARTIAL_NO_LOWER_PRECISION_ARTIFACT`.

The local file `D:\strata\state\trace-native-experts.txt` has SHA256 `AE28CF7A2A1C9063C4B55D6C8CF86D4D079DCDDCF597F9E8697C9157D462C0EE`. Its header declares 512 experts and `42,912,972,800` native bytes. The 48 rows use `layer gu_type d_type offset blob_bytes gate_off up_off down_off`; they are layer-level records, but their `blob_bytes` sum is exactly `83,814,400`, which equals `42,912,972,800 / 512`.

Therefore the native size of one expert is verified as `83,814,400` bytes (`79.9255 MiB`), and a 20 GiB budget is at most 256 such expert-blob equivalents if it were entirely available to expert blobs. That is a capacity calculation, not proof of spare RAM for a duplicate copy. The actual IQ3 pack has only `experts.bin`, `native_experts.txt`, and `conversions.json` with `tensors=[]`; no IQ2/Q2 lower-precision expert artifact was found. I deliberately did not invent a compression ratio or build a new quantized copy. No quantization, RAM allocation, process, source, schedule or remote benchmark was changed.

Next: obtain an actual lower-precision expert artifact or an explicitly authorized conversion/parity plan before any HOBBIT implementation. In the meantime, continue with Fate provenance or a new DoMoE trace matrix; this is a soft partial result, not a campaign blocker.
