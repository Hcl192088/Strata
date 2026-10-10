TASK_ID: LUNA-20261010-013
SUPERSEDES: LUNA-20261010-012 (BLOCKED+FOLLOWUP)
BASELINE: Task009 6/512; 28911-logged ~35-37 tok/s.
HYPOTHESIS: An adaptive RAM-residency candidate based on upstream #1838 may reduce repeated file-tier expert reads and improve accepted decode tok/s while preserving 6/512.
HISTORY: Read 005-012+followup and current source; do not repeat rejected or already-present mechanisms.
BENCH: Same toolchain; isolated control/candidate; same prompt/model/MTP/env/settings; 1024 accepted; 3 interleaved pairs. Log tok/s,file MB,pool ms,RAM moves/errors.
GATE: Paired median >=3% and no correctness/RAM regression => PROMOTE; otherwise REJECT and restore control. If candidate is not applicable, test one bounded decode-fed RAM LRU alternative; no sweep.
LIMIT: <=12 benchmark runs and <=3h active work.
RAW: C:\Users\User\Strata-Adrian\runs\iq3-ram-adapt-013
REPORT: main outbox; baseline,candidate,delta,decision,new baseline.