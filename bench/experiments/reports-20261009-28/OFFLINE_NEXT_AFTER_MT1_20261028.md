# MT1 後的下一步：使用者遊戲期間，本機離線分析

範圍：只讀 D:\strata 既有 source 快照、300 列 replay JSON 與報告，不 SSH、不跑桌機測試、不改服務／排程／溫度。使用者接受相同數學運算的浮點順序差異，仍排除路由偏置、跳過 expert、重新量化及硬體。

## 這輪重新算出的 MT1 資料

輸入：iq3s-mt1-ab-20261028/out/rows-AB.json，完整 300 列；MT1 為 100 請求。依 window 數加權：window 40.855 ms、CPU 23.903（58.51%）、GPU-reach 11.769、jobs 0.275、draft 1.825、1.919 tokens/window；全部 MT1 token/全部 decode time 合併 46.972 tok/s。不是新測量。達 50 約需再減少 6% 時間；不可把更高 neuro 速度當 Hermes 已達標。

該 100 請求 sum(prefill)/sum(prefill+decode)=68.89%，prompt reused/prompt total=18.92%。每 block 新引擎且題目不同，這不證明 live cache 失效，也不是自然流量比例；不能據此宣稱有 69% 可節省。p01..p10 median decode tok/s=33.39/39.67/37.17/44.62/48.80/47.85/48.14/52.57/52.67/49.74，50 tok/s 並非各點均成立。

## 1. 先判 gate/up–down 交錯是否值得做

實際讀到 worker-skew-20261028/src/pool.cpp:761 起：同批所有 expert run_phase(5) 完畢，host 逐 expert/token 量化，再 run_phase(6)。因此「不同 expert 能否提早進 down」有具體 source 依據，不只是時間線想像。run_phase 採全域 mode_、mrows_、mtasks_，不能直接同時呼叫兩個 phase；必須設計帶 phase 類型的任務與每 expert completion 狀態。

最小可交錯單位是 expert：該 expert 全部 gate/up 列完成，保留原 activation/quantization，再允許 down 列工作；不改每列 kernel 或 expert 最終合併順序。scratch 目前依 expert 分開，但完整 ownership/lifetime 與 reduction 路徑仍需確認；不是已驗證 thread-safe。

現在可做：列依賴、所有權、最少需改的介面；用既有 phase/worker 彙總建立共享頻寬下的保守/樂觀界線。現有分析 JSON 沒有完整逐 expert readiness 時序，無法誠實還原完整 pipeline speedup。原診斷基於 S2K/neuro，MT1 已加速 gate/up，舊 +3..6% 或 +11% 上限均不能直接沿用。若資料不足，先列最小 measurement 需求，不自行插樁測量。

## 2. 小型 kernel 候選：IQ2_S 的 nt=1，用現有 VNNI-only 變體

既有 all-types 微基準：P-core LP11 207.1→164.6 us（1.258x）、LP1 216.8→172.2（1.259x）；E-core 486.3→381.6（1.274x）。benchmark 原碼已有 iq256_gu_rows_v(variant=2,...)。適合先設計「只針對 type22/nt1」的 dispatch，不要把所有型別 MT_MIN 設成1。

不能全域關 gather：MT1 的 IQ3_S 快路徑依賴 gather 設定。IQ2_XS 在 E-core 的替代 kernel 只有 0.785x，也不能一律切換。優先讓同型別跨核心走相同數值 kernel，避免額外引入按 worker 分配改變 rounding 的行為。

粗估：沿用舊 8.8 ms GU 與層數等權近似，IQ2_S 單項約 0.3 ms/window 級；模型跨工作負載且未計 MT1 後的分工，僅用於篩選，不是實測，也不能預測穩過50。可能小於整機 A/B 的可分辨範圍，因此不先排一小時級 A/B；先設計短的同輸入微基準與正確性比較。

## 3. 實際等待時間：先稽核既有 prefix/KV 重用

與 decode 50 目標分開。先從已保存 server/client 路徑與資料檢查共同 prefix、reused/read、壓縮後 prefix 改變及 cache 容量；若沒有自然流量資料，明列缺口。不要先新增快取層、截 prompt、改採樣或用此 fresh-engine replay 判 live cache 壞了。此項若之後需要桌機 log，等使用者結束遊戲再做唯讀檢查。

## 優先順序及停止條件

先交錯依賴/上限分析；IQ2_S 做小候選設計，未證明可測增益就不排長 A/B。跨層 RAM 配額、SSD 空隙讀取/搬運留後順位，已有資料不支持先重構。Git 憑證問題與部署已分開記錄，不占用本輪分析工作。

## Coverage

完整處理 replay 300 列並擷取 MT1 100 列；targeted 閱讀 native header、pool 相關工作分派/phase 函式、all-types 微基準與既有 pool-split/gu-tasks 報告相關段。沒有全面 source audit、沒有 raw kernel 微基準重算、沒有逐 expert 時序、沒有 MT1 新 trace、沒有自然 Hermes 流量分析、沒有遠端操作。分析未停止目前常駐 API。
