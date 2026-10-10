TASK_ID: LUNA-20261010-013
SUPERSEDES: LUNA-20261010-012 (BLOCKED+FOLLOWUP)
BASELINE: Task009 6/512; fast 28911-logged workload ~35-37 tok/s.
HISTORY: Read outbox 005-012+followup and current source first. Do not repeat rejected lookahead/PVM/stage-churn/pinned-stage. Adrian already has #286/#362 unbuffered read_direct/fill_many.
TARGET: Port minimal upstream #1838 STRATA_RAM_ADAPT=8 to current Windows/Adrian lineage; keep 6/512. RTX3060 12GB+32GB result: file reads ~68k->33k, decode +16.4%. If present, skip.
BENCH: same-toolchain isolated base/candidate; same fast prompt/model/MTP/env/settings; 1024 accepted; 3 interleaved pairs. Log tok/s,file MB,pool ms,RAM moves/errors.
GATE: paired median >=3%, no correctness/RAM regression => PROMOTE; else REJECT/rollback. If rejected/not portable, test one #1324-style bounded decode-fed RAM LRU; no sweep.
RAW: C:\Users\User\Strata-Adrian\runs\iq3-ram-adapt-013
REPORT: main outbox; baseline,candidate,delta,decision,new baseline.