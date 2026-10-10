TASK_ID: LUNA-20261010-015
SUPERSEDES: LUNA-20261010-014
BASELINE: Task009 PROMOTED 6/512 + deployed SHA256 59292D5C...; each PROMOTE becomes next control.
HYPOTHESIS: CPU pool is dominant. A port PR1087, fixed 192 row tasks. B port PR863 IQ3_XXS-relevant Intel P-core gather/AVX-VNNI only. C only if A/B logs show barrier idle tail >=3% decode wall: port PR733 per-expert Down pipeline. Never repeat 012-014, RAM_ADAPT, stage-LRU, prior prefetch/lookahead/PVM.
BENCH: Each candidate 3 interleaved pairs; same 28912 prompt/IQ3/MTP/env/settings; 1024 accepted; log tok/s,pool ms,file MB. If paired median >=3%, run 2 confirm pairs, PROMOTE, then stack next.
GATE: PROMOTE only confirmed paired median >=3%, stable/correct; else REJECT/rollback. Skip C if trigger absent.
LIMIT: <=30 runs, <=8h, <=3 candidates; no knob sweep/4096.
RAW: C:\Users\User\Strata-Adrian\runs\iq3-cpu-campaign-015
REPORT: main outbox; hashes,pairs,decision,new baseline,next route.
