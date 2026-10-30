# AVX2／AVX-VNNI i-quant CPU kernel 公開研究

2026-10-30；RESEARCH ONLY。結論：**沒有找到三個已證實全新、符合容量與品質條件、且對本工作負載有加速證據的候選；甚至沒有一個達到這個標準。** 下列兩個待核線索值得保留，但不是已證可行的加速方案。

## 基準與估算

下述 38.6 ms/window、gate/up 8.8 ms、五類層數與 current kernel 由使用者 brief 提供，本次未接觸遠端或驗證 live 狀態。假設 gate/up 省下的時間全部暴露於 window 關鍵路徑，kernel 加速 r、受影響的 gate/up 時間占比 f 時：saved = 8.8 × f × (1 − 1/r) ms；整體 = 38.6/(38.6 − saved) − 1。這是條件式上限，並非實測預測；重疊與排程可使實際收益更小。若五類每層成本相等，層數權重 IQ3_S 13/48、IQ3_XXS 6/48、IQ2_XS 10/48、IQ2_S 10/48、IQ2_XXS 9/48；實際各格式成本、P/E 分配與 nt 分布不同，不應把層數視為實測時間占比。

全 gate/up 假設 1.2×：saved = 8.8×(1−1/1.2)=1.467 ms，整體 38.6/37.133−1=3.95%；1.3×：saved=2.031 ms，整體 38.6/36.569−1=5.55%。這和 brief 所列 4.7%／6.5% 不同，因為本報告依指定的 38.6 ms 與 8.8 ms 直接計算。僅 IQ3_S 假設 1.2× 且等層成本：saved=8.8×13/48×(1−1/1.2)=0.397 ms，整體 38.6/38.203−1=1.04%；四種非 IQ3_S 共 35/48，假設均 1.2×則 saved=1.069 ms、整體 2.85%。無已證 r 的項目不能把上述假設當作預估收益。

## 公開來源及與既有實驗的關係

1. **ik_llama.cpp [PR #1474](https://github.com/ikawrakow/ik_llama.cpp/pull/1474)：IQ3_XXS／IQ3_S R4 AVX-VNNI 256-bit。** 對象為 R4 matmul，不是證實新發現的 native-layout single-row kernel；AVX-VNNI 分支不需 AVX-512。PR 不是本次可證明的、在所給 d4c1f755 之後才出現的新增變更：未取得該基準與 PR head 的完整 ancestry/diff。沒有可適用於 12600KF、nt=1 的可信加速數字。品質分類：R4 僅在 lossless roundtrip、單份 resident blob 與累加差異符合規則時有條件允許；本機已做的 R4 v2 用同 pinned source、VNNI 與 gather，詳見 [kernel notes](../cpu-r4-v2-20261030/KERNEL_NOTES.md) 及 [ledger R4](../EXPERIMENT_LEDGER.md#L479)。因此不重提同方案；不能由該 PR 推出新增的 ms 或整體加速。相鄰 [#1446](https://github.com/ikawrakow/ik_llama.cpp/pull/1446)、[#1455](https://github.com/ikawrakow/ik_llama.cpp/pull/1455)、[#1467](https://github.com/ikawrakow/ik_llama.cpp/pull/1467)、[#1482](https://github.com/ikawrakow/ik_llama.cpp/pull/1482) 分別針對 Q4_K/Q5_K、Q8_1、IQ4_NL、Q6_K，均非指定 gate/up 五類；IQ4_NL 在此為 down，不計入收益。

2. **[KTransformers #2240](https://github.com/kvcache-ai/ktransformers/pull/2240)，open：x86 llamafile IQ2_XS、IQ2_S、IQ3_XXS、IQ3_S。** 使用 Q8_K，AVX2／AVX-512 均有路徑，測 qlen 1 與 32；明言 dequantizer 和 helpers 摘自 ik_llama.cpp，增加先前缺少的支援，未給可核對的 nt=1 kernel 加速數字。IQ2_XXS 原已有，IQ4_NL 對此為 down。品質分類：有條件允許；須檢查 integer overflow、累加與單份容量。**並非獨立新演算法**，與上述 ik 家族及 [ledger](../EXPERIMENT_LEDGER.md#L195) 的 native／iq256、R4 有機制重疊；但它的非 R4 路徑是否與實際 Strata iq256 實作完全相同，未讀遠端 source，不能定論。可作唯讀 source diff 線索，收益未知；等層示例四類 1.2× 為 2.85%，無證據宣稱能達到。其 [測試敘述](https://github.com/kvcache-ai/ktransformers/pull/2240) 是正確性測試，不是本機 benchmark。

3. **[KTransformers #2242](https://github.com/kvcache-ai/ktransformers/pull/2242)，open：小視窗按 expert 合併 token。** 在 qlen 2–8 避免每 token 各跑 forward_one，並改 down job 的 merge；雙 EPYC 7452、32 threads、Q4_K 下 qlen 2 的 529→484 μs（約 1.093×），qlen 3 的 778→680 μs（約 1.144×）；不是 IQ2/IQ3 或 12600KF 數據，無 nt=1 增益。無 AVX-512 限制被聲稱。品質：作者稱 down merge bit-identical，移植仍須確認；不增加 resident weight copies。使用者指明 Strata nt≥2 已走 iq256，因此 token 共用已屬同方向；down 不計收益。若極樂觀地假設全部 8.8 ms 都恰好以 1.093× 加速，saved=8.8×(1−1/1.093)=0.749 ms，38.6/37.851−1=1.98%；這不是適用本機的估計，實際 nt≥2 占比與重複工作皆未知。[ledger](../EXPERIMENT_LEDGER.md#L195)。

4. **llama.cpp [#27402](https://github.com/ggml-org/llama.cpp/pull/27402)：AVX2 IQ panel GEMM。** 將 8 個 weight rows 暫時解碼到 cache-sized int8 tile 後供多 token 使用，涵蓋目標 grid IQ；PR 作者在 512-token batch 報 dense 最多 10×、MoE 約 2×，小 batch 收益較小，非 nt=1 證據。AVX2 可用，不需 AVX-512；scratch 是暫時 panel，不等於第二份 resident 權重，但 peak RAM 及固定 20 GiB cache 的共存須確認。作者報約 0.24% PPL 差，故品質 **邊界**，不得假設只有累加次序差異。與 [ledger 的 NR2/NR4](../EXPERIMENT_LEDGER.md#L515) 都處理 row/token reuse，機制不是完全相同：這裡顯式建 int8 panel，且與 activation-dependent LUT 不同。PR 的 10-row batch 測試不能證明 nt=2–3 有益；2× 若錯誤地套到全 gate/up 得 saved=4.4 ms、38.6/34.2−1=12.87%，只能是算術情境，**不是此工作的預測**。需先取得其實際 per-expert dispatch threshold、臨時記憶體及量化／rounding 語義，才可決定是否是新且允許的低 nt 線索。

5. **[llama.cpp #25346](https://github.com/ggml-org/llama.cpp/pull/25346)：MSVC native 偵測 AVX-VNNI。** PR 稱 FindSIMD 未偵測致 generic dot 使用 maddubs/madd；i5-13420H、Q4_0、8 threads 的 pp512 570→753 t/s（+32%），tg128 不變；非本五類 IQ nt=1 效能證據。VEX AVX-VNNI 不需 AVX-512。品質：以相同整數語義為前提，仍須檢查正確性；不改 resident weights。與現行 iq256 的 VNNI 已部署重疊；而 ggml IQ vec_dot 是否真的受此 macro 控制、會變出何種指令，本次未檢查實際遠端編譯產物，不能推定。等五類全 gate/up 理論 1.2× 情境 3.95%，但 PR 不支持任何此處的 r。亦未找到可核實的 Windows clang-cl 對 MSVC、相同 IQ kernel／相同 ISA 的實測比較；不能宣稱 clang-cl 減少 spills 或必然更快。[#26348](https://github.com/ggml-org/llama.cpp/pull/26348) 是 Q2_0，對 down 不列收益，也不能直接證明 IQ 路徑受益。

6. **[T-MAC](https://github.com/microsoft/T-MAC)／[論文](https://arxiv.org/abs/2407.00088)：activation LUT 與低位元整數 GEMM。** 它展示低 bit × activation lookup，不是對這五個 GGUF lattice codebook、原量化值及原 Q8_K 格式的已證直接支援；範例涉及轉換模型。與 [既測 full-H LUT](../PLUS10_REVISED_PLAN_20261030.md) 同屬 activation-dependent LUT，既有實作僅 baseline 13.8–25.1% 吞吐。不同 LUT 算法不能一概否定，但目前沒有不同算法、維持精確值且有成本證據的候選；品質與收益均未確認。**不以其其他格式的速度當作 IQ 收益。**

7. **[Intel Neural Speed](https://github.com/intel/neural-speed)** 宣稱 AVX2／AVX-VNNI 與多種 N-bit 權重及 GGUF 支援，但公開說明不證明五種 GGUF IQ codebook 原值直接運算或其 nt=1 效能；不能把通用 N-bit 支援等同 IQ lattice 支援。品質、額外 resident 記憶體及收益未知。[KTransformers llamafile 文件](https://github.com/kvcache-ai/ktransformers/blob/main/doc/en/operators/llamafile.md) 證明其 backend 的來源，並未證實對指定格式快於現行 kernel；[ik 作者討論](https://github.com/ikawrakow/ik_llama.cpp/discussions/319) 指出 llamafile 相關代碼同源，故不能把這些專案當作獨立收益累加。

8. **Gracemont E-core**：Intel [Optimization Reference Manual](https://cdrdv2-public.intel.com/821614/356477-Software-Optimization-Manual_V2.pdf) 提供 Atom 指令優化資料，並不提供本 IQ kernel 的可轉移實測速度。現有 [ledger](../EXPERIMENT_LEDGER.md#L209) 記載 E-core gather 顯著慢，IQ3_S 與 IQ2_S 的 no-gather VNNI 已量過；不重提 gather 或泛泛調 affinity。未找到對這五種格式與 Gracemont、nt=1 的新方案及速度。改 compiler 的 E-core codegen 只屬待驗證假說，沒有可信 end-to-end r。

## 優先級與下一步研究

沒有合格的 top 3。僅保留兩個**尚未確認全新、亦未證有收益**的唯讀研究方向：

1. 核對 #27402 最終 source 中每 expert 的 dispatch threshold、scratch 容量和 exact Q8_K 算術，確認 nt=2–3 是否會走、是否符合品質；即便符合，也仍需與既有 NR2/NR4、iq256 做具體機制去重。
2. 對照 #2240 的 non-R4 IQ2/IQ3 路徑與實際 Strata iq256／ggml 路徑，特別是 IQ2 sign 解碼、Q8_K 292-byte ABI 和 P/E 分支；來源出自 ik，不能先假定為新方案。另查 MSVC VNNI macro 對現行 ggml 的實際作用；與 clang-cl 性能比較目前無證據。

此為研究排序，非執行、build 或 benchmark 授權；不建議重跑 R4、完整 activation LUT、NR2/NR4、gather／prefetch 掃描或 NT1 extension。

## Coverage 與限制

要求範圍為 d4c1f755 之後的 ik commits/PR、2025–2026 llama.cpp PR、llamafile、KTransformers、T-MAC/bitnet、Intel 後端、Windows compiler codegen 和 E-core。實際完成：讀取指定交接文件與兩份計畫、R4 kernel notes、兩份既有搜尋報告；ledger 以關鍵字查詢及相關位置補核，**並非逐行完整讀取**；首次合併輸出被截斷，已對關鍵 ledger 和 kernel notes 另查，計畫及長報告只依可見段落與 targeted 搜尋理解。公開資料以關鍵字搜尋、上述 PR 正文與專案說明查核；不是對所有 ik commit/PR 逐筆比較，也無法確認 d4c1 的 ancestry。未完整審查 #27402 source 的最終 threshold、所有開放及已合併 llama.cpp PR、bitnet.cpp、xFasterTransformer 的完整 source、Windows clang-cl disassembly 或 Gracemont kernel 指令級數據。GitHub commit 頁對指定 d4c1 抓取失敗，不能排除未索引的後續改動。公開頁和 PR 狀態可能變動；效能數字皆為來源自報、不同硬體及工作負載。沒有 SSH、遠端操作、build、benchmark、GitHub 寫入或 live binary/source 驗證；本機非 Git repository。
