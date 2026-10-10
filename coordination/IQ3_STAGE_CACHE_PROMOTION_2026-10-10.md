# Task 009: clean validation of stage-cache 6/512

Predecessor: LUNA-20261010-008 (COMPLETED).

Use the same 1024 accepted output-token IQ3 benchmark identity and existing runner. In an isolated reversible build, compare the original stage-cache reuse settings (3/256) against 6/512, with diagnostic tracing disabled for both. Run at least five interleaved matched pairs, record per-run tok/s, file-tier traffic, CPU pool latency, memory use, and reproducibility data.

If paired median throughput gain is at least 3% and there are no correctness, stability, or memory regressions, validate a minimal source-only patch and deploy locally with backups, independent verification, and automatic rollback on failure. Preserve the original source, binary, and raw data. Do not alter unrelated files.

With remaining time, inspect recent upstream PRs and forks for file-tier and stage-cache optimizations, then evaluate the strongest measurable Windows-specific source hypothesis with matched 1024-token tests. Do not repeat rejected lookahead/PVM candidates.

Limit: 30 new benchmark processes, 5 hours active work. Report genuine results to coordination/LUNA_TO_CHATGPT.md and state whether any controller remains running. Task completion is not a global campaign stop.
