# Adapt-async remote preflight — 2026-10-18

`PREFLIGHT_COMPLETE_RUNNER_NOT_FOUND`. This was a read-only identity and runner-discovery check; no benchmark, source edit, process stop or scheduled API change occurred.

## Verified

- Strict SSH hostname: `DESKTOP-LKMLUPC` via `User@<desktop-tailscale-ip>`.
- Remote `C:\Users\User\Strata-Adrian-control\AGENTS.md` was read.
- No relevant `strata.exe`, Python benchmark, build or CUDA process was found. The remaining `sshd` entries were services/SSH wrappers; a transient command wrapper had already exited when classified.
- The canonical clone is `main` at `1b90d1cdc7193874440e7c684f40c8ae7808b496`.
- The actual live binary build source is the detached `runs\ram-lru-20261013\source` at `61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406`, with only the two known RAM-LRU dirty files.
- Binary SHA256 is `366A355E...015E2`; scheduled config SHA256 is `C805B120...FEA18`; task `Strata-Task020-API` returned state code `3`.

## Runner discovery

The remote `runs` listing contained `iq3-ram-adapt-013`, so it was inspected rather than assumed usable. It contains only:

`source-backup\expert_source.cpp`, `source-backup\expert_source.hpp`, and `source-backup\generate.cpp`.

There is no executable, isolated serve launcher, exact request harness or raw log in that directory. It is therefore source backup evidence, not a same-source runner.

## Decision

Keep `--adapt-async 1` at `NOT_DEPLOYED` and use the existing [runner contract](D:/strata/state/ADAPT_ASYNC_RUNNER_CONTRACT_20261018.md) for any future run. Do not use another historical directory as fallback, and do not touch the scheduled API.

The first local SSH inventory attempt had a quoting error and no remote side effect. The same read-only inventory was corrected and succeeded; this is recorded as a tooling retry rather than a process blocker.

## Coverage limit

The conclusion is scoped to the remote `runs` directory listing and the inspected `iq3-ram-adapt-013` contents. This is not a full-disk claim and not a benchmark result.
