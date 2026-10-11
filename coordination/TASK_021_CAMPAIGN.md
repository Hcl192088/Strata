TASK_ID: LUNA-20261011-021
BASELINE: 018 e26d5538; binary 662C7E6103B29538EAF530FB2657BE0C384730F76D9805987695327C11967D71; 6/512,20GiB.
HYPOTHESIS: IQ3_XXS(18) NT=1 uses ggml vec_dot on AVX2. In src/kernels/cpu/native_expert.cpp::native_gu_mt_min dispatch NT=1 to existing iq256_gu_rows, type18 only; keep others. Decode pool time falls.
BENCH: Verify route absent; NT1 share>=20%, AVX2 NT1 microbench >=10% faster, numerical parity pass or stop. IQ3/MTP/ctx/env/profile matched; 28912 prompt SHA9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA; 1024 accepted. 3 interleaved A/B pairs; >=3% median then 2 confirm.
GATE: 5-pair median >=3%, stable, identical output tokens => PROMOTE; else REJECT/rollback.
LIMIT: <=12 processes/5h; no 4096/sweep; canonical untouched until gate.
RAW: C:\Users\User\Strata-Adrian\runs\iq3-campaign-021
REPORT: main outbox; NT1 counts, pairs, tok/s,pool/file, source/binary SHA, commands/env, decision.