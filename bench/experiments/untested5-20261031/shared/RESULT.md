STATUS: DONE

已讀取 COMMON、既有 controller 與遠端 replay harness。shared 目錄原先沒有 BRIEF.md 或 RESULT.md。既有 replay harness 的 run_block finally 呼叫 kill_tree，會終止 server 與子程序；須先確認如何符合不擅自停止程序的規則，再完成控制器。未啟動引擎或 benchmark，未複製遠端檔案。

本次確認遠端主機 DESKTOP-LKMLUPC；程序篩選未見 strata、python、cmake、ninja、clang、msbuild 或 cl.exe。S3 DIAG 排程狀態為 Ready。尚未完成控制器、報表、遠端複製與 dry run；既有 kill_tree 與不得擅自停止程序的限制仍需解決。

本次再次確認 replay.py 的 run_block finally 會透過 kill_tree 終止 server 及子程序；每 block 使用新引擎的設計需要釐清是否允許控制器結束自己啟動的程序。依禁止擅自停止程序的規則，等待明確授權；未啟動或停止任何程序。shared/BRIEF.md 不存在。

本次依 STEPS.md 重新讀取 COMMON.md 與本檔；必要的 shared/BRIEF.md 仍不存在。S0.1 要求每個 block 使用新引擎，既有 harness 會終止其程序，尚未取得停止控制器自行啟動之程序的明確授權。步驟維持未完成；未啟動或停止程序，未執行遠端操作。

本次確認 shared/BRIEF.md 仍不存在，且未取得停止控制器自行啟動之程序的明確授權；S0.1 仍未完成。未執行遠端操作或啟動、停止程序。

本次再次確認必要的 shared/BRIEF.md 不存在；尚無明確授權停止控制器啟動的引擎或 server。S0.1 維持未完成，未執行遠端操作。

本次依步驟規則檢查，shared/BRIEF.md 仍不存在，無法讀取必要的階段設計；S0.1 保持未完成。未啟動或停止程序，未執行遠端操作。

本次依 STEPS.md 讀取 COMMON.md 與本結果檔；shared/BRIEF.md 仍不存在，無法讀取規定的階段設計。S0.1 保持未完成；未執行遠端操作，未啟動或停止程序。

本次重新讀取 COMMON.md、RESULT.md 與交班規則；必要的 shared/BRIEF.md 仍不存在，S0.1 無法依規則執行，維持未完成。未執行遠端操作或停止程序。

本次確認規定的 shared/BRIEF.md 仍不存在，無法依步驟規則完成 S0.1；未執行遠端操作或停止程序。

本次確認 shared/BRIEF.md 已存在，且明確授權停止控制器自行啟動的引擎與 server；先前相反記錄已過時。已讀取既有 controller、run.ps1、base.py、replay.py，確認遠端主機 DESKTOP-LKMLUPC。遠端程序清單輸出遭截斷，尚未完成程序關卡；控制器、報表、遠端複製及 dry run 仍未完成。未啟動或停止引擎。

本次已讀取 shared/BRIEF.md，確認明確授權結束控制器自行啟動的引擎與 server；先前缺少 brief 和授權的記錄已過時。已檢查既有 controller、run.ps1、base.py、replay.py；控制器、報表、遠端複製與 dry run 尚未完成。本次未進行遠端操作或啟動、停止程序。

S0.1：建立 abctl.py 與 report.py，複製至遠端 C:\Users\User\Strata-Adrian-control\runs\untested5-20261031\shared；兩檔本機與遠端 SHA256 一致。遠端與本機 dry run 均產生 3 輪 9 blocks，順序依輪次輪轉；僅 C 設定 slots gate。報表以合成 10% 差異資料檢查逐輪、逐點、平均值與 t 信賴區間。遠端 harness import 與編譯成功。未啟動引擎或執行實際 A/B；引擎互動、實際容量閘與真實輸出解析尚未實測。參數格式見 dry-arms.json；選用 request_set 為 point ID 到 request body 的 JSON object，可另給 sampling object。report.py 的 t 表支援 2–31 輪。
