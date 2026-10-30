# Routing trace capture contract — 2026-10-18

這份 contract 只定義未來完整 trace 的 evidence 與 parser gate，沒有啟動 capture。

現有 validator `simulate_ram_routing.py::windows` 的硬性條件是：每筆 record 為 little-endian `int32 layer + int32 k`，payload 必須完整讀到 `k*8` bytes；layer 必須連續，window 必須完整包含 48 layers，且同一 window 的 token count 與 route width 必須一致。EOF 若落在 partial header、partial payload 或 incomplete window，整個 trace invalid，不能截斷、修補或丟棄 tail。

未來 capture 還必須凍結 binary/source/config/model、prompt/seed/hash、temperature/sampling、context/KV/cache，保存遠端 raw path、size、SHA256、capture 時間、process gate 與 scheduled API non-interference evidence。完整 window 數量必須在 capture 前宣告，不能事後挑門檻。

目前 `hermes-routing.frozen-01.bin` 仍是 `INVALID_PARTIAL_RECORD_PAYLOAD`，不可作為 capture output 或 SRP/SCH 輸入。本工作單元沒有遠端 run、source/model/scheduler/temperature 修改、process stop 或 fallback。
