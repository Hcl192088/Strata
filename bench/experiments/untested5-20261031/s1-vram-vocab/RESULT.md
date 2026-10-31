STATUS: INCOMPLETE Part A 引擎啟動與 allocation 逐項盤點；Part B trace 分析、字表、coverage 與 A/B；Part C 啟動 log 核對及排程 token 確認

## S1.3 單次啟動與 allocation 搜尋（部分完成）
- strict host-key SSH 核對 DESKTOP-LKMLUPC；啟動前程序篩選未列出 Strata、Python、build、診斷程序或工作集超過 1 GiB 程序，S3 排程 Ready；binary SHA256 A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8，設定 SHA256 060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93。
- 以現行設定參數及環境直接啟動一次 --serve，沒有 API 或請求；READY 後擷取 nvidia-smi，送 QUIT，exit code 0。GPU 使用由 558 MiB 變為 11547 MiB（全 GPU 總量，差值 10989 MiB，包含其他背景變動）。引擎 INFO 為 3153 slots、expert cache 5245 MiB、arena 20479 MiB；啟動 log 記載 verify buffers 69.8 MiB、draft head 178.4 MiB、MTP layer 820 MiB。結束後未見 strata.exe 或 serve.server，API 排程 Ready。
- 原始檔案位於遠端 `C:\Users\User\Strata-Adrian-control\runs\untested5-20261031\s1\startup-stderr.log`、`startup-stdout.log`、`startup-before.txt`、`startup-after.txt`、`startup-exit.txt`；控制腳本 `s1-vram-vocab\startup_once.py`。啟動 log 未找到 large-page 字樣；page-locking refused 是不同訊息，不能推論 large-page 結果。
- 唯讀掃描 current-best source 的 src 內 .cu/.cpp/.cuh/.h 的 cudaMalloc、cudaMallocAsync、cuBLAS workspace，476 筆搜尋命中已保存遠端 `s1\alloc-search.txt`，包含註解與非活動測試；僅抽查部分 MTP、verify、cache、prefill 項目，未完成逐項大小、活躍路徑及 flag 表，未估算 CUDA/WDDM overhead，S1.3 不可勾選。未執行 S1.4 及後續步驟。

# S1 已完成紀錄

## 身分與程序 gate
- 2026-10-31 本輪以 strict host-key SSH 驗證 hostname `DESKTOP-LKMLUPC`，登入帳號 `desktop-lkmlupc\user`。
- current-best binary `C:\Users\User\Strata-Adrian-control\runs\native-pipe-deploy-prep-20261029\build\strata.exe` SHA256 `A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8`，與 COMMON 指定值相同。
- source worktree `C:\Users\User\native-pipe-generic-20261029` HEAD `f520bc5e9d31c93caeb296b059e3a3eaa16e493f`，`git status --short` 無輸出；已讀遠端主工作區 AGENTS.md。
- 本輪 Win32_Process 篩選名稱 strata、python、cmake、ninja、nsys、luna、cl.exe 或工作集大於 1 GiB，未列出符合程序；API 排程 `Strata-Task020-API` 為 Ready。nvidia-smi GPU 程序列表有桌面及其他背景程式，未停止任何程序。這是盤點時狀態，後續每次操作前須重新盤點。
- API 未啟動；排程 Ready 且程序篩選無 strata/python。未執行 benchmark，未修改溫度、遠端 source 或 OS 權限。

## Part A
未執行完整 allocation 盤點及本次引擎啟動。歷史唯讀 inventory `D:\strata\state\vram-inventory-20261029\RESULT.md` 指出 draft head 178.4 MiB、verify buffers 69.8 MiB，約 930 MiB 未歸屬；這些是舊資料，並非本輪測量，也不能代替要求的逐項分解。舊資料指出 `STRATA_MTP_FULL_HEAD=1` 可省 draft head 約 178.4 MiB，但是否符合本次 A/B arm 與使用者要求的相同 env 尚須核實，不能視為已確認結果。

## Part B
遠端 `C:\Users\User\Strata-Adrian-control\runs\gpu-bw-nsys-20261030\trace2.sqlite` 存在，大小 824156160 bytes，尚未執行要求的 draft kernel 拆解。現有 trace 歷史報告只提供整體 draft 2.16 ms/window，不提供 draft head 與其餘 draft 的拆分，不能代替要求的分析。尚未產生 V32/V64、計算 coverage 或執行 A/B，因此沒有速度或輸出一致性結論。

## Part C
本輪以 SSH 登入帳號執行 `whoami /priv`，輸出清單沒有 `SeLockMemoryPrivilege`。API 排程 principal 為 `User`、Interactive、Limited；排程實際 token 尚未核對，因此不能宣稱兩個 token 一致。先前嘗試檢查指定舊 log 未找到 large-page 訊息；本輪未重新核對啟動 log。source `src/core/pinned.cu:68-109` 確有嘗試及 refused/skipped 訊息邏輯；未更動權限。

## Coverage 與續作
完整驗證範圍僅限上述 binary SHA、source HEAD/dirty、SSH token privilege、程序篩選與 API 排程狀態；未完整檢查所有 GPU allocation、既有 log、字表與 trace kernels。824 MB trace 僅確認存在，未掃描。Part A 全部量測、Part B 全部數據與 Part C 引擎啟動訊息仍未完成。下次先重新執行 process gate、current-best identity 與 effective config 核對，再依 BRIEF 與 COMMON 繼續；不得將此紀錄當作完成報告。

## 本次續作補充（2026-10-31 00:26，台北）
- 再次以 strict host-key SSH 確認 `DESKTOP-LKMLUPC`；binary SHA256 仍為 `A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8`。當次程序篩選未列出 strata、python、build、nsys 或工作集超過 1 GiB 的程序；nvidia-smi 為 558 MiB，排程 `Strata-Task020-API` 為 Ready。這只是檢查當下狀態，操作前仍須重查。
- 直接檢查遠端 current-best source `src/core/mtp.cpp:637-656`：字表必須至少 4 bytes 且長度為 4 的倍數；每 4 bytes 一個 token ID，GPU 上另配置字表原始 bytes 與 `token數 × head row_bytes` 的 draft head，並依字表順序 gather。這段讀取本身沒有看到排序或 32K/64K 對齊要求；尚未完整檢查其他呼叫路徑，不能推論沒有其他限制。`tools/draft_vocab.py` 使用 int32 並保留 base ID 次序。
- 唯讀掃描既有 `runs/gpu6-ab-20261030/out` 下的 engine.log，沒有找到 `large pages` 或 `large.page` 字串；新啟動記錄尚未取得。`STRATA_MTP_FULL_HEAD=1` 是 source 中的診斷模式，改變 draft head，不足以直接判定符合此任務要求的「輸出與 draft window 不變」arm。
- 本次續作只檢視 allocation 搜尋結果的前 100 筆，輸出亦截斷，包含測試及非活動檔案；並非完整清單。未處理 824 MB SQLite trace，未建立字表或執行 A/B，也未啟動引擎。所有 Part A/B 的量測與 Part C 的引擎啟動訊息仍待完成。

## 本次續作補充（2026-10-31，attempt 3）
- 重新以 strict host-key SSH 確認 `DESKTOP-LKMLUPC`；A1E6 binary SHA256 仍一致。當次 Win32_Process 篩選 strata、python、cmake、ninja、nsys、luna、cl.exe 與工作集 >1 GiB，未列出符合程序；API 排程 Ready，nvidia-smi 558 MiB。此為檢查當下狀態，之後操作前仍需重查；沒有啟動或停止任何進程。
- build 的 CMake cache 確認來源 `C:/Users/User/native-pipe-generic-20261029`；`generate.cpp` 實際位於 `src/program/`。
- 唯讀檢查 deploy-prep 中保存的 `candidate-live.json`：`--spec 6 --suffix-draft 3 --mtp-max-t 3`。此檔為保存的候選設定，尚未重新比對目前受控 live config hash，不應單獨當成目前有效設定。
- `src/program/generate.cpp:8846` 指出 MTP 視窗受 `mtp_max_t` 限制，但 suffix 可使用高至 `S` 的視窗；`2407-2414` 亦有調整 spec 的邏輯。因此不能只因 MTP cap 為 3 就認定將 spec 從 6 降低不會改變 tokens/window；該 arm 尚未符合納入條件。
- 再次執行 SSH 帳號 `whoami /priv`，清單中沒有 SeLockMemoryPrivilege；排程帳號實際 token 與新 engine startup large-page 訊息仍未驗證。舊 gpu6 harness 的 controller 明確有 stop/restore API 步驟；必須依 COMMON 改成保持 API 未啟動的專用控制器，不能直接執行原 controller。
- 本輪沒有啟動 engine、分析 SQLite、建立字表、執行 A/B 或取得 slots，因此 Part A/B/C 仍未完成。既有 trace、字表與分配清單仍未完整掃描；不得將本段記錄視為實測結果。

## 本次續作補充（2026-10-31 00:29，attempt 4）
- 重新透過 strict host-key SSH 驗證 `DESKTOP-LKMLUPC`；A1E6 binary SHA256 符合 COMMON。程序篩選未列出 strata、python、cmake、ninja、nsys、luna、cl.exe 或工作集大於 1 GiB 的程序；API 排程 Ready，GPU 558 MiB。此為當次快照，後續操作前仍須重新盤點。
- 已讀取 `tools/STRATA_GITHUB_AUTO_HANDOFF.md` 及既有 gpu6 controller；後者含 stop/restore API，不可直接執行。
- 對遠端 824 MB SQLite 唯讀檢查 schema：有 `CUPTI_ACTIVITY_KIND_KERNEL`，沒有 `NVTX_EVENTS` 資料表；StringIds 中以 mtp/draft 搜尋只辨識出 `mtp_select_kernel`。因此不能直接靠 NVTX 或名稱把 draft head 與其他 kernel 歸類；仍需比對 kernel 呼叫與 trace 的 grid、順序或其他可證明的欄位，不得把全部 Q5 kernel 當成 draft head。
- 這次未啟動 engine、未建立字表或執行 A/B；Part A/B/C 未完成，沒有新的速度或 VRAM 結論。trace 只檢查 schema 與名稱，並非完整 kernel 分析。尚需 engine startup、allocation 盤點、trace 拆解、字表與 coverage、A/B、large-page log 和最終 API 狀態核對。

## 本次續作補充（2026-10-31 00:31，attempt 5）
- strict host-key SSH 取得 hostname `DESKTOP-LKMLUPC`；重新確認 current-best executable SHA256 `A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8`，與 COMMON 及遠端 BEST.json 一致。實際受控設定 `C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\server-task020-8080-v0142-s2k-mt1.json` SHA256 `060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93` 亦一致；BEST.json 的設定列有 `--spec 6 --suffix-draft 3 --mtp-max-t 3`。
- 當次 Win32_Process 篩選 strata、python、cmake、ninja、nsys、luna、cl.exe 與工作集超過 1 GiB 無符合結果；API 排程 Ready，GPU 使用 558 MiB。未啟動引擎或 API，也未停止程序。這只代表檢查當下，操作前須重查。
- 既有 `runs\miss-overlap-20261027\s2k-mt1-api.engine.log` 有 `page-locking refused (out of memory)`，例如第 15659 行；這是 page-locking 訊息，不足以判定 large-page 嘗試結果。source `src/core/pinned.cu:68-109` 顯示 large-page 路徑另有 refused/skipped 訊息；新啟動訊息仍未取得。
- 既有 gpu6 controller 的 stop/restore API 與 COMMON 相衝突，不能原樣執行；必須在本 stage 建立專用控制流程並維持 API 未啟動。遠端 `BEST.json` 歷史 slots 3153、arena 20479 MiB 是舊驗證，並非本次量測。
- 本次未掃描 824 MB trace 或完整 allocation；沒有建立字表、啟動引擎、執行 A/B。仍須完成首行所列全部項目，並驗證結束時 API 未運行。遠端沒有本次建立的 controller 或正在運行的 benchmark。

## 第 6 次續作補充
- 以 strict host-key SSH 確認遠端 hostname `DESKTOP-LKMLUPC`、binary SHA256 `A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8`，API 排程 Ready；遠端篩選無 strata、python、cmake、ninja、nsys、luna、cl.exe 或工作集大於 1 GiB 的程序。GPU 清單為桌面、ASUS、Razer、LG、Edge WebView 與 Riot Vanguard 等程式；未停止任何程序。上述為檢查當下快照，後續操作仍須重做 process gate。
- 第一次 shell 命令引號解析錯誤，部分命令落在本機，該輸出不作遠端證據；已用 PowerShell EncodedCommand 成功重查。
- 實際 config 顯示 `--spec 6 --suffix-draft 3 --mtp-max-t 3`；完整 env 包含 `STRATA_IQ3S_MT1=1`、`STRATA_NATIVE_PIPE=1`。未再修改或調整溫度。
- 遠端 `big-exact-20261030/harness/replay_ab_20261027.py:145-158` 針對 current-best binary 無條件把 slots gate 固定為 3153，因此 V64/V32 預期釋放 VRAM 所增加的 slots 會被誤判；新控制器必須只對 C 固定 3153，所有組仍檢查 20.00 GiB / 20479 MiB，且不能呼叫原 controller 的 stop/restore API。尚未建立控制器或執行實驗。
- 遠端 `tools/draft_vocab.py` 確認 corpus 以 tokenizer 編碼後按頻率排序並以 token ID 打破平手；base 次序保留。於 `Strata-Adrian-control/runs` 遞迴找到 `mtp-fixed-20261014` 等少量 `.tokens`，其來源與格式尚未驗證，尚未選作語料；未建立字表。
- 對三個既有 runs 目錄遞迴搜尋 large-page 文字找到 source 副本下的其他系統歷史 log，包括 Windows VirtualAlloc error 1314，但這不是本遠端 current-best 啟動證據，不可用來宣稱本機 engine 嘗試結果。搜尋輸出限制前 20 筆且包含非活動 source 子樹，並非完整有效 log 盤點。
- 本次未啟動 engine 或 API，未做新 nsys、trace kernel 分類、allocation 全掃描、coverage 或 benchmark。結束時 API 排程 Ready 的證據是本次前檢；沒有執行會啟動 API 的操作，但未做最終獨立再次核對。首行所列項目全部仍待完成。

## 第 7 次續作補充
- strict host-key SSH 確認 hostname `DESKTOP-LKMLUPC`，current-best binary SHA256 `A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8`；篩選無 strata、python、cmake、ninja、nsys、luna、cl.exe 或工作集超過 1 GiB 的程序。API 排程最後確認為 Ready，未啟動 API 或引擎。上述為當時快照，後續操作須重新執行 process gate。
- 唯讀取得實際 config：`--spec 6 --suffix-draft 3 --mtp-max-t 3 --resident-budget-gib 20`，`STRATA_IQ3S_MT1=1`、`STRATA_NATIVE_PIPE=1`；既有 controller 含停止與恢復 API 行為，不可直接執行。
- 唯讀查詢遠端 824 MB trace 的完整 kernel table，依 kernel 名稱及 grid 分組：`native_q5_k_mmvq_kernel` 的 `gridX=106299, gridY=1, blockX=32` 與 draft 字表列數一致，是 draft head 的候選；全 trace 433 次合計 173.855240 ms。原 `result2.json` 的最後 PP 到 DONE 時間區間內為 431 次、173.062682 ms；以既有 292 windows 換算為 0.59268 ms/window。這是依 grid 維度辨識的候選，尚須對照 source kernel launch 證實，亦尚未拆出 draft layer、MoE 的時間，因此不是完整 Part B 結論。SQL 查詢完整掃描 kernel table，並非 GPU metrics 或全 trace 所有表的完整分析。
- 上述 SQL 首次因 Python raw 字串尾部反斜線語法錯誤失敗，已修正後成功；未改遠端檔案。未建立字表或控制器、未執行 benchmark，未完成 Part A/C 啟動記錄，也無 A/B 結論。仍須核對 source 對應、完成 allocation/啟動/large-page、字表與 coverage、A/B，以及最終 API 狀態。

## 第 8 次續作補充
- 重新以 strict host-key SSH 確認 `DESKTOP-LKMLUPC` 與 `desktop-lkmlupc\user`；current-best binary SHA256 為 `A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8`，符合 COMMON。程序篩選沒有 strata、python、cmake、ninja、nsys、luna、cl.exe 或工作集大於 1 GiB 的項目；API 排程 Ready。GPU 列出桌面與背景程式，WDDM 未提供各程序 VRAM；未停止任何程序。這是檢查時快照。
- 讀取 `big-exact-20261030/base.py`：其 `run` 與現有 replay harness 可提供每個 block 的量測，但 `verify` 要求 API 運行，`main` 會停止及恢復 API，不能照原樣使用。`make_body` 保留原始 sampling；不得修改溫度。
- 字表工具的 `corpus_counts` 將 UTF-8 語料用 GGUF tokenizer 編碼、`covering` 按頻率降序與 token ID 排序；現有工具的 `--corpus` 只擴充 base，不能直接產生本任務所需縮小字表。尚須建立專用選取流程、核對特殊 token 與非 Hermes 語料來源，再測 coverage。
- 本機 `D:\strata` 不是 Git repository，故沒有 commit 或 push。本輪沒有啟動引擎或 API、建立字表、執行 benchmark，也沒有更動遠端設定或 source。Part A、B、C 仍未完成；前述 API Ready 為本輪檢查結果，非獨立的結束後檢查。

## 本次續作補充（2026-10-31，process 與身分複核）
- strict host-key SSH 確認 `DESKTOP-LKMLUPC`，binary SHA256 仍為 `A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8`。遠端依 strata、python、cmake、ninja、nsys、luna、cl.exe 與工作集 >1 GiB 篩選，沒有符合程序；API 排程為 Ready。GPU 程序清單為 Windows 桌面與背景程序，WDDM 未提供程序 VRAM。這是當次快照，後續遠端操作前仍須重新盤點。
- 再次核對原 gpu6 controller：會停止及恢復 API，不能原樣執行；本次未建立替代控制器。遠端 shell 沒有 `rg`，本輪 allocation 搜尋因此失敗，沒有取得完整盤點。
- SSH 登入 token 的 `whoami /priv` 清單再次未出現 `SeLockMemoryPrivilege`；排程實際 token 與本次 engine 啟動 log 仍未確認。未改權限，未啟動或停止 engine/API，亦未執行 benchmark。
- 仍待 Part A 完整 allocation、單次啟動與 VRAM；Part B trace 分類、字表及 coverage、A/B；Part C 啟動訊息與排程 token；最終 API 狀態獨立複核。未新建遠端控制器，沒有本輪背景 benchmark。以上核對不等於完成。

## 本次續作補充（2026-10-31，source 對照）
- strict host-key SSH 再確認 hostname DESKTOP-LKMLUPC；current-best binary SHA256 為 A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8。當次程序篩選無 strata、python、cmake、ninja、nsys、luna、cl.exe 或工作集超過 1 GiB 的程序；API 排程 Ready。GPU 程序為桌面及背景應用，WDDM 未提供逐程序 VRAM。此為檢查當下快照，後續操作前須重做 gate。
- source `src/core/mtp.cpp:977-980` 的 draft head 呼叫 `native_mmvq`，輸出列數為 `n_dvocab_`；`src/kernels/cuda/native_mmvq.cu:2122` 的非特例 Q5 kernel launch grid 為 `n_out`。因此先前 trace 的 Q5 gridX=106299 與 draft head 相符；仍須檢查特例條件與其他同維度呼叫才能完全排除誤分類。先前 trace 窗口區間 431 次、173.062682 ms，除以 292 為候選 0.59268 ms/window；其餘 draft kernel 尚未拆解。
- 唯讀掃描 src 原始碼的指定符號，找到 graph instantiate（`src/core/graph.cpp:65`、`mtp.cpp:1019`、`session.cpp:253,899`、`verify.cpp:1899,2568,2575`）與 cuBLAS workspace（`src/prefill/gemm.cu:406,420,446`）。此為符號搜尋而非 allocation 完整盤點，未計算大小或確認各路徑是否啟用。
- 本次未啟動引擎或 API、未產生字表、未執行 benchmark；Part A、B、C 與最終 API 獨立核驗仍待完成。尚未建立遠端 controller。不得將 source 位置或歷史 trace 候選數字誤報為實際本輪量測。

## 本次續作補充（attempt 5）
- strict host-key SSH 再次核對 hostname DESKTOP-LKMLUPC，A1E6 binary SHA256 一致；Strata-Task020-API 排程為 Ready，依 strata、python、cmake、ninja、nsys、luna、cl.exe 與工作集 > 1 GiB 篩選未見符合程序。nvidia-smi 顯示桌面與背景程序，WDDM 未提供逐程序 VRAM；沒有停止任何程序。以上是檢查當下的狀態，不取代後續操作前的程序 gate。
- 檢視遠端 replay_ab_20261027.py：run_block 使用 serve.server 建立 API，且容量 gate 對 current-best exe 強制 slots=3153；不能直接用它完成 Part A 要求的無 API 單次啟動，也不能直接用於 slots 增加的 V32/V64 arms。尚未建立專用控制器。
- 本次沒有啟動引擎、建立字表或執行 A/B；Part A/B/C 及最終 API 狀態獨立核驗仍未完成。所有既有未完成事項維持首行 INCOMPLETE，不能宣稱測試成功。

## 本次續作補充（attempt 6）
- strict host-key SSH 確認 DESKTOP-LKMLUPC；current-best binary SHA256 為 A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8。啟動前篩選未見 strata、python、cmake、ninja、nsys、luna、cl.exe 或工作集超過 1 GiB 程序；API 排程 Ready，GPU 使用量 558 MiB。結束時重新篩選同樣沒有上述程序，API 排程 Ready；沒有啟動或停止任何程序。
- 重新檢查實際設定及 `mtp.cpp`：STRATA_MTP_FULL_HEAD=1 會跳過子字表 head 配置並改用完整 head，改變 draft 候選與 acceptance；尚未完成 Part A 全面盤點，不能據此宣稱此 arm 符合本 brief 的條件。子字表的 GPU 配置明確為 ID 數 × 4 bytes，加上 ID 數 × head row_bytes（mtp.cpp:637-654）。另有 state_arena（338-349）、buffer arena（409-410）及 sampler scratch 等配置（515-530）；尚未計算 live 配置數值，不能當成完整 allocation 表。
- 發現 `runs\mtp-fixed-20261014\pooled-reference.tokens` 與 `stream-reference.tokens` 是逗號分隔的 token ID；其 identity.json 指向 2026-10-14 舊執行檔，沒有證明與本次 Hermes p01–p10 輸出無關，故尚未採用作頻率語料。其他同名檔案可能重複，未逐一比對；未建立 V32/V64。
- 已確認原 replay 的 run_block 啟動 serve.server，並要求 API health；Part A 要求無 API 單次啟動，不能直接使用。既有 controller 另會停止與恢復 API，且 current-best 的 slots gate 固定 3153；尚未建立替代控制器。
- 本輪僅檢視指定 source 符號與六個候選 `.tokens` 路徑、兩個 token 檔中的一個及其 identity；並非 allocation、語料或 824 MB trace 的完整掃描。未啟動 engine、未產生新 trace、字表或 A/B 資料。首行所列步驟仍待執行；不可視為完成或 benchmark 結論。

## 本次續作：process gate（2026-10-31 00:51 台北）
- strict host-key SSH 驗證 hostname `DESKTOP-LKMLUPC`；current-best binary SHA256 `A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8`，符合 COMMON。
- 遠端程序盤點發現 PID 27532，`cmake.exe`，command line `cmake --build "C:\Users\User\Strata-Adrian-control\runs\s3-mtp-experts-20261031\build" --target strata -j 2`，屬 S3 建置；依 process gate 停止 S1 遠端操作，未停止該程序，也未啟動 S1 engine 或 benchmark。此程序不符合可逕行處理之 stale/orphan 已確認條件。
- 同一時間 API 排程 `Strata-Task020-API` 為 Ready；程序篩選未列出 strata 或 python。GPU 使用 591 MiB，程序表列桌面及背景應用，WDDM 未提供逐程序 VRAM。這是當時快照，續作前需重查。
- 本次沒有新增 Part A/B/C 量測；首行 INCOMPLETE 所列與上述續作事項維持未完成。待 S3 建置自然結束後重新盤點程序及核對 binary，再繼續 S1。

## 本次續作：process gate 再確認
- strict host-key SSH 確認 DESKTOP-LKMLUPC，current-best binary SHA256 為 A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8，符合 COMMON。
- S3 建置仍在執行：PID 27532 cmake.exe 執行 s3-mtp-experts-20261031\build 的 strata build；PID 10988 cmake.exe 與 PID 2860 cl.exe 為編譯子程序。依 process gate 暫停 S1 遠端操作，未停止任何程序，未啟動 S1 engine 或 benchmark。
- API 排程 Strata-Task020-API 為 Ready；程序篩選未見 strata 或 python；GPU 使用 591 MiB。這是當次快照，不代表整個任務結束時的狀態。
- Part A、B、C 及獨立最終 API 狀態核驗仍未完成。待 S3 建置自然結束後重新盤點程序及核對 binary，再繼續。

## 第 9 次續作：process gate
- strict host-key SSH 確認 DESKTOP-LKMLUPC，current-best binary SHA256 A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8 符合 COMMON。
- S3 建置仍在執行：PID 27532 cmake.exe 執行 s3-mtp-experts-20261031\build 的 strata build，PID 29956 cl.exe 正在編譯 CUDA template。依 process gate 暫停 S1 遠端操作，未停止任何程序，也未啟動 S1 engine 或 benchmark。
- API 排程 Strata-Task020-API 為 Ready；依指定名稱及工作集 > 1 GiB 篩選未見 strata 或 python，GPU 使用 591 MiB。這是本次檢查快照；API 的獨立結束核驗仍未完成。
- Part A、B、C 仍未完成；無新增量測。S3 建置自然結束後，須重新核對 process gate 和 binary identity，再繼續首行所列工作。

## S1.1 字表與涵蓋率
- 頻率語料為遠端 `C:\Users\User\Strata-Adrian-control\docs\DETAILS.md` 與 `docs\AI_SETUP.md`，共 30,824 tokens；不含 Hermes p01–p10 輸出。按頻率降序、同頻率 ID 升序選取，保留原字表順序與其中全部 33 個特殊／控制 ID。
- 遠端 `runs\untested5-20261031\s1\draft_vocab_v64.bin`（65,536 IDs，SHA256 e3a652458fa4b9ef7e04ec247adca6b4a096b3f84b17dd11199aba05d660d61f）及 `draft_vocab_v32.bin`（32,768 IDs，SHA256 21626ccf11da6ef3960fd09518c1cb32b2484fc388524b5c2aebec6a7b2f4e4a）均為現有 106,299 IDs 的子集。
- 涵蓋率使用 gpu6-ab 所有 100 個現有 `resp-p*.json` 的 content 與 reasoning_content 重編碼，14,087 tokens：V64 95.8756%、V32 88.8408%、原字表 96.2448%。這是文字重編碼估計，不是原始生成 token ID 的精確涵蓋率；特殊結束 token 可能未包含。
- 遠端詳細結果：`runs\untested5-20261031\s1\vocab-result.json`；本機腳本 `s1-vram-vocab\make_vocab.py`。遠端腳本副本存於 `runs\untested5-20261031\shared\make_vocab_s1.py`。
- 本步未啟動引擎或 benchmark；S1.2–S1.6 仍未完成。

## S1.2 trace 續查（未完成）
- strict host-key SSH 確認 DESKTOP-LKMLUPC；遠端操作前的程序篩選未列出 strata、python、cmake、ninja、nsys、luna、cl.exe、nvcc 或工作集超過 1 GiB 的程序。未啟動或停止引擎。
- 唯讀查詢 trace 的最後 PP 至 DONE 區間，含 696,404 筆 kernel；只逐一檢視第一個 mtp_select_kernel 前後的局部序列。該例中 gridX=106299 的 native_q5_k_mmvq_kernel 位於 argmax、row_top_prob、map_ids 與 mtp_select 之前，支持既有 draft head 辨識；此單一樣本不足以證明所有視窗分類。
- 第一例顯示 verify commit 與 draft 之間有 copy_indexed、copy_from_mapped_multi、embed 等 kernel，router 後又出現另一 stream 的 verify kernel；跨 stream 有重疊。尚未確認所有 window 的正確邊界及逐 kernel 彙總，因此未提供完整 draft 與其餘 kernel 的 ms/window，也未將 S1.2 標為完成。原始 trace 保持不變。
## S1.2 trace 續查：draft head 全區間彙總（未完成）
- 本次 strict host-key SSH 確認 `DESKTOP-LKMLUPC`，依程序名稱及工作集 > 1 GiB 篩選未列出程序；未啟動或停止程序。
- 以 SQLite 唯讀掃描遠端 `runs\gpu-bw-nsys-20261030\trace2.sqlite` 中 `analyze2.py` 相同的最後 PP 至 DONE 區間，包含 696,404 筆 kernel、512 個 T 標記。`gridX=106299` 的 `native_q5_k_mmvq_kernel` 共 431 次，均在 stream 14，累計 173.062682 ms；依指定 512/292 換算為 **0.592680 ms/window**。它與既有 head 行數及局部 argmax/map_ids/mtp_select 序列一致，辨識為 draft head GEMV。
- 431 個 `mtp_select_kernel` 出現在同一區間；verify 與 draft kernel 跨 stream 重疊，尚未證實逐 window 邊界，因此尚不能列出完整 draft 各 kernel 或計算其餘 draft 的時間。上述 0.592680 是 kernel duration 加總而非跨 stream 消除重疊的牆鐘時間；不應與未分類 kernel 時間直接相加推定延遲。原始 trace 未修改。
- Coverage：完整掃描指定 PP–DONE 區間的 kernel 名稱、gridX、stream 與 duration 以彙總 draft head；僅抽看前兩個 router 局部序列，未完成每個 window 的邊界驗證及所有 draft kernels 分類。S1.2 保持未完成。

## S1.2 續查：第一個 draft stream 序列
- 本輪以 strict host-key SSH 再確認 `DESKTOP-LKMLUPC`，唯讀讀取既有 trace，沒有啟動或停止程序。分析腳本：`D:\strata\state\untested5-20261031\s1-vram-vocab\trace_inspect.py`。
- 第一個 `mtp_select_kernel` 前的 stream 14 序列包含 `copy_from_mapped_multi_kernel`、embedding、attention、MoE、gridX=106299 的 `native_q5_k_mmvq_kernel`、argmax 和 map_ids；下一個 stream 19 embedding 由 router 後約 0.171 ms 開始。相同時間 stream 36 有 route、GU 與 down kernel，不能僅依時間把它們認定為 draft 或 verify。
- Coverage：這次僅檢視第一個 router 前後的局部 kernel 序列與 stream 14 前序；未完成全部 431 次 router 的邊界歸屬或逐 kernel 總計。先前 head 0.592680 ms/window 的全區間彙總仍有效，但完整 draft phase 及其餘 kernel 的 ms/window 未驗證，S1.2 保持未完成。

## S1.2 續查：source 的 side stream
- 本次 strict host-key SSH 確認 DESKTOP-LKMLUPC；程序篩選 strata、python、cmake、ninja、nsys、luna、cl.exe、nvcc 與工作集大於 1 GiB，未列出符合項目。未啟動或停止程序。
- 唯讀檢查 source 的 src/core/mtp.cpp：MtpDrafter 建立 cs_ 與 side_；record_rest 中 shared expert 可在 side_ 上執行，並以 event fork/join 同步。capture_round 與 capture_step 在 cs_ 上 capture，mtp_select 亦在 cs_。因此不能只彙總 router 所在 stream，亦不能僅以時間重疊將另一 stream 判為 draft。
- Coverage：本次只檢視 MTP 的 stream、capture 及 shared expert 相關 source 摘要，未完成所有 trace window、side stream 與 kernel 的歸屬。既有 head 數值不變；剩餘各 kernel ms/window 尚未確認，S1.2 保持未完成。

## S1.2 router graph 全區間 kernel 彙總
- strict host-key SSH 核對 hostname `DESKTOP-LKMLUPC`；依 strata、python、cmake、ninja、nsys、luna、cl.exe、nvcc 與工作集大於 1 GiB 篩選未列出程序。沒有啟動或停止程序，原 trace 以 SQLite 唯讀開啟。
- 使用 `analyze2.py` 同一最後 PP 至 DONE 區間（512 個 T、292 個 window），以 `mtp_select_kernel` 所在 CUDA graph ID 篩選所有 kernel，包含 graph 中的 side stream。graph ID 為 14、17、23、29、35、38、41；各 graph 的 router 與 gridX=106299 head 次數分別均為 158、141、50、79、1、1、1，總計各 431。graph 起始局部序列為 copy_from_mapped_multi、embed 等，與 MTP source 的 capture 及 fork/join 相符。此分類完整涵蓋這些 router graph，但沒有獨立證明 graph 外所有 verify/draft 交界 kernel 的歸屬；表格不含 graph 外 kernel。
- 下表是 kernel duration 加總除以 292，相當於每 token 數值乘 512/292；因 stream 可重疊，**不是牆鐘延遲**。head 的 `native_q5_k_mmvq_kernel` gridX=106299 對應 Q5_K draft head gather，431 次共 173.062682 ms，0.592680 ms/window；router graph 其餘 kernel 共 1.248996 ms/window，合計 1.841676 ms/window。

| Kernel | 次數 | ms/window |
|---|---:|---:|
| native_q5_k_mmvq_kernel（head） | 431 | 0.592680 |
| attn_chunk_kernel | 431 | 0.402179 |
| native_small_mmvq_kernel | 3052 | 0.244410 |
| attn_merge_kernel | 431 | 0.169026 |
| gr_up_multi_kernel | 1293 | 0.086569 |
| gr_down_staged_kernel | 1293 | 0.084501 |
| native_mmvq_multi_kernel | 911 | 0.054374 |
| gu_grouped_t_kernel | 431 | 0.042341 |
| bf16_f32_mmvf_kernel | 862 | 0.025618 |
| down_grouped_t_kernel | 431 | 0.019745 |
| gr_norm_split_kernel | 1293 | 0.011692 |
| native_quantize_q8_1_kernel | 2802 | 0.011531 |
| mtp_select_kernel | 431 | 0.009421 |
| route | 431 | 0.008911 |
| norm | 563 | 0.007628 |
| fwht256_kernel | 1724 | 0.006718 |
| argmax_rows_kernel | 431 | 0.006176 |
| norm_rope_kernel | 730 | 0.005753 |
| embed_rows_kernel | 431 | 0.005609 |
| row_top_prob_split_kernel | 431 | 0.005416 |
| norm_grouped | 431 | 0.004767 |
| quantize_q8_0_scaled_kernel | 431 | 0.004431 |
| group_resident_kernel | 431 | 0.004286 |
| kv_append_q4_kernel | 431 | 0.003466 |
| copy_from_mapped_multi_kernel | 431 | 0.002950 |
| swiglu_quantize_q8_0_scaled_kernel | 431 | 0.002723 |
| copy_row_to_first_kernel | 132 | 0.002601 |
| native_swiglu_quantize_q8_1_kernel | 431 | 0.002186 |
| add_streams_broadcast_kernel | 431 | 0.002105 |
| window_ids_kernel | 431 | 0.002100 |
| apply | 352 | 0.001862 |
| sigmoid_scale_rows_vec4_kernel | 431 | 0.001734 |
| combine_k10_vec4 | 431 | 0.001697 |
| gate | 431 | 0.001550 |
| post | 431 | 0.001467 |
| map_ids_kernel | 431 | 0.001454 |

- Coverage：完整掃描指定區間 696,404 筆 kernel 以辨識含 router 的 graph，彙總其所有 25,351 筆 kernel 和全部 side stream；graph 外的交界 kernel 未逐一分類。S1.3–S1.6 與 stage 最終驗證仍未完成。

## S1.2 source 邊界續查
- 本次以 strict host-key SSH 確認 `DESKTOP-LKMLUPC`，程序篩選 strata、python、cmake、ninja、nsys、luna、nvcc、cl.exe 與工作集大於 1 GiB 無符合結果；未啟動或停止程序。
- 唯讀檢查 `C:\Users\User\native-pipe-generic-20261029\src\core\mtp.cpp`：`capture_round` 的 graph 包含 catch-up、`record_rest` 與 `mtp_select`（1050–1091 行）；`capture_step` 包含 `record_forward` 與 `mtp_select`（1094–1117 行）；draft 路徑啟動 round/step graph（1265–1270、1308–1314、1342–1364 行）。這支持先前以 router graph 彙總 MTP kernel 的分類。
- Coverage：本次只查上述 source graph 的擷取與啟動位置，未重新掃描 trace，也未證實「最後 verify-layer kernel 至下次 verify start」之間所有 graph 外 kernel 的歸屬；因此既有表格仍只涵蓋 router graph，不能宣稱完整 draft phase，S1.2 保持未勾選。

## S1.2 視窗邊界續查（仍未完成）
- strict host-key SSH 確認 DESKTOP-LKMLUPC；按 strata、python、cmake、ninja、nsys、luna、nvcc、cl.exe 與工作集大於 1 GiB 篩選未列出程序。trace 以 SQLite 唯讀開啟，未啟動或停止程序。
- 全部 431 個 router 的 graph 次數重新核對為 14:158、17:141、29:79、23:50、35/38/41 各 1。第一個 router 的 graph 23、correlationId 689796；之前 graph 5、correlationId 689595 最後依序有 copy_from_mapped_kernel、append、copy_indexed_kernel，分別早於 router 2.019、2.016、2.014 ms；之後 graph 11、correlationId 689824 先出現 copy_i32_from_mapped_kernel（晚 0.166 ms），其後 embed_rows_kernel。這證明至少該局部窗口的 graph 外邊界還涉及其他 kernel，但未能僅據此判定其應歸入 draft 的完整範圍。
- Coverage：完整統計 PP–DONE 的 router 數與 graph 分布；只檢視第一個 router 附近約 150 筆 kernel，未驗證全部 window 的 verify-layer 結束及下一次 verify 起點，亦未彙總 graph 外區段。因此 S1.2 未完成，既有 router graph 表不可視為完整 draft phase。原 trace 不變。
## S1.2 本輪狀態
- 重讀既有 trace_inspect.py 與 analyze2.py：前者只列第一個 router 附近 kernel，後者分析整體 GPU 區間，均未建立每個 draft window 的 verify 邊界。已用 strict host-key SSH 確認 DESKTOP-LKMLUPC；程序篩選未列出 strata、python、cmake、ninja、nsys、luna、nvcc、cl.exe 或工作集大於 1 GiB 的程序。
- Coverage：本輪只檢查上述兩支分析腳本及遠端程序篩選；未重新掃描 trace 或驗證 graph 外 kernel 歸屬。先前 router graph 的 0.592680 / 1.248996 ms/window 不足以證明完整 draft phase，S1.2 仍未完成，後續步驟未執行。
## S1.2 本輪 graph 分布檢查（仍未完成）
- strict host-key SSH 確認 DESKTOP-LKMLUPC；程序 gate 篩選 strata、python、cmake、ninja、nsys、luna、nvcc、cl.exe 與工作集大於 1 GiB，未列出符合程序。未啟動或停止程序。
- 以 SQLite 唯讀檢查相同 PP–DONE 區間所有 kernel 的 graphId 分布：graph 11 有 307,164 筆、26 有 227,050 筆、20 有 104,291 筆、5 有 14,504 筆、32 有 13,040 筆；含 router 的 graph 14/17/29/23/35/38/41 分別有 9,006/8,037/5,056/3,050/69/68/65 筆。這確認 router graph 以外的資料量很大，但 graphId 單獨不能判定 verify 與 draft 視窗交界。
- Coverage：完整按 graphId 統計 PP–DONE 的 kernel 數及 duration；沒有逐次核對 verify 結束、下次 verify 開始，也沒有將 graph 外 kernel 分類。既有 head 0.592680 與其他 router graph 1.248996 ms/window 仍僅為部分範圍，S1.2 不能標記完成；原 trace 未變更。
## S1.2 本輪 verify source 續查（未完成）
- strict host-key SSH 確認 DESKTOP-LKMLUPC；以 strata、python、cmake、ninja、nsys、luna、nvcc、cl.exe 與工作集大於 1 GiB 篩選程序，未列出符合項目。未啟動或停止程序。
- 唯讀查閱遠端 AGENTS.md 與 native-pipe-generic-20261029/src/core/verify.cpp：verify window graph 在 2005、3045 行啟動；另有獨立 commit graph 在 2337、3209 行啟動，3209–3211 行在 commit 後記錄 event。這說明 verify layer、commit 和 draft graph 並非必然是單一 graph；僅憑 router graph 不能確定要求的時間邊界。
- Coverage：本輪只搜尋 verify.cpp、session.cpp 的 graph capture/launch 摘要，未重新掃描 trace、未建立全部視窗邊界，未辨識所有 graph 外 kernel。既有 router graph 表和 head 數字維持部分結果；S1.2 未完成，後續步驟未執行。

## S1.2 首個 router 的擴大局部序列（未完成）
- strict host-key SSH 確認 DESKTOP-LKMLUPC；以程序名稱及工作集大於 1 GiB 篩選未列出符合程序。以 SQLite 唯讀執行本機 `trace_boundaries.py`，沒有啟動或停止引擎或其他程序。
- 首個 router 前 graph 5（correlation 689595）有多個 GDN commit、copy、append kernel；router 所在 graph 23（correlation 689796）開始於 router 前約 1.122 ms，末端為 head、argmax、map_ids 與 router；之後 graph 11（correlation 689824）包含 copy、embed 和 verify layer kernel。此局部序列顯示 commit 不能直接排除在題目要求的視窗外，但單一樣本不足以確認各視窗完整歸屬。
- Coverage：掃描 PP–DONE kernel 找到首個 router，輸出其前 120 與後 100 筆；未逐個驗證其餘視窗或 graph 外 kernel 的歸屬，也未產生完整逐 kernel 彙總。既有 router graph 結果仍為部分範圍；S1.2 保持未完成，S1.3 以後未執行。

## S1.2 graph 啟動序列續查（未完成）
- strict host-key SSH 確認 DESKTOP-LKMLUPC；按名稱及工作集大於 1 GiB 篩選未列出符合程序。第一次程序查詢有引號錯誤，已用 EncodedCommand 修正；未啟動或停止引擎。
- `trace_graph_sequence.py` 以 SQLite 唯讀完整掃描 PP–DONE 區間，按 graphId 和 correlationId 彙整 870 個啟動群組，含 431 個 router 群組。router 前後五個群組的序列至少有多種模式：例如 14,11,14,11,14 出現 45 次，11,14,17,26,5 出現 42 次；首個 router 前依序是 graph 20、5，後接 graph 11、14。第二個 router 後可直接接另一個 router graph 17，說明不能假設每個 router 後都是 verify graph。
- Coverage：全區間完成 graph/correlation 群組與 router 鄰接模式統計；只輸出前三個 router 的局部群組摘要，未逐筆確定每個 verify-layer 結束及下一 verify 起點，亦未按所要求的完整視窗彙總 kernel 時間。graph 啟動順序不等同 kernel 時間邊界；既有 head 與其他 router graph 數字仍為部分結果。S1.2 保持未勾選，後續步驟未執行。

## S1.2 本輪 source 順序核對（未完成）
- strict host-key SSH 確認 DESKTOP-LKMLUPC；程序名稱與工作集 >1 GiB 篩選無符合項目。唯讀核對 verify.cpp:2337-2340：commit graph 與下一 verify window 使用相同 stream，而 drafter 使用另一 stream；mtp.cpp:1308-1314 顯示 draft 可連續啟動 round 與多個 step graph。這表示僅按 graph 啟動先後切分，不能證明跨 stream kernel 的完整時間邊界。
- Coverage：本輪僅查看 verify.cpp 和 mtp.cpp 的 cudaGraphLaunch 上下文，未重掃 trace 或核實所有視窗的 verify-layer 末端與下一起點；原 router graph 數據仍是部分結果，S1.2 保持未勾選。未啟動或停止程序，未進行後續步驟。

## S1.2 本輪 commit 條件核對（未完成）
- strict host-key SSH 確認 DESKTOP-LKMLUPC；依程序名稱及工作集大於 1 GiB 篩選未列出程序，未啟動或停止程序。唯讀檢查 verify.cpp：一般 commit 在單 token 且符合 one_token_self_commit 條件時不啟動 commit graph；否則啟動 commit graph，依 g_commit_async 與 next_ 決定同步；pipelined commit 另等待前次 commit event，再啟動 graph 並記錄 event。這些條件表示不可假定每個視窗都有獨立 commit graph。
- Coverage：本輪僅讀取 verify.cpp 的兩處 commit 上下文，未重新掃描 trace，也未驗證每個視窗的最後 verify-layer kernel 與下一次 verify 起點。既有 router graph 彙總與 head 識別仍是部分結果，完整 draft phase 無法確認；S1.2 保持未勾選。未執行後續步驟。

## S1.3 分項表續查（未完成）
本次重新唯讀核對遠端 DESKTOP-LKMLUPC 啟動 stderr 與既存 allocation 搜尋；未重新啟動引擎。以下 MiB 為該次 log 明示值，source 行號為已保存搜尋命中；估算值另標示。

| 項目 | MiB | source | 現有選項與限制 |
|---|---:|---|---|
| canonical weights | 1466 | src/program/generate.cpp:2899 | 未確認有不改輸出的縮減旗標 |
| native projections | 1781.11 | src/core/native_dense.cpp:292 | 未確認可縮旗標 |
| 主 head | 416.80（437043200 bytes） | src/core/native_head.cpp:49 | 未確認可縮旗標 |
| expert cache | 約 5243（log 5.12 GiB；3153 slots） | src/core/expert_cache.cpp:519 | 減少 cache 會減少 slots，並可能改變 CPU/GPU rounding |
| MTP layer | 820，內含 experts 675、dense 111、其餘約 34 | src/core/mtp.cpp:283、307、339、410 | 是否存在符合要求的縮減旗標仍待確認 |
| MTP draft head | 178.4 | src/core/mtp.cpp:643-644 | STRATA_MTP_FULL_HEAD=1 不配子集，理論省 178.4 MiB、約 107 slots；改變 draft 路徑，輸出與 window 條件尚未核實，不可先判為合格 arm |
| verify buffers | 69.8，spec 6 | src/core/verify.cpp:618 | 降 spec 可縮，但 suffix 最多可用 S，不能確認 window 不變 |
| KV | 約 135（歷史 inventory，非本次獨立量測）；20480 cells | src/program/generate.cpp:4135 | 具體大小公式與選項尚待核對 |
| cuBLAS workspace | source 常數 32 MiB，是否本次實際配置未核對 | src/prefill/prefill.cpp:903、src/prefill/gemm.cu:442 | workspace 可能借用 cache，不可與 cache 直接相加 |
| CUDA graph、GDN/SSM state、staging、context/WDDM | 尚無可分離的量測 | src/core/session.cpp:429、src/program/generate.cpp:4135；其餘待核對 | 約 930 MiB 僅為舊 inventory 的混合未歸屬值，不是 context/WDDM 單獨估計，也不能宣稱全不可回收 |

本次啟動前後 GPU 總量 558 → 11547 MiB，差 10989 MiB；含其他背景變動，不能用來直接計算每個項目。large-page 字樣在此次 startup log 未見；page-locking refused 不是 large-page 結果。
Coverage：已核對整份 startup stderr；allocation 搜尋原檔 476 行包含測試與非活動路徑，本次輸出截斷、僅抽看一部分，尚未逐項核對完整活躍路徑、大小公式、borrowed buffers 與 graph/context 拆分。故此表是部分結果，S1.3 保持未勾選；未執行後續步驟。

## S1.3 本輪 allocation 呼叫補查（未完成）
- strict host-key SSH 確認 DESKTOP-LKMLUPC；本輪程序篩選未列出 strata、python、cmake、ninja、nsys、luna、nvcc、cl.exe 或工作集超過 1 GiB 的程序，S3 排程 Ready。未啟動或停止任何程序。
- 針對 session.cpp、mtp.cpp、verify.cpp、expert_cache.cpp、generate.cpp、prefill.cpp 唯讀搜尋 allocation 與 graph 呼叫：session buffer 在 generate.cpp:4135 以 session_bytes(g, max_context, K, 0, hi0) 計算；MTP state 在 mtp.cpp:339、348，arena 在 410，draft head 大小為 n_dvocab * row_bytes（644）；verify arena 在 verify.cpp:618；prefill.cpp:903 宣告 32 MiB GEMM workspace，但 prefill.cpp:369、392 顯示可能借用區域或自行配置，尚未確認本次路徑。graph instantiate/upload 也有多處呼叫，無法從呼叫清單推算佔用。
- Coverage：僅這六個檔案的搜尋結果前 130 筆，含測試或非活動路徑；未完整驗證分配條件、計算 live config 大小、去除重複借用，也未拆分 graph/context/WDDM。因此 S1.3 尚未完成，不能勾選或得出完整 VRAM 表。未執行後續步驟。

## S1.3 本輪既有記錄與 allocation 呼叫核對（未完成）
- strict host-key SSH 確認 DESKTOP-LKMLUPC；本輪依 strata、python、cmake、ninja、nsys、luna、nvcc、cl.exe 名稱及工作集大於 1 GiB 篩選，未列出符合程序。未啟動或停止任何程序。
- 重新搜尋既有 startup-stderr.log：serve 明記 prompt path 借用 1687 個 cache slots（2.70 GiB），不得把該空間再次加到 cache；verify 69.8 MiB、draft head 178.4 MiB，及 254 MiB VRAM free 均為該次 log 記錄。這不提供 graph 與 context 個別大小。
- 完整輸出六個已識別主要 source 檔的指定 cudaMalloc、cudaMallocAsync、session_bytes、workspace、graph instantiate/upload 搜尋命中：另有 MTP sampler/ring/scratch（mtp.cpp:516-517）、logits（621）、prefill allocation（1137、1179），以及 generate.cpp 中 hit scratch、history 等 allocation；是否在該次啟動或後續 decode 啟用與實際大小仍未逐項核實。
- Coverage：本輪只搜尋六個檔案的指定字串，未覆蓋其餘 source、所有配置 API 與呼叫條件；沒有解出 session 各項大小，也沒有測得 graph/context/WDDM 各自佔用或合格旗標。故 S1.3 保持未完成，不能將已有部分表視為完整 itemization；未執行後續步驟。

## S1.3 session arena 公式與 graph 呼叫續查（未完成）
- strict host-key SSH 確認 DESKTOP-LKMLUPC；名稱與工作集 >1 GiB 的程序篩選未列出符合項目。遠端 binary SHA256 為 A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8。未啟動或停止程序。
- 唯讀檢查實際 source `C:\Users\User\native-pipe-generic-20261029\src\core\session.cpp:55`：session arena 包含 GDN buffers、各層 GDN state、QSA state（其中一份含 RoPE，其他借用）、QSA buffers、MoE buffers、block buffers 和 PLE history，最後對齊並加 4096 bytes；配置呼叫位於 `src/program/generate.cpp:4135`。各子項 live 數值仍未計算，不能把 QSA、GDN 或 borrowed RoPE 當作獨立重複配置相加。
- 全部 `src` 的 `.cpp`、`.cu`、`.h` 搜尋 session_bytes、STRATA_MTP_FULL_HEAD、cudaMallocAsync、cudaGraphInstantiate 與 cudaGraphUpload：找到 graph.cpp、mtp.cpp、session.cpp、verify.cpp 等 production 呼叫及多個 parity 測試命中；未找到上述檔案中的 cudaMallocAsync 字串。這些呼叫無法單獨量化 graph 或 context/WDDM 記憶體。
- Coverage：完整搜尋上述副檔名和五個指定字串；未搜尋其他配置 API、其他副檔名或程式外部函式庫，未計算 live 子項大小，也未拆分 graph/context/WDDM 或核定合格縮減旗標。既有啟動 log 重讀，但沒有重啟引擎。S1.3 仍未完成，後續步驟未執行。
## S1.3 本輪核對（未完成）
- strict host-key SSH 確認 DESKTOP-LKMLUPC，current-best binary SHA256 A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8；依名稱與工作集 >1 GiB 篩選未列出程序，S3 排程 Ready。未啟動或停止任何程序。
- 唯讀核對 session.cpp:55 起的 arena 公式及 startup-stderr.log：QSA 首個 state 持有 RoPE，其餘借用；日誌顯示每 QSA layer 20480 cells 在 VRAM，另有 0.64 GiB pinned RAM。後者是主記憶體，不得加到 VRAM 表。
- Coverage：只核對 session arena 公式和 startup log 的匹配行；未計算各項 live 大小、拆分 graph/context/WDDM 或核定可縮旗標。S1.3 未完成，未進行後續步驟。

## S1.3 本輪紀錄核對（未完成）
- strict host-key SSH 確認 DESKTOP-LKMLUPC；未啟動或停止程序。tasklist 輸出截斷且未取得完整命令列，因此不能視為通過完整 process gate。
- 重新檢視 startup-stderr.log 對記憶體與 cache 的所有匹配行：20.00 GiB、20479 MiB 是鎖定的主記憶體 expert cache complement，不是 VRAM arena；GPU expert cache 為 3153 slots、5.12 GiB，prompt path 借用 1687 slots（2.70 GiB），不能重複計算。先前紀錄中「arena 20479 MiB」應理解為 RAM，不是 VRAM。
- Coverage：僅依指定字串檢查該啟動 log；沒有完成 source allocation 活躍路徑、live session 子項、graph/context/WDDM 與可縮旗標盤點。S1.3 未完成，後續步驟未執行。

## S1.3 本輪補查（未完成）
- strict host-key SSH 確認 DESKTOP-LKMLUPC；依程序名稱及工作集大於 1 GiB 篩選無符合程序，S3 排程 Ready；未啟動或停止程序。
- SSH 帳戶的 `whoami /priv` 清單未列出 SeLockMemoryPrivilege；尚未核對該 SSH token 與實際引擎啟動 token 的權限是否相同，不能直接視為引擎帳戶結論。
- 完整搜尋目前 source 的 `.cpp`、`.cu`、`.h`，字串為 cudaMallocManaged、cudaMallocHost、cudaHostAlloc、cudaMemPool、cublasSetWorkspace、cublasLtMatmul、STRATA_MTP_FULL_HEAD；命中包括 host-pinned/mapped 配置與 prefill/gemm.cu 的 cuBLAS workspace。這些 host 配置不能直接全部計入 VRAM，也尚未逐一核對 live 路徑。
- Coverage：僅搜尋上述副檔名與字串；其他配置 API、外部函式庫、實際活躍分配與 live 數值未完成。graph/context/WDDM 分項及符合條件的縮減旗標仍未確認；S1.3 保持未完成。

## S1.3 本輪 process gate（未完成）
- SSH strict host-key 確認 DESKTOP-LKMLUPC；按名稱 strata、python、cmake、ninja、nsys、luna、nvcc、cl.exe、msbuild 或工作集 >1 GiB 篩選，沒有符合程序；Strata-S3-MTP-DIAG-20261031 排程為 Ready。
- nvidia-smi 列出 dwm、explorer、ShellHost、Windows shell、ASUS、Razer、LGHUB、Taskmgr、Edge WebView、Riot Vanguard 等 GPU 程序，Windows 未提供各程序 GPU 用量；尚未核對所有 PID 命令列及用途，因此依工作區 process gate 暫停，沒有繼續遠端操作或停止程序。
- Coverage：僅完成上述篩選與 GPU 名稱清單；未完成 GPU 程序分類，也未完成 live allocation、graph/context/WDDM 分項與可縮旗標。S1.3 保持未勾選。

## S1.3 本輪補查（未完成，02:39）
- strict host-key SSH 確認 DESKTOP-LKMLUPC；名稱篩選及工作集超過 1 GiB 無符合程序。GPU 清單 15 個 PID 的名稱及命令列已核對，屬 Windows 桌面、Search WebView、ASUS、Razer、LGHUB、Riot Vanguard tray 和工作管理員；未停止程序。GPU 合計 558 MiB，WDDM 未提供各程序用量。此盤點只代表當下。
- 重讀既有 startup-stderr.log 中 allocation、MiB、GiB、slot、graph、workspace 的匹配行；記載 300 native projection matrices 1781.11 MiB、MTP layer 820 MiB、expert cache 5.12 GiB、verify 69.8 MiB、draft head 178.4 MiB。prompt path 借用 cache slots，不能重複計算；20 GiB complement 為 RAM。
- 遠端沒有 rg，graph/workspace 搜尋命令失敗，未替換工具或宣稱完成。Coverage 僅上述程序快照與啟動紀錄匹配行，仍缺完整活躍 allocation 公式、live 子項、graph/context/WDDM 及縮減旗標；S1.3 保持未完成。未執行後續步驟。

## S1.3 本輪 graph 與 workspace 補查（未完成）
- strict host-key SSH 確認 DESKTOP-LKMLUPC；名稱與工作集大於 1 GiB 篩選無符合程序，S3 排程 Ready。GPU 清單 15 個程序的 PID、名稱與命令列已核對，屬桌面、裝置工具與系統匣程序；未啟動或停止任何程序。
- 搜尋 source 全部 .cpp、.cu、.h、.cuh 的 cudaGraphInstantiate、cudaGraphUpload、cudaMallocAsync、cublasSetWorkspace：production 命中 core/graph.cpp:65、core/mtp.cpp:1019,1026、core/session.cpp:253,899、core/verify.cpp:1829,1899,2435,2568,2575，以及 prefill/gemm.cu:406,420,446；另有 parity 測試命中。該範圍沒有 cudaMallocAsync 命中。呼叫存在不代表本次 startup 均啟用，也不能量化 graph/context 記憶體。
- Coverage：完整搜尋上述副檔名及四個字串，未覆蓋其他配置 API、外部庫、live 呼叫條件與尺寸；VRAM live 子項、graph/context/WDDM 歸屬與可縮旗標尚未完成。S1.3 保持未勾選；未執行後續步驟。

## S1.3 本輪 workspace 核對（未完成）
- strict host-key SSH 確認 DESKTOP-LKMLUPC；程序名稱與工作集大於 1 GiB 篩選無符合項目，S3 排程 Ready。GPU 清單 15 個 PID 的名稱與命令列已核對為系統桌面、Search WebView、裝置工具及系統匣程序；WDDM 未提供各程序 GPU 用量。未啟動或停止程序。
- 遠端 source `src/prefill/gemm.cu:394-406` 的 `init_external` 使用傳入的 workspace；`416-420` 的 `rebind` 重新綁定，不能將其視為新的分配。`430-446` 的另一個 `init` 路徑自行分配 32 MiB workspace，`451-452` 另分配 `scratch_elems * 2` bytes。尚未驗證實際啟動採用哪條路徑，不得將 32 MiB 直接列為 live 額外占用。
- Coverage：本輪只讀取上述 source 行與程序快照；未完整檢查活躍 allocation 路徑、live 大小、graph/context/WDDM 與縮減旗標。S1.3 保持未完成，未執行後續步驟。
## S1.3 本輪 prefill 配置核對（未完成）
- strict host-key SSH 確認 DESKTOP-LKMLUPC；Strata、Python、建置及工作集大於 1 GiB 的篩選無符合程序，S3 排程 Ready。GPU 15 個 PID 與命令列核對為桌面、裝置工具和系統匣程序；GPU 總用量 558 MiB，未停止或啟動程序。
- 完整搜尋目前 source 的 .cpp、.cu、.h、.cuh 中 init_external、scratch_elems 等字串；prefill/prefill.cpp:902-903 定義 GEMM scratch 為 32M 個 FP16 元素（64 MiB）、workspace 為 32 MiB；1132-1138 透過 Alloc 取用並傳給 init_external，1274-1279 重綁。這些是 prefill carve 的子項，不能直接加到借用的 expert cache 上；尚未完整核對所有路徑與超出 borrow 的分配，不能斷言實際額外 VRAM 為零。
- Coverage：本輪只核對上述搜尋字串及 prefill 子項；未完成其他活躍配置、live session 子項、graph/context/WDDM 和既有縮減旗標，S1.3 仍未完成。既有 startup 檔及先前單次啟動結果見本檔開頭；未執行後續步驟。
## S1.3 本輪程序盤點（未完成）
- strict host-key SSH 確認 DESKTOP-LKMLUPC；首次遠端命令引號錯誤，修正後取得程序清單、S3 排程與 nvidia-smi，但完整程序清單輸出遭截斷，不能確認所有程序及命令列。S3 排程狀態數值 3，GPU 558 MiB；未停止或啟動程序。
- Coverage：本輪僅確認主機、GPU 清單和部分程序；完整 process gate 未通過，未繼續遠端操作。S1.3 allocation 分項、活躍路徑、graph/context/WDDM 與縮減旗標仍未完成，故保持未勾選。

## S1.4 啟動
- 已啟動遠端排程 Strata-S1-VOCAB-20261031，優先權 2；三組 C、V64、V32，五輪輪替共 15 blocks。執行檔 SHA256 A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8。
- 遠端目錄 C:\Users\User\Strata-Adrian-control\runs\untested5-20261031\s1\ab，設定 arms.json，執行 run.ps1，完成後自動撤銷排程；結果與進度尚待 S1.5 核實。初次排程註冊的帳戶名稱無效，改用既有排程的互動式 User principal 後已啟動。

## S1.5 程序 gate
- strict host-key SSH 確認 DESKTOP-LKMLUPC；S1 排程執行中，controller PID 8012、4488，server PID 25056、10072，strata.exe PID 30328，命令列顯示目前為 block-01-C-r1。依工作區遠端 process gate 暫停，未讀取 progress.json，無法確認已完成 block 數；未啟動或停止程序。S1.5 保持未勾選。

## S1.5 程序 gate（2026-10-31 02:48:41）
- SSH strict host-key 確認 DESKTOP-LKMLUPC；S1 排程狀態為 Running，controller PID 8012、4488，server PID 25056、10072，strata.exe PID 30328，命令列對應 block-01-C-r1。S3 排程為 Ready。依工作區 process gate 停在程序盤點；未讀取 progress.json，完成數未知，未啟動或停止程序。S1.5 保持未勾選。
