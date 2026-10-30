# adapt-async readiness — 2026-10-18

Status: `READINESS_VERIFIED_RUNNER_NOT_READY`.

The current controlled IQ3 binary (`366A355E...015E2`) accepts `--adapt-async 1` in `generate --help`. The live scheduled config does not set the flag, so the current baseline remains blocking/adaptive-off. Fresh remote checks found no matching Strata/Python/benchmark/build process, and the source identity remains HEAD `61b3fb5d...` with only the two pre-existing RAM-LRU dirty files.

The candidate is not benchmarked in this unit. The current remote run tree has no same-source adapt-async runner or exact request harness. The live API is launched by `start_task020_api.ps1`; replacing or reconfiguring that scheduled service would be a deployment change, not a safe readiness check. A runner from a different historical source/build would invalidate matched comparison, so it is not used as fallback.

Required future gate: an isolated `--serve` process, unchanged IQ3 model/prompt/temperature/sampling/context/KV/resident settings, startup resident 20 GiB/20479 MiB and 3153 GPU slots, successful async exchange/pinned path, actual adaptive swaps, three interleaved matched pairs, output hashes/parity, and complete raw logs on the remote host. Until that runner exists, this is `PREPARE_ONLY`, `NOT_DEPLOYED`, and a soft blocker only.
