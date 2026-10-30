# Research-only candidate contracts — 2026-10-18

ReMoE、CommitMoE、FloE 已各自定義 landing prerequisites，但目前都不是 cache-only、低風險 source A/B：

- ReMoE 需要 router training/conversion 與 quality/parity。
- CommitMoE 需要改 expert-selection/fallback semantics，必須先有明確授權與品質風險測試。
- FloE 需要 Qwen IQ3-compatible compression artifact、重建誤差與 PCIe/RAM budget；不能把 Mixtral 結果直接搬過來。

目前只保存 contract，不做 fine-tuning、router replacement、fallback change、compression artifact、benchmark 或 global-best claim。本工作單元沒有遠端操作。
