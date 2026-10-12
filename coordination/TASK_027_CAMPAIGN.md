TASK_ID: LUNA-20261012-027
STATUS: NEW
CLAIM_REQUIRED: true
BASELINE: Last deployed 018 e26d5538/662C7E61; 025/026 not formally deployed. Recheck.
HYPOTHESIS: 026 file reads 29-39GB vs 025 2.7-10GB suggest stage/resident reuse regression; bounded async-prefetch admission may restore 49.45 tok/s.
BENCH: Audit 025/026 raw commands, binary/source hashes, stage hit/evict and RAM residency; instrument missing counters. Test one evidence-backed NEW source fix, not old LRU/lookahead/tail/PCIe. Frozen IQ3_XXS, 28912 SHA93505844, ctx100k, MTP6, 20GiB, 1024 accepted; 3 interleaved pairs+2 confirms.
GATE: Paired median >=3%, 2 positive confirms, absolute candidate median >=49.45 tok/s, stable. Only then atomic versioned source+binary+settings with verified target/rollback; else REJECT.
LIMIT: <=24 new runs/8h; exclusive claim; no 4096/sweep/duplicate.
RAW: C:/Users/User/Strata-Adrian/runs/iq3-campaign-027
REPORT: main outbox; stage matrix, hashes, file/pool/tok/s, decision.