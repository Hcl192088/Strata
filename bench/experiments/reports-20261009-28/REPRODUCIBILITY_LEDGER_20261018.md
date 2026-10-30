# IQ3 paper campaign reproducibility ledger — 2026-10-18

This is the single local index for the current six-direction paper campaign. It is a coordination ledger, not a copy of remote Strata source, models, raw logs or benchmark artifacts.

## Control identity

The controlled IQ3 baseline is `DESKTOP-LKMLUPC`, binary SHA256 `366A355E0E866B12D1793C9D8BE022925305B4560E1AE7DC47F8716C865015E2`, actual build-source HEAD `61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406`, config SHA256 `C805B1206CDD23B22EE3CC66A80C52014EF9904CDB4314A6C6A17B8E00FFEA18`, IQ3_XXS, 20 GiB resident budget, 3153 GPU slots, 9 workers, adaptive every 3 / max 16 swaps / decay 0.60. The canonical clone is separately `main` at `1b90d1cdc7193874440e7c684f40c8ae7808b496`; the live binary comes from the detached run-tree source, not canonical main. The source has two pre-existing dirty RAM-LRU files. This is a matched campaign control, not a global-best claim; every remote run must revalidate it.

## Direction status

| Direction | Current state | Decision | What is still missing |
|---|---|---|---|
| Fate | Current local trace has partial payload; old report hash conflicts | Diagnostic only | Complete approved trace with matching provenance |
| DoMoE | 10 historical 48x512 profiles cataloged; current source has static profile load/save only; no current IQ3 trace | Partial, data-only | Candidate matrix now; matched IQ3 trace/run and domain selector evidence still missing |
| HOBBIT | Native per-expert size verified; no low-precision artifact | Feasibility only | Actual lower-precision artifact, parity, quality and miss-path budget |
| ReMoE | Requires router training/conversion | Research candidate | Authorized training and quality validation |
| CommitMoE | Changes expert-selection semantics | Research candidate | Explicit quality-preserving selection test |
| FloE | Compression/transfer architecture | Research candidate | Locality ceiling and transfer budget |

## Anti-stop rules

The four current soft blockers are direction-specific: Fate partial trace, DoMoE no current IQ3 trace/selector, HOBBIT no lower-precision artifact, and adapt-async no same-source isolated runner. They do not stop the campaign: preserve their evidence, record the failed layer, and move to the next offline unit. A hard stop is reserved for unverified remote identity, binary mismatch, an interfering process, uninterpretable data with no same-scope evidence, or an unapproved destructive/semantic change.

Every future result must include the full identity contract (binary/source/config/model/prompt/seed/temperature/sampling/context/KV/cache), matched accepted decode tok/s, run count, hit/error, quality/parity, process/resource gate, raw remote path and SHA256, and a decision. Temperature and fallback policy remain unchanged.

The verified paper metadata and method boundaries are in `PAPER_SOURCE_VERIFICATION_20261018.json`. Fate's consulted authoritative source is arXiv 2502.12224; its WWW 2026 venue label remains unverified. External paper numbers are not Strata evidence.

## Next safe phase

1. Preserve Fate provenance and obtain a complete approved trace when the capture flow is available.
2. Maintain the existing `PAPER_DIRECTION_GATE_MATRIX_20261018.json` and `DOMOE_CANDIDATE_MATRIX_20261018.json` as a non-duplicative DoMoE multi-domain/profile matrix with measurement fields explicitly empty; do not repeat the same two IQ2 held-outs or imply that catalog structure is a benchmark.
3. Keep HOBBIT at feasibility until a real lower-precision expert artifact exists.
4. Use `CANDIDATE_READINESS_MATRIX_20261018.json` to audit compiled-but-unmeasured cache/admission candidates offline; keep adapt-async readiness-only until a same-source isolated runner exists; any benchmark must re-run the remote process/binary gate.
5. Keep the historical adapt-every 2/3 audit diagnostic-only; do not rerun it because the completed pairs disagree and the third pair is incomplete.
6. Update this ledger, the candidate matrix, and `AUTOMATION_PROGRESS.json` after every work unit.
