# DoMoE selector input contract — 2026-10-18

This contract defines the minimum identity and measurement fields for a future DoMoE selector. It is deliberately not an implementation: the current IQ3 model root has no verified compatible profile, the frozen domain/prompt set is absent, and selection semantics are not authorized.

Every future arm must preserve prompt hash, seed, unchanged temperature, sampling, context/KV settings, binary/config/model identity, exact profile path/SHA, accepted output length, raw evidence path, expert hit rate, quality/parity, error rate and accepted decode tok/s. An unmatched request is `NOT_APPLICABLE`; it must not silently fall back to a historical profile.

No remote operation, profile execution, source/API/model change, benchmark, temperature change, process stop or fallback occurred.
