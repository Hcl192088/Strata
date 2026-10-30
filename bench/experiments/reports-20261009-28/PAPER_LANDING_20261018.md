# IQ3 paper landing status — 2026-10-18

This is a local coordination record. It does not claim that a remote paper implementation or benchmark has been completed.

## Execution gate

- Remote identity: `DESKTOP-LKMLUPC\\user` verified.
- Remote process gate: no matching Strata/Python/benchmark/build/CUDA compilation process was found during this check; no process was stopped.
- Scheduled task: `Strata-Task020-API` exists; current task state was returned as code `3` by `Get-ScheduledTask`.
- IQ3 binary recheck: `C:\Users\User\Strata-Adrian-control\runs\ram-lru-20261013\build\strata.exe`
- IQ3 binary SHA256: `366A355E0E866B12D1793C9D8BE022925305B4560E1AE7DC47F8716C865015E2`
- Source HEAD: `61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406`
- Canonical clone `main` HEAD was separately rechecked as `1b90d1cdc7193874440e7c684f40c8ae7808b496`; the live binary identity is tied to the detached `runs\\ram-lru-20261013\\source` build tree above.
- Existing dirty source: `include/strata/core/expert_source.hpp`, `src/core/expert_source.cpp`
- Remote benchmark status: **NOT STARTED**. The previously unresolved identity is now recorded as a controlled baseline only; every future remote run must revalidate the same SHA before starting. This does not claim global fastest.

## Fate / cross-layer gate prediction

Status: `BLOCKED_INPUT_INTEGRITY`

The existing offline SRP/SCH-style analyzer was run against the local frozen routing trace and stopped at the strict parser:

- Trace: `D:\strata\state\hermes-routing.frozen-01.bin`
- Trace size: `20,742,144` bytes
- Trace SHA256: `87CA2E3EA201E4AFEB27C415BBFC4927D67EFFC4ECFC6D97F1F3E94AA291509D`
- Failure: `ValueError: partial record payload`
- Output: no `srp-sch-20261018.json` or `.md` was produced.

The old `LUNA-20261012-027.ram-screening-20261013.md` claims a different trace SHA and complete windows. That discrepancy is recorded as an input-provenance mismatch; this run does not repair, truncate, or substitute the trace.

The local analyzer was hardened to accept the actual IQ pack v3 layer-level `native_experts.txt` schema; a 48-layer × 512-expert unit check passed. The retry still fails only at the routing trace payload, so the remaining Fate block is input integrity rather than expert-size parsing. Scoped local/remote provenance checks found no additional complete routing trace. This is a Fate-only input block, not a campaign-wide block.

## DoMoE / domain-profile routing

Status: `PARTIAL_PROFILE_CATALOG_NO_CURRENT_IQ3_TRACE`

Existing local research already covers a limited profile-transfer analogue:

- Source report: `D:\strata\reports\Strata_筆記learned_profile轉移測試_2026-10-05.md`
- Profile: `learned-heart.bin`
- Profile SHA256: `AA28BA0800A598DE0D83EBD83E918E2736BB2F4AB6750DB8AA72461E5829510F`
- Workloads: heart-trained profile held out on 神解 and anti-hypertensive.
- Capacity-matched result: 神解 approximately `+6.6%` decode tok/s; anti-hypertensive approximately `+2.8%`.
- Evidence limit: only one held-out topic per transfer direction and two runs per arm; this is not a domain classifier, semantic routing table or DoMoE reproduction.
- Current-source audit: static `--expert-profile` load/save exists, but no domain classifier, routing-table selector or semantic dispatch was found in the scoped `src`, `include` and `serve` scan.
- Profile catalog: 10 historical `48x512` profiles are structurally usable by the current profile parser; one `48x256` coder profile is incompatible. The current IQ3 model root contains no profile artifact, and no complete routing trace is available.

Decision: keep the historical transfer as prior evidence only. The zero-measurement, non-deploying candidate matrix is now recorded in `DOMOE_CANDIDATE_MATRIX_20261018.json` and the six-direction gate is recorded in `PAPER_DIRECTION_GATE_MATRIX_20261018.json`; no profile is copied, converted, selected by semantics or sent to the live IQ3 API. Do not claim current-IQ3 throughput or DoMoE reproduction.

## HOBBIT / mixed-precision miss path

Status: `PARTIAL_NO_LOWER_PRECISION_ARTIFACT`

The authoritative IQ3 metadata was rechecked on `DESKTOP-LKMLUPC`: 512 experts, `42,912,972,800` total native bytes, and `83,814,400` bytes per expert (`79.9255 MiB`) because the 48 layer records sum exactly to that value per expert. The pack has no lower-precision expert artifact; `conversions.json` has `tensors=[]`. A 20 GiB budget is at most 256 native expert-blob equivalents if entirely available to experts, but this does not establish spare RAM for a duplicate copy. No quantization change, extra RAM allocation, live API replacement or remote benchmark was made in this pass.

Decision: do not invent a compression ratio or start a conversion. HOBBIT remains a soft partial result until an actual lower-precision artifact or an explicitly authorized conversion/parity plan exists.

## ReMoE / CommitMoE / FloE

Status: `RESEARCH_CANDIDATES_NOT_LANDED`

- ReMoE: requires router fine-tuning and model conversion/quality validation; not a cache-only change.
- CommitMoE: changes expert execution/selection semantics; must be evaluated as a quality-versus-speed experiment, not ordinary cache tuning.
- FloE: compression/transfer path has the highest implementation cost and is not justified before IQ3 trace locality and miss-path feasibility are established.

## Verified paper sources

The source and venue boundary is recorded in `PAPER_SOURCE_VERIFICATION_20261018.json`. In particular, the consulted authoritative source for Fate is arXiv `2502.12224` dated 2025-02-17; `WWW 2026` is not treated as verified metadata. Paper-reported speedups, hit rates and compression ratios remain external claims and are not current Strata IQ3 evidence.

## Decision for the next safe run

1. Revalidate the controlled IQ3 baseline identity before any remote run.
2. Obtain or regenerate a complete routing trace through the approved Strata flow; do not use the truncated local file as a substitute.
3. Re-run Fate offline only after trace hash and parser completeness agree with the report metadata.
4. Use the existing learned-profile report and `DOMOE_PROFILE_CATALOG_20261018.json` to maintain one non-duplicative domain/profile matrix. Populate measurement fields only after a complete trace or an explicitly approved matched IQ3 run exists.
5. Consider HOBBIT only after an actual lower-precision artifact and a measured IQ3 miss-path memory/quality budget exist; continue other paper directions meanwhile.
6. Use `CANDIDATE_READINESS_MATRIX_20261018.json` to avoid repeating rejected, unreproducible or non-current-binary routes; prepare an isolated adapt-async runner contract before any remote A/B.
7. Treat the historical adapt-every 2/3 comparison as diagnostic-only: two completed pairs disagree, so keep every=3 and do not rerun it.
8. Keep adapt-async at readiness-only: the inspected `iq3-ram-adapt-013` directory is source-backup-only, not a runner and not a fallback.

## Coverage

Checked this pass: `AGENTS.md`, `STRATA_GITHUB_AUTO_HANDOFF.md`, the new local indices, all `LUNA-20261012-027*.md` local reports, the IQ3 live audit/evidence, the three local trace/profile inputs, the existing profile-transfer report, the offline analyzer execution, the scoped current-source DoMoE audit, the three-root remote profile catalog, the candidate readiness audit, the adapt-async remote preflight, and the two adapt-every historical artifact roots.

Not checked: a fresh GitHub connector snapshot, every byte of remote raw logs, a new routing capture, or any remote benchmark. No source, model, process, schedule, temperature or GitHub state was modified.
