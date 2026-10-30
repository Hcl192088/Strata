# DoMoE candidate provenance audit — 2026-10-18

對 `DOMOE_CANDIDATE_MATRIX_20261018.json` 與 `DOMOE_PROFILE_CATALOG_20261018.json` 做唯讀交叉核對：

- 10 個 included candidates、10 個 unique profile hashes。
- 0 個 hash 找不到 catalog、0 組重複 hash。
- 10 個 included candidates 全為 `48x512`；`coder` 的 `48x256` 已排除。
- domain planning labels：neuro 4、heart 2、pitching 1、travel 1、UNKNOWN 1、UNKNOWN_MULTI_TOPIC 1。
- source quantization labels：IQ2_XS 5、IQ2_XS_HISTORICAL 2、UNKNOWN_LEGACY 3。
- current IQ3 profile artifact：0；完整 routing trace：否；domain selector：否。

因此 matrix 的結構與 provenance 已可用於去重與未來 trace planning，但沒有任何測量或 deployment ranking。沒有複製、轉換、選擇 profile，也沒有啟動遠端 run。
