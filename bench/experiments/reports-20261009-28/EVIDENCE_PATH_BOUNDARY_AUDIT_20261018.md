# Evidence Path Boundary Audit — 2026-10-18 02:49 +08:00

- Checked all 47 current `EXPERIMENT_INDEX.jsonl` rows.
- Missing local evidence paths: 0.
- Rows with `remote_run_started=true`: 0.
- One older retained provenance row points to `D:\strata\reports\...`; it is recorded as historical and was not moved, deleted or overwritten.
- New evidence remains under `D:\strata\state\` only.
- This is a local path-boundary audit, not proof of remote benchmark correctness.
