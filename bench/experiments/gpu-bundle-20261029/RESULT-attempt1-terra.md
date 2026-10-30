[LUNA_BLOCKED]

# GPU_EXACT_BUNDLE：前置檢查未完成

TASK_ID：LUNA-20261012-027 continuation。STATUS：PARTIAL / REPORT_LOCAL。2026-10-29 使用者直接授權本次測試，禁止 source edit、build、live config 變更、push 與 GitHub writes。

已透過 strict host key SSH 確認 DESKTOP-LKMLUPC；實際 binary SHA256 為 A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8，與遠端 BEST.json 一致。live config SHA256 為 060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93，與 BEST.json 一致。遠端 source HEAD 為 f520bc5e9d31c93caeb296b059e3a3eaa16e493f，git status 無輸出。

遠端程序盤點觀察到 live API 的 engine PID 1052、server 與記憶體政策 watch 程序；未看到其他符合名稱篩選或工作集大於 1.5 GiB 的程序。此為當時快照，後續操作前須重新盤點。舊 Strata-Spec-Split-20261029 task State=3（Ready）；尚未刪除。

已閱讀既有 SPEC_SPLIT controller；它仍固定使用 --spec-split、兩個 128-token checks 與五輪策略，不能直接當成本次 GPU bundle controller。八個開關的 source 查詢輸出被截斷，逐項 getenv、啟用條件和啟動訊息尚未完整核對。未建立或啟動 controller，未停止 API，未執行 SMOKE、A/B、exactness，故沒有 rows.json、速度或 verdict。未做本次 live 最終驗證；僅觀察到 API engine 程序仍存在，不可據此宣稱 loaded 或所有環境與容量驗證通過。

Coverage：讀取本機規則、ledger 該項、switch inventory、SPEC_SPLIT 報告及 controller/harness/exactness；遠端讀取 AGENTS、BEST、source HEAD/status、binary/config hash 和篩選程序。source 搜尋結果截斷，並非完整逐項審查；沒有新的執行資料。下一步須重新 process gate、完整核查八開關並依本次設計製作及審核 controller，才能執行；再依終止規則、restore 與結果更新 ledger。
