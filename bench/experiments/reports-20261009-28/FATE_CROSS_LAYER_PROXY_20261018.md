# Fate cross-layer route-ID proxy — 2026-10-18

Task 028's complete routing trace was analyzed offline after a fresh remote identity/process gate. No Strata runtime, benchmark, scheduler, source, model, temperature or live binary was changed.

- Remote raw root: C:\Users\User\Strata-Adrian\runs\iq3-fate-trace-capture-028
- Analysis: fate-cross-layer-proxy-20261018.json, 57,000 bytes, SHA256 1FF115845ED653E2B0B1B1E4E981870DDF3CD96859D76332B0B56A9C614D993D
- Trace: SHA256 3D73DC8715A29311A16CA539DD39BFDB96BB97DA0F45EF38676EAE5A35297987; 567 complete windows; chronological split 396 train / 171 test; 47 target layers; route width 10.

The proxy uses the selected expert IDs from layer l-1 to predict the selected IDs at layer l. It is not Fate's gate-input predictor because the frozen dump has no gate-input vectors or logits.

| prediction set | global recall | cross-layer proxy recall | gain | proxy precision |
|---:|---:|---:|---:|---:|
| top-10 | 25.83% | 40.83% | +15.00 pp | 40.83% |
| top-20 | 38.03% | 58.05% | +20.01 pp | 29.02% |
| top-40 | 54.17% | 74.28% | +20.11 pp | 18.57% |
| top-80 | 72.28% | 87.06% | +14.79 pp | 10.88% |

Decision: DIAGNOSTIC_ONLY_WORTH_ONE_CONTROLLED_PREDICTOR_COST_TEST. The signal is strong enough to justify one carefully bounded predictor-cost diagnostic, but it does not justify runtime implementation, accepted decode claims, quality/parity claims or promotion. The proxy counts ten source-expert lookups per target token; that is an operation-count estimate, not measured CPU time.

Coverage: full 567-window trace was parsed remotely with the strict complete-window parser and evaluated across layers 1–47 at top-10/20/40/80. Not measured: gate-input features, predictor CPU latency, transfers, accepted decode tok/s, output quality, parity or cross-topic generalization.
