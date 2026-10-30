# Current-Best Source Boundary Recheck — 2026-10-18 04:07 +08:00

## Result

`LIVE_DEPLOYMENT.json` and `CAMPAIGN_CURRENT_BEST.json` agree on the controlled IQ3 binary SHA256 `366A355E0E866B12D1793C9D8BE022925305B4560E1AE7DC47F8716C865015E2` and `IQ3_XXS` quantization. The campaign record remains `CONTROLLED_BASELINE_ONLY`; it is not a global-fastest claim and is not promoted as one.

The two recorded IQ2 snapshots remain provenance-only and non-authoritative. They are not recreated or used as a current-best source.

## Boundary

This is a local pointer-consistency result, not a fresh remote liveness or performance result. Before any benchmark, build, resume or deployment, recheck hostname/identity, process gate, source/branch/HEAD/dirty state, binary SHA256 and config SHA256. No remote operation, process stop, temperature change or fallback occurred.

Decision: `PASS_IQ3_CONTROL_POINTERS_MATCH_NO_GLOBAL_CLAIM`.
