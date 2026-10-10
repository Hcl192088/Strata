# Task 010: canonicalize 6/512 and reduce stage-cache churn

Predecessor: LUNA-20261010-009 (COMPLETED).

Current promoted control is the task-009 stage-cache reuse patch: `kStageAge=6`, `kStageSeq=512`, deployed binary SHA256 `59292D5CCBCD200BD209AE04EE59E795DA979B6AFFD175C870E673F9FFAECEC3`. The old 3/256 control is historical only.

## Phase 0 — canonicalize the promoted control

1. Verify no existing Strata/controller process owns the target.
2. Apply only the validated 6/512 source patch to the authoritative desktop source at `C:\Users\User\Strata-Adrian\repo\Strata-Adrian-control`; preserve unrelated dirty files.
3. Build from that source and verify the resulting binary behaves as the deployed 6/512 control. Do not spend five standalone runs on baseline reproduction; use interleaved matched controls in the experiments below.
4. If source synchronization cannot reproduce a valid 6/512 control, stop before new optimization and report the exact mismatch.

## Phase 1 — attack refill/eviction churn

Task 008/009 showed that 6/512 reduced file-tier traffic about 30% and improved paired decode about 6.6%, while refill/eviction churn remained the dominant measurable opportunity. Inspect the current `FileExpertSource::claim_stage` path and recent upstream/fork implementations, then implement the strongest bounded source hypothesis that reduces avoidable refills without increasing the stage-buffer footprint materially.

Preferred direction: replace the current simple eligible-oldest victim choice with a reuse-aware / second-chance victim policy using information already available on the hot path (for example recent re-reference/hit history or layer/reuse distance). Avoid prompt-specific hard-coded layer IDs. Keep the policy cheap enough that victim selection overhead cannot erase I/O savings.

Instrument only what is necessary to measure:
- stage hits/fills/refills/evictions,
- file-tier bytes and read time,
- CPU pool-call time,
- stage-buffer count/RAM,
- accepted decode tok/s.

Run interleaved matched 1024-token pairs against the canonical 6/512 control. Start with 3 pairs for a candidate. If paired median gain is >=3% with no correctness/stability/memory regression, confirm with 2 additional pairs before promotion. Reject a candidate early if the first 3-pair median is <=0% or it materially increases file-tier traffic/CPU pool time with no compensating throughput gain.

If the first reuse-aware policy fails, use the remaining budget for one substantially different stage-churn source hypothesis supported by the trace; do not turn this into a broad knob sweep and do not repeat task-007 lookahead/PVM experiments.

## Promotion rule

A promoted candidate immediately becomes the new canonical source+binary+settings control for all later tasks. Promote only when:
- paired median accepted decode gain >=3% after confirmation,
- no crash/CUDA/verification failure,
- no material memory regression,
- raw identity and all matched results are preserved.

If promoted, synchronize authoritative source and deployed binary before reporting completion. If rejected, leave canonical 6/512 unchanged.

## Frozen benchmark identity

Use the task-009 IQ3 identity: 28,912-token prompt, max_context=100000, exactly 1024 accepted output tokens, same IQ3 model/quant/tokenizer/sampling/profile/MTP/runtime/settings. Only the intended source candidate may differ.

Store artifacts under:
`C:\Users\User\Strata-Adrian\runs\iq3-stage-churn-optimization-010`

Budget: up to 24 new benchmark processes and 5 hours active work. Preserve raw logs and report genuine results to `coordination/LUNA_TO_CHATGPT.md`, including current control, candidate, paired delta, PROMOTE/REJECT, resulting new control, and whether any durable controller remains running.
