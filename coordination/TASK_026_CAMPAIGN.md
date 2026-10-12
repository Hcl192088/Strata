TASK_ID: LUNA-20261012-026
STATUS: NEW
CLAIM_REQUIRED: true
BASELINE: Last formal IQ3 Task018 e26d5538/662C7E61, 20GiB; recheck actual PROMOTE.
HYPOTHESIS: Task025 standalone v0.1.42 async-miss source 61b3fb5d+BA592A98, binary E3FA77FE, is directly promotable; no 018 patch port.
BENCH: Audit Task025 stage A/B 5 pairs, especially stage-B control binary/SHA and same IQ3/28912 prompt SHA93505844/ctx100k/MTP6/20GiB/1024. Reuse valid matched evidence; only fill missing comparisons. After PROMOTE profile pool/file miss and implement one causal source fix.
GATE: 3 interleaved matched pairs median>=3% +2 same-control confirm; stable. KL diagnostic only. Commit exact source, deploy source+binary+settings atomically with rollback; source must rebuild to same behavior.
LIMIT: 8h/28 new processes max; no 4096, sweeps, old tests or parallel claim.
RAW: C:\Users\User\Strata-Adrian\runs\iq3-campaign-026
REPORT: main outbox; SHA, source, pair audit, promotion, new canonical, raw.