# R4 actual pool continuation — incomplete preflight

TASK LUNA-20261012-027 direct-user continuation; STATUS PARTIAL / REPORT_LOCAL. 本輪未建立或執行 actual-pool candidate，未量 speed、語意品質，原因是尚未完成單份資料表示與全部 consumer 的實作。這是未完成工程，不是已證 NO_GO。

現場：DESKTOP-LKMLUPC，source f520bc5e9d31c93caeb296b059e3a3eaa16e493f clean；BEST binary A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8，config 060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93，磁碟實際 hash 一致。API 原 PID32568；全程未停。

核對 source：pool.cpp 721、766–785、789–859；phase_tasks 預設 3 × (workers + host)，每批 nb 上限96，GU 分成 ceil(phase_tasks(nb*640)/nb) 片，邊界 640*part/parts，非保證4列對齊；原生 down 照 type42 q2_rows_any 或 native_down_rows。lowreg 接口要求4列對齊、nt2/3；單純替換 native_gu_rows 並傳原始 blob 會以錯誤格式解碼；對所有 nt、P/E、邊界須設計明確語意，不能自動 fallback。

expert_source.cpp 2465–2480、3436–3457 返回原始 resident/mapped/staged blob；verify.cpp 2235–2247 直接把來源原 blob DMA 至 GPU；prefill.cpp 3145附近也依賴 blob_stable。可行整合需要單份 resident 對各 consumer 的格式契約、冷讀與 GPU upload 的原格式互轉或同格式 GPU kernels、workspace／lifetime 與容量；不得未經量測假定轉換成本或宣稱無解。既有 FAST_CONVERT 單 scratch 155.1 us/expert 是不同 working set，不能作此 pool 決策值。尚未實作 candidate pool、不同 nt 與 row 的 consumer 及成本計時，不得拿單核25%當 pool/engine 速度。

|項目|狀態|
|---|---|
| pool | BLOCKED on unfinished candidate/data representation engineering; 沒有測速，非 NO_GO |
| engine C/B/C | DEFERRED：pool 正面門未過 |
| 語意品質 | QUALITY_UNCONFIRMED；無 A/A、logit/loss 或可判定任務 |
| operational | TESTED preflight/final health/idle/3153/20479；API 未停，無 restore |

獨立回條 C:\Users\User\Strata-Adrian-control\runs\r4-repair-20261030\pool-preflight-final.json，SHA256 80B0EB4113EFDDC5FC0AE657B67F2C2A0148A11A0B8C4A8CBFEA43ECCB9D876E。回條未獨立檢查 priority/env；只核對 live health、容量、進程與 binary/config。無來源修改、build、benchmark、部署、sampling 修改或 GitHub 發布。
