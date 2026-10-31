STATUS: INCOMPLETE S3.3 已完成路由統計與部分成本模型；須取得完整 q2_0 expert CPU 成本並確認跨門檻估計

## S3.3 本次狀態

- 已重新讀取本步規則與既有分析。步驟容許引用 10/28 的 q2_0 down nt=1 數值；既有紀錄為 86.21 μs，但這項數值僅代表 down，不能確認完整 expert 成本。PCIe 理想淨收益上界 0.695 ms/window 跨越 0.6 門檻，尚不足以判定結果。
- 本次未重新盤點遠端程序、核對執行檔或啟動微測；因此未取得新量測，S3.3 維持未完成。API 即時狀態未核對。

## 2026-10-31 00:50 續作進度

- 再次核對主機 `DESKTOP-LKMLUPC`、current-best SHA256 `A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8`；啟動前的程序 gate 未列出相關程序或超過 1 GiB 的程序。API 排程為 Ready。
- 已建立遠端隔離 source 複本 `C:\Users\User\Strata-Adrian-control\runs\s3-mtp-experts-20261031\source`，僅在 `src/core/mtp.cpp` 的 resident grouping 前增加同步讀回及輸出 `S3_MTP_ROUTE T=... K=... ids=...` 的診斷程式。尚未驗證編譯、輸出格式、每個 window 的對應或量測干擾。原 source 和 current-best exe 未修改。
- 獨立 build `C:\Users\User\Strata-Adrian-control\runs\s3-mtp-experts-20261031\build` 已由 priority 2 的一次性排程 `Strata-S3-MTP-DIAG-20261031` 啟動。00:50 檢查為 Running，`build-progress.json` 為 BUILD，wrapper PID 32548；CMake 已辨識 MSVC 與 CUDA。日誌及進度檔均在遠端 `C:\Users\User\Strata-Adrian-control\runs\s3-mtp-experts-20261031\`，腳本副本在本資料夾。成功或失敗尚未知；排程 wrapper 結束後會取消註冊。
- 下次續作先輪詢上述 progress 與 build.log；若仍執行，不啟動其他遠端工作。若結束，依 COMMON 規則核對 gate、編譯結果及執行檔身份，完成 DIAG 執行、分點分析、冷 expert microbench 和 PCIe 成本；依 0.6 ms/window 條件決定是否 prototype 與 A/B。未執行 DIAG 量測，尚無 histogram 或效益結論。

2026-10-31 00:46（遠端時間）重新確認 SSH 主機 DESKTOP-LKMLUPC，current-best SHA256 為 A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8；API 排程 Ready，GPU 使用 558 MiB，檢查時未見 strata/python/build 類程序或 >1 GiB 程序。已讀遠端控制工作樹 AGENTS.md；執行前仍需讀實際 source 工作樹 AGENTS.md，並重新盤點程序及 SHA。此次未啟動任何測試或修改遠端。以下為前次檢查紀錄；尚未完成的步驟仍需執行，不能作效能結論。
# S3 MTP expert residency — 未完成

## 已核對

- 2026-10-31 遠端 SSH hostname 為 DESKTOP-LKMLUPC；current-best `C:\Users\User\Strata-Adrian-control\runs\native-pipe-deploy-prep-20261029\build\strata.exe` SHA256 為 `A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8`，符合 COMMON.md。
- 該 build 的 CMake source 為 `C:\Users\User\native-pipe-generic-20261029`，HEAD `f520bc5e9d31c93caeb296b059e3a3eaa16e493f`，git status 無輸出。
- `src/core/mtp.cpp:296-318`：從 `experts.bin` 分塊讀取，將全部 expert 配置並複製到 GPU；64 MiB host chunk 是載入時的區域變數，並非此處保留的完整 host 副本。尚未完整檢查程式其他位置是否另有 host 副本。
- `src/core/mtp.cpp:897-918`：router 為每個 token row 選 top-10；特定條件採 multi-token native router；可選 route-resident 調整在 grouping 前執行；隨後以 ids 對 resident experts 分組計算。尚未確認每個 draft window 與 row 的完整對應。
- `src/program/generate.cpp:4666-4696`：expert cache 在 weights、session 與 drafter 後配置；自動容量取得當時可用 device memory。精確 slot 公式與 reserve 尚未完成檢查。
- 最後一次程序檢查未列出名稱含 strata/python/cmake/ninja/cl.exe/nvcc/luna 或工作集大於 1 GiB 的程序；API 排程 `Strata-Task020-API` 為 Ready，未啟動 API。

## 尚未執行

沒有建立 DIAG build、沒有執行 10 個 Hermes points、沒有直方圖、冷 expert microbench、成本模型、prototype 或 A/B。無法判斷是否達到 0.6 ms/window 門檻，也不能推論效能結論。尚須檢查完整 slot 公式、effective args/env 和 host copy，再依 COMMON.md 完成量測。上述僅為局部原始碼檢查，非全程式 coverage。


## 本次續作的額外核對

- 重新以嚴格 host-key SSH 確認 `DESKTOP-LKMLUPC`；current-best SHA256 仍為 `A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8`。進程查詢未列出 Strata、Python、編譯器、Luna 或工作集超過 1 GiB 的程序；API 排程 `Strata-Task020-API` 為 Ready。來源工作樹的 AGENTS.md 已讀取。
- `src/core/mtp.cpp:254-260`：共享 drafter 直接共用另一個 drafter 的 device expert 指標；`151` 僅擁有權重者釋放該 GPU 配置。`297-318` 的載入暫存 chunk 在區域結束後消失；仍未確認其他模組是否獨立保有 host 副本。
- `src/program/generate.cpp:4732-4736`：自動 slot 數為 `(free_b - reserve) / expert_layout().max_blob`，並受 profile 大小限制；reserve 包含 VRAM reserve、prefill、MTP bind 及 pipeline 記憶體。`4770-4785` 另有小容量設備的 reserve 調整條件。
- 現有部署使用 NMake、Release、CUDA 架構 89；本次僅讀取來源與 CMakeCache，尚未建立 source copy 或 build。
- 遠端無 `rg`，改以 PowerShell `Select-String` 檢查指定檔案；這不代表已完成全程式 host-copy 搜尋。

## 下一次續作

先重新執行 process gate 和 current-best SHA 核對；建立隔離 source copy，於 routing 調整後記錄每 row 的 expert IDs 並識別 draft step/window，建立獨立 DIAG build。用既有 harness 執行 10 個 Hermes points 各 512 tokens（保持既有取樣與 API 不啟動），建立分點 histogram、前五點排名與後五點 coverage；完成 CPU q2_0 microbench、PCIe 實測、RAM/SSD 影響估計及淨收益表。僅當估計達 0.6 ms/window 時才進行指定 prototype、greedy identity 與五輪 A/B。完成後再次驗證 API 未運行並更新本報告。

## 第 4 次續作輪詢

- 已重新讀取工作區規則與 handoff 文件；遠端一次性排程 `Strata-S3-MTP-DIAG-20261031` 仍為 Running，`build-progress.json` 仍為 BUILD（wrapper PID 32548），build.log 最新可見 CUDA `gdn.cu` 編譯警告，尚無完成狀態或可用執行檔驗證。未啟動其他遠端工作。
- 下次先輪詢該進度與日誌；完成後依程序 gate 和 current-best SHA 核對，再繼續 DIAG 量測、分析及條件式 prototype。API 本次未重新確認。


## 第 5 次續作輪詢

- 遠端排程 `Strata-S3-MTP-DIAG-20261031` 仍為 Running；`build-progress.json` 仍為 BUILD，wrapper PID 32548。`build.log` 已出現 `native_mmvq.cu` CUDA 編譯警告，尚無完成或失敗結果。未啟動其他遠端工作；API 本次未重新確認。
- 待該工作完成後，重新核對程序 gate、current-best SHA，繼續 DIAG 量測、成本模型及條件式 prototype；執行中不可並行啟動其他遠端工作。

## 第 6 次續作輪詢

- 遠端排程 Strata-S3-MTP-DIAG-20261031 仍為 Running；build-progress.json 仍為 BUILD，wrapper PID 32548。尚未驗證編譯完成或 API 目前狀態，未啟動其他遠端工作。
- 下次先輪詢進度；完成後重新核對程序及 current-best SHA，再執行路由量測、成本模型和條件式 prototype。

## 第 7 次續作輪詢

- 遠端一次性排程 `Strata-S3-MTP-DIAG-20261031` 仍為 Running；`build-progress.json` 為 BUILD，wrapper PID 32548。`build.log` 仍有 CUDA 編譯器輸出及 C4819 警告，尚無編譯完成或失敗結果。
- 依 COMMON.md，編譯仍執行時未啟動其他遠端工作。本次未重新確認 API 狀態，也未取得路由量測或成本結果。
- 後續先輪詢進度；完成後重新核對程序 gate 與 current-best SHA，再完成 DIAG 量測、成本模型和門檻決定的 prototype／A-B，最後確認 API 未執行。

## 第 8 次續作輪詢

- 遠端一次性排程 `Strata-S3-MTP-DIAG-20261031` 仍為 Running；`build-progress.json` 仍為 BUILD，wrapper PID 32548。未啟動其他遠端工作；本次未重新確認 API 狀態。
- 下一次先輪詢既有編譯，完成後核對 process gate 和 current-best SHA，再完成 DIAG 量測、成本模型及條件式 prototype／A-B，最後確認 API 未運行。

## S3.1 DIAG 重建完成

- 遠端 `C:\Users\User\Strata-Adrian-control\runs\s3-mtp-experts-20261031\build-progress.json` 顯示 `phase: DONE`、`exit_code: 0`，時間為 `2026-10-31T04:54:24.5568273+08:00`；`build.log` 顯示 `[100%] Built target strata`。
- 實際執行檔 `C:\Users\User\Strata-Adrian-control\runs\s3-mtp-experts-20261031\build\strata.exe` SHA256：`4C0F2F8C43EA23ADD16D78D25CFF44350ABEBAF1361A1932327635AA63C1BD26`。本次只核對編譯結果與檔案雜湊，尚未執行或驗證診斷輸出；API 狀態未重新確認。

## S3.1b 控制器修改

- shared/abctl.py 支援每組指定 exe 與 sha，未指定時使用 current-best；只提供其中一項會拒絕。實際遠端 replay 在啟動前檢查指定執行檔 SHA，並檢查執行中程序雜湊；current-best 的既有 identity gate 仍保留。
- 本機兩輪 dry run 為 C、DIAG、DIAG、C，驗證預設與診斷 SHA；輸入及結果為 s3-1b-arms.json、s3-1b-dry-run.json。未啟動引擎，實際 DIAG 執行與雜湊拒絕行為尚未實測。
- 控制器已複製至遠端 runs\untested5-20261031\shared\abctl.py；本機及遠端 SHA256 均為 1E9ABC21C62FEF3BE1F671D3017C4650F6AF3227C051C192242D27BE985EF7FD。

## S3.2 診斷執行中

- 05:25 核對遠端 DESKTOP-LKMLUPC，current-best SHA A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8，DIAG SHA 4C0F2F8C43EA23ADD16D78D25CFF44350ABEBAF1361A1932327635AA63C1BD26；未見其他測試或編譯程序，API 排程 Ready。GPU 558 MiB、0% 使用；列出程序為桌面及常駐工具。
- 一次性排程 Strata-S3-ROUTE-20261031 執行中；單組、單輪，0/1 blocks；遠端 runs\untested5-20261031\s3\diag，engine.log 已建立。尚未確認 10 點完成或路由輸出，下一次應先檢查排程、progress.json、error.txt 及引擎日誌，避免重複啟動。

## S3.2 本次輪詢 05:28

- 遠端排程仍為 Running；controller.log 已記錄 p01–p08，區塊尚未完成（0/1），progress.json 尚未建立。輸出位於遠端 runs\untested5-20261031\s3\diag\out\block-01-DIAG-r1；未重複啟動。

## S3.2 診斷完成

- 遠端 progress.json 為 DONE、1/1；block meta.json 為 OK、rows=10，十個 resp-p01 至 resp-p10 均存在。DIAG binary SHA256 為 4C0F2F8C43EA23ADD16D78D25CFF44350ABEBAF1361A1932327635AA63C1BD26。
- 遠端 `C:\Users\User\Strata-Adrian-control\runs\untested5-20261031\s3\diag\out\block-01-DIAG-r1\engine.log` 含 1198 行 S3_MTP_DRAFT、1924 行 S3_MTP_ROUTE；draft steps/window 與路由資料已收集，尚未分析其分布或收益。逐點回應、tail logs、results.json 與 meta.json 位於同一資料夾；進度檔位於上層 diag\progress.json。
- 一次性排程 Strata-S3-ROUTE-20261031 查為 Ready，已依規則取消註冊。API 狀態本次未確認。


## S3.3 路由分析與未決成本（2026-10-31）

- 十個逐點 tail 日誌均已複製至本資料夾：1198 個 draft 紀錄、1924 個 steps、19240 次 expert route；每 step 10 個 ID。完整 512 expert 直方圖、逐點計數、訓練 top-N IDs 與計算結果見 s3-analysis.json。每點皆按該點日誌統計；前五點訓練，後五點測試。
- 表格依序為 N、全資料 top-N coverage、前五點排名在後五點 coverage、後五點冷呼叫/window、釋放 MiB、預估 VRAM 收益 ms/window、PCIe 理想傳輸成本 ms/window：

| N | 全部 | 測試 | 冷呼叫/window | MiB | 收益 | PCIe |
|---:|---:|---:|---:|---:|---:|---:|
| 32 | 27.72% | 23.14% | 13.095 | 632.8 | 1.125–1.406 | 0.742 |
| 64 | 43.71% | 36.03% | 10.899 | 590.6 | 1.050–1.313 | 0.617 |
| 128 | 65.13% | 55.49% | 7.584 | 506.3 | 0.900–1.125 | 0.430 |
| 192 | 78.06% | 67.46% | 5.543 | 421.9 | 0.750–0.938 | 0.314 |
| 256 | 86.67% | 76.94% | 3.930 | 337.5 | 0.600–0.750 | 0.223 |
| 384 | 97.14% | 91.12% | 1.512 | 168.8 | 0.300–0.375 | 0.086 |

- PCIe 成本按每冷呼叫 1,382,400 bytes、既有實測 host-to-device 24.4 GB/s（gpu-bw-nsys-20261030/result2.json 的 probe）計算；未計傳輸啟動、同步、GPU 計算或重複載入影響。VRAM 收益沿用 brief 的 675 MiB 對應 1.2–1.5 ms/window 線性估算。N=64 理想淨收益約 0.433–0.695 ms/window，跨越 0.6 門檻，因此不能直接判定達標或未達標。
- worker-skew-20261028/analysis.json 的 nt=1 q2_0 down 為 86.21 μs／921600 bytes；它只測 down，不能當作完整 MTP expert 的 gate、up、down 成本。按大小比例 1.5 倍只是未驗證代理，s3-analysis.json 中 cpu_proxy_ms 不代表完整 expert 實測。需完成適用維度的完整 CPU 成本測量或取得有根據的完整估算，再判定條件。host copy 約 675 MiB；RAM cache 排擠的額外 SSD 讀取量未知，尚未納入。API 本次未檢查。

## S3.3 本次核對

- SSH 嚴格驗證後 hostname 為 DESKTOP-LKMLUPC，current-best SHA256 為 A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8；遠端控制工作樹 AGENTS.md 已讀。程序查詢未列出 strata、python、編譯器、Luna 或工作集超過 1 GiB 的程序；Strata-S1-VOCAB-20261031 與 Strata-S3-MTP-DIAG-20261031 排程均為 Ready。未啟動任何測試。
- 已檢索既有 worker-skew 與 IQ microbench 資料，現有 q2_0 down 86.21 μs 仍不涵蓋完整 gate、up、down；PCIe 理想估計跨越 0.6 ms/window。未取得完整 expert 測量，尚無可靠門檻結論。下一次須檢查遠端原微測 harness 與 MTP 維度，依規則測量完整 CPU expert，再完成模型；本步保持未勾選。

## S3.3 本次檢查

- 遠端主機 DESKTOP-LKMLUPC，current-best SHA256 A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8；按名稱 strata、python、cmake、ninja、nvcc、cl.exe、luna、bench 或工作集超過 1 GiB 篩選，沒有結果。此篩選不是所有程序的完整分類；API 與排程狀態本次未查。
- 未啟動微測，完整 q2_0 expert 成本、門檻與 S3.3 仍未完成；既有分析及其限制保持不變。

## S3.3 本次續作

- 嚴格 SSH 核對 DESKTOP-LKMLUPC 與 current-best SHA256 A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8；名稱篩選 strata/python/cmake/ninja/nvcc/cl.exe/luna/bench 或工作集超過 1 GiB 無結果。完整程序清單輸出遭截斷，未完成全程序分類，GPU 程序未核對；不可據此啟動測試。
- 已定位遠端 runs\worker-skew-20261028 的 harness、source、build 和 out；尚未檢查 harness 維度及執行完整 expert 微測。成本與 0.6 ms/window 門檻仍未判定，S3.3 保持未勾選。

## S3.3 本次檢查

- 嚴格 SSH 主機金鑰驗證後，hostname 為 DESKTOP-LKMLUPC。遠端 worker-skew-20261028 含 build、harness、source、out；harness 列出兩個 Python 檔。對 source bench 的名稱搜尋輸出截斷，未完成微測原始碼定位，不能視為完整搜尋。
- 本次未啟動微測，亦未重新檢查 current-best SHA、完整程序或 GPU；完整 expert 成本及門檻仍未判定。S3.3 保持未勾選。

## S3.3 本次檢查（未完成）

- 嚴格 SSH 驗證主機 DESKTOP-LKMLUPC；current-best SHA256 為 A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8。遠端程序與檔案混合查詢輸出截斷，未完成程序分類與 GPU 核對；排程 S1、S3 DIAG 顯示 Ready。
- 未執行完整 expert 微測，既有 PCIe 理想估計跨越門檻，不能判定 S3.3 完成或跳過後續步驟。

## S3.3 本次續作

- 已以嚴格 SSH 主機金鑰驗證 DESKTOP-LKMLUPC；current-best SHA256 為 A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8。名稱篩選相關程序及工作集超過 1 GiB 無結果；兩個 Strata 排程狀態為 Ready。GPU 清單顯示 Windows 桌面、裝置工具等程序；未取得各程序 GPU 用量，亦未完成全部程序分類。
- 遠端 worker-skew source 定位到 src/kernels/native_expert_bench.cpp；尚未核對其維度、執行路徑與完整 q2_0 gate/up/down 支援。既有 IQ all-types 報告不含 q2_0 完整 expert。未啟動微測，完整 CPU 成本與 0.6 ms/window 門檻仍未判定；S3.3 保持未勾選。

## S3.3 本次唯讀核對

- SSH 主機名稱為 DESKTOP-LKMLUPC。檢查遠端 runsworker-skew-20261028sourcesrckernels
ative_expert_bench.cpp：程式呼叫 CUDA native_expert_grouped，使用 CUDA event 計時，固定 H=2560、FF=640；這是 GPU grouped expert 微測，不能作為 CPU nt=1 完整 MTP expert 的量測。
- 本次未啟動微測，亦未完成 current-best SHA、process gate 或 API 狀態核對；現有 PCIe 理想估計仍跨越 0.6 ms/window，CPU 完整 expert 成本與條件判定仍未完成。S3.3 保持未勾選。


## S3.3 本次核對

- SSH 確認 DESKTOP-LKMLUPC，current-best SHA256 為 A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8；兩個既有排程狀態為 Ready，GPU 程序清單可見桌面與常駐程式，但 GPU 個別用量不可得。完整程序清單輸出遭截斷，無法完成 process gate。未啟動微測或修改遠端；完整 CPU expert 成本及門檻仍待判定，S3.3 保持未完成。

## S3.3 本次檢查

- 嚴格 SSH 驗證主機 DESKTOP-LKMLUPC；完整程序清單輸出截斷，無法完成程序 gate。本次未重新核對 current-best SHA 或 GPU，未啟動微測；完整 expert CPU 成本和 0.6 ms/window 門檻仍未判定。S3.3 保持未勾選。

## S3.3 本次檢查

- SSH 主機 DESKTOP-LKMLUPC；current-best SHA256 A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8。名稱篩選相關程序與工作集 >1 GiB 無結果；兩個 Strata 排程狀態 Ready。GPU 程序列出桌面與常駐程式，但 Windows 未提供個別 GPU 用量，未完成全部程序分類。
- 遠端 worker-skew 遞迴檔案清單輸出截斷，不能據此判定微測資料完整性。未啟動微測；完整 expert CPU 成本、0.6 ms/window 門檻與 S3.3 仍未完成，API 狀態未查。

## S3.3 既有模型淨收益核算

由 s3-analysis.json 的收益範圍減去成本，單位 ms/window：N=32、64、128、192、256、384 的 PCIe 理想淨收益依序為 0.383–0.664、0.433–0.695、0.470–0.695、0.436–0.623、0.377–0.527、0.214–0.289。PCIe 未計啟動與同步等成本，最高上界跨越 0.6，無法判定是否達標。依相同順序，現有 CPU proxy 的淨收益為 −0.568–−0.287、−0.359–−0.097、−0.081–0.144、0.033–0.221、0.092–0.242、0.104–0.179；這是 down 量測按大小外推的未驗證代理，並非完整 expert 實測，不能作門檻判定。RAM cache 與 SSD 影響仍未知。本次未啟動遠端微測，S3.3 尚未完成，維持未勾選。
## S3.3 本次核對（完整清單）

- 嚴格 SSH 驗證 DESKTOP-LKMLUPC；current-best SHA256 A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8。完整 243 個程序清單保存在 process-inventory.json；名稱篩選相關程序及工作集超過 1 GiB 均無結果，最大工作集 289 MiB。兩個 Strata 排程 Ready；GPU 程序列出桌面與常駐程式，個別 GPU 用量不可得。尚未逐一核對全部程序用途，因此不能宣稱通過完整 process gate。
- 未啟動微測；CPU 完整 expert 成本、PCIe 實際額外開銷與 0.6 ms/window 門檻仍未確認。S3.3 未完成。


## S3.3 本次門檻敏感度

- 已核對遠端 hostname 為 DESKTOP-LKMLUPC；本次未啟動測試，未重新核對 binary、程序或 API。
- 由既有 s3-analysis.json 計算，PCIe 理想成本以外仍可容許的額外成本（淨收益達 0.6 ms/window），N=32、64、128、192、256、384 分別為 -0.217–0.064、-0.167–0.095、-0.130–0.095、-0.164–0.023、-0.223–-0.073、-0.386–-0.311 ms/window。這是既有收益範圍的敏感度運算，不是額外開銷實測；負數代表該收益端點已低於門檻。RAM/SSD 影響與 PCIe 啟動及同步成本仍未知。
- 成本範圍跨越門檻，無法作確定的通過或未通過判定；完整 CPU expert 成本仍未量測。S3.3 未完成，保留未勾選。

## S3.3 既有 down 數據直接代理

- 依步驟允許沿用的 10/28 q2_0 down nt=1 86.21 μs，直接乘以前五點訓練、後五點測試的冷呼叫/window；N=32、64、128、192、256、384 的成本分別為 1.129、0.940、0.654、0.478、0.339、0.130 ms/window。扣除後的 VRAM 收益範圍分別為 −0.004–0.277、0.110–0.373、0.246–0.471、0.272–0.460、0.261–0.411、0.170–0.245 ms/window。這只是 down 代理，不是完整 expert 成本，也不是實際收益。
- PCIe 理想淨收益仍有 0.433–0.695（N=64）及 0.470–0.695（N=128）ms/window，跨越 0.6；傳輸啟動、同步與 RAM/SSD 影響未知。因此不能宣稱達標或未達標，S3.3 尚未完成。未啟動遠端工作；API 即時狀態未核對。