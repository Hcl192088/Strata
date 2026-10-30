# DoMoE-adjacent profile matrix — 2026-10-18

This work unit converted the existing learned-profile report into a structured matrix. It did not start a remote benchmark and does not claim a DoMoE reproduction.

## Existing evidence

- Source: `D:\strata\reports\Strata_筆記learned_profile轉移測試_2026-10-05.md`
- Profile: `learned-heart.bin`
- Profile SHA256: `AA28BA0800A598DE0D83EBD83E918E2736BB2F4AB6750DB8AA72461E5829510F`
- Historical quantization: `IQ2_XS`; current target: `IQ3_XXS`
- Capacity-matched comparison: 3977 slots, two matched runs per arm per workload.

| held-out workload | combined tok/s | learned-profile tok/s | relative gain | hit gain | interpretation |
|---|---:|---:|---:|---:|---|
| anti-hypertensive | 26.92 | 27.68 | +2.82% | +1.70 pp | insufficient generalization |
| 神解 | 27.45 | 29.26 | +6.59% | +6.77 pp | positive single held-out direction |

## What this proves

It proves that one profile trained on the `heart` workload had a positive result on the stored `神解` held-out workload and an inconsistent/small result on `anti-hypertensive` under the historical IQ2 setup.

It does not prove DoMoE, because there was no semantic domain classifier, no explicit domain routing table, no current IQ3 reproduction, and only two runs per arm.

## Next safe action

Use this matrix to select a genuinely new domain/profile combination or an offline routing-trace matrix. Do not repeat the same two comparisons. Any IQ3 remote test must first revalidate host, process inventory, source identity, binary SHA256 `366A355E0E866B12D1793C9D8BE022925305B4560E1AE7DC47F8716C865015E2`, prompt, sampling and capacity.

## Coverage

Read the complete named profile-transfer report and preserved profile hash/results available in local state. No remote raw log was re-read in this work unit; no source, model, process, schedule or temperature was modified.
