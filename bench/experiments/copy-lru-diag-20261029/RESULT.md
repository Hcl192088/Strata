[LUNA_REPORT]

# COPY_LRU_DIAG：UNCLEAR

TASK_ID：LUNA-20261012-027 continuation；TASK_SOURCE：本輪使用者直接授權；STATUS：REPORT_LOCAL。只做唯讀 SSH、既有資料離線計算及本機報告／ledger 寫入。BENCHMARK_RAW_PATH：NONE（本次未執行 benchmark）。無 build、API 呼叫／停止、程序停止、source／Git／config 修改或 GitHub 操作。

判定 **UNCLEAR**：有值得定位的 serial admission copy，但現有資料不能把 LRU copy 與 bookkeeping 拆開，亦不能確認現行 pipeline 下的可移除 wall time。單純便宜化 bookkeeping 沒有足夠證據能補上 brief 指定的約 1.2 ms/window；直接 ReadFile 到 arena 則不屬於安全的一行修改。本次不建議直接實作或宣稱可以達到 50 tok/s。

## Identity 與來源

- 本輪 SSH strict host-key／hostname：DESKTOP-LKMLUPC。engine PID31512，執行路徑 `C:\Users\User\Strata-Adrian-control\runs\native-pipe-deploy-prep-20261029\build\strata.exe`；實讀 SHA256 `A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8`，符合 brief 與本輪實讀遠端 `bench\results\2026-10-29-native-pipe\BEST.json`。
- Source root `C:\Users\User\native-pipe-generic-20261029`；HEAD 指向同名 branch，其 ref 實讀 `f520bc5e9d31c93caeb296b059e3a3eaa16e493f`；同名 tag ref 為 annotated-tag object `9150720b64607146242683d49a3ace27e7e32e37`，本次未解碼 tag object，commit 關聯依 BEST manifest。CMakeCache 的 CMAKE_HOME_DIRECTORY 指向此 source root。
- **重要核對**：遠端 `src/core/expert_source.cpp` SHA256 `2294D6B8F007A3D238EE0D68CAA77B888A4491682156B796C869EC07E6163658`，與 `state/overnight-20261029/patch_identity.json` 的 DIAG patched expert_source SHA 完全相同。以下 E 行號均指該遠端檔；D 指本機 `state/overnight-20261029/patched/expert_source.cpp`，兩者檔案內容相同。計時器映射不是依相似程式碼猜測。
- 數據來源是 **pre-pipeline** Hermes DIAG：`state/overnight-20261029/{phase_analysis.json,phases.json,rows.json,prepare_diag.py,analyze_phase.py}`，不是部署後重新量測。既有 join 結論沿用 `state/ssd-join-bound-20261029/RESULT.md`，不重做 trace／oracle。
- 每次後續遠端讀取前重新列 process；只見已分類的 memory-policy --run／--watch、serve.server 的 venv/base pairs 與單一 engine，沒有所列名稱範圍內的額外 Strata/Luna/build/benchmark。未停止任何程序。無 Git status 操作，未全面驗證 worktree dirty 狀態；只核對目標 source hash 與 HEAD，不宣稱全樹乾淨。

## Q1：lru_ms 計時內容與 critical path

`prepare_diag.py` 將 PhaseTimer 包在 ram_lru_complete 呼叫周圍；實際 D/E:4152–4155，4153 建構開始、4155 離開 scope 解構停止。steady_clock 起點在 D/E:81–82，終點與 relaxed atomic 累加在 :84；enabled 判斷 :87–88。不是函式內某一段 memcpy 的專屬計時器，包含整個 ram_lru_complete（含 early return、檢查和偶發列印），不包含外層 dynamic_cast。

它由 decode 的 dispatch 呼叫執行緒同步執行，不是 MissIo helper 或 pool worker。同步 expert compute 在 E:4084–4089，helper join 在 :4090；LRU 在 :4152–4155，c4 才在 :4156，`d.ms_run += ms(c3,c4)+mo_ms` 在 :4162。因此位於 CPU-per-layer 的 run timer 內，serial 在 expert compute 後、返回下一層前。它不是 ready/helper overlap 的一部分；GPU 可能仍有其他工作，但不能因此將這段從 host decode path 排除。

舊 DIAG 的 weighted LRU **1.195714 ms/w**，CPU **24.496452 ms/w**；來源 phase_analysis。這是量得的 serial interval，不等於整機 wall time 必然可省同額。

## Q2：LRU 逐項拆解與 scaling

E:3370–3420 是完整實作：

- :3372–3377：開關、參數驗證、遞增 clock、計算 layer base。
- :3378–3382：掃 routed entries，對已 resident 且非 tail-skip 者更新陣列時間戳。成本隨 routed entries 數量；重複 expert 也會走訪。
- :3383–3386：保護 GPU-resident、override 與 staged adaptive exchange 的 in/out；使用陣列查詢及 staged_ 線性掃描。
- :3388–3405：逐 CPU entry 嘗試 admission；已 resident／protected 跳過。每個需 admission 的 expert 掃同層所有 candidate，對候選再掃 routed ids，排除當前正在使用者，找最舊 timestamp。成本隨 admission 次數、同層 expert 數、routed entry 數及 staged exchange 數增長。重複 incoming 在首次成功後會被 resident 檢查去重；no-victim 可能重掃。
- :3406–3415：容量界限檢查；**jobs[job].blob → complement_host_+victim offset 的完整 expert memcpy**；可選 parity memcmp；改 offsets ownership、touch、admission 與 copy-byte counters。copy 隨實際 admitted bytes，不嚴格等於 SSD bytes：stage reuse、protected/no-victim 或 admission skip 可使兩者不同。
- :3417–3420：低頻 stderr 統計列印。live config 實讀 RAM_LRU=1、RAM_LRU_CHECK=0，因此設定上沒有額外 memcmp；本輪未讀 process 的 inherited environment block。

此 LRU 函式內**沒有 hash/map、linked-list 維護或 mutex lock**。resident_blob（E:3206–3208）在未啟用 exchange storage 時走 complement offsets helper；不能把 stage_of_ 的 hash 查找或 stage_mu_ 算進 lru_ms。那兩項出現在 stage claim（E:1236–1239、1476–1487），在其他計時範圍。

Page faults／first touch 沒有獨立 counter。arena 初始化已逐 layer 填入（E:3029–3055；3037 以 read_direct 填 batch），故不能把每次 admission 都說成全新頁 first touch。pageable arena 在記憶體壓力下仍可能有 fault；stage source／destination 的 cache miss、TLB、memory bandwidth 和排程延遲都可能包含在 memcpy wall time。沒有 fault trace，不能定量歸因；也未量出 bookkeeping/memcpy 各自時間。

下表由本次 `analyze.py` 重算：30 個 D rows 與 30 phases 按原順序配對並逐筆確認 windows；每題三輪按 windows 加權。MB 是十進位 useful SSD bytes；SSD experts 是 decode-only m_file_blobs。CPU experts/layer-w 是 rows 既有四捨五入欄位再加權，用於 routed-compute 規模代理，並非精確 distinct routed union 或 admission 數。

|題|windows|SSD MB/w|SSD experts/w|CPU experts/layer-w|lru ms/w|copy ms/w|
|---|---:|---:|---:|---:|---:|---:|
|p01|123|58.625|31.439|7.820|2.9421|4.3053|
|p02|84|14.461|7.750|6.090|0.6999|1.0438|
|p03|138|45.978|25.413|7.990|2.2858|3.4999|
|p04|253|30.253|16.636|6.309|1.4967|2.1415|
|p05|826|14.844|8.113|5.205|0.7561|1.0572|
|p06|246|30.555|16.837|6.700|1.5361|2.2632|
|p07|161|28.731|15.478|6.784|1.3956|2.0558|
|p08|290|21.148|11.452|6.203|1.0911|1.4888|
|p09|239|22.350|11.649|5.654|1.0829|1.5205|
|p10|478|20.220|10.845|6.164|0.9964|1.4087|

十題等權、帶截距單變量 OLS（詳 analysis.json）：LRU 對 SSD MB/w 的 slope **0.050178 ms/MB**、intercept **−0.012659 ms/w**、R² **0.998888**；對 SSD experts/w 的 R² **0.997977**；對 CPU experts/layer-w 的 R² **0.811117**。copy 對 MB、SSD experts、CPU experts 的 R² 分別 **0.997132／0.998639／0.840313**。SSD bytes 與 SSD expert 數本身 R² **0.998600**，所以只能說 miss/admission 規模比全部 CPU compute expert 規模更吻合，**不能區分 bytes 主導或每次 admission 掃描主導**，更不能把負截距當作負 bookkeeping 或零 bookkeeping 的證明。這是十個 aggregate point 的關聯，非逐 window 因果回歸。

## Q3：copy_ms 的資料流、執行緒與可避免性

Windows direct 路徑為：GGUF 檔案 role ranges → ReadFile 到 thread-local aligned scratch `sc.buf` → 拼接有效 bytes 到 stage buffer → CPU kernels 直接讀 job.blob → admission 再複製到固定 RAM arena。

- E:1834–1859：thread-local Scratch；:1861–1879：一個 blob 的 role windows 與輸出 at；:1882–1910：按檔案位置排序／合併讀取；:1911–1915：VirtualAlloc scratch。
- :1933–1949 是 issue_wait timer，ReadFile 寫 `sc.buf+r.pos`（:1940），等待 GetOverlappedResult（:1948）。
- **copy_ms 起點 :1951，scope 終點 :1958 前**（return :1957 時解構）；:1952–1955 含 short-read 檢查及 `memcpy(x.dst+x.at, sc.buf+...+skip, x.n)`。dst 來自 prefetch_split 的 stage_buf（:1487），不是 arena，也不是另造 compute buffer。
- stage publish 在 :1548，CPU job.blob 直接取 source blob（:4062、4073）。arena copy 是 :3409，計入 lru_ms，**不計入 copy_ms**。
- 一般 overlapped miss 由 MissIo thread 執行 :3701；主 decode 計算 ready experts（:4019），再 join（:4023）。若沒有 ready expert，主 decode inline read（:3999–4000）；大批 fill_many 還可由最多四個執行緒分攤（:1533–1557）。所以 copy counter 是多 thread 呼叫累計，不是全部 decode wall time，不能與 LRU 相加當實測加速。

把 ReadFile 直接改成 arena destination **不安全且不能一律免 copy**。目前 code 用 FILE_FLAG_NO_BUFFERING|OVERLAPPED（E:1610），以 kSector=4096 做 offset/size rounding（:1841、1867、1877）；scratch 保證對齊且容納 skip、padding、merged gaps。最終 blob 是數個 role 的緊密拼接，而檔案 role offsets、dst+at、arena slot stride 未在本次逐一驗證 sector 對齊；直接讀對齊外圍會覆蓋相鄰 blob／role。保留 merging 也不能將一個連續 ReadFile 散寫到數個 arena slot。現有數據不是 Windows 磁碟實際 sector-size 查驗。

此外 victim 必須在 read 開始前 reservation，而目前選擇在同步 CPU compute 完成後才做，排除 routed/GPU/override/staged exchange。提前覆寫可能破壞 ready job 的 pointer、GPU DMA 或 adaptive copy；失敗時還需避免把未完成 bytes publish 成 resident。stage 還服務異步 CUDA 讀取，已有事件保護（E:1301–1309）。不能只換 pointer 或提前 offsets swap。

較小的資料流候選是**保留 aligned scratch，將 scratch scatter 的目的地改成已預留且安全的 arena slot**，讓 pending CPU job 直接讀該 slot，省掉後續 stage→arena copy；這保留 copy_ms 類型的拼接 copy，只消除 LRU admission copy。仍需 reservation／成功 publish／失敗處理及 stage consumers 契約，並不是本次已驗證可行的 patch。另一種 stage/arena 指標交換會改固定 arena 和 pinned/device ownership，範圍更大，不列為最小修改。

## Q4：可移除上限與 1.2 ms/w

以下是舊 pre-pipeline DIAG 的 accounting bounds，**不是 current live 的 measured speedup**；假設其他工作、route、快取狀態和 I/O 不變，沒有資源競爭的連帶收益：

|目標|量得 interval|critical-path 可移除量的樂觀上限|
|---|---:|---|
|scratch→stage copy_ms 全部消除|1.716546 ms/w（重疊 thread 累計）|0 至最多 1.716546 ms/w；只在未遮蔽／inline 部分才直接省時間，無 per-event timeline 無法收窄|
|stage→arena admission copy 全部消除|未單獨計時|不超過整段 LRU **1.195714 ms/w**；其中還含不可省的 bookkeeping，實際 copy 可省量更低|
|便宜化 LRU bookkeeping、保留 bytes copy|未單獨計時|同樣不超過 **1.195714 ms/w**，但不能將整段視作 bookkeeping；無證據給更緊的量化值|
|兩段 copy 與整段 LRU 都理想消除|非實測|粗鬆總 accounting ceiling **2.912260 ms/w**；LRU copy 與 bookkeeping 共用同一上限，不能重複計入|

phase_analysis 的 join **6.090162 ms/w** 足以容納 copy_ms 的上限，但不代表所有 copy 都暴露在 join；helper **9.663324**、direct **9.749506**、ready **4.168051 ms/w** 是不同重疊區間，不能用平均值重建逐事件 slack。多 thread counter 累計及不完全遮蔽會使 copy_ms 高於實際可省的 wall time。

brief 的 1.2 ms/w 是給定目標，非本次重測。整個舊 LRU interval 已略低於它；所以只改 bookkeeping 或只去掉 admission copy，依這份資料均無法保證補足差距。scratch→stage 的樂觀上限超過目標，但安全免除該 copy 的條件和暴露比例未確認。跨兩段的合併方案只有鬆上限超標，不能當作值得上線的證明。

## Q5：最小下一步與必要驗證（僅描述，未實作）

優先補最小診斷拆分：ram_lru_complete 內分別記錄 victim search／protection scan、memcpy、可選 check、admitted bytes/count、no-victim；並依 layer-window 記 helper copy 與 ready/join 邊界，保留 DIAG-off 的正式速度臂。這才能判斷是改 bookkeeping 還是改資料流；本次未授權新執行，沒有啟動它。

若 bookkeeping 確實可觀，最小改動是每個 layer-call 先建 routed/protected membership，避免每個 candidate 重掃 ids/staged_；保留同層 timestamp、victim tie order、admission 順序及 no-victim 語意，不加 linked list 或新 cache policy。風險是重複 routes、tail-skip、同一次呼叫多 admission 更新造成選擇不同。

若 admission copy 才主導，才考慮 Q3 的 scratch→預留 arena scatter：主執行緒先選與保護 victims，helper 僅填 bytes，完成同步後一次 publish offsets；pending jobs 使用最終位置。必須驗證 routed exclusions、GPU/adaptive pending DMA、stage event lifetime、失敗／short read 不發布、同層容量及 pointer lifetime。若 sector/role layout 不適用 direct ReadFile，就不宣稱它可直接免拼接 copy；本次沒有採用任何 fallback。

Correctness 要比對逐 expert bytes、offset ownership、victim/admission 序列、duplicate/tail-skip/protected/no-victim 情境；涵蓋所有實際 native format/role sizes、並行 ready/pending、adaptive exchange 及 read failure。既有 RAM_LRU_CHECK 只驗證 memcpy 後 bytes（E:3410），不足以證明提前 reservation 無 race。再做既有 CPU row bitwise reference 與生成 smoke；不能只看文字正常。

A/B 必須另獲執行授權：先重新 process gate、核對 current-best A1E6 binary/source/config；isolated candidate 與同日 best，以相同 Hermes points、sampling（溫度不改）、workers/affinity、容量、cache 初態、window accounting 交錯配對。正式速度 DIAG-off，診斷另列；報告 paired decode rate、ms/window、tokens/window、copy/LRU components、miss/admission bytes/count 及不確定性，避免路由 mix 差異當作因果。先寫 gate 再跑，不以本次上限作採用 gate。

## Coverage 與未確認項目

完整讀取本機 prepare_diag/analyze_phase、phase_analysis、patch_identity；rows/phases 全部 D 配對資料由程式完整解析，十題全部納入，完整既有 join 報告供上下文。遠端讀兩份 AGENTS、指定 source 關鍵區段、process 篩選、binary hash、Git HEAD/ref/tag-ref 檔、CMake source pin、BEST manifest 與 active config；source 為關鍵區段檢查，不是全 repo audit。較長輸出保存在 remote-index.txt、source-evidence.txt、additional-evidence.txt；console 截斷未視作已閱讀，對結論相關的被截區段另以本機證據檔篩選讀回。未讀模型 payload／大型歷史 logs，未新下載整 repo、未掃全部遠端磁碟，未做 API probe。

剩餘盲點：當前 pipeline 實測 phase、實際 admission bytes/time split、fault counters、逐事件暴露 copy、實際 sector/role/slot alignment、完整 worktree dirty 與 tag-object 解碼、process inherited env、非篩選名稱下的其他 GPU/RAM 使用者。故不宣稱全機無干擾或可省 1.2 ms/w。`D:\strata\.git` 不存在，本次不建立 Git repository，依任務禁止 GitHub，不 commit/push。
