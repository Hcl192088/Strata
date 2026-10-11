TASK_ID: LUNA-20261011-020
SUPERSEDES: LUNA-20261011-019
BASELINE: 018 e26d5538 binary 662C7E6103B29538EAF530FB2657BE0C384730F76D9805987695327C11967D71; 6/512.
HYPOTHESIS: Official Niko1221/Strata v0.1.42 (61b3fb5) expert_source.cpp tail-skip + generate.cpp::PcieAuto measured PCIe share cut CPU/PCIe cost; port winners onto 018.
BENCH: Fix 20GiB resident, GPU cache 3604, IQ3/MTP/ctx/env; prompt 28912 SHA9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA; 1024 accepted. Compare 018 vs v0.1.42 defaults; then skip 0/7 PCIe old, then PCIe old/auto at skip 7. Each 3 interleaved pairs.
GATE: >=3% paired median then 2 confirm pairs; check skip token quality. Port winners into 018, rebench >=3%, stable/correct => PROMOTE+sync; else REJECT/rollback.
LIMIT: <=30 runs/6h; no 4096, RAM cuts or knob sweep.
RAW: C:\Users\User\Strata-Adrian\runs\iq3-campaign-020
REPORT: main outbox; commands/env, source/binary SHA, paired tok/s, pool/file/PCIe, quality, decision.