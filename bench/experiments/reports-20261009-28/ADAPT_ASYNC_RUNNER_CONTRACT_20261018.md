# Adapt-async isolated runner contract — 2026-10-18

`PREPARE_ONLY_RUNNER_CONTRACT_READY`: this contract prepares a future test. It does not create a remote runner, touch `Strata-Task020-API`, or claim a speedup.

## Frozen comparison

The control is the verified IQ3 campaign binary `366A355E...015E2`, source HEAD `61b3fb5d...46406`, config SHA `C805B120...FEA18`. The candidate may change exactly one thing: add `--adapt-async 1`. Model, IQ3 pack, profile, prompt, seed, temperature, sampling, context, KV, resident budget, workers and adaptive settings stay unchanged.

## Gates before any run

1. Revalidate hostname, remote identity, remote `AGENTS.md`, source branch/HEAD/dirty state, binary/config/model hashes and all relevant processes.
2. Use a sibling isolated `--serve` runner. The scheduled API remains untouched.
3. Freeze the exact prompt/request/seed/hash. The target is the existing neuro workload with 1024 generated tokens, not an improvised prompt.
4. Require startup evidence for 20 GiB/20479 MiB resident, 3153 GPU slots, 9 workers, an explicit async startup line, a successful exchange/pinned path and actual swaps.

## Measurement and decision

Run three interleaved matched control/candidate pairs. Record accepted decode tok/s, timing, CPU/pool metrics, adaptive rounds/swaps, file-tier traffic, hit/error, RAM and output hashes/parity. A paired median gain of at least 3% with healthy quality/stability earns two confirmation pairs; otherwise record `REJECT` or `NOT_APPLICABLE`. Missing raw logs, request drain, output quality or identity evidence is not a promotion.

No fallback runner, source edit, temperature change, process stop or live scheduled API change is allowed under this contract. Until the fresh remote gate and isolated runner exist, the status remains `NOT_DEPLOYED`.

## Coverage

Derived from the current adapt-async readiness record, feature audit/evidence, live IQ3 pointer and campaign rules. No fresh remote process scan or benchmark was performed in this preparation unit.
