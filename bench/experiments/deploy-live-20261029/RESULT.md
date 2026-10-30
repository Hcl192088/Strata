[LUNA_REPORT]

# NATIVE_PIPE_DEPLOY_LIVE：FAILED_ROLLED_BACK

TASK_ID：LUNA-20261012-027；STATUS：REPORT_LOCAL。使用者今日「切換 live」與本次 brief 直接授權 continuation。未進行 GitHub、push、source／main／git／模型／harness 修改，未重試部署，未調整溫度。hostname 實讀 DESKTOP-LKMLUPC。

失敗層級：step 5 的 smoke 回覆驗收。唯一一次 request HTTP 正常、生成32 tokens，但 finish_reason=length，message.content=null，只有 reasoning_content，因此未通過「正常最終回覆」。依 brief 立即回滾；沒有補送 request、沒有改 thinking／sampling 或增加 token 上限。已驗證 pipeline ACTIVE 與 decode timing；不能由此失敗宣稱 pipeline 計算錯誤，也不能宣稱成功部署。

## 時間線（2026-10-29，Asia/Taipei）

- 10:14:37：既有 harness 確認 metrics live.state=idle，Stop-ScheduledTask Strata-Task020-API。
- 10:14:40：依 PID／command line 終止原 API 遺留子程序，engine PID26660；無關程序未停止。
- 10:14:48.960：process gate clean；10:14:48.965 完成同目錄 temp 驗證與原子替換 config。
- 10:14:52.531：Start-ScheduledTask；10:15:12.678 新 API loaded=true，engine PID11628。
- 10:15:15.996：唯一一次中性 smoke；10:15:18.981 記錄 content 空的驗收失敗。
- 10:15:25：回滾前重新確認 idle／PID，Stop-ScheduledTask；10:15:28 終止已核對候選 API PID11628 等。
- 10:15:37：process gate clean，原 config bytes 還原並驗證 F23F…EB6F。
- 10:15:40.683：原 task 重啟；10:16:00.818 原 API loaded=true。
- 10:16:04.082：控制器完成 FAILED_ROLLED_BACK；10:16:30.210 獨立核對通過，原 engine PID32040。

以 Stop-ScheduledTask 發出至 loaded 偵測計，兩段維護中斷約35.7秒與35.8秒，合計約71.5秒。停止 log 精度為秒、health 每3秒輪詢；這是操作窗口估計，未以外部連續探測測量精確不可用時間。

## Identity 與設定

- 原／恢復 binary SHA256：385EF64EE24BDF3BD4B309264FA811901DF9256B92CE4589BAEC70B3F26B30F5。
- 候選 binary SHA256：A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8。
- 原／備份／恢復 config SHA256：F23F1AAD8E385987708D6DFB854AD139D513FE398151CCCC5FBD43CFE303EB6F。
- 新 config SHA256：060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93（曾短暫套用，現已回滾）。
- active config：C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\server-task020-8080-v0142-s2k-mt1.json。
- 原 task action 保持 tools\start_task020_api_s2k_mt1.ps1；launcher SHA256 192B016AAE303C61B1639833D2BA545804164FE12C44BC7904FD019CFCC564ED 前後相同。
- 新 config 保留原 JSON 排版與換行，parsed object 僅 exe、cwd、env.STRATA_NATIVE_PIPE 三項改變；候選檔與 temp 全檔 hash 相同才 replace。

Exact diff（相對 live-original.json）：

```diff
--- live-original.json
+++ candidate-live.json
@@ -1,7 +1,7 @@
 {
     "api_monitor": true,
-    "exe": "C:\\Users\\User\\Strata-Adrian-control\\runs\\miss-overlap-20261027\\build\\strata.exe",
-    "cwd": "C:\\Users\\User\\Strata-Adrian-control\\runs\\miss-overlap-20261027\\build",
+    "exe": "C:\\Users\\User\\Strata-Adrian-control\\runs\\native-pipe-deploy-prep-20261029\\build\\strata.exe",
+    "cwd": "C:\\Users\\User\\Strata-Adrian-control\\runs\\native-pipe-deploy-prep-20261029\\build",
     "tokenizer": "C:\\Users\\User\\Strata-IQ3-20261008\\packs\\iq3_xxs\\tokenizer",
     "model_name": "Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS",
     "log": "C:\\Users\\User\\Strata-Adrian-control\\runs\\miss-overlap-20261027\\s2k-mt1-api.engine.log",
@@ -67,6 +67,7 @@
         "STRATA_RAM_LRU_CHECK": "0",
         "STRATA_MISS_OVERLAP": "1",
         "STRATA_MISS_OVERLAP_SPIN_US": "2000",
-        "STRATA_IQ3S_MT1": "1"
+        "STRATA_IQ3S_MT1": "1",
+        "STRATA_NATIVE_PIPE": "1"
     }
 }```

## Step 5 驗證實值

| 檢查 | 候選 live 實值／結果 | 回滾後獨立核對 |
|---|---|---|
| 唯一 engine／SHA | PID11628，A1E6…1AD8，通過 | PID32040，385E…30F5，通過 |
| cwd | C:\Users\User\Strata-Adrian-control\runs\native-pipe-deploy-prep-20261029\build | C:\Users\User\Strata-Adrian-control\runs\miss-overlap-20261027\build |
| PIPE／MT1 | STRATA_NATIVE_PIPE=1、STRATA_IQ3S_MT1=1 | PIPE absent、MT1=1 |
| CHECK／DIAG／MT_MIN | 無啟用；原 RAM_LRU_CHECK=0 保留 | 同左 |
| Priority | AboveNormal=32768 | AboveNormal=32768 |
| health | loaded=true | loaded=true |
| 容量 | 3153 slots／20.00 GiB／20479 MiB | 同左 |
| workers／affinity | 9／all；logical 2,4,6,8,10,12,13,14,15，host0 | 同左 |
| pipeline log | NATIVE_PIPE ACTIVE workers=10 down_limit=3 exact_row_kernels=1 | 原版無 PIPE |
| fatal | 候選啟動＋smoke 解析範圍無 NATIVE_PIPE FATAL／mismatch | 回滾啟動驗證通過 |
| smoke | **FAIL：content=null，reasoning 有生成，finish=length** | 未另送 request |

唯一 smoke 使用 brief 範例的32-token上限，中性藍天句子，未傳 temperature。usage：prompt61、completion32、total93；API predicted_ms=905.1、35.4 tok/s；engine：32 generated in 905 ms (35.4 tok/s)，17 windows、53.24 ms/window、1.88 tokens/window，draft accepted15/15。沒有私人 prompt 紀錄。PIPE ACTIVE 是首次生成才輸出，於這筆 smoke 後核對，並非省略啟用驗證。

## Best manifest 與目前狀態

既有 best manifest：C:\Users\User\Strata-Adrian-control\bench\results\2026-10-28-s2k-mt1\BEST.json（S2K+MT1，385E…30F5／F23F…EB6F）。本次未成功，依 step7「On success」條件，**未新增 promotion entry、未產生新 CURRENT_BEST.json**；D:\strata\CURRENT_BEST.json 未編輯。fresh 的 source tag native-pipe-generic-20261029／commit f520bc5e9d31c93caeb296b059e3a3eaa16e493f 僅為本次失敗候選 identity，未晉升。

最終 process gate：只有原 API／memory-policy／watch，所有 PID、name、command line 存 independent-final-processes.json；無未分類相關 engine／benchmark／build。讀取探針本身及其 SSH ancestors 依原 harness 排除。heavy process 列表僅記錄，未停止。

## 回滾提醒與 raw paths

本次回滾已完成，不要重複執行。既有程序：先 strict SSH／hostname／process gate／idle，使用 next_steps_ab_20261018.stop_api(run_root)，將 C:\Users\User\Strata-Adrian-control\runs\native-pipe-deploy-prep-20261029\live-original.json 原 bytes 還原至上述 active config，核對 F23F…EB6F，執行 `Start-ScheduledTask -TaskName Strata-Task020-API`，完整核對385E…30F5與容量／env。完整命令契約見 state/deploy-prep-20261029/ROLLBACK.md。不得直接廣泛依 process name kill。

遠端 raw root：C:\Users\User\Strata-Adrian-control\runs\native-pipe-deploy-live-20261029；本機完整此 run raw：D:\strata\state\deploy-live-20261029。主要證據：deploy.py、state.json（含失敗 response）、preflight.json、candidate-live.json、config.diff、verification.json、startup.log、controller.log、rollback-startup.log、rollback-verification.json、independent-final-verification.json、independent-final-processes.json、smoke-log-evidence.json、final-task-manifest.json。原共享 engine log 留遠端 C:\Users\User\Strata-Adrian-control\runs\miss-overlap-20261027\s2k-mt1-api.engine.log，未整份複製以免攜帶歷史私人請求；只擷取本次 pipeline／timing 行。

既有來源證據：runs/native-pipeline-po-confirm-20261029、runs/native-pipe-deploy-prep-20261029、runs/fresh-build-sanity-20261029/attempt-2。沒有重跑既有 benchmark。

Coverage：完整核對要求的四個 gate SHA、三項設定 diff、候選啟動 identity/env/priority/capacity/cwd、單次 smoke response 與 decode 行、原 bytes rollback、恢復後獨立 process／health／identity。大型 binary 僅全檔 SHA，未搬移／審閱全部 source；startup log 全檔模式解析，smoke 僅限定 pipeline/timing 行擷取，未做自然語言品質或長期穩定性測試。32 tokens 在目前 thinking 行為下不足以完成最終回答是合理推論，未以新 request 驗證；未確診為 native pipeline 缺陷。

上游工具紀錄：部署前曾因 Windows command line 過長及一次 PowerShell quoting 錯誤而未成功送達控制器；修正傳輸命令後完成唯一次 live switch。首次 preflight 亦發現 Path.resolve 將 junction 展開，已在切換前改成 brief 指定 canonical 路徑並重新核對 diff。這些前置失敗均未停止 API、未改 live config。未採替代 binary、fallback 或重試部署。