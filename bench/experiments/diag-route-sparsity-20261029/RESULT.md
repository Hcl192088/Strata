# ROUTE_PREDICT_DIAG（A）＋ DOWN_SPARSITY_DIAG（C）結果

任務：LUNA-20261012-027 continuation，使用者授權（「都做」）。一個 DIAG build、一次 run；無 push、無 GitHub、無 live config／binary 改動、無動遠端 main。

## 一、結論與 ledger 判定

| 項目 | 數字 | ledger 判定 |
|---|---|---|
| A 路由預測（top-10，W_router[L+1]·x_L） | SSD miss byte recall **66.3%**（≥60% 過關）；但 extra 71.9 MB/w 是 rescued 14.9 MB/w 的 **4.83 倍**（上限 2 倍，未過）；lead time 中位數 0.58 ms | **未達「值得實作預取」**（條件是 recall ≥60% 且 extra ≤2×，兩者要同時成立）。recall 也不 <40%，所以嚴格來說落在 ledger 兩個判定區之間；我的判讀是**偏放棄**（理由見第四節），這是判讀不是 ledger 條文 |
| C 下投影稀疏（h=silu(g)·u） | 門檻 5% of max：**51.9% 的 h 元素**低於它，這些元素占 **3.3% L2 能量**（逐 call 平均 2.6%）；1% 門檻只有 18.2%（能量 0.1%）；10% 門檻 72.1% 但能量 11.5% | **剛好過線**：「≥50% 神經元且能量 <5%」只在 5% 這一檔成立（51.9% 對 50% 門檻，邊際很小）。判定：**值得評估 neuron-major 重排**，但有三個重要保留（第五節） |

## 二、DIAG patch 與 build

- 來源：tag `native-pipe-generic-20261029`（commit f520bc5e9d31c93caeb296b059e3a3eaa16e493f）→ 新 worktree `C:\Users\User\Strata-Adrian-control\runs\diag-route-sparsity-20261029\source`，branch `diag-route-sparsity-20261029`，未 commit。diff 4 檔（+239／-2），`diag.patch` SHA256 `B54104CD410D93C0F2D5AB6FE0B2C2A3F537BEAAC119D98AD4058B4ABCD3646A`（本機 raw\diag.patch）。
- build：同 `native-pipe-deploy-prep-20261029\build.cmd` 的旗標（NMake Release、CUDA arch 89、`-j 2`），新 build dir `...\diag-route-sparsity-20261029\build`；build 退出碼 0（約 4 分鐘，大多數 object 已編過）。**DIAG binary SHA256 `B2CC444DA3F14DF40AD4ABD20D3C1D2C510EF25B115CCB330AE67AEC2A29771D`**（52,478,976 bytes），與 live（A1E6…91AD8）不同，符合預期。
- 全部 DIAG 程式都在 env 之後，沒設 env 就完全不執行：
  - `STRATA_DIAG_ROUTE_DUMP=<檔>`（`src/core/expert_source.cpp`，`expert_pool_dispatch_multi` 進入點）：每次 verify window 的每個（層、token 組）pool call 寫一筆 CALL record：標頭 40 bytes（idx、layer、n_tok、k、H、n_expert、進入時間微秒）＋ routed ids（router rank 序）＋該層 512 個 expert 此刻所在的 tier（0 VRAM／1 RAM 複本／2 SSD／3 stage buffer）＋ x_f（fp32，就是這層 router 乘的那個 `mixed_` 向量；dispatch 的 `xm` 與 router 輸入是同一塊緩衝）；call 回傳時再寫 END record（離開時間）。上限 `STRATA_DIAG_ROUTE_DUMP_CAP_GB`（預設 14）。新增 `FileExpertSource::diag_tier_map`（持 stage_mu_ 的唯讀查詢，不 claim、不讀檔）。
  - `STRATA_DIAG_H_SPARSITY=<json>`（`src/kernels/cpu/pool.cpp`）：在 native 路徑把 h 量化成 down 的輸入之前（pipe 的 GU 完成處與非 pipe 的 phase 5→6 之間兩處），對每個（expert, token）call 累計：|h| 低於 1/2/5/10/20% of max|h| 的比例、這些元素的 L2 能量占比、同時 ≥50% 元素且能量 <5%／<10% 的 call 數；每層一組，背景執行緒每秒原子寫出 JSON。宣告在 `expert_layout.hpp`，層索引與型別由 dispatch 在每層設定。
- 沒做的驗證：沒有拿 DIAG binary 在「不設 env」下與 live binary 逐 token 比對輸出（設計上不改計算，沒設 env 時只多一個 static bool 判斷）。

## 三、這次 run

- 排程 `Strata-Diag-Route-Sparsity-20261029`，detached controller（沿用 gpu-screen 的 stop_api／finally restore_api／final_verify 型態）。engine 設定＝live config 複本，只換 exe／cwd／log 並加兩個 DIAG env（config-audit 斷言：除授權差異外與 live config 逐項相同）；strict capacity 通過（slots 3153／RAM 20.00 GiB／locked 20479），engine AboveNormal；`STRATA_NATIVE_PIPE=1`、`STRATA_IQ3S_MT1=1`、tail skip 預設 7 開啟。
- Hermes p01..p10，max_tokens 512，greedy。10 題全 OK：輸出 token 78／41／90／163／**512**／94／89／195／159／299＝**1720**（只有 p05 打滿 512，其餘模型自己停）；總計 **946 個 verify window**（約 1.82 token／window，每個 window 恰好 48 個 call，沒有 token 分組）。decode 33.8–50.8 tok/s（含 DIAG 開銷，不是速度量測）。
- 時間線（遠端本地時間）：15:22:24 停 API → 15:22:58 engine ready → 15:25:18 p10 結束 → 15:25:24 開始 restore → 15:25:46 API 恢復。API 停機約 3.4 分鐘。
- 原始 dump：`C:\Users\User\Strata-Adrian-control\runs\diag-route-sparsity-20261029\out\block-00-DIAG-r1\route.bin`，1,013,165,176 bytes，SHA256 `8B66657DA22DBAFF8E6BE1D76E2C332135E0D178543B7E3CA21843DB6B1F6601`（未下載，留在遠端）；`hsparse.json` SHA256 `8E377A174E9DAE8B5FCE16491E36434950BD0A61FB60FEF2361E0EDD67C922A3`。遠端剩餘空間約 66.5 GB。
- 請求時間區間由 harness 包裝記錄（request-times.json），946 個 window 全部落在請求區間內（0 個在外）。

## 四、A：路由預測結果

方法：離線（遠端 venv Python＋numpy）從 GGUF 讀 48 層 `blk.N.ffn_gate_inp.weight`（BF16，2560×512），對每個 window、每層 L 用 `x_L @ W[L+1].T` 取每 token top-K，再對 token 取聯集當預測集合，對照 L+1 層實際 routed ids 聯集。指標與 SSD_JOIN_BOUND 同定義：precision／recall 在「distinct routed 聯集」上；SSD miss＝L+1 層呼叫進入時 tier=2（在 SSD）的 expert，扣掉 tail skip（所有 token 都只在 rank≥7 路由的）；預取只取「預測集合裡 tier=2」的 expert；extra＝預取了但 L+1 層沒用到；bytes 用 native_experts.txt 每層 blob 大小。

**正確性檢查**：同一份 x_L 用該層自己的 router 重算 top-10，與引擎實際 routed ids 完全相同的 token-layer 占 **99.42%**（expert 層級 99.81%，96,048 筆）。表示 dump 的 x 就是 router 輸入，離線 router 也對。

**tier 分布（每 window，layer 1..47 的 routed 聯集）**：VRAM 357.1、RAM 400.0、stage 0、SSD 25.26（其中 tail skip 跳過 13.05，實際要讀 12.21）。交叉核對：重建的 SSD 讀取 12.21 expert／window × 946 ≈ 11,548 blobs，引擎 `m_file_blobs` 合計 10,972（重建高 5.3%；MB／w 22.44 對引擎 21.35）。

| 預測法 | union precision | union recall | SSD miss byte recall | rescued MB/w | extra MB/w | extra／rescued | 若 rescued 全換成 issue_wait（0.334 ms/MB，上限）ms/w |
|---|---:|---:|---:|---:|---:|---:|---:|
| top-4 | 86.4% | 36.2% | 30.5% | 6.85 | 13.50 | 1.97 | 2.29 |
| top-6 | 81.0% | 49.9% | 45.6% | 10.23 | 26.97 | 2.64 | 3.42 |
| top-8 | 75.0% | 60.7% | 58.0% | 13.01 | 46.30 | 3.56 | 4.35 |
| **top-10** | **68.8%** | **68.8%** | **66.3%** | **14.88** | **71.87** | **4.83** | **4.97** |
| top-12 | 62.8% | 74.7% | 73.3% | 16.45 | 102.52 | 6.23 | 5.50 |
| top-16 | 52.5% | 82.1% | 80.8% | 18.12 | 177.80 | 9.81 | 6.06 |
| lag-2（x_L 預測 L+2，top-10） | — | — | 53.6% | 11.88 | 78.65 | 6.62 | 3.97 |
| 只取預測機率 ≥0.02 的 SSD 候選 | — | — | 12.3% | 2.77 | 4.32 | 1.56 | 0.92 |
| 每層最可能的 1／2／3 個 SSD 候選 | — | — | 38.5%／54.8%／64.2% | 8.63／12.30／14.41 | 73.3／151.6／231.4 | 8.5／12.3／16.1 | 2.88／4.11／4.82 |

- 全部變體裡，**沒有任何一個同時達到 byte recall ≥60% 與 extra ≤2×rescued**：要 ≥60% 至少需要 top-10（extra 4.8 倍）；extra ≤2 倍的最大 recall 約 30%（top-4）。後三列（機率門檻、最佳 M 個、lag-2）是同一份資料上事後掃出來的，屬 in-sample 探索，只用來看有沒有更好的曲線，沒有更好的。
- 每請求穩定：top-10 union precision 67.1–71.2%、recall 67.0–71.3%、SSD byte recall 60.9–75.7%（p01..p10 逐題見 route-summary.json）。逐層 top-10 recall 中位數 70.4%（最低 40.0%、最高 79.3%）。
- **lead time（x_L 在主機可用 → L+1 層 dispatch 開始）**：n=44,462 個層對；p10／p50／p90／平均＝0.32／**0.58**／1.32／0.75 ms。只看 L+1 層真的有 SSD miss 的 7,493 個層對：0.44／**1.00**／2.09／1.19 ms；其中間隔 ≥1 ms 占 50%、≥2 ms 占 12%、≥3 ms 占 4%。層 L 本身的 dispatch 耗時中位數 0.34 ms（p90 1.03）。對照：這些有 miss 的層平均約 1.5 個 SSD expert（約 2.8 MB），以 Hermes 實測 0.334 ms/MB 要 ~0.9 ms 才讀完，另需 router 點積（512×2560 BF16，估 0.1–0.3 ms，**未實測**）與執行緒喚醒。也就是一層前瞻能用的時間，大約一半的有 miss 層連自己的讀取時間都不夠。x_L 是 GPU router 之後經 doorbell 到主機，沒有更早的來源（要更早必須從 GPU 另外複製）。
- 判讀：recall 66% 看似夠，但 SSD expert 本來就是冷門（每層平均只有 0.26 個），預測 top-10 裡總有約 1 個/層落在 SSD，而實際用到的很少，預取精度（rescued／預取）只有 17%；預取 86.7 MB/w 要換回 14.9 MB/w，I/O 總量會是現在的 4 倍，且上限收益 4.97 ms/w（<join 6.09 ms/w，且那還是不計 extra 成本與 lead time 的樂觀值）。所以雖然 ledger 條文沒有覆蓋「recall 過、extra 不過」這個組合，我建議**不實作**。

## 五、C：down 稀疏結果

母體：CPU 端 native 路徑算的（expert, token）call，共 **383,024** 次（≈405／window，對應 RAM＋SSD tier 的 expert；VRAM 裡 GPU 算的 expert 沒有納入，它們的 h 分布可能不同）。FF=640，zero-h call 0 次。48 層全覆蓋。

| 門檻（相對該 call 的 max|h|） | 低於門檻的元素比例（逐 call 平均／全體合併） | 這些元素的 L2 能量占比（逐 call 平均／合併） | 同時 ≥50% 元素且能量 <5% 的 call 占比 | 同時 ≥50% 且能量 <10% 的 call 占比 |
|---|---|---|---:|---:|
| 1% | 18.2%／18.2% | 0.1%／0.1% | 1.3% | 1.3% |
| 2% | 29.6%／29.6% | 0.3%／0.4% | 5.9% | 5.9% |
| **5%** | **51.9%／51.9%** | **2.6%／3.3%** | **37.1%** | 47.9% |
| 10% | 72.1%／72.1% | 10.4%／11.5% | 16.3% | 52.3% |
| 20% | 89.0%／89.0% | 30.4%／29.9% | 0.1% | 1.8% |

依型別（gate-up／down，各型別的 5% 門檻平均元素比例／平均能量）：IQ2_XXS/IQ4_NL 46.5%／2.2%（1 層）；IQ2_XXS/Q2_0 54.2%／3.0%（8 層）；IQ2_XS/IQ4_NL **65.4%／4.3%**（4 層，最稀疏）；IQ2_XS/Q2_0 51.4%／2.5%（6 層）；IQ3_XXS/IQ4_NL 47.7%／2.2%（3 層）；IQ3_XXS/Q2_0 50.7%／2.8%（3 層）；IQ3_S/IQ4_NL 49.0%／2.1%（6 層）；IQ3_S/Q2_0 50.7%／2.3%（7 層）；IQ2_S/IQ4_NL 50.7%／2.4%（4 層）；IQ2_S/Q2_0 49.2%／2.2%（6 層）。各型別都落在 46–65% 之間，沒有哪一型明顯不同（逐層與逐型別完整表在 h-summary.json）。

判定（ledger：≥50% 神經元且能量 <5% → 值得評估 neuron-major 重排）：**成立，邊際很小**，只在 5% 門檻成立（51.9%、能量 3.3%）。保留事項：
1. 這是「動態」稀疏（每個 token、每個 expert 的 h 各自不同），不是固定的冷神經元；逐 call 來看，同時 ≥50% 元素且能量 <5% 的只有 37.1%。要吃到收益，down 權重必須改成 neuron-major（每個 FF 神經元一欄連續），執行時依當下 h 跳過小的欄；現行 down 是以 32／64 元素為一個量化區塊沿 FF 排列，直接跳區塊幾乎不可能（元素比例 ~52% 不集中）。
2. 5% 門檻丟掉 3.3% 能量，相當於 h 的相對 L2 誤差約 √0.033≈18%，**會改變輸出**（非 exact）；若要輸出近乎不變只能用 1%（能省 18% 的 down 元素，能量損失 0.1%，相對誤差約 3%），這一檔過不了 50%。
3. 只能省 down 投影這一段（gate／up 仍要全算）；以 expert 位元組粗估，down 約占三分之一，5% 門檻最多省 ~17% 的 expert 讀取量，且前提是 neuron-major 的 gather 沒有額外成本。這個估計未實測。
所以這個方向的實際價值遠小於 51.9% 這個數字，建議把「值得評估」理解為可做離線誤差／品質評估，而不是直接投入實作。

## 六、Live 驗證（獨立於 controller）

controller 的 final_verify 與我另外執行的 `indep_verify.py`（獨立 SSH、psutil）結果一致：唯一 strata.exe PID 27744；binary SHA256 `A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8`；config SHA256 `060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93`；優先權 AboveNormal；`/health` loaded=true；expert_slots 3153；arena 20479 MiB；`STRATA_NATIVE_PIPE=1`、`STRATA_IQ3S_MT1=1`；引擎環境與 log 都沒有 DIAG 項目；live_state idle。排程 `Strata-Task020-API` Running，`Strata-Diag-*` 兩個排程皆 Ready（未刪，供稽核）。process gate：停 API 前、停後、restore 前皆乾淨；controller 內建的「sshd 底下的 python 視為良性」容忍規則沒有被觸發（campaign.json 無 benign_seen）。

## 七、沒做的事與限制

- 只有一次 run、946 個 window、1720 個 token、10 題 Hermes；其中 p05（512 token）占 32% 的 window，沒有多次重複，也沒有 A/A。
- A 只涵蓋主 verify 路徑（`expert_pool_dispatch_multi`）；MTP draft 路徑的 router／expert 沒有 dump。prefill 不經過這條路徑，也沒有納入。
- tier 是 call 進入時刻的快照；L 層時刻（預取真正會發生的時間）的 tier 沒有記錄；adaptive swap 若在兩者之間落地，會有誤差。stage buffer hit（tier 3）在這次資料中為 0。
- SSD 重建比引擎計數高 5.3%（原因未查）；extra 以整個 blob 計，未含 4 KiB 對齊／合併讀放大，也沒有 cache pollution。
- 0.334 ms/MB 取自 SSD_JOIN_BOUND 的 Hermes issue_wait 比率（含 OS 開銷、與 CPU 重疊），僅作上限換算，不是 SSD 頻寬；預測器本身的 CPU 時間只是估計。
- C 沒有記錄逐神經元分布（是否固定那幾個神經元小）、也沒有區塊層級（32／64 元素）稀疏度、也沒有 VRAM 內（GPU 算的）expert 的 h；沒有做近似輸出的品質評估。
- 未驗證 DIAG binary 在不設 env 時與 live 輸出逐 token 相同。
- 遠端未清理：worktree、build、1 GB dump 都保留（約 1 GB dump＋build 目錄）。

## 八、原始檔位置

- 遠端 run root：`C:\Users\User\Strata-Adrian-control\runs\diag-route-sparsity-20261029`（source worktree、build、controller.py、harness、out\block-00-DIAG-r1\{route.bin,hsparse.json,engine.log,...}、route-analysis.json 等）。
- 本機：`D:\strata\state\diag-route-sparsity-20261029\raw\`（campaign.json、controller.log、rows.json、request-times.json、final_verify.json、independent_verify.json、config-audit.json、diag.patch、route-analysis.json、route-summary.json、h-summary.json、block\{engine.log,hsparse.json,meta.json,tail-p*.log,...}、分析腳本 analyze_route.py／summarize_route.py／summarize_h.py／gguf_min.py）。
