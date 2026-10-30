# 夜間診斷中間結果，非最終結論

更新：2026-10-29 00:39 Asia/Taipei。直接使用者夜間自主測試授權，Task027 continuation。遠端runner仍在跑，未重啟；最晚07:00停止。每小時heartbeat已設定在本thread，未宣告完成。

## 第一輪診斷

來源：遠端 overnight-20261029/out/block-03-D-r1，10請求820 windows。下載rows.json/phases.json並執行analyze_phase.py，window、CPU對帳通過。

CPU24.6465ms/window：GU12.4653、quant0.1409、down5.4019、join5.3318、LRU1.2816、殘差0.02488。GU包含worker平衡與記憶體stall，不是純解碼指令時間。helper9.4518、direct9.5263、copy1.8947、issue/wait7.6127ms/window彼此重疊，不能與CPU分項相加。

issued/useful bytes=1.001663；已讀取bytes過量約0.1663%，不能從此論證減少miss沒有價值。LRU1.28ms屬同步CPU關鍵路徑，但即使完全消除仍只約達2.47ms缺口一半；實際不能直接全部消除。join5.33ms包含helper完成/排程，不是純SSD service。

第一輪C為Normal，O中途調AboveNormal，兩者速度對比排除。D引擎PID5300在16:34:55.232Z調為AboveNormal，首請求完成16:35:27；需最終用request開始時間證實調整早於量測。watcher記錄priority-watch.jsonl；後兩輪仍須核對。沒有promotion或修改current-best。

## 接續

先讓現有C/O/D三輪跑完，再比較分項穩定性及計時擾動。候選聚焦GU、join、拷貝/LRU；不能因read amplification低便否定cache miss策略。優先檢查固定GPU集合/固定容量下可否避開同步重複拷貝；不能以更改GPU placement繞過tail-skip限制。

Coverage：本階段完整第一輪10點phase紀錄，probe3點僅守恆；其餘兩輪尚未完成。不是全campaign或效能改善結論。首輪C/O priority偏差已寫ledger。部分結果曾在D尚未落盤時解析失敗，未重跑runner；D完成後讀回再解析成功。

## 00:45 第二輪累積

完整D兩輪20點1830 windows：CPU24.3991、GU12.0423、quant0.1498、down5.2112、join5.7538、LRU1.2173、殘差0.02471ms/window。讀取放大1.001657，helper拷貝1.7532ms/window，與CPU/其他helper項不相加。D/O唯一priority-matched完整輪暫為+2.84%，樣本僅1且window mix不同，不能判定插樁無開銷或效能改善。

結構候選：目前read_direct將對齊scratch拆拷到stage_buf，ram_lru_complete又在CPU jobs結束同步拷到complement arena。可評估cache admission目的地預先綁定，消除後一份拷貝；但只能約1.22ms的理想上限，不足單獨達50。若合併改直接讀目的地還涉及4096對齊、GGUF三role分散及合併ReadFile請求，不能假裝改一個memcpy即可全省helper1.75ms。

預綁定須維持原ids順序、LRU clock/touch/victim、保護GPU/PCIe/staged/adapt pairs、只驅逐未route expert、同容量；且prefetch_split_begin後才能重導fills，不可在此之前發布resident而跳過實際read。fill_many原先publish_stage語意要求stage_buf的內容有效，重導到arena若仍標stage ready會留下陳舊bytes，不能直接實作。這是需解決的上游生命週期問題。

遠端rg不存在，pool實作檔定位命令失敗於工具層；未用替代搜尋流程。現有expert_source.cpp targeted核對可繼續，不阻礙已在跑的三輪診斷。候選尚未實作或測速。
