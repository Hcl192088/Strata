# Paper applicability matrix — 2026-10-18

已把正式論文方法轉成目前 IQ3 的落地順序。這不是論文加速結果，也不是 Strata benchmark；它只決定下一個安全工作與不能越過的 gate。

| 優先 | 方向 | 目前落地模式 | 目前 gate | 下一步 |
|---:|---|---|---|---|
| 1 | SRP/SCH | diagnostic first | partial trace | 有完整 approved trace 後做 offline locality ceiling |
| 2 | Fate | trace diagnostic → source A/B | partial trace | 先做 cross-layer/locality offline，不直接改 source |
| 3 | DoMoE | profile matrix first | 無 current IQ3 trace/selector | 維持零測量 matrix |
| 4 | HOBBIT | artifact feasibility | 無 lower-precision artifact | 維持 RAM/quality feasibility |
| 5 | ReMoE | research only | 未授權 router training | 只記錄 training/conversion/quality plan |
| 6 | CommitMoE | research only | 未授權 expert-selection change | 只記錄 quality-risk contract |
| 7 | FloE | model-specific research only | 無 IQ3-compatible compression artifact | 等 locality/transfer budget 足夠再評估 |

目前 hard blocker 是 `0`；四個 soft blocker 仍是方向性，不會停止整個 campaign。下一個優先工作是完整 trace 的 provenance/capture planning，不是重跑 partial trace。

本次沒有遠端 run、source/model/scheduler/temperature 修改、process stop 或 fallback。
