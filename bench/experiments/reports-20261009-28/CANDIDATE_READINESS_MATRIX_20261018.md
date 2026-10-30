# IQ3 candidate readiness matrix — 2026-10-18

This is an offline coordination audit. It does not start a benchmark and does not promote a binary.

## Decision

`AUDIT_COMPLETE_NO_SAFE_NEW_RUNNER`. The current 366A binary remains the matched campaign control. `--adapt-async 1` is compiled, but it is not a runnable matched candidate yet. The historical Task025 E3FA result is not reproducible and is not a current-best claim.

| Candidate | Classification | Current decision | Required next gate |
|---|---|---|---|
| Same-layer RAM LRU / 366A | Deployed baseline trial | Keep as controlled baseline; historical output divergence prevents global promotion | New matched current-workload comparison only |
| `--adapt-async 1` | Compiled readiness | `NOT_DEPLOYED`; no same-source runner | Isolated runner, unchanged IQ3 identity, raw logs and output hashes |
| Task025 async-miss / E3FA | Historical candidate | `NOT_REPRODUCIBLE` | Recover exact identity and matched workload before any comparison |
| Upstream overlap path | Outside current image | Unavailable; do not infer from help output | Explicit source plan and authorization |
| Host-core historical result | Rejected historical route | Do not repeat without a new hypothesis | Fresh matched evidence |
| Fetch-admit/lookahead/PF-fused flags | Current configuration | Not an isolated candidate | Explicit plan and new process/binary gate |
| `iq3-ram-adapt-013` | Source backup only | Not a runner or fallback | Retain provenance; require executable, harness and raw-log contract |
| Historical adapt-every 2/3 | Partial existing A/B | Diagnostic only; keep every=3 control | Do not duplicate; require a new hypothesis or isolated adapt-async runner |

## Stop-risk reduction

This matrix prevents three recurring false stops: treating a compiled flag as a completed experiment, treating a historical speed number as current-best, and repeatedly reopening an already-rejected route. These are recorded as candidate-level `NOT_DEPLOYED`, `NOT_REPRODUCIBLE` or `REJECTED` outcomes, not campaign-wide blockers.

## Coverage

Checked the current campaign/live pointers, the 2026-10-18 adapt-async readiness record, the 2026-10-15 feature audit/evidence, and the 2026-10-13 same-layer LRU trial. Not checked: fresh remote processes, new source state, new benchmark, or GitHub connector state; this unit was deliberately local and non-mutating.
