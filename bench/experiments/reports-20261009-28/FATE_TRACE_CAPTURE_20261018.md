# Fate trace capture — LUNA-20261018-028

Status: `CAPTURE_COMPLETE_SRP_SCH_DIAGNOSTIC_ONLY`

The task used the controlled IQ3 binary `366A355E...015E2`, build source `61b3fb5d...46406`, config `C805B120...FEA18`, IQ3_XXS and 20 GiB resident budget. The only runtime addition was a new `--dump-routing` output path. No source, model, quantization, temperature, sampling, scheduler or existing Task020 process was changed.

Fresh remote gate passed on `DESKTOP-LKMLUPC` / `DESKTOP-LKMLUPC\\User`: remote `AGENTS.md` SHA256 `FD9EB03F...E070A`, no interfering Strata/Luna/benchmark/build process, and Task020 was not running or mutated. The one-shot capture completed with `READY`, exit code `0`, `DONE 1024`, and no residual relevant process.

Raw trace: `C:\Users\User\Strata-Adrian\runs\iq3-fate-trace-capture-028\\routing-dump-01.bin`; 4,616,832 bytes; SHA256 `3D73DC8715A29311A16CA539DD39BFDB96BB97DA0F45EF38676EAE5A35297987`.

The strict `simulate_ram_routing.py::windows` parser reached EOF at a complete boundary: 567 windows, 52,464 records, fixed route width 10. The remote SRP/SCH bundle then produced fixed-profile hit rate `0.5017059316864898`; representative aggregate values include SRP segment 4/cache 16 `0.697206`, segment 16/cache 64 `0.944903`, segment 64/cache 128 `0.966418`, segment 256/cache 256 `0.993570`; SCH values for future lengths 4/16/64/256 were `0.571300/0.719581/0.703216/0.673906`.

The analyzer bundle required three execution-only compatibility fixes: suppress its old `__main__` entry while overriding paths, fix the route tuple iteration in `sch_hit_rate`, and pass/index the cache-size argument in `weighted_layer_value`. The repository tool was not modified. This is recorded as a tooling follow-up, not hidden as a trace failure.

Decision: `DIAGNOSTIC_ONLY_COMPLETE_TRACE`. This is not accepted decode tok/s, quality parity, deployment, or paper reproduction. The next safe step is offline Fate cross-layer predictor analysis; a matched IQ3 decode A/B requires predictor-cost, hit-rate, quality and parity evidence first.

Remote raw and analysis artifacts remain under the raw root. Local state stores only the evidence index, hashes and this report.
