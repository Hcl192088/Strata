# Historical adapt-every audit — 2026-10-18

`PARTIAL_INCONCLUSIVE_DIAGNOSTIC_ONLY`: this audit reuses existing remote artifacts and starts no new process.

The artifacts use the same 366A binary and neuro prompt hash. The only intended runtime difference was `--adapt-every 2` versus `--adapt-every 3`; this is not an adapt-async test.

| Pair | every=3 control | every=2 candidate | Relative result |
|---|---:|---:|---:|
| Original pair | 47.72 tok/s | 46.78 tok/s | −1.97% |
| Recheck pair | 45.24 tok/s | 46.60 tok/s | +3.01% |

One extra candidate run reached 46.36 tok/s without a completed paired control. Another original candidate was excluded for a capacity mismatch, and recheck control02 ended during startup. Therefore the evidence cannot support a pooled mean, stable gain, promotion or adapt-async conclusion. Keep `adapt-every=3` as the controlled setting and do not duplicate this comparison.

Raw roots remain remote at `C:\Users\User\Strata-Adrian-control\runs\adapt-every-20261014` and `...\adapt-every-recheck-20261014`. SHA256 for the identity, command, result, token and post-process metadata files is recorded in the JSON audit; stdout/stderr are retained remotely but were not fully hashed in this unit.

## Coverage

Checked both directory trees, both identity JSON files, representative command JSON files, completed result JSON files, post-process gates, and the existing local report. Not checked: every raw log byte, new benchmark, current API request, or full remote disk.
