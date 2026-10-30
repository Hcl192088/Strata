# 依實測修訂：優先追求大幅收益與品質不降

日期：2026-10-30，Asia/Taipei。狀態：REVISED_PLAN / NOT_EXECUTED。

依據使用者「依照目前測試的結果，你覺得計畫內容要改嗎？一樣先追有機會大幅進步也不降品質的」修訂。本文是目前有效的優先順序；取代 R4_PLUS10_PLAN 與 NEW_BIG_EXACT_DIRECTIONS 中早期的排序、待測狀態及執行順序。歷史測試與原始報告保留。

後續使用者要求重新判斷 R4 能否修到有用並發想下一輪，已補 [R4_REPAIR_AND_NEXT_EXPERIMENTS_20261030.md](R4_REPAIR_AND_NEXT_EXPERIMENTS_20261030.md)：新確認 R4 缺少原生路徑的顯式預取，並具體化 lowreg／native reduction 的修正門，以及 HC 同精度 layout 與單矩陣 Q6 實驗。R4 全面整合仍暫停；僅在新證據下考慮一次有限修正，沒有自動執行。

## 1. 決策

**要改，而且應更換主線的選擇方式。** 不再把 R4 當預設主線，也不把 P1–P4 當成依序都要寫完的實作清單。下一個工作單位先回答：在原設定與排程下，是否存在足夠大、能以相同算術和狀態更新消除的成本？找到具體位置後，只實作一個最有證據的候選。

目標仍是相同硬體、模型、有效 expert 貢獻集合、容量與 sampling 下，accepted decode 相對同期 current best 至少 +10%。目前沒有已通過證據門、可合理預估整機 +10% 的候選。這不是判定無法再進步，而是目前結果不足以指定下一個大改寫。

優先選擇能保留每個輸出的整數、浮點 reduction／rounding 和狀態更新的變更。相同權重、小數值誤差、文字看起來正常，都不能代替品質不降的驗證。

## 2. 實測後的候選處置

| 方向 | 已確認結果 | 修訂決策 |
|---|---|---|
| P1 原 layout 跨 row×token | IQ3_S、P/E、nt1/2/3：NR2 完整 expert 慢 3.7–16.9%，NR4 慢 1.8–7.6%；樣本 h/down bits 相同 | 關閉這兩個原型，不擴展格式、不進整機 A/B。其他 row kernel 並未被全部否定，但須有新機制證據才重開 |
| P2 full-H activation LUT | IQ2_XXS、P/E、nt2/3：含建表與每 1/4/8 expert 攤提後，吞吐僅 baseline 13.8–25.1%；樣本 bits 相同 | 關閉此全 H 查表設計。不繼續掃表大小、reuse 或格式來湊收益；不同 LUT 算法須另有成本證據 |
| packed R4 v2／full-blob | 各格增減混合；full-blob 事後每格式最佳模型約 +8.60%，未扣轉換且不是實際整機結果；對 native 浮點結果不同 | 暫停整合。+8.60% 不是全域上限，但也不支持既定 +10% 主線；先不投入共同 CPU/GPU/SSD 格式 |
| R4 tile／lowreg／公平 conversion | 僅有未完成實測的草案；靜態 stack 存取不等於已證熱點；lowreg 仍繼承 R4 對 native 的數值差異 | 保留檔案，不因 runner 已寫好就排入測試。只有新診斷證明足夠大且可解的成本時重開 |
| 一般 P/E 工作再分配 | 舊 worker-skew 已有動態領任務，未過事前拖尾／等待門；舊排程餘量不足以直接支持 +10% | 不包裝成新大方向。舊資料不是 current bound；重開需要當前具體拖尾證據，不再掃 workers／affinity |
| P3 GPU Q6 dense 佈局／kernel | 三題 profile 的混合投影組約 4.70–5.07 ms/window，非 Q6-only；同容量 consumer 尚未解決 | 保留研究假設，降為條件候選。先分離實際目標成本與 consumer，不能直接進全模型重寫 |
| P4 GPU 跨階段資料流 | profile 中 shared+quant 0.94–1.02、copy+combine 0.49–0.61、hc0 split 2.02–2.10 ms/window；未找出足夠大的新可刪鏈 | 保留，但只在原排程下找到具體可移除的讀寫／同步鏈後實作。不重開 LFUSE／QFUSE |

P1/P2 的負面結論只涵蓋已測原型、樣本與條件，不能擴大為整個算法家族不可能改善。

## 3. 下一輪第一優先：一次有停止門的成本診斷

這是選候選所需的工作，不是新的加速方案。先利用已有原始資料與 source；只有缺失會改變決策時，才設計一次有限的新量測。不得用同一批粗計數反覆產生新候選。

### A. CPU 原生 pipeline：先找仍可刪除的實際工作或等待

理由：舊 pipeline 計數約 14.68 ms/window，且新 profile 有較大的 waitCPU，但前者的 GU/down 子 counter 為零，後者包含 host pipeline 等待。兩者都不足以定位純解碼、點積、下投影、I/O 或排程成本，更不能直接相加。

要交付的證據：

1. 現行 native 算法的實際 format×nt×row partition×core 工作分布，而非單核完整 expert 的等權平均。
2. 對齊同 window／layer 的 ready、GU 完成、h quant、down 完成與 GPU 真正等待區間；指出哪一段延遲會延後下游完成。既有 native GU/down pipeline 已部署，不能再次把「讓 GU/down 重疊」列為新機制。
3. 選中位置的成本歸屬：必要算術／權重 traffic、已重疊工作、可移除的重複處理或同步。沒有相應計數時標未確認，不把 waitCPU 當純算術。
4. 一個具體「原流程 → 新流程」及保留算術／量化 bytes／狀態的說明。若只有一般 P/E 平衡、prefetch 距離或不同旗標，不能升為大收益實作主線。

停止門：沒有找到可定位、暴露在關鍵路徑、且規模足以接近 +10% 所需省時的成本，就關閉本輪 CPU 執行／切分探索。不得接著自動展開 tile、lowreg 或整合 R4。

### B. GPU 原排程：與 A 共用可行的量測，不再依 serialized profile 選融合點

理由：STRATA_VERIFY_PROFILE 會停用 shared side stream 與 DF_BRANCH。因此三題 34.74–54.00 ms/window 只能作 instrumented 成本資料；不能據此判定原本關鍵路徑、排程收益或 GPU 不能改善。

要交付的證據：

1. 保留原 stream／graph 排程的相鄰 kernel、buffer 與等待關係，分開實際執行、已被重疊的工作與 host/device wait。
2. P3：將目標 Q6 矩陣從混合投影組分離，記實際 shape、nt、原 kernel 成本及對下游完成時間的影響。同時核對 decode、prefill、capture、transfer、釋放的 consumer。
3. P4：列出一條新的具體 producer→consumer 鏈、可刪操作、buffer bytes、必要 rounding 邊界，以及預計能縮短的暴露時間；不能只列 kernel 名稱或 launch 數。

工具門：量測仍須符合 current-best binary identity 和 3153 slots／20479 MiB 等原容量契約。先前 Nsight 曾影響 slots，不能默許降成不同容量再作正式比較。若既有工具無法在這些條件下提供資料，記為診斷受阻，提出工具變更方案；不自動改用未授權替代方式或放寬門檻。

停止門：若沒有足夠大的暴露成本，或原 consumer 無法在單份權重表示下使用，就不做全模型新佈局／廣泛 fusion。單鏈不足不能證明整個 GPU 方向無效，但也不能為了湊 10% 隨意拼接多個百分比。

### 診斷預算與產物

- 先查現有證據。若需新量測，先固定方法、instrumentation 差異、request 數和停止條件，再登記 ledger。
- 預設只用三個既有短 request 作一次機制診斷；數量不因結論不利而增加。若確有工程錯誤，只修同一方法並保留 failed attempt，不轉成另一套測速。
- 輸出一張成本／重疊表，以及最多一個「值得實作」的主候選。若沒有候選，明確回報，不產生新的長清單。
- 這份計畫不自動啟動遠端工作。上次 API 暫停授權針對三題 profiling，不能據此推定未來任意測試都可暫停 API；執行時依當時授權與 process gate 處理。

## 4. 大收益門檻：由同期成本計算，避免沿用假精確值

設同期 control 的每 accepted token 時間為 T，+10% throughput 需要至少省 T/11。以歷史 47.316 tok/s 為例是約 1.92 ms/token；約 3.37 ms/window 只對原 trace 的 token/window 與 workload 組合成立。

對一個可優化且真正暴露的成本 C，若需省 ΔT，必要倍率為 C/(C−ΔT)，前提 C>ΔT、其他成本及 accepted tokens 相同。若 C≤ΔT，該項即使歸零也無法單獨達標。

新 profile 的混合投影組 4.70–5.07 ms/window，在硬套舊 3.37 差距時需約 3.0–3.5×；這只顯示該假設要求很高。它既不是所有 dense 的總成本，也不是 Q6-only 或原排程暴露成本，因此不能用作 P3 的正式上限或關閉整個 GPU 方向。

實作候選至少須有「足夠的可省成本」與「有根據的達成機制」兩項。只計算把某段完全刪光的理論上限，仍不足以開大型實作。幾個方法只有在時間區間與依賴可區分後才可組合估算，收益最終以聯合實測判定。

## 5. 通過診斷後才做最小原型

1. **先同 input 正確性。** 與實際 current-native 路徑比整數 lane、quant bytes、完整 h/down 或 GPU 算子輸出及狀態。包含原本難處理的格式、row 邊界與 nt，不用排除失敗樣本通過。
2. **保持品質契約。** 能保留 arithmetic order 就先保留。若 bits 不同，候選停在 QUALITY_UNCONFIRMED；只有速度機制已值得投入時，才另列 teacher-forced/logit／可判定任務與 A/A 對照的品質評估。不得用小 float 誤差自動通過。
3. **先完整局部成本。** 將量化、轉換、索引、建表、transfer、scratch、同步和 multiworker contention 算入；採實際 working set 與工作切片，不只挑最佳單格。
4. **只做短交錯篩選。** 正確性及局部 headroom 都過後，沿用主計畫的 C/B/C 短篩與固定停止條件。機制或速度不足便停止，不靠加輪救候選。
5. **最後才正式 +10% 配對測試。** 沿用主計畫固定五輪、平均與信賴區間規格；不能以一次峰值、局部 kernel 倍率或品質未確認候選宣稱成功。

不變條件：權重／量化碼、routing、tail-skip 與有效 expert 集合、context/KV、容量、temperature/top_p/top_k/min_p/seed 不變。不增加第二份 resident 權重，不用未授權 fallback，不自動部署或改 best。

## 6. 明確不排入下一輪的項目

P1 NR2/NR4、P2 full-H LUT、R4 全面格式整合、沒有新證據的 workers／affinity／spin／power／prefetch 掃描、LFUSE／QFUSE，以及已測失敗的相同 SSD arrival／quota／route-prediction 命題。未跑草案不等於值得跑；同家族必須提出新的可驗證機制才重開。

降低權重／activation 精度、略去更多 expert、改 routing 或少算 token，不屬於本次以品質不降和相同有效計算為前提的候選。

## 7. 證據與 coverage

本次修訂核對下列本機保存的已完成實驗資料；它們是遠端測試的回傳紀錄，不是目前遠端 live 狀態。此次沒有 SSH、build、benchmark、API 操作或部署。

- big-exact-20261030/RESULT.md（含 GPU 完成追加節）、gpu-analysis.json、gpu2 profile 原始列。
- R4_PLUS10_PLAN、NEW_BIG_EXACT_DIRECTIONS 的原排序、成本與品質門；CPU_R4_NEXT、CPU_R4_ORACLE。
- cpu-r4-v2／cpu-r4-cost 的 analysis、model，以及 tile／lowreg NOTES；worker-skew 報告與模型；PE guard、pipeline、I/O 相關報告的決策段落。

完整核對 P1/P2/GPU 成果與上述候選的狀態；長 JSON／歷史報告以相關統計和決策段落核對，未逐列重算全部 raw timings。未全面讀取所有 source、全部組語／trace／私人回應，也未確認當前遠端 process、GitHub head 或新 current-best。下一次執行仍須依專案 protocol fresh 驗證。

主要證據：

- [本輪實測報告](big-exact-20261030/RESULT.md)
- [GPU 成本資料](big-exact-20261030/gpu-analysis.json)
- [R4 條件模型](cpu-r4-cost-20261030/model.json)
- [舊 worker-skew 反證](WORKER-SKEW-20261028.md)
- [tile 草案限制](cpu-r4-tile-20261030/NOTES.md)
- [lowreg 草案限制](cpu-r4-lowreg-20261030/NOTES.md)

原 GitHub publication 限制仍保留 REPORT_LOCAL。D:\strata 為非 Git 協調工作區；本次只改計畫，不建立 repository／clone，不將文件更新稱為遠端實作完成。
