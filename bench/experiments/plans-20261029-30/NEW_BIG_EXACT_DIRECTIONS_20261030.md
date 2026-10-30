# 尚未測過、以品質不降為前提的大收益方向

日期：2026-10-30。狀態：HISTORICAL_PROPOSALS / SUPERSEDED_PRIORITY。P1/P2 原型已測且較慢；P3/P4 成本診斷完成，新 kernel 未測。**目前有效的處置與下一步見 [PLUS10_REVISED_PLAN_20261030.md](PLUS10_REVISED_PLAN_20261030.md)。** 以下保留最初命題與契約，不再代表所有方向尚未測過或依序等待實作；本文件不啟動實驗。

## 判定標準

目標是相同硬體、模型、容量、有效 expert 貢獻集合與 sampling 下，accepted decode 相對同期 current best 至少 +10%。歷史 47.316→52.048 tok/s 只作直觀標尺；約需省 1.92 ms/token，10/29 trace 的相應量級約 3.37 ms/window。正式判定採同期對照，不引用歷史絕對速度當 current rate。

以下只納入尚未測過的結構命題。已測旗標、同一參數重掃，以及會修改權重／跳過更多 expert／改路由的方案，不當作新的大收益方向。「不影響品質」是必須通過的契約；沒有一項未測方案可預先保證品質非劣。

共同限制：原 quant codes/scales/signs、routing、tail-skip、context/KV、temperature/top_p/top_k/min_p/seed 不變；不增加第二份 resident 權重。新增 LUT／scratch／metadata 也要列入同容量比較。禁止失敗後自動切舊版或其他未授權 fallback。

## P1：原 native layout 的跨 row×token CPU microkernel

**新命題。** 現行同 row 跨 token 共用已存在；R4 則先把四個 row 交錯存放。這裡保留現有原格式，從多個原 row 同時取量化區塊，在暫存器內安排 decode、activation load、整數點積與流水線，並共同處理多 token。CPU 介面與 GPU／SSD 格式不變，不引入 miss repack 或 GPU inverse。

**為何值得查。** R4 小篩已證明跨 row 方案在部分情境有足夠大的局部增益，但退步和新資料格式成本阻止整合。原 layout 能直接避開這項整合成本；已產生的組語也顯示多 token 的向量 stack 存取，存在具體的編排問題可處理。這不證明 strided loads 比 packed layout 快。

**品質契約。** 每 row 使用原碼、原 activation bytes、相同整數 lane 結果，保留逐 256-block 的浮點 FMA 與最後 reduction 次序。只改工作交錯，不能跨 row 混加輸出，不能依核心換成不同數學。先與現行 native path 比對完整 GU／down bits；若不能保留，標 QUALITY_UNCONFIRMED。

**最小證據。** 先對最大 CPU 成本的實際格式與 nt2/3 做一個原 layout 四 row 原型，檢查 compiled 指令、decode/load 次數、stack traffic 及原 pool 的 row 邊界。機制成立才覆蓋五格式、P/E、nt1/2/3、完整 expert 與實際工作權重。

**+10% 門。** 需要讓真正暴露在 critical path 的完整 CPU compute 約達 1.4× 的量級，或直接證明含排程／I/O 後可省至少 3.37 ms/window。只讓 GU 快 40% 不等於達標。

**停止條件／成本。** 原 row 的分散 load、額外拆 bit 或 stack traffic 抵銷收益就停止該原型；不能改做膨脹權重來掩飾。工程成本中等，優先於同時重寫 CPU／GPU 格式；目前未有此原 layout 原型的效能結果。

## P2：activation-dependent codebook dot LUT，跨 expert 攤提

**新命題。** 現有 weight grid 查表回傳權重向量，再做點積。新算法針對當次相同的 Q8 activation 小組，預先計算「signed codebook pattern × activation」的小組整數點積，讓許多 row／expert 重用這些結果。這是新的計算分解，不是直接套用外部 backend，也不是展開整份權重。

**為何可能有大幅收益。** 相同 layer/token 的 activation 被許多 CPU expert、每個 expert 數百個 row 共用；若 signed pattern 的有效集合夠小，建表成本可能被大量重用攤薄，移除熱迴圈的部分 sign／decode／dot 工作。現行 AVX-VNNI 已很便宜，所以查表未必勝出；不能用重用次數直接推測加速倍率。

**品質契約。** LUT 只存精確整數小組和，保持原有 int32 的範圍／overflow 規則、scale 作用邊界與逐 256-block 浮點累加次序。不得降低 activation 精度、合併近似 patterns、剪枝或改 codebook。pattern ID 的解碼映射亦須全值驗證。

**先做可行性，不先寫完整引擎。** 對五種實際格式數出半 grid／四值 signed patterns 的 unique 數，算 LUT bytes、建表運算、索引生成、查表及 cache traffic；以實際每 dispatch 的 expert/row/token 重用量攤提。LUT 可以按 activation tile 建立，但必須證明不重建到抵銷收益，scratch 算入容量。這些 pattern 數目前未完整核對，不填假數字。

**最小測試與收益門。** 先做單一合適格式的建表＋完整多 expert 計時，包含所有建表成本，對現行 VNNI 比較。只有模型能支持 3.37 ms/window 的整體可省量，或與另一個已量測且不重疊的改善合起來達標，才擴展格式。

**停止條件／成本。** pattern 太多、LUT 不能留在合理 cache、dispatch 重用不足，或建表＋lookup 不快於現行核心即停止；不靠省略難處理的權重／token 通過。工程成本高、收益不確定，適合先做小型成本證據。

## P3：GPU 原量化 dense 的同容量新佈局與 tile kernel

**新命題。** 針對實際 native Q6 dense 矩陣設計保留原碼與原 bytes 的 block/lane 排列，讓 GPU kernel 減少重複 unpack／shuffle，並在適當 tile 重用資料。現有 head packed 功能不是這項方案：本模型 head 是 Q5_K；先前核對的 Q6 dense 有合適 shape，但尚未有完整 consumer 與新 kernel 實作。

**品質與容量契約。** 相同量化碼還原相同值；保留每個輸出的原 reduction／rounding 次序為優先。decode、prefill、graph capture、transfer 和釋放流程都須使用同一份可逆 representation，不能為 decode 雙存一份新權重卻聲稱同 VRAM。prefill 仍需原資料時，先解決 consumer，不能刪原副本或在失敗時默默轉回。

**為何可能大。** 這是跨大量 dense 矩陣的資料表示與運算路徑變更，與單個小融合旗標不同。但矩陣總 bytes 不等於 decode critical-path 占比，不能由約 804 MiB 的候選集合推成收益百分比。

**最小證據。** 先對 current-best 取得目標矩陣的串行時間 C，以及原/native/packed consumers 表。挑一個實際矩陣做可逆排列、bitwise 或原 rounding 契約檢查，再測相同 T 的 kernel，將額外搬移／scratch／prefill 成本算入。

**+10% 門。** 單項至少需要 C 大於 3.37 ms/window；達標所需目標段倍率為 C/(C−3.37)。C 不夠或所需倍率缺乏機制支持，就不投入全模型重寫。先前 GPU dense 分段是較舊證據，不能拿來填當前 C。

**停止條件／成本。** 無法單副本供全部 consumer 使用、reduction 改變而品質關卡未過，或可省串行時間太小即停止。工程成本高，須先 consumer／成本證據；尚未測新佈局或新 kernel。

## P4：GPU 關鍵路徑的新跨階段資料流融合

**新命題。** 從 current timeline 與 source 找出同 activation 在相鄰 producer/consumer 間的重複讀寫、中間 buffer 或可移除的同步，考慮把資料留在同一個執行 tile／階段。實作點目前尚未選定；不能把 LFUSE、QFUSE、batching 或已測旗標重新命名成新方向。

**為何值得保留。** 既有 GPU kernel 名稱總表顯示成本分散，單一最大 kernel 小不代表跨階段沒有空間。GPU-reach 段的量級足以容納 +10% 所需改善，但它含等待，不能全部當成可消除的 kernel 時間。

**品質契約。** 保留原 producer 的 FP32 rounding、量化 bytes、每列 reduction 次序、因果 attention、cache/state commit 與 routing。消除 buffer 時，也必須保留原本由 store/load 形成的 rounding；禁止略算 token、簡化 normalization 或改 attention。

**最小證據。** 先取得同 binary/source 的 kernel adjacency、各邊搬移 bytes／耗時、host/device wait 歸屬，列一條「原鏈→新鏈」及可刪操作。核對現有融合功能已涵蓋哪些邊。只有未涵蓋的鏈與足夠成本同時存在，才設計一個小型 fused kernel。

**+10% 門與停止。** 串行段 C 需足夠大；單項至少省 3.37 ms/window。若只有 launch 名稱變少、沒有暴露在 critical path 的時間下降，或所有可移除成本上限太小，就關閉該點，不做廣泛 fusion。尚無此新鏈的收益預估；工程成本先低（診斷），通過後高（實作）。

## R4 的配套：CPU／GPU／SSD 共同消費同一個可逆格式

若 CPU R4 核心本身已有足夠收益，才研究讓 SSD pack、RAM resident、GPU admission、prefill／decode 都直接消費同 bytes 的 R4 表示。這可能把轉換留在一次性的 pack 產生階段，去掉每 miss repack 與每 admission inverse，維持 slots／20GiB 與單副本。

已知：R4 block size 與原四 rows 相同，且樣本解碼／還原已通過。未知：實際 CUDA/prefill 全 consumer 是否能接受同格式、所有 transfer/lifetime 與啟動成本。需要逐一核對，不可只改最終 kernel。

這是使 R4 收益能落地的配套；current best 原本沒有 R4 轉換，不能把省掉新引入的成本另算一份加速。若 CPU R4 仍不足，單做這項不能製造 +10%。

## 驗證順序與最終判定

1. 審閱本計畫後，選一個主方向；P1 最貼近已確認缺口，P2 先做離線 pattern／成本證據，P3/P4 先查 actual critical path，不一起開多個實作。
2. 重新核對 GitHub task/current-best、source/binary/config/library/input SHA、host/process/容量與 sampling。缺一停在該層，不改用別的 binary 繼續比較。
3. 先證實機制與成本上限，再做最小原型。先 bitwise／整數及狀態契約，後短交錯 A/B；沒有正確性就沒有速度候選。
4. 取得實際 format×nt×core 與 critical-path 工作權重，將 transfer、LUT、轉換、scratch、cache contention 和 exposed I/O 計入。不以最佳單格、48層均權或無關 workload 外推整機。
5. 速度與品質都通過才做同期整機確認；固定樣本／停止條件，不無限加輪。報平均配對收益與不確定性；目標至少 +10%，不能只有單次峰值。數個方法只有在聯合實測後才能宣稱組合收益。
6. 若算術次序無法保持，先與 current/current 的 A/A 差異分開，補 teacher-forced/logit 或可判定任務的品質非劣證據。缺合適工具／資料即 QUALITY_UNCONFIRMED，停止晉升，不用文字看起來正常替代。

## 已做、未做與盲點

- 已有原始結果：R4 v1／VNNI／gather／token 拆組／full-blob 小篩與既有 phase trace。它們支持研究問題，尚未證明整機 +10% 或品質非劣。
- 新增的 P1–P4 與共同格式方案均未完成效能／品質驗證；P1 的原 layout 版本尚未測，不能以已寫好的 packed R4 lowreg 代替。
- 接下來只待審閱，沒有新 benchmark、部署或自動執行佇列。已啟動的舊小旗標短篩與本計畫分開記錄，不把它的結果當成上述新方向的證據。
- 本文件使用已讀 source 片段、型別／consumer 盤點、R4 原始結果與成本模型，並非全 repository／所有 private requests 的完整審計。P2 pattern 集合、P3 current cost/consumers、P4 current adjacency 是明確盲點。
- 進一步來源核對遭 shell 自動審核因用量額度拒絕，未執行；未改用其他管道繞過。因此不宣稱新方向已全數去重、證實可行或有可靠收益估值。
