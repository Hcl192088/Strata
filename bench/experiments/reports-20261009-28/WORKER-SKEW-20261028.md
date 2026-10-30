# POOL_WORKER_SKEW 診斷結果（2026-10-28）

狀態：診斷完成；不是優化、沒有部署。live S2K 已還原並驗證。

## 身分與執行
- 主機 DESKTOP-LKMLUPC。live = S2K（runs\miss-overlap-20261027\build\strata.exe，SHA 385EF64E…30F5）；起跑前盤點到的 strata/python 全是 live API 堆疊與 memory-policy --watch，無未分類程序。
- 診斷 build：把 S2K source 複製到 runs\worker-skew-20261028\source（只改 pool.cpp、expert_source.cpp，新增 wskew_trace.hpp），用 cmake 全新建到 runs\worker-skew-20261028\build（belownormal，-j 2，約 8 分鐘）。診斷 binary SHA 246D8550253FDDE209E032BE44260DEF2D182182757FFB930F3864A08A166B6B。原 S2K source/build/config/排程工作都沒動。
- 計時只在 `STRATA_WSKEW=1` 才開，預設關。每個 native 計算 phase（gate/up 與 down）每個 worker 記錄 LP、任務開始與結束時間（相對 publish）、列數、token 列數、處理位元組；host 記錄 drain、完成等待、re-park；記憶體內彙總、每 1000 次 pool call 與離開時寫檔。
- 單執行緒微基準（`STRATA_WSKEW_MICRO=1`）：每次 pool call 之後，在 host 執行緒（LP0，P-core，workers 已 park）對一個 expert 做 clflush → IQ3 gate/up kernel（冷）→ 再跑一次（暖）→ clflush → 純 AVX 讀同樣位元組 → clflush → down kernel。只寫 scratch，不動輸出。
- 執行（排程工作 Strata-WSkew-20261028，priority 2，引擎 AboveNormal，live S2K 環境變數，neuro prompt SHA 9350584440AD…18BA，1024 token，每次新引擎、一個 GEN）：ON1、ON2（計時）、MIC（計時＋微基準，額外）、OFF（診斷 binary、env 關，額外的開銷對照）。4 次全部 OK、1024 token、容量 3153／20.00 GiB／20479 MiB、優先權 AboveNormal。live API 停止約 5 分鐘（18:49–18:54）。
- 還原：finally 啟動 Strata-Task020-API，20 秒內 loaded=true；final_verify：loaded、3153 slots、20.00 GiB、locked 20479 MiB、引擎 SHA 385EF64E…30F5、STRATA_MISS_OVERLAP=1／SPIN_US=2000、AboveNormal，verified=true。
- 輸出相同性：只加計時，沒有改任何計算；但引擎本身不是逐 token 決定性的（先前 r3 的 token SHA 也每次不同），所以沒有做 token 逐位元比對。OFF 54.88→53.69 tok/s（ON1 54.88、ON2 54.89）顯示開關開銷在雜訊內；MIC 47.77 因微基準的 clflush 拖慢，不作為速度參考。

## 結果（ON1+ON2 合併，約 52,000 次 pool call；兩次單獨結果一致）
CPU layer-window 只計有 CPU 工作的層窗（plain＋overlap 第 2 次呼叫）。每 window 的 pool call 約 13.1 ms（引擎自報 CPU 段 15.5 ms，差額是活化量化與 miss 讀取等）。

| 項目 | P 群（LP 2,4,6,8,10） | E 群（LP 12–15） | host（LP0） |
|---|---|---|---|
| 每 phase 平均完成時間（µs） | 113.1 | 127.3（+12.5%） | 114.7 |
| 忙碌時的有效頻寬 GB/s（gate/up） | 3.73 | 1.73 | 3.63 |
| 忙碌時的有效頻寬 GB/s（down） | 5.47 | 2.89 | 5.43 |
| 每 phase 領到的任務數 | 3.66 | 2.0 | 3.73 |
| 負責的列數佔比 | 61% | 27% | 12% |
| 每個 layer-window 忙碌 ms | 0.246 | 0.277 | 0.251 |
| 完成後閒置（等最慢者）µs | 27.5 | 13.3 | 25.9 |

- 每 phase 30 個任務、列數等分（mrows/30），但任務是動態領取（3 task/thread），所以 E-core 自動少領：E 群 4 條執行緒只做 27% 的列，P 群 5 條加 host 做 73%。E-core 在這個 kernel 上每位元組慢約 2 倍（2.0 vs 4.2 GB/s），不是頻寬量測的 19.3 vs 25.5。
- 完成時間差：E 比 P 晚 12.5%（T=1 11.5%、T=2 13.4%、T=3 12.6%）。
- host 完成等待（wait_done）佔 pool call 18.2%（T=1 14.1%、T=2 18.2%、T=3 19.2%）；約 2.35 ms/window。換成「容量閒置」算法（10 條執行緒的總容量中沒在算的比例）是 16.3%。兩種算法都低於 25%。
- 任務數 30 vs 執行緒 10：host 派發／park 邊界極小（re-park 0.1%、activation 量化 0.7%、第一個任務起跑延遲 <1 µs）。
- nt 不平衡：各執行緒的平均 nt（token 列／列）P 1.197、E 1.21，幾乎相同；有效 GB/s 在 T=1、2、3（平均 nt 1.00、1.18、1.26）下都是 P 4.2、E 2.0，沒有隨 nt 變化。結論：等列數切分不會因 nt 不同造成成本失衡（多 token 一次讀同一份權重，成本主要在權重解碼）。

## 單執行緒 kernel（MIC 執行，553 個樣本，其中 nt=1 533 個）
- gate/up kernel 單獨、冷快取：329 µs／1.25 MB → 約 3.8 GB/s；暖快取 4.1 GB/s。
- 同樣位元組的純 AVX 讀（冷）：45 µs → 約 27.7 GB/s（與今天 bwtest 單 P-core 25.5 一致）。
- down kernel 單獨冷：約 86 µs／0.92 MB（約 10.7 GB/s）；在 pool 內實測 5.5 GB/s。
- 限制：微基準的位元組數用的是 dump 時最後一個樣本的層型別（IQ3 層 gu_row 不同，位元組 1.25 MB 與 1.05 MB 兩種），所以 kernel-alone GB/s 有約 ±15% 的不確定；in-situ 的位元組數是逐任務累加，準確。down 的 in-situ 比單獨慢約一半，可能是任務很小（約 17 µs）加上領取／快取開銷，這次沒有拆開。E-core 的單獨 kernel 沒量（沒有空閒的 E-core LP 可用，workers 在自旋）。

## 判定（照事前登記，未改標準）
標準：E 群平均完成時間比 P 群晚 ≥ 20% 且（host 完成）等待 ≥ CPU 段 25% → 做第 3 階段依速度／成本分配。
實測：12.5%（<20%）、18.2%（<25%），兩條都不成立 → **POOL_WORKER_SKEW 不成立，不進依速度分配的第 3 階段**，差距另有來源。

差距的來源：kernel 本身。單核 gate/up kernel 只有約 3.8 GB/s（同一核純讀可到約 27 GB/s），在 9 個 worker 並行時每條 P 執行緒仍是 3.7 GB/s（沒有並行損耗），E 執行緒只有約一半。所以 CPU 段 28 GB/s 的有效頻寬不是記憶體頻寬，也不是排程，而是 IQ3 kernel 在每個核上是算力（解碼）受限：6 條 P 級執行緒 × 約 4 + 4 條 E × 約 2 ≈ 33 GB/s 的上限，離 DRAM 的 45.7 GB/s 還有空間，但要靠加快 kernel 本身。

排程上殘留的空間：容量閒置 16%（約 2.1 ms/window，佔 32.8 ms 的 6%）是理論上限，實務上受任務粒度（E 每任務約 63 µs，phase 約 140 µs）限制，能拿到的大概是其中一半以下，約 +3% 以內，低於雜訊（CV 約 7%），單獨不值得做。

## 檔案
- 本機：D:\strata\state\worker-skew-20261028\（raw\ 原始輸出、analysis.json、analyze_wskew.py、patch_wskew.py、patched\ 與 src\ 的 source、wskew_queue.py）
- 遠端：C:\Users\User\Strata-Adrian-control\runs\worker-skew-20261028\（source、build、out）
