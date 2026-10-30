# Fate trace integrity audit — 2026-10-18

以唯讀 byte-level audit 重跑現有 `hermes-routing.frozen-01.bin`：

- SHA256：`87CA2E3EA201E4AFEB27C415BBFC4927D67EFFC4ECFC6D97F1F3E94AA291509D`
- 失敗位置：header offset `20,742,128`，payload offset `20,742,136`
- 宣告：layer `8`、route width `10`、應有 `80` bytes
- 實際：只讀到 `8` bytes，EOF 後剩餘 `0` bytes
- 失敗前完整 records：`235,706`
- 失敗前完整 windows：`2,307`

因此這個檔案確實在 record payload 中截尾，不能當成完整 trace 送入 SRP/SCH，也不能用舊報告中不同 SHA 的 `12,569` windows 取代或合併。本 audit 沒有修改 trace、遠端狀態、source、model、排程、temperature 或 process。
