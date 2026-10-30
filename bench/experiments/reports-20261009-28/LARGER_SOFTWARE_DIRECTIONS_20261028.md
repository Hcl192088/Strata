# MT1 後：改找足以補足 50 tok/s 差距的軟體方向

> 2026-10-29 修正：先前將IQ無損排列列優先的排序撤回。Hermes CPU timer含helper join及其他工作；已完成既有log離線拆解，見 `state/iq3s-mt1-ab-20261028/CPU_DECOMPOSITION_OFFLINE_20261029.md`。當前下一證據為MT1 decode起訖的helper/pool phase快照；在釐清前不投入完整IQ新格式或GPU融合。下文保留原研究假設，不能當成已驗證優先計畫或效能承諾。

範圍：使用者要求重新想較大的方法；維持相同權重/路由/有效expert貢獻，允許浮點累加差異。不換硬體、不改temperature、不SSH、不跑遠端測試。這是研究候選排序，沒有新增效能結果。

## 優先研究：減少IQ解碼本身，而非再換現成flag

具體假設：對相同量化code、scale、sign作無損的SIMD友善重排，移除熱迴圈中反覆的拆bit/排列/查表工作。不是重做量化，不刪expert；重排必須可還原原始code/scale，並驗證解碼後數值一致。只接受和MT1同類的浮點運算順序差異，不假設換成另一種低bit格式也等價。

歷史kernel快照 task015_src_kernels_cpu_iq_avx2_rows.inl 的row_dot確在每block/half呼叫Fmt32.decode，再做sign/scale/dot；它是舊快照，不是目前編譯檔權威。不能把「現有替代kernel測過」當成所有layout/演算法都無效。此方向的真正門檻：重排後是否同容量/低膨脹，否則RAM resident降低、SSD miss增加可能抵銷；不能直接展開成int8/float後宣稱更快。

下一個純本機可做單位：在已有完整型別layout來源的範圍，逐欄位列出哪些只需bit permutation、哪些需要擴充；估算bytes/row和最多能移除的操作。完整五型別decode實作尚未齊備，缺的就列明，不另抓不相符版本冒充當前source。不先寫新kernel或做全pack轉換。

外部方法佐證僅為可行方向，非Strata測速：T-MAC (https://github.com/microsoft/T-MAC)改低bit乘法為lookup；FLUTE (https://arxiv.org/abs/2407.10960)討論離線權重重排以減少unpack操作。前者不等於現有IQ codebook可直接接用；後者為GPU，不證明本CPU可有同樣收益。不採其量化、模型或宣稱倍率。

## 第二研究方向：GPU attention/router 路徑的重複資料處理與kernel融合

完整解析舊Nsight kernel summary157列，剔除wait_flag後156個kernel名稱，最大單項約有用kernel時間的6.2%。這只表示沒有單一大頭，不能推出整段沒有優化空間，也不能由名稱總表證明相鄰kernel可融合。具體要查的是串行相鄰節點是否重複讀同一activation、做相同量化/normalization或可消除中間buffer；不改矩陣/attention數學，也不重做只省host launch的adapt-async。

門檻是目前GPU-reach 11.769ms/window中的約2.475ms（21.0%），才可能單項補足差距；GPU-reach不是純kernel時間，因此這只是串行段改善的必要量級，不是可達預測。需實際graph/source與對應kernel記憶體資訊；現有表沒有kernel adjacency，故目前不能具體選fusion點或開始改程式。

## 本輪排除的假捷徑

- CPU cache/miss重排不一定只有數值誤差：本機S2K source的tail skip只跳過非GPU-resident低rank expert。改VRAM placement會改哪些expert貢獻零，不能直接當作「輸出不變的快取優化」。任何GPU配置想法必須先處理這個有效計算集合約束，不在本輪實作。
- 不再用較長MTP、confidence gate、PR1934或全型別MT_MIN的既有負面結果繼續掃參數；更高acceptance不等於更快。
- prefill/cache重用只列端到端延遲改善；不拿fresh-engine replay的prefill比例冒充decode提速。
- gate/up-down交錯、IQ2_S小型kernel修正降為次要項；不能把數個尚未證實的增益直接相加。

## Checklist逐題

1. 目標50，既有MT1 Hermes46.9715，差1.2895ms/token（約2.4745ms/window）。
2. 10/28 MT1 rows的CPU23.903、GPU-reach11.769、jobs0.275、draft1.825ms/window；舊nsys/source只供構想，不是current-best即時profile。
3. CPU全歸零的算術Amdahl113.20tok/s（非可達）；要達50只需CPU整段縮10.35%。情境：CPU整段縮15%→51.49；GPU-reach串行段縮25%→50.62。兩者都是目標情境，不是預估收益。若新CPU kernel只影響部分CPU，受影響部分必須更大幅加速；目前缺MT1逐型別phase占比。
4. 沒有新增旋鈕試驗；由低收益pipeline轉向IQ資料流/計算演算法及GPU資料流，是結構研究。
5. 不重跑PIN/AA/PATCH4、worker/affinity、舊MTP gate、sign-LUT原候選；新layout必須證明具體少了什麼操作，否則也停。
6. 已考慮miss/placement（tail-skip約束）、重疊（收益未證）、減少浪費驗證（已有反例）、mainline（舊報告Windows/Qwen差異）與新CPU/GPU實作；沒有把換backend當fallback。
7. 先前失敗根因分開處理：CPU/GPU瓶頸轉移、整批等待換位置、解碼型別差異、MTP多算抵銷acceptance；不足以宣告所有精確軟體方法無解。

本輪無benchmark，實驗登記/遠端營運不適用，未委派agent。下一工作單位是IQ無損layout的bytes/操作可行性表，資料不足就明列缺口；不為填補時間寫整套kernel。沒有重開部署或Git憑證工作。

## Coverage

本輪讀專案checklist、相關ledger與MTP/GPU診斷報告，解析完整舊Nsight kernel summary157列，targeted核對舊CPU row kernel與S2K tail-skip程式；未全source掃描、未解析完整Nsight timeline/SQL、未取得current-best新trace、未做kernel ISA/周期量測、未做layout parity或效能驗證。外部僅查看上述兩種方法的一手摘要/專案介紹，未評測其對IQ的支援。
