[LUNA_BLOCKED]

# FRESH_BUILD_SANITY：BLOCKED_CONFIG_DIFF

TASK_ID：LUNA-20261012-027 continuation。依本次直接授權執行前置檢查；無 GitHub 操作、push、source/git/model/live config 修改，未停止任何程序，未啟動 benchmark。

## Identity 與程序

Strict host-key SSH 已確認 DESKTOP-LKMLUPC。遠端實際 harness 已讀取並下載保存；preflight.py 直接 import 原 native-pipeline-po-confirm-20261029/controller_confirm.py，呼叫原 build_cfg。

F SHA256：A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8。
T SHA256：3F98913EDB0B01D5D5DD3282412725141C298BF5CC9E890DD286AA0720C27230。
兩者完整 hash 均符合 brief。source tag/commit 僅讀取 deploy-prep 報告，未重新查 git。

程序 gate：已按 PID、名稱、command line 核對 API、memory-policy/watch；原 harness 程序集合無未分類項目。另以 Win32_Process 檢視 Python/Strata/PowerShell/cmd/Codex/Claude/build 程序，只有 API 家族、watch 與本次 SSH 檢查；未見 SSD_JOIN_BOUND controller。完整原 harness inventory 存 preflight.json。

## 停止原因：上游 config 生成規則

原 replay_ab_20261027.py/build_cfg 同時設定 cfg['exe']=exe、cfg['cwd']=exe.parent，並為各 block 指定獨立 log。實際產生 F/T/F 三份 preflight config，全 key 比較 F/T 得到 exe、cwd、log 三項不同；其餘 key（含全部 args/env）相同。

- F cwd：C:\Users\User\Strata-Adrian-control\runs\native-pipe-deploy-prep-20261029\build
- T cwd：C:\Users\User\Strata-Adrian\repo\Strata-Adrian-control\runs\native-pipeline-20261029\build
- log 為各 preflight-block 目錄下 engine.log。

依 brief「except exe path；stop if anything else differs」停在 config gate。即使將獨立 log 視為輸出檔差異，cwd 仍是額外差異。沒有自行改 harness、正規化 cwd、放寬規則或追加輪次。

三個 block 均未執行。pooled tok/s、ms/window、tokens/window、window-weighted CPU ms/window、合併 F/T 百分比均為未量測；不能判定 PASS/FLAG。rows.json 為空陣列，明確代表沒有測量資料。預登記 −5% 規則保持不變。

## Live 狀態

API 未停，故未呼叫 stop_api/restore_api。實際 engine PID 27444，binary SHA256 385EF64EE24BDF3BD4B309264FA811901DF9256B92CE4589BAEC70B3F26B30F5、config SHA256 F23F1AAD8E385987708D6DFB854AD139D513FE398151CCCC5FBD43CFE303EB6F 均通過原 final_verify。AboveNormal、health loaded=true、3153 slots、20479 MiB、workers 9、MT1=1，無 PIPE/CHECK/CPU_PHASE_DIAG/MT_MIN 啟用。live command line 同時確認 resident-budget-gib 20、pool-affinity all。這是未停機的狀態核對，不宣稱完成停機後還原測試。

## Coverage 與原始路徑

完整讀取指定 ledger entry、po-confirm RESULT、原 controller、replay harness、遠端 AGENTS；deploy-prep RESULT 初次批量讀取遭顯示截斷，後續完整讀取 source/build 前段及末段 restore/config/coverage，未逐字重讀中段 SMOKE/CHK。完整全檔 hash F/T、完整三份生成 config 比較，完整 preflight inventory 與 live health/metrics 身分核對。未執行測速、未完整 source audit、未重驗歷史 raw logs/prompt SHA。未將未量測項目填入歷史數字。

遠端：C:\Users\User\Strata-Adrian-control\runs\fresh-build-sanity-20261029，含 preflight.json、rows.json、preflight-block-1/2/3/config.json。
原 harness：C:\Users\User\Strata-Adrian-control\runs\native-pipeline-po-confirm-20261029\harness。
前置腳本：C:\Users\User\Strata-Adrian-control\runs\fresh-build-sanity-preflight-20261029.py。
本機：D:\strata\state\fresh-build-sanity-20261029，同步上述證據與原 harness/controller。

下一步需 planner 明確修正 config 契約：是否允許沿用 harness 的 exe/cwd/log 差異，或指定共同 cwd 並允許最小 controller 調整。此文件不自行授權任何替代方案。
