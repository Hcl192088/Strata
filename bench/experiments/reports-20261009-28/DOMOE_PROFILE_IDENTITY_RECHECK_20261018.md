# DoMoE Profile Identity Recheck — 2026-10-18 02:25 +08:00

## Result

Fresh remote read-only inspection found all 10 catalogued profiles. Every file matched its recorded SHA256, `STRP` v1 format, `48x512` dimensions and `24,576` ranked pairs. The current binary/source identity was also recorded: binary `366A355E...015E2`, source HEAD `61b3fb5...`.

This refreshes provenance only. It does not prove that any profile is suitable for the current IQ3 workload, and it does not implement DoMoE's domain selector.

## Overlap analysis status

Two attempts to calculate top-K ordering overlap failed at the remote PowerShell collection/serialization layer and returned no usable metrics. No overlap number is recorded, and this failure did not change the remote state. The successful identity query was narrower and is the only evidence used here.

## Decision

Keep the DoMoE matrix at zero measurements. Do not copy, convert, deploy or semantically select any historical profile into the live IQ3 API.

## Coverage

Checked all 10 catalogued profile artifacts, hashes and structural headers. Did not claim ordering similarity, domain generalization, current IQ3 throughput or selector behavior.
