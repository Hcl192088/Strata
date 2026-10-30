# Fate Trace Runner Discovery — 2026-10-18 02:22 +08:00

## Result

The actual live build run-tree contains these matching tools:

- `research_run.py`: client for an already running OpenAI-compatible API;
- `serve_load.py`: client/load generator for an already running API;
- their tests.

There is no live-source model-start helper, `--dump-routing` launcher, isolated serve runner or one-shot capture request harness. The canonical clone's unrelated untracked helper names are not part of the inspected live build source and are not an approved fallback.

## Decision

Fate remains `PARTIAL` with a precise runner-missing boundary. The API client tools must not be executed as a substitute for a one-shot routing capture, and the scheduled API must remain untouched. No helper was run, no benchmark started, and no remote state changed.

## Coverage

Checked a fresh process gate and the live run-tree/source tools matching runner terms, then read the two relevant client helper roles. Did not inspect every remote run file, execute helpers, or use canonical-clone untracked files.
