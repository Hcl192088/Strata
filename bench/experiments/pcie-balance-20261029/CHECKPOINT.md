# PCIE_BALANCE_PORT 連線中斷 checkpoint（尚非最終報告）

TASK_ID：LUNA-20261012-027 continuation。使用者 2026-10-29 brief 授權 port／build／checks／預註冊 A/B；禁止 push、GitHub writes、remote main 修改與 live config 切換。

最後成功 SSH：2026-10-29 約 12:05（台北），remote hostname DESKTOP-LKMLUPC，controller_pid=26496、venv parent=30052，B8 r3 engine PID8524、server PIDs5332/5648。其 command line 已核對指向本次 run root，無其他未分類測試程序。

已完成：
- 全部指定本機規則／ledger／live／Hermes harness 紀錄已讀。
- 遠端 live A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8、config 060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93、AboveNormal、loaded、3153／20.00／20479、PIPE=1／MT1=1，停機前均實讀通過。
- Base tag refs/tags/native-pipe-generic-20261029^{commit}=f520bc5e9d31c93caeb296b059e3a3eaa16e493f。
- 隔離 worktree：C:\Users\User\Strata-Adrian-control\runs\pcie-balance-20261029\source；branch pcie-balance-20261029；commit 4639ae8a61c870abde192e13f09c6b0489604977；annotated local tag pcie-balance-port-20261029；乾淨。未 push。
- fresh build exit 0；binary DF13A36431461CA117F105BE4588BBAA618C9357BD7281F812391547CD689EC2。flags 同 deploy-prep build.cmd，僅 source／build／log 路徑替換。
- 衝突 10 hunks／4 檔，詳 CONFLICTS.md；完整 ported.patch 與 identity.json 已下載。
- SMOKE3＋CHK10 ×128：OK，全部十組 gu/down、missing=[]，零 mismatch。檢查紀錄的 values 為進度行之累積值相加，不把它解讀為唯一比較值總數。
- MECH p04/p05/p06 ×128：OK；registered=8.00 GiB、locked=12288 MiB、總量20480；PCIe 1.68／1.00／1.27 expert/層-window；三題 fit ready=1；PIPE ACTIVE，無 fatal，詳 mechanism.json。
- detached scheduled task Strata-PCIE-Balance-20261029；controller.py finally 呼叫既有 restore_api 並驗證。live config 未修改。原 API 已於 11:42:50 後 stop_api 停止（精確時間待 controller.log），目前尚未實證恢復。
- 正式第1輪 C/P8/B8、第2輪 P8/B8/C 已完成。remote round-deltas.json 實讀 B8/C：−2.2330698816036443%、−1.0850474942168287%。最後正在第3輪 B8→C→P8，尚未取得第3輪結果；不可判提前停止或最終效能。
- 正式 rows.json 仍在遠端，尚未成功下載；不可用空陣列冒充正式結果。CI／block metrics 待下載計算。

連線問題（2026-10-29 12:06 起）：SSH timeout；12:07:41 筆電作用中 Wi-Fi= TANetRoaming，Tailscale 本機 offline／logged out，錯誤 register request controlplane.tailscale.com context deadline exceeded，TCP22=false。證據支持筆電端 Tailscale control-plane 不通，不能確認桌機 offline。未改網路／Tailscale、未停止任何程序。已通知使用者切回手機熱點。

Remote raw root：C:\Users\User\Strata-Adrian-control\runs\pcie-balance-20261029（junction 實路徑 C:\Users\User\Strata-Adrian\repo\Strata-Adrian-control\runs\pcie-balance-20261029）。本機 state/pcie-balance-20261029 有 controller.py、launch.ps1、poll.ps1、archive.py、analyze.py、pin.py、resolve.py、serve_log.py、CONFLICTS.md、identity.json、ported.patch、mechanism.json、check-SMOKE.json、check-CHK.json。

恢復連線後：先 process inventory（poll.ps1），讀 campaign.json／wrapper.done.json／final_verify.json，勿重跑 controller 或 benchmark。若仍在執行就等待。結束後獨立驗 live，下載 evidence（archive.py 不含 source/build/harness），完整 audit logs/rows，跑 analyze.py，寫 RESULT.md，重讀 ledger 後 append 結果。臨時 task 只能在完成狀態核對後 unregister，勿停止仍執行中的 controller。
