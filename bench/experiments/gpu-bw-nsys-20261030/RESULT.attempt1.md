# GPU_KERNEL_BW_DIAG — 未完成（2026-10-30）

使用者授權停止 API 一次、執行 nsys 診斷並還原。已停止一次並還原；未修改 source、build、部署、GitHub 或系統設定。這不是 brief 所列的 DONE 或 BLOCKED：診斷控制器的時序與 prompt 選擇錯誤使資料無法回答問題。

- 主機 DESKTOP-LKMLUPC；binary SHA256 `A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8`；config SHA256 `060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93`。執行前 live command 與 command.json 相符，MT1=1、PIPE=1、MT_MIN 未設；process gate 通過，API idle。
- Nsight Systems 2026.5.1.161，以 Highest 一次性 task、AD10x general set、20 kHz、CUDA graph node trace 執行。注入下 3135 slots。GPU_METRICS 有 DRAM Read/Write Bandwidth 指標，不能把該事實當成有效 decode 頻寬。
- 控制器要求 GEN 512，但短 prompt 在 13 行 T、DONE stop 後結束；以第一行 T 觸發 nsys start 的同步呼叫過晚。SQLite 沒有 CUPTI_ACTIVITY_KIND_KERNEL，診斷訊息為 `No CUDA events collected. Does the process use CUDA?` 與 `CUDA profiling might have not been started correctly.`；無法證實 metrics 覆蓋有效 decode。因而整段 busy fraction、busy DRAM GB/s、family 與 top 10 表格均未測得，預註冊 verdict 無法判定。不得把其他 GPU 活動的 metrics 當引擎數據。
- 控制器 finally 等待引擎退出後還原；獨立檢查 PID 22020、loaded、idle、queued 0、AboveNormal、3153 slots、binary/config SHA 均一致；最終 gate 通過，一次性 task 已註銷。停止範圍為已確認 API stack；未停止其他程序。
- 本地保留控制器、啟動腳本、SQLite、metrics 日誌與結果；遠端 trace 位於 `C:\Users\User\Strata-Adrian-control\runs\gpu-bw-nsys-20261030\trace.nsys-rep`。必須取得再次停止 API 的明確授權才可進行另一輪；在不中斷 API 的範圍可先修正 prompt 和捕捉時序。
