# Fate Isolated Capture Manifest — 2026-10-18 02:27 +08:00

## Purpose

This manifest freezes the safe shape of a future IQ3 one-shot routing-trace capture. It is preparation only; it did not start a remote process or touch `Strata-Task020-API`.

The only candidate change is:

```text
--dump-routing <new sibling raw trace path>
```

All other config arguments, binary/source/model identity, temperature, sampling, context and KV settings must remain unchanged. The expert pool must remain enabled; `--no-pool` is forbidden by the live source implementation.

## Gates before execution

- fresh strict hostname/identity and process gate;
- binary/source/config/model SHA identity match;
- approved sibling isolated runner or one-shot launcher;
- frozen representative prompt, seed and request hash;
- new raw output path, never the known partial trace;
- raw trace retention and SHA256 capture.

The trace is accepted only when the `layer,k,expert IDs,weights` records parse exactly to EOF with no partial tail. Even a valid trace is diagnostic input; it does not itself prove throughput, quality or paper reproduction.

## Current decision

`READY_FOR_FUTURE_GATED_PREPARATION_ONLY; NOT_READY_TO_EXECUTE`.

The missing runner and frozen prompt identity remain candidate-specific readiness gaps, not campaign-wide blockers.
