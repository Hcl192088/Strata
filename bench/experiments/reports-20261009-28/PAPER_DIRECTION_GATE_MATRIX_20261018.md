# IQ3 paper direction gate matrix — 2026-10-18

這是目前六個論文方向的單一 gate 入口。它把「論文提出過」與「目前 IQ3 已有證據」分開；方向性的 soft blocker 不會讓整個 campaign 停止。

| 方向 | 目前狀態 | 現在可做 | 下一個必要 gate | 是否可量測 |
|---|---|---|---|---|
| Fate | `DIAGNOSTIC_ONLY / BLOCKED_INPUT_INTEGRITY` | 保留 partial trace 與 parser/provenance 證據 | 取得 hash 與 parser tail 都一致的完整 approved routing trace | 否 |
| DoMoE | `PARTIAL_DATA_ONLY / NOT_READY_NO_COMPLETE_TRACE` | 維持零測量 profile matrix、去重 48x512 artifacts | 完整 trace，或明確核准的 matched IQ3 run；需 profile/domain/parity/decode evidence | 否 |
| HOBBIT | `FEASIBILITY_ONLY / PARTIAL_NO_LOWER_PRECISION_ARTIFACT` | 維持 native expert size 與 RAM feasibility | 真實 lower-precision artifact，或核准的 conversion/parity/RAM/quality plan | 否 |
| ReMoE | `RESEARCH_CANDIDATE / NOT_LANDED` | 只記錄 router fine-tuning prerequisites | 核准的 Qwen router train/convert、品質 parity、matched accepted decode | 否 |
| CommitMoE | `RESEARCH_CANDIDATE / NOT_LANDED` | 保留 quality-risk 與 tail-skip 的界線 | 核准的 expert-selection change、parity 與 matched accepted decode | 否 |
| FloE | `RESEARCH_CANDIDATE / NOT_LANDED` | 只記錄 IQ3 compatibility/transfer prerequisites | IQ3-compatible compression artifact、parity、RAM 與 PCIe evidence | 否 |

## 自動續跑規則

- 本輪 hard blocker：`0`；方向性 soft blocker：`4`。它們不是 campaign-wide stop。
- 沒有新證據時，下一個安全工作是 ledger、state consistency 或 runner-contract 的離線整理；不重跑已完成的 adapt-every，也不把 `iq3-ram-adapt-013` 當 fallback。
- 在同 source、isolated runner 出現前，adapt-async 只保持 readiness-only。
- 不改 temperature、不停 process、不改 live IQ3 API、不做未授權的 router/quantization/compression 變更。
- 心跳唯一的自動暫停條件仍是週用量剩餘量嚴格大於 `60%`。

本工作單元沒有啟動遠端 run，也沒有修改遠端 source、binary、model、排程或 process。
