TASK_ID: LUNA-20261011-023
STATUS: NEW
CLAIM_REQUIRED: true
BASELINE: Latest promoted IQ3; Task018 e26d5538/bin 662C7E61 if unchanged; 20GiB.
HYPOTHESIS: Qualify standalone upstream v0.1.42 fast path (61b3fb5/bin 803C1EA), then optimize expert pool/file stalls on promoted source. Read coordination/TASK_023_OVERNIGHT.md.
BENCH: Audit Task020 28 runs first. Frozen IQ3, prompt SHA93505844, ctx100k, MTP6, profiles/env, 20GiB, 1024 accepted. 3 interleaved canonical-v0142 pairs then 2 confirm; fixed-prefix numerical quality. Repeat for source candidate.
GATE: Paired median >=3%, stable and quality pass => PROMOTE synchronized source+binary+settings; else REJECT/rollback. No output SHA parity gate.
LIMIT: <=28 new runs/8h; no 4096 or knob sweeps; exclusive claim; retry recoverable faults.
RAW: C:\Users\User\Strata-Adrian\runs\iq3-campaign-023
REPORT: main outbox; stage raw/SHA/activation/pairs/quality/PROMOTE and next baseline.