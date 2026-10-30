[LUNA_REPORT]

# FRESH_BUILD_SANITY attempt-2：PASS

TASK_ID：LUNA-20261012-027；STATUS：REPORT_LOCAL；TASK_SOURCE：使用者今日「先做健全檢查」及本次明確 brief，直接 continuation，無新 claim／GitHub 操作。TASK_BRANCH／TASK_COMMIT_SHA：本次未經 GitHub claim；不以歷史鎖定值冒充當輪資料。

## Identity 與流程

已重新核對 hostname DESKTOP-LKMLUPC。canonical root `C:\Users\User\Strata-Adrian-control` 的實際 junction target 為 `C:\Users\User\Strata-Adrian\repo\Strata-Adrian-control`。遠端 main HEAD 實讀為 `2f1e99872969c9b4586a2d41c7f1915f27e4f298`；既有 dirty/untracked 保留，未修改 source／remote main／git／模型／live config，未 push。fresh source HEAD 與具名 tag 解參照皆為 `f520bc5e9d31c93caeb296b059e3a3eaa16e493f`，source worktree clean。tag 與 branch 同名造成 rev-parse ambiguity warning，但解參照值符合。

- F SHA256：`A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8`。
- T SHA256：`3F98913EDB0B01D5D5DD3282412725141C298BF5CC9E890DD286AA0720C27230`。
- 執行前及每 block 前核對 F/T 與 live current-best identity；run_block 另核對啟動中的 engine SHA。各 meta 保存實值。
- 使用 `native-pipeline-po-confirm-20261029` 原 harness，所有 Python SHA 與該 campaign compatibility manifest 相同；十題 request SHA 與原 audit 相同。未修改 harness。
- 預先生成三份 config，比對原 P block，僅 exe／cwd／log 可不同；實際三份 block config 再互比亦只有這三項差異（兩 F 間僅 log）。完整差異存 preflight.json／local-audit.json。
- Hermes 十題、max 512、每 block 新 engine、workers 9、affinity all、PIPE=1；無啟用 CHECK／DIAG。既有 replay temperature=0 與其他 sampling 保持原契約，沒有調溫。
- 每個 engine 首題前 AboveNormal、逐題由原 harness 重驗 priority／process gate；三組容量全為3153 slots／20.00 GiB／20479 MiB。
- 執行前盤點 PID／名稱／command line，僅 live API／memory-policy／watch；SSD_JOIN_BOUND controller 已不在，未見其他 Codex／benchmark／trace／build。分類存 pre-stop-processes.json／classified.json。停 API 後 process gate=[]。無停止無關程序。
- detached scheduled controller 使用既有 stop_api，finally restore_api。三 block 都 OK、共30題，零 request error；完整 logs 有 NATIVE_PIPE ACTIVE 與實際 overlap counter，無 fatal／CHECK／DIAG。

控制器完成時間（UTC）：`2026-10-29T01:52:08.063607+00:00`；phase=DONE，restored=true，verified=true。首次兩次 launcher 命令在本機 shell parsing 層失敗，未送達遠端、未建立 attempt-2 或停 API；修正引號後使用原定 scheduled-controller 方式。無 fallback、無重跑 block。

## 結果

pooled tok/s = Σ m_out_tokens（engine_generated）×1000 / Σ m_decode_ms；ms/window = Σ m_decode_ms / Σ windows；tokens/window = Σ m_out_tokens / Σ windows；CPU ms/window = Σ(row.cpu_ms × row.windows) / Σ windows。CPU 原值為 engine decode timing 的每 window CPU，非 process CPU time。metrics 保留0.1 ms，文字 generated-in 行為整數 ms 四捨五入，已核對 token 完全一致與時間精度差。

| 順序／臂 | tokens | decode ms | windows | pooled tok/s | ms/window | tokens/window | window-weighted CPU ms/window |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 F | 1779 | 38117.2 | 950 | 46.67184368 | 40.123368 | 1.872632 | 22.769589 |
| 2 T | 2031 | 44759.3 | 1021 | 45.37604475 | 43.838688 | 1.989226 | 25.769775 |
| 3 F | 1869 | 40067.2 | 1010 | 46.64663366 | 39.670495 | 1.850495 | 22.240525 |
| F兩 block 合併 | 3648 | 78184.4 | 1960 | 46.65892429 | 39.890000 | 1.861224 | 22.496959 |

F合併對T：**+2.827218% → PASS**。依預登錄 −5% 規則，未見明顯退步；不是等速證明。僅一輪 F→T→F，沒有增加門檻或輪次。輸出/window mix 不同，單輪約±5%雜訊的既有設計限制仍在，不把此差值當固定相同輸出的純 kernel 收益。

## Live 還原

controller finally 與之後獨立 audit 均通過。live engine PID 26660，AboveNormal（32768）、health loaded=true；binary SHA256 `385EF64EE24BDF3BD4B309264FA811901DF9256B92CE4589BAEC70B3F26B30F5`，原 config SHA256 `F23F1AAD8E385987708D6DFB854AD139D513FE398151CCCC5FBD43CFE303EB6F`。3153 slots／20.00 GiB／20479 MiB，workers9／affinity all，STRATA_IQ3S_MT1=1；無 PIPE／CHECK／DIAG／MT_MIN 啟用，原 RAM_LRU_CHECK=0 保留。獨立 process gate 僅原 API／memory-policy／watch；benchmark controller 已退出，排程 Ready。未切換候選 live。

## Coverage、原始資料與限制

完整檢查要求的三個 block config／meta／command／startup／results、30 rows及各逐題 tail、三份完整 engine logs（373646 bytes／3414行），核對所有 harness與十題 input SHA、process／priority／capacity／restore identity。logs 以完整檔案解析 gate／計時／pipeline counter，非逐字語義審閱；未逐字審閱自然語言 responses，未做全 source／dependency audit，未重做 bitwise correctness。大型 binary 全檔 SHA，未複製到本機。startup 三組皆保留 page-locking refused 與低 free-VRAM 訊息，未改設定或新增判定門檻；容量嚴格 gate 皆通過，這些訊息的成因未另行診斷。

遠端權威 root：`C:\Users\User\Strata-Adrian-control\runs\fresh-build-sanity-20261029\attempt-2`；實際 junction target 同名 runs。block raw：`out/block-01-F-r1`、`out/block-02-T-r1`、`out/block-03-F-r1`。F：`runs/native-pipe-deploy-prep-20261029/build/strata.exe`；T：`runs/native-pipeline-20261029/build/strata.exe`。

本機完整 raw 保存在 `D:\strata\state\fresh-build-sanity-20261029\attempt-2`；包含 rows.json、analysis.json、preflight.json、campaign.json、restore.json、initial/final_verify.json、independent-live-verify.json、final-processes.json、local-audit.json、controller/log與三組out。根目錄 rows.json 同步為本次30 rows。第一次 preflight、RESULT-attempt1.md 保留，未覆寫原始證據。

剩餘風險：單輪無法證明等速；fresh與T完整binary差異來源未在本次定位。只做健全檢查，無部署或 GitHub 操作。
