# DoMoE Offline Evaluation Manifest — 2026-10-18

This manifest turns the existing DoMoE profile catalog into a future evaluation contract. It is not a benchmark result and does not reproduce the DoMoE paper.

The current evidence is provenance-only: all 10 catalogued profiles were freshly found with matching SHA256, STRP v1, 48x512 dimensions, and 24,576 ranked pairs. Profile overlap was not recovered, current-IQ3 model-root presence was not rechecked, and no current IQ3 trace, domain selector, throughput, hit rate, or quality result exists.

The candidate groups are therefore metadata-only. Neuro, heart, pitching, and travel labels are catalog labels, not a proven semantic classifier. The legacy IQ2 or unknown-quantization source labels must not be compared to the current IQ3 runtime as if they were matched arms.

Before any future measurement, the run must provide a current-IQ3 trace or approved matched run, exact profile SHA/path, frozen prompt hashes and domain labels, seed, unchanged temperature, full sampling/context/KV-cache settings, matched runs, accepted decode tok/s, expert hit rate, quality/parity, error rate, and a fresh process/identity gate.

Until those inputs exist, this remains MANIFEST_PREPARED_NOT_EXECUTED; there is no deployment, no live selector change, and no PROMOTE decision.
