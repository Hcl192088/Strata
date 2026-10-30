# Routing-trace provenance matrix — 2026-10-18 04:22 +08:00

This is a local diagnostic/provenance record, not a new runtime experiment.

- The authoritative complete Task 028 IQ3 trace is remote at `C:\Users\User\Strata-Adrian\runs\iq3-fate-trace-capture-028\routing-dump-01.bin`, SHA256 `3D73DC...5297987`, 4,616,832 bytes, 567 EOF-complete windows, 52,464 records and route width 10.
- It contains selected expert IDs and a frozen prompt hash, but no gate-input vectors, logits or per-window domain/session labels.
- The Fate proxy used 396 chronological train windows and 171 test windows across 47 target layers. It is useful locality evidence, not a reproduction of Fate's gate-input predictor.
- The historical DoMoE catalog has 10 structurally usable 48x512 profiles, but zero current-IQ3 model-root profiles. Its domain counts (`neuro 4`, `heart 2`, `pitching 1`, `travel 1`, `UNKNOWN 1`, `UNKNOWN_MULTI_TOPIC 1`) are planning metadata, not semantic-selector measurements.
- The old truncated local trace is explicitly excluded and remains preserved. No profile was copied or converted, no trace was rerun, and no remote process was touched.

## Decision

Keep Fate at diagnostic-only and DoMoE at zero measurement. The next meaningful gate is a local reproducibility-ledger audit; any live test still requires a fresh remote identity/process/source/binary/config gate and matched quality plus accepted-decode evidence.
