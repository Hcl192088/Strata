TASK_ID: LUNA-20261010-013
SUPERSEDES: LUNA-20261010-012 (BLOCKED)
BASELINE: Task009 6/512 SHA256 59292d5c...faecec3; median 37.93 tok/s.
GOAL: Diagnose Task009 binary slowing to ~21 tok/s; no rebuild.
CLAIM: Exclusive guard; check live processes.
AUDIT: Read Task009 10 raw logs/commands and Task012; compare prompt path/SHA/tokens, model/quant/shards, MTP, env, cache, runtime, file-tier, pool. Find 28912-token prompt.
TEST: Same deployed SHA, frozen Task009 model/quant/profile/MTP/env/settings, ctx100000, 1024 accepted output. Verify prefill=28912; run 3 repeats. Log tok/s, MTP accepted/proposed, file MB, pool ms, RAM/GPU, command/env/SHA.
GATE: >=35 median tok/s restores baseline; otherwise report causal evidence. No promotion without matched >=3% paired gain.
STOP/RETRY: Identity/error -> stop, fix prompt once, retry; if unresolved BLOCKED. No source/build/deploy; rollback=unchanged.
RAW: C:\Users\User\Strata-Adrian\runs\iq3-identity-013
REPORT: main outbox; controller state.