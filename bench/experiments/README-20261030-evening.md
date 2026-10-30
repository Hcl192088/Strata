# 2026-10-30 下午～晚間補充（給 GPT 的交班說明）

早上的 commit（README-20261029-30.md）只涵蓋到 10/30 上午。這次補上之後的實驗，以及 Claude 對「下一輪該做什麼」的看法，供你從不同角度討論。原始 log、模型回應、trace（nsys-rep／sqlite）、程序盤點沒有上傳，只在桌機 `Strata-Adrian-control\runs\…`。

## 條件（不變）
同硬體（i5-12600KF、DDR4-3200 2×16 GB、RTX 4070 12 GB）、同權重與量化值、同 expert 選擇（current best 含預設 ROUTE_TAIL_SKIP=7）、同 sampling、精確 speculative；只允許浮點加總順序差異。使用者不考慮任何硬體變更。

current best：binary A1E6123852A5…D9491AD8、config 060F2FBCCC54…46893D93、source f520bc5（native pipeline）。目標 +10%（47.316 → 約 52 tok/s，約省 3.37 ms/window）。

## 現行（pipeline 之後）時間分布
10 個 C block（Hermes 10 題×512）：39.18 ms/window、1.818 tokens/window。
- GPU-reach wait 11.63
- CPU 段 22.33 ＝ pool 15.41 ＋ SSD join 4.65 ＋ LRU 1.04（＋其他）
- MTP draft 1.76
- 其他約 3.5：已拆開，見 pool-diag

注意：README-20261029-30 與 OVERNIGHT 報告裡的 GU 11.88／down 5.16／join 6.09／37.07 ms/w 是 **pipeline 上線前**的數字。

## 這批新增的實驗（結果都在各資料夾 RESULT.md，ledger 有完整條目）

| 資料夾 | 內容 | 結果 |
|---|---|---|
| r4-repair / r4-prefetch / r4-native-unpack | R4 lowreg、固定距離預取、解包後走原生算術 | 預取 NO_GO；解包法只有原生的 21.5–36.5% |
| r4-actual-pool | 真實 9 worker pool，逐 4 列即時轉換 | 8 格全負（−8.2～−19.5%），停止 |
| r4-prepacked-pool | 事先轉好（不計轉換）vs 原生 | nt2 約持平、nt3 時快時慢；只有 nt3/nb8 5/5 較快 |
| r4-engine（結果在 ledger R4_ENGINE_CBC） | 整機 C/B/C，每批動態 prepack | **B 慢 11–12%**（40.26 / 35.75 / 40.53），NO_GO |
| nt1ext / nt1ext-ab | 單 token kernel 擴充到更多量化型別 | +1.44%，CI [−3.25, +6.14]，未通過 |
| gpu6-ab | 6 個「輸出精確」GPU 旗標組合 A/B | +0.61%，CI [−3.31, +4.53]；GPU-reach 配對差 ≈0。GPU 旗標家族結案 |
| pool-diag | pool 內部＋decode 迴圈未計時段（DIAG build） | 見下節 |
| gpu-clock | live 請求時每 100 ms 記 GPU 時脈 | decode 期間固定 2850 MHz、P2，無降頻 → 結案 |
| gpu-bw（ncu） | Nsight Compute 量 kernel 頻寬 | 失敗兩次（VRAM 不足無法 replay；引擎在 ncu 下卡住） |
| gpu-bw-nsys | nsys GPU metrics 10 kHz 量 decode 期間 DRAM 頻寬 | 見下節 |
| speed-research / upstream-search / cpu-kernel-search / overlap-search | 四次外部搜尋（一般、上游與 fork、CPU kernel、batch-1 精確 CPU/GPU 重疊） | 都沒有找到符合條件、預期能單獨 ≥3% 的新方向 |

## 兩個關鍵診斷

### pool-diag（DIAG binary DA40C93A…，C/D/C/D 3 題×512）
- 每 worker 平均：GU P 9.15／E 9.63、quant 0.01–0.04、down P 3.83／E 3.95 ms/w。
- **host 等 pool 完成只有 0.173 ms/w**：工作分配平衡，沒有明顯拖尾。
- decode 迴圈：verify 35.43、draft 1.67、apply_pending 0.68、commit+emit 0.06、suffix/lookup 0.001、未歸屬 0.94 ms/w。
- 結論：沒有 ≥1 ms/w 可以移除的等待或重複工作；CPU 段由 GU 解碼本身主導。10/28 已量到 gate/up 每核只有約 3.8 GB/s（DRAM 上限 45.7 GB/s），卡在 IQ codebook 查表解碼的運算，不是頻寬也不是排程。
- 未量：派工延遲、worker idle/spin、skew、commit 子步驟（估計合計 <1 ms/w）。

### gpu-bw-nsys（同 A1E6，neuro.tokens 28912 prompt，GEN 512，292 windows，44.4 tok/s）
| 家族 | ms/window | DRAM 平均 | GB/s |
|---|---:|---:|---:|
| dense mmvq | 6.96 | 69.4% | 350 |
| HC（gr_*） | 3.66 | 66.2% | 334 |
| attention | 1.26 | 40.0% | 201 |
| GDN | 0.95 | 68.3% | 344 |
| router/topk | 0.25 | 22.9% | 116 |
| wait_flag_ge（GPU 自旋等 CPU） | 16.3 | — | — |

長 kernel 較可信：q5_k_mmvq 86.7%、mmvq_il 72.3%。10–17 µs 的短 kernel（gu_multi 39%、down_multi 26%）在 100 µs 取樣下只能粗估。dense 和 HC 拉到 85% 的上限約 2.1 ms/w，而且只作用在 GPU-reach 段。

## Claude 對「下一輪做 critical-path attribution」的看法
1. **CPU critical path 上的等待／重複處理**：pool-diag 和 nsys 已經回答了。GPU 自旋的 16.3 ms/w 就是 CPU 真正在算 expert 和讀 SSD 的時間；host 等 pool 只有 0.17 ms/w。沒有接近 3.37 ms/w、可以靠排程消除的串行成本。
2. **CPU 在算時讓 GPU 先做後面的事**：每層都是資料依賴（GPU router → CPU expert → 下一層）。已測過的做法：LOOKAHEAD（−6.4%）、路由預測預取（多讀的錯誤資料是救回部分的 4.8 倍，提前量中位數只有 0.58 ms）、`--spec-split` 把 window 拆組交錯（−1.34%：GPU-reach −2.83 ms，但 CPU +2.05 ms，而且 tokens/window −3%）、PIN8／PCIE_BALANCE 讓 GPU 經 PCIe 分擔 expert（兩邊互相抵銷，−1.43%）。
3. **SSD 快取策略**：好處是不改變輸出，符合條件。但 OPT 的 63% 用到未來資訊，不可能實現；可以實作的 ARC／LRU-2 只省 11–16% 讀取量（換算現行 join 約 0.7 ms/w），RAM 跨層配額在保留題只省 14.1%。使用者 10/29 已決定暫停這一類。
4. **GPU kernel 改寫**：上限約 2.1 ms/w（+5%），實際可能只有一半，工程量大。
5. **在條件內還能做的都是小項目**：expert 載入時直接寫進 arena（≤2.7%）、MTP full head（約 1%）、快取策略（約 2%）、GPU kernel（≤5%）。全部疊起來樂觀估計 +5～8%，而且每項單獨都在雜訊附近。

## 條件外、但數字比較大的兩件事
- **HTTP 串流**：live 用 stream=true 時每個 window 多約 6.3 ms（非串流的殘差是 1.7、串流是 8.1 ms/w），實際使用比 benchmark 慢 14–17%。這不影響輸出。使用者已改成客戶端預設不串流；原因還沒找到（server 程式碼看起來不會卡住引擎，多出來的時間落在引擎沒計時的段）。
- **會改變輸出的路由偏置**（ROUTE_PRIOR／ROUTE_BIAS／ROUTE_RESIDENT／GATE_SKIP）：10/20 在舊 binary 量到 +15～60%。上游 0.2.7 在 ≤13 GiB 的卡預設 ROUTE_PRIOR=1.5，0.2.8 因長對話重複文字改回預設關閉。我們的品質評估計畫（10/27 草稿，60 題）從未執行。

## 想請 GPT 從不同角度檢查的問題
- 上面的拆解有沒有漏掉、不靠改變輸出也能省 ≥3 ms/w 的段落？
- 如果 +10% 在條件內做不到，是要放寬條件（哪一條、要配什麼品質關卡），還是改追串流的 6 ms 這類「實際使用」的損失？
- 路由偏置要做的話，品質評估怎麼設計，才抓得到長對話重複這種短題測不出來的問題？
