# Batch-1 MoE decode 的精確 CPU／GPU 重疊：文獻搜尋結果

搜尋日期：2026-10-30。僅公開資料研究；未連線遠端、未執行 benchmark。硬體、16 ms／39 ms 與既有功能均採題目設定，並非本次實測。

## 結論

找到可研究的精確方向：**已路由的專家依實際工作量分配運算位置**、**將同一專家的中間維度分塊並在同層合併**、**分段回傳並累加已完成的專家結果**，以及**縮短 CPU／GPU 交接**。前兩者與分段合併有明確數學路徑，但沒有找到針對指定 4070／12600KF、IQ3_XXS、2–6 token MTP 的直接加速數字。論文數據不能當成該機器的預期收益。

跨 window draft 與 verify 重疊有研究，但現有 MTP 對 target hidden state 的依賴使直接套用未獲證實；精確 speculative sampling 的分布正確也不自動等於「同一 seed、同一逐 token 結果」。如果嚴格要求保留現有 draft 與隨機數消耗順序，必須另行驗證。

題目所述 16/39 ms 是每 window 而非每 layer 的數字。假設它全部都可移除且其他成本不變，Amdahl 上限為 39/23 ≈ **1.70 倍**；實際不可能據此認定全部等待可被消除，也無法從它估算某個方法的收益。

## 候選方法

### 1. 依本層實際 routing 分配已選專家

[Fiddler 論文](https://arxiv.org/html/2402.07033) 使用 CPU/GPU 延遲模型，依專家的 token 數、權重傳輸與算力，決定把已選專家留在 CPU 算或傳到 GPU 算；兩端可並行，最後同層合併。這是 router 已完成後的排程，不需要預測下一層專家。對本題可以比較「CPU 算 miss」與「將已知 miss 的同一量化權重搬入空間並在 GPU 算」，也可利用現存 GPU 副本；需要把 PCIe 傳輸、VRAM 擠占、GPU 熱專家工作與 CPU 排隊成本一起算入。動態搬移可能比 CPU 更慢，特別是在小 token 數與 DDR4／PCIe 限制下。

**品質：有條件是。** 保持每 token 原 router/top-k、原始量化值、全部專家與同層 residual；GPU kernel 的解量化及乘法精度也必須與目前 CPU 路徑相符，只容許加總順序差。若轉成其他精度或其算子差異超過此定義，則不合格。這是實作條件，論文沒有證明對 IQ3_XXS 成立。

**數據：** Fiddler 報告相對標準 offloading 單 batch 延遲 8.2–10.1 倍；其環境包括 Quadro RTX 6000 24 GB + Xeon Gold 6126，另一組 RTX 6000 Ada 48 GB + Xeon Platinum；並非本題的已優化 hot/cold baseline。作者也報告 Mixtral-8x7B 超過 3 token/s，不能推算本題改善。[論文](https://arxiv.org/html/2402.07033)、[作者專案](https://github.com/efeslab/fiddler)。

[KTransformers expert scheduling](https://github.com/kvcache-ai/ktransformers/blob/main/doc/en/kt-kernel/experts-sched-Tutorial.md) 則用 expert mask、不同放置策略與動態更新；文件中的 10% GPU expert ratio 表為 frequency 58.60、dynamic 70.22（約 +19.8%），官方 release 宣稱低 GPU expert ratio 最多 +30%。這是放置策略整體差異，並不證明本題逐層即時搬移有效；文件測試配置為 4×4090、Xeon 6454S、512 GB、Linux，文件要求至少 24 GB VRAM 和 AVX-512，故不能視為 4070／12600KF 可直接運行的證據。[release](https://github.com/kvcache-ai/ktransformers/releases)。品質同樣取決於量化與算子實作，文件未驗證此嚴格條件。

### 2. 單一專家按中間維度切分

對標準 SwiGLU 專家，令中間維度集合分成互斥的 A、B：各自計算 `s_A = silu(Wgate_A x) ⊙ (Wup_A x)`，再算 `Wdown_A s_A`；B 同理，最後在**同一層**相加。因 down projection 沿中間維度可加，GPU 可處理部分 rows／對應 down columns，CPU 處理餘下部分，不改選到的專家。所需資料是 gate/up 對應 rows 和 down 對應 columns；只拆 gate/up 而不對應拆 down 並不完整。

**品質：有條件是。** 每個量化 block 及其 scale 保持原值，切分需符合 block 邊界；不重新量化，不改 activation/乘法精度與非線性，完整地在原層加總。量化格式、累加順序及 CPU／GPU kernel 仍需檢查。尤其 GPU 從 RAM 搬片段、down 權重重新排版、較小 kernel、額外合併和 VRAM 空間可能抵銷收益。可行性是數學推論，非已驗證的 Strata 實作。

[FIRM-MoE](https://ojs.aaai.org/index.php/AAAI/article/download/39106/43068) 提供細粒度拆分的相關證據，**但其文中子專家是分開的 gate/up/down 矩陣，不是已證明的 CPU/GPU 行切分實作**；它的完整方法另包含預測與預載，因此不能將其加速歸因於此候選。作者在 batch 1、RTX 3090 24 GB、32 核 CPU、64 GB RAM，Qwen／DeepSeek／OLMoE 測試，報告最高 1.5 倍 decode，對 Fiddler/llama.cpp 跨設定平均 1.31 倍；不是此方法單獨消融結果。單 GPU 消費級硬體形式相近，但 12 GB、DDR4、IQ3 與 MTP 皆未驗證。

### 3. 提前回傳已完成專家的部分結果，重疊傳輸與合併

對同一層已選專家，CPU 完成一個 expert 或一個完整 output tile 就回傳；GPU 用獨立 stream 累加已到達結果，同時 CPU 繼續餘下專家；最後仍等待全部專家，才執行本層 residual 與下一層。這縮短的是**最後一次結果傳輸／合併尾巴**，不能讓下一層在結果不完整時開始。需要量測分段通知、PCIe 複製、累加 kernel 與 CPU 排程是否比一次回傳更昂貴。

**品質：有條件是。** 同一組完整結果與量化值，同層合併，只允許加總順序差；如改變中間精度則不符合。量測時也應比對每 token top-k，因浮點差異可能在臨界點影響後續路由。

[Tile-level signaling 論文](https://arxiv.org/abs/2607.19539) 是相關的 producer/consumer 類比：在多 GPU expert parallel 系統，專家計算 tile 完成後即啟動回傳通訊。其報告 operator（expert GEMM + 回傳 all-to-all）最高 3.01 倍、完整 MoE layer 最高 1.78 倍；**這是跨 GPU 通訊，並非 CPU→單張消費 GPU，也沒有本題的數據**。實作是否在 batch 1 的小輸出尺寸有利未知。

[llama.cpp RFC #24528](https://github.com/ggml-org/llama.cpp/discussions/24528) 報告其特定 fused rows CPU overlap 實驗 **−2.6% 至 −6%**，與提早 D2H、stream priority 等一起列為未採用項；不是此處所有分段合併方案的否定，但提供很具體的負面先例。該 RFC 有不同硬體、cache 與其他設定，無法移植其百分比。

### 4. 精簡交接與工作提交

[NVIDIA CUDA 文件](https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/asynchronous-execution.html) 指出 page-locked host buffer、非預設 stream 和事件可讓具備相應能力的裝置重疊複製與計算；先以 trace 區分 router→CPU input、喚醒、CPU 實算、CPU→GPU output 與 GPU combine，才能知道優化哪一段。將全裝置同步縮窄為必要的 stream/event 依賴、重用 CPU worker、減少 host enqueue／graph 重建，可保留運算內容；[ggml issue #721](https://github.com/ggml-org/ggml/issues/721) 是 CPU worker 重用與非同步 queue 的具體提案，並非本題已完成效能測量。

**品質：是，前提是依賴和可見性正確且數值算子不變。** 報告的此工作負載加速：**未找到**。這只能減去測得的交接／啟動開銷，不能消除 CPU 真正的計算時間。Pinned memory 使用、stream 實際重疊與 Windows driver 行為需核對；不應假設 page-locked 一定更快。

GPU 端 doorbell／stream memory wait 理論上可以減少 host 發送延遲，但 [CUDA 8 driver 文件](https://docs.nvidia.com/cuda/archive/8.0/pdf/CUDA_Driver_API.pdf) 對 Windows 該 API 記載需 TCC；這是**舊版文件**，不能據此斷言現行 CUDA/4070 Windows 一定支援或不支援。要先查目前 API 文件、driver mode、capability，再討論；本搜尋未找到目標平台可用性或速度的直接證據。GPU 忙等亦可能占用資源。

### 5. 驗證期間提前準備下一輪 draft

[Saguaro／Speculative Speculative Decoding](https://arxiv.org/abs/2603.03251) 在 verify 期間對可能的接受結果預先 draft，命中時縮短下一輪等待。它報告相對最強 speculative baseline 平均約 30% 快、最高約 2 倍；主要設定 batch 1、greedy，target 4×H100、draft 另用 1×H100。這是端到端 draft 隱藏，並非每層 CPU expert latency 改善，硬體遠大於本題。

**品質：論文算法維持 target 輸出分布；對本題嚴格定義尚不能判定為是。** 原樣保留現有 MTP 權重、隨機取樣及 target 路由時，必須確保草稿所需 target hidden state／GDN state 與接受邊界正確；預先算錯分支只能捨棄，不能讓它進入 residual。多分支可能改變 RNG 消耗，不能僅以分布等價宣稱同 seed 行為一致。單 GPU 上 draft 會與 verifier 的 GPU kernels／VRAM 競爭，MTP 可能根本拿不到尚未完成的正確 hidden state；是否存在可提前的現有子圖以及效益均未知。論文使用額外 draft device，沒有證明同卡空檔可執行此 MTP。

## 建議的證據順序

先讀取既有實作與 trace：確定 16 ms 包含多少真正 CPU 運算、等待、回傳和 combine，以及 hot expert GPU 工作的時間位置。接著僅做離線成本推估：對已選專家與各 token 數比較 CPU 執行、已 resident GPU 執行、權重搬移及子專家拆分所需 bytes；核對 IQ3 block 邊界及 GPU 數值語意。只有存在足夠長的可隱藏尾巴或可轉移工作，才值得考慮最小 A/B。若後續獲授權實測，需固定 current-best binary、prompt、採樣設定、量化、MTP 及硬體狀態，記錄 top-k、結果誤差、acceptance、每 window wall time 和端到端 tok/s；不能把 profiler 中互相重疊的區間相加。本文不授權或啟動實驗。

## 搜尋範圍與 coverage

執行 **20 組不同搜尋**，涵蓋 2024–2026 arXiv、官方論文、CUDA 文件與指定專案公開 issue／PR／repo。以下為實際查詢（概略保留原查詢字詞）：

1. MoE inference CPU GPU collaborative expert neuron partition batch 1 Fiddler hybrid decode
2. arxiv mixture experts heterogeneous CPU GPU intra expert partition inference decode 2025
3. MoE CPU GPU expert parallel splitting neurons cooperative inference single GPU 2024
4. Fiddler CPU GPU heterogeneous MoE inference experts workload balance paper speedup
5. FIRM-MoE fine grained expert decomposition cpu gpu accuracy split
6. site:github.com/ggml-org/llama.cpp pull request cpu gpu moe overlap asynchronous event
7. site:github.com/ikawrakow/ik_llama.cpp moe cpu gpu asynchronous expert overlap
8. site:github.com/kvcache-ai/ktransformers cpu gpu moe balance asynchronous expert inference
9. site:github.com/Mozilla-Ocho/llamafile moe cpu gpu overlap expert
10. site:github.com/SJTU-IPADS/PowerInfer MoE GPU CPU split neurons inference speed
11. site:github.com/efeslab/fiddler issue gpu cpu parallel expert dynamic placement
12. CUDA CPU GPU synchronization stream wait value write value host mapped memory doorbell latency inference cuda graph
13. arxiv 2025 2026 speculative decoding overlap draft verification asynchronous single sequence dependency
14. arxiv FIRM-MoE decomposition GPU CPU sub-expert down projection experiment
15. site:github.com/SJTU-IPADS/PowerInfer CPU GPU hybrid neuron split activation inference
16. site:github.com/ggml-org/llama.cpp asynchronous CPU GPU moe expert overlap pull
17. site:docs.nvidia.com cuda cuStreamWaitValue32 windows WDDM support
18. site:github.com/mozilla-ai/llamafile issues 973 MoE matmul regression
19. site:arxiv.org MoE cpu gpu fine grained expert partition overlap inference
20. site:github.com ktransformers CPU-GPU Expert Scheduling inference

另查 CUDA Windows TCC、Saguaro 硬體、Fiddler benchmark 和 FIRM-MoE 硬體。實際查閱相關論文摘要及所需段落、FIRM 論文、Fiddler 論文、KTransformers tutorial、llama.cpp RFC、ggml issue、CUDA 文件；搜尋並抽查 [ik_llama.cpp 文件](https://github.com/ikawrakow/ik_llama.cpp/blob/main/docs/parameters.md)、[PowerInfer repo](https://github.com/SJTU-IPADS/PowerInfer)、[llamafile issue #973](https://github.com/mozilla-ai/llamafile/issues/973)。llamafile 該 issue 的 CPU-only regression 與 kernel 修復不等於本題已有多 token kernel 的增益。PowerInfer 的預測稀疏神經元不能直接滿足本題的精確條件。

這是依搜尋索引與相關性篩選的**定向搜尋**，不是完整掃描所有 arXiv 論文、repo 的全部 issues／PR 或程式碼；大型論文及長 RFC 只查相關段落，未逐行審核實作或每個量化 kernel。搜尋索引可能漏掉未索引的實作，亦未驗證指定機器的 CUDA driver、IQ3 kernel 與 MTP graph。未找到直接 benchmark 不等於證明方法不存在。
