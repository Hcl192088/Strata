TASK_ID: LUNA-20261010-015
SUPERSEDES: LUNA-20261010-014
BASELINE: Task009 deployed SHA256 59292D5C...; canonical source must preserve 6/512.
HYPOTHESIS: First recover a rebuild reproducing Task009 throughput; then reduce dominant file-tier stalls with bounded adjacent Windows reads in FileExpertSource. Distinct from rejected RAM_ADAPT/stage-LRU.
BENCH: A: deployed vs rebuilt, 3 interleaved pairs, same 28912 prompt/1024 accepted/full IQ3 identity; require rebuilt paired median within 3%. B: implement adjacent-read batching, isolated build, 3 pairs +2 confirm if >=3%.
GATE: If A fails, isolate source/build delta until matched; do not optimize on a slow rebuild. In B PROMOTE only confirmed paired median >=3%, stable/correct; else REJECT/rollback.
LIMIT: <=18 runs, <=5h; one source candidate; no knob sweep/4096.
RAW: C:\Users\User\Strata-Adrian\runs\iq3-file-tier-batch-015
REPORT: main outbox; source/binary hashes, A gap cause, pair deltas, decision,new baseline.
