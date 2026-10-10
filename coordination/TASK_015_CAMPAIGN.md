TASK_ID: LUNA-20261010-015
SUPERSEDES: LUNA-20261010-014
BASELINE: Task009 PROMOTED 6/512 source+deployed SHA256 59292D5C...; preserve all promoted settings.
HYPOTHESIS: Port only PR1087 CPU expert-pool task partitioning. Historical Strata data show speed tracks pool latency; PR1087 reports 192 vs default tasks cut CPU layer-call time 4.41-21%. This route is absent from current source/reports.
BENCH: Candidate=192 pool tasks; control=default. Same 28912 prompt/IQ3/MTP/env/settings, 1024 accepted. Run 3 interleaved pairs; log tok/s,pool ms,file MB. If paired median >=3%, run 2 confirm pairs.
GATE: PROMOTE only confirmed paired median >=3% with stable/correct runs; else REJECT/rollback. No task-count sweep.
LIMIT: <=10 benchmark runs, <=5h; no 4096/other knobs.
RAW: C:\Users\User\Strata-Adrian\runs\iq3-pool-tasks-015
REPORT: main outbox; source/binary hashes,pairs,pool delta,decision,new baseline.
