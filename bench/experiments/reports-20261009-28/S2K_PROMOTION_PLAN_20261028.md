# MISS_OVERLAP＋S2K 確認與部署計畫（草稿，2026-10-28，未執行）

狀態：DRAFT，等使用者核可。第 1 階段（確認）與第 2 階段（部署）分開授權。核可前不連遠端、不跑、不改任何 config。

## 0. 候選是什麼

- binary：`runs\miss-overlap-20261027\build\strata.exe`，SHA `385EF64EE24BDF3BD4B309264FA811901DF9256B92CE4589BAEC70B3F26B30F5`
- 來源：current-best 源碼（ram-lru-20261013\source）副本＋patch3（只改 expert_source.hpp/.cpp）。不含 10/20 的 GATE_SKIP／ROUTE_BIAS。
- 開關：`STRATA_MISS_OVERLAP=1`、`STRATA_MISS_OVERLAP_SPIN_US=2000`。不設開關時（D0）實測和 C0 差 +0.5～2%，在雜訊內。
- 輸出：MCHK 通過（6209 次 split、87,992 列、0 不一致），理論上與 current best 位元相同 → **不需要品質評估**，只需要位元檢查。
- 已有證據：兩個時段各一次，S2K 對 M +5.2%／+5.4%；S2K 對 C0 +6.5%（按輪 CI −3.0～+16.0，跨 0；逐點 CI +2.5～+11.1）。

## 1. 第 1 階段：確認實驗（約 2 小時，排夜間或使用者不用 Hermes 時）

只放兩臂，把輪數加倍，目標是讓**按輪配對的 CI 也排除 0**。

| 步驟 | 內容 | 時間 |
|---|---|---|
| 1a. MCHK | S2K 設定下加 `STRATA_MISS_OVERLAP_CHECK=1`，10 點 × 128 tokens | 約 5 分 |
| 1b. Hermes replay（greedy） | C0、S2K；**8 輪**，ABBA 交錯（輪替先後）、10 點、512 tokens、每 block 新引擎 | 16 block，約 60 分 |
| 1c. Hermes replay（production 抽樣） | C0、S2K；3 輪交錯；temperature 1.0、top_p 0.95、top_k 20、enable_thinking、max_tokens 512 | 6 block，約 25 分 |
| 1d. neuro 1024（暖機後） | C0／S2K／S2K／C0 四個 block；每個 block 同一個引擎，先丟掉 1 次暖機，再量 3 次 | 約 30 分 |

為什麼要 1c 和 1d：
- 1c：實際使用是抽樣模式，要確認收益不是 greedy 才有。
- 1d：順便回答昨天「neuro 為什麼只剩 40～42」的問題，量出穩態下的數字。

- 優先權（開跑前修訂）：佇列排程工作用 priority 2（跟 live API 一樣），每個 block 讀回引擎 PriorityClass，應為 AboveNormal；沒繼承到就在引擎啟動後對兩臂一樣設成 AboveNormal 並記錄，設不了就記錄並在 A/B 前停止。

### 判定（事前登記，跑完不改）

- **通過**要同時符合：
  1. MCHK 0 不一致，且 split_calls ≥ 20、check_rows ≥ 100。
  2. 1b 的 S2K vs C0：block 合併 tok/s 按輪配對（df=7）平均 ≥ +3%，**而且 CI 排除 0**；逐點（df=9）同方向。
  3. 1c 的平均不是負的（≥ 0%；n=3 太小，不要求顯著）。
  4. 1d 的 S2K 暖機後平均不低於 C0 超過 3%。
  5. 全部 block 狀態 OK、沒有當掉或逾時；候選的 capacity 要**嚴格**等於 3153 slots／20.00 GiB／20479 MiB（要上線，標準跟 control 一樣）。
- 1 不過 → 整個停止，回報。
- 2 的平均 ≥ +3% 但 CI 跨 0 → 不部署，回報「方向正但證據不足」，由使用者決定要不要再加輪數。
- 平均 < +3% → 判無效，MISS_OVERLAP 家族結案。

### Identity／流程閘門（照 AGENTS.md）

- 開跑前與每個 block：hostname DESKTOP-LKMLUPC、C0 SHA 366A…15E2、S2K SHA 385E…30F5、程序盤點（有未分類程序就停）。
- live API 會停；runner 用 detached 腳本，finally 一定還原 API，還原後核對 loaded、3153、SHA 366A。
- 沿用 `tools/replay_ab_20261027.py`（已有 `--pre-arm MCHK` 閘門），只新增 arms 檔，不改 harness 邏輯。
- SSH 連續失敗 > 10 分鐘就停止重試，查清是哪一端斷線後回報。
- 結果 append 到 LUNA-20261012-027 的夜間報告與 ledger。

## 2. 第 2 階段：部署（第 1 階段通過後，另外請使用者授權）

### 2a. 部署前的唯讀檢查
- 讀 live config `iq3-campaign-020\server-task020-8080-v0142.json`（SHA C805…EA18）和 `tools\start_task020_api.ps1`，確認環境變數是由 config 還是 launcher 帶進去的（10/15 審計看到 live 程序有 `STRATA_RAM_LRU=1` 等環境變數，但沒記錄來源）。
- 確認排程 `Strata-Task020-API` 的狀態，以及它指向哪個 config。

### 2b. 切換（需要明確授權：會改 live config）
- **不覆蓋原檔**：複製出新 config `server-task020-8080-v0142-s2k.json`，只改兩處：
  1. binary 路徑改成候選 build。
  2. 環境變數加 `STRATA_MISS_OVERLAP=1`、`STRATA_MISS_OVERLAP_SPIN_US=2000`。
- launcher 或排程改指新 config（看 2a 的結果，改動越少越好）。原 config、原 binary 都不動，方便回滾。
- 不改遠端 source、不改 canonical main。

### 2c. 上線後驗證
- `/health` 回 loaded；啟動 log 確認 MISS_OVERLAP 開啟、spin 2000、slots 3153／20.00 GiB／20479 MiB、binary SHA 385E。
- 用 3 個 Hermes 點做 smoke test，回應正常。
- 觀察期 2 天的實際 Hermes 使用：從引擎的 decode timing 行收集 tok/s，和前幾天 current best 的 log 比較分布（只當參考，工作內容不同，不做統計判定）。

### 2d. 回滾條件與步驟
- 觸發：當機、卡住、錯誤回應、記憶體或 VRAM 不足的警告比之前多，或使用者覺得變慢。
- 步驟：launcher／排程改回原 config → 重啟 → 核對 SHA 366A、3153、loaded。預計 5 分鐘內完成。

### 2e. 記錄更新（部署確認後）
- `state/CAMPAIGN_CURRENT_BEST.json`、`state/LIVE_DEPLOYMENT.json`：current best 改成 385E…30F5＋兩個環境變數；舊的 366A 留作 previous／rollback。
- 記下候選源碼的檔案 SHA（ram-lru-20261013 基底＋patch3），讓 build 可以重現。
- ledger 與報告 append。GitHub outbox 只在使用者要求時走兩階段流程。

## 3. 不在這份計畫內

- 把 2000 寫成 source 的預設值：不需要，用環境變數就好，回滾比較簡單。
- 路由三臂（DB25V100 等）：會改輸出，另外走品質評估計畫。
- pool 本身的自旋（`STRATA_POOL_SPIN_US`，預設 20 ms）：跟 helper 是不同的開關，沒測過；如果要測，另外登記。

## 4. Ledger 預登記（核可後寫入）

## 2026-10-28 xx:xx｜S2K_PROMOTION_CONFIRM
- 類型：確認（家族：I/O 重疊／MISS_OVERLAP；家族已結案，這筆不是新的旋鈕掃描，是上線前的確認）
- 假設：如果 MISS_OVERLAP＋SPIN_US=2000 對 current best 的 +6.5% 是真的，則 8 輪 ABBA 的按輪 CI 會排除 0，而且抽樣模式和 neuro 暖機下都不會變慢
- 目標段／上限：jobs＋CPU 段；MISS_OVERLAP 上限 4.5～7.3 ms/window，自旋修正的是 helper 跟 pool 搶核
- 設計：見第 1 節
- 停止條件：見第 1 節判定
- 結果：（待填）
