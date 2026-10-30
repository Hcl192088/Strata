# Prepacked R4 actual ExpertPool bounded screen

2026-10-30, LUNA-20261012-027 direct-user continuation. TESTED / MIXED_POSITIVE_MECHANISM / REPORT_LOCAL. The user authorized the pool experiment; no engine test or deployment was authorized for this unit.

A is native pool; B directly consumes prepacked R4 GU; C repacks each 4-row group in the timed pool. All arms use isolated copies of the same f520bc5 ExpertPool, 9 pinned workers plus host, `STRATA_NATIVE_PIPE=1`, actual GU→quant→type42 `act_quant_any/q2_rows_any` down. B/C use the same four-row group partition as the preceding tile screen; A retains native row partition. Every B/C task reads a four-row slice with the same token stride and writes it into the original output row positions. Each on-the-fly C thread has an 8192-byte scratch, up to 81920 bytes across 10 participants, plus small stack outputs. B executes no pack/unpack inside timed pool. All three arms execute their dispatch branch in the same isolated executable; native A is not an invocation of the full A1E6 engine binary. Original blob for A/C and prepacked blob for B coexist: this is a controlled test arrangement, not a one-copy production proof.

Workload: same first IQ3_S layer 8 and 18 actual experts as prior screen, down type42; nt2/3 and nb1/4/8/16; five cyclic A/B/C passes per cell, one warmup each, same activations and working set. Measurements are median full pool wall time in microseconds; no SSD, GPU, transfer, or B initialization costs are included. Shares of nt and nb in production were not measured, so no weighted whole-engine estimate. One fixed sample, short five-round screen; confidence intervals or causal comparison with earlier campaign are not claimed.

|nt|nb|A native us|B prepacked us|C per-group pack us|A/B|C/B|B faster than A, paired rounds|
|---:|---:|---:|---:|---:|---:|---:|---:|
|2|1|71.000|70.300|82.000|1.010|1.166|3/5|
|2|4|209.300|211.200|257.100|0.991|1.217|1/5|
|2|8|418.000|428.900|511.100|0.975|1.192|1/5|
|2|16|948.500|867.600|1090.200|1.093|1.257|4/5|
|3|1|84.300|83.900|94.700|1.005|1.129|3/5|
|3|4|352.100|246.900|300.700|1.426|1.218|4/5|
|3|8|589.100|538.700|666.200|1.094|1.237|5/5|
|3|16|1310.900|1073.900|1578.100|1.221|1.470|4/5|

C was slower than B in all 40 paired rounds. B has a positive mechanism in several cells, notably nt3/nb8 5/5 and nt3/nb16 4/5, while nt2/nb4 and 8 are unfavorable. nt3/nb4's median +42.6% reflects 4/5 paired positives, with one −1.7% and unusually high native times; interpret as noisy sample, not an engine prediction. Individual paired ratios are in pool.log. Changes of partitions, branch code, concurrent cache traffic and weights retained in separate blobs are part of this sample; the C/B comparison includes data-layout/working-set differences along with timed conversion, not a direct conversion-only clock.

Initial copy of 18 full native blobs into prepacked storage took 2146.2 us; packing their two GU matrices took 2768.3 us in one setup pass (~153.8 us/expert); neither is timed in B. These are one-pass observations and exclude other production conversion, GPU/prefill adaptation, ownership, cache, transfer, scratch and any costs associated with maintaining 3153 slots/20479 MiB. Each representation 33,638,400 bytes; both together 67,276,800 bytes. Sampled process peak working set 85,897,216 bytes, private 80,515,072 bytes, sampling 20ms; peaks could be missed between samples. Production single-copy consumer/capacity contract unresolved.

Correctness: all 18 × 640 GU rows × 2 matrices and nt2/3, VNNI and gather variants: fast full pack equals original pack bytes; GU roundtrips bytewise; unchanged down bytes equal original. Every four-row direct lowreg output equals corresponding full-row old R4 result bitwise with left/right output canaries. Full actual pool B vs C down outputs are bitwise equal for all 8 cells. Native pool down values differ in 4,256–101,238 floats/cell, max absolute 5.96046448e-8; neither semantic noninferiority nor degradation established. No A/A, fixed-token logits/loss or task evaluation: QUALITY_UNCONFIRMED.

Current best physical binary SHA A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8 and config SHA 060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93 verified preflight and before build/run. Source f520bc5e9d31c93caeb296b059e3a3eaa16e493f clean. Candidate executable SHA256 78407755F5CAE9966C052C501997AD941D9D1E14B0038100575B821944284BD0; pool.cpp 35448DAC62AFC1F38C086F33F82DC7CA579ED5E8AE4DD501071BD4D241E357C1; bench.cpp FD4547B5BCD732B4F8BF626A0FA454D5F85B0791AB71ADFB95058EE910B28D08; r4.cpp 116BB160D529F2A7A3521DB7C58D1ED0652C6F5058EC459C088D507F6B01BE74; pool.log FB80BA41A12D9DA0DE722582B664FC23D6080E4C011E8659D68932FA684C1254; library/input hashes in inputs.json. Remote C:\Users\User\Strata-Adrian-control\runs\r4-prepacked-pool-20261030.

API remained running; independent-final.json SHA D011202CF2FF88AF39BBE8EFED488446C9D80C34EF441FC9B6F16DCDFFD75E9D confirms PID32568, loaded/idle/queued0, original config/env, AboveNormal, 3153/20479, binary/config identity and no relevant test/build processes. No restore needed; no temperature or sampling change. No engine benchmark, consumer redesign or GitHub publication. Future consideration requires measured actual routing/nt/batch weights, single representation for CPU/GPU/prefill, complete conversion and cache/transfer costs, original capacity and semantic quality gate; no automatic advancement.

## Parent final acceptance
2026-10-30：父層交付後抽驗同一ExpertPool的A/B/C分支，B熱路徑確實直接讀packed而沒有pack/unpack；核對PARITY、八筆SUM、DONE和raw/independent-final SHA，均符合報告。fresh strict-host核對DESKTOP-LKMLUPC、A1E6/060F、receipt SHA D011202C…FFD75E9D，API PID32568 loaded/idle/queued0、3153/20479，只有已分類API/watch、無相關bench/build殘留。接納單層18expert、五輪局部pool的MIXED_POSITIVE_MECHANISM；nt3/nb8與16支持後續評估，nt3/nb4不當可靠+42.6%預測。未逐列重算所有RAW，未重跑或全面審核新source。品質、單副本consumer/production容量與整機tok/s均未驗證，不自動部署或擴展。
