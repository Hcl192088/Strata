TASK_ID: LUNA-20261010-014
SUPERSEDES: LUNA-20261010-013 (COMPLETED/REJECT)
BASELINE: Latest PROMOTED canonical 6/512 control; preserve current-best deployment.
HYPOTHESIS: A bounded decode-fed RAM LRU based on upstream #1324 will reuse cold experts better than fixed profile/RAM_ADAPT and raise accepted decode tok/s. Verify current source first.
BENCH: Same model/prompt/MTP/env/settings; 1024 accepted; isolated control/candidate; 3 interleaved pairs; log tok/s,file MB,pool ms,L2/LRU hits,RAM.
GATE: Paired median >=3% with no correctness/RAM regression => PROMOTE; else REJECT/rollback and test one next highest-value untested source route.
LIMIT: <=18 benchmark runs, <=5h, <=3 candidates; no repeated rejected/present route.
RAW: C:\Users\User\Strata-Adrian\runs\iq3-campaign-014
REPORT: main outbox; each candidate,delta,decision,new baseline,next route.