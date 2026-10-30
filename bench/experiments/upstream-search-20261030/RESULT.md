# Strata 上游與 fork 提速搜尋（2026-10-30；研究紀錄）

## 判讀與限制

本次僅讀指定本機紀錄及公開網頁，未 SSH、build、benchmark、修改 GitHub 或讀取我方 fork 的 coordination。基準 38.6 ms/window、GPU-reach wait 11.7、CPU 21.7、SSD join 4.4、LRU copy 0.9、draft 1.8 ms 均由 brief 提供，並非本次 live 核實；各段可能重疊，不能加總。以下消除整段的樂觀算術邊界：GPU wait 11.7 → 38.6/26.9−1＝43.5%；CPU 21.7 → 38.6/16.9−1＝128.4%；SSD join 4.4 → 38.6/34.2−1＝12.9%；draft 1.8 → 38.6/36.8−1＝4.9%。GPU-reach 是等待，不代表整段可由 GPU kernel 消除；SSD join 屬 CPU 路徑內，實際可省時間往往遠低於上限。若改變每 window 有效 token 數，這些固定 token/window 換算不成立。

品質規則以 brief 的 current best 為比較對象：`ROUTE_TAIL_SKIP=7` 保持原樣，不增加 skip；相同 weights、quant values、expert selection、sampling，speculative verification 精確，僅允許 float accumulation order 差異。**允許候選**指機制表面符合，仍須驗證我方實際實作；**邊界**代表來源或適用路徑不足以確定。成本 S/M/L 為工程量粗估，不是測試授權。

## A. RTX 4070／Ada／12 GB 相關

1. [Issue #3724](https://github.com/Niko1221/Strata/issues/3724)（closed）：將 [llama.cpp #30553](https://github.com/ggml-org/llama.cpp/pull/30553) 的 MMQ Stream-K block 數限制於實際工作量。Windows 11、i5-14490F、63.8 GiB、4070 SUPER 第一層加 2080 Ti、IQ3_S、262K、int8 KV、`--spec 4 --mtp rt`、engine 0.1.47；單次兩份報告 short chat decode +12.66%，4K/16K prefill +2.88%/+2.62%。作者明說 decode 因果需再研究，且不是單卡；**不能外推到我們**。baseline 是否有相同改動：本機指定紀錄未證明，未知。品質：**邊界**，需確認是否只是排程及 accumulation order、目前 IQ3_XXS 的 decode 是否走該 MMQ，而非 prefill 或不同格式。若命中 GPU 段，寬鬆上限 11.7 ms/window，38.6/26.9−1＝43.5%，但真正受影響 kernel 時間未知；成本 M。這是值得先做 source 比對的線索，不是已確立的本機加速。

2. [Issue #1922](https://github.com/Niko1221/Strata/issues/1922)（closed）報告 4070、i5-13500、Windows、UD-IQ4_XS、experts 全部 GPU/RAM resident，0.1.41 關閉 `STRATA_LOOKAHEAD` 從 32.80 到 39.06 tok/s（+19.1%）；0.1.43 的日本語/英文/code 分別 +22.3/+15.9/+11.6%，輸出不全一致；另一 20 核 3060 機器五組配對沒有明顯收益。與我們有 SSD miss 的狀況不同，不能照搬。baseline 實際 flag／先前是否測過：本次定向搜尋未能確認。品質 **邊界**：停 prediction 應保留最終選路，但必須檢查 current best 具體程式及驗證語義。可能減 CPU 競爭，極寬上限 21.7 ms，即 38.6/16.9−1＝128.4%；僅 prediction overhead 才可能回收，未知。成本 S。非已證新候選。

3. [Issue #3448](https://github.com/Niko1221/Strata/issues/3448)：4070 12 GB、Ryzen 5700X、31 GiB、Coder IQ1_M、0.1.45.3，新舊 expert profile 43.6 vs 44.8 tok/s，落在約 ±5% 波動；adaptive tier 在最初 requests 交換 2,166 experts。這是 profile 更新後未證增益的報告，且不是我們模型。baseline 與此 profile 的關係未知；精確 cache placement 原則上允許，但實際路由及驗證仍須確認。目標 SSD join，最大 4.4 ms＝12.9%；實際未知，成本 M；不列推薦。

4. [Issue #4261](https://github.com/Niko1221/Strata/issues/4261)（closed）：5070 12 GB + 5060 Ti、Windows、NVFP4、262K、int8 KV、0.1.51，`STRATA_STAGE_TRIM=1` 加 layer split 將 46.2→53.9 tok/s；再加 Cyrillic draft vocabulary 至 67.0；多個設定相繼變動，非 4070 單卡效果。trim 省第二卡 stage weights、slot 1128→2115。**我方是否適用未知**，屬 dual-GPU split，draft vocabulary 是否維持相同 sampling/精確 verifier 亦未知；品質邊界。若能增加 resident experts，影響 SSD join 與 CPU，僅用 join 可見的 4.4 ms 作窄上界：12.9%，不能假定增加 slot 能完全消除它；成本 M。不是當前單卡可直接採用的候選。

5. [0.2.7/0.2.8 release](https://github.com/Niko1221/Strata/releases)：12 GB RTX 3060 的 story +15%、code +37% 來自 `ROUTE_PRIOR=1.5`；0.2.8 因長 session 重複文字回報將預設關閉。它改 expert selection，見 E，明確排除。

### 社群原始配置與可比性

[社群索引](https://github.com/Niko1221/Strata/blob/main/bench/results/COMMUNITY.md) 的行並非相同 benchmark：

- [我方 4070 報告](https://github.com/Niko1221/Strata/tree/main/bench/results/2026-10-08-community-rtx4070-iq2-xs)：i5-12600KF、32 GB DDR4、Windows、IQ2_XS、100K、q4_0 KV、adaptive E4/S24，自行修改 build；28,912 prompt tokens，accepted decode 五次中位數 48.23 tok/s。不同量化與目前 baseline，不可視為本次驗證。
- [3060 報告](https://github.com/Niko1221/Strata/tree/main/bench/results/2026-10-09-community-rtx-3060-0141)：3060 12 GB、i7-12700、64 GB、Windows、0.1.41，IQ3_XXS、128–260K，4K/32K/128K decode 26.2/27.1/27.0 tok/s。
- [4060 Ti 報告](https://github.com/Niko1221/Strata/tree/main/bench/results/2026-10-05-community-e5-2673v3-rtx-4060ti)：16 GB、Xeon E5-2673 v3、DDR3、PCIe 3.0 x8、0.1.39；Q2_0 48.1–55.7，IQ3_S 30.5–35.0 tok/s。
- [4070 Ti SUPER 報告](https://github.com/Niko1221/Strata/tree/main/bench/results/2026-10-05-community-rtx-4070-ti-super)：16 GB、9800X3D、0.1.39；IQ3_XXS 在 32K/64K/128K/256K 為 76/71/70/56 tok/s。
- [V100 + 4070 split](https://github.com/Niko1221/Strata/tree/main/bench/results/2026-10-04-community-v100-rtx4070-split)：V100 32 GB + 4070 12 GB、16 GB RAM、IQ2_XS、0.1.39；decode 79.1/83.8/77.1 tok/s，不能代表單卡。

## B. 其他上游／PR 項目

- [0.2.8 release](https://github.com/Niko1221/Strata/releases/tag/v0.2.8)：Qwen IQ3_S 在 RTX A6000 上 0.2.7.1→0.2.8，五組配對 story 105.9→111.4（+5.2%）、code 139.8→145.2（+3.9%）；R9700 story 73.7→79.7。這是版本整體數據，發布頁未在該數據處指出造成收益的具體 Qwen 改動。f520bc5 是否已含等效改動未知；品質 **邊界**，不得將版本打包視為符合品質或歸因某個 kernel。目標段未知，沒有可信 ms/window 上限；定位版本 diff 成本 M。Arc B-series 雙卡 pipeline 與四張 R9700 並行設定不適用單 4070。
- [0.2.5 release](https://github.com/Niko1221/Strata/releases/tag/v0.2.5) 的 SSD miss 與已 resident expert 計算重疊，在 3060 +11–15%、5070 +13.5%，是 DeepSeek engine。Qwen `STRATA_COLD_OVERLAP` 類似機制與我方 MISS_OVERLAP 的詳細比較見 [本機比較](../UPSTREAM_025_027_COMPARE_20261028.md)。已知同家族且曾測；[arrival 診斷](../io-arrival-20261029/RESULT.md) 已檢查逐波 headroom，不可將舊 DeepSeek 數字當 Qwen 新收益。精確分波理論上允許，仍需驗證累加次序；SSD join 算術上限 4.4 ms＝12.9%，實際可重疊部分更小，成本 L。
- [Issue #3201](https://github.com/Niko1221/Strata/issues/3201)：雙 socket Xeon NUMA expert pool +10–14%；單 socket 12600KF 不具該拓撲。baseline 未確認、相同計算屬允許，但移植效益未知；CPU 整段寬鬆上限 21.7 ms＝128.4%，並非單 socket 預期，成本 L，不推薦。
- [Issue #2936](https://github.com/Niko1221/Strata/issues/2936)：3090、AVX2、0.1.43→0.1.44 的 `STRATA_ADAPT_OVERLAP` 預設變動及回歸，不能直接當 4070 提速；baseline 與相關本機開關狀態需看 [switch inventory](../switch-inventory-20261029.md)，品質與可用路徑待核。若影響 CPU/GPU 排程，上限不明，成本 S；不列新候選。

## C. Fork

- [AdrianBM96/Strata3060](https://github.com/AdrianBM96/Strata3060) 確認為 upstream fork；公開 repo 頁能看到 fork 身分，但此次 commit list 抓取失敗，沒有可核實的 fork-only patch 或 3060 新數字。baseline 重疊、品質、目標段及成本均 **未知**；不能憑名稱推測優化。
- [eddoursul/Lamina](https://github.com/eddoursul/Lamina) 明述從 Strata fork，針對 3090+5070 Ti；[多 GPU 結果與討論](https://www.reddit.com/r/LocalLLM/comments/1wwp4cw/200_toks_peaks_with_qwen38flashnext_on_a_5080/) 描述額外 GPU expert tier。該比較的原始 fork 比較頁本次未成功取得，具體 patch、上游合入狀態和品質未知；需要第二張 GPU，對固定單卡不適用。無可信單卡 ms 上限；成本 L。
- [Basalt](https://github.com/jesdga95/basalt) 的[作者說明](https://www.reddit.com/r/LocalLLaMA/comments/1x223ai/basalt_flashnext_at_665_toks_structured_354_prose/) 稱重寫 decode／prefill 且移除非 Blackwell 支援，宣稱其雙卡工作負載最高 2.6×；RTX 4070 是 Ada，不能直接採用。baseline 無法確認相應 kernel，品質未知；無可信上限，成本 L。
- [4 GPU fork](https://github.com/johnmosesventura06/strata-4gpu) 擴充多 GPU expert tier；固定單卡不適用。baseline 差異和品質未審計、成本 L，無可估計的本機 ms 上限。

## D. 已在 baseline 或已測

- 依使用者所給 baseline 與 [實驗 ledger](../EXPERIMENT_LEDGER.md)：native CPU GU/down pipeline、MISS_OVERLAP、S2K、MT1 已有；0.1.45 + RAM_ADAPT 已評估為效能中性，見 [rebase 報告](../LUNA-20261012-027.mainline-rebase-eval-20261018.md)。本次未讀遠端 source 或 live binary，不能獨立驗證 f520bc5。
- [GPU6 A/B 紀錄](../gpu6-ab-20261030/RESULT.md)：六旗標組合 +0.61%，信賴區間跨零，GPU-reach 差異約零；其他 GPU flags 與既有驗證見 [switch inventory](../switch-inventory-20261029.md)。不再以單純重新開 flag 當新方案。
- [既有今日研究](../speed-research-20261030/RESULT.md) 已涵蓋 MTP tree、DirectStorage、IOCP、Q2_0 AVX-VNNI 等，不能在此當成新 upstream/fork 發現。

## E. 依品質規則排除

- [ROUTE_PRIOR](https://github.com/Niko1221/Strata/releases/tag/v0.2.7) 會依 resident 狀態改路由；無論上游品質測試結論均不符合「同 expert selection」。上游 [0.2.8](https://github.com/Niko1221/Strata/releases/tag/v0.2.8) 亦已將其預設關閉。
- 降低權重/KV 精度、更換量化、增加 tail skip、改 sampling 或 approximate verifier 均不符合 brief；不同模型格式的跑分僅作背景，不能作候選。

## Coverage 與盲點

要求範圍是 0.1.42 後每一項 upstream release/commit、所有狀態 PR/issue/discussion 及 fork，並盤點相關社群結果。**本次未完成全量盤點，不能宣稱「每一項」均已檢查。** 已讀指定比較檔、rebase、switch inventory、今日研究；ledger 以 `rg` 主題搜尋而非逐行完整閱讀。公開部分讀取 release 頁最新清單與若干版本節錄、上述 issues、community index 與數個 fork 主頁，另外使用關鍵字搜尋，並非逐一讀取所有 release、commit、PR、issue/discussion 或所有 bench README。社群大索引的長行由網頁提供，取相關項目而非逐資料夾完整核對；原始 dumps 在上游索引中註明已裁剪。GitHub network/members、Adrian commit list、Lamina comparison 與版本 compare 頁本次抓取失敗；未取得 fork 全名單、所有 branch 的差異及未被搜尋索引收錄的項目，也未完成 AVX2/VNNI kernels、hybrid CPU、MTP 全部 PR 的逐個審核。公開頁可能變動；我方 fork 僅使用已公開上游 community 報告，未碰 coordination。

## 排序結論

**目前沒有找到三項能同時確認真正新、符合品質且對此機器有可證據支持的候選；甚至沒有一項完成這三項確認。** 最有價值的下一個唯讀查核是 #3724 的 MMQ Stream-K patch 是否命中 f520bc5 的實際 IQ3_XXS decode，及其精度與既有實作；第二是定位 0.2.8 相對 0.2.7.1 的 Qwen decode 變更。兩者目前都只是待判定線索，不是已證可行的前三名。
