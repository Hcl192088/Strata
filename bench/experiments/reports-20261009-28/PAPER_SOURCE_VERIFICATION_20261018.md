# Paper source verification — 2026-10-18

正式來源已核對，並將論文方法與 Strata 目前證據分開：

| 方向 | 已核對來源 | 可帶入的實作邊界 |
|---|---|---|
| Fate | arXiv 2502.12224，2025-02-17 | cross-layer gate、shallow-favoring cache、量化/IO；先做完整 trace diagnostic。WWW 2026 未由目前查到的官方來源確認。 |
| ReMoE | PMLR，ICML 2026 | router fine-tuning；不是 cache-only source A/B。 |
| DoMoE | IJCAI 2026 | domain routing tables + domain-restricted semantic matching；目前 Strata 只有 static profile load/save。 |
| HOBBIT | arXiv 2411.01433，2024 | cache miss 使用較低精度 expert、prefetch、mixed-precision cache；IQ3 沒有現成 lower-precision artifact。 |
| CommitMoE | AAAI-26 | fallback-free Commit Router；改變 expert-selection semantics，需 quality gate。 |
| FloE | PMLR，ICML 2025 | expert matrix compression + sparse prediction；論文是 Mixtral/RTX 3090 等配置，不可直接套 Qwen IQ3。 |
| SRP/SCH | ICLR 2026 | 先量測 local-routing ceiling；不等於 throughput 或 Strata 實測。 |

這次修正的是來源 metadata 與落地邊界，不是 Strata benchmark。沒有啟動遠端 run、修改 source/model/scheduler/temperature，也沒有使用 fallback。
