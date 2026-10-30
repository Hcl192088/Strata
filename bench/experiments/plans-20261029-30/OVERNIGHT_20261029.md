# 夜間自主測試控制點

**收尾完成（06:54前）**：禁止再啟動夜間測試。roles runner4392早於05:56 FAILED/退出；根因engine `NATIVE_PIPE FATAL role pin id=-1 actual=1 expected=0`，503/priority ownership錯誤為後續症狀。全十點CHK未過，零正式role性能樣本。06:50/06:51兩次核對原MT1 API23540/385/F23、AboveNormal、loaded、3153/20/20479及env正確，無測試/build殘留。Generic49.37278仍只是未採用候選，best不變。完整結果state/OVERNIGHT_RESULTS_20261029.md；remote .codex/handoffs/2026-10-29-overnight.md與bench/experiments/overnight-20261029已commit **2f1e99872969c9b4586a2d41c7f1915f27e4f298**，保留兩個既有dirty tools。正常push僅一次，exit128 wincredman credential store失敗；不重試/不fallback。Receipt remote roles root/git-save-receipt.json，兩候選六個明確修改檔base-relative patch已保存，非完整source重建證明。automation已用原id/target/prompt/rrule設PAUSED並成功回傳；本機非Git不建repo。GitHub outbox未發布，REPORT_LOCAL，非已同步GitHub。後續只依使用者新授權繼續，勿自動重跑terminal campaign。

**05:55驗收**：roles SMOKE三請求已OK，獨立原phase bitwise至少249,999,360 values零mismatch，嚴格P/E pin與容量gate皆通過。唯一runner4392已進全十點CHK，尚無正式速度結論。05:55即時campaign/log已讀，不能把CHECK低tok/s當性能退步（CHECK故意額外重算）。下一heartbeat先看同root campaign/final_verify/comparison；若DONE只收結果不重跑。每批raw由runner落out，all-blocks/phase-rows/rows/comparison持久化；API原best未改。角色分析器analyze_roles.py與audit_roles.py已準備，audit僅完整19blocks/150formalrequests才可pass。若deadline導致PARTIAL，用實際完成範圍回報，不放寬gate。07:00須pause此automation，仍需完成remote task-scoped handoff/patch/report commit及一次正常push，不可稱已做。

**05:53唯一runner已啟動，禁止重複跑**：遠端runs/native-pipeline-roles-20261029/controller_roles.py，PID4392/create1793224375.7222364（venv parent12736），task Strata-Native-Pipeline-Roles-20261029。campaign.json START，按受控流程停止原API後開始SMOKE/CHK→GD/RD→C/G/R五輪。candidate SHA165059E7A5F528B80D5B029C487741AD652E0F0C38F4B6E112F99F4AAC61A110。prelaunch.json確認原MT1 PID7724/385/F23/env/priority/容量皆正確，無foreign process；builder exit0。每block距06:50至少4分鐘，06:50自有children watchdog、finally原MT1復原並核對；07:00 task時限。沒有promotion。舊generic/shadow runner不得重啟。下一步只核對這個新runner狀態及結果，完成後保存report/patch到remote git並依既有授權commit/push；憑證錯誤不fallback。

**05:52更新**：02:4x遠端執行曾因automatic approval review額度失敗而未執行，非測試卡住；直到本輪才恢復工具。已重新讀回automation target正確、遠端hostname/全部相關process與385/F23 SHA正確，API PID7724 loaded=true（服務只bind<tailscale-host>，127.0.0.1 health失敗非服務故障）。roles新root已建立，build PID16880/child19024正在編譯；尚未啟動benchmark。舊generic runner仍不可重啟。roles source SHA9E0F/48AF。截止不延後。

**目前接續位置（02:28更新）**：generic pipeline舊runner25144已DONE且退出，原MT1 API已復原；目前沒有測試runner在跑。先讀state/overnight-20261029/PIPELINE_GENERIC_RESULT.md。generic正式C46.96/O47.22/P49.37，尚不promote；下一步實作P優先GU/E維持down優先的role策略，須另開root/state/task並重新process/binary gate，不重啟任何舊runner。07:00硬截止與本thread heartbeat不變。

- Goal/thread: 01a18236-3646-7281-ae59-19ec75adeb77。
- 使用者明確授權：自行決定並執行測試，無人協助，最晚台灣時間 2026-10-29 07:00 停止測試；先設每小時排程。
- 已完成排程：strata-github-auto-handoff 已改綁本thread，ACTIVE，每小時，截止2026-10-28 23:00 UTC。配置檔已讀回確認target_thread_id和截止時間。
- 最新工作：MT1 Hermes decode-only CPU/I/O 精確拆解；先做診斷，再依證據選能補足約6.4%速度差距的結構改法。不變更路由、有效expert貢獻、量化、溫度；接受MT1類浮點順序差異，不加fallback。
- 本輪是 LUNA-20261012-027 的直接使用者授權continuation，不claim舊main Task011或改寫mailbox。
- Deadline UTC: 2026-10-28T23:00:00Z。runner須在06:50前停止新增run，07:00前結束自有測試並恢復已核對的MT1 API；不停止無關程序。
- 本機進度：state/overnight-20261029/progress.json；遠端root預定 C:\Users\User\Strata-Adrian-control\runs\overnight-20261029。
- 排程只接續本檔和durable runner狀態，不重跑已活躍runner。沒有實質新事實時保持安靜。

## 已驗證的00:15左右preflight

遠端hostname正確。MT1 binary 385EF64E…30F5、config F23F1AAD…EB6F、launcher192B016A…64ED均與受控狀態一致；canonical main6251a722…008b。API排程Ready、沒有Strata/Python/build/nsys/wpr等相關進程，8080未載入；不是測試掛住。既有不相關dirty檔保留。build base和來源須在build前另核對。

## 方向檢查

1. 目標50；既有MT1 replay46.97，差1.29ms/token、約2.47ms/window。
2. MT1 decode CPU23.90、GPU-reach11.77、jobs0.275、draft1.83ms/window；helper全request約6.33不可當精確decode-only。
3. 本次先精確定位CPU內可改份額，不從重疊helper總時長算速度。後續候選若理想上限不足差距一半，不單獨投入長A/B。
4. 最近MT1已通過並部署；不連掃worker/affinity/spin/PIN/AA。
5. 不重做PATCH4、已失敗MTP gate、全型別MT_MIN、舊GPU-only predictor。
6. miss/位置受tail-skip有效集合約束；kernel只允許同數學；pipeline尚待有效證據；mainline不直接替換live。
7. 修正真正上游問題：原log沒有decode起訖快照，非純解析問題；需要只加計時的診斷來源，不偽造分項比例。

## 第一階段驗收

獨立source/build，記錄SHA/patch/build；off/on相同候選binary與current-best錨點，容量3153/20GiB/20479MiB、AboveNormal、相同Hermes10點、same env與sampling。診斷輸出須每request decode-only GU/quant/down、helper read/join、inline read、LRU時間，守恆可對CPU/join與總window，不相加重疊項。若計時本身污染正常行為，標示並量off/on，不把診斷速度當優化成果。

## 停止與交付

時間到或無可行已授權後續時彙整真實結果、未驗證項與下一步；07:00截止是硬上限，不是要求填滿時間。最終state/OVERNIGHT_RESULTS_20261029.md，raw留遠端並下載小型結果。本機非Git不建repo。遠端task-scoped變更commit/push；若憑證仍失敗只記錄，不認證fallback或重試。舊6251a722 push認證已知失敗不再為它打轉。

## 00:34 priority gate 修正
遠端即時盤點發現初始PROBE、C-r1為Normal，O-r1中途才於2026-10-28T16:34:27.754Z調為AboveNormal，PID5900實讀32768。第一輪C/O速度比較排除；probe只驗守恆。後續由Strata-Overnight-Priority-20261029控制priority-watch.ps1，僅處理controller29148（核對creation time）的子孫、且binary SHA必須為current-best385E…30F5或診斷C7F4…3FA54。不停止程序；記錄每engine的調整時間，需確認調整早於request。watcher隨controller退出或06:50停止；不能將測試事前登記當成實際priority證據。controller仍live，未重啟。

## 約01:00 第一階段完成；下一步不要重啟舊controller
遠端controller已DONE，90正式requests/30D phases+3probe，API MT1已恢復且verified=true，PID27736 AboveNormal。小型Windows unmapped I/O probe與同檔map切換確認都DONE且bytes hash通過。新證據：同U檔512KiB U/M比2.930→0.848；2MiB1.619→0.892，mapping後優勢消失。不是模型加速。原始小檔已下載。詳讀state/overnight-20261029/PHASE_AND_IO_RESULTS.md，下一步直接做第一GGUF shard shadow direct-reader候選與模型A/B，不再跑相同小probe。只第一47.04GB可容納（free69.37GB）；雙75.84GB不合容量。shadow複製/hash必須direct，不要buffered導致cache；process/current-best gate重新做。舊runner不可重啟；新runner單獨state並按07:00截止。夜間goal仍active，heartbeat尚ACTIVE。

## 01:13 新模型campaign已啟動，禁止重複啟動
新權威root C:\Users\User\Strata-Adrian-control\runs\unmapped-shadow-20261029；排程Strata-Shadow-20261029，controller PID18972/create1793207556.6678953（venv parent2684）。權威狀態campaign.json、controller.log、out/，第一階段舊controller已DONE不可重啟。已核對idle並按既有task lifecycle停止MT1 API；最新盤點只剩這個controller兩個Python PID，原API與memory-policy已退出。
47.04GB影子copy.json DONE：source/prefix SHA219ea929900dfa9ef091f3aa473fdba6874b65fcb36526d7d851ac9e95856d15，尾補640zero，shadow47,039,860,736 bytes。僅direct讀寫/hash，source大小mtime未變。
候選build/strata.exe SHA9268FAD812CB2C970D021EC7EAF29A2C6E137593A47F07BB2061F5FCBC858C42；isolated expert_source.cpp F14DE745C390B78D927A71CA8DEB3863324F5776FEACB9CB362F674F4EAA56BD。原DIAG C7F4 exe保留且舊build路徑已恢復其bytes；current-best385E…30F5與live source未修改。新source只調第一shard directhandle，嚴格path/FileId/size/任何read錯誤abort，無cached retry；env STRATA_DIRECT_SHADOW_FIRST。
進度：先BAD_PATH負例、CHK三點128tokens、OD/SD各10點診斷，再C/O/S×5輪10點512tokens。新harness在health ready後/第一request前明設並驗AboveNormal，每request再驗，沒有外部priority watcher。第三輪一致負/均值<-3%則依預登記停止，不用微基準宣告tok/s。06:50 watchdog只停自己子程序，finally原MT1復原並核對env/priority/SHA/capacity，task還有07:00時限。
工程偏差已解決：第一個shell巢狀here-string解析失敗未改source；改已保存PS腳本。PS build實際100%但ExitCode為null，wrapper誤判並還原舊exe、未保留新exe；build-recovery.json記錄證據，同source重編由既有venv Python Popen取真exit0並保存新exe。系統Python缺psutil的誤呼叫在import階段就失敗、未修改，已使用專案既有venv。沒有fallback或盲重啟模型runner。

## 01:20 修正：shadow campaign已FAILED/不適用，MT1已復原
最新應讀state/overnight-20261029/PIPELINE_NEXT.md。controller18972已terminal，不可重啟。第一BAD_PATH撞到source match gate；真正CPU來源是已存在42.91GB experts.bin，不是native GGUF。當前MT1 startup log已核對mapped view closed，KEEP_MAPPING absent，因此mapping微基準方向已在best實現，撤回影子來源收益推論。未跑任何正式C/O/S性能比較。錯誤建立的47GB自己新建shadow已單檔清理、discarded.json留證；原始模型/pack沒動。API verified=true PID32084，latest process盤點只有原API/memory-policy，舊test/build都無殘留。
下一步直接實作native GU/down pipeline。已從實際source核對並SCP pool.cpp SHA4A7AE645…650A，run_split_multi_native761..791現有全域GU/quant/downbarrier；局部code與可驗證設計在PIPELINE_NEXT.md。不重做shadow/磁碟copy/mapping微基準。夜間goal仍ACTIVE，截止07:00，heartbeat仍本thread。

## 01:38 pipeline check已通過，唯一runner仍live
PID25144/creation1793208778.8993585即時核對存活。SMOKE3點128與CHK全10點128均OK，獨立原phase reference bitwise零差異，十種實際format pair全部覆蓋（missing=[]），並確認down真與未完成GU重疊、slots3153/20.00GiB/20479MiB。現在OD/PD計時後自動進C/O/P五輪，未promote；不要重跑check或啟動第二runner。新pipeline_ms單獨combined wall，分析CPU守恆需納入，不把它當GU或加總重疊thread time。完整接續細節在PIPELINE_NEXT.md頂部更新。

## 02:28 generic pipeline五輪已DONE，不再等舊PID
唯一舊runner25144已退出，native-pipeline-20261029/campaign.json DONE/verified true/completed19，API MT1已恢復PID7724，原385 SHA+AboveNormal+capacity+env核對通過。正式150requests：C46.95884、O47.21754、P49.37278 pooledtok/s；P/C按輪+4.893% CI+1.572..8.214%，P/O+4.347% CI-1.148..9.843%。P/O按輪未滿足嚴格gate，尚不promote，不宣稱穩過50。CPU bitwise至少906,705,920 values零差異、十pair全部覆蓋；19meta/config/full logs與183總requests audit verified。
下一步讀PIPELINE_GENERIC_RESULT.md與PIPELINE_NEXT.md條件式role策略：保持worker/pin/down cap3，只P優先GU、E維持Down優先；DIAG-only每worker工作分配+CPU ID先驗假設，十pair bitwise再C/G/R受控五輪。尚未新source改動/啟動，新的root/task/state不可覆寫舊runner。Goal ACTIVE，07:00硬截止。Main source與base不同，不能直接覆寫canonical或兩個dirty tools。
