# Fate predictor-cost diagnostic — 2026-10-18

## Result

The corrected bounded offline replay completed as `DIAGNOSTIC_ONLY`. It used the existing EOF-complete Task 028 IQ3 route trace and did not run the Strata runtime, benchmark, API, deployment, router training or source modification.

- Remote evidence: `C:\Users\User\Strata-Adrian\runs\iq3-fate-trace-capture-028\fate-predictor-cost-20261018-rerun.json`
- Evidence size/hash: 1,978 bytes / `0FCF5E70133E1B783945EEBED889B22483ACFB9DCA200F2DA5B4F0BA7E94DAA8`
- Trace: 567 windows, 396 train / 171 test, 48 layers, route width 10, EOF complete
- Trace SHA256: `3D73DC8715A29311A16CA539DD39BFDB96BB97DA0F45EF38676EAE5A35297987`

## Corrected measurements

- Top-10 replay: 384,930 lookup operations, 148,662 hits, lookup hit rate 38.6205%, 6.2841874 s total, 163.2553 us per target token.
- Top-20 replay: 384,930 lookup operations, 212,070 hits, lookup hit rate 55.0931%, 6.5612766 s total, 170.4538 us per target token.
- Both methods use 12,831 target tokens per repeat and 3 repeats; `lookup_operations = target_tokens * source_width * repeats` is internally consistent.

## Boundary and follow-up

The first replay is retained as invalid raw evidence because its target-token field was divided by the repeat count while lookup operations were not. The corrected rerun is a host-side route-ID proxy measurement, not the runtime cost of a gate-input predictor. The trace lacks gate inputs/logits, so this is not a Fate paper reproduction. Quality/parity and matched accepted decode tok/s remain unmeasured; no A/B or promotion follows from this result.

Post-run identity gate confirmed host `DESKTOP-LKMLUPC`, controlled binary SHA256 `366A355E0E866B12D1793C9D8BE022925305B4560E1AE7DC47F8716C865015E2`, config SHA256 `C805B1206CDD23B22EE3CC66A80C52014EF9904CDB4314A6C6A17B8E00FFEA18`, expected source/build heads and zero relevant processes.
