# CPU R4 screen — completed, no promotion

Task: LUNA-20261012-027 continuation. Authorization: user「去做」following CPU_R4_NEXT_20261029.md. Status: COMPLETED / NO_GO_BOUNDED_SCREEN / REPORT_LOCAL.

The pinned AVX2 four-row IQ implementation does not support the requested whole-engine +10% target on this host. Keep current best. This closes this particular implementation/screen, not every possible row-interleaved kernel.

## Corrected complete-expert results

Numbers are A/B−1 throughput percentages from median microseconds per expert; A is the current deployed CPU library, B changes GU only and retains the actual live down/activation dispatch. Not engine tok/s. Each cell is 9 interleaved AB/BA pairs on 36 experts.

| Format | P nt1 | P nt2 | P nt3 | E nt1 | E nt2 | E nt3 |
|---|---:|---:|---:|---:|---:|---:|
| IQ2_XXS | +26.1% | +2.9% | −6.3% | +15.7% | −2.1% | −7.3% |
| IQ2_XS | +2.8% | −15.7% | −18.2% | +0.4% | +7.0% | +4.9% |
| IQ2_S | +12.3% | +9.5% | −0.9% | +18.0% | −7.7% | −2.0% |
| IQ3_XXS | +10.4% | −8.4% | −22.8% | +9.9% | −4.8% | −6.7% |
| IQ3_S | −26.5% | −24.0% | −23.0% | −9.9% | −5.9% | +2.0% |

13/30 positive,17/30 negative; do not average these uniformly into an engine forecast. Best cell 1.26134×, worst0.73514×. Many single-token cases improve; multi-token reuse already exists in current Strata, and current IQ3_S P-core gather/MT1 path beats this reference. This explains why GU load-sharing alone is insufficient here; no instruction-level attribution was measured.

Even granting every existing CPU compute segment an optimistic1.3× (greater than every measured combined median), the previously captured fixed-I/O model gives only+8.059%, before new conversion costs. About1.4× all-compute is needed for+10%. This conditional feasibility comparison is not a rigorous universal upper bound: real pool row partitions, contention and operation weights differ from this single-thread full-row screen. It gives no basis to invest in integration now.

Conversion cost for both GU matrices per expert: P pack209.66–822.65µs, inverse187.62–1223.00µs; E pack371.51–1343.38µs, inverse335.09–2067.02µs. These are not included in the timing table. They further weaken dynamic admission; no second resident copy, full-pack conversion or new cache was implemented.

## Correctness and coverage

- All five actual native GU types; 6 selected layers/type (30/48),6 experts/layer:180 unique experts out of24576. Same samples on LP2/P and LP15/E; fresh process/core/type, pinned before ISA dispatch, BelowNormal. Formats represented9/10/10/6/13 actual layers respectively, not equal model weights.
- 396,288,000 bytes roundtripped exactly across both cores;1,179,648,000 decoded values matched exactly. GU packed size equals original GU size. A/B allocates both copies for measurement only; no production memory-parity claim.
- All30 corrected numeric cells finite and passed the declared mechanical h-error screen. Maximum h absolute difference9.53674316e-7; maximum downstream absolute difference0.000427365303. Float results are not bitwise equal. No language-quality/non-regression gate, real hidden-state distribution or semantic evaluation was run. Do not call quality preserved.
- Corrected combined:30 cells×9pairs=270pairs/540 timed passes;77.594s campaign. All raw lines parsed with completeness assertions. Prior GU-only30 cells retained in wrong-down-attempt logs. No extra parameter sweep or formal engine A/B.
- Source inspection targeted the relevant reference types/repack/dequant/AVX2 kernels and current native_expert/pool/expert_layout dispatch. Not a repository-wide audit. No AVX512 or new AVX-VNNI candidate, runtime scheduling/multiworker contention, all-expert scan, real conversion-admission implementation, end-to-end inference or throughput validation. No weighted nt/core inference because required joint live weights are unavailable.

## Engineering errors retained

1. MSVC half-conversion intrinsic and compile/link include handling failed before measurement; logs build-attempt1/2 retained remotely. Fixed equivalent F16C intrinsic, private header include and object link placement.
2. Initial adapter assumed ik_llama.cpp Q8_K296-byte ABI; live Strata is292 bytes (no extra sum). Two numerical attempts stopped before valid arithmetic timing; raw failures/binaries retained in numeric-attempt1/2. Corrected adapter directly reads live292-byte activation, with static size assertion; no conversion or fallback.
3. Initial completed matrix used ggml scalar Q2_0 down, while actual pool.cpp uses act_quant_any/q2_rows_any. Its combined results are invalid and excluded. Original logs/binary remain in wrong-down-attempt. Fixed same dispatch and reran only combined on unchanged samples/design; did not repeat GU timing. Final source includes the real type42 branch and unchanged type20 native_down_rows. An additional verification shell quoting failure was corrected by a saved verify.py; independent verification then passed.

## Identity and operational outcome

Remote DESKTOP-LKMLUPC; canonical run `C:\Users\User\Strata-Adrian-control\runs\cpu-r4-20261029` (junction resolves under Strata-Adrian\repo). Native pack42912972800bytes; metadata SHA AE28CF7A2A1C9063C4B55D6C8CF86D4D079DCDDCF597F9E8697C9157D462C0EE. Original sampled expert IDs/layers in ITEM records; no42.9GB full-pack rehash.

Current source f520bc5e9d31c93caeb296b059e3a3eaa16e493f; current-best binary A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8; config060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93. Fresh current-best/BEST/process gates used before build/each cell; exact deployed CPU/ggml library hashes in raw/build-inputs.json. Reference ik_llama.cpp d4c1f75533ec897f54944f2734ea0d0e89e4fe01; MIT LICENSE retained. Candidate EBC611F71C29A0264CFEB5253D00DD6E78496D95D934B00D0E339052629036CA.

Independent postrun: original API PID27640, AboveNormal32768, loaded,3153slots/20479MiB, original env/config/binary retained. Idle/queued0 and request totals0 throughout, no foreign benchmark/build leftovers. No API stop/restart, temperature change, engine source edit or deployment. Main raw manifests and analysis.json preserve provenance; full remote failed attempts remain at their original paths.

GitHub publication remains REPORT_LOCAL. Earlier automatic approval review rejected the report/commit/push payload pending explicit payload-publication authorization. No retry, publication-route change, commit, push or guard-state rewrite in this experiment.
