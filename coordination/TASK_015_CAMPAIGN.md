TASK_ID: LUNA-20261010-015
SUPERSEDES: LUNA-20261010-014
BASELINE: Latest PROMOTED canonical source+binary+settings from prior terminal report.
HYPOTHESIS: The highest-value untested source-level intervention selected after reading all prior reports/current source/upstream can materially raise accepted decode tok/s; exclude rejected, present, or superseded routes.
BENCH: Same model/prompt/MTP/env/settings; 1024 accepted; isolated control/candidate; 3 interleaved pairs; log tok/s and bottleneck-specific metrics.
GATE: Paired median >=3% and stable/correct => PROMOTE; else REJECT/rollback and continue to next untested high-value route.
LIMIT: <=18 benchmark runs, <=5h, <=3 candidates; no micro-sweep or duplicate route.
RAW: C:\Users\User\Strata-Adrian\runs\iq3-campaign-015
REPORT: main outbox; baseline,candidates,deltas,decisions,new baseline,next route.