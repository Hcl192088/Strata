# Gate/up–down 交錯：離線上限判定

本輪已讀並使用 `.claude/skills/strata-checklist/SKILL.md`。只做本機 JSON 計算與 source 快照核對；沒有 SSH、引擎、build、模型請求、系統設定或服務操作。本機不是 Git 倉庫，不建立倉庫或 push。

## 計算結果

MT1 Hermes 既有 100 請求合併為 46.9715 tok/s（21.2895 ms/token），到50尚差1.2895 ms/token。對應現有40.8545 ms/window，約需省2.4745 ms/window（固定 accepted tokens/window 的情境）；若只動CPU，需削減目前23.9030 ms/window的10.35%。這不是實測預測。

| 同一工作負載假設每 window 省下 | 推算 tok/s |
|---:|---:|
| 0.5 ms | 47.55 |
| 1.0 ms | 48.15 |
| 1.5 ms | 48.76 |
| 2.0 ms | 49.39 |
| 2.5 ms | 50.03 |

ON1+ON2完整原始 worker dumps（S2K/neuro、非MT1/Hermes）共1138 windows、52480 pool calls，重新加總得：gate/up 9.4876、down3.4886、quant0.0939、pool總13.1043 ms/window；每call平均4.464 experts。logical weight traffic354.4455 MB/window，以歷史純讀45.7 GB/s為參考流量下限7.7559 ms/window，但這不代表pool可達該時間。

gu/down 的 phase wall 有效流量分別23.97/36.42 GB/s；與先前引用每worker忙碌時吞吐相加的29/44 GB/s口徑不同，不能混用來宣稱持續飽和。舊445MB/window→9.7ms下限及+11%是另一套外推，不能當成本輪已重現的完整計數結論。

同時，十個執行緒的閒置core-time除以十，只有2.1197 ms/window；這是假設各core相同且busy service不變時的資源鬆弛量，不是可收回wall time。P/E差異、expert readiness、GU/down共享CPU和DRAM使其不能直接移植到Hermes，更不能用它宣稱「pipeline一定過50」或「一定不可能過50」。

## Source 可行性與缺口

本機 pool.cpp:761確有整批GU→host逐expert量化→整批down。不同expert提早完成後可否先down是一個結構假設；但mode_、mrows_、mtasks_是全域phase狀態，不能直接把現有run_phase(5)/(6)並行呼叫。需要帶階段資訊的task、每expert的完整GU completion與一次量化、固定scratch生命週期，且保持原每列kernel與最後合併順序。

wskew_trace.hpp 明確只存按(T,kind,mode,thread)的加總；沒有逐expert的ready timestamp或原任務序列，因此無法從這兩個dump重建真實pipeline。不能用平均expert數假裝逐事件模擬，亦不能把min(GU,down)當可重疊量。

**判定：暫不進長A/B或完整pipeline實作；沒有足夠資料確認保守收益≥3%。沒有判定整個方向無效。** 下一個必要證據是MT1下每expert GU-ready/quant-ready/down-finish和phase資源使用；等使用者不玩遊戲且另行授權時，再擬單一短機制探查，不先排長測試。

## 防打轉 checklist 逐題回答

### 第1節
1. 目標50，目前既有MT1 replay46.97；差1.2895ms/token，非目前即時速度。
2. 10/28同binary、MT1 env的完整Hermes rows重算：window40.855、CPU23.903、GPU-reach11.769、jobs0.275、draft1.825ms。舊ON1/ON2為S2K/neuro，對current best拆解過期，不直接沿用作預測。
3. 針對CPU內phase順序。CPU全歸零的Amdahl算術上限113.20tok/s，非物理可達；交錯本身可回收份額未知。若最終只能省0.5ms/window，仍須其他方向補約1.97ms/window，單項不達標。
4. 最近為BW→worker-skew→kernel probe→兩次micro→MT1 AB，是同CPU主題的結構/機制工作，不是三次同旋鈕雜訊內掃描。MT1按輪+4.26%且CI排除0已採用。下一筆不重掃worker/spin/affinity。
5. 不重做GU30/60 tasks、P/E重新分配、PIN/AA/PATCH4或MT_MIN全型別開啟。交錯是變更跨expert階段依賴，與只改task數不同；仍未證明效益。
6. 結構方向逐類考慮：miss/RAM策略已有模擬且小收益；改計算位置PIN/GPU-only prefetch已有負面證據；等待計算重疊是本輪；減計算量的MTP深度有負面結果且不改本輪路由/計算量；mainline既有Windows/Qwen差異已記錄，沒有新證據支持直接rebase。IQ2_S的type22-only kernel保留小候選，非全型別切換。
7. PATCH4的join轉chunk沒有減總等待；PIN使CPU下降但GPU等待上升，組合有400；worker已動態分配、沒有足夠不平衡。這些根因支持停掃各已測具體候選，不等於所有I/O或CPU演算法都已無解。pipeline缺的是readiness證據，不能用現有資料宣告失敗。

### 第2節
本輪是既有檔案離線算術，不啟動A/B或benchmark。若未來機制探查獲授權，必須先另登樣本數、上限、停止條件與identity gate；本文件不是遠端執行授權。

### 第3節
本輪沒有啟動任何遠端工作，未查遠端即時狀態、未委派agent，也不做SSH營運巡檢，以免干擾使用者遊戲。未替使用者停止常駐API。

### 第4節
- 已完成MT1部署不是待辦；不要再花時間重做部署或認證繞路。
- 本輪上限計算已完成，機制資料不足是明確下一證據，不把「繼續想pipeline」當無期限工作。
- 下一個結構性單位是設計最小的per-expert readiness探查；在缺少新資料期間不寫完整pipeline，也不開旋鈕掃描。

## Coverage / 驗證

完整解析ON1/ON2兩個wskew.json的thr/phase/call全部紀錄；ncalls守恆、GU/down phase數等於call數、busy不超過十執行緒phase wall、phase+quant不超過call wall均通過；從兩份stderr各取唯一decode window總數。Hermes replay全部300列檢查，其中MT1的100列無error並完整合併。未重跑微基準、未處理MIC的插入測試開銷、未模擬逐expert時序、未確認MT1新phase資源輪廓、未全面掃source或原始log。source僅核對pool phase/worker與dump schema。

可重算命令：`python D:\strata\state\worker-skew-20261028\offline_pipeline_bound.py`。數字與來源SHA：同資料夾offline_pipeline_bound.json。

目前方向是先證明跨expert交錯的實際可重疊份額，而非直接實作。本輪沒有新增旋鈕掃描；離線可辨識的上限/缺口已算完，等新的必要證據前停止擴張分析。
