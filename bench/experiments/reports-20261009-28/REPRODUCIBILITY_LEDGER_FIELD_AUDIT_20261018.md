# Reproducibility-ledger field audit — 2026-10-18 04:25 +08:00

This audit answers the practical question: what must be recorded before any future IQ3 candidate can be compared without stopping or confusing the campaign?

- Every direction now has an explicit identity/evidence/policy status. Zero directions are measurement-ready; this is not a campaign-wide block.
- Fate has a complete route-ID trace and offline diagnostics, but still lacks a gate-input/logit predictor, measured runtime cost, quality/parity and matched accepted decode tok/s.
- DoMoE has historical profile provenance but zero current-IQ3 model-root profiles and no frozen semantic domain/prompt provenance.
- HOBBIT has only native-size/budget arithmetic; there is no lower-precision artifact.
- ReMoE, CommitMoE and FloE remain research-only. Adapt-async remains readiness-only because the inspected candidate has no same-source runner, harness or raw log.
- The old ledger rows that say the complete IQ3 trace is absent or point to the truncated local trace are preserved as historical inputs; the current wrappers govern navigation.

The current-best SHA remains the controlled IQ3 baseline `366A355E...6015E2`, not a global-fastest claim. A fresh remote identity/process/config/runtime gate is still mandatory before any live operation. No remote operation, process stop, temperature change or fallback occurred.

Next: maintain local stop-resilience and continuation state; do not manufacture a runnable candidate from incomplete fields.
