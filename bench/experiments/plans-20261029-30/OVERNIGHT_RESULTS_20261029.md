[LUNA_REPORT]
TASK_ID: LUNA-20261012-027
STATUS: PARTIAL / REPORT_LOCAL
TASK_SOURCE: direct user authorized overnight continuation
TASK_BRANCH: historical Task027; no new GitHub claim
TASK_COMMIT_SHA: continuation uses measured source base 61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406; canonical main 6251a722f9c98fbfde3465cb5f4639de589a008b
BENCHMARK_RAW_PATH: C:\Users\User\Strata-Adrian-control\runs\overnight-20261029; runs\native-pipeline-20261029; runs\native-pipeline-roles-20261029

# 夜間結果：未部署新 best

截止2026-10-29 07:00台灣時間；06:50進入收尾，無新測試。Host DESKTOP-LKMLUPC。

1. 精確decode-only診斷完成：Hermes 30requests/2838windows，CPU24.49645ms/window，其中GU11.87930、quant0.14382、down5.16286、join6.09016、LRU1.19571、殘差0.02459。helper9.66332/direct9.74951/copy1.71655/issuewait8.01635/ready4.16805是重疊項，不能相加成CPU。GU不是純解碼指令時間。
2. GU/down交錯已實作、完整測完五輪150正式requests。原MT1(C)46.95884，新binary關閉交錯(O)47.21754，開啟交錯(P)49.37278 pooled tok/s。P/C按輪+4.8930%，95%CI+1.5721..8.2140%；P/O primary按輪+4.3475%，CI-1.1478..9.8428%，未過事前採用gate。只有首輪51.16，其餘低於50，不能宣稱穩過50。獨立舊phase CPU reference至少906,705,920 float values逐位元相等，十種實際GU/down格式pair全覆蓋；全部19blocks容量/priority/參數audit通過。詳見PIPELINE_GENERIC_RESULT.md與remote native-pipeline-20261029/audit.json。
3. P/E優先序版本build成功（165059E7A5F528B80D5B029C487741AD652E0F0C38F4B6E112F99F4AAC61A110），SMOKE三題逐位元至少249,999,360 values通過。全十點CHK第一題時abort：`NATIVE_PIPE FATAL role pin id=-1 actual=1 expected=0`。之後harness才報503/priority ownership changed；後者不是根因。沒有完成CHK、沒有GD/RD、沒有任何C/G/R正式速度資料。不可把這個失敗當角色策略的負效能結果。
4. 既有Windows host placement使用SetThreadSelectedCpuSets，新增guard卻要求GetCurrentProcessorNumberEx瞬時CPU精確等於host_core。已確認不相符，是否為CPU Set語意、排程遷移或呼叫範圍需再診斷；不能直接刪掉guard、放寬後宣稱pin正確。06:50前已無足夠時間修正及完成五輪，不重啟舊runner。
5. I/O shadow方向曾錯把native GGUF當CPU來源；實際CPU用experts.bin且best早已drop_mapping，因此撤回微基準外推。該campaign未正式測速；自己建立的47GB影子已清理，原model/pack未變。錯誤與receipt留存。
6. 02:4x後工具automatic approval review額度限制令遠端操作未執行，直到05:50才恢復；期間無角色測試。05:53啟動的新runner05:56已因guard失敗退出並復原API，06:49才由本輪heartbeat讀回失敗。這一段沒有持續即時監控，不宣稱整夜無間斷執行。

## Live 與剩餘風險

06:50重新核對唯一strata PID23540，原current-best binary SHA385EF64EE24BDF3BD4B309264FA811901DF9256B92CE4589BAEC70B3F26B30F5、config F23F1AAD8E385987708D6DFB854AD139D513FE398151CCCC5FBD43CFE303EB6F，AboveNormal、health loaded、3153slots/20GiB/20479MiB皆正確；MT1=1，PIPE/ROLES/CHECK/DIAG/MT_MIN不存在。相關process只有原API/memory-policy及watch，沒有benchmark/build，未停無關process。best manifest不變，溫度不變。

canonical main兩個既有dirty tools/run_mtp_depth_20261014.py、tools/run_task027_ram_lru.py保留。測試來源是isolated source，不覆蓋main。保留base-relative patch與SHA以便後續，尚未達到source commit/tag+fresh rebuild的reproducible-best標準，不部署候選。

## Coverage 與下一步

Generic全部19meta/config/完整engine logs（1,307,971bytes/10,998lines）、150formal rows及檢查/診斷資料已audit。Role只完整SMOKE3請求+失敗CHK第一請求的meta/config/engine log；其他十點與正式150請求皆未執行。未逐字審閱私人prompt/response、未做完整source audit；私人raw不發布Git。

下次先檢查host CPU Set實際選取與call site是否在作用範圍內，再定義可證明P/E身分且不改原affinity的guard。修正後新root重做完整正確性與C/G/R五輪；不得重啟本次terminal runner。Generic目前是有正面證據但尚未正式採用的約49tok/s候選。

本機report狀態REPORT_LOCAL；舊GitHub snapshot不是即時發布依據，未執行outbox寫入。遠端task-scoped handoff/patch/manifest採正常git commit與單次push，結果另存收尾receipt；不使用認證fallback。

收尾receipt：remote main commit `2f1e99872969c9b4586a2d41c7f1915f27e4f298`，16個task-scoped文件已提交（報告、六檔base-relative兩候選patch、identity/audit/比較及兩套controller/harness）。正常push一次exit128，wincredman無法保存credentials且不能讀Username；未重試、未認證fallback、未推送成功。兩個既有dirty tools保留。排程strata-github-auto-handoff已PAUSED，其他排程未修改。沒有新best部署。
