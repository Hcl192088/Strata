# 回滾程序（準備文件，未執行）

TASK LUNA-20261012-027 / NATIVE_PIPE_DEPLOY_PREP。目前 live 已是原版；此程序供未來獲准切換後回滾。

1. 先以 strict host-key SSH 確認 DESKTOP-LKMLUPC，盤點 PID／名稱／command line。只處理經分類的候選 API；發現其他未分類程序就停。先等待 API idle，不中斷使用者 request。
2. 驗證原 binary `C:\Users\User\Strata-Adrian-control\runs\miss-overlap-20261027\build\strata.exe` SHA256=`385EF64EE24BDF3BD4B309264FA811901DF9256B92CE4589BAEC70B3F26B30F5`，備份設定 `C:\Users\User\Strata-Adrian-control\runs\native-pipe-deploy-prep-20261029\live-original.json` SHA256=`F23F1AAD8E385987708D6DFB854AD139D513FE398151CCCC5FBD43CFE303EB6F`。任何不符就停。
3. 使用既有 harness 的 `next_steps_ab_20261018.stop_api(run_root)` 暫停經核對的 API；它採 Stop-ScheduledTask Strata-Task020-API、核對 API PID、等待 process gate clean。不得用程序名稱廣泛殺除。
4. 若未來部署覆寫了 active config，將 `live-original.json` 以原 bytes 複製回 `C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\server-task020-8080-v0142-s2k-mt1.json`；重驗 SHA256=`F23F1AAD8E385987708D6DFB854AD139D513FE398151CCCC5FBD43CFE303EB6F`。本次未覆寫 live config，因此現在不需要執行複製。
5. 使用原 task action：powershell.exe `-NoProfile -NonInteractive -ExecutionPolicy Bypass -File C:\Users\User\Strata-Adrian-control\tools\start_task020_api_s2k_mt1.ps1`。其原 launcher 已存 `live-original-launch.ps1`，task action 已存 `live-task-actions.json`。後續部署應保留此原 task action；若另行修改 task，必須另有可審閱的還原步驟。
6. 在 controller finally 使用既有 `restore_api(run_root)` / Start-ScheduledTask Strata-Task020-API。驗證唯一 engine binary SHA=`385EF64EE24BDF3BD4B309264FA811901DF9256B92CE4589BAEC70B3F26B30F5`、config SHA=`F23F1AAD8E385987708D6DFB854AD139D513FE398151CCCC5FBD43CFE303EB6F`、AboveNormal、health loaded=true、3153 slots／20.00 GiB／20479 MiB、workers 9／affinity all、STRATA_IQ3S_MT1=1；無 PIPE／PIPE_CHECK／DIAG／MT_MIN 啟用。既有 STRATA_RAM_LRU_CHECK=0 是停用值，保留。
7. 保存 restore、環境、capacity、process evidence；restore 失敗就回報失敗層級，不採 fallback、不改模型或 current-best build。

原 config 的 cwd/log/args/env 與 API 溫度均須還原為原 bytes；不要套 correctness 的 CHECK/DIAG 設定。此文件不授權現在部署或額外停服務。
