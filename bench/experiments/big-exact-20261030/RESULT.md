[LUNA_REPORT]
TASK_ID: LUNA-20261012-027
STATUS: PARTIAL
TASK_SOURCE: direct user continuation of branch task
TASK_BRANCH: coordination/task-027-file-tier-reuse-20261012
TASK_COMMIT_SHA: da28699a382304ec8afc87a547f9c37123985f77
AUTHORIZATION: 2026-10-30 user「去實測這個計劃」; P1–P4 structural plan.
BENCHMARK_RAW_PATH: C:\Users\User\Strata-Adrian-control\runs\big-exact-20261030 ; C:\Users\User\Strata-Adrian-control\runs\big-lut-20261030
PUBLICATION_STATUS: REPORT_LOCAL; no new claim/state rewrite, deployment or GitHub publication.

# P1/P2 completed; P3/P4 GPU profiling awaiting API-stop permission

No tested candidate supports +10% whole-engine promotion. P1 and P2 preserve sampled h/down bits, but both are slower than the current deployed CPU path. Do not broaden the negative result into an impossibility claim for all row kernels or all LUT algorithms.

## P1: original-layout multi-row/token microkernel

This is a new prototype, not a rerun of packed R4. It keeps the original native blobs, reuses the exact f520 Fmt32 decoders/hsum, and tests two/four rows together, sharing activation loads across rows and tokens. Per-row integer lanes, per-256-block FMA and reduction order remain unchanged. No repack/inverse or resident weight copy is introduced. Gate/up are streamed separately before unchanged SwiGLU and actual down dispatch.

IQ3_S type21, six of its13 layers × six experts=36 unique experts, same samples on P LP2/E LP15. nt1/2/3, GU-only and complete expert, five rotating A/B2/B4 passes. Baseline is the exact current-best CPU library, not a copied decoder used as a substitute baseline.

| Complete expert throughput change | P nt1 | P nt2 | P nt3 | E nt1 | E nt2 | E nt3 |
|---|---:|---:|---:|---:|---:|---:|
| Two rows | −16.9% | −11.7% | −3.7% | −13.9% | −8.8% | −6.9% |
| Four rows | −7.1% | −5.3% | −3.4% | −7.6% | −1.9% | −1.8% |

All sampled h and down float outputs match current native bitwise. Correctness alone does not give a performance case: activation sharing did not compensate for this prototype's extra live accumulators and changed work organization. No cycle-level attribution is claimed. Stop this prototype before other formats, production integration or whole-engine A/B, as registered.

## P2: activation-dependent signed-codebook dot LUT

The actual pinned codebooks were fully enumerated for four-value signed patterns:

| Format | Signed patterns | Full H int32 table / token |
|---|---:|---:|
| IQ2_XXS | 1184 | 3,031,040 bytes |
| IQ2_XS | 1296 | 3,317,760 bytes |
| IQ2_S | 1296 | 3,317,760 bytes |
| IQ3_XXS | 4096 | 10,485,760 bytes |
| IQ3_S | 8192 | 20,971,520 bytes |

Counts alone are not timings. IQ2_XXS was selected for a full lookup prototype. Its exact dot4 fits signed int16 (absolute bound4×43×128=22016), so the actual table is half the int32 estimate:1,515,520 bytes/token,4,546,560 bytes for nt3, plus pattern metadata. Activation sign handling preserves the original int8 negation wrap, including−128; no new activation precision or weight format is used.

The prototype builds the complete activation table using AVX2 vector arithmetic and performs lookup-based original integer lane accumulation. Table construction, lookup/indexing, h and unchanged actual down costs are all charged. One-time immutable map construction is outside timing; reused scratch is not reallocated in each pass. It is not a production-capacity result: any future scratch must be charged to the fixed RAM contract.

Type16,36 unique experts from six of nine layers, P/E,nt2/3; table rebuilt per1/4/8 experts, five AB/BA passes, GU-only and complete expert. nt1 is deliberately not substituted: its current ggml reduction contract differs from the multi-token path.

All sampled h/down results match current native bitwise. Even sharing across eight experts, complete-expert throughput is only15.0–25.1% of baseline across the four core/nt cases. Across all batch sizes it is13.8–25.1% of baseline, or roughly4.0–7.2× longer execution. This large regression is beyond a borderline-noise decision; no extra rounds or formats were added.

The smaller theoretical pattern set did not translate into speed. The actual table addressing, scalar indexed loads and building cost outweigh saved decode/dot operations. Build amortization improves results modestly but does not rescue this implementation. Do not call all activation LUT designs disproven; the registered full-H lookup prototype is NO_GO.

## P3/P4: consumer verification and profiling blocker

Fresh source checks confirm:
- native_dense.cpp still retains a second packed Q8 copy while the GGUF copy remains for prompt GEMM.
- prefill.cpp native_proj directly requires native_data/native_type and supplies it to gm.native. Thus a same-VRAM replacement needs consumer/ownership work, not a flag or deleting the original allocation.
- Verifier profile_report exposes named GPU stages, but prof_on disables shared side-stream work and DF_BRANCH. Its results would be instrumentation-specific stage costs, not the untouched live critical path. hc0 substages must not be added again to their parent phase.

A bounded three-request STRATA_VERIFY_PROFILE capture was prepared using the exact A1E6 binary/config, original Hermes sampling, strict3153slots/20479MiB, and finally restore. The shell that would stage/launch it was rejected before execution by automatic approval review: explicit permission to stop the live API is required under the user's process rule. No API stop, GPU profile upload/run, alternate profiling route or retry occurred. The permission question is pending; no default answer was assumed.

P3 new Q6 dense layout/kernel and P4 new fusion are therefore NOT_MEASURED. Actual current cost/adjacency evidence remains missing; no +10% estimate or quality conclusion is invented. This is PARTIAL, not a completed four-direction campaign.

## Identity, coverage and operational state

Fresh strict-host SSH verified DESKTOP-LKMLUPC; source f520bc5e9d31c93caeb296b059e3a3eaa16e493f clean. Current-best binary A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8 and config060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93 match actual disk/BEST. GitHub main and all task heads refreshed unchanged; main e19a73c18ab455ffd02cdafa5ff8cfdd33739fa8,027 da28699...,028 already consumed. No new claim was created.

The prior small-flag controller is DONE with API restored; current API PID30648 was freshly classified. P1/P2 prebuild/per-case/postrun identity/process/API-idle gates passed, same API PID,3153slots/20479MiB,AboveNormal and original env. No temperature/request sampling changes, engine source edits, API stop/restart, new best or deployment in P1/P2. Candidate/static-library/source hashes are preserved in raw/source-identity.json and binary.json; raw files carry SHA manifests locally.

Coverage: P1 one GU format,two row groupings,two cores,three nt values,two timing extents; P2 one format,two cores,nt2/3,three reuse batch sizes,two extents. Both use actual native expert bytes and actual type42/type20 down dispatch. Pattern enumeration covers all entries of the five actual grid tables. Output parsers verify both DONE receipts and expected24 metric rows per experiment.

Limits: one synthetic activation seed,36 deterministic experts per format,not every layer/expert or real hidden-state distribution. No semantic generation quality evaluation, row-partition/multiworker contention test, full-pack hash, new GPU kernel, GPU timing, whole-engine A/B or proof that the entire design family cannot improve. Broad source search only found existing profile controls; semantic inspection was limited to the named consumer/profile sections, not every consumer or CUDA path.

Remaining action: receive explicit API-stop authorization, then re-inventory live processes and run the prepared GPU-cost diagnostic with restore/independent verify. If authorization is withheld, preserve this partial result and keep the API running.

## 2026-10-30 follow-up: authorized GPU diagnostic completed

This section supersedes only the earlier pending API-stop permission/current process status. User explicitly answered「允許暫停並於測後恢復」. STATUS remains PARTIAL / REPORT_LOCAL: the three-request cost diagnostic is complete; new P3/P4 kernels and whole-engine +10% are not measured.

Attempt1 was stopped by the inherited replay harness assertion prohibiting STRATA_VERIFY_PROFILE, before a test engine launched. Finally restored API, independently checked by controller. No data from that attempt is used. Attempt2 preserves the original harness and creates a separate copy differing only in the assertion requiring PROFILE arm/value1. Before stopping API, the complete config is compared with the original: only cwd/log plus the intentional profile env differ. Both attempts and restore receipts remain append-only files.

Attempt2: exact A1E6/060F, p01/p05/p08 original temperature1/top_p/top_k/min_p/seeds, only max_tokens128. All three completed, 70/84/58 windows. Capacity3153 slots/20479MiB, priority AboveNormal, no CUDA/fatal. Evidence: gpu2-meta.json, gpu2-rows.json, gpu2-profile-lines.json, gpu2-engine.log, gpu2-inputs.json; remote under runs/big-exact-20261030/gpu2-out/block-00-PROFILE-r1.

| instrumented ms/window | p01 | p05 | p08 |
|---|---:|---:|---:|
| waitCPU (GDN+QSA) |29.25|18.42|36.54|
| broad attention projections |4.81|4.70|5.07|
| shared+quant |0.97|0.94|1.02|
| copy+combine |0.53|0.49|0.61|
| hc0 norm/down/up combined |2.05|2.02|2.10|

The broad projection group is GDN q8+qkv/z/out plus QSA q8+kv-idx,k/v+norm-rope,q+q-idx,out. It includes quantization, mixed formats and other work: it is NOT measured Q6-only time. Even unrealistically attributing all this group to one optimizable target, saving3.37ms/window would require approximately3.0–3.5× acceleration of the group in this instrumented execution. This is a conditional hurdle, not a true live Amdahl bound or forecast. It does not justify implementing a whole-model same-VRAM replacement yet. P3 remains NEEDS_ISOLATED_Q6_COST_AND_SINGLE_CONSUMER_PROTOTYPE, not NO_GO for all GPU layouts.

For P4, the individual shared+quant, copy+combine and hc0 chains are each below3.37ms/window even if made free in this capture. They are not automatically independent/additive, and existing shared stream overlaps work when profiling is off. Existing source already fuses gr-read and recurrence/norm work; LFUSE/QFUSE are not reopened. No newly identified removable adjacency with sufficient exposed cost was established. P4 remains NEEDS_UNINSTRUMENTED_ADJACENCY, not a completed fusion experiment.

Important source correction: accumulate_profile subtracts hc-read0 parent when all hc0 split timestamps exist (verify.cpp1964..1970). This output prints the split only; its reported total is not double-counted by that split. Conversely do not add a reconstructed parent again. Earlier generic warning about hc0 double counting was precautionary, not an observed source bug.

Operational limits: STRATA_VERIFY_PROFILE disables shared side stream/DF_BRANCH and inserts GPU stamps; waitCPU includes host pipeline waits, not pure CPU arithmetic or GPU-fusible work. Reported34.74–54.00ms/window and32.5–41.4tok/s are instrumented diagnostic results, not baseline regression or speed comparison. Three short original-sampling requests are not semantic quality validation. No new GPU kernel, same-input parity, per-matrix timing, actual original-stream timeline or whole-engine A/B was completed. Source evidence is limited to named verify/profile/consumer sections; not an all-source audit.

API restored at local10:22:27 with original binary/config/env/priority/capacity. Fresh independent postgpu verification returned INDEPENDENT_POSTGPU_OK, PID32568, loaded/idle/queued0; STRATA_VERIFY_PROFILE absent, CPU libraries unchanged, only classified API/watch processes, no benchmark/build leftovers. Receipt raw/independent-postgpu.json and process/verify-independent-postgpu.json. No deployment, model/sampling changes or GitHub publication. The old publication restriction is unaffected by API-stop permission.

Decision: P1/P2 tested NO_GO prototypes; P3/P4 diagnostic completed but implementation/performance proof still pending. No candidate supports a +10% claim. Avoid escalating to a large rewrite from these coarse instrumented totals; next evidence would require isolated Q6 current-kernel costs and original-stream adjacency, not more flag sweeps.
