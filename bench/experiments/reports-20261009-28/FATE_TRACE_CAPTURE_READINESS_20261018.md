# Fate Trace Capture Readiness — 2026-10-18 02:21 +08:00

## Result

The real IQ3 source has a valid one-shot capture mechanism:

```text
--dump-routing PATH
```

`src/program/generate.cpp` documents that it writes routed expert IDs and weights per layer and position. The implementation explicitly requires the expert pool and rejects `--no-pool`; this is an important safety gate. `tools/make_profile.py` confirms the record format as `layer, k, k expert IDs, k weights`.

The remote process gate was clear and the live binary identity remained controlled, but no matching remote `.bin` trace or isolated capture runner was found. The current local `hermes-routing.frozen-01.bin` therefore remains an invalid partial input and was not repaired or substituted.

## Decision

Fate is still candidate-specific `PARTIAL`, but the failure is now precise: the source capture flow exists; an isolated runner, exact model/config identity and frozen prompt/seed are still missing. No capture, benchmark, source edit, scheduled-API change, process stop, temperature change or fallback occurred.

## Coverage

Checked the fresh process gate, live source help and implementation, the trace parser, existing reproduction guidance and remote `.bin` inventory. Did not start a model run or construct an unapproved runtime command.

## Tooling note

One composite SSH query returned no usable stdout and was not treated as evidence. A narrower encoded read-only query was rerun after a fresh process gate and succeeded. No remote side effect or fallback was used.
