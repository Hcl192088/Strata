# Ledger contract audit — 2026-10-18

對目前 22 筆 `EXPERIMENT_INDEX.jsonl` 做 schema/decision-boundary audit：

- required fields 全部存在：`experiment_id`、`paper_direction`、`scope`、`status`、`local_evidence`、`remote_run_started`、`next_gate`。
- 22 個 unique IDs；0 個缺欄位；0 個錯誤 remote-run type。
- 0 個 unsupported global status。第一次檢查曾把 `COMPLETED_GATE_MATRIX_SOFT_BLOCKERS_NON_GLOBAL` 誤判為 global，修正條件後重跑通過；`NON_GLOBAL` 是防誤宣稱標記。

這只證明 ledger contract 完整，不證明遠端 benchmark 或論文方法已落地。本輪沒有遠端操作、source/model/scheduler/temperature 修改、process stop 或 fallback。
