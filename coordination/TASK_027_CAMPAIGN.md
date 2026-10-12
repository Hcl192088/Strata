TASK_ID: LUNA-20261012-027
STATUS: NEW
CLAIM_REQUIRED: true
SUPERSEDES: LUNA-20261012-026
BASELINE: CURRENT_BEST=Task025 async v0.1.42 E3FA77FE, median 49.45 tok/s; 018 is rollback only.
HYPOTHESIS: 026 absolute slowdown/file reads came from stale benchmark process/RAM pressure; 026 causal-fix 77F5DA99 may still beat CURRENT_BEST.
BENCH: Audit/stop only stale campaign-owned Strata/Llama benchmark processes; record free RAM/processes. Run 2 interleaved E3FA77FE vs 77F5DA99 pairs with frozen IQ3_XXS/28912 SHA93505844/ctx100k/MTP6/20GiB/1024. If healthy and promising, extend to 3 pairs+2 confirms.
GATE: If clean control median <45 tok/s, STOP ENV_BLOCKED. Otherwise candidate must paired-median >=3% and absolute median >=49.45; final PROMOTE needs 3+2. Else REJECT 026 path.
LIMIT: <=10 new runs/2h; no new source change/sweep/4096.
RAW: C:/Users/User/Strata-Adrian/runs/iq3-campaign-027
REPORT: main outbox; process/RAM pre/post, pair tok/s, file reads, decision.