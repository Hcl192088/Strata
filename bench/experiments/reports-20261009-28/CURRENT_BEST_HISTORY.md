# Current best 歷代紀錄（由 2026-10-28 起維護；之後每次換版新增一列）

新的在上。tok/s 只在「同一次實驗、同一 harness」內可比，跨列不可直接比（硬體狀態、優先權、workload 都可能不同）。

| 生效時間 | 名稱 | binary SHA256（前 8…後 4） | 開關／設定 | 證據與數字 | 回滾／原始紀錄 |
|---|---|---|---|---|---|
| 2026-10-28 21:33 切換／21:35 驗收 | **S2K+MT1** | 385EF64E…30F5（與 S2K 相同） | S2K 加 `STRATA_IQ3S_MT1=1`，`STRATA_IQ_MT_MIN` 未設；config `server-task020-8080-v0142-s2k-mt1.json`（SHA F23F1AAD…EB6F）；launcher `start_task020_api_s2k_mt1.ps1`；排程 priority 2 | 既有 IQ3S_MT1_AB：47.00 vs 45.10 tok/s，按輪 +4.26%（CI +2.15～+6.37），CPU −2.19 ms/window；本輪只驗收部署，3/3 smoke 通過；浮點差異經使用者接受 | S2K 原檔保留；`LIVE_DEPLOYMENT.pre-mt1-20261028.json`／`CAMPAIGN_CURRENT_BEST.pre-mt1-20261028.json`；receipt `runs/mt1-deploy-20261028/out/deploy_receipt.json` |
| 2026-10-28 10:27 | **S2K**（MISS_OVERLAP＋短自旋） | 385EF64E…30F5 | `STRATA_MISS_OVERLAP=1`、`STRATA_MISS_OVERLAP_SPIN_US=2000`，其餘與 Task020 config 相同；config `server-task020-8080-v0142-s2k.json`、launcher `start_task020_api_s2k.ps1` | S2K_PROMOTION_CONFIRM 第 1 階段：greedy 8 輪 ABBA 對前一版 +8.49%（CI +5.91～+11.06，46.42 對 42.81 tok/s）；抽樣 +4.0%；neuro 暖機後 +5.6%；MCHK 0／69896 不一致。使用者於 2026-10-28 授權上線 | 見 `LIVE_DEPLOYMENT.json`（rollback 節）；舊版完整紀錄 `CAMPAIGN_CURRENT_BEST.pre-s2k-20261028.json`、`LIVE_DEPLOYMENT.pre-s2k-20261028.json` |
| 2026-10-13 建置／2026-10-18 重新驗證～2026-10-28 | **Task020 live**（ram-lru-20261013，IQ3_XXS） | 366A355E…15E2 | 排程 `Strata-Task020-API`，launcher `start_task020_api.ps1`，config `server-task020-8080-v0142.json`（STRATA_RAM_LRU=1 等） | 作為 C0 對照臂，Hermes replay greedy 約 36.6～37.6 tok/s（2026-10-27 夜間，優先權 7）；2026-10-28 優先權 2（引擎 AboveNormal）下約 42.8 tok/s。未宣稱 global fastest | binary 與原 config／launcher 原封不動，仍是之後配對比較的 C0 |
| 2026-10-08 | PHASE4_E4S24_DECAY050（IQ2_XS 舊快照） | E67EB500…FA74 | adapt-every 4、adapt-swaps 24、decay 0.50 等（`D:\strata\CURRENT_BEST.json`） | 舊 IQ2 快照，**不是**目前 IQ3 部署的 authority | `D:\strata\CURRENT_BEST.json`（legacy） |

備註
- Task025 的 E3FA77FE…27FB（報告 49.45 tok/s，source-async-miss）無法重現，不列入歷代 current best，見 `CAMPAIGN_CURRENT_BEST.json` 的 `historical_candidate_not_reproducible`。
- 在 10/08 與 10/13 之間是否還有其他被當作 current best 的版本，我沒有逐一查證；上表只列有檔案證據的三筆。
- 2026-10-28 部署時 Task020 的 config 檔雜湊是 43A48004…39C07，與 `LIVE_DEPLOYMENT.json` 舊紀錄的 C805…EA18 不同（變更早於這次部署，內容未再追究）。
- 部署後 harness 提醒：`next_steps_ab_20261018.py`／`replay_ab_20261027.py` 仍以舊 binary（366A）辨識 live API 與 C0，下次遠端 benchmark 前要先更新或複製 harness。
