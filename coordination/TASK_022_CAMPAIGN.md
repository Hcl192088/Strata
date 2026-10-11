TASK_ID: LUNA-20261011-022
BASELINE: 018 e26d5538; bin 662C7E6103B29538EAF530FB2657BE0C384730F76D9805987695327C11967D71; 6/512,20GiB.
HYPOTHESIS: Isolate 020's unverified tail-skip: port only upstream 61b3 rank>=7 missed-expert skip into src/core/expert_source.cpp::expert_pool_dispatch_multi, header skip counters, src/program/generate.cpp activation. No PcieAuto. Less CPU/file work.
BENCH: Preflight skip0 vs 018 token parity; skip7 count>0; fixed 018 PCIe share, no Auto, else stop. Same IQ3/MTP/ctx/profile/env; 28912 SHA9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA; 1024 accepted. 3 interleaved 018/skip7 pairs; >=3% then 2 confirm.
GATE: 5-pair median>=3%, stable, same-prefix logit KL<=0.006 => PROMOTE; else REJECT/rollback.
LIMIT: <=14 runs/5h; no 4096/sweep; canonical untouched until pass.
RAW: C:\Users\User\Strata-Adrian\runs\iq3-campaign-022
REPORT: main outbox; skips,tok/s,pool/file,KL,source/bin SHA,commands/env,decision.