TASK_ID: LUNA-20261011-019
SUPERSEDES: LUNA-20261010-018
BASELINE: 018 direct-slot 6/512 662C7E6103B29538EAF530FB2657BE0C384730F76D9805987695327C11967D71; 20GiB/GPU fixed.
HYPOTHESIS: Rank ignores SSD miss cost. Replay separate routing trace with 6/512. In generate.cpp::rank_all load cost-rank (misses*blob_bytes); expert_source.cpp::pin_cache_complement keeps 20GiB cap/GPU exclusions. Fewer reads.
BENCH: 2 confirm pairs 018/009; combined 5-pair median >=3% else rollback/stop. Replay 20GiB old/new on independent trace; require >=15% fewer predicted SSD bytes before edit. Match IQ3/MTP/context/env/settings; prompt 28912 SHA9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA; 1024 accepted; 3 interleaved pairs+2 confirm if >=3%.
GATE: PROMOTE only 5-pair median >=3%, stable/correct; else REJECT/rollback.
LIMIT: <=14 runs/6h; no 4096/sweep.
RAW: C:\Users\User\Strata-Adrian\runs\iq3-campaign-019
REPORT: main outbox; trace/sim, commands/env, source/binary SHA, pairs, decision.