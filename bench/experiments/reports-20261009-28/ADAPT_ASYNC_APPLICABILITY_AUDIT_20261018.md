# Adapt-Async Applicability Audit — 2026-10-18 02:56 +08:00

- The current IQ3 binary supports `--adapt-async 1`, but the live config leaves it absent/default-off.
- The inspected `iq3-ram-adapt-013` directory contains source backups only, not a same-source executable, request harness or raw log.
- The required experiment is three interleaved matched pairs with unchanged runtime identity; it is not measurement-ready.
- Result: `NOT_DEPLOYED_READINESS_ONLY`; no fallback runner, scheduled API replacement, process stop or parameter change.
