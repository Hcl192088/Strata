# GPU_KERNEL_BW_DIAG — 未完成（2026-10-30）

使用者授權停止 API、執行 profiling 並還原；未修改 source、build、設定或 GitHub。

- 主機 DESKTOP-LKMLUPC；Nsight Compute 2026.1.1.0，診斷排程 RunLevel Highest，priority 2，clock-control none、cache-control none。
- Binary SHA256：A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8；config SHA256：060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93；與遠端 BEST manifest 一致。
- 初次多指標捕捉因 kernel replay 無法保存記憶體失敗。此次輸入因腳本誤將逗號分隔 token 當作空白分隔而過長；未採用結果。控制器在引擎剛退出時誤判程序殘留，未自動還原；在確認程序退出後手動啟動 API，並確認恢復。
- 第二次短 prompt、僅 duration/read/write 指標，engine 報 watchdog stall，應用程式退出碼 3221226505，沒有產出 ncu report 或 CSV。profiler 注入時 3127 slots、20478 MiB。無法製作 per-kernel、family、每 window 時間或預註冊規則判斷。這些失敗不在 brief 指定的可接受 BLOCKED 條件中，故不能宣稱 BLOCKED 或 DONE。
- 第二次 finally 成功還原 API；另一次獨立檢查 PID 23184、loaded、idle/queued 0、AboveNormal、3153 slots、20.00 GiB、20479 MiB，binary 和 config SHA 均一致；診斷 task 已移除。獨立證據見 independent.json、processes-independent-final.json；詳細 log 保存在此目錄。
- 只停止確認過的 API stack；第一次嘗試停止本次 profiler 時它已自行退出。第二次 engine 寫出診斷 dump `C:\Users\User\Strata-Adrian-control\runs\native-pipe-deploy-prep-20261029\build\strata-stall-8284.dmp`，保留未動。
