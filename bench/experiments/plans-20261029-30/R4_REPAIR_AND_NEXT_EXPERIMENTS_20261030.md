# R4 為何還沒落地，以及下一階段實驗

2026-10-30，Asia/Taipei。狀態：SOURCE_REVIEWED / EXPERIMENT_PROPOSAL_ONLY。依使用者詢問重新檢查，沒有執行本文件的新測試。

## 判斷

R4 不是完全沒用。補 VNNI／gather 確實消除了部分移植劣勢，但「原型 kernel 更快」距離「相同品質、容量下的整機 +10%」還差完整 expert 成本、實際工作切片、格式消費者和浮點契約。值得一次有限且可否決的修正，不值得直接恢復全面整合或宣稱 30 格都能加速。

## 1. 後來的修補實際做了什麼

使用者引用的是最初 R4 v1 的 13 正／17 負。後續 v2 已補 AVX-VNNI、gather，並測 token 拆組；full-blob 又將候選 GU 與 unchanged down 放在同一份連續 blob。

以 IQ3_S／P 核的同輪 A/B 為例：

| 測試 | nt1 | nt2 | nt3 |
|---|---:|---:|---:|
| v2 gather，GU 吞吐變化 | +24.0% | +12.0% | +27.8% |
| v2 gather，完整 expert | +0.6% | −0.4% | +5.5% |
| full-blob gather，完整 expert | +51.1% | −6.6% | +12.0% |

以上都是微基準，非整機。不同 campaign 的 baseline 時間也有明顯差異，不能將表格兩輪的差值當作「連續 blob 的因果收益」。它們足以指出資料存取與測試工作集值得隔離，還不足以歸因。

v2 選中 30 格有 14 正／16 負；full-blob 選中 30 格有 12 正／18 負。full-blob 事後每格式最佳的條件模型約 +8.60%，未扣轉換，且套用了無法直接實現的最佳值；既不是收益預估，也不是所有 R4 重寫的上限。

## 2. 現在可指認的缺口

### A. 仍有原生核心具備、R4 未帶入的顯式預取

當輪遠端 source 的 iq_avx2_rows.inl 在每個 block 呼叫 rows_ahead(blk,pf)，預設距離由 iq_avx2.cpp 定義。與遠端 hash 相同的 v2/full-blob r4.cpp 未找到 prefetch／rows_ahead 顯式操作；lowreg 草案也沒有。

這是 source 缺口，不是「已證預取是主要根因」。硬體預取可能已有效，多核心時額外預取也可能搶頻寬。只值得固定一種、按實際 packed byte stream 設計的候選，不再掃距離。這與未跑的 native-prefetch4096 草案不同，不能混用其結論。

### B. 四列 × 多 token 的暫存器壓力

gathered IQ3_S 迴圈同時保留 acc[NT]、isum[NT]、qx[4]、四個 sign 向量和其他暫存值。已有 compiled 組語紀錄 29 個靜態 YMM stack access，但尚未量出熱迴圈的動態 spill 成本。

lowreg 草案將四組 decode/sign 逐組消費，可縮短 live range；代價是 activation load 可能增為四次。已測的 token 拆成 2+1 沒有救回效能，不能重跑該拆組冒充低暫存器方案。必須以完整 expert 時間和實際組語判斷，不能只看寄存器數。

### C. reduction 契約確實不同

當輪 native row_dot 每個輸出保留 8 個 float lane，跨 256-block FMA，最後 hsum8。R4 將四列排進向量，最後用低／高 128-bit 相加輸出四列；整數部分的分組與轉 float 邊界也不同。權重可逆不會自動恢復 native 的 rounding。

lowreg 若只保持舊 R4 bits，仍不等於保持 native bits。要符合本次品質目標，優先做可追蹤的 native-lane／FMA 順序版本；這可能增加暫存器和重排成本，是實作取捨，不能保證免費。若無法逐位相同，停在 QUALITY_UNCONFIRMED，不以小誤差通過；另需正式品質非劣證據才能考慮採用。

### D. kernel 以外的落地成本尚未解決

實際 pool 依 nb 與 worker 數切 row，完整 640-row 單核時間不能直接外推。R4 range 邊界需四列對齊；轉換必須包含相同 working set。舊 fast-pack timing 的單一 scratch 與原 36-expert stream 不同，倍率作廢。GPU／SSD 仍消費原格式，不能新增第二份 resident 權重或在未支援時自動切回。

## 3. R4 最後一輪有限修正：分辨是否值得繼續

這是明確的新缺口驗證，並非重新掃完 30 格。

1. **品質可行性先行。** 只挑 IQ3_S 的代表資料，逐 256-block 對齊 native 整數 lane、FMA 與最後 reduction。確認 packed layout 是否能以可接受的存取／暫存成本供原算術使用。不能解決契約，就先保留品質未確認，不擴展格式。
2. **機制小篩。** explicit arms：current native、current R4 gather、只加 packed-stream 預取、只做 lowreg。IQ3_S、P/E、nt2/3，既有 18-expert／6-layer 小樣本，五次輪序輪替；相同完整 blob／working set／actual down。先對各臂宣稱的算術基準全 bits；舊 R4 等價只算機制證據，不算 native 品質過關。兩項各自有效才另登記聯合臂，不先 bundle。
3. **不要只測 GU。** 同時記完整 GU→h quant→down 與組語熱迴圈的 spill/load；原型沒有完整收益就停。若只有幾個百分點，也沒有工作權重支持 +10%，停止修補，不為補齊 30 格而擴展。
4. **正面才查 production 切片。** 以實際 nb/nt 分布、原 row 邊界與四列對齊候選做同 input 完整 pool 比較。把轉換、copy、cache contention 計入，並檢查每個輸出的原 reduction。單核快但 pool 不快，就關閉落地路徑。

只有候選具備 native 品質契約或足夠的品質非劣證據，且加權完整成本支持目標，才進整機 C/B/C。上述門沒過，不進整機測試、共同格式工程或部署。

## 4. R4 之外：下一階段具體實驗

### E1：HC 的同精度資料佈局／tile kernel

**研究命題：** 保留 HC 的 BF16 權重和 FP32 activation／累加，為 10240↔320 的 down/up 設計同 bytes 的存取排列，減少重複權重讀取、位址計算或 shuffle。這是目前新增的研究候選；不是 HC→Q8、Tensor Core 降 activation 精度，也不是重測 GR_DOWN_MAX4／GR_V3。

**為何值得先評估：** 既有權重盤點的 HC down/up 約 1200 MiB，覆蓋多層。當輪 profile 的 hc0 split 約 2.02–2.10 ms/window，但包含 norm；hc1 又與 router 混在一起，所以不能把 hc0 乘二當可省時間。單做 hc0 不足以支撐舊 3.37ms/window 差距。

**首個工作單位：** 先分離原 HC0/HC1 down/up 成本，核對原排程暴露時間；比較既有 launch_multi variants，確認新排列確有未被處理的重複存取，再取一對真實矩陣做原/新 kernel 同 input 測試。不先改 48 層 loader。

**品質／容量：** 保留原 FP32 FMA、warp reduction、norm epsilon 與 store/load rounding；same-input intermediate 和輸出先 bitwise。新表示須由所有 consumer 共用，scratch 計入，不雙存整份權重。若只能靠改 reduction 或 BF16 activation 才變快，不能直接採用。

**收益門：** 必須量到兩段中足夠大的可改善成本，以及合理的可達倍率；1200 MiB 本身不是收益證據。沒有可定位的存取浪費，或 headroom 不夠，就停止。完整 kernel 尚未實作，與所有既有 variants 的去重尚未完成。

### E2：Q6 dense 的單矩陣同容量 kernel，而非全模型重排

這是原 P3 的具體化。先從實際 Q6 矩陣選出最大的可改善成本，測原格式與同 bytes 新 layout 的 nt1/2/3；涵蓋原 reduction。71 個 Q6、52 個 shape eligible 的盤點只用來選樣，不能當加速證據。

當輪混合投影組 4.70–5.07ms/window 不等於 Q6-only 或所有 dense。先測出 Q6 對原排程完成時間的貢獻，再決定是否值得單矩陣原型；達標才解 prefill／decode／ownership／free 的完整 consumer 契約。現成 Q6 head packed 在本模型 Q5_K head 不適用，不重開該旗標。

### E3：R4 與 GPU 改善的聯合收益，只在兩者獨立成立後

若 R4 或原 native CPU 修正與 E1/E2 各自有品質及完整成本證據，且時間區間不重疊，可考慮組合達到 +10%。目前沒有這組正面結果，不能將局部百分比直接相加。

先算同一 workload 下每 accepted token 的可省時間；組合可能改變重疊和頻寬競爭，所以最終需 explicit combined arm。若兩項只各快約 1%，不因可組合就拉長實驗。

## 5. 順序與停止條件

推薦順序：R4 品質可行性／有限缺口修正 → HC 成本與既有 variant 去重 → HC 或 Q6 中實際暴露成本更大者的單矩陣原型 → 正面才做聯合整機比較。可以先用唯讀證據淘汰 E1/E2，不必為了完成清單都寫 kernel。

仍以同期 +10% 為目標。省時門是同期 control 的 T/11（每 accepted token）；舊約 1.92ms/token、3.37ms/window 僅作尺度。保留 sampling、routing、tail-skip、有貢獻的 experts、context/KV、RAM/VRAM 容量。identity/process gate 與 API 授權照專案 protocol；不自動停止 API、不 fallback、不部署。

不重開 P1 NR2/NR4、P2 full-H LUT、一般 workers／affinity／spin 掃描、已測 token 拆組、LFUSE／QFUSE，或以降精度／略算取得的加速。

## 6. 本輪核對與 coverage

唯讀 SSH 驗證 DESKTOP-LKMLUPC、canonical junction、遠端 AGENTS、generic source f520bc5e9d31c93caeb296b059e3a3eaa16e493f clean。BEST 的 A1E61238…D9491AD8 與磁碟 binary 相同；程序盤點只有已分類的 API／watch，API engine PID32568。此次沒有送生成 request、build、benchmark、修改遠端 source／config／sampling、停止程序或部署；未重新量當前 tok/s。

v2 r4.cpp SHA A8DC2813B42BF69BBB7C8FD7FF6B568E9DDD131AA79FC2E184FAD7FB4B6CF265；full-blob SHA 6690FCEE7240879C65C6ED5CEF0FC2D38EDFB6D5EBAAF86A776F7C0EB04AE908，本機與遠端相同。核對 v2 DONE、相關 raw SUM、兩份 analysis/model、lowreg/tile NOTES；直接讀取遠端 native row_dot/hsum8、pool native pipeline、native_dense consumer、fused_gr_read_multi 的實際路徑。

完整讀取所用 IQ3_S 原型迴圈與 native row_dot；其他格式主要核對統計，未逐條分析全部組語、全部 raw passes 或每個 HC kernel。HC 類新佈局尚未與全部 variants 去重，沒有 kernel 成本或品質實測；這些都屬研究假設。沒有整個 R4/GPU 家族的不可行結論。

證據：[v2 raw IQ3_S P](cpu-r4-v2-20261030/raw/lp2-t21.log)、[full-blob raw](cpu-r4-cost-20261030/raw/lp2-t21.log)、[條件模型](cpu-r4-cost-20261030/model.json)、[lowreg 草案](cpu-r4-lowreg-20261030/NOTES.md)、[GPU profile](big-exact-20261030/raw/gpu2-profile-lines.json)、[VRAM 盤點](vram-inventory-20261029/RESULT.md)。

本機非 Git 協調工作區；新內容為計畫，保持 REPORT_LOCAL，既有 GitHub publication 限制不變。
