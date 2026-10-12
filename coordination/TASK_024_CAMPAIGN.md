TASK_ID: LUNA-20261012-024
STATUS: NEW
CLAIM_REQUIRED: true
BASELINE: Latest promoted IQ3 Task018 e26d5538/662C7E61, 20GiB; recheck.
HYPOTHESIS: Task023 v0142 KL=.0248568 may be tail7 zeroing or source drift; recover speed without quality loss.
BENCH: Reuse 023 logits; one v0142 tail0 prefix separates causes. If KL>.006, trace first divergent layer and repair v0142 semantics in isolated source. Else modify src/core/expert_source.cpp::expert_pool_dispatch_multi: skip tail7 only in low-error layers selected by one instrumented omitted-output norm profile, not rank sweep. Require prefix KL<=.006 before 3 interleaved+2 confirm pairs, 1024 accepted, frozen IQ3/MTP/prompt/env/20GiB.
GATE: KL<=.006, stable, paired median>=3% and 2 confirms => PROMOTE source+binary+settings; else REJECT.
LIMIT: <=24 new processes/8h; no 4096, sweep, old port or double claim.
RAW: C:\Users\User\Strata-Adrian\runs\iq3-campaign-024
REPORT: main outbox; attribution, activation, mask, raw, pairs, quality, outcome.