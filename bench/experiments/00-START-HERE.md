# Strata（RTX 4070 桌機）優化：提案前必讀

更新：2026-10-31（第 2 版）。提任何加速方案前，請先讀完本頁，並對照第 4 節的「已試方向索引」。
本頁沒列到的細節，在同目錄的 `EXPERIMENT_LEDGER-20261031.md`（完整實驗紀錄）與各實驗資料夾裡。

## 1. 名詞定義（請照這個用詞，不要混用）

「不降品質」這個詞很容易被誤會，所以這裡分成兩類，提案時請寫清楚屬於哪一類：

- **A 類：輸出不變。**
  - 條件：同硬體、同權重與量化值、同 expert 選擇（含現行的 `ROUTE_TAIL_SKIP=7`）、同 sampling、精確的 speculative decoding（MTP 只影響速度、不影響輸出）。
  - 只允許浮點加總順序造成的微小數值差異。
  - 改 kernel、排程、快取、預取、搬運位置、編譯器，都屬於這一類，前提是 expert 選擇與數值結果不變。
- **B 類：會改變輸出。**
  - 例子：路由偏置（`ROUTE_PRIOR`、`ROUTE_BIAS`）、跳過低權重 expert（`GATE_SKIP`）、降精度、重新量化。
  - 速度可能大幅提升，但必須另做品質測試，不能稱為「不降品質」。
  - 使用者的主要目標是 A 類。B 類只在使用者明確要求時才測。

**不提硬體變更**（加 RAM、換 GPU 等）。也不提換權重或重新量化。

## 2. 現況（current best）

- 硬體：RTX 4070 12 GB（VRAM 只剩約 254 MiB 可用）、i5-12600KF（6P+4E）、DDR4-3200 雙通道 2×16 GB（實測讀取 45.7 GB/s，6 條 P-core 執行緒就飽和）、Windows 11、experts 放在 NVMe SSD。
- 模型：Qwen3.8-Flash-Next IQ3 混合量化 pack（48 層 × 512 experts；GU 型別：IQ3_XXS 6 層、IQ3_S 13 層、IQ2_XS 10 層、IQ2_S 10 層、IQ2_XXS 9 層；down 為 q2_0 或 iq4_nl）。
- 執行檔 SHA256：`A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8`
- 設定 SHA256：`060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93`
- 容量：VRAM expert slots 3153、RAM expert cache 20.00 GiB（arena 20479 MiB）。
- 速度：Hermes 10 題 × 512 tokens，約 46～47 accepted tok/s。
- 每個 verification window 約 39.2 ms，平均 1.79 tokens/window：

| 段落 | ms/window |
|---|---|
| GPU-reach（GPU 等待） | 11.63 |
| CPU expert pool（GU＋quant＋down，pipeline 重疊後） | 15.41 |
| SSD join | 4.65 |
| LRU 與其他 CPU | 2.27 |
| MTP draft | 1.76 |
| 其他 | 約 3.46 |

- **+10% 目標**：淨省約 3.4～3.6 ms/window。

### 重要：GitHub 上的程式碼不是實際在跑的程式碼

- 實際部署的 source 是 commit `f520bc5e9d31c93caeb296b059e3a3eaa16e493f`，base 為 `61b3fb5d`（上游 f-142 系列）。
- 這兩個 commit **都不在**這個 fork 的 main 上。
- 和 GitHub main 不同的 6 個檔案（含 per-expert GU→down pipeline），完整內容與 patch 放在 `live-source-f520bc5/`。
- 讀 `pool.cpp`、`expert_source.cpp`、`generate.cpp` 時，請以那個資料夾為準。

## 3. 已確立的硬體／機制事實（提案時請直接引用，不要重新假設）

- **CPU 與 GPU 計算 expert 的成本：** 經 PCIe 讓 GPU 計算一個 RAM expert 約 186～199 µs；CPU 計算約 60～89 µs。把 expert 從 CPU 移到 GPU（PCIe 路徑）實測變慢（10/29 PCIE_BALANCE_PORT；10/28 PARTIAL_PIN）。
- **VRAM 的邊際價值：** 每多 100 MiB VRAM 給 expert slot，CPU expert 工作約少 1.0～1.2%（10/29 VRAM_MARGINAL_SIM，離線估計）。
- **adaptive swap 的效果：** live VRAM hit 63.8%，靜態最佳約 52～58%。
- **CPU pool 內部（10/30 POOL_INTERNALS_DIAG）：**
  - GU：P 核 9.15、E 核 9.63 ms/w；
  - down：P 核 3.83、E 核 3.95 ms/w；
  - quant：約 0.01～0.04 ms/w；
  - host 等 pool 完成：只有 0.173 ms/w。
  - GU 是算力受限（單核約 3.8 GB/s）；down 已經頂到 DRAM 頻寬。
- **MTP：** 接受率約 87%；被拒位置 Top-2 rescue 為 0/41；verify 成本隨 T 陡增（T1/T2/T3 = 26.4/37.0/53.3 ms）。
- **下一層路由預測（10/29 ROUTE_PREDICT_DIAG）：**
  - `W_router[L+1]·x_L` top-10 的 recall 68.8%，SSD miss byte recall 66.3%；
  - 但多讀的量是救回量的 4.83 倍；
  - 提前量中位數只有 0.58 ms。
- **更早就拿得到的預測資訊**（用上一個 window 的路由）：precision 37%、recall 25%。
- **GPU：** decode 時固定 2850 MHz，沒有降頻。dense mmvq 6.96 ms/w（約 350 GB/s），HC 3.66 ms/w。

## 4. 已試方向索引（A＝輸出不變，B＝會改變輸出）

狀態說明：**已部署**＝在 current best 裡；**NO_GO**＝測過、沒效或變慢；**未確認**＝方向正面但證據不足；**暫停**＝使用者暫停。

### 4.1 CPU expert 計算

| 方向 | 類 | 結果 | 狀態 | 證據 |
|---|---|---|---|---|
| per-expert GU→quant→down pipeline（等同 Basalt／上游 PR #733） | A | 7 輪 +3.83%（CI +0.15～+7.51） | **已部署** | ledger NATIVE_GU_DOWN_PIPELINE、NATIVE_PIPE_PO_CONFIRM；`live-source-f520bc5/` |
| P/E 角色優先（P 先做 GU） | A | 執行失敗於 CPU Set guard，未測速 | 未完成 | NATIVE_PIPE_ROLE_PRIORITY |
| pool tasks（PR #1087） | A | 中位數 +2.82%，未過 3% | NO_GO | LUNA-20261010-015 |
| Intel gather／AVX-VNNI（PR #863） | A | 中位數 +0.05% | NO_GO | LUNA-20261010-015 |
| IQ3_XXS nt=1 AVX2 kernel | A | 比 ggml 慢 5.5% | NO_GO | LUNA-20261011-021 |
| 各型別 nt=1 單核微基準 | A | IQ3_S 1.78×，其他 1.08～1.26×；IQ3_XXS 只有 6 層 | 診斷 | IQ3_NT1、IQ_ALLTYPES_NT1 |
| IQ3_S multi-token（MT1） | A | +4.26%（CI +2.15～+6.37） | **已部署** | IQ3S_MT1_AB |
| nt=1 依型別改走 iq256（NT1_EXT） | A | 5 輪均值在雜訊內 | NO_GO | NT1_EXT_TYPES |
| GU 任務數 30 vs 60 | A | −0.03% | NO_GO | gu-tasks-20261015 |
| GU 依權重分配 | A | −1.28% | NO_GO | gu-weighted-20261015 |
| worker 依 P/E 速度分配 | A | E 群只晚 12.5%，未達門檻 | NO_GO | POOL_WORKER_SKEW |
| R4 重排（ik_llama 式，含 lowreg、tile、prepack、unpack、預取） | A | 全部比 native 慢 8～80% | NO_GO | CPU_R4_*、R4_*（10/29～30） |
| 原生 layout NR2/NR4 | A | −1.8～−16.9% | NO_GO | BIG_EXACT_P1 |
| IQ2_XXS 完整 LUT | A | 只有 baseline 的 13.8～25.1% | NO_GO | BIG_EXACT P2 |
| down 稀疏（neuron-major） | B | 5% 門檻剛好成立，但會改輸出（相對 L2 誤差約 18%） | 未做 | NEW_DIRECTIONS_DIAG C |
| clang-cl 編譯 CPU source | A | +3.15%（CI −3.3～+9.6）；CPU 22.01→20.00 ms/w；tokens/window −3.17%，原因不明 | **未確認** | `untested5-20261031/s2-clang/` |
| CPU affinity（all／auto／P-cores） | A | all 最快 | 已採用 all | 早期任務 |
| pool spin（MISS_OVERLAP_SPIN，S2K） | A | +8.49%（8 輪） | **已部署** | S2K_PROMOTION_CONFIRM |
| timer resolution（timeBeginPeriod） | A | −1.5～−2.6% | NO_GO | TIMER_RES |

### 4.2 SSD／RAM 快取與預取

| 方向 | 類 | 結果 | 狀態 | 證據 |
|---|---|---|---|---|
| MISS_OVERLAP（先算常駐、再補讀 SSD） | A | 含在 S2K 裡 | **已部署** | MISS_OVERLAP |
| 分塊完成通知（PATCH4） | A | −0.3～−1.4% | NO_GO | NEXT4 PATCH4 |
| COLD_OVERLAP | A | 無法重現 | NO_GO | ledger 10/20 |
| RAM LRU／stage LRU 變體 | A | +2.1% 中位數 | NO_GO | LUNA-20261010-014、ram-policy-sim |
| 每層 RAM quota（離線） | A | held-out SSD bytes −14%，未達 25% | NO_GO | RAM_QUOTA_OFFLINE |
| ARC、LRU-2、TinyLFU（模擬） | A | 最多約 −20% reads（冷軌跡，不可直接換算） | 部分 | ram-policy-sim-20261018 |
| 下一層路由預取 | A | 多讀 4.83 倍，提前量不足 | NO_GO | ROUTE_PREDICT_DIAG |
| GPU-only 跨層預取（Fate 類） | A | 變慢 | NO_GO | vram-prefetch-20261013 |
| 訓練式 pre-attention predictor 預取（PAP） | A | 慢約 17%／9% | NO_GO | pap-live-20261015 |
| SP-MoE／MTP 引導預取 | A | 上面幾項已涵蓋大部分前提；只剩「用 token／MTP 資訊預測淺層路由」沒測，上限只救 SSD join，估計 +2～4% | 使用者暫不做 | 本頁第 3 節 |
| unmapped direct read／first-shard shadow | A | 路徑錯誤，未測速 | 未完成 | FIRST_SHARD_DIRECT_SHADOW |
| 無損壓縮 expert（XPRESS／zlib／LZMA） | A | 只省 1.2～1.6% | NO_GO | LOSSLESS_RAM_SCREEN |
| IO arrival bound | A | 不改工作量時受串流限制 | NO_GO | IO_ARRIVAL_BOUND |
| DirectStorage／IOCP | A | 屬已暫停的 SSD 家族 | 未做 | SPEED_PRIOR_ART_SEARCH |
| large pages（SeLockMemoryPrivilege） | A | 帳號沒有權限；改權限要使用者決定 | 未測 | untested5 S1 |

### 4.3 GPU 與 VRAM 配置

| 方向 | 類 | 結果 | 狀態 | 證據 |
|---|---|---|---|---|
| PARTIAL_PIN（PCIe 路徑） | A | 8 輪 −0.5% | NO_GO | PINAA_CONFIRM |
| PCIe balance（上游 04be241a5） | A | GPU-reach +1.0～1.4 ms | NO_GO，家族結案 | PCIE_BALANCE_PORT |
| adapt-async | A | +1.28%，雜訊內 | NO_GO | PINAA_CONFIRM |
| GPU kernel 開關組合（6 旗標） | A | +0.61%，GPU 段沒變 | NO_GO | GPU6_BUNDLE_AB |
| GPU exact bundle（含 DF_QB_Q4 等） | — | 輸出壞掉 | BROKEN | GPU_EXACT_BUNDLE |
| spec-split（CPU/GPU 重疊） | A | −1.34% | NO_GO | SPEC_SPLIT |
| MTP draft vocab 縮小（V64／V32） | A | −1.1%／−2.5%；省下的 VRAM 沒有變成 slot | NO_GO | `untested5-20261031/s1-vram-vocab/` |
| MTP experts 只留熱門 N 個在 VRAM | A | 估計淨省約 0.3 ms/w，未達 0.6 門檻 | NO_GO | `untested5-20261031/s3-mtp-experts/` |
| VRAM 依頻率／成本排序 | A | 約 −2.7～−3.6% CPU 工作，約 +1% | NO_GO | VRAM_MARGINAL_SIM |
| GPU resident expert 融合／weight-major mega-kernel（MonoMoE 類） | A | 不在關鍵路徑：GPU 每 window 有 16.3 ms 在自旋等 CPU（wait_flag_ge），VRAM 命中的 expert kernel 和 CPU pool 同時進行，CPU 比較慢，所以加速 GPU expert kernel 幾乎不會縮短 window | 不做 | GPU_KERNEL_BW_DIAG B''（10/30） |
| per-slot vs dedup（每 token 分開算 vs 合併同一 expert） | A | CPU 端就是 `STRATA_IQ_MT_MIN` 這個門檻，已測 MT1（+4.26%，已部署）與 NT1_EXT（雜訊內）；source 註解：多 token kernel 在 3 token 快 2.0～2.4 倍。GPU 端同上，不在關鍵路徑 | 已涵蓋 | IQ3S_MT1_AB、NT1_EXT_TYPES |
| `--kv-grow`（彈性 KV） | A | 需要拿掉 `--kv-resident 20480` 才能開；KV 每 cell 約 6.7 KB（q4_0），現在 VRAM 裡的 KV 只有約 134 MiB，短對話最多省約 80 MiB（約 +0.3%）；6 萬 token 以上的長對話會長到約 420 MiB，反而讓出 slot | 不做（未實測，source＋log 估算） | 10/31 評估 |
| 換作業系統（Linux） | — | 使用者決定先不考慮 | 不做 | — |

### 4.4 Speculative decoding（MTP）

| 方向 | 類 | 結果 | 狀態 | 證據 |
|---|---|---|---|---|
| MTP depth 4 | A | −6.04% | NO_GO | mtp-depth-20261014 |
| 動態 depth／信心門檻 | A | −2.40% | NO_GO | mtp-options-20261014 |
| MTP PR #1934 | A | 未過 3% | NO_GO | mtp-pr1934-ab-20261015 |
| tree verification／OPT-Tree 類 | A | Top-2 rescue 0/41，verify 成本陡增 | 不做 | mtp-options、SPEED_PRIOR_ART_SEARCH |
| suffix／lookup chain | A | +1.59%，不穩 | NO_GO | ledger |
| 依「預期接受 token ÷ 成本」決定驗證長度（EVICT／SpecFit／EcoSpec 類） | A | 10/14 已實作：用實測 T1/T2/T3 成本 26.4/37.0/53.3 ms，取 (1+q1+q1·q2)/cost 最大的長度，結果 −2.40%（剪掉的窗口損失了本來會被接受的 token）。若改用「每個 window 預測的 expert 增量成本」，需要先預測下一個 token 的路由，而這類預測實測很弱（precision 37%／recall 25%） | NO_GO | mtp-options-20261014（dynamic gate） |

### 4.5 會改變輸出的路由（B 類，僅供參考）

| 方向 | 結果 | 狀態 | 證據 |
|---|---|---|---|
| ROUTE_PRIOR 0.5／1.0／1.5 | +21.9%／+39.7%／+57.9%（3 輪；CPU 22.3→6.2 ms/w） | 品質測試暫停；上游 0.2.8 因長對話重複而撤回 1.5 | `untested5-20261031/s4-route-quality/` |
| ROUTE_RESIDENT 1.0／2.0 | +4.1%／+1.7%，雜訊內 | NO_GO | 同上 |
| ROUTE_BIAS（舊候選 patch） | +13.6～+39.3% | 品質未評估 | ledger 10/20 |
| GATE_SKIP | tau ≥ 0.075 才有效（+16.9～+41.3%） | 品質未評估 | ledger 10/20 |

### 4.6 外部搜尋（已做過，不要重查同一批）

- 10/20 literature-scan（Fate、DoMoE、HOBBIT、ReMoE、CommitMoE、FloE 等）。
- 10/30 SPEED_PRIOR_ART_SEARCH、UPSTREAM_FORK_SEARCH（含 Basalt、Lamina、Strata3060、strata-4gpu）、CPU_KERNEL_SEARCH、OVERLAP_NARROW_SEARCH。
- 結論都是：沒有找到同條件下、證據能單獨接近 +10% 的新 A 類方向。

## 5. 尚未完成、可以接手的項目

1. clang-cl 的 10 輪確認，並查清 tokens/window 為何下降 3%（A 類）。
2. ROUTE_PRIOR 1.0／1.5 的品質測試（B 類；設計見 `untested5-20261031/s4-route-quality/BRIEF.md`，需停 API 約 4 小時）。
3. large pages：需要使用者決定是否改帳號權限。

## 6. 常見誤讀（請避免）

- 「pre-attention 預測 72.2% recall」：72.2% 是 10/13 一筆 live 請求的 GPU expert hit rate，不是預測器的 recall。
- 「fork 仍用 `run_phase(5)` 接 `run_phase(6)`」：那是 GitHub main 的舊碼；實際部署版本已是 per-expert pipeline。
- 「把 CPU expert 移到 GPU 就省時間」：在這台機器上，PCIe 路徑每個 expert 的 GPU 成本是 CPU 的 2～3 倍。
- 「加速 GPU 上的 expert kernel」：GPU 大部分時間在等 CPU，這些 kernel 不在關鍵路徑上。關鍵路徑是 CPU expert pool，以及 GPU 每層開頭的 dense 段（attention、router、dense mmvq），那段 CPU 必須等。
