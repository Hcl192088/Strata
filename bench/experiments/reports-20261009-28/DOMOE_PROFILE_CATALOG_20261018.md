# DoMoE profile catalog — 2026-10-18

Status: `PARTIAL_PROFILE_CATALOG_NO_CURRENT_IQ3_TRACE`.

The remote artifact scan found 10 structurally 48×512 profiles and one 48×256 coder profile. The 48×512 artifacts include generic, early-decode neuro, three historical neuro profiles, pitching, travel, learned-3topics and two learned-heart artifacts. The coder profile is not dimension-compatible with the current 48×512 model.

The important boundary is provenance: all named topic profiles are under the legacy `Strata-v0.1.38-ab-20261003` tree, while the current IQ3 model pack root contains no profile artifact. Their dimensions make them parseable as 48×512 profiles; that does not prove current IQ3 numerical parity, workload transfer, or DoMoE semantics.

The catalog is therefore useful for selecting a future data-only matrix, not for deployment. A valid current IQ3 comparison still needs a frozen profile hash, domain/prompt identity, current binary/config identity, matched output quality/parity, accepted decode tok/s and raw remote evidence. No profile was copied, converted, loaded or deployed in this unit.

Coverage: three exact remote roots were scanned after a fresh identity/process gate. Results were limited to profile/learned/heart/coder-named `.bin` files; other binary artifacts and full raw logs were not treated as profile evidence.
