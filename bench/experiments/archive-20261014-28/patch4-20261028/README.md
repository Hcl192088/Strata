# patch4：STRATA_MISS_CHUNK（分塊完成，建立在 patch3 之上）

資料夾內容：`orig\`（= patch3 套用後的原始碼）、`new\`（orig + patch4）、`patch4.py`（在 `new\` 目錄下執行，與 patch3.py 同風格：精確比對 `once()`、保留 CRLF、assert）、`patch4.diff`（orig 與 new 的 unified diff，共約 190 行）。

## 開關
- `STRATA_MISS_OVERLAP=1`：patch3，不變。
- `STRATA_MISS_CHUNK=N`：只在 MISS_OVERLAP（或 CHECK）啟用時有效；N 為每塊 expert 數（上限 128）。0 或未設 = 與 patch3 完全相同的程式路徑（兩段式，整批 join）。啟用時第一次進入 dispatch 會在 stderr 印 `MISS_OVERLAP chunked completion on: STRATA_MISS_CHUNK=N experts per chunk`。
- `STRATA_MISS_OVERLAP_SPIN_US`、`STRATA_MISS_OVERLAP_CHECK=1`：不變。

## 設計
1. helper 執行緒收到的 batch（`split_todo_`，順序 = claim 順序，也就是 CPU 消費順序）改由新函式 `prefetch_split_run_chunked(N, landed)` 讀：每 N 個 expert 一塊，呼叫既有 `fill_many`（塊內仍是 overlapped direct read 與 ≤32 MiB 合併；N>16 時 `fill_many` 內部依舊每 16 個一批、最多 4 條執行緒）。`fill_many` 返回時該塊每個 blob 的 `publish_stage` 都已執行，之後才 `landed.store(++c, release)`。
2. dispatch 的 pass 由 2 個改成「pass 0 = 不需讀取的 expert；pass 1..K = 第 p 塊的 expert」（K = ceil(待讀數/N)）。每個 pass 開頭：先把前面各 pass 累積的 job 交給 pool 執行，再 `wait_chunk(p)`（acquire 自旋，與 patch3 的 join 同風格，120 秒保險 abort）等第 p 塊落地，然後才建立這一塊的 job。所以 worker 在算上一批時，helper 同時讀下一塊；等待的只剩「上一批算完後下一塊還沒到」的空檔。
3. 每個 expert 仍是整個 window 內一個 job（同一 expert 的所有 token 在同一個 pass 建出），寫入的 row 與 patch3 / 原版相同，job 內部運算沒變，因此輸出應與原版位元相同；只改變各 job 開始的時間與 pool 批次的切法（patch3 已經是切成兩批）。
4. CHECK 模式：既有的 `STRATA_MISS_OVERLAP_CHECK` 區塊在所有 pass 結束後才執行，用 `d.job_of` 與 `d.jobs_multi` 重算全部 CPU rows 並 memcmp，所以自動涵蓋分塊路徑（未改動該區塊）。
5. 計數（沿用 patch3 的 `MISS_OVERLAP progress` 行，每 64 次 split 印一次）：新增 `chunks_published=`（helper 累計已發佈的塊數）與 `chunk_wait_ms=`（dispatch 在 `wait_chunk` 上自旋等待的總毫秒）。分塊模式下 `join_wait_ms` 不再累加（因為不 join 整批），`compute_while_read_ms` 仍表示前幾批 pool 運算的時間。`ms_jobs`/`ms_run` 的位移同 patch3，但改為累加每個 pass 的（運算+等待）時間。

## 執行緒安全：已驗證 vs 未驗證
已從本機原始碼確認（orig\src\core\expert_source.cpp）：
- `publish_stage` 在 `stage_mu_` 內清 `stage_busy_[v]`（失敗時 erase `stage_of_`），鎖外 `stage_cv_.notify_all()`；`staged_blob` 對仍 busy 的 blob 以 `stage_cv_` 等待、並檢查 key 是否仍相同。`claim_stage` 只在 `stage_mu_` 下呼叫。所以 helper 發佈與主執行緒 `blob()` 同時進行是這份程式碼原本就支援的用法（`blob()` 對「另一執行緒正在填」的 blob 本來就會等）。
- 主執行緒的 `wait_chunk` 只用 helper 的 release 計數，不依賴 stage 鎖；之後 `blob()` 取得的是已發佈的 blob，會在鎖內直接返回（不等待）。
- 被 `claim_stage` 重用的條件包含 `!stage_busy_` 且已過期（`kStageAge`/`kStageSeq`=256）。某塊發佈後、其 job 建立前，理論上可被別的 claim 回收；但 dispatch 期間主執行緒不會再 claim 新 key（後續 pass 的 key 都已在 `stage_of_`，`claim_stage` 命中時會更新 epoch/seq 保護它），而且 patch3 的 pass 1 同樣有「發佈到使用之間」的視窗，所以沒有比 patch3 更危險。
- helper 讀取時只持有裸指標 `Fill.dst`（來自 `stage_buf_[v].get()`），vector 重新配置不影響該指標。

未驗證（本機只有這兩個檔案的快照，沒有編譯器，也不得 SSH/建置）：
- **整份修改沒有編譯過，也沒有跑過。** 需要在遠端建置並先跑 `STRATA_MISS_OVERLAP_CHECK=1 STRATA_MISS_CHUNK=N` 驗證 `check_mismatch_rows=0`。
- `read_direct` 內 thread_local scratch 與別處是否共用、`fill_many` 在分塊後每塊都要重新排隊的額外 overlapped I/O 啟動成本，是否讓整體讀取時間變長（塊越小，32 MiB 合併的效果越差），只能靠實測。建議先試 N = 4、8、16。
- 若 `fill_many` 的失敗備援（`fill_stage`）觸發，仍會 `publish_stage`，不會卡住計數；但此路徑未實測。
- 預期效益（回收 join_wait 約 1.5~2.5 ms/window）只是推估，沒有數據支持。

## 套用方式
在 `patch4-20261028\new\` 內執行 `python ..\patch4.py`（需先把 `orig\` 複製成 `new\`，即目前狀態的反向；若要在遠端 source 上套用，需先是 patch3 的結果）。
