# Strata decode 提速：文獻與既有實驗交叉研究

日期：2026-10-30。研究限定本機協調檔與公開網頁；沒有 SSH、遠端操作、編譯、benchmark 或 GitHub 寫入。下列機器設定與分段數字來自使用者 brief，非本次 live 驗證。

## 判讀方式

基準 38.6 ms/window、約 47 tok/s；若每 window 的有效輸出 token 數固定，+10% 需要 38.6−38.6/1.1 = **3.51 ms/window** 的淨縮短。各分段互有重疊：SSD join 4.4 ms 與 admission copy 0.9 ms 包含在 CPU segment 21.7 ms 的敘述中；不得將兩者再加到 21.7。GPU-reach wait 11.7 ms 是等待而非可直接刪去的純 GPU 工作。下列「上限」是該段全部移除的樂觀算術邊界，並非可以達到的預測，亦不應跨候選相加。若只是提高接受率，則應以有效 token/window 除以 window 時間衡量，而非假設 window 本身縮短。

採樣分布必須相同；精確 speculative sampling 須包含 target 分布和 rejection/correction；greedy 的一致性不能證明抽樣分布一致。tree 的各路徑必須保留因果 attention、GDN state、HC 和 KV commit，不能讓兄弟分支互相污染；GPU 與 CPU 的浮點運算須符合題目允許的 fp32 rounding 差異，不能把「數學上相同」直接當作已驗證。新舊比較僅指已查本機資料，無法保證所有歷史實驗均已去重。

## 候選

### 1. Native MTP tree verification — ALLOWED，成本 L

[Lattice native MTP tree issue](https://github.com/ohdearquant/lattice/issues/591) 描述將單一路徑擴成分支 tree，同批驗證多個 token 候選；[SpecInfer](https://www.cs.cmu.edu/~zhihaoj2/papers/specinfer.pdf) 提供 tree verification 先例。MTP 可作 proposer，但 issue 是設計提案，不能當已驗證加速。精確抽樣需採用有證明的 tree verifier；不得簡單選最高分分支。需先確認實際 MTP head 能否低成本提供分支，及 GDN/HC 狀態樹能否正確實作。

目標是每 window 接受更多 token，非某一固定分段。若 window 成本維持 38.6，平均有效 token 增加 10% 即 +10%；更一般地，需新舊平均有效 token 比 > 1.1 × 新舊 window 時間比。例如成本增加 10% 時，token/window 至少需增加 21%。沒有固定 ms/window 上限，額外 tree 節點會增加 routed experts、I/O 與記憶體占用。相對 [R4 plan:79-80](../R4_PLUS10_PLAN_20261030.md#L79) 已試深度、gate、lookup 和 spec-split，**tree 狀態與 branching 為新候選，非已證完全未試**。文獻無此 12600KF/4070 混合 offload 證據；SSD miss 可能抵銷收益。

### 2. Delayed tree expansion / traversal verification — ALLOWED，成本 L

[Dynamic Delayed Tree Expansion](https://arxiv.org/abs/2602.16994) 在較深位置才展開分支，並比較不同精確 tree 驗證方法；作者報告跨模型和抽樣設定的平均吞吐差異，並非本機測量。此為候選 1 的替代 tree 設計，不是可疊加的獨立收益。優點是假設可避免根部大量分支與不必要 expert 載入；適用性取決於本模型分支機率、昂貴的 routed experts 和驗證狀態複製。

同上：固定 38.6 ms/window 而 token/window +10% 等同 +10%；若增加 5% window 成本，需 token/window 至少 +15.5%。未有本機接受率或 tree node 成本，因此不存在可信的 ms 上限。已查計畫的線性深度試驗並不等同 delayed branching；**新，但依賴候選 1 基礎工程**。

### 3. Suffix automaton / suffix tree proposer — ALLOWED，成本 M–L

[SAM-Decoding](https://arxiv.org/abs/2411.10666) 以 suffix automaton 從既有文字找可重用片段；[SuffixDecoding](https://arxiv.org/abs/2411.04975) 使用動態 suffix tree 和候選樹。它們產生草稿，輸出仍由 target 的精確 verifier 決定；不得直接輸出檢索結果。與已測 lookup-chain 3 不同之處是可變長 suffix 匹配、頻率排序或 tree，而非固定鏈的直接重跑。

目標為提高有效 token/window 或減少 MTP draft 開銷。若僅完全消掉 draft 1.8 ms，理論上限為 38.6−1.8 = 36.8 ms，即 38.6/36.8−1 = **4.9%**；若增加接受率可超過此值，但沒有數值上限或本機證據，資料結構成本和額外 verify 要扣除。既有 lookup 結果見 [switch inventory 的已測表](../switch-inventory-20261029.md) 中 `--lookup-chain 3`（+1.59%，不穩）；新的是 suffix automaton/tree，**同家族新機制，未證有收益**。論文工作負載不是本機。

### 4. DirectStorage CPU-memory destination and persistent queues — ALLOWED，成本 L

[Microsoft DirectStorage](https://github.com/microsoft/DirectStorage) 說明批次 I/O 對小讀取可減少 CPU 提交負擔；[官方指引](https://github.com/microsoft/DirectStorage/blob/main/Docs/DeveloperGuidance.md) 也警告單次 read latency 與 staging/queue 設計。只讀原封不動 expert bytes 到 CPU 可消費的記憶體；不使用壓縮或更換 expert，且必須檢查 buffer alignment、lifetime、取消及錯誤傳播。公開 [SSD streaming POC](https://www.reddit.com/r/LocalLLM/comments/1u6j5a3/experimental_poc_streaming_a_160gb/) 使用 persistent DirectStorage service，但其 GPU streaming、模型及效能與本機不同，非可移植的提速證據。

目標 SSD join 4.4 ms：即使完全消除，38.6/34.2−1 = **12.9%**；需消除至少 3.51/4.4 = **79.8%** 才單獨達 +10%，而 DirectStorage 不能消除實際 SSD latency。官方未證此特定專案讀取粒度下較現有 overlapped ReadFile 快。既有 mapped/direct 比較及 arrival 結果見 [R4 plan:79-80](../R4_PLUS10_PLAN_20261030.md#L79)；DirectStorage API 本身在所查紀錄中未見，**新 API，非新 I/O overlap 機制**。

### 5. Batched completion with I/O completion ports — ALLOWED，成本 M

[Microsoft IOCP](https://learn.microsoft.com/en-us/windows/win32/fileio/i-o-completion-ports) 說明多個 overlapped 操作可透過 completion port 收集與限制 runnable threads。研究點是合併完成通知、降低喚醒/每筆管理成本；既有提交和 completion 實作是否已如此，僅靠 local 摘要無法確認。所有必要讀取仍須成功並讀回原 bytes，不能因漏通知跳過 expert。

目標 SSD join，硬邊界 **4.4 ms/window**；若僅減掉其中 10%，示例為 0.44 ms，38.6/38.16−1 ≈ **1.15%**，10% 是假設而非實測。需要先找到 join 裡 completion/喚醒開銷而非裝置服務時間。與 [R4 plan:145](../R4_PLUS10_PLAN_20261030.md#L145) 的 QD4→8 是不同的完成通知機制，但也可能已存在；**是否新未確認**。官方證明 API 語義，不證速度。

### 6. Q2_0 down AVX-VNNI dot — ALLOWED，成本 M

[llama.cpp PR #26348](https://github.com/ggml-org/llama.cpp/pull/26348) 宣稱對 Q2_0 × Q8_0 使用 x86 VNNI；先核對 Strata 的 type42 `q2_rows_any`、activation 格式、產生的 P/E 組語及位元解碼是否已具同等路徑。不能把 PR 中另一格式/模型的倍率直接套至本機；需要相同量化 codes/scales 和允許的浮點誤差。

目標 Q2_0 down；簡化上限為 CPU segment 21.7 ms 中的 down 且限 Q2_0 部分，該份額未知，最多 **21.7 ms**，實際遠小於此；down 已近 45.7 GB/s，計算加速可能只減少極少 wall time。假設其暴露時間為 2 ms、kernel 無限快且讀取完全消失，才有 2 ms 上限；這只是情境，不是量測。PR 報告不同 CPU-only workload，非本機。 [R4 plan:71](../R4_PLUS10_PLAN_20261030.md#L71) 已指出不能誤用 scalar Q2_0 down 作基準；因此 **PR 特定實作新穎性未確認，不應在核對原 kernel 前重做**。

### 7. Large pages for expert cache — ALLOWED，成本 M，需系統權限

[Microsoft large-page support](https://learn.microsoft.com/en-us/windows/win32/memory/large-page-support) 需要 `SeLockMemoryPrivilege`，大頁可能減少 TLB 壓力；不改 weight bytes。先核對配置是否可用、記憶體碎片和 slot 容量，且設定權限需要明確授權。本機先前盤點稱預設會嘗試 large pages 但非特權帳號受拒，這是歷史記錄，並非目前遠端狀態。

目標 CPU expert cache 訪存，理論總段上限 21.7 ms，真正 TLB 造成的 exposed 時間未知，down 的物理頻寬上限不會因 page size 消失。例：若 TLB stall 僅佔 21.7 的 5%，全部去除也僅 1.085 ms、約 2.9%；5% 無量測依據。見 [switch inventory 的不可用項](../switch-inventory-20261029.md)，**已盤點，非新發現，未見成功啟用或收益證據**。

### 8. SP-MoE draft-informed cutoff prefetch — ALLOWED（僅精確載入），成本 L

[SP-MoE](https://arxiv.org/abs/2510.10302) 利用 draft/target 的對應來預載 expert，並用 cutoff layer 約束過度讀取；僅借用預載和 cutoff，最終仍以 target router 執行所有實際選中 experts。錯誤預測只能造成多餘 I/O，不能改 routing。此法需先確認本 MTP 是否真的暴露與 target layer 對應的路由訊息；MTP head 不等於免費得到整模型各層 expert 路由。

目標 4.4 ms SSD join：全消除上限 4.4 ms（12.9%），但預載競爭 SSD、DRAM、CPU，收益未知。[R4 plan:178](../R4_PLUS10_PLAN_20261030.md#L178) 既有 route prediction miss byte recall 66.3%、extra/rescued 4.83×，不過成本閘門；**SP-MoE cutoff 是新文獻機制但仍屬已受挫家族，沒有證據它能克服本機代價**。論文平台與本機不同。

### 9. Expert deferral / heterogeneous scheduling — ALLOWED，成本 L

[KTransformers](https://madsys.cs.tsinghua.edu.cn/publication/ktransformers-unleashing-the-full-potential-of-cpu/gpu-hybrid-inference-for-moe-models/SOSP25-chen.pdf) 的 Expert Deferral 將 expert 工作與 GPU 其他計算安排重疊；[Fiddler](https://arxiv.org/abs/2402.07033) 比較 CPU 執行與搬到 GPU。僅能延後順序與安排，不得漏算或替換 experts，combine 的浮點差異需驗證。

目標 CPU/GPU 同步暴露；以 11.7 ms GPU-reach wait 為極寬鬆上限，真正可重疊時間未知，不能假設整段消失。若只多隱藏 0.62 ms，38.6/37.98−1 ≈ 1.63%；0.62 是既有 arrival 分析的特定上限而非所有排程上限。見 [R4 plan:80](../R4_PLUS10_PLAN_20261030.md#L80) 與 [PLUS10 revised:37-44](../PLUS10_REVISED_PLAN_20261030.md#L37)：pipeline 已部署、需要原排程定位具體新可省鏈。**已有同類，不建議原樣重做**。Fiddler repo 表示其 CPU PyTorch 路徑在無 AVX-512 時慢：[repo](https://github.com/efeslab/fiddler)。

### 10. Expert admission copy elimination — ALLOWED，成本 M–L

[Microsoft DirectStorage guidance](https://github.com/microsoft/DirectStorage/blob/main/Docs/DeveloperGuidance.md) 描述 staging 的資料搬運與資源管理；可研究是否讓讀取直接落在未被使用的最終 cache slot，消除目前 staging→LRU admission copy。這是依 API 和本機計時提出的工程推論，不是來源中已證的 Strata 實作。必須保持 buffer alignment、slot 所有權與 eviction 語義，且不能以犧牲 slot 容量為代價隱藏成本；目前是否已有直達路徑未查遠端，未知。

若整個 admission copy 暴露且可省，最大 **0.9 ms/window**，38.6/37.7−1 ≈ **2.39%**；不可能單獨 +10%。[R4 plan:170](../R4_PLUS10_PLAN_20261030.md#L170) 已列為需成本診斷，**已知待查方向，不是新發現**。沒有相同平台量測。

### 11. Adaptive tree structure OPT-Tree — ALLOWED，成本 L

[OPT-Tree](https://arxiv.org/abs/2406.17276) 根據接受長度期望選擇 tree 的擴展。使用同一 MTP 權重作 proposer、精確 verifier 與確實隔離的 GDN/HC 狀態時符合條件；論文的 up to 3.2× 是對其 autoregressive baseline，不能外推到已有 MTP 的 Strata。它與候選 1、2 是替代設計，禁止將收益相加。

以每 window 成本 38.6 和 token/window 為基準：成本增 20% 時需要 token/window 增 1.1×1.2−1 = **32%** 才達 +10%；增量成本、平均接受長度與 expert 負擔未知，沒有可信 ms 上限。已查本機 linear depth/gate 不等於 adaptive tree，但完整去重未完成；**新 tree 機制，無本機證據**。

## 不符合品質或硬體限制

- [Pre-gated MoE](https://www.microsoft.com/en-us/research/wp-content/uploads/2024/05/isca24_pregated_moe_camera_ready.pdf)：改變 gating 的位置／模型結構，不能當成保留現有模型的純排程。
- [SPICE](https://arxiv.org/abs/2608.21240) 的 approximate expert surrogate 若用來取代實際 expert 輸出會改計算；只預載並精確恢復才可能符合。
- [Approximate Speculative Decoding](https://arxiv.org/abs/2608.03447) 的近似 verifier 不保證目標輸出分布，排除。
- 更低權重量化、KV 精度降低、routing bias、expert skipping、AVX-512 專用 kernel、硬體更換或超頻均不符合 brief。歷史 `ROUTE_TAIL_SKIP=7` 是否在現在有效設定中啟用，**本次未 live 確認**；若啟用，與此次品質條件衝突，任何未來驗證須先釐清基準，不可把它默認為符合條件。

## 排序：真正新增、符合條件的三個方向

1. **Native MTP tree verification**：唯一有機會透過增加每 window 有效 token 跨過 3.51 ms 等效門檻的方向；但 GDN/HC、exact sampling 和 SSD 追加讀取讓成本高，尚無相同機器的效果。
2. **Delayed tree expansion**：比直接擴大根節點更有針對性，提供控制分支 I/O 的研究假設；與第一項共用基礎工程、並非第二份可疊加收益。
3. **DirectStorage persistent queue**：Windows 專有且保持 bytes，不需更改模型；但 SSD join 必須消除近八成才單獨 +10%，公開資料沒有證明能在此 I/O 形狀達到。

這是研究優先順序，不是宣稱任何項目有足夠證據可直接開工或達到 +10%。若要求三項完全獨立，候選 2 與 1 同屬 tree；目前找不到第三個同時獨立、可信且足以支持 +10% 的新方向。

## Coverage 與盲點

- 依使用者要求讀取交班協定與五份指定檔案；首次整批 shell 輸出被截斷，後續以主題及行號查詢補核。長 ledger 並非逐行完整閱讀，計畫檔也非逐字完整審查；去重結論僅涵蓋輸出與 targeted `rg` 命中的項目。沒有讀取遠端 source、binary、設定、原始 trace 或 live process。
- 網頁檢索涵蓋 exact tree/speculation、MoE CPU/GPU orchestration與 prefetch、AVX-VNNI Q2_0、Windows DirectStorage/IOCP/large pages；閱讀搜尋摘要、部分原文頁與 repo/issue，不是完整系統性文獻回顧。未完整逐項檢索題目列出的所有專案、全部 GitHub issues/PR、Reddit 或每種 CPU kernel；尤其 AdapMoE、HOBBIT、ProMoE、SwapMoE、DAOP 和 vLLM/SGLang offload 未完成逐篇評估。
- 沒有相同 12600KF + DDR4-3200 + RTX 4070 + Windows + 該模型和 100k context 的可核實對照；來源所報加速不能套用至本機。分段資料由 brief 提供，未確認是否同一次測試、是否完全守恆或彼此獨立；估算僅供量級篩選。
