TASK_ID: LUNA-20261010-012
SUPERSEDES: LUNA-20261010-011 (COMPLETED)
BASELINE: promoted 6/512 source; deployed SHA256 59292D5CCBCD200BD209AE04EE59E795DA979B6AFFD175C870E673F9FFAECEC3.
HYPOTHESIS: rebuilt slowdown is binary/config; batched file-tier reads may help.
A: Compare deployed vs Task011 rebuilt binaries in 3 interleaved matched pairs; freeze command/env; log tok/s, file MB, pool ms, hashes, build flags. If >5% gap, isolate/correct cause before B.
B: On validated control, implement bounded adjacent Windows file-tier read batching; isolated build; 3 pairs then 2 confirm if median gain >=3%.
BENCH: IQ3; prompt 28912; accepted 1024; ctx 100000; Task009/011 model, quant, MTP, profile, runtime/settings fixed.
GATE: PROMOTE only confirmed paired median >=3%, no errors/RAM regression; else REJECT/rollback.
LIMIT: 24 runs, 5h; no 4096, merge, force-push.
RAW: C:\Users\User\Strata-Adrian\runs\iq3-file-tier-012
REPORT: main outbox; include controller state.