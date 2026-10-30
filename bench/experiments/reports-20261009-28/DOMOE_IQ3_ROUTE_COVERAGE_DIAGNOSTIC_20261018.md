# DoMoE IQ3 route-coverage diagnostic — 2026-10-18

This was a read-only remote analysis. It did not execute a profile, alter the selector, start a benchmark, change source/model/configuration, stop a process, or deploy anything.

The complete Task 028 trace was parsed with the existing `simulate_ram_routing.py::windows` parser:

- trace: `C:\Users\User\Strata-Adrian\runs\iq3-fate-trace-capture-028\routing-dump-01.bin`
- trace SHA256: `3D73DC8715A29311A16CA539DD39BFDB96BB97DA0F45EF38676EAE5A35297987`
- 567 windows, 52,464 tokens, route width 10, 524,640 route events
- fixed profile prefix: 3,153 pairs, matching the current IQ3 runtime capacity

Route-event coverage varied materially by profile:

| profile | coverage | delta vs generic |
|---|---:|---:|
| generic | 32.574% | — |
| learned-heart-chat | 50.202% | +17.629 pp |
| iq2xs-neuro-oracle | 37.730% | +5.156 pp |
| iq2xs-neuro-quota-locked | 37.597% | +5.023 pp |
| iq2xs-travel | 28.320% | −4.254 pp |
| iq2xs-pitching | 30.441% | −2.133 pp |

This proves only that profile ordering changes static route coverage on this captured IQ3 trace. The profiles are legacy/unknown-quantization artifacts, so this does not prove semantic domain selection, current model-root compatibility, throughput, quality parity, or DoMoE reproduction. The direction remains `PARTIAL`, not measurement-ready or deployed.

The full profile list, hashes, remote identity and coverage limits are in the JSON companion. Remote raw output was streamed read-only and has no separate remote output path.
