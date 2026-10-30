# 上游 Strata 0.2.5 / 0.2.7 與我方 patch3、ROUTE_PRIOR 比對（唯讀，2026-10-28）

讀取方式：只用 curl/WebFetch 抓個別檔案（raw.githubusercontent.com、api.github.com 的 tree/commit/release），沒有 clone、沒有 SSH、沒有跑任何 benchmark。抓下來的檔案放在 scratchpad `...\scratchpad\up\`，不在專案內。

上游 tag commit：v0.2.4 = 96ca4383c，v0.2.5 = fa663fabc，v0.2.7 = 5e8a4cca7。
下文行號若未註明，上游一律指 v0.2.5（Qwen 的 `src/core/expert_source.cpp` 在 v0.2.4 與 v0.2.5 逐位元相同，6388 行；v0.2.7 為 6429 行，行號約 +41）。

---

## 0. 最重要的發現（先看這裡）

1. **0.2.5 release note 那一句「CPU starts on the experts it already has while the rest are read from the SSD」是寫在「DeepSeek is faster on many PCs」小節底下，實作在 DeepSeek 引擎（`src/dsv41/`，開關 `DS4_MISS_SPLIT`），不是 Qwen 引擎。** RTX 3060 +11~15%、RTX 5070 +13.5% 的數字是 DeepSeek-V4.1-Flash 的，不是我們的 Qwen3.8-Flash-Next。同一小節的其他項目也都是 DeepSeek（RAM store、4096 chunk）。
2. **Qwen 引擎本來就有同一個構想，叫 `STRATA_COLD_OVERLAP`（commit 註解代號 "149-cold"），在 v0.2.4 就已存在（v0.2.4 與 v0.2.5 的 expert_source.cpp 完全相同），不是 0.2.5 新增。** 它在 Windows 預設是關的：`d.cold_mode = cold_env >= 0 ? cold_env : (linux_file_defaults() ? 4 : 0)`（expert_source.cpp:4817 附近，v0.2.7 為 4853）。所以 Windows 上的 Qwen 使用者拿不到這個優化。
3. 我方 overnight-20261020.md 與 EXPERIMENT_LEDGER 已經測過 `COLD_OVERLAP=1`（在 v0.2.0-beta 上）：campaign A +3.7%、campaign C -0.7%，判定未重現。我方 0.1.42 基底的 expert_source.cpp（orig，4945 行）完全沒有 COLD_OVERLAP / prefetch_begin / wait_landed（grep 0 筆）。所以 patch3 是在沒有這套機制的基底上重做同一件事，+6.5%（spin 2000）其實已高於上游 Qwen 版在 Windows 上的實測。
4. ROUTE_PRIOR：公式與我方相同，上游 1.5 = 我方 1.5，同一尺度（見第 3 節）。

---

## 1. 上游實作怎麼運作

### 1A. DeepSeek 引擎（0.2.5 的實際內容，`DS4_MISS_SPLIT`，預設開）

檔案（v0.2.5）：
- `src/dsv41/ds4_store.hpp`：`begin()` 151 行起、`loaded()` 177、`wait_slots()` 179、`start_fill()` 414。
- `src/dsv41/ds4_pool.hpp`：`IoQueue` 137–232。
- `src/dsv41/ds4_model.cu`：`StoreHold` 5790、`cpu_experts()` 5829–5868 起（DS4_MISS_SPLIT 在 5834）。
- v0.2.4 → v0.2.5 對 ds4_store.hpp 的改動就是把原本一個阻塞式 `ensure()` 拆成 `begin()`（只找 slot、啟動讀取，不等）＋`wait_slots(sl, ok, a, b)`（可只等第 a..b 個）＋`loaded(s)`（無鎖輪詢）。

運作方式：
- **誰發讀取**：`StoreHold` 建構時呼叫 `store->begin()`，在 `mu_` 鎖內對每個 miss expert 呼叫 `start_fill()`；`start_fill` 把一個 expert 的 3 個矩陣（gate/up/down，各約 6 MB）組成 3 個 `IoQueue::Job` 推進佇列，然後立刻返回（呼叫端不等）。
- **讀取執行緒**：專用 `IoQueue`，8 條常駐執行緒（`DS4_STORE_THREADS`，預設 8，ds4_model.cu:4627），條件變數喚醒，FIFO，一個 job = 一個矩陣的一次 `os::pread_direct`（Windows：`FILE_FLAG_NO_BUFFERING | FILE_FLAG_OVERLAPPED`，ds4_os.hpp:80–125）；page cache 已有的範圍改走 buffered `pread_par`。需求讀取（demand）的佇列 `q_` 一定先於預測讀取（`ql_`，prefetch）。
- **完成通知**：每個 slot 有 `left` 原子計數（初值 3），每個 job 完成就 `fetch_sub`；`loaded(slot)` = `left <= 0`。完成時 `done_cv_.notify_all()`。
- **CPU 取用**：`cpu_experts()` 把 entries 分成 hot（`hold.ready(e)`，已讀好或在 RAM copy）與 cold。先算 hot（一次 `cpu_experts_mx` 批次），然後迴圈：優先挑「這段時間內已 landed 的 cold expert」，沒有就依序挑第一個未完成的，`wait_expert(e)`（`wait_slots` 單一個，睡在 `wait_any(2000 us)`），**一個 expert 一次呼叫 `cpu_experts_mx`**。也就是**逐 expert 完成通知，不是整批 join**。結果位元相同（每個 entry 的 row 彼此獨立）。
- **讀取粒度**：每矩陣一個 request（約 6 MB），3 個矩陣/expert，8 條執行緒並行。**無合併成 32 MiB。**
- **順序**：`begin()` 依 ents 的出現順序啟動讀取；不做「最大優先」或依 layer 排序；只有 demand > prefetch 的優先級。
- **Windows 路徑**：同一份程式，Windows 用 overlapped direct read；不是 Linux-only。
- **開關**：`DS4_MISS_SPLIT`（預設 1，`=0` 回到舊的「全部讀完再算」）；`DS4_STORE_THREADS`（8）。條件 `ents.size() >= 2` 且 `ord == nullptr` 且格式為 MXFP4（`l.lay.fmt == gg::kFmtMXFP4`）才分流；EXL3 格式走原路。

### 1B. Qwen 引擎的 `STRATA_COLD_OVERLAP`（v0.2.4/0.2.5 就有，Windows 預設關）

檔案：`src/core/expert_source.cpp`
- `FileExpertSource::prefetch_begin` 2192–2256、`wait_landed` 2258、`prefetch_end` 2290、`publish_stage` 2014、`fill_many` 2335（原始同步版）、`read_direct` 2694（Windows 合併成 ≤32 MiB 請求，kGap=1 MiB、kMerge=32 MiB，註解說明 NTFS 對被 map 的檔案會把 unbuffered 讀取序列化）。
- 調度端 `expert_pool_dispatch_multi`：模式表 4814、主迴圈 5019 起（mode 1 的註解：「Mode 1 reads them in the background and computes the ready ones first, then each read one as it lands」）。

運作方式：
- **誰發讀取**：`prefetch_begin` 先在 `stage_mu_` 內 claim stage buffer（`claim_todo`），把 todo 放進 `async_todo_`，然後**每層新建 std::thread**（`async_th_.emplace_back(work)`；direct 路徑最多 4 條：`nt = min(4, (todo+15)/16)`；非 direct 用 `fetch_threads_`）。每條執行緒用 `async_next_.fetch_add(16)` 一次領 16 個 blob，呼叫一次 `read_direct`（overlapped 批次），讀完才對這 16 個逐一 `publish_stage`（清 `stage_busy_`、`stage_cv_.notify_all()`）。
- **決策執行緒**：`mstate[]`（0 ready / 1 reading / 2 landed / 3 computed）。第一批 = 不需讀取的 expert，立刻 `run_split_multi_native`；之後迴圈 `wait_landed()`（`stage_cv_` 條件變數，**任何一個** landed 就返回），把已 landed 的整批再丟給 pool 當第二、第三批……直到全部算完，最後 `prefetch_end()` join 執行緒。
- **粒度**：完成通知是「每 16 個 expert 一個 chunk」（chunk 讀完才一起 publish），不是逐 expert；但 chunk 內仍是合併 ≤32 MiB 的 overlapped 讀取。
- **順序**：claim 順序（ids 首次出現順序）；沒有最大優先、沒有依 layer。
- **等待機制**：純條件變數（無 spin）。
- **預設值**：`STRATA_COLD_OVERLAP` 未設 → Linux 且 GGUF in place 時 = 4（zero-copy，需要 page cache residency 查詢，Linux-only），否則 0（含 Windows）。模式 2 = 只量測；3 = overlap + zero-copy。
- 位元結果相同：註解明說「every expert keeps its own token rows… same bits in any batch order」。

---

## 2. 與我方 patch3 的逐點比較，以及對 ~3 ms/window join_wait 的影響

patch3（`miss-overlap-20261027\patch3.diff`）：
- 一條常駐 helper thread（`MissIo`，spin 後睡），`prefetch_split_run()` = 原 `fill_many(split_todo_)`，也就是**單一批次、單一次 `read_direct` 呼叫（我們說已合併成 ≤32 MiB overlapped 請求）**。
- 兩段式：pass 0 = 不需讀取的 expert 先 `run_split_multi_native`；然後 `mo_join.join()`（spin 等 helper 讀完**全部**）；pass 1 = 所有被讀的 expert 一次丟進 pool。
- 只在 `!io_pf_ && !direct_.empty()` 的 unbuffered 路徑啟用。

| # | 差異 | 上游 | patch3 | 對 join_wait 的影響 | 預期影響（我方） | 可移植性 / 工作量 |
|---|---|---|---|---|---|---|
| D1 | **完成通知粒度、分波計算** | DS4：逐 expert；Qwen：每 16 expert 一個 chunk，之後「每次 landed 就再算一批」 | 全部讀完才算被讀的 expert（一次大批） | **直接決定 join_wait**：我方 pool worker 在 ready 批算完後閒置等整個讀取結束（~3 ms）；分波後 worker 在讀取進行中持續有工作可做，理想情況只剩「最後一個 chunk 的計算尾巴」 | **最高**。理論上限：join_wait 3 ms 中能吃掉的部分 ≈ 被後續 chunk 取代的計算量（CPU segment 增加的 ~4 ms 本來就得算，只是目前排在讀取之後；分波可與讀取重疊）。實際最多回收 1.5~2.5 ms/window（因為 read 本身 3.5 ms 是下限、chunk 變小可能降低合併效率） | **可移植**。需要：(a) `fill_many` 拆成多個 chunk，每個 chunk 讀完對該批 stage 個別 publish（`publish_stage` 在我方 0.1.42 基底有？未驗證；patch3 已用 `claim_stage`/`stage_buf_`，應有）；(b) 以原子計數或 `stage_busy_` 讓決策執行緒輪詢/等待 landed；(c) dispatch 迴圈改成 N 波。約 120–200 行，集中在 expert_source.cpp。chunk 大小要折衷（上游 16；我方 miss 數/window 若只有 ~10–30，建議 4–8 個 expert 一個 chunk，仍可合併 requests） |
| D2 | **多條讀取執行緒（queue depth）** | DS4：8 條；Qwen direct：最多 4 條，各領 16 個 | 1 條 helper | 單條 helper 的一次 overlapped 批次已有深佇列，但 helper 還要做 `read_direct` 後的 memcpy（「read into aligned buffer, then copied into place」）— 這段是單執行緒串行；多條可把拷貝並行 | 中。我方量到 helper 讀 3.5 ms 但只重疊 2.4 ms，且 join 3 ms，表示 helper 起跑延遲／被 9 條 worker + host 搶核 | 中小：helper 內部再開 2 條或沿用 `fill_many` 的 4 條 thread 模式；但 `NTFS 序列化被 map 檔案` 的上游註解提醒，queue depth 超過合併後請求數沒意義 |
| D3 | **讀取順序配合計算** | 無（claim/出現順序）；DS4 有 demand>prefetch 優先 | 無 | 無直接差異；但分波後（D1）可把「對 token 數多、計算久的 expert 先讀」排前面，讓最後一波短 | 小～中（需 D1 才有意義） | 小：claim 後依「被幾個 token 選中」排序 todo。注意 `read_direct` 內部依檔案位置排序/合併，排序後合併率可能下降 |
| D4 | 執行緒生命週期 | Qwen：**每層 new std::thread**（有成本）；DS4：常駐 | 常駐 helper + spin（我方更好） | 無 | 我方已優於上游 Qwen 版 | 已有 |
| D5 | 等待機制 | 條件變數（`stage_cv_`/`done_cv_`，2 ms timeout） | spin（`_mm_pause`） | 上游沒 spin；我方 spin 在 16 執行緒 / 10 核下可能與 worker 爭核 | 我方 spin 2000 us 最佳，代表等待延遲確實敏感；沒有上游的證據支持 spin 更好 | — |
| D6 | **預設在 Windows 是否啟用** | Qwen：Windows 預設關（mode 0）；DS4：開 | 開關 | — | — | — |
| D7 | 跨層預讀（io prefetch/read-ahead） | `STRATA_IO_PREFETCH`、`IO_PF_AHEAD` 等，**Linux 預設開**（generate.cpp:5757–5790，`linux_io_defaults()`），在目前層計算時預讀後面層的預測 expert | patch3 條件 `!io_pf_`，即不與之共存 | 這是不同的、可能更大的槓桿（把讀取藏到整層計算後面，而不只是藏在同層 ready 計算後），但 Windows 預設不啟用，我方 overnight 記錄為「Linux-only zero-copy/IO prefetch 在 Windows 不生效」 | 未驗證（我方沒有上游這部分的 Windows 實測） | 大：牽涉預測來源與 stage buffer 壓力，不建議當作 patch3 的小修 |

**排序（對我方預期影響，由大到小）：D1 ＞ D2 ＞ D3（依賴 D1）＞ D7（另案）＞ D4/D5/D6（已持平或我方較好）。**

重要的誠實保留：
- 上游 DS4 的 +11~15% 是 DeepSeek 的 MXFP4 約 6 MB/矩陣、expert 很大、讀取單位大且 miss 多的情境；我方 Qwen IQ3_XXS expert 只有約 1.xMB，每 window miss 數與 chunk 效率不同，不能把 11~15% 當我們的目標。
- 上游自己的 Qwen 版（D1 同概念的 16-chunk 分波）在我方 v0.2.0-beta 的 Windows 實測只有 +3.7%/-0.7%，沒有顯示分波本身就能給大增益；patch3 的 +6.5% 已高於該結果。因此 D1 的預期是「把 patch3 從 +6.5% 再推高幾個百分點」，而非翻倍，我無法證實上限。
- 我沒有驗證：我方 0.1.42 基底有沒有 `publish_stage`/`stage_cv_`/逐 stage 發佈機制（本機只有 expert_source.cpp 快照，需看 orig 內 `claim_stage`、`stage_busy_` 的使用；patch3 有用到 `claim_stage`、`stage_buf_`，所以 stage 機制存在，但沒逐一核對 publish 的鎖/條件變數是否可被另一執行緒安全輪詢）。

Linux-only 部分：mode 3/4 的 zero-copy（`zc_roles`、page cache residency 查詢、mincore/madvise）、`linux_file_defaults()`、`io_submit`（read_direct 的 Linux 分支）、Linux 預設啟用的 IO prefetch。DS4 的 IoQueue 與 Qwen 的 Windows `read_direct`（overlapped）都是跨平台/Windows 可用。

---

## 3. ROUTE_PRIOR：公式比對與尺度結論

上游 v0.2.7（`src/kernels/cuda/route_prior.cu` 全檔 79 行；`include/strata/kernels/route_prior.hpp`；呼叫處 `src/core/verify.cpp:2113–2115`；預設值 `verify.cpp:270–295`，`include/strata/core/sm120_series.hpp:53–62`）：

- 每 token 一個 warp，512 個 expert 各 16 個值/lane。
- `s[i] = logit[e] + (res[e] >= 0 ? lambda : 0)` 作為**選擇分數**，在 **softmax 之前、原始 logit 上相加**（加法偏置，不是乘法/機率偏置）。
- top-10 以偏置後分數挑選（tie 以較小 expert id）。
- **權重**用**未偏置**的 logit 做 softmax（對 512 個），再對選中的 10 個重新正規化（與 native router 同）。
- `res_layer` = `hits_.d_res + l * n_expert`，即 **VRAM 常駐表**（d_res >= 0 才加）。**不認識 RAM tier**。
- **沒有 top-1 guard**（top-1 可被換掉）。無額外正規化。
- 只在 verify 路徑（`verify.cpp` 的 window）且 `NE == 512 && K == 10 && hits_.d_res != nullptr` 時套用。
- 預設：env 未設 → 離散 CUDA 卡且 VRAM ≤ 13 GiB 時 = **1.5**（`kRoutePriorSmallCard`），其他（HIP、整合顯卡、大卡）= 0；`STRATA_ROUTE_PRIOR=0` 關閉，其他值一律優先。我們的 RTX 4070 12 GB 會落在這個預設範圍內。
- 歷史：v0.2.7 早期候選是 2.0；2026-10-26 owner 決定降到 1.5（2.0 在 copy/code 檢查有缺陷；1.5 在 19 個任務沒有缺陷；原始碼註解：另有 61 任務的 0/1.5/2.0 檢查仍在跑，若 1.5 出缺陷則降到 1.0）。
- v0.2.4 的版本（verify.cpp:1971）是 opt-in、讀 env、預設 0，內容相同。

我方（依 overnight-20261020.md 第 12 行記載：「CURRENT-BEST source already contains the identical route_prior.cu / STRATA_ROUTE_PRIOR (verify.cpp:1380)」，VRAM-only、選擇用偏置 logit、權重為未偏置 softmax 對 10 個重新正規化、無 top-1 guard、不認識 RAM tier）。**注意：我本次沒有讀到我方 verify.cpp/route_prior.cu 原文**（本機只有 currentbest_generate.cpp 與 currentbest_expert_source.cpp 的快照，兩者都不含 ROUTE_PRIOR），所以「與上游相同」這一點是依據我方自己的 overnight 記錄，不是我親眼比對；從該記錄的描述與上游行為逐項一致。

**結論：上游 1.5 就是我方的 1.5（同一個 λ、同一個 raw-logit 加法尺度、同一個 VRAM-only 條件），不對應我方的其他值。**

與我方實測的衝突如何看：
- 我方 0.25/0.5/1.0 → decode +15.7/+30.7/+59.6%，SSD 讀取 -16/-34/-50%；上游 3060 在 1.5 只拿 +15%（story）/+37%（code），2.0 約 +35~38%。**同一 λ 下我方的收益大得多**（我方 1.0 已 +60%，上游 1.5 才 +15~37%）。合理解釋（未驗證）：我方 4070 的 VRAM 常駐比例與 baseline 命中率不同（~3153 slots、20 GiB RAM tier）、我方 Hermes 10 點 profile 與上游 story/code prompt 不同、且該偏置作用在 verify window（多 token）。這也代表同一 λ 在兩邊造成的「換掉 expert 的比例」可能差很多，**不能把上游的 1.5 直接當成我方的安全值**。
- 上游的「安全」證據其實很弱：官方 note 自己寫「Agent loops may finish slightly less often」（10 個 agent 任務 4.5 vs 5.6）、2.0 有缺陷、1.5 只有 19 任務（另 80 任務 copy/code 檢查）沒看到缺陷、仍有 61 任務檢查在進行、若出缺陷退到 1.0。他們的品質關卡是「copy/code 錯誤與 agent 通過率」，我方是小樣本並列比對，兩者量的不是同一件事，所以 1.0 在我方看起來劣化與上游 1.5 被視為可接受，並不直接矛盾。
- 我方若要比較，應用上游的品質關卡（copy/code 任務 + agent 通過率）在同一 λ（0.5、1.0、1.5）重測，而不是只看並列主觀比對。這是建議，不是已驗證結論。

---

## 4. 「shared-expert stream 在 Windows 預設關」

上游 v0.2.7 `src/core/verify.cpp:346–355` 的註解與 `sh_stream_on()`：
- shared expert 在自己的 stream 上 fork/join（`sh_fork`，record_window 裡）。在 **CUDA 預設開**（`return true`，非 HIP）；**HIP 預設關**（R9700 實測關掉 62.9 vs 開 43.4 t/s；gfx1030 RX 6800 Windows 42.5→56.4）。
- Strix Halo gfx1151：Linux 由 arch table 設 `STRATA_SH_STREAM=1`（+1.8% / +6.7%）；**Windows gfx1151 開啟反而慢**（註解寫 Qwen IQ3_S decode -6.4%），所以 table 在 Windows 不設，落到「HIP 預設關」。
- 你引用的「+6.9%」我在 v0.2.7 release body 與 verify.cpp 註解都沒找到完全一致的數字（註解是 -6.4%、+6.7%、+1.8%）；可能在 `docs/STRIX_HALO_WINDOWS.md` 或 arch table 註解，我沒讀那份文件，**無法驗證 6.9%**。
- **與我們無關**：這是 HIP / AMD Strix Halo 的議題。我們是 NVIDIA（CUDA），上游 CUDA 預設就是開。
- 我方 0.1.42 原始碼是否有該 stream：本機快照（currentbest_generate.cpp / currentbest_expert_source.cpp）grep `sh_fork`、`STRATA_SH_STREAM`、`SHARED_STREAM` 皆無；`verify.cpp` 不在本機快照內，所以**無法判定我方是否有**。上游 v0.2.4 的 verify.cpp 有 `sh_fork`（255 行註解、1929 行；註解說明由 commit cfd3b72 加入 CUDA overlap），因此 0.1.42 之後的上游版本應該都有；0.1.42 本身是否有，需要在遠端 verify.cpp 確認（本次不得 SSH）。

---

## 5. 建議的下一步（僅供決策，不含任何已執行動作）

1. 先確認遠端 `verify.cpp`/`expert_source.cpp` 內 `publish_stage`、`stage_cv_`、`stage_busy_` 的存在與線程安全（需要遠端權限，本次未做）。
2. 若要追加 patch4：把 helper 的 `fill_many` 拆成 4~8 expert 的 chunk、逐 chunk publish、dispatch 改成多波（D1）；先用現有 CHECK 模式（`STRATA_MISS_OVERLAP_CHECK`）驗證位元一致，再 A/B。預期是在 +6.5% 基礎上再加幾個百分點，上限不確定。
3. ROUTE_PRIOR 若要評估 1.0~1.5，需要與上游相同等級的品質關卡，否則結論只能維持「速度有效、品質未證實」。
