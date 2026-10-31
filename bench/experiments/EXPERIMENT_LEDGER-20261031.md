# Strata 實驗 ledger

## 2026-10-29 00:2x｜HERMES_CPU_PHASE_DIAG（事前登記；夜間直接授權）
- 類型：結構診斷，僅新增計時/計數，獨立source/build；家族：Hermes CPU/I/O精確拆解，不掃旋鈕。
- 假設：23.90ms/window的Hermes CPU段可用decode起訖快照分成GU、量化、down、join、LRU與剩餘，而全request helper約6.33ms的估計受prompt verifier污染。helper read另拆直接讀取/issue-wait/memcpy及issued/useful bytes，但不把重疊時間相加。
- 目標段/上限：定位CPU23.90ms，補滿50需要約2.47ms/window；本診斷沒有速度收益承諾。CPU全歸零的113tok/s僅算術非可達上限。
- 設計：先probe三點×128 tokens檢查守恆；Hermes10點×512，三輪C/O/D旋轉（current-best MT1／診斷binary開關off／同binary開關on），逐request計時。以上均AboveNormal，容量3153/20.00/20479，sampling依既有replay不改live溫度。診斷probe不是效能樣本。
- 指標：decode-only GU/quant/down/join/LRU/inline/direct/copy/issue-wait、issued/useful bytes、helper執行緒時間、CPU守恆、各臂tok/s與輸出長度；O/C區分rebuild影響，D/O檢查計時擾動。n=3只供診斷，不能作小增益promotion。
- 停止：任何scope/守恆/容量/identity錯誤先停分析修工程；不偽造拆分或加fallback。06:50停止新增run，最晚07:00測試結束並核對MT1 API復原。
- Identity：起跑前實查DESKTOP-LKMLUPC；baseline SHA385E…30F5，MT1 configF23F…EB6F，build source61b3fb5+原兩檔dirty patch。遠端初始沒有相關程序，API task Ready；main6251a722。runner每build/run前重新process gate；只可清理本runner自有後代/經核對stale流程。
- RAW：遠端runs/overnight-20261029；本機state/overnight-20261029。結果待實際執行補登。

## 2026-10-28 21:35｜S2K+MT1 部署與 current-best promotion（本輪無新效能測量）
- 授權：使用者在本對話明確要求「幫我部署及改 best」，並接受相同數學運算的浮點累加差異。
- 已完成：原 binary SHA 385EF64E…30F5 不變；新增 MT1 config/launcher，既有 Strata-Task020-API action 改指 MT1，priority 2 保留。config 只加 STRATA_IQ3S_MT1=1 與專用 log；STRATA_IQ_MT_MIN 未設，溫度與 argv 不變。
- 驗收：3/3 bounded smoke 成功；獨立 audit 21:35:32 核對 loaded、唯一 engine PID25900、AboveNormal、3153／20.00／20479、實際 env；舊 S2K config/launcher 雜湊不變。current-best live/campaign/history 更新為 S2K+MT1，前版快照保留。
- 證據：state/mt1-deploy-20261028/MT1_DEPLOYMENT_20261028.md；遠端 runs/mt1-deploy-20261028/out/deploy_receipt.json 與 final_state.json。
- 速度沿用先前 IQ3S_MT1_AB 按輪 +4.26%（CI +2.15～+6.37），不是本次測得；未宣稱輸出逐 token 相同。無新 benchmark、無重建、無自動 fallback。

依 `.claude/skills/strata-checklist` 第 2 節格式。2026-10-27 建檔；以下 10/20 各筆為事後由 `state/overnight-20261020.md` 補登（非事前登記），數字以該檔為準。
雜訊參考：自由生成 CV 約 7%；replay 交錯 3 輪的 paired sd 約 1–3 tok/s。

## 2026-10-20 00:57｜ROUTE_PRIOR（VRAM-only 路由偏置）
- 類型：旋鈕（家族：路由偏置；env only，control binary 已內建）
- 假設：給 VRAM 常駐 expert 加 logit bonus，CPU/SSD miss 下降，waitCPU 縮短
- 目標段／上限：waitCPU（10/15 profile 17.37 ms/window，約 49%）
- 設計：n=3 交錯 fresh engine，10 個 Hermes 點，greedy
- 結果：CRP25/50/100 = +15.7/+30.7/+59.6%；SSD -16/-34/-50%。超過雜訊
- 根因／學到什麼：SSD 讀取量是主要槓桿；但輸出改變，0.25 看起來品質中性、0.5 邊緣、1.0 劣化（僅小樣本並列比對）

## 2026-10-20 00:57｜COLD_OVERLAP=1
- 類型：旋鈕（家族：I/O 重疊）
- 結果：campaign A +3.7%，campaign C -0.7% → 未重現，判定無效
- 根因：未查明（Windows direct unbuffered 路徑）；同家族不再加碼，除非有新證據

## 2026-10-20 00:57｜v0.2.0-beta
- 類型：結構（mainline 版本）
- 結果：預設 -36%，RAM_ADAPT=8 時 -16%
- 根因：沒有私有 RAM LRU；Linux-only 的 zero-copy/IO prefetch 在 Windows 不生效

## 2026-10-20 02:50｜GATE_SKIP（低路由權重 miss 直接跳過）
- 類型：結構（candidate source，SHA 89380A69..F923）
- 結果：tau .01/.02/.05 = +1.7/+4.9/+7.0%（雜訊內）；.075/.10 = +16.9/+41.3%（campaign C）
- 根因／學到什麼：ROUTE_TAIL_SKIP=7 已拿掉大部分低權重尾；tau≥0.075 才有效但輸出明顯改變，品質未評估

## 2026-10-20 02:50｜ROUTE_BIAS（VRAM+RAM tier bonus，保留 top-1）
- 類型：結構（candidate source）
- 結果：DB25/50/100 = +13.6/+22.6/+30.7%；DB25V100 = +39.3%、DB50V100 = +33.8%（VRAM bonus 1.0）
- 根因／學到什麼：只對 RAM tier 加分省 SSD 但 CPU 仍要算；加大 VRAM bonus 才把工作移到 GPU。campaign C 各臂沒做並列品質判斷

## 2026-10-27｜Nsight Systems 時間線（診斷，非 A/B）
- 類型：結構（家族：關鍵路徑／CPU-GPU 重疊）；control binary 不改，輸出不變
- 假設：如果 window 主要是「等 GPU ~12 ms」＋「CPU expert」串行相加，則縮短 GPU 段或填補兩邊空檔可回收數 ms/window，因為 10/15 decode-segments 各段相加 ≈ window（T1 20.0/24.8、T3 44.2/49.7）
- 目標段／上限：完全重疊時 T1 window 24.8 → ~12–13 ms（理論，依賴關係下不可達）
- 指標：每層 GPU busy/idle、CPU worker busy/idle、GPU 12 ms 的 kernel 組成、shared-expert fork 是否重疊
- 設計：n=1 診斷 trace（不計速度），另跑未插樁同設定參考 1 次
- 停止條件：遠端無 nsys → 停止回報，不安裝；trace 開銷使 tok/s 低於參考 30% 以上 → 只用作相對結構，不用絕對 ms
- 結果（16:33–16:52）：nsys 2026.5.1 已安裝；traced run 在 nsys 注入下只有 3135 slots（閘門 3153），依閘門停止，未收 trace。untraced ref 兩次 31.59／42.57 tok/s（冷啟動 512 token，差 35%，差在 CPU 段），GPU-reach wait 穩定約 12 ms。API 兩次皆還原（loaded、3153、SHA 不變）。報告：state/LUNA-20261012-027.nsys-timeline-20261027.md
- 根因／學到什麼：12 GB 卡只剩 254 MiB，nsys 佔 VRAM 導致 slot -0.57%；`nsys launch` 在此機會阻塞到目標結束
- 17:00 第 3 次（使用者同意重跑，traced 接受 ≥3135）：launch 指到上層資料夾，跑到舊 512-token 腳本，`ref` 資料夾已存在 → FileExistsError，未量測；runner 的 600 s 還原檢查逾時，但引擎 17:10 起來，18:47 核對 loaded／3153／SHA 正常
- 18:48 第 4 次：root 改為 attempt3（GEN 1024、ref/ref2/A/B、總上限 75 分），18:57 完成，API 18:56:47 還原（3153）
- 結果（trace-A，563 windows，45.98 ms/window）：GPU 真正工作 18.74 ms/window（其餘是 wait_flag_ge spin 等 host）；每層 pre（GPU attention+router）11.39 ms、post（等 CPU expert）25.92 ms，post 內 GPU 只忙 3.51 ms；CPU/GPU 只重疊 3.46 ms（7%）。post ≥1 ms 的長尾層（12% 的層）佔 post 54%，worker 多半閒置，成因未知
- 根因／學到什麼：交替確認；不改輸出可填的空檔只有 swap 拷貝約 1.79 ms + launch ≤0.5 ms（約 +5%）；最大未解項是 CPU 側長尾層（約 11.5 ms/window），需 symbol/osrt 再擷取
- Attempt 5 結果（長尾層，nsys CPU 取樣+WPR I/O，不改 source/設定）：long 層（12% 層）占 post 61%；host 同步 SSD 大讀取（prefetch 在 pool publish 之前，期間 worker 全閒置）每 window 4.3 次/7.3 ms，約占長尾 32%，其餘為 pool park/wake（5.4 ms，部分為追蹤 artifact）與其他；缺頁為 nsys artifact。attempt 3「host 無阻塞」為解析錯誤已更正。可行 exact-output 修法：讀取與 resident job 重疊（上限 ~4.5–7 ms/window，未量測）。API 已還原（20:16，SHA 不變）。報告：LUNA-20261012-027.nsys-timeline-20261027.md「Attempt 5」

## 2026-10-27 21:00｜MISS_OVERLAP：先算常駐 expert，再補讀 SSD
- 類型：結構（家族：關鍵路徑／CPU-I/O 重疊；改 source，預期位元相同）
- 假設：如果 expert_pool_dispatch_multi 不在建立 job 前同步讀完所有 miss（expert_source.cpp:3814），而是先讓 worker 算 RAM 常駐的 expert、讀取同時進行，則 window 時間下降，因為 attempt 5 量到同步讀取時 9 個 worker 全部閒置
- 目標段／上限：同步讀取等待 4.5（W）～7.3（A）ms/window；以 ref 37.17 ms 計約 +13% 上限
- 指標：decode tok/s（paired）、jobs/CPU ms/window、SSD MB/req、位元一致檢查
- 設計：同一 candidate binary 以 env 開關 off/on 交錯，另含 current-best 錨點；Hermes replay 10 題 × 3 輪
- 停止條件：位元一致檢查失敗 → 不跑 A/B；paired 中位數 < +3% 或 CI 跨 0 → 不採用
- 結果（夜間 00:19–01:51，見 LUNA-20261012-027.night-20261027.md）：MCHK 通過（6209 次 split、87992 列比對、0 不一致）。A/B 5 輪×10 點（block 合併 tok/s，按輪配對 df=4）：M vs D0 +2.05%（95% CI −5.4～+9.5）、M vs C0 +4.20%（CI −2.4～+10.8）、D0 vs C0 +2.18%（CI −1.3～+5.6）。逐點平均 df=9：+2.79%／+3.30%／+0.54%，CI 皆跨 0。未達事前訂的 +3% 且 CI 跨 0 → 依停止條件不採用（但為正向趨勢，非負）。機制有作用：neuro 1024 tokens 的 jobs 由 5.9／4.0 ms/window 降到 0.3，CPU 段同時由 14.9／13.0 升到 18.9／16.9（讀取等待移進 CPU 段），join_wait 仍約 3 ms/window，所以只回收一部分。
- 【夜間更新 2026-10-27 22:xx，事前登記，使用者尚未說「開始」】
  - Amdahl：目標 50 tok/s（20.0 ms/token）、現 37.6（26.6 ms/token），差距 6.6 ms/token（12.4 tok/s）。此方向上限 +13%（約 +4.9 tok/s）＝差距的約 40%，< 一半 → 單獨不可能達 50，即使成功也還需其他段（pool park/wake 5.4 ms、swap 拷貝 1.8 ms）一起動。
  - 設計定案：arms C0（current-best SHA 366A…15E2）、D0（候選 SHA 385E…30F5，開關關）、M（STRATA_MISS_OVERLAP=1）；5 輪交錯（schedule 輪替）、10 點、greedy、max_tokens 512、每 block 新引擎。先跑 MCHK（STRATA_MISS_OVERLAP_CHECK=1，128 tokens×10 點）。
  - 閘門：MCHK 出現任何 MISMATCH、check_bad≠0、split_calls<20 或 check_rows<100 → 整個 MISS_OVERLAP 家族中止。M vs D0 判定：paired 平均 ≥ +3% 且 CI 不跨 0 → 正面；D0 vs C0 用來量候選 binary 本身的開銷。
  - 雜訊：paired sd 約 1–3 tok/s；n=5 輪 × 10 點。判定時 df 用點數（10 點各自 5 輪平均 → df=9）或 block 配對（df=4），兩者都報。
  - 容量：候選 binary 只記錄 slots/RAM/locked，不要求等於 3153（控制 binary 嚴格 3153／20.00 GiB／20479 MiB）。

## 2026-10-27 22:xx｜MISS_OVERLAP_SPIN（事前登記，條件式）
- 類型：旋鈕（家族：I/O 重疊的 helper 自旋閾值；與 MISS_OVERLAP 同一家族，計為同家族第 1 筆）
- 假設：如果 helper thread 的 idle 自旋時間（STRATA_MISS_OVERLAP_SPIN_US，預設 20000）改 2000 或 100000，則 M 的 tok/s 改變，因為自旋決定 helper 在兩層之間是否被 OS 喚醒延遲拖累
- 目標段／上限：不超過 MISS_OVERLAP 本身上限（4.5–7.3 ms/window）；預期只修正其中一小部分
- 設計：只在 M vs D0 不是明顯負（paired 平均 > -3%）時跑；arms M、S2K、S100K，3 輪交錯，10 點，512 tokens
- 停止條件：兩個值都在雜訊內（|Δ| < 3%）→ 此家族掃完，不再加碼
- 結果：3 輪（M/S2K/S100K 交錯，按輪配對 df=2）：S2K vs M +5.24%（CI +0.2～+10.3；逐點 df=9 +6.93%，CI +1.6～+12.3）；S100K vs M +2.98%（CI −11.7～+17.6；逐點 +1.13%，CI 跨 0）。S2K 邊緣顯著，n 太小，需確認。

## 2026-10-27 22:xx｜NEURO_DECODE_BASELINE（事前登記，診斷）
- 類型：診斷（不改 source；家族：關鍵路徑）
- 假設：未插樁下，C0 與 M 的 engine-reported 各段（jobs / CPU / GPU-reach wait ms/window）能顯示 M 實際縮短哪一段
- 設計：neuro prompt（SHA 9350…18BA）、GEN 1024，C0/M/M/C0 交錯各 2 次，引擎 `strata decode timing` 行；若 MCHK 失敗則只跑 C0×2
- 停止條件：capacity 與閘門不符時只記錄；僅作新的參考，不做速度判定
- 結果：neuro 1024 tokens：C0 42.8／44.5 tok/s（window 38.42／34.36 ms；jobs 5.91／4.04、CPU 14.87／12.97、GPU-reach wait 11.77／11.83）；M 44.9／46.2（window 37.24／35.49；jobs 0.28／0.30、CPU 18.88／16.93、GPU-wait 12.25／12.22）。M 平均 +3.9%，但 C0 兩次本身差 4%。jobs+CPU：C0 20.8／17.0 → M 19.2／17.2 ms，只回收約 0–1.6 ms/window，遠小於 4.5–7.3 的上限：讀取（helper_read 約 3.5 ms/window）只有約 2.4 ms 與計算重疊，其餘 join_wait 約 3 ms/window。

## 待辦（2026-10-27 checklist）
- 下一個結構性步驟：對 DB25V100、DG100、CRP25 做 task-level 品質評估（未授權前不跑）

## 2026-10-28 02:30｜SPIN_CONFIRM（事前登記）
- 類型：旋鈕（家族：I/O 重疊／MISS_OVERLAP；此家族第 3 筆。前兩筆：M +2.05%（雜訊內）、S2K +5.24%（邊緣）→ 若本筆 S2K 仍在雜訊內，家族掃完，不再有旋鈕式實驗）
- 假設：如果 helper 的 idle 自旋改短（SPIN_US 2000／500），則 tok/s 比預設 20000 高，因為 helper 自旋與 9 個 pool worker＋host 搶 16 條執行緒的核心（i5-12600KF 6P+4E）；S2K 的第一次訊號 +5.2%
- 目標段／上限：上限仍是 MISS_OVERLAP 的 4.5–7.3 ms/window（已回收約 0–1.6），單獨不可能達 50 tok/s
- 設計：C0、M（預設 20000）、S2K、S500 共 4 臂；5 輪交錯、10 點、greedy、512 tokens、每 block 新引擎（20 block 約 75 分鐘）；之後 neuro 1024 的 C0/S2K/S2K/C0 取各段 ms/window
- 指標：block 合併 tok/s 按輪配對（df=4）＋逐點（df=9）；jobs／CPU／join_wait
- 停止條件：S2K vs M 的 CI 跨 0 且平均 < +3% → 家族結案；S500 與 S2K 皆正且 CI 排除 0 → 才進入下一步（把 S2K 當預設的來源變更，仍為候選，不部署）
- Identity：C0 SHA 366A…15E2、候選 SHA 385E…30F5；capacity 3153／20.00／20479；MCHK 沿用夜間 00:19 的結果（旋鈕只改自旋時間，不改輸出）
- 結果（02:19–03:34，75 分；block 合併 tok/s，按輪配對 df=4／逐點 df=9）：C0 36.59、M 36.92、S2K 38.83、S500 39.13 tok/s。S2K vs M +5.35%（CI −2.0～+12.7；逐點 +5.64%，CI +2.8～+8.5）；S500 vs M +6.13%（CI −0.7～+12.9；逐點 +5.65%，CI +1.5～+9.8）；S2K vs C0 +6.50%（CI −3.0～+16.0；逐點 +6.80%，CI +2.5～+11.1）；S500 vs C0 +7.45%（CI −5.0～+19.9；逐點 +6.70%，CI +3.2～+10.2）；M vs C0 +1.61%（逐點 CI 跨 0）。neuro 1024：C0 44.0／44.4，S2K 44.7／46.9（jobs 0.3、CPU 16.1／18.9）。
- 判定：停止條件（S2K CI 跨 0 且 < +3%）未成立（平均 +5.4～6.5%，逐點 CI 排除 0；與夜間 1 的 +5.2% 重現）→ 短自旋有效，S2K≈S500（平台），不再掃此旋鈕（家族結案：預設 20 ms 自旋太長，與 pool/host 搶核）。候選(S2K) 相對 current best 約 +6.7%（≈ 40 tok/s 的 Hermes replay），只是候選，不部署。
- 學到什麼：剩餘 join_wait 約 3 ms/window 受 SSD 帶寬限制（read_direct 已是 overlapped、合併至 32 MiB 請求），再加讀取平行度無明顯空間；要再降只能減少 miss（輸出會變）。

## 2026-10-28 04:10｜TIMER_RES（事前登記）
- 類型：結構（改 source 的 Windows 計時器／電源節流；家族：pool park/wake；env 開關，預設關，預期輸出位元相同）
- 假設：如果引擎行程要求 1 ms 計時器解析度（timeBeginPeriod(1) 並關閉 PROCESS_POWER_THROTTLING_IGNORE_TIMER_RESOLUTION），則 pool worker／host 在 park 後被喚醒的延遲不再量化在 15.6 ms 刻度，decode tok/s 上升，因為 Nsight 顯示 AlertByThreadId 喚醒延遲量化在約 15.6 ms，且 source 內完全沒有 timeBeginPeriod／SetProcessInformation／priority 設定（grep 確認）
- 目標段／上限：pool park/wake 5.4 ms/window（A，含追蹤成分，實際可能明顯較小）；以 ref 37.17 ms/window 計上限約 +14%，現實預期 0–5%；Amdahl：即使全中也只補到 ~42.5 tok/s，與 MISS_OVERLAP 上限不可相加
- 設計：從 current-best 源碼 COPY（runs	imer-res-20261028\source）加 generate.cpp 約 25 行；臂 C0、T1（STRATA_TIMER_RES=1：timeBeginPeriod(1)＋不忽略計時器解析度）、T2（=2：再加關閉 EXECUTION_SPEED 節流）；5 輪交錯、10 點、greedy、512 tokens、每 block 新引擎（15 block 約 55 分）；另跑 neuro 1024 的 C0/T1/T1/C0 取各段 ms/window
- 指標：block 合併 tok/s（按輪配對 df=4＋逐點 df=9）；GPU-reach wait／jobs／CPU ms/window；引擎啟動行確認 timer 設定生效
- 停止條件：T1 與 T2 vs C0 的 CI 皆跨 0 且平均 < +3% → 判無效，結案
- Identity：C0 SHA 366A…15E2；T 二進位 SHA 於 build 後記錄；capacity 3153／20.00／20479（候選只記錄）；build 在遠端以 belownormal 優先權、-j 2；不碰 canonical source

- 結果（04:16–05:15，59 分；T 二進位 SHA 3658CFE4…4EB0，引擎 log 確認 timeBeginPeriod(1)→0、SetProcessInformation→1）：block 合併 tok/s：C0 37.20、T1 36.55、T2 36.17。T1 vs C0 −1.50%（按輪 CI −15.8～+12.7；逐點 −1.63%，CI −6.9～+3.7）；T2 vs C0 −2.57%（按輪 CI −10.8～+5.7；逐點 −0.69%，CI −3.4～+2.0）；T2 vs T1 −0.41%。neuro 1024：C0 46.1／46.7，T1 47.3／46.2（window 37.9／33.6 vs 34.6／37.8；兩邊組內差異大於組間）。
- 判定：停止條件成立（T1、T2 的 CI 皆跨 0 且平均 < +3%）→ 無效，結案。pool 喚醒的 15.6 ms 量化在正式環境下不是可回收的瓶頸（或 nsys 追蹤放大了它），不再追計時器／電源節流。

## 2026-10-28 (morning)｜S2K_PROMOTION_CONFIRM（事前登記；使用者授權第 1 階段，不部署）
- 類型：確認（家族：I/O 重疊／MISS_OVERLAP；家族已結案，這筆是上線前確認，不是新旋鈕掃描）
- 假設：如果 MISS_OVERLAP＋SPIN_US=2000 對 current best 的 +6.5% 是真的，則 8 輪 ABBA 的按輪 CI 會排除 0，且抽樣模式與 neuro 暖機下不變慢
- 目標段／上限：jobs＋CPU 段；MISS_OVERLAP 上限 4.5～7.3 ms/window
- 設計：state/S2K_PROMOTION_PLAN_20261028.md 第 1 節（1a MCHK、1b greedy 8 輪 ABBA、1c production 抽樣 3 輪、1d neuro 暖機 C0/S2K/S2K/C0）；開跑前修訂（使用者，看資料前）：佇列排程工作改用 Task Scheduler priority 2，與 live API 相同，引擎應為 AboveNormal；絕對值不與前幾晚（priority 7）比較
- 停止條件：同計畫第 1 節判定（MCHK 失敗即停；按輪 df=7 平均 ≥ +3% 且 CI 排除 0 才算通過）
- 結果（2026-10-28 08:59–10:15，第 1 階段，優先權 2）：**通過**。MCHK 0/69896 不一致（split 5057）；1b greedy 8 輪 ABBA S2K vs C0 按輪 +8.49%（CI +5.91～+11.06，df=7），逐點 +9.75%（CI +5.85～+13.66），C0 42.81→S2K 46.42 tok/s，8 輪全正；1c 抽樣 3 輪 +4.00%（逐點 +5.83%）；1d neuro 暖機後 C0 50.28→S2K 53.08（+5.57%）；全 block OK、容量嚴格符合。jobs 8.5→0.24 ms、CPU +5 ms，淨回收約 3.3 ms/window。引擎優先權由佇列強制設成 AboveNormal（兩臂相同），live watcher 未動它。未部署；第 2 階段待另外授權。
- 部署（2026-10-28 10:27）：使用者授權後上線為 live current best（config／launcher 複本，原檔未動）；驗證與回滾見 LIVE_DEPLOYMENT.json；歷代表 CURRENT_BEST_HISTORY.md。

## 2026-10-28｜NEXT4 佇列（事前登記，S2K 確認結束後跑；不部署）
（10:27 S2K 已上線為 current best → 以下各項的對照臂改為 S2K（385E…30F5＋MISS_OVERLAP=1、SPIN_US=2000），PIN／AASYNC 在 S2K 上疊加；harness 辨識 live 的 binary 需先更新）共同設計：每臂 5 輪交錯、Hermes 10 點、greedy、512 tokens、每 block 新引擎、引擎 AboveNormal（與 S2K 確認一致）；block 合併 tok/s 按輪配對＋逐點，皆報 95% CI。判定：平均 ≥ +3% 且逐點 CI 排除 0 → 正面，另排確認；否則無效。

### PARTIAL_PIN（PCIe 路徑啟用）
- 類型：結構（只改計算位置，不改路由；家族：PCIe／pinned，首筆）
- 假設：如果用 STRATA_PARTIAL_PIN=1 把最熱的 8／16 GiB 註冊給 GPU，則 PCIe 路徑從 0.00 expert/層變成 >0，CPU 段縮短，因為目前 page-locking 被拒、pinned 0 GiB 使 PCIe 路徑從未啟用
- 目標段／上限：CPU 段（jobs＋CPU 約 17～21 ms/window）；紙上估約 +10%（PCIe 24 GB/s、每 expert 約 1.9 MB）
- 設計：current-best binary；臂 C0、PIN8（STRATA_PARTIAL_PIN_GIB=8）、PIN16；機制閘門：啟動行「GiB of it registered」>0 且 decode timing 的 PCIe/層 >0，否則記 NOT_APPLICABLE
- 指標：tok/s、PCIe 與 CPU experts/層、GPU-reach wait、啟動時間、VRAM free 警告
- 停止條件：兩臂皆 < +3% 或 CI 跨 0 → 家族結案（與 5070 的結論一致）
- 結果（11:20–12:56，優先權 2，5 輪，對照 S2K 44.29 tok/s；我方由 rows-AB.json 重算）：閘門通過（PIN8 註冊 8.00 GiB、PIN16 實際 14.00 GiB；PCIe 1.14／1.88 expert/層-window）。PIN8 45.78，按輪 +3.38%（CI −1.9～+8.7），逐點 +6.89%（CI +0.9～+12.9）→ **依事前標準為正面，需確認**。PIN16 44.54，+0.58%（逐點 CI −0.3～+6.8）→ 無效。機制：CPU 段 33.0→27.2（PIN8）／25.6（PIN16）ms，但 GPU-reach wait 11.9→13.4／15.8 ms，pin 越多 GPU 端越成為瓶頸，8 GiB 附近是甜蜜點。

### ADAPT_ASYNC
- 類型：結構（只改 swap 時機；家族：adaptive，首筆非同步）
- 假設：如果 --adapt-async 1，則阻塞式 swap 拷貝（約 1.8 ms/window）移出關鍵路徑
- 目標段／上限：約 1.8 ms/window → 最多約 +5%
- 設計：current-best binary；臂 C0、AA（--adapt-async 1）；閘門：啟動行確認 async 開啟、exchange pinned 成功、實際有 swap，否則記 NOT_APPLICABLE（不量阻塞式 fallback）
- 停止條件：< +3% 或 CI 跨 0 → 無效
- 結果：AA 45.90，按輪 +3.69%（CI −1.5～+8.9），逐點 +4.35%（CI +0.4～+8.3）→ **依事前標準為正面，需確認**。async 開啟、exchange pinned 成功；CPU 段 33.0→30.9 ms，GPU wait 不變。

### PATCH4 分塊完成通知
- 類型：結構（改 source，預期位元相同；家族：I/O 重疊／MISS_OVERLAP 延伸——本家族旋鈕已結案，這筆是結構改動）
- 假設：如果 SSD 讀取切成小塊、每塊落地就讓 worker 計算，則 join_wait（約 3 ms/window）大部分消失，因為目前 worker 算完常駐 expert 後要等整批讀完
- 目標段／上限：約 3 ms/window → 最多約 +8%（疊在 S2K 上）
- 設計：先 CHECK 模式位元比對（0 不一致才繼續）；臂 S2K、P4（P4＋SPIN 2000）、C0 錨點
- 停止條件：CHECK 失敗即停；P4 vs S2K < +3% 或 CI 跨 0 → 不採用
- 結果：CHECK 通過（chunk 8／16 皆 0 不一致，join_wait 歸 0、chunk_wait 約 3.1～3.4 s/run 取而代之）。P4_8 44.16（−0.29%，CI −2.1～+1.6）、P4_16 43.62（−1.42%，逐點 −2.32%）→ **無效，不採用**。根因：等待只是從 join_wait 換成 chunk_wait，總量不變——瓶頸是 SSD 讀取本身的總時間（helper_read 約 6 s/run），不是通知粒度；小塊反而降低合併效率。MISS_OVERLAP 家族至此結案。

### CPU_BW_DIAG（診斷，非 A/B）
- 類型：診斷（不改 source）
- 假設：如果 CPU expert kernel 的實際讀取頻寬遠低於本機 DRAM 頻寬上限，則 kernel 改寫（AVX-VNNI、預取）還有空間；接近上限就結案
- 設計：用 decode timing 的 CPU us/expert 與 expert blob 大小算 kernel GB/s；在遠端以自寫小程式量 DRAM 頻寬（不下載第三方工具）
- 結果：本輪未另做頻寬量測（依交辦只用既有 timing；尚未算 GB/s），保留待辦。

## 2026-10-28 13:xx｜PINAA_CONFIRM（事前登記；使用者授權，不部署）
- 類型：確認（家族：PCIe／pinned 第 2 筆、adaptive async 第 2 筆；NEXT4 中 PIN8、AA 為正面需確認）
- 假設：如果 PIN8（+6.9% 逐點）與 AA（+4.4% 逐點）為真，則 8 輪下按輪 CI 排除 0；兩者動不同段（PCIe 分流 vs swap 時機），PA（PIN8+AA）可疊加；PIN6 用來找 pin 量甜蜜點
- 目標段／上限：CPU 段（PIN）與阻塞 swap 約 1.8 ms/window（AA）
- 設計：current best S2K 為對照；臂 S2K、PIN8、PIN6、AA、PA；先探測 PIN6／PA 機制閘門（PIN 註冊 >0 且 PCIe/層 >0；PA 另需 async 開啟）；A/B 8 輪輪替、10 點、greedy、512 tokens、每 block 新引擎、優先權 2／AboveNormal、嚴格容量（pin 臂為 locked+registered=20480 MiB）
- 判定：按輪配對（df=7）平均 ≥ +3% 且 CI 排除 0 → 通過，可擬部署；平均 ≥ +3% 但 CI 跨 0 → 證據不足；< +3% → 無效。PA 需優於 PIN8 與 AA 中較佳者才算疊加成立
- 結果（13:09–15:08，8 輪，對照 S2K 44.75 tok/s；我方由 rows-AB.json 重算）：PIN8 44.56（按輪 −0.50%，CI −4.4～+3.4；逐點 +2.41%，CI 跨 0）、PIN6 45.25（+1.17%，CI −1.2～+3.5）、AA 45.28（+1.28%，CI −3.6～+6.2）、PA 42.19（−5.54%，CI −11.6～+0.5）→ **全部無效**。PA 另有穩定性問題：p05 在 8 輪中 4 輪回 HTTP 400（PIN8 單獨、AA 單獨都沒有），組合不可用。機制有作用但淨效益抵銷：PIN8 CPU 段 −2.2 ms、GPU-reach wait +1.4 ms。NEXT4 的 PIN8 +6.9%／AA +4.4%（逐點）未重現，判為 5 輪雜訊。PCIe／partial pin 與 adapt-async 兩家族結案（皆 2 筆、累積收益在雜訊內）。live S2K 已還原：SHA 385E…30F5、AboveNormal、loaded、3153／20479（final_verify 的 verified=false 是腳本讀 cmdline 的 KeyError，非還原失敗）。

## 2026-10-28 15:xx｜CPU_BW_ROOFLINE（事前登記，診斷，第 1 階段）
- 類型：診斷（不改 source、不改 live；家族：CPU kernel 效率，首筆）
- 假設：如果 CPU expert 計算是記憶體頻寬受限且已接近本機 DRAM 實際頻寬，則 kernel 改寫沒有空間（結案）；若有效頻寬明顯低於實測上限，差距來自 kernel 效率、pool 開銷或 E-core 拖尾，值得進第 2 階段
- 已知數據（s2k-confirm rows-GREEDY，C0，讀取不在 CPU 段內）：CPU 段 19.36 ms/window、6.09 expert/層-window、65.9 µs/expert（wall，9 worker 並行）、1.835 MB/expert → 有效約 28 GB/s
- 目標段／上限：CPU 段約佔 window 60%；若可逼近實測頻寬的 80%，紙上上限 +15～30%
- 設計：自寫 AVX2 讀取頻寬程式（不下載第三方工具），遠端 MSVC 編譯；量 1 P-core、1 E-core、6 P-core、9 worker 同組 LP（2,4,6,8,10,12,13,14,15）、16 LP；連續大塊讀與「隨機 1.8 MB 區塊」讀兩種模式；記錄 DIMM 型號／速度／條數。live API 不停（閒置），測試約 1 分鐘
- 判定：9-worker 隨機 1.8 MB 讀的實測頻寬 ≤ 1.25×28 GB/s（≤35）→ 已近上限，CPU kernel 方向結案；≥ 1.6×（≥45）→ 進第 2 階段（拆解 kernel／pool／E-core 各佔多少）；介於中間 → 回報，由使用者決定
- 結果（15:4x，live API 閒置未停，CPU 負載 6%）：記憶體 DDR4-3200 雙通道 2×16 GB（TEAMGROUP-UD4-3200，理論 51.2 GB/s）。實測讀取頻寬：1 P-core 25.5（隨機 1.8 MB 塊 25.9）、1 E-core 19.3、6 P-core 執行緒 44.5、9 worker LP 45.7（隨機 1.8 MB 塊 45.7）、16 LP 45.3 GB/s——6 條 P-core 執行緒就已飽和，E-core 不增加總頻寬。注意 worker LP 12～15 都是 E-core（P-core 只有 LP 2,4,6,8,10）。kernel 有效頻寬 28 GB/s＝實測上限的 61%（1.63×）→ 依事前標準（≥45）**進第 2 階段**。紙上上限：C0 CPU 段 19.4 ms/window 若達 45.7 GB/s 可降到約 11.9 ms，省約 7.5 ms/window（約 +15～20%）。第 2 階段要拆差距來源：單執行緒 IQ3 kernel 的 GB/s（kernel 本身）vs 9 worker 並行（分工、E-core 拖尾、每層同步／喚醒）。

## 2026-10-28 16:xx｜POOL_WORKER_SKEW（事前登記，診斷，CPU_BW_ROOFLINE 第 2 階段）
- 類型：診斷（只加計時的診斷 build，輸出應不變；家族：CPU kernel 效率／pool 協調）
- 假設：如果 kernel 有效頻寬只到實測上限 61% 的差距主要來自並行協調（等列數切分＋4 個 worker 在 E-core，單核頻寬 19 vs 25 GB/s；expert 成本因 nt 不同），則每層 P-core worker 會明顯早於 E-core worker 完成，host 完成等待佔 CPU 段的大部分
- 依據：10/15 pool-split 拆解（gate/up 73%、T=3 完成等待 5.7 ms/window，提議依成本切分但未做）；今天頻寬 45.7 GB/s vs kernel 28 GB/s
- 設計：以 S2K 源碼（runs\miss-overlap-20261027\source）複本加每 worker 每層計時（開始、結束、處理位元組），參考 runs\pool-split-20261015-r3 的 split_trace 作法；neuro 1024 × 2 次，優先權 AboveNormal；live 停約 30 分鐘，finally 還原 S2K
- 指標：每層各 worker 的忙碌時間與完成時間差（P 群 vs E 群）、worker 閒置等待佔比、各 worker 有效 GB/s、單執行緒 kernel GB/s（若可行）
- 判定：E 群平均完成時間比 P 群晚 ≥ 20% 且等待 ≥ CPU 段 25% → 第 3 階段實作依速度／成本分配（位元相同）；否則回報差距另有來源
- 結果（18:49–18:54，ON1／ON2 計時＋MIC 微基準＋OFF 對照，皆 1024 token OK；我方由 raw 重算）：E 群平均完成時間比 P 群晚 **12.5%**（<20%），host 完成等待佔 pool call **18.2%**（容量閒置算法 16.3%，都 <25%）→ **不成立，不進第 3 階段依速度分配**。任務動態領取，E 群 4 條只做 27% 列、P 群 5 條加 host 做 73%；等列數切分不因 nt 失衡（平均 nt P 1.20／E 1.21，GB/s 不隨 nt 變）。差距來源是 kernel 本身：單核 gate/up kernel 只有約 3.8 GB/s（同核純讀 27.7 GB/s），9 worker 並行時 P 執行緒仍 3.7 GB/s、E 約 1.7–2.0 GB/s，即 kernel 在每核是算力受限（解碼），不是記憶體頻寬也不是排程；理論上 kernel 加速才能逼近 45.7 GB/s。排程殘留空間上限約 2 ms/window（約 6%），實務 ≤3%，在雜訊內。微基準位元組數有約 ±15% 不確定（見報告）。live S2K 已還原驗證（loaded、3153、20.00 GiB、20479 MiB、SHA 385E…30F5）。詳見 state/WORKER-SKEW-20261028.md。

## 2026-10-28 19:xx｜IQ3_KERNEL_PROBE（第 1 階段機制探查，只讀 source，不跑 benchmark）
- 類型：診斷（家族：CPU kernel 效率，第 3 筆；不改 source、不連 live）
- 假設：如果 gate/up kernel 的 3.8 GB/s/核有位元相同的加速空間，則可把 gate/up phase 從算力受限推向 DRAM 受限
- 讀到的事實（S2K 源碼複本 native_expert.cpp、iq_avx2.cpp、expert_layout.cpp）：nt < STRATA_IQ_MT_MIN（預設 2）的 gate/up 走 ggml-cpu 的單 token vec_dot；nt ≥ 2 走 Strata iq256（P-core 自動 gather、AVX-VNNI）。源碼註解：多 token kernel 在 3 token 快 2.0–2.4 倍、1 token 不快，「都受 codebook 查表限制，約 5 GB/s/核」。iq256 的浮點加總順序與 ggml 不同 → 換 kernel 對 nt=1 不是位元相同
- 拆解（由 WORKER-SKEW 數字重算）：gate/up phase 總計 6×3.7+4×1.73 ≈ 29 GB/s（單核單獨 3.8，並行無損 → 算力受限），約佔 pool 時間 67%（≈8.8 ms/window）；down phase 6×5.45+4×2.89 ≈ 44 GB/s ≈ DRAM 實測 45.7 → **已是 DRAM 受限**（WORKER-SKEW 報告說 down 在 pool 內慢一半「原因未拆」，其實是頻寬飽和）
- Amdahl 上限：gate/up 解碼無限快 → 變 DRAM 受限 8.8→約 5.6 ms，省約 3.2 ms／32.8 ms ≈ **+11%**（需 kernel ≥1.57×）；kernel 1.3× ≈ +6.5%、1.2× ≈ +4.7%
- 既有反證（同一台機器）：10/08 STRATA_IQ_MT_MIN=1（nt=1 改走 iq256 gather+VNNI）中位 46.66→43.84（約 −6%，n=3）；10/10 PR863 P-core gather／AVX-VNNI 移植 +0.05%，拒絕；10/05 sign 查表（IQ2 pack）單核慢 7–13%
- 結論：上限過第 0 階段篩選（>5%），但已知兩種替代解碼在 nt=1 都沒贏 ggml，沒有新的、有證據的解碼想法；改存成免查表格式會多約 33% 位元組，RAM 層容量下降、miss 增加，預期淨負。kernel 方向暫停，除非做第 1 階段微基準證明某個 nt=1 解碼 ≥1.3× ggml

## 2026-10-28 19:xx｜IQ3_NT1_MICROBENCH（事前登記，第 1 階段機制探查；使用者授權，不停 live、不部署）
- 類型：診斷微基準（家族：CPU kernel 效率，第 4 筆；不改 live、不改遠端 canonical source，只在 runs\ 複本 build 小工具）
- 更正 IQ3_KERNEL_PROBE：10/08 MT_MIN=1 的 −6% 為 n=3、對照組 ±10% 散佈，不足以當反證；10/10 PR863 只動 nt≥2。nt=1 是否有更快解碼仍未被檢驗
- 假設：如果 P-core 上 gather（＋VNNI）解碼在 nt=1 比 ggml vec_dot 快 ≥1.3×，則值得寫一個位元相同（照 ggml 的整數 lane 與浮點累加順序）的 nt=1 kernel
- 目標段／上限：gate/up 約 8.8 ms/window；CPU 段整體下限為 DRAM（約 445 MB/window ÷ 45.7 GB/s ≈ 9.7 ms vs 現在 13.1 ms）→ kernel＋交錯合計上限約 +11%
- 設計：真實 IQ3_XXS（type 18）gate/up 列，多層多 expert（輪替超過 L2），單執行緒釘 P-core（另測 1 個 E-core 參考），臂：A ggml vec_dot（現行 nt=1 路徑）、B iq256 gather+VNNI、C iq256 gather 無 VNNI、D iq256 無 gather；暖／冷兩種；每臂多次重複取中位數；記錄 B/C/D 對 A 的最大差（預期非 0，因加總順序不同）
- 判定：P-core 上最佳臂 ≥1.3× A → 第 2 階段（寫位元相同 nt=1 kernel＋parity）；<1.15× → kernel 家族結案；介於中間 → 回報
- Hermes／neuro 差距拆解：使用者指出差距主要來自 VRAM hit 與 neuro 1024 長輸出暖機，已知原因，不另做
- 結果（2026-10-28 07:2x，單執行緒，實際 IQ3_XXS 66 個 expert／82.8 MB，6 個 type18 層 L35/36/41/44/45/47，每臂 25 次交錯重複）：P-core LP11 stream 中位 A ggml 247.1 µs/expert（5.08 GB/s）、B gather+VNNI 210.7（5.95，**1.172×**）、C gather 219.1（1.128×）、D 無 gather 241.3（1.024×）；LP1 同樣 B 1.174×；warm 狀態 B 1.155×/1.171×（LP11/LP1）。stream≈warm → 單核是算力受限，不是 DRAM。**最佳臂 B 約 1.17×，落在 1.15–1.30 之間 → 依事前判定「回報使用者」，不自動進第 2 階段**。B/C/D 彼此輸出逐位相同，與 A 差：max_abs 7.2e-7（max|A|=3.72，約 1.9e-7 相對滿刻度）、max_rel 7.4e-4（近 0 值）、約 52% 的值不同；A 重複間逐位相同。E-core LP15（live idle，worker parked）：A 499.7 µs、D 0.90×、B/C（強制 gather）0.26×（gather 在 E-core 慢 4 倍，與現行 cpu_gather_fast_here 一致）。Amdahl 粗估：若只有 P-core 換 B（1.17×），gate/up 8.8 ms 省約 1.3 ms／32.8 ms ≈ +4%，且 E-core 不受益、需位元相同改寫。VNNI 已編入（STRATA_AVXVNNI=1，iq256_variants()=3）。live SHA 385E…30F5／AboveNormal 前後不變。詳見 state/iq3-nt1-bench-20261028/IQ3-NT1-BENCH-20261028.md
- 協調者核對（由 raw 重算中位數一致）：P-core stream B 1.171–1.174×，判定落在 1.15–1.30「回報」。**重大更正**：這個 pack 的 48 層 gate/up 只有 6 層是 IQ3_XXS；其餘 IQ3_S 13 層、IQ2_XS 10、IQ2_S 10、IQ2_XXS 9（down 為 q2_0 或 iq4_nl）。所以先前「IQ3 kernel」的說法不精確，單改 IQ3_XXS 的效益約 6/48 × P-core 73% × 8.8 ms × (1−1/1.17) ≈ 0.12 ms/window（約 +0.4%），可忽略；子代理的 +4% 估計假設所有層都是 IQ3_XXS，不成立。要判定 kernel 家族得量全部 5 種型別的 nt=1（IQ3_S 有 gather 版，源碼註解稱 14900KF P-core 單 token 0.34→0.19 ms，且已有 opt-in STRATA_IQ3S_MT1）

## 2026-10-28 20:xx｜IQ_ALLTYPES_NT1_MICROBENCH（事前登記，使用者授權，不停 live、不部署）
- 類型：診斷微基準（家族：CPU kernel 效率，第 5 筆；IQ3_NT1_MICROBENCH 的延伸）
- 假設：如果 IQ3_S（13 層）在 P-core 單 token 用 gather 版比 ggml 快接近源碼註解的 1.8×，則整體 CPU 段可省數 ms，值得用現成開關 STRATA_IQ3S_MT1=1（或 STRATA_IQ_MT_MIN=1）做整機 A/B
- 設計：同一工具，型別 IQ3_S(21)、IQ2_XS(17)、IQ2_S(22)、IQ2_XXS(16)（IQ3_XXS 已測），各取多層多 expert 超過 L3；臂 A ggml vec_dot、B iq256 gather+VNNI、C gather、D 無 gather（無 gather 版的型別只跑 A、D 與 VNNI）；P-core LP11、LP1，25 次交錯，中位數；E-core LP15 只跑 A 與 D（短）
- 判定：以層數×P-core 列占比（73%）加權後，估計整體 gate/up 省時 ≥ 1.5 ms/window（約 +4.5%）→ 進整機 A/B（現成開關，會改四捨五入，非位元相同）；< 0.7 ms → kernel 家族結案；介於中間 → 回報
- 結果：（2026-10-28，單執行緒，每型 66 expert／56–93 MB，stream，LP11／LP1 各 25 次）各型層數 IQ3_XXS 6、IQ3_S 13、IQ2_XS 10、IQ2_S 10、IQ2_XXS 9（共 48）。P-core LP11 最佳臂對 A：IQ3_S 1.78×（LP1 1.90×）、IQ2_XS 1.24×、IQ2_S 1.26×（無 gather+VNNI；gather 版反而 0.90×）、IQ2_XXS 1.085×（IQ3_XXS 1.17×）。E-core LP15（live idle）：IQ3_S 無 gather 1.62×、IQ2_S 1.27×、IQ2_XXS 0.99×、IQ2_XS 0.785×、IQ3_XXS 0.90×；gather 臂在 E-core 0.35–0.65×。所有臂彼此逐位相同、對 A max_abs ≤7.2e-7（約 2e-7 滿刻度），A 重複逐位相同。加權（A_us×層數 權重，總 13224.7；省 3570.9 → 27.0%）×73%×8.8 ms = **1.735 ms/window ≥ 1.5 → 建議整機 A/B**（現成開關，非位元相同）：優先 STRATA_IQ3S_MT1=1（粗估 P 1.12＋E 0.37≈1.5 ms，只動 IQ3_S）；STRATA_IQ_MT_MIN=1 粗估 P 1.41＋E 0.30≈1.7 ms，但 P-core IQ2_S 0.90×、E-core IQ3_XXS 0.90×／IQ2_XS 0.785× 為損失。為單執行緒外推，引擎內不一定成比例。live SHA 385E…30F5／AboveNormal／idle 前後不變。詳見 state/iq-alltypes-nt1-bench-20261028/IQ-ALLTYPES-NT1-BENCH-20261028.md
- 協調者核對（由 raw_t16/17/21/22 重算 stream 中位數，與子代理一致）：IQ3_S P-core gather 1.78×（LP11）／1.90×（LP1），E-core 無 gather VNNI 1.62×；IQ2_S P-core gather 0.90×（反而慢）、無 gather 1.21–1.26×；IQ2_XS P 1.24×／E 0.79×；IQ2_XXS 約 1.08×／0.99×。結論：先前「kernel 家族結案」的判斷錯誤——瓶頸主要在 IQ3_S（13 層）的 ggml AVX2 解碼慢，Strata 已有的 iq256 kernel 在 nt=1 就快很多。下一步：整機 A/B `STRATA_IQ3S_MT1=1` 對 S2K（非位元相同，只是浮點加總順序不同，max_abs ≤7.2e-7；效果約 +4%，低於輸出改變類 8 輪 MDE 5.7%，判定要加看引擎自報的 CPU 段 ms 與更多輪數）

## 2026-10-28 21:xx｜IQ3S_MT1_AB（事前登記；使用者授權「你先跑」，不部署）
- 類型：旋鈕（現成開關 `STRATA_IQ3S_MT1=1`；家族：CPU kernel 效率，第 6 筆；非位元相同，只改浮點加總順序）
- 假設：如果 IQ3_S（13 層）單 token 改走 iq256（P-core gather+VNNI 1.78–1.90×、E-core VNNI 1.62×），則 CPU 段每 window 省約 1.1–1.5 ms，Hermes tok/s 約 +3–4%
- 設計：臂 S2K、MT1（S2K＋STRATA_IQ3S_MT1=1，STRATA_IQ_MT_MIN 保持未設）、S2K'（S2K 第二份，A/A 對照量雜訊）；Hermes replay greedy 10 點、512 tokens、每 block 新引擎、10 輪輪替、優先權 2／AboveNormal、嚴格容量 3153／20.00／20479；沿用 pinaa_queue 架構
- 指標：block 合併 tok/s（按輪配對）、引擎自報 CPU 段 ms/window（機制）、A/A 差
- 判定：MT1 vs S2K 按輪平均 ≥ +3% 且 CI 排除 0 → 通過，可擬部署（另請授權）；CPU 段 ms 降 ≥0.7 ms 但 tok/s CI 跨 0 → 回報「機制成立、速度證據不足」；CPU 段沒降 → 無效。A/A 差 >3% 視為環境不穩，結果標示不可靠
- 結果：（2026-10-28 19:48–21:14，10 輪×3 臂、Hermes greedy 10 點×512、嚴格容量 3153／20.00／20479、引擎 AboveNormal，31 block 全 OK）MT1 vs S2K 按輪配對 **+4.26%**，95% CI（df=9）**[+2.15, +6.37]**，按點 +6.84% [+3.29, +10.39]；A/A S2KB vs S2K −2.03% [−4.27, +0.22]（|差|<3%，環境可用）；MT1 vs S2KB +6.47%。引擎自報 CPU 段 26.10→23.92 ms/window（配對 −2.19，CI [−3.61, −0.76]），GPU-reach wait 不變（−0.007）；A/A CPU 段 +1.78（CI [−1.05, +4.61]，雜訊約 ±2 ms）。依判定：≥+3% 且 CI 排除 0 → **通過，可擬部署（另請授權，未部署）**。機制探針：引擎程序環境確有 STRATA_IQ3S_MT1=1、無 STRATA_IQ_MT_MIN、容量嚴格；引擎沒有印 kernel 選擇行（僅「AVX-2」一行）。輸出長度：MT1 每 block 多約 +181 token（+11%），與 S2K 同長度的點僅 4/100（S2KB 為 36/100），tok/s 可能略偏有利 MT1，但按點與 ms/window 同向。live 已還原並驗證（PID 19076、SHA 385E…30F5、--serve、AboveNormal、MISS_OVERLAP=1／SPIN_US=2000、3153／20.00／20479）；停機約 86 分。已修 final_verify 的 cmdline KeyError。詳見 state/iq3s-mt1-ab-20261028/IQ3S-MT1-AB-20261028.md
- 協調者核對（由 rows-AB.json 重算，與子代理完全一致）：MT1 vs S2K 按輪 +4.26%（CI +2.15～+6.37），CPU 段 −2.19 ms/window（CI −3.61～−0.76）；A/A −2.03%（CI −4.27～+0.22）。輸出長度偏差：MT1 平均長約 17%（log 比 0.159），對照組內 tok/s 對長度的彈性 0.057 → 長度偏差約 +0.9%，扣除後約 +3.3%，CI 仍排除 0。live 還原再確認：PID 19076、SHA 385E…30F5、AboveNormal、3153／20.00／20479。判定「通過，可擬部署」成立；部署需使用者另行授權

### HERMES_CPU_PHASE_DIAG identity deviation（2026-10-29 00:34）
首輪PROBE、C以Normal執行，O中途於00:34:27改AboveNormal，因此首輪C/O速度對比排除；保留計時守恆資料。已啟動只限已核對controller子孫和兩個核准SHA的priority watcher，後續需以逐PID調整時間早於request佐證，不能直接聲稱全程AboveNormal。原runner繼續，不中斷/重啟，不promotion。

## 2026-10-29 00:52｜UNMAPPED_DIRECT_READ_PROBE（事前登記；等待phase runner結束後）
- 類型：結構診斷，家族：Windows GGUF mapping與direct I/O，不掃worker/affinity/spin。
- 假設：本機保存並核對的read_direct註解指出NTFS對mapped/cached file可能序列化unbuffered I/O；本機器是否有同樣問題未確認。保持原始量化bytes，改從未映射獨立檔案讀取，可能降低helper issue/wait。
- 目標／上限：三輪D已完成30請求2838windows，CPU24.4965、GU11.8793、down5.1629、join6.0902、LRU1.1957ms/window；helper issue/wait8.0163但重疊不能當可回收收益。理想可回收join至多6.09ms，大於2.47ms目標缺口；若reader提升1.5倍，僅粗估helper8.02*1/3=2.67ms，實際須看critical-path測速。
- 設計：先只做隔離I/O probe，使用新建同bytes的小型direct-write shadow檔，mapped/unmapped兩份，512KiB與2MiB請求QD16，6輪交錯；n=6為機制篩選，不是模型tok/s promotion。未映射檔不得用buffered copy/hash讀取，以免失去對照語意。記bytes/hash、每round吞吐、read錯誤；API不生成、沒有其他runner/build才可執行。
- 停止：ReadFile錯誤、byte不符、process gate失敗即停，不fallback；沒有一致至少15%改善便不做全模型shadow/build/A/B。小樣本有映射/物理placement與SSD快取等殘留混雜，不能宣布因果定論。具體probe程式尚未實作/啟動。
- Identity：下一步重新核對hostname、current-best385E…30F5、live API env/config、process用途與source。現有測試仍live，禁止同時啟動此probe。C盤實讀Free69,365,649,408 bytes；兩GGUF47,039,860,096及28,800,138,432 bytes，完整雙副本不合容量，不能自行刪資料。若機制成立，只考慮明確定義第一shard影子讀取等可容納方案，不能當原流程失敗後fallback。
- 初測結果：512KiB unmapped平均+203.74%，paired95%CI+126.33..281.14%，6輪皆正；2MiB平均+57.22%但CI-11.19..125.63%，不能稱穩定。兩256MiB shadow完整direct-read SHA256相同。新證據支持一個同檔案mapping切換確認，不先拷完整模型。
- 確認設計（01:00前事前登記）：同一U檔先不map、後map，M檔全程mapped reference；每階段6輪、同兩種chunk、交錯U/M，用U/M比例在mapping前後是否收斂到1排除固定SSD extent差異。時間順序/cache仍是限制。輸出confirm-mapping.json，獨立不覆寫原probe，已存在就停、不重跑。
- Preflight偏差：初測外層health誤用127.0.0.1而服務只bind<tailscale-host>，非terminating錯誤未阻擋probe；當輪已有runner final_verify和實際process/SHA gate。其後已用實際<tailscale-host>:8080核對loaded=true及PID27736 AboveNormal，沒有restart/fallback。後續shell明設ErrorActionPreference=Stop並用正確bind。

## 2026-10-29 01:0x｜FIRST_SHARD_DIRECT_SHADOW（事前登記）
- 類型：結構，家族：Windows映射檔direct I/O來源；不是硬體/量化/路由調整。
- 假設：同bytes第一GGUF shard改從未映射副本讀，原mapping仍供既有其他用途；減少NTFS direct I/O序列化，縮短helper/join。小型同檔map前後probe支持，但未證模型收益。
- 目標／上限：Hermes診斷join6.09ms/window，可回收理想上限大於2.47ms缺口；只第一shard，實際份額須用counter核對。LRU/worker/spin不動。
- 準備：第一shard47,039,860,096 bytes，direct-write shadow尾補640零bytes至4096對齊；source完整prefix SHA與shadow完整prefix SHA相同、source size/mtime前後相同；不buffered hash或map shadow。C盤free68.83GB，複製後約21.79GB，要求保留10GiB；不刪既有資料。大檔在runs/unmapped-shadow-20261029，不入Git。
- 身分／失敗閘門：hostname DESKTOP-LKMLUPC、current-best385E…30F5；每次操作先盤點已分類API/memory-policy，沒有其他test/build。shadow env啟用時來源path需精確命中、大小／FileId分離／讀取成功；任何錯誤中止，不cached fallback。預設未啟用走原流程。
- 設計：候選source基於本輪已核對diagnostic source（2294D6…3658），原C7F4…3FA54 exe先獨立保存；current-best/live source不動。先shadow+MISS_OVERLAP_CHECK三點128tokens、capacity/rows/source bytes檢查；通過再C/O/S（原MT1／新exe開關off／新exe開關on）Hermes10點512tokens、至少5輪交錯，依按輪及逐點配對CI判斷。DIAG只另跑一輪確認機制，不拿其tok/s作promotion。新引擎明設AboveNormal並記錄開始時間；溫度使用既有replay契約，live不改。
- 指標：decode tok/s、總時間/輸出tokens/windows、join/helper/copy、first-shard shadow read bytes/count、SSD bytes/miss、slots3153/20.00GiB/20479MiB、有效GPU集合與cache配置不變。
- 停止：任何bytes/rows/identity/capacity/未命中錯誤即停；前三輪一致負或無機制效果則不加碼；5輪需平均至少+3%且CI不跨0才候選正面，否則維持MT1。最晚06:50停止新增run、07:00結束自有測試恢復MT1 API；不改溫度、不停止無關程序、不加fallback。
- FIRST_SHARD_DIRECT_SHADOW結果（01:20）：NOT_APPLICABLE/REJECTED_BEFORE_BENCH。BAD_PATH在expected exactly one source match中止，沒有正式性能樣本；MT1 API自動恢復且verified。根因：未先檢查exists(experts.bin)，實際CPU讀42.91GB experts.bin，current best已drop_mapping且實際startup log確認closed；native GGUF47GB副本不被使用。已清理自己新建副本47,039,860,736 bytes，保留copy/phase/build/negative evidence。微基準不能外推此runtime；此方向不再加碼，轉native GU/down pipeline。

## 2026-10-29 01:28｜NATIVE_GU_DOWN_PIPELINE（事前登記）
- 類型：結構，家族：native CPU GU/quant/down工作資料流；worker/affinity/spin/溫度/路由/量化/GPU集合不變。
- 假設：每expert GU tiles完成即量化發布down，其他expert GU繼續；GU偏compute、down偏bandwidth可混用，移除全batch barrier。不是把全部GU先claim完才跑down。GU仍有任務可claim時，down同時工作上限固定max(1,threads/3)，尾端放開至threads保持work-conserving；只試這個預設策略，不掃配額。
- 目標／上限：Hermes GU11.879+down5.163+quant0.144=17.186ms/window；完全重疊down理想上限5.16ms，實際共享RAM/AVX與少GU核心可能吃掉收益。補50需2.47ms/window（combined約14.4%）；不承諾3..6%估算為實測。
- 實作：opt-in STRATA_NATIVE_PIPE=1、固定每expert GU/Down row parts，最後GU完成者量化後release ready，down acquire後讀取。原phase5/6保留作reference。mode7每worker/host一個drain token，全部down結束才返回、確認park才換batch。每expert具原子gu_left/ready/down_next；量化函式native_quant_h已targeted確認只寫dst，沒有共享scratch。新增pipeline wall單獨counter，不污染GU/down計時語意。
- 正確性：STRATA_NATIVE_PIPE_CHECK=1每batch保存pipeline output rows，原分段路徑重算bitwise memcmp；任何mismatch/stall立即abort，無容錯或fallback。先Hermes3點×128，再全十點確認涵蓋格式；MISS_OVERLAP_CHECK可另核對，但不能取代獨立phase reference。
- 設計：新root native-pipeline-20261029、獨立state/task。C=385E原MT1，O=新binary PIPE off，P=同binary PIPE on。check通過才十點512tokens、至少5輪旋轉配對；OD/PD診斷另列，計時不拿作promotion。所有engine在第一request前明設AboveNormal並記PID/creation/時間，每request再驗。
- 指標：decode tok/s、窗口/輸出長度、combined pool ms、join/LRU、overlap down tiles（確實與未完成GU重疊）、bitwise checked rows與格式coverage；固定slots3153/20GiB/20479MiB、config/pack/MTP identity。
- 停止：check/identity/process/capacity錯誤停並回復MT1；若前三輪P/O全負或mean<-3%停止加碼，5輪平均>=+3%且paired CI不跨0、P/C亦正才正面；否則保留MT1。內部5秒無進度fatal，外部06:50終止自有tests、07:00硬截止並原API復原。
- Identity：hostname DESKTOP-LKMLUPC；當前best385E…30F5。實際isolated pool.cpp4A7AE645…650A、pool.hpp4255FD01…3C1A已remote hash核對；generate基於DIAG27CCC961…4F5F。上一shadow隔離source的F14改動將恢復為2294DIAG原版（僅自己source）；所有修改限isolated，不改live/current-best。
- 01:33里程碑：pipeline獨立build exit0，binary3F98913EDB0B01D5D5DD3282412725141C298BF5CC9E890DD286AA0720C27230；pool.cppAF976BB3…9453、pool.hpp8B993048…6351、generate1F17C2E5…1B24B。舊DIAG C7F4 exe保留且原build路徑恢復，shadow隔離source已移除回2294基礎；current-best/live source不動。已從實際native_experts.txt完整48層提取十種(gu,down) pair，正式CHK要求全部見到獨立reference紀錄，未覆蓋就停。runner PID25144已啟動START，尚未驗收任何check或效能。
- 01:38驗證：新runner PID25144仍live；SMOKE3請求、CHK10請求（各128 tokens上限）全部OK，獨立原分段reference bitwise零mismatch，十種(gu,down) pair coverage missing=[]。SMOKE比較超2.5億float值，down overlap計數非零。Strict容量3153/20.00/20479。進入OD/PD與正式C/O/P五輪；CHECK的tok/s不可視為效能結果。舊best不變。
- 五輪結果（02:28）：正式150requests，C46.95884/O47.21754/P49.37278 pooledtok/s。P/C按輪+4.893% CI+1.572..8.214%；P/O+4.347% CI-1.148..9.843%，按題P/O+4.418% CI+2.589..6.248%。primary按輪P/O未過gate，尚不採用；不是無收益，也不是穩過50。OD/PD單輪combined pool17.522→15.412ms/w，point平均省1.33ms/w。
- 驗收：19meta/config/full engine logs（1.308MB/10998lines）+150正式rows全處理，共183requests，reference>=906,705,920float values全bitwise parity，十pair全覆蓋，所有capacity/priority/其餘args/env相同；audit verified。controller terminal DONE，原MT1 API PID7724 verified回復，best385不變。下一個role-priority結構假設須另登記，不掃原quota，不把正面pointCI替代未過的primary按輪CI。

## 2026-10-29 02:4x｜NATIVE_PIPE_ROLE_PRIORITY（事前登記）
- 最終結果（06:50收尾）：BUILD成功165059E7…A110；SMOKE三題128至少249,999,360 float values逐位元通過；全CHK第一題因host actual CPU1 !=expected0 fatal，runner05:56退出並自動復原原MT1。GD/RD、正式C/G/R皆未執行，無效能判定、不promote。原Windows host使用CPU Sets，新guard瞬時CPU等值假設與實際衝突；須診斷作用範圍/CPU Set語意後修正，不直接刪guard或聲稱角色策略無效。截止前不開新run。完整raw保留，MT1於06:50重新驗正確；report/patch commit2f1e9987、push憑證失敗不重試。
- 05:52執行前時間限制補充：工具review額度阻擋至本輪，build現正執行，舊campaign無重跑。保持五輪十點設計；逐block開始需距06:50至少4分鐘（上一campaign單block約2至3分鐘），原15分鐘gate過於保守改為4分鐘；06:50 watchdog及07:00硬截止不變。若未完成五輪則PARTIAL，不promotion，不縮樣本充作過gate。source pin/rebuild若無充分時間則留候選不部署。
- 類型：結構；家族：同一pipeline內依task型態選擇先後，並非worker/affinity/quota掃描。原9worker/pin/all、down cap3、同quant/kernel/路由/GPU集合保持。
- 假設：generic所有worker先搶ready down，P可能花時間做bandwidth工作、E仍做GU；僅P優先claimGU，E維持down優先，沒有該類ready工作時共享另一類，可能提升combined pool。此根因尚未實測；DIAG-only每worker GU/down tiles和kernel busy_ns及actual CPU ID先核對。thread-sum/whole-engine資料不冒充wall/decode-only。
- 目標／上限：generic combined約15.41ms/w，原17.52ms/w，仍有GU約12ms與down5ms的資源競爭；理想再重疊的剩餘上限不能從單輪diag精確算，最多不超過原down5.16ms，需實測至少再省約0.6ms/w才有機會把generic49.37推到50。維持cap3，只測一個priority策略。
- 實作：STRATA_NATIVE_PIPE_ROLES=1僅支援實際hybrid All且完整physical worker拓樸；native pipeline第一request前/每drain核對actual LP等於原pin，不符/不支持立即fatal，無fallback。既有CPU topology排序P在前、host留P，不新增硬體偵測層。DIAG-only cacheline隔離每worker counters，正式效能臂不收busy time。
- 設計：新root/task/state native-pipeline-roles-20261029。先R SMOKE3點128與全10點128 bitwise原phase reference/十pair覆蓋；GD/RD各十點512量機制；正式C/G/R五輪旋轉10點512。C原best385；G新binary PIPE on/roles off（獨立確認generic vs385正面結果）；R同binary PIPE+roles on。所有engine第一request前AboveNormal且每request再驗、容量3153/20/20479。live sampling不變、replay契約不變。
- 指標：R/G、R/C、G/C按輪df4和按題df9 pairedCI；token/window/SSD量，combined pipeline_ms/join/LRU；P/E task/busy分配，十pair bitwise與pin/capacity/SHA。
- 停止／決策：任何mismatch/pin/identity/process/capacity錯誤停止並恢復MT1；三輪R/G全負或均值<-3%則不再加R加碼。完整五輪R/G>=+3%且CI不跨0、R/C亦>=+3%CI正才採role；否則不採role。若G/C完整獨立確認>=+3%CI正，可作generic候選採用依據（與上一輪P/C正面一起報，不能把它冒充新role收益）。不以首輪最好值或pool micro代替完整結果。最晚06:50停自有測試、07:00復原服務；預留source pin/必要rebuild驗證時間。
- Identity：current-best仍385E…30F5，已remote重新核對；原pipeline source AF976BB3…9453／8B993048…6351／generate1F17C2E5…1B24B；角色改動pool.cpp9E0F3DD3…FF07／pool.hpp48AFA366…2F8C。只改isolated source，main與無關dirty tools不動。

## 2026-10-29 晚｜NATIVE_PIPE_PO_CONFIRM（事前登記；使用者授權「同意」，Codex gpt-6.1-sol low 執行，Claude 規劃核對）
- 類型：結構（家族：native CPU GU/quant/down 資料流）；不是新旋鈕，只是補足 NATIVE_GU_DOWN_PIPELINE primary P/O 的樣本數。
- 假設：交錯本身使 decode 約 +4%（5 輪點估計 P/O +4.35%，按題 CI +2.59..6.25）；primary 按輪 CI 跨 0 是 df=4 檢定力不足。
- 目標段／上限：combined pool 17.52→15.41 ms/w；down 完全重疊理想上限 5.16 ms/w。補 50 需 2.47 ms/w。
- 設計：只跑 O（3F98…7230，STRATA_NATIVE_PIPE off）與 P（同 binary，on），沿用原 harness／Hermes 十點 512／每 block 新引擎／AboveNormal／3153／20.00／20479，不跑 C、不改任何參數。第 6 輪 O→P、第 7 輪 P→O。與原 5 輪合併成 7 輪計算 P/O 按輪配對 CI（df=6）。
- 停止規則（寫死）：7 輪均值 ≥ +3% 且 CI 下限 >0 → 停，primary 通過。否則跑第 8 輪（O→P），以 8 輪（df=7）為最終結果，不論成敗都停，不再加碼。前兩輪 P/O 皆負 → 直接停、判未過。有 sequential look 一次，型一錯誤略升，報告須註明。
- 採用條件：primary 通過且原 5 輪 P/C 已正（+4.89%，CI +1.57..8.21）→ 可擬部署候選（另請授權，且需 source commit/tag＋fresh rebuild 才算 reproducible best）。
- 指標：block 合併 tok/s、按輪配對、輸出長度/windows、引擎容量與 priority、跨日漂移（新 O 與舊 O 平均差）。
- Identity：hostname DESKTOP-LKMLUPC；live current-best 385E…30F5；O/P binary 3F98913E…7230；process gate 照 AGENTS.md；結束恢復原 MT1 API 並驗證。

- 2026-10-29 08:48 完成追加驗證：第6輪 O45.08160606／P45.11552308（+0.075235%），第7輪 P48.14362722／O45.86009488（+4.979345%）；七輪 primary 平均+3.827416%，95% t-CI+0.145269..+7.509562%（df6），依預註冊 PASS，第8輪未跑。Sequential look 未校正，型一錯誤略升；未部署。
- 漂移與驗收：新O平均45.47085047 vs舊47.22684092（-3.718204%）；新P46.62957515 vs舊49.24582655（-5.312636%）。4 blocks／40 rows、完整325359 bytes／2795 lines logs及舊O/P設定與harness/input SHA核對通過；原MT1 API PID13612、385E…30F5／F23F…EB6F、AboveNormal、loaded、3153／20.00／20479、MT1環境復原驗證通過。完整結果 state/po-confirm-20261029/RESULT.md；raw runs/native-pipeline-po-confirm-20261029。無GitHub／remote git操作。

## 2026-10-29 上午｜NATIVE_PIPE_DEPLOY_PREP（事前登記；使用者授權「準備部署 pipeline」，不切換 live）
- 類型：結構（家族：native CPU GU/quant/down 資料流）；部署前 reproducibility 與正確性，不是效能 A/B。
- 目的：把 generic pipeline（3F98…7230 的 source）固定成可重現的 source commit/tag，fresh rebuild，確認 binary identity 與 bitwise 正確性，準備好 live 設定與回滾，但不切換 live。
- 設計：遠端新 worktree/branch（基於 61b3fb5…，套 2f1e998 內 generic pipeline patch，不含 roles patch），本地 commit＋tag，不 push、不動 main 與兩個既有 dirty tools。獨立 build 目錄 fresh build，比對 SHA 與 3F98…7230。新 binary 跑 SMOKE3×128＋CHK10×128（STRATA_NATIVE_PIPE=1＋PIPE_CHECK=1），獨立原分段 reference bitwise、十種 gu/down pair 全覆蓋。
- 判定：SHA 相同且 CHK 零 mismatch → READY（待使用者授權切換）。SHA 不同但 CHK 通過 → READY_REBUILT_SHA_DIFFERS，回報差異來源，速度證據屬 3F98，需使用者決定是否補短 O/P 確認。任何 mismatch／build 失敗／source 對不上 → STOP。
- 不做：正式速度輪、切換 live、push、修改 main。
- Identity：hostname DESKTOP-LKMLUPC；live 385E…30F5／config F23F…EB6F；process gate 照 AGENTS.md；CHK 期間停 API，finally 恢復並驗證。

## 2026-10-29 上午｜SSD_JOIN_BOUND（事前登記；使用者同意「好」，部署準備完成後執行；分析，不是效能 A/B）
- 類型：結構診斷（家族：expert 快取／預取／SSD miss）；不掃 worker/affinity/spin/cache 參數。
- 假設：join 6.09 ms/window（CPU 25%）主要是等 experts.bin 的 SSD 讀取；逐題 join 與 issue_wait 高度同向（p01 13.6/16.7、p04 11.2/13.6、p02 3.7/4.9、p05 3.8/5.1）。若同 20 GiB RAM 下最佳替換策略或下一層預取可大幅減少 miss，join 可降。只是相關，尚未證因果。
- 目標段／上限：join 6.09 ms/w；部署 pipeline 後距 50 約 1.2 ms/w。Belady 最佳快取或預取若省不到 1.2 ms/w 等量的 SSD 等待，此方向停止。
- 設計：先查 Task027（RAM LRU）與既有 artifacts 是否已有 expert 存取 trace 或最佳快取上限，有則沿用不重做。缺 trace 時，只能用 current-best binary 既有的診斷/trace 開關跑一次 Hermes 10 題 trace（停 API、finally 恢復）；若需改 source 才能取得 trace → 停下回報，不改 source。離線模擬：現行策略 vs Belady（同 20 GiB、同 slot 大小）vs 簡單預取（用第 L 層路由預測 L+1，或前一 token 同層集合）命中率，換算 SSD bytes 與 ms/w（用實測 issue_wait/GB 比例，標明是估算）。
- 指標：每 window SSD bytes、miss 數、現行 hit rate 能否重現實測、Belady hit rate、預取 precision/recall 與多讀 bytes、換算 ms/w 上限。
- 停止：模擬無法重現實測 SSD 量（差 >20%）→ 先回報模型不可信；Belady 上限 <1.2 ms/w → 放棄此家族；不寫新快取或預取實作、不做 A/B。
- Identity：hostname DESKTOP-LKMLUPC；current-best 385E…30F5（若已部署 pipeline 須由使用者另行授權，未授權前仍為 385E）；process gate 照 AGENTS.md。

- 2026-10-29 NATIVE_PIPE_DEPLOY_PREP 完成追加：**READY_REBUILT_SHA_DIFFERS**。新 worktree `C:\Users\User\native-pipe-generic-20261029`，branch/tag `native-pipe-generic-20261029`，commit `f520bc5e9d31c93caeb296b059e3a3eaa16e493f`；generic 六檔 SHA 全同、main/兩 dirty tools 未變、未 push。fresh build exit0、SHA `A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8`，不同於3F98，差異不限timestamp且完整來源未定位。SMOKE3×128至少232,883,200、CHK10×128至少747,256,320 float values，零bitwise mismatch、CHK十pair全覆蓋；完整165,414bytes/1,557lines engine logs驗收。原API finally恢復並獨立驗證PID27444、385E…30F5/F23F…EB6F、AboveNormal/loaded/3153/20.00/20479/MT1。候選config+exact diff+rollback已準備未套用；未跑正式速度。報告 `state/deploy-prep-20261029/RESULT.md`；raw `runs/native-pipe-deploy-prep-20261029`。fresh速度未驗證、需使用者另決定短O/P確認。

## NATIVE_PIPE_DEPLOY_PREP｜2026-10-29 結果續記（append-only，對應原事前登記）
- 判定 READY_REBUILT_SHA_DIFFERS；完整結果及上方完成追加紀錄均屬 LUNA-20261012-027 的 NATIVE_PIPE_DEPLOY_PREP，不屬其他預註冊實驗。
- Source commit f520bc5e9d31c93caeb296b059e3a3eaa16e493f；generic 六檔 byte-for-byte 相符。Fresh SHA A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8；SMOKE/CHK 零 mismatch、CHK 十 pair 全覆蓋。
- 原 live 已恢復且最後獨立核對通過；候選設定／exact diff／rollback／RESULT.md 已存遠端及本機，五個交付檔 SHA 兩端相同。未部署、未 push、未修改 main；fresh 速度未驗證。
- 完整報告：state/deploy-prep-20261029/RESULT.md。保留所有原 ledger 內容，僅於末尾追加具名續記。

## 2026-10-29 上午｜FRESH_BUILD_SANITY（事前登記；使用者授權「先做健全檢查」；SSD_JOIN_BOUND 結束後執行）
- 類型：部署前健全檢查，不是效能 A/B；家族同 native pipeline。
- 目的：fresh build A1E6…1AD8（source tag native-pipe-generic-20261029）與測速 binary 3F98…7230 都開 STRATA_NATIVE_PIPE=1，排除明顯退步。
- 設計：1 輪，順序 F(A1E6)→T(3F98)→F(A1E6)，每 block Hermes 十題 512、新引擎、AboveNormal、3153/20.00/20479，其他 env/args 與 P 臂完全相同（無 CHECK/DIAG）。F 取兩 block 合併 tok/s，與 T 比。另比 ms/window、tokens/window、CPU ms/window。
- 判定：F/T ≥ −5% → PASS（無明顯退步，不代表等速）；F/T < −5% → FLAG，回報並不部署。單輪雜訊約 ±5%，只能抓明顯退步。不加輪、不改設計。
- Identity：live 385E…30F5／config F23F…；process gate；finally 恢復並驗證；不切換 live。

- 2026-10-29 SSD_JOIN_BOUND 完成追加（REPORT_LOCAL；分析）：重用 Task027 63,947,136-byte／8623-window trace 與既有 Belady；同 trace 現行 SSD bytes 校驗最大誤差 1.879% <20%。Hermes phase 36,858 SSD experts／2838 windows，issued 68.080484352 GB、join 6.090162／issue_wait 8.016347 ms/w。OPT forced 省 62.978% bytes，按 phase 比率條件式估 5.049 ms/w >1.2，**CONTINUE 僅為舊 trace oracle headroom**；current MT1/Hermes 轉移未驗證，不代表可達速度。兩種 K10 預取 precision/recall／extra bytes 見 `state/ssd-join-bound-20261029/RESULT.md`。live PID27444、385E…30F5／F23F…EB6F／AboveNormal／loaded／3153／20479 核對；API未停，無新capture、source/build/config/git/GitHub 操作。
- 協調者判讀與決定（2026-10-29）：Belady 63% 為不可實現上限；10/18 warm 報告中可實作策略（ARC/LRU-2）僅省 11–16% reads，換算 Hermes 約 0.9 ms/w join（估算）。neuro trace 與 Hermes miss 量差 2.7 倍。使用者決定不再抓 Hermes trace，此家族暫停。

- 2026-10-29 FRESH_BUILD_SANITY 執行前置檢查追加：BLOCKED_CONFIG_DIFF。遠端 F/T SHA 全符合；原 harness 實際生成 config 除 exe 外，cwd 與各 block log 也不同，依 brief 停止規則未啟動 F/T/F。無測速數字，PASS/FLAG 未判定，rows.json=[]。API 未停且 live 385E…30F5／config F23F…EB6F／AboveNormal／loaded／3153／20479／MT1 核對通過；未見 SSD_JOIN_BOUND controller。無 GitHub/push/source/git/config 修改或程序停止。詳細證據：state/fresh-build-sanity-20261029/RESULT.md、preflight.json、三份 preflight config。預登記 −5% 決策規則未改。
- 第一次嘗試（2026-10-29）：BLOCKED_CONFIG_DIFF，未測速、API 未停。原因是 brief 只允許 exe 不同，但 harness 本來就設定 cwd=exe.parent 與每 block 獨立 log。協調者修正 brief：允許 exe／cwd／log 三項差異，其餘不變，判定規則不變，重跑 attempt-2。

- 2026-10-29 FRESH_BUILD_SANITY attempt-2 完成追加（LUNA-20261012-027；REPORT_LOCAL）：沿用原P harness，F→T→F各十題512，三block OK／30題零error；F/T SHA與current-best核對，config僅exe/cwd/log不同。block pooled tok/s 46.67184368／45.37604475／46.64663366；F兩block合併46.65892429，對T +2.827218%，依預登錄−5%規則 **PASS**（未見明顯退步，非等速證明）；未加輪。F/T ms/window 39.890000／43.838688、tokens/window 1.861224／1.989226、window-weighted CPU ms/window 22.496959／25.769775。finally還原且獨立核對live PID26660、385E…30F5／F23F…EB6F／AboveNormal／loaded／3153／20.00／20479／MT1，無PIPE/CHECK/DIAG/MT_MIN啟用。未部署、未改source/main/config/model、未push/GitHub；原始證據與完整coverage見 state/fresh-build-sanity-20261029/RESULT.md 及 attempt-2/，根目錄rows.json已存本次30rows。

## 2026-10-29｜NATIVE_PIPE_DEPLOY_LIVE
- LUNA-20261012-027；使用者授權切換 live；FAILED_ROLLED_BACK。新binary A1E6…1AD8／config 060F2F…93D93，僅exe/cwd/PIPE三項；loaded、AboveNormal、3153/20.00/20479、workers9/all、MT1/PIPE及ACTIVE通過。唯一32-token smoke為reasoning-only／content=null／finish=length，32 tokens、905.1ms、35.4 tok/s；依brief立即回滾，未重試。10:16:30獨立核對原PID32040、385E…30F5／F23F…EB6F與完整容量env恢復。未晉升best、未改歷史CURRENT_BEST、無GitHub/push/source/main/git/model/harness或溫度修改。兩段stop→loaded窗口合計約71.5秒。詳見 state/deploy-live-20261029/RESULT.md。
- 協調者核對（2026-10-29 10:2x）：FAILED_ROLLED_BACK 為 brief 的 smoke 驗收條件錯誤所致。對原 live 385E…30F5 送相同 32-token 請求，同樣 finish=length、content=None、只有 reasoning（thinking 模型 32 token 不足以產生最終回答）。候選 A1E6 啟動、PIPE ACTIVE、容量與 identity 全部通過，沒有 pipeline 缺陷證據。

## 2026-10-29｜NATIVE_PIPE_DEPLOY_LIVE attempt-2
- LUNA-20261012-027；使用者授權切換 live；DEPLOYED。live 現為 binary A1E6…1AD8（engine PID31512）／config 060F2F…93D93，PIPE=1、MT1=1，3153/20.00/20479、workers 9/all、NATIVE_PIPE ACTIVE、無 FATAL。停機約 27 秒（10:29:24→10:29:51）。
- Smoke（max_tokens=512）：HTTP200、47 tokens、finish=stop、content 非空、35.3 tok/s（非 benchmark）。新 best manifest：bench\results\2026-10-29-native-pipe\BEST.json（舊 manifest 未動）。完整報告：state/deploy-live-20261029/attempt-2/RESULT.md。

- 2026-10-29 COPY_LRU_DIAG 完成追加（LUNA-20261012-027 continuation；REPORT_LOCAL）：唯讀診斷判定 UNCLEAR。live PID31512、A1E6…1AD8 與 source f520bc5 核對；expert_source SHA 與原 DIAG patched 檔完全一致。lru_ms 是 decode thread compute 後的 serial ram_lru_complete，包含 stage→arena memcpy；copy_ms 是 scratch→stage 的重疊 thread 工作。舊 Hermes 30 D requests／2838 windows：LRU 1.195714、copy 1.716546 ms/w；十題 LRU 對 SSD MB/w R²=0.998888，但 bytes/miss counts 共線，無法拆 bookkeeping/copy；未證明 current pipeline 可省 1.2 ms/w。報告 state/copy-lru-diag-20261029/RESULT.md 與 analysis.json；無 API、build、benchmark、stop、source/git/config 或 GitHub 操作。

## 2026-10-29｜PE_GUARD_DIAG
- LUNA-20261012-027 continuation；REPORT_LOCAL。ROOT_CAUSE_FOUND：host CPU Sets soft placement 與單一瞬時LP equality guard契約不符；當晚實際遷移原因LIKELY，缺TID/selection歷史紀錄。無CPU Set ID/LP混用證據。
- BelowNormal stdlib/ctypes probe：group0 LP0→ID256、selection readback[256]；soft 3465/10000（34.65%）集合外，hard group affinity 0/10000，各約2秒；soft集合外均P class，不能外推Strata遷移率。raw：remote runs\pe-guard-probe-20261029；本機 state/pe-guard-diag-20261029/。
- 建議保留host soft語意，核對TID／selected IDs／mapped class，host guard改驗實際P class、worker保留硬LP核對；不宣稱全段不遷移。未改碼，後續需新SMOKE+完整CHK及C/G/R五輪。API PID31512／A1E6…1AD8原地存活、health loaded；無build/benchmark/API stop/source/git/config/GitHub操作。完整證據與coverage：state/pe-guard-diag-20261029/RESULT.md。

## 2026-10-29 午｜PCIE_BALANCE_PORT（事前登記；使用者授權「可以叫gpt去做」，Codex 執行）
- 類型：結構（家族：PCIe／pinned 第 3 筆；與已結案的 PARTIAL_PIN 不同處：每層依實測 CPU/GPU 成本動態決定 PCIe 數量，不是固定比例）。不是旋鈕掃描：PIN 量固定 8 GiB（上一輪甜蜜點），不掃 PIN、不掃 balance 參數。
- 依據：上游 Niko1221/Strata commit 04be241a5（STRATA_PCIE_BALANCE=1，port of PR #1548），我們的 base 沒有。PIN8 結案原因是固定比例下 CPU 段 −2.2 ms、GPU-reach +1.4 ms 互相抵銷；balance 正是在每層取兩邊較長者最小。
- 假設：PIN8＋BALANCE 讓 CPU 與 GPU 端時間接近，淨省 ≥1 ms/window。上游自己的反證：DRAM-bound pool 幾乎無收益（9950X3D 16 workers 12.19→12.17 ms）；我們 CPU 有效頻寬約 28 GB/s，可能同樣受限。
- 目標段／上限：CPU 段約 22 ms/w 與 GPU 等待 11.7 ms/w 的不平衡；PIN8 已量到 CPU −2.2 ms 的機制量，上限約 1–2 ms/w。
- 設計：live source（tag native-pipe-generic-20261029）上開新 worktree 移植該 commit，fresh build。先 PIPE_CHECK SMOKE3＋CHK10 bitwise；機制閘門：PIN 註冊 >0、PCIe experts/層 >0、balance 有輸出 fit。臂 C（live A1E6 原設定）、P8（新 binary＋PARTIAL_PIN 8 GiB，無 balance）、B8（新 binary＋PIN8＋BALANCE）。Hermes 十題 512、每 block 新引擎、5 輪旋轉、AboveNormal；容量：C 為 3153／20.00／20479，PIN 臂沿用 PARTIAL_PIN 前例（locked+registered=20480 MiB）。
- 指標：tok/s（按輪配對 CI df4、按題 df9）、ms/window、tokens/window、CPU ms/w、GPU-reach ms/w、PCIe experts/層、CPU experts/層。
- 判定：primary B8/C 按輪 ≥ +3% 且 CI 下限 >0 → 候選（部署另請授權）；B8/P8 用來確認 balance 本身的貢獻。前三輪 B8/C 全負或均值 < −3% → 停止，不加輪。
- Identity：hostname DESKTOP-LKMLUPC；current-best A1E6…1AD8／config 060F…3D93；process gate；結束恢復 live 並驗證。
- 執行追加（2026-10-29 12:17，LUNA-20261012-027 continuation）：**BLOCKED_CONNECTIVITY，未作最終效能判定**。base f520bc5 上獨立 branch pcie-balance-20261029／commit 4639ae8a61c870abde192e13f09c6b0489604977／local tag pcie-balance-port-20261029，10 hunks 衝突手工解決，保留 PIPE/MISS_OVERLAP；fresh build exit0，binary DF13A36431461CA117F105BE4588BBAA618C9357BD7281F812391547CD689EC2。SMOKE3＋CHK10×128 零 mismatch、十組gu/down齊全；PIN8 registered8.00＋locked12288=20480 MiB，PCIe1.68/1.00/1.27，fit ready=1、PIPE ACTIVE，機制門通過。正式第1／2輪完成，遠端round-deltas實讀B8/C −2.2330699%／−1.0850475%；最後成功盤點為第3輪B8已載入。12:06起SSH持續timeout超過10分鐘，筆電實際Wi-Fi為TANetRoaming、Tailscale offline/logged out且controlplane.tailscale.com不通，判筆電端連線層阻擋，不能宣稱桌機離線。live API已依stop_api停止；controller為detached臨時task且有finally restore，但**目前API狀態／restore均未確認**。未取得完整rows/CI/block metrics，不以空rows冒充；原始rows仍在remote runs\pcie-balance-20261029。已保存本機RESULT.md／CHECKPOINT.md／identity／patch／機制與coverage；未改live config／remote main，無push/GitHub writes。恢復連線後先process gate讀campaign/restore/final_verify、勿重跑；補收rows與獨立live驗證後才結案。報告：state/pcie-balance-20261029/RESULT.md。

### 2026-10-29 12:25｜PCIE_BALANCE_PORT 最終結果（協調者補收）
- Codex 因筆電切到 TANet（Tailscale 控制面不通）於 12:17 停止，報告為 BLOCKED_CONNECTIVITY；遠端 detached controller 照常跑完。
- controller 在第 3 輪後依停止規則結束（前三輪 B8/C 全負）：phase=DONE，12 blocks 完成，12:13:41 API RESTORE OK。
- 協調者 12:22 恢復連線後獨立核對 live：PID 26244、binary A1E6…1AD8、config 060F…3D93、AboveNormal、loaded、PIPE=1、MT1=1。
- 由 rows.json（90 rows，已下載至 pcie-balance-20261029/rows.json）重算 pooled tok/s，按輪 t-CI df=2：
  - B8/C −2.23 / −1.09 / −0.99，平均 −1.43%，CI −3.15~+0.28
  - B8/P8 −0.12 / +0.14 / +1.79，平均 +0.60%，CI −1.96~+3.17
  - P8/C −2.12 / −1.22 / −2.72，平均 −2.02%，CI −3.90~−0.14
- 機制：PCIe 每層-window 0.68~0.83 個 expert；GPU-reach wait 比 C 多 +1.0~+1.4 ms/w，CPU ms/w 沒有穩定下降；平衡的 CPU fit 對 n_pcie 係數 0.000。
- 判定：STOPPED（停止規則觸發），不是候選。PCIe/pinned 家族第 3 筆，累積收益都在雜訊內或為負 → 依 checklist 此家族結案，下一筆不准再是同家族。
- 根因：PCIe 路徑每個 expert 約 186~199 µs GPU 成本，對比 CPU 約 60~89 µs/expert；把 expert 從 CPU 移到 PCIe 只是把等待從 CPU 換到 GPU，平衡只能把壞處縮小，無法變成好處。
- 殘留：遠端臨時排程工作 Strata-PCIE-Balance-20261029 尚未移除。

## 2026-10-29 12:50｜SPEC_SPLIT（事前登記）
- 類型：結構（家族：CPU/GPU 重疊；現成開關 `--spec-split`，source 不改；上游註解稱 exact）
- 假設：如果把 T≥2 的 verify window 拆成 A/B 兩組交錯（CPU 算 A 的 expert 時 GPU 跑 B 的 mixer/router），則 window 時間下降，因為 10/27 nsys 顯示 GPU 每次 forward 幾乎不隨 T 變（pre T1/T2/T3 10.1/10.9/12.1 ms）而 CPU post 隨 T 大增（13.9/22.4/42.0）
- 目標段／上限：用 10/27 per-T 資料估 T=2 37.2→約 29 ms、T=3 58.2→約 47 ms，加權約 +15% tok/s（舊 binary，未計第二次 launch 與交錯空檔）；上游自己標「exact, ~7% slower」（他們的機器）
- 已有資料核對：ledger 與 state 報告無任何 --spec-split 測試紀錄
- 指標：pooled tok/s、ms/window、tokens/window、CPU ms/w、GPU-reach ms/w；exact 檢查：S 與 C 同題 greedy 輸出逐 token 相同與否
- 設計：臂 C（live A1E6＋live config）、S（同 binary＋args 加 --spec-split）；先 SMOKE 3＋CHK 10（PIPE_CHECK=1，十組 gu/down 全覆蓋、零 mismatch）；Hermes 10 題×512、每 block 新引擎、5 輪輪替、AboveNormal、容量 3153/20.00/20479
- 判定：S/C 按輪平均 ≥+3% 且 CI 下限 >0 → 候選（部署另需使用者同意）；前三輪 S/C 全負或平均 < −3% → 停止
- Identity gate：C binary A1E6…1AD8、config 060F…3D93；process gate 每步


### 2026-10-29｜SPEC_SPLIT 執行結果追加（LUNA-20261012-027 continuation；REPORT_LOCAL）
- 完成 SMOKE3＋CHK10×128：零 bitwise mismatch、十組 gu/down 全覆蓋、PIPE ACTIVE、無 fatal；5 輪 C/S 十題×512，全 100 正式 rows，各 block fresh engine、AboveNormal、3153/20.00/20479 嚴格通過。
- 同 live A1E6…1AD8／060F…3D93，正式設定僅 --spec-split／block log／harness cwd 差異；未改 source、build、live config、溫度，無 commit/push/GitHub writes。舊 PCIe task 經 Ready＋DONE 核對後已刪。
- S/C 逐輪 +0.3333／−0.6220／−2.7692／−3.0596／−0.5649%；前三輪平均 −1.0193%，未觸發停止規則，完成原定五輪。primary 平均 -1.3365%，95% CI [-3.1902, +0.5173]%，df=4；secondary 十題跨輪 pool 後平均 −4.1832%，CI [−9.9204,+1.5540]%，df=9。判定 NOT_CANDIDATE，未達 ≥+3% 且 CI 下限>0。
- 機制觀測：GPU-reach wait C 11.7888→S 8.9628 ms/w；CPU 22.6725→24.7199 ms/w；tokens/window 1.9262→1.8659。runtime flag＋source G=2 條件＋多token timing支持 split 啟用；沒有專用group counter／graph count，G=2仍屬control-flow推論，不能把內容不同的 timing 差值全歸因於機制。
- Exactness：reasoning＋content identical 0/50；reasoning 0/50、content 37/50（含空）。首差位置以同 server tokenizer 分欄位重編碼，非未保存的原始 engine/control token IDs；完整表與限制在 RESULT.md／raw/exactness.json。依brief沒有因差異停測。
- detached controller DONE，12 blocks，wrapper exit0；13:27:20 API RESTORE OK，獨立核對 PID1052／A1E6／060F／AboveNormal／loaded／3153/20.00/20479／PIPE1／MT1／無 --spec-split。新臨時 task Ready保留，無controller殘留。
- 本機 RESULT.md：state/spec-split-20261029/RESULT.md；rows.json已下載，raw manifest 384檔size/SHA通過，qa.json與analysis.json保存。遠端權威 raw：C:\Users\User\Strata-Adrian-control\runs\spec-split-20261029。source僅讀相關控制與log路徑，未全面audit；model/pack未重hash；無原始token IDs/group counter，詳coverage。
- 協調者核對（13:4x，由 rows.json 重算，與 Codex 一致）：tok/s S/C −1.34%（CI −3.19~+0.52，df=4）。拆成兩個因子：ms/window −1.66%（CI −3.23~−0.09，五輪四輪為負）＝split 確實縮短 window；tokens/window −2.98%（CI −4.62~−1.34，五輪全負）＝每個 window 接受的 token 變少，吃掉收益且更多。機制：GPU-reach wait −2.83 ms/w，但 CPU +2.05 ms/w（CPU experts/層-window 6.04→6.53，約 1.08×，加上 nt=1 每 expert 效率較差），淨省約 0.65 ms/w，遠小於用 10/27 nsys 估的 −8~−11 ms（估算高估了重疊、低估了 CPU 增量）。
- 判讀：輸出 0/50 完全相同，與源碼「exact」註解不符，且 p01 每輪都在同一位置分歧（確定性差異，不是雜訊）；推測與我們的 tail-skip／native pipeline 在分組後的行為有關，未驗證。即使 tokens/window 不掉，ms/window −1.66% 也低於 +3% 門檻 → 不值得追 exactness 根因。CPU/GPU 重疊家族第 1 筆，結案此開關；整體重疊方向不因此結案（瓶頸是 CPU 端多出的工作，不是重疊本身）。

## 2026-10-29 14:1x｜GPU_EXACT_BUNDLE（事前登記）
- 類型：旋鈕（家族：GPU kernel 開關；現成 env，source 不改；家族第 1 筆）
- 已有資料核對：switch-inventory-20261029.md（Sonnet 盤點）＋ledger grep：下列開關無任何測試紀錄；在 CUDA 預設關，只在 AMD gfx1151 預設表開（arch_defaults.cpp:34-57）
- 臂：C（live）、G（C＋STRATA_DF_QB_Q4=1、STRATA_DF_BRANCH=1、STRATA_GDN_SPLIT=1、STRATA_LFUSE=1、STRATA_QFUSE=1、STRATA_TSUM=1、STRATA_MMVF_ROWS=1、STRATA_ATTN_LANECELL=1）
- 假設：這組精確的 GPU kernel 開關縮短 GPU pre 段（約 10～12 ms/w），使 GPU-reach wait 下降；DF_QB_Q4 直接命中我們的 --kv q4_0 逐 token 路徑（verify.cpp `qb=…&&(!st.kv_q4||qb_q4)`）
- 上限：GPU pre 快 10～20% → 省 1～2.4 ms/w → 約 +3～6%
- 指標：tok/s、ms/w、tokens/w、GPU-reach ms/w、CPU ms/w；精確性：G 與 C 同題 greedy 輸出逐字相同與否（全部聲稱 bitwise）
- 設計：SMOKE 3 題 G（無 fatal、PIPE ACTIVE、與 C 輸出比對）→ Hermes 10 題×512，3 輪交錯；若平均落在 0～+5% 或 CI 跨 0 → 加到 5 輪（此加輪規則事前登記）
- 判定：按輪平均 ≥+3% 且 CI 下限 >0 → 候選，之後逐一拿掉做消去；前三輪全負或平均 < −3% → 結案；輸出不同 → 記錄，候選前需二分找出不精確的開關
- 結果（2026-10-29 14:1x，detached controller 跑完 SMOKE＋3 輪，14:13:18 還原 live；本機 RESULT：state/gpu-bundle-20261029/RESULT.md）：
  - 八個開關 source 皆有 getenv、皆以 env=1 啟用，engine 實收（meta.effective_env）；engine log 無任何啟用標記、無逐 kernel 計數器。SMOKE OK。
  - tok/s G/C 逐輪 +5.36／+10.31／+11.12%，平均 +8.93%，95% CI [+1.18, +16.67]（df=2）→ 形式上達候選門檻，3 輪即止（不延長）。ms/window −28.8%（CI −42.6~−15.0）、tokens/window −22.3%（CI −42.6~−2.0）。
  - 機制：GPU-reach 持平（C 11.81 vs G 11.81 ms/w）→ 「縮短 GPU pre 段」假設不成立；增益來自 CPU ms/w 22.90→12.04、CPU experts/層-window 6.14→3.22，伴隨 tokens/window 下降。G 總產出 8507 vs C 5807 tokens（同題），內容不同使 tok/s 混淆。
  - 精確性：同題同輪完全相同 0/30，reasoning 於第 0～7 token 就分歧 → 依規則候選前需二分開關；暫不部署、不當 best。逐題 secondary 平均 +11.83%（CI −1.79~+25.46，df=9），p04、p08 為負。
  - live 獨立核對通過（單一 strata.exe PID 19064、A1E6、060F、AboveNormal、loaded、3153/20479、PIPE=1／MT1=1、八 env 皆無）；注意 live API 綁 <tailscale-host>:8080，不是 127.0.0.1。
- 協調者核對（14:3x）：**G 的輸出是壞的，+8.93% 無效。** 抽看 raw 回應：G-r1 p03 reasoning 以 ' action" action" action"…' 無限重複到 512 上限；p06 'the tool the tool the tool…'；p01 句子破碎（'[course material testing ]" …'）。C 同題正常。首差在 reasoning 第 0～7 個 token，表示主模型數值從第一步就錯。tokens/window −22%、CPU experts/層-window 6.14→3.22 是 MTP draft 幾乎全被拒（T 變小）的結果，不是加速；tok/s 上升只是較短 window × 垃圾輸出。
- 機制：GPU-reach wait C 11.81 vs G 11.81 ms/w，完全沒變 → 這組 GPU kernel 開關在 4070 上沒有縮短 GPU 段（假設不成立）。
- 判定：BROKEN／結案。不做二分：即使找出精確子集，GPU 段無改善的跡象，預期收益 ≈0。推測破壞來源（未驗證）：DF_QB_Q4（Q4_0 KV 批次 rotation）或 AMD 調校的 GDN_SPLIT／TSUM 在 sm_89 的路徑。GPU kernel 開關家族第 1 筆，結案。

## 2026-10-29 14:4x｜GPU_SWITCH_EXACT_SCREEN（事前登記，篩選，不測速度）
- 目的：GPU_EXACT_BUNDLE 8 開關一起開會讓輸出壞掉；逐一單開，找出哪些開關在 4070 上輸出與 C 相同（精確），供之後只用精確子集做 A/B。
- 協調者更正：bundle 的「GPU-reach 沒變」因 G 的 T 變小（draft 被拒）而不是公平比較，不能據此結案整組。
- 設計：同 live binary／config；臂 C、C2（A/A 對照）、以及 8 個單開臂（DF_QB_Q4、DF_BRANCH、GDN_SPLIT、LFUSE、QFUSE、TSUM、MMVF_ROWS、ATTN_LANECELL 各自 =1）；每臂新引擎，Hermes p01/p05/p08 ×128，順序 C、8 臂、C2。
- 判定：C 與 C2 相同 → 單開臂與 C 逐字相同＝精確、不同＝不精確；C 與 C2 本身就不同（suffix 決策用 wall-clock）→ 改用首差位置（與 A/A 首差比較）＋文字是否出現重複迴圈／破碎判讀，並標明限制。不看 tok/s。
- 結果（2026-10-29 14:26～14:39，detached controller 10 blocks 全 OK，14:39:30 還原 live；本機 RESULT：state/gpu-screen-20261029/RESULT.md）：
  - C 與 C2 本身不同：p05 @246、p08 @51（字元索引），p01 相同 → 改用首差位置判定（分歧不早於基準＝A/A 噪音內）。
  - EXACT（噪音內）：LFUSE（三題與 C 逐字相同）、DF_QB_Q4、DF_BRANCH、MMVF_ROWS、ATTN_LANECELL。UNCLEAR：GDN_SPLIT、TSUM（p05 對 C 與 C2 皆 @136，早於基準，兩者 p05 輸出一致，文字連貫無迴圈）。BROKEN：QFUSE（前 7～15 字元分歧、p01 破碎重複）。
  - 限制：3 題×128 token、n=1；engine log 無開關標記，只證明 env 送達；EXACT 非 bitwise 證明。
  - 粗略速度（單次、非 A/B；僅輸出與 C 相同的題才 like-for-like，整臂三題全同的只有 LFUSE；C vs C2 的 ms/w 就差 7.9%、windows 184 vs 170）：tok/s vs C：QB_Q4 +3.7%、BRANCH +5.0%、GDN +3.4%、LFUSE +3.9%、QFUSE -9.9%（輸出不同，不可比）、TSUM -8.1%、MMVF -2.9%、LANECELL -8.2%；GPU-reach 各臂 11.08～11.86 ms/w，與 C 11.55／C2 11.73 相比在噪音內。完整表見 RESULT.md 第四節。不作速度結論。
  - live 獨立核對通過（PID 18544、A1E6、060F、AboveNormal、loaded、3153/20479、PIPE=1／MT1=1、八 env 皆無）；新排程 Strata-GPU-Screen-20261029 保留 Ready；舊 Strata-GPU-Bundle-20261029 已刪。

## 2026-10-29 15:1x｜NEW_DIRECTIONS_DIAG（事前登記，3 個新方向的診斷，不測速度）
- 已有資料核對：ledger／state 報告無以下任何一項；SSD_JOIN_BOUND 只測過弱預測（上一 window：precision 37%／recall 25%），trace 無 hidden state；10/18 VRAM 盤點只看外部程式／reserve／spec，未看權重。
- B VRAM_WEIGHT_INVENTORY（唯讀，不停 API）：MTP draft experts 675 MiB、native projections 1781 MiB、canonical 1466 MiB 各自的型別／大小／是否重複；判定：找出可換成 expert slot 的 MiB（MTP 降量化＝輸出不變；dense 降精度＝輸出小變）。
- A ROUTE_PREDICT_DIAG（DIAG build，結構，輸出不變）：dump 每層 router 輸入向量與實際路由，離線用 W_router[L+1]·x_L 預測下一層 top-10；指標：對 SSD miss 的 byte recall／precision、extra MB/w；上限 join 6.09 ms/w（pre-pipeline）。判定：SSD miss byte recall ≥60% 且 extra ≤ rescued 的 2 倍 → 值得實作預取；<40% → 放棄。
- C DOWN_SPARSITY_DIAG（同一 DIAG build）：CPU expert 的中間值 h=silu(g)·u，記錄 |h| 低於門檻（相對該 expert 呼叫 max 的 1%、5%、10%）的比例與這些 h 的 L2 能量占比；判定：≥50% 神經元且能量 <5% → 值得評估 neuron-major 重排；否則放棄。

- 2026-10-29 B VRAM_WEIGHT_INVENTORY 完成（唯讀）：完整表在 state\vram-inventory-20261029\RESULT.md。結論：canonical 1466 MiB 全是 GPU 上的 BF16/F32（HC down/up 1200 MiB 最大）；native 1781 MiB 是 GGUF 原生量化（Q6_K 824、IQ4_XS 374、Q4_K 283…），主模型無重複；唯一重複是 MTP draft head 178.4 MiB（主 head Q5_K 子集複製）。MTP experts 已是 2.25 bit，--mtp-q4 不省 VRAM（多用約 37 MiB）；STRATA_HC_Q8 對此 GGUF 是空操作。零改動候選：STRATA_MTP_FULL_HEAD=1 省 178.4 MiB（約 +107 slot，輸出不變，draft 變慢未測）。最大池子：HC BF16→Q8_0 約 563 MiB（需改程式，輸出 rounding 級變化）。未歸屬約 930 MiB 仍未逐項量。

- 2026-10-29 A ROUTE_PREDICT_DIAG＋C DOWN_SPARSITY_DIAG 完成（一個 DIAG build、一次 run；完整表在 state\diag-route-sparsity-20261029\RESULT.md）。DIAG binary B2CC444D…9771D（f520bc5e + diag.patch B54104CD…3646A，env 之後才啟動）；Hermes p01..p10×512（1720 token、946 verify windows），live 已獨立驗證恢復（A1E6…91AD8／config 060F…93D93／AboveNormal／3153／20479／PIPE=1／MT1=1／無 DIAG env）。
  - A：x_L 重算本層 router 與實際 routed ids 一致 99.4%（dump 正確）。W_router[L+1]·x_L top-10：union precision 68.8%／recall 68.8%；SSD miss byte recall 66.3%（≥60%），但 extra 71.9 MB/w 是 rescued 14.9 MB/w 的 4.83 倍（上限 2 倍）；top-4..16、lag-2、機率門檻、最佳 M 個全掃過，沒有任何變體同時 ≥60% 且 ≤2 倍（≤2 倍時最大 recall 約 30%）。lead time（x_L 可用→L+1 dispatch）中位數 0.58 ms，有 SSD miss 的層 1.00 ms，約一半連自己的讀取時間都不夠。判定：未達「值得實作」，也不在 <40% 的「放棄」區（ledger 條文沒覆蓋這個組合）；判讀偏放棄，上限收益 4.97 ms/w 且未計 extra 成本。
  - C：CPU 端 383,024 個（expert,token）call；低於 5% of max|h| 的元素占 51.9%、能量 3.3%（逐 call 平均 2.6%）；1% 檔 18.2%／0.1%，10% 檔 72.1%／11.5%。依 ledger 規則（≥50% 且能量 <5%）只在 5% 檔剛好成立 → 值得「評估」neuron-major 重排；保留：動態稀疏（逐 call 同時達標僅 37%）、5% 檔 h 的相對 L2 誤差約 18%（輸出會變）、只省 down（最多約 17% expert 位元組）、未量區塊層級與逐神經元固定性。

## 2026-10-29 16:xx｜VRAM_MARGINAL_SIM（離線分析，不跑遠端、不是 A/B）
- 類型：離線模擬（家族：VRAM placement；不改 live）
- 目的：回答「多出 X MiB VRAM 值多少」與「依 rank<7／CPU 成本／bytes 排 VRAM 有沒有用」，給 HC Q8、MTP_FULL_HEAD、MTP experts 移 RAM 等提案同一把尺。
- 資料：Hermes routing dump state\ram-policy-sim-20261018\capture-01\routing-dump.bin（8623 windows；dump 的權重欄全是 0，rank 用儲存順序，與 10/13 trace 前三名順序一致，屬推論）；layer 型別與 blob bytes 取 vram-inventory-20261029\raw\native_experts.txt；CPU 成本＝IQ_ALLTYPES 微基準 live 臂 GU µs＋down bytes/4.9 GB/s；套 tail-skip（非 VRAM 且只在 rank≥7 出現的不算 CPU）。靜態 top-N（in-sample 與前半訓練→後半測試），預算 5245 MiB。程式與輸出：state\vram-marginal-sim-20261029\。
- 結果（held-out／in-sample 的 CPU expert 工作量變化）：
  - 排序法：freq(rank<7) −2.7%／−1.8%；freq(rank<7)×cost/bytes −3.6%／−2.6%；被跳過的 tail route 比例 +1.9～2.9 pp（會改輸出）。→ 約 +1% 等級，不值得單獨做。
  - 多出 VRAM：+178 MiB −2.2%／−2.6%；+563 MiB −6.6%／−8.2%；+675 MiB −8.0%／−9.6%；+1238 MiB −13.9%／−16.9%。約每 100 MiB 少 1.0～1.2% CPU expert 工作。
- 限制：靜態 oracle 不重現 live 的 adaptive swap（live Hermes VRAM hit 63.8% 高於靜態 52～58%）；CPU 成本模型是單核微基準換算，不是實測 ms/w；未含 SSD/RAM tier 交互。只能當相對尺，不是速度預測。
- 第一次跑時把權重 0 當排序依據，得到 rank<7 排序 −14～16% 的假結果；已更正，以上為更正後數字。

## 2026-10-29｜LOSSLESS_RAM_SCREEN＋GPU_PACKED_FEASIBILITY（事前登記）
- LUNA-20261012-027 continuation；使用者「好去做」。範圍：遠端小型無損壓縮screen、GPU packed source唯讀可行性；不停止API、不推論、不部署、不安裝、不改temperature。
- 假設：expert量化bytes若可明顯壓縮且解碼足夠快，可在20GiB內增加有效容量；GPU packed若可替換原副本，才有同VRAM的優化空間。
- 目標段／上限：舊pre-pipeline join6.09ms/w、GPU dense6.24ms/w均為過期上限線索；不預測tok/s。
- 設計：48層各expert0/257，共96blob；XPRESS-Huffman、zlib1、LZMA1預選獨立三臂，每blob壓一次／解七次、codec輪替、byte/SHA parity；單執行緒BelowNormal、240秒上限，逐層process/identity/API-idle gate。
- 判定：ratio<=0.90且decode>=3.0GB/s與零mismatch才通過初篩；否則關閉該codec，沒有加碼或替代。通過也不代表整機收益；無完整cache實作。
- Identity：live A1E612…91AD8/config060F2F…93D93、BEST吻合、sourcef520bc5；API idle／3153slots／20479MiB；實際CPU來源42912972800-byte experts.bin，不用GGUF當CPU來源。
- 計畫／coverage：state/lossless-screen-20261029/PLAN.md；GPU僅讀source判original/packed consumers與bytes，不build。
- 完成追加：COMPLETED／NO_GO_FOR_TESTED_CODECS。96blob/48層/10pair、167628800bytes；XPRESS-Huff省1.559%/0.240GB/s、zlib1省1.537%/0.316GB/s、LZMA1省1.162%/0.046GB/s；288rows×7=2016次還原byte比較全過，128.59秒、peak49.59MiB。三臂皆未過ratio<=0.90/decode>=3GB/s，不實作cache；未測zstd/LZ4，不宣告所有無損codec無效。
- GPU實際source核對：333 C/C++/CUDA檔6459821bytes精確Q6 pack callsite搜尋，只在Q6 heads啟用；當前output/MTP head是Q5_K，主模型Q8_0矩陣0個，因此現成Q6/Q8_PACKED不適用。71個Q6 dense中52個shape合格約803.91MiB，但prefill仍讀原native_data，不能直接刪原副本；無build／測速，DEFER新layout工程。完整coverage／限制：state/lossless-screen-20261029/RESULT.md。
- Final verify：原PID27744、A1E6/060F、AboveNormal、loaded、3153/20479、全部live env與BEST相符；無測試程序殘留。Git收尾shell被automatic approval review在啟動前拒絕（需明確同意此report payload至GitHub main）；未commit、未push、未重試或改發布管道，已詢問。這不影響screen結論；git-receipt.json保存拒絕層級。

## 2026-10-29｜RAM_QUOTA_OFFLINE＋LFUSE_AB（事前登記）
- LUNA-20261012-027 continuation；使用者「好去測看看」。先本機離線RAM跨層配額，再單開LFUSE同日A/B；不部署、不改temperature/source或其他GPU flags。
- RAM結構：完整舊8623-window trace，固定GPU/tail-skip與engine LRU語意，48層quota有限grid16slots＋baseline/max；request0-4選quota、5-10 held-out，byte budget<=21474406400，先驗baseline精確重現。held-out SSDbytes至少減25%才值得後續成本分析；舊單prompt不能冒充Hermes加速。另報finite-grid in-sample oracle；600s期限。
- LFUSE旋鈕家族第3筆（bundle→screen→本次正式單開）：同A1E6/060F，F只加STRATA_LFUSE=1；C/F/C三題128smoke後8輪C/F輪替×10題512，共160formal，df7主CI、df9次CI；每block fresh、3153/20.00/20479、AboveNormal。primary>=3%且CI下限>0與其他gates通過才候選；前三輪全負或平均<-3%早停，不加輪，不自動部署。
- 指標：pooled accepted tok/s、GPU/CPU/ms-window/tokens-window、env/config/輸出長度與壞輸出。算子exactness先做source契約核對；text smoke不冒充bitwise證明。
- Identity/process：本輪重新核對livePID27744與remote BEST，API idle、只有已分類API/watch程序。正式停止／每block／restore再gate，停機只限已核對API堆疊，finally恢復並獨立驗證。
- 完整設計／coverage：state/lfuse-ramalloc-20261029/PLAN.md；GitHub舊payload審核仍未同意，不重試該次發布。
- 開跑前sampling修正：實讀捕獲十題temp1.0/top_p0.95/top_k20/min_p0/seed1001..1010；舊harness會強制temp0，這輪在controller只替換request construction，保留原sampling與seed，只改已授權max_tokens。兩臂相同，無新測試前先固定；不把舊greedy screen速度當對照。metadata首次PowerShell預設編碼讀UTF8失敗，已明確UTF8讀同一來源，未停API、未替換資料。
- RAM完成：64.09秒，完整8623windows／48層有限capacity curves；vectorized engine-LRU重現全部11請求reads/adapt counts完全一致。request0-4選quota→5-10 held-out SSDbytes−14.1055%，全trace−17.8476%；全資料事後選quota−18.6909%（保守MiB離散DP，不是全allocation上界）。皆未達25%門檻，NO_GO_BOUNDED_SCREEN，不改live。完整coverage與限制RAM_RESULT.md／ram-quota-results.json；非Hermes/current-best速度。
- LFUSE attempt1工程中止：C smoke3題完成，guard的泛用MISMATCH誤匹配MISS_OVERLAP check_mismatch_rows=0；未跑F、無formal資料。API恢復 verified。attempt2只收窄為NATIVE_PIPE_CHECK MISMATCH與非零check_mismatch_rows並保留fatal/CUDA檢查；相同設計，新目錄lfuse-ab-20261029-attempt2，原目錄不重跑。
- 2026-10-29 LFUSE：使用者要求提前停止；6完整配對/120formal＋9smoke，mean paired−1.2553%，5/6輪負收益；pooled C47.316/F46.698tok/s。第7輪C僅6responses，stop.py檢查遠祖PID失敗、未terminate；其存在觸發既有process gate，原finally清理恢復。原始FAILED/PROCESS_GATE保留，另記STOPPED_BY_USER_NO_PROMOTION，不算8輪CI。19:30:12 API恢復，獨立驗證PID1356/A1E6/060F/AboveNormal/3153/20479/原env且無測試程序。RAM heldout−14.1055%未過25%gate。RESULT.md與RESULT.json保存完整coverage；不部署、不重跑、不發布GitHub。
`n## 2026-10-29｜IO_ARRIVAL_BOUND（事前登記）`n- 結構診斷：SSD batch→逐expert ready→既有GU/down的樂觀重疊上界；使用者「去做」。current-best A1E6/060F/f520先驗證，新隔離DIAG build；smoke3×128＋Hermes10×512一次capture，原temp1/top_p/top_k/seed不動，finally恢復API。`n- 逐I/O request與expert-destination完成區間、ready/cold compute、decode windows；unchanged-work樂觀bound min(cold duration,cold-start−earliest-ready)，用實際window/11作+10%門檻；未過則結束，通過只代表headroom，不實作／部署／加輪。具體誤差、coverage與停止條件見 state/io-arrival-20261029/PLAN.md。

### IO_ARRIVAL_BOUND 完成追加（2026-10-29）
- LUNA-20261012-027 continuation；COMPLETED / NO_GO_UNCHANGED_WORK_STREAMING_BOUND / REPORT_LOCAL。隔離diag binary2EE75897…BF821C（base f520bc5，僅expert_source.cpp/generate.cpp/cpu_phase_diag.hpp）；SMOKE3×128至少246407680 floats零mismatch、9個format pair；一次Hermes10×512 capture，原temp1/top_p.95/top_k20/min_p0/seeds不動。
- 完整1114windows／53472層-window，7691I/O batches／11430OS requests；逐expert完成區間的樂觀重疊上限0.620503ms/w，條件式+1.7026%，遠低於本輪+10%所需3.369594ms/w。71.33% miss dispatch只有一個expert；全部miss後計算僅0.639156ms/w，即使全免費加外部I/O全部免費也僅0.641054ms/w（+1.76%）。不實作新streaming、不部署、不加輪。
- Coverage：所有trace行與decode counter相符，全部dispatch覆蓋。2筆I/O位於dispatch之外、caller未確認；不丟棄，整段2.1151ms全部加到樂觀上限。此為原計算／原讀取工作量的模型上限，非所有kernel/IO/layout方向的全域上界；診斷tok/s48.098不作A/B。raw7.13MB CSV全解析、hash保存。事件為觀察區間，非device timestamp，最大寬7.2619ms；兩種邊界皆未達門檻。
- API20:15:12恢復，獨立核對PID27640/A1E6/060F/AboveNormal/loaded/3153/20479/原env，無diag/build殘留。原始資料、source patch/build與限制在state/io-arrival-20261029/RESULT.md及remote runs/io-arrival-20261029。先前GitHub report payload審核仍未解，不重試發布。

## 2026-10-29｜CPU_R4_SCREEN（事前登記）
- LUNA-20261012-027 continuation，使用者「去做」；結構：同位元組四列交錯 IQ GU kernel。只隔離 CPU 微基準，API 不停，不部署／不整合／不改溫度。
- 假設：保留所有量化碼與權重值，跨四列共用解碼與 activation，可減少 GU 時間；目前 pipeline14.6818ms/w，完整觀測 dispatch 固定 I/O 樂觀模型需全 CPU compute 約1.4倍才有整體10%可能，GU收益需扣 unchanged down／轉換成本。
- 設計：5種實際native GU格式×P/E兩核，每格36expert跨6層；nt1/2/3，GU-only與GU+quant+down，每cell九次AB/BA交錯；10新程序、單執行緒BelowNormal、總測試600秒上限，非整機速度測試。先全部byte roundtrip與decoded values完全相等；數值誤差另報，不冒充品質通過。
- 指標：GU與combined us/expert、repack/inverse成本、bytes、decoded/float mismatch；缺實際core/nt權重時不造整機加權收益。無支持整體10%的證據即不加碼；任一機械parity/finite失敗立即停止，工程錯誤保留log後修同流程。
- Identity：current-best A1E612…91AD8、config060F…93D93、sourcef520bc5；連結現行部署strata_kernels_cpu.lib與ggml libs，啟動前與每程序重新process/API-idle gate。模型原native experts.bin 42912972800bytes；參考ik_llama.cpp d4c1f75533ec897f54944f2734ea0d0e89e4fe01，保留MIT LICENSE。
- Checklist七題逐項答案：state/CPU_R4_NEXT_20261029.md；避免重做SSD arrival／MT1／flags。Status RUN_REGISTERED，尚未測得收益。既有GitHub payload審核限制維持，不重試發布。
- CPU_R4工程修正追加：初次全矩陣GU有效；combined誤用Q2_0 ggml scalar而非live pool act_quant_any/q2_rows_any，combined全數作廢，不作收益推論。保留原始run於wrong-down-attempt；修正同pipeline後只重測combined，樣本不變、不掃參數、不重測GU。兩次numeric工程失敗Q8_K ABI誤接已保留，修正後byte/decoded皆過。

## 2026-10-29 CPU_R4_SCREEN completion (LUNA-20261012-027 continuation)
- User authorization「去做」; COMPLETED / NO_GO_BOUNDED_SCREEN / REPORT_LOCAL. Report state/cpu-r4-20261029/RESULT.md; corrected candidate EBC611F7…9036CA, current-best A1E6/config060F unchanged.
- Corrected 30 combined cells/270 AB pairs, 5 GU types×P/E×nt1/2/3,180 unique experts/30 selected layers. Best+26.13%,worst−26.49%;13positive/17negative. IQ3_S P−23..−26%; multi-token mixed/slower. Not engine tok/s. Every measured combined median<1.3×; conditional all-compute1.3× fixed-I/O model only+8.06% before conversion, insufficient evidence for requested+10%; no integration/promotion.
- Exact396288000-byte roundtrip /1179648000 decoded values across both cores. Float outputs differ: max h9.54e-7, downstream4.27e-4; semantic quality NOT_ESTABLISHED. Packing209.7..1343.4µs/expert and inverse187.6..2067µs, excluded from speed table, no second runtime copy.
- Engineering failures preserved: MSVC build, Q8_K296-vs292 adapter (fixed), initial combined Q2 scalar path (invalid/excluded; corrected to actual pool act_quant_any/q2_rows_any, only combined rerun). All coverage/limits/paths in RESULT; not an all-kernels/layout impossibility claim.
- Independent verify API originalPID27640/A1E6/060F/AboveNormal/loaded/3153/20479/env, idle/queued0/requests0; no bench/build leftovers. No API stop/source integration/temp change. Prior GitHub payload automatic-review restriction remains; no commit/push/publication retry.

## 2026-10-30｜R4_PLUS10_V2（事前登記）
- 授權：使用者要求完整+10%計畫並測所有相關未測方向；027 direct continuation，GH main/branch heads fresh unchanged，無新claim。當前實體BEST A1E6/060F/f520 clean核對，API由原排程啟動PID7888（初始無Strata/python程序）。
- 類型：結構CPU資料流/kernel；假設在同R4 layout補VNNI及P-core gather可去除移植缺口，明確variants：A=live native、V1=VNNI、V2=VNNI+gather、V3=multi-token分組（P用V2/E用V1，nt2拆1+1，nt3拆2+1）；不做失敗時fallback、不改temperature/weights/routing。
- 目標段／上限：10/29 pipeline14.6818ms/w，固定I/O全compute1.4×模型約+10.16%，需省3.37ms/w；不把舊max1.261或1.3當新版上限。品質機械初篩不等於語意不降。
- 設計：沿用5 GU types×P/E×nt1/2/3，36expert/6層/type，180unique；每格5次輪替臂次序、GU-only及actualGU+quant+down。nt1不測重複V3。先byte roundtrip/decoded value equality與V1/V2對舊R4 bitwise check；V3另報數值。10程序單核BelowNormal、600s上限，process/identity/API-idle gate逐格。
- 指標／停止：各臂us/expert、bitwise/numeric、pack/inverse成本、asm spills。任一mechanical parity錯誤立刻停；先修具體工程錯誤，不加參數替代。輸出無支持+10%的headroom則不盲目engine整合；其餘有限候選逐項機制gate/短篩，見R4_PLUS10_PLAN_20261030.md。
- 接續範圍：fast conversion獨立byte驗證、actualrowpartition及nt/spill diagnosis；既有CPU down保持currentdispatch，不拿scalar Q2當live。未執行完整engine測速，不部署。GitHub舊payload自動審核限制仍在，不重試發布。

### R4_FULLBLOB_COST事前追加（2026-10-30）
- V2初篩完成正確性，舊候選GUIQ3S gather改善，但候選down仍讀另一個originalblob。為隔離packed-GU與down分離的working-set成本，本輪改成candidate同bytes完整blob（packedGU+unchangedDown連續），兩臂各自完整單份blob；microbench並存兩臂僅供A/B，不稱production已整合。
- 明確新run cpu-r4-cost-20261030，原v2證據不覆寫；只重測combined，3次輪替pass、不重測GU。增加fast_pack/unpack五type直接SIMD轉換候選：先oldpack==fastpack與還原原bytes全sample，後5次cost；原轉換9次沿用作對照。不fallback，不改權重，identity/process/APIidle gates同v2。

## 2026-10-30｜UNTESTED_SINGLE_FLAGS_SCREEN（事前登記）
- User同輪測未試項目授權；027 continuation。固定10 fresh blocks：C、EXPERT_V2、DF_PLE、FUSE_HEAD_GR、GR_DOWN_MAX4、DF_QB_Q4、DF_BRANCH、MMVF_ROWS、ATTN_LANECELL、C2；每臂Hermes p01/p05/p08×128，原temp1/top_p.95/top_k20/minp0/seeds保留，僅改max_tokens。
- 目的：數值/輸出與初步機制screen，非正式speed A/B。全A1E6/060F、3153/20479、AboveNormal，onlyoneflag，逐request確認真正ownedengineenv；8新方向不bundle，GDN/TSUM/QFUSE/LFUSE不重跑。EXPERT_V2符合GU21/down20只有6層，不外推13層。
- 與GPU11ms/w段相關；沒有足以保證+10%的單項預估，不把固定順序3題screen百分比作正式收益或bitwise證明。C/C2首差可見wallclock雜訊；repetition候選reject後繼續別臂，fatal/CUDA即中止並finally復原；不加輪或部署。
- DMA_BATCH原實作包含alias/API錯誤自動fallback，未取得fallback同意所以不啟用，需failclosed機制診斷另列；IO_THREADS與IQ_PREFETCH分開CPU/IO screen。PLAN/controller在state/untested-screen-20261030。

## 2026-10-30｜BIG_EXACT_P1（事前登記）
- 使用者「去實測這個計劃」；027 continuation。只新大方向P1–P4，不恢復小旗標掃描。當輪remote process只有API/watch、PID30648、A1E6/060F、f520clean，舊screen DONE/恢復。
- P1原native layout跨row×token整數microkernel，非packedR4。假設共用activation loads可減少成本；2row與4row固定兩臂；實際重用f520原Fmt32/hsum，保留int32 lane與每256-block FMA順序，無新權重副本／格式／fallback。
- 首screen IQ3_S（13層格式）取6層×6expert36，P/E各fresh、nt1/2/3，GU-only與actualGU+quant+down，5輪三臂輪替。先h/out對current native全bits；不符立即停止，不放寬品質門。
- 目標CPU pipeline14.68ms/w，完整compute1.4×才約+10%量級；僅一型原型不作整機速度推論。不佳則停止此原型，不擴展5type；成功才擴展與actualrowpartition及品質/整機AB。
- 同時P2先codebook signed patterns/建表成本，P3/P4先consumer及current-cost gates，缺證據明列不做假實測。current-best/library/input hashes＋APIidle/process gate每步核對。沒有部署或temp變更。

### P2_LUT事前登記
- 實際f520 codebooks signed4 patterns：IQ2XXS1184、XS/S1296、IQ3XXS4096、IQ3S8192。先IQ2XXS原layout LUT原型；精確int16 dot4表，max4*43*128=22016安全，-128/sign-wrap按原byte語意處理，原256block FMA與hsum不變。無activation降精度/權重展開。
- nt2/3×P/E；36sampleexpert，建表/索引/讀取全部包含，LUT每1/4/8expert amortize；5次AB/BA，GU-only與actualdown。先全部h/out對current native bits，不過即停止，不放寬品質。metadata建一次、scratch預配置且bytes另列，非production容量通過。
- P2 1token IQ2XXS現行ggml reduction不同，不混入此bitwise子測；未覆蓋5types或實際routing/core份額，不推整機speed。P1已完成兩prototype，未啟動整機測試。

## 2026-10-30 BIG_EXACT P1/P2 completed; GPU permission pending
- P1 original-native-layout NR2/NR4 IQ3_S:36unique/6layers,P/E,nt1/2/3,5rotatingpasses,GU+combined. Allsampled h/out bits match native;completeexpert NR2−3.7..−16.9%,NR4−1.8..−7.6%.NO_GO_PROTOTYPE，不擴格式或整機AB。
- P2 actual5grids完整signed4patterns1184/1296/1296/4096/8192；IQ2XXS LUT exactint16prototype（-128/signwrap保持），nt2/3,P/E,36experts,build每1/4/8experts計入，5AB/BA。Allsampled h/out bits match native；combined僅baseline13.8..25.1%吞吐，NO_GO_FULL_H_LUT，不加輪。
- P3/P4 source consumer fresh核對：prefill仍需native_data，stageprof會停用sharedstream。準備3requestprofile但包含停API的shell被auto-review launch前拒絕，原因缺明確API暫停授權；未上傳/執行、未繞過/重試，已詢問。待使用者回覆後才能處理GPU部分。
- RESULT state/big-exact-20261030/RESULT.md，STATUS PARTIAL/REPORT_LOCAL；API30648/BEST A1E6/060F、3153/20479/AboveNormal與原env保持，P1/P2 postrun gates pass。沒有部署/temp改變/GitHubpublication。不是四方向全部測完。

## 2026-10-30 GPU_COST_DIAG P3/P4（事前登記）
- 授權：user明確「允許暫停並於測後恢復」。027 continuation，三題後恢復API；無部署/temperature變更。
- 假設：現行GPU各段成本可篩選P3 dense kernel及P4跨階段fusion的足夠headroom；未量測前無+10%收益預估。
- 類型：結構方向的診斷；不是flag速度掃描。舊目標47.316→52.048tok/s需約1.92ms/token，舊GPU拆解不代替本次。
- 設計：exact A1E6/060F，p01/p05/p08原sampling、128token，單次非交錯，不能作效能AB或品質證明。STRATA_VERIFY_PROFILE會停用sharedstream/DF_BRANCH，僅instrumented各段ms/window；hc0不重複計入。
- 指標：GDN/QSA各段與windows，CUDA/fatal、容量3153/20479、前後binary/config/APIenv/priority。fresh process分類只有API/watch；controller每階段gate。
- 停止：identity/process/capacity/profilecapture不符立即停止並恢復；三題完成即停，不加輪。原型實作僅在成本與consumer證據足夠後進行。
- GPU attempt1: FAILED_BEFORE_ENGINE（既有harness禁止PROFILE）；API恢復verified PID28628。保留gpu-* receipts。最小修正attempt2：獨立harness副本僅允許PROFILE arm值1，原檔不動；停止API前完整config equality gate。樣本/容量/取樣不變，無fallback。

### 2026-10-30 GPU_COST_DIAG completion
- User explicitly authorized API stop/restore. Attempt1 inherited harness forbade profiling; no test engine; restored. Attempt2 isolated profiling-only harness assertion, full config equality pre-stop,3 original-sampling points×128,strict3153/20479,completed70/84/58windows.
- Instrumented waitCPU18.42–36.54ms/w; broad mixed attention projections4.70–5.07;shared+quant0.94–1.02;copy+combine0.49–0.61;hc0 split2.02–2.10. Profile disables shared stream/DF_BRANCH; no original critical-path/speed claim. Source collector subtracts parent when hc0 split is shown; no observed double-count.
- P3 isolatedQ6cost absent; broadgroup would need~3.0–3.5× to save3.37ms/w even if fully attributable, conditional only. P4 no new removable exposed chain sufficient for10%. No newkernel/qualityproof/engineAB; statusPARTIAL/REPORT_LOCAL, not all4directions tested.
- API restored10:22:27;independentpostgpuOK PID32568/A1E6/060F/originalenv(noPROFILE)/priority/capacity/idle, libraries unchanged, no leftoverbench. Results+coverage in state/big-exact-20261030/RESULT.md. No deployment/GHpublication.

## 2026-10-30｜R4_REPAIR_LOWREG_MECHANISM（事前登記）
- LUNA-20261012-027 direct continuation；使用者明確授權測試及 API 暫停恢復。結構型 IQ3_S lowreg 與舊 R4 對照，減少同時存活的解碼向量，代價是增加 activation loads。這一臂只測對舊 R4 bitwise，不能通過 native 品質門。
- 目標 CPU pipeline 歷史 14.68 ms/window；同期 +10% 約需 T/11，歷史尺度約 3.37 ms/window，單核測試無整機上限。既有 fullblob 最佳模型 +8.60% 非實際收益。
- 同 18 expert/6 layers、IQ3_S、P/E、nt2/3，5 輪 native/old R4/lowreg 輪替，GU 與完整 GU/quant/actual down；逐樣本 old/lowreg 全 bits，native 數值差異另記。臂不足以檢驗 prefetch 或 native 品質，不能代表整份計畫完成。
- 指標完整 expert us、GU us、全 bits、靜態組語 stack access；停止於建置、identity、process、容量、parity 失敗，或完整成本無正面證據。每個 build/run 前 fresh gate；binary A1E612…91AD8、config 060F2F…93D93、native metadata AE28…C0EE、API idle。無 prompt、無 sampling 修改；單核 BelowNormal，並存兩個測試 blob 非 production 容量通過。

### R4_REPAIR_LOWREG_MECHANISM partial completion
- 4/4 IQ3_S P/E nt2/3、18 experts/6 layers/5 rounds。相對 old R4 全 bits 相同，native h/down 大量 bits 不同，QUALITY_UNCONFIRMED。完整 expert 相對 native P +24.80/+15.83%、E −5.30/+0.49%；未含 production pool、conversion 或品質評估，不能推整機。
- API 保持原 PID32568；獨立核對 loaded/idle/3153/20479、BEST A1E6/060F、無 bench/build 殘留。首次獨立 health 使用 localhost 失敗，保留回條；改正為實際 bind address 後成功。詳細限制和待完成事項 state/r4-repair-20261030/RESULT.md。REPORT_LOCAL。

### R4_PACKED_PREFETCH 四臂事前登記
- 具體假設：對 IQ3_S packed stream 預取下一個 256-block 能降低記憶體停頓；只測一個固定距離，未假定預取有效。相同完整 blob，P=VNNI+gather，E=VNNI；native、old R4、lowreg、prefetch 四臂，P/E nt2/3，各18 experts/6 layers，5輪輪替，GU 與完整 actual down。各臂先對舊 R4 同 input bits；native 差異另報，不能宣稱品質通過。
- 原生 CPU pipeline 舊尺度14.68ms/window，單核臂無整機上限；目標 +10% 所需約同期 T/11。指標包括完整 expert、GU、位元一致性，並保留 timing 原始列。CPU 單核低優先權；事前與每 build/run 核對 BEST A1E6/060F、API idle 及程序。任何 parity/identity/process 失敗停止；局部結果不足以通過 production pool 或品質門，不部署。

### R4_NATIVE_UNPACK 品質／成本 feasibility 事前登記
- 單一清楚的精確算術 feasibility：由 packed GU 明確解回一份可重用 scratch，再呼叫原生 GU 算術與 unchanged actual down；同 input 對 native h/down 全 bits。每次 expert 使用都計完整 unpack，不把 scratch 視為免費或第二份常駐權重。此法成本若過高只否定此直接解包法，不證明其他 packed-native-lane kernel 不可行。
- P/E、nt2/3、18 experts/6 layers，五輪 native/old R4/lowreg/unpack-native 交錯；量 GU 與完整 expert，確認全部 native bits。來源 identity A1E6/060F 與 metadata AE28…C0EE，實施與前述相同 build/run process/API idle gate。無可支持+10%之成本證據則不推進 pool/整機。

### R4 packed prefetch and unpack-native completed
- Four-arm packed prefetch bitwise vs old R4: P nt2 +0.55%, P nt3 −3.93%, E nt2 +2.63%, E nt3 −3.11% complete expert; fixed distance NO_GO within tested scope.
- Full per-expert unpack then native arithmetic h/down bits exact, complete expert throughput 21.54–36.50% of native; NO_GO for this unpack method only, direct packed native-lane untested.
- HC/Q6 original schedule isolated costs unmeasured; no promotion or engine AB. Full raw hashes, coverage, API independent receipt and outstanding work: state/r4-repair-20261030/RESULT.md.

## 2026-10-30 R4_ACTUAL_POOL_TILE — pre-registration
- LUNA-20261012-027 direct continuation; user expressly authorizes real pool candidate and API pause/restore. One authoritative native blob; IQ3_S nt2/3 GU only, real ExpertPool pipeline with 9 workers plus host, all cores and existing down dispatch. Each 4-row group packs native gate, executes lowreg, packs native up, executes lowreg and SwiGLU; aligned partition covers each group exactly once. 8192 bytes thread-local scratch per participant = 81920 bytes max for ten participants, plus small stack outputs; no resident duplicate, no GPU/prefill format change. Other format/nt remains explicit existing dispatch, not failure fallback.
- Hypothesis: candidate's reduction in GU may exceed per-group conversion plus scheduling; target 10% overall requires T/11; no claim this cell suffices. Current previous best A1E6/060F, original binary source f520bc5. Baseline is same candidate-linked isolated source with arm disabled; source library drawn from current best build, not full current-best executable. Record this limitation.
- One layer 18 actual IQ3_S experts, nt2/3, nb1/4/8/16, 5 alternating A/B passes, real pool entire GU/quant/down wall time including all per-group conversion, row scheduling and worker contention. Fixed same activations; all tiles fast-pack bytes vs old and old vs lowreg dots bits for both ISA/nt; native output max diff/bit count separately. No LM semantic claim. Conversion paid on each invocation. Bounded screening not engine AB, no formal confidence claim.
- Each build/run current best SHA/config and process/API idle gates, same live capacity; input/source/library hashes. If candidate complete pool nonpositive or weak, stop; no engine, no extra cycles. If positive, next assess representative batch weighting and the exact capacity/scratch before engine. No sampling changes or deployment.

### R4_ACTUAL_POOL_TILE result
- TESTED / NO_GO for this candidate: 9 workers+host, layer8 IQ3_S/type42, n1/4/8/16 × nt2/3 × 5 alternating A/B. Conversion paid per four rows, original single blob, <=81920 bytes thread-local scratch. Full-pool throughput relative baseline −15.36/−18.32/−19.53/−17.86% nt2 and −11.33/−14.32/−8.20/−12.26% nt3. Eight medians negative, stop, no engine C/B/C.
- Every sampled row gate/up fast-pack matches old bytes and lowreg old-R4 bits both ISA/nt; pool down vs native differs at bits, max abs 5.96e-8. No logit/loss or semantic evaluation, QUALITY_UNCONFIRMED. A/B baseline isolated candidate-linked pool arm off, not A1E6 engine. API remained loaded/idle, capacity/env/priority/BEST independently verified. Full coverage, limitations, paths/hashes in state/r4-actual-pool-20261030/RESULT.md.

## 2026-10-30 R4_PREPACKED_POOL — pre-registration
- LUNA-20261012-027 direct user continuation, explicit authorization. Hypothesis: avoiding repeated packing allows R4 lowreg complete pool to improve native; only mechanism test, not single-copy production. Old per-group conversion eight cells −8.20..−19.53%; no unsupported whole-engine headroom claim.
- A native, B prepacked R4 direct lowreg, C on-the-fly four-row pack+lowreg; actual nine-worker+host pool, same 4-row GU part boundaries for B/C as previous candidate, native original partition. IQ3_S/down42 layer8 18 experts, nt2/3, nb1/4/8/16, five cyclic three-arm passes; unchanged real quant/down. Separate one-time copy and pack times, retain both datasets for shared A/B/C screen and track private/working-set peak; double resident data is a test artifact, no production capacity claim.
- Preflight all 18 blobs full GU fast-pack vs old bytes, roundtrip, unchanged down; all rows, both ISA and nt full R4 dot vs 4-row direct dot bitwise with output canaries; pool B vs C all down bits. Native numeric difference separate; no semantic noninferiority claim. Complete pool time excludes B initial pack intentionally, includes all C repacks and pool scheduling/quant/down. No SSD/GPU/transfer within CPU-only test.
- Current best binary A1E6/060F, f520bc5 and API idle/process verified; gate fresh per build/run. A/B/C same isolated candidate-linked pool, not A1E6 full engine. Stop after five rotations: if no stable positive result stop; even positive no automatic engine run or deployment. Fixed model sampling, no new flags/format sweeps.

### R4_PREPACKED_POOL completion
- Actual pool A native/B prepacked/C per-group repack, layer8/18 experts, nt2/3, nb1/4/8/16, five cyclic passes. B/A throughput ratios nt2 1.010/0.991/0.975/1.093; nt3 1.005/1.426/1.094/1.221. Mixed, nt3 nb8 B faster 5/5; nt3 nb4 native times anomalously high. C slower than B 40/40 pairs; C/B includes separate representation/workset effects. No whole-engine inference or auto engine.
- All rows/nt/ISA prepack roundtrip/old R4 bits/canary pass; B/C full pool bits pass, native differs, semantic QUALITY_UNCONFIRMED. Full setup 18 blobs copy 2146.2us and GU pack 2768.3us excluded from B, representations 33,638,400B each, process sampled peak private 80,515,072B. Single representation/GPU/prefill/capacity unresolved. API unchanged and independent verification pass. Full matrix, paired evidence, paths/hashes in state/r4-prepacked-pool-20261030/RESULT.md.

## 2026-10-30 R4_ENGINE_CBC — pre-registration
- 027 direct-user continuation; user explicitly asks isolated engine port and Hermes10×512 C/B/C with original sampling, user explicitly allows API pause/restore. Candidate IQ3_S R4, current best A1E612…91AD8/config060F…93D93/source f520bc5, identical 3153 slots/20479MiB, routing/tailskip, 9workers/priority/env, no second resident model copy, no deployment/fallback.
- Prior isolated pool prepacked nt3/nb8 +9.4% median/5 of 5; nt2 mixed, not engine estimate. Target +10% requires T/11; prior 47.316tok/s implies 1.92ms/accepted token as scale only. On-the-fly repeated four-row pack failed; do not rerun that. Include all prepacking/transfer/initialization costs, sample actual accepted tokens/window, decode times, SSD, capacity and output; paired C/B/C single blocks are short screen, not confidence proof.
- Each build/run current-best identity and fresh process gate, actual original prompts and sampling, strict capacity, fatal/broken-output stop. Before each block fresh engine. User-authorized API stop only after checking idle and process tree; restore and independent final verification. Semantic quality unconfirmed absent fixed-token and formal task evidence; no auto promotion. REPORT_LOCAL, previous publication rejection still applies.

### R4_ENGINE_CBC completion（2026-10-30，13:0x 唯讀補收）
- 遠端 campaign.json phase=DONE、error=null、restored/verified=true；build 12:15:56 完成（僅 C4996 warning），C r0→B r0→C r0 皆 OK，restore 12:26:12。B binary 434DD4EB…4FE607。
- result.json：C1 40.263、B 35.746、C2 40.527 tok/s；B/C1 0.8878、B/C2 0.8820（B 慢約 11–12%）。quality UNCONFIRMED（semantic/operator bitwise NOT_MEASURED）。單一 C/B/C 短篩，非正式 CI；10 題中 B 只有 p03、p06 高於第一個 C。
- 判定 NO_GO：每批動態 prepack 的 IQ3_S R4 候選整機變慢，與 pool 中 per-group 轉換 40/40 輸、prepack 成本未計入 B 的推論一致。不加輪、不部署。
- API 已恢復：PID14832（12:25:54 起）、exe A1E6…91AD8、config 060F…93D93、AboveNormal、health loaded、final_verify idle/3153/20479；無 controller/build/bench 殘留。由筆電端唯讀 SSH 獨立抽驗 hostname、result.json、API path/SHA/priority。

### 2026-10-30 BASELINE_RESIDUAL_OBSERVATION（本機分析，未跑新測試）
- 同 A1E6/060F、同 harness rate 公式（m_out_tokens/m_decode_ms）：R4_ENGINE_CBC 的 C 只有 40.26/40.53 tok/s，10/29 LFUSE C 47.316、SPEC_SPLIT C 48.57。
- 以 rows 的 windows 加權：殘差 ms_window−verify_ms−draft_ms 在 10/29 SPEC_SPLIT C 1.70、DIAG 1.65、10/30 上午 GPU profile 1.56–1.69；12:05 CBC 的 C1 7.39、B 6.59、C2 5.19 ms/w。GPU-reach wait（11.7）與 CPU 段（20.7–24.0 vs 22.7）沒有同步變大。engine timing line 本身沒有逐項列出這段（例：58.85 = verify 48.85 + commit 0.09 + draft 1.68，還差 8.2）。
- 原因未查（啟動方式、背景負載、build 後狀態等都只是假設）。CBC 的 B/C 比較是同條件，仍然有效；但 live API 是否也處於高殘差狀態未知。下一步需另行授權：先唯讀看 live engine log 的 timing line，再決定要不要做 C-only 診斷。

### 2026-10-30 BASELINE_RESIDUAL 追查（唯讀，未停 API、未跑請求）
- 正式 API log（runs/miss-overlap-20261027/s2k-mt1-api.engine.log）逐 request 殘差：10/28 21:34 由 Strata-MT1Deploy-20261028（RunLevel Highest）啟動的引擎 1.52–1.70 ms/w；10/29 05:55 起所有 Strata-Task020-API（Limited）啟動的引擎，包括 10/29 和 10/30 的實際請求，7.08–8.23 ms/w。
- 同 binary、同 config：spec-split C（10/29 12:58）1.53–1.76、GPU profile（10/30 10:20）1.46–1.63、CBC C（10/30 12:15，Strata-R4-Engine-CBC，Limited）8.07–8.68。CBC 與 spec-split 的引擎命令列逐字相同，啟動訊息除 timing 數值外也相同。
- 所有 Strata 排程：低殘差的執行都來自 RunLevel=Highest 的 task（MT1Deploy、LFUSE、DIAG、Overnight…），高殘差只出現在 Limited（Task020-API P2、R4-Engine-CBC P7）；task priority（P2/P7）跟殘差沒有對應。強相關、未證因果，機制未知（不在 decode 迴圈有計時的段：GPU wait/CPU/commit/draft 都沒變）。
- 影響估算：LFUSE C 38.56 ms/w＋6.3 → 約 40.6 tok/s，與今天 C 40.3–40.5 吻合。即歷次 A/B 的 47–48 tok/s 是提權環境的數字，正式 API 自 10/29 05:55 起實際約 40 tok/s。
- 下一步待授權：同 harness 同 binary 交替用 Limited／Highest task 啟動的短 C/C 對照（需停 API）；確認後再找出需要權限的具體機制。改 API task 為 Highest 會讓對外服務以系統管理員權限執行，屬安全設定，由使用者自行決定、不由 agent 修改。
- 更正（同日，使用者指出）：task priority 7 會變慢是已知問題（10/28 S2K_PROMOTION 起佇列一律用 priority 2）。R4_ENGINE_CBC 的排程以 P7 註冊，違反既有做法，所以它的 C 40.3 tok/s 不能跟歷史 47 比；B/C 兩臂同條件，相對結論仍成立。上面「Highest／Limited」的相關性與 P2／P7 混在一起，不能單獨歸因於 RunLevel。
- 仍未解釋的一點：正式 API（Strata-Task020-API 是 P2）從 10/29 05:55 起的實際請求殘差也是 7–8 ms/w。目前 live 程序鏈：launcher powershell AboveNormal、serve.server 那幾個 python 是 Normal（Windows 不會把 AboveNormal 傳給子程序，BelowNormal 才會）、strata.exe AboveNormal。P2 harness 的 server 優先權尚未核對。
- 2026-10-30 下午 LIVE_TWO_REQUEST_CHECK（使用者授權送兩個請求，不停 API）：送前 SSD C: 剩 63.3 GB（已用 670.9）；gate：API idle/queued0、只有 strata.exe PID14832。桌機本機對 live API 送 p02×128（原 sampling、seed1002、非串流），client 分別 AboveNormal／Normal：殘差 49.18−45.58−0.07−1.75=**1.78**、35.98−32.69−0.06−1.51=**1.72** ms/w（42/87 windows）。結論：live 引擎本身目前不慢，client 優先權（AboveNormal vs Normal）沒有影響；10/29 起 log 裡 7–8 ms 的是外部實際請求，CBC 的 8 ms 來自 P7（server 鏈為 BelowNormal）。待驗證假設：外部客戶端用串流（stream=true），引擎每個 window 間接等 Python server 處理輸出。
- 2026-10-30 下午 LIVE_STREAM_CHECK（使用者授權送一個串流請求）：gate 同上；p02×128 同 sampling，只加 stream=true（89 chunks，wall 2.6s）：61 windows、36.27 ms/w = verify 26.56＋commit 0.06＋draft 1.56，**殘差 8.09 ms/w**；同條件非串流 1.72–1.78。確認：HTTP 串流每個 window 多約 6.3 ms，數值與 10/29 起 live 外部請求的 7–8 ms 吻合（n=1 對 n=2，但殘差指標本身很穩）。代表實際使用（串流）比 benchmark（非串流）慢約 14–17%。另：10/14「stream 較快」指的是 MTP 草稿模式（pooled vs stream），與 HTTP 串流無關。下一步：唯讀查 serve.server 串流路徑與引擎在串流時多做的事。
- 2026-10-30 STREAM_PATH_READ（唯讀程式碼，未送請求）：live server = upstream-v0142/serve/server.py（6329 行，複本在本機 scratchpad）。串流與非串流用同一個 chunks generator（openai_chunks），差別只有串流在 server.py 約 5253–5262 行每個 chunk 做 wfile.write＋flush；非串流收完一次回傳。引擎 stdout 由獨立讀取執行緒放進 slot_q queue（約 1418 行），server 送給引擎的指令（GEN/STOP/BSTOP/BYIELD）和 sampling_keys 不受 stream 影響。所以 server 不會直接卡住引擎；6 ms 落在引擎 decode 迴圈沒有計時的段（suffix/lookup 草稿、apply_pending、window 後處理）。server 只綁 Tailscale IP <tailscale-host>，連本機 client 的串流封包也經過 wintun/tailscaled。機制未定，待測：串流時各程序 CPU（tailscaled/python/System/strata）。
- 2026-10-30 使用者決定：客戶端預設關閉 HTTP 串流，只在需要 debug 或即時看思考時才開。預期 decode 每個 window 省約 6.4 ms（約 +15%，依 n=1 串流對 n=2 非串流）。server stdout log 沒有印出每個請求的 stream 旗標（那行只在特定模式才輸出），所以無法從 log 回頭核對外部請求是否都是串流；串流機制本身仍未定位，之後可考慮在 server 端合併 SSE 送出。

## 2026-10-30｜NT1_EXT_TYPES（事前登記；使用者「好，先做這個」）
- 類型：結構（家族：CPU kernel 效率／單 token dispatch；延伸 10/28 IQ3S_MT1，含 R4_PLUS10 U14 未跑的 IQ2_S nt1）。不是 R4、不是旋鈕掃描。
- 假設：如果把 nt=1 gate/up 依型別×核心改走既有 iq256（IQ2_S：P/E 都用 VNNI 無 gather；IQ2_XS、IQ3_XXS、IQ2_XXS：只在 P 核用最佳臂，E 核維持 ggml），則 CPU 段每 window 省約 0.7 ms（10/28 IQ_ALLTYPES 單核外推；IQ3_S 同法實測為估計的 1.5 倍），因為這些型別的 ggml AVX2 解碼在單核實測慢 1.08–1.27 倍。
- 目標段／上限：gate/up；外推 0.7（最多約 1.0）ms/w ≈ +2～3%；單獨達不到 +10%，需與 clang-cl、direct-to-arena、殘差等其他段一起。
- 指標：tok/s（按輪配對）、引擎自報 CPU 段 ms/w、GPU-reach 不變、輸出長度、check/parity。
- 設計：第 1 階段（不停 API）：遠端獨立 worktree 加 opt-in env 的型別×核心 dispatch，build，kernel 層 A/B 數值檢查（nt2/3 與未選型別必須 bitwise 相同；選中型別差異 ≤1e-4 相對）。第 2 階段另行執行：C/B/C 交錯，Hermes 10 題×512，至少 5 輪，priority 2／AboveNormal，3153/20.00/20479。
- 停止：第 1 階段 parity/build/identity 任一失敗即停；第 2 階段前三輪全負或均值 <−3% 停止；5 輪均值 ≥+1.5% 且 CI 不跨 0 才算正面，可與其他候選組合；不部署。
- Identity gate：current best A1E6…91AD8／config 060F…93D93／source f520bc5；每次遠端操作前 process gate。
- 第 1 階段結果（2026-10-30，不停 API）：gate 通過（DESKTOP-LKMLUPC、live PID14832 A1E6／060F／f520bc5、只有 live 堆疊、C: 63.5 GB）。新 worktree C:\Users\User\nt1ext-20261030，branch nt1ext-20261030，commit 27fa1c5（本地，未 push），只改 src/kernels/cpu/native_expert.cpp +36 行；opt-in env STRATA_IQ_NT1_EXT=1（需 MT1=1、MT_MIN 未設，否則無作用；無 VNNI 等條件即 abort，無 fallback）。新 exe FD272B49…FC129A（同 A1E6 build 腳本）。Parity（真實 GGUF blob 每型 66 個×3 activation，呼叫真正 native_gu_rows）：選中格（P 核 16/17/18/22 nt1、E 核 22 nt1）max_abs ≤7.15e-7（≤2.0e-7 滿刻度）；E 核 16/17/18、所有 nt2/3、type21 全部 bitwise 相同；全 finite。單核計時（5 次中位）：IQ2_S P 1.289×／E 1.295×、IQ2_XS P 1.243×、IQ3_XXS P 1.163×、IQ2_XXS P 1.091×，與 10/28 一致。負面測試：無 MT1 時無作用；STRATA_NO_AVXVNNI 時 abort。引擎未用新 binary 啟動。產物 state/nt1ext-20261030/。待第 2 階段整機 C/B/C（需停 API 授權）。
- 第 2 階段結果（2026-10-30，Codex gpt-6.1-terra low 執行，協調者重算核對）：attempt1 停在 process gate（第 1 階段 build 遺留 vctip/mspdbsrv，14:05 建立、parent 已不在，協調者核對後停止）；attempt2 run dir runs\nt1ext-ab-20261030，task priority 2 讀回、PT3H，10 block 全 OK，NT1_EXT 只在 B 生效，容量/AboveNormal/MT1 皆符。按輪 B/C：+5.39、−2.30、−2.45、+4.97、+1.62%，平均 **+1.44%**，95% CI（df=4）**[−3.25, +6.14]**；CPU 段配對 −0.68 ms/w（與事前外推 0.7 相符，但每輪 ±2.5 ms 雜訊）。輸出長度 B 平均短 21 token（sampling 結果不同）。判定：**未通過**（均值 <+1.5% 且 CI 跨 0）；機制方向一致但效果小於 5 輪可偵測量，不部署。C 臂本身 44.5–48.7 tok/s，先跑的臂較快的順序效應明顯。API 恢復獨立核對：PID21760、A1E6/060F、AboveNormal、3153/20479、idle，無殘留，測試 task Disabled。產物 state/nt1ext-ab-20261030/RESULT.md。
- 旁註：遠端電源計畫是 Razer Cortex Power Plan，最低處理器狀態 AC/DC 皆 100%、最高 100%、核心暫止下限 4%；歷來 benchmark 都在此設定下跑，沒有做過與平衡模式的 A/B。
- 2026-10-30 補收 UNTESTED_SINGLE_FLAGS_SCREEN 結果（遠端 runs\untested-screen-20261030\result.json，唯讀讀取；先前未回收）：SCREEN_COMPLETE_NO_PROMOTION。固定順序 3 題×128，C 33.31／C2 36.21 tok/s（A/A 漂移 +8.7%）。輸出與 C/C2 相同（無額外分歧）：EXPERT_V2 35.54、DF_PLE 38.24、DF_QB_Q4 38.45、DF_BRANCH 39.02、MMVF_ROWS 39.03、ATTN_LANECELL 37.88；數值分歧較早（未決）：FUSE_HEAD_GR 33.30、GR_DOWN_MAX4 37.87。對 C2 為 −1.9～+7.8%，固定順序且非配對，不構成速度證據；10/29 單開 screen 的 LFUSE +3.9% 後經正式 A/B 為 −1.26%，同類 screen 會高估。這六個輸出一致的旗標從未做過配對 A/B。

## 2026-10-30｜GPU6_BUNDLE_AB（事前登記；使用者「確定沒跑過就去測」）
- 已確認未做過：10/29 G bundle（含 GDN_SPLIT/TSUM/LFUSE/QFUSE，BROKEN）與兩次單開固定順序 screen；這 6 旗標組合從未配對 A/B。
- 類型：旋鈕組合（家族：GPU 現成精確旗標；上次同家族為 10/29 LFUSE 正式 A/B −1.26%）。只跑這一次，不二分、不加輪。
- 假設：B＝A1E6/060F＋STRATA_DF_BRANCH=1、MMVF_ROWS=1、DF_QB_Q4=1、DF_PLE=1、ATTN_LANECELL=1、EXPERT_V2=1；若各自省下 GPU 段小量時間，合計可縮短 GPU-reach wait，因為兩次 screen 輸出與 C 相同且單開 +4.6～7.8%（固定順序，可能高估）。
- 目標段／上限：GPU-reach 約 11.7 ms/w；省 1–2 ms ≈ +3～5%。
- 指標：按輪配對 tok/s、GPU-reach／CPU／draft ms/w、輸出長度、錯誤與重複迴圈。
- 設計：同 binary，C/B 交錯 5 輪（CB、BC、CB、BC、CB），Hermes 10 題×512 原 sampling，priority 2／AboveNormal，3153/20.00/20479。
- 停止：第 3 輪後全負或均值 <−3% 停；5 輪均值 ≥+2% 且 CI 不跨 0 且 GPU-reach 配對下降才算正面；不部署。
- Identity：A1E6…91AD8／060F…93D93；每 block process gate；結束恢復 API 並獨立核對。
- 結果（2026-10-30 15:15–15:43，Codex 執行，協調者由遠端 blocks.json 重算）：10 block 全 OK。按輪 B/C：−3.14、+5.25、+1.02、−1.32、+1.25%，平均 **+0.61%**，95% CI（df=4）**[−3.31, +4.53]**。GPU-reach wait 配對差 −0.04、−0.21、+0.06、+0.01、+0.17 ms（≈0，機制未動）；差異全在 CPU 段雜訊（±4 ms）。判定：**未通過**，六旗標組合對此機器 GPU 段無可量測效果；GPU 現成旗標家族結案，不二分、不重跑。API 恢復：final_verify verified，PID22184、A1E6/060F、loaded、3153。
- 協調者更正（2026-10-30）：此 A/B 的「GPU 段沒變」結論在 10/29 GPU_SWITCH_EXACT_SCREEN 就已有證據（各單開臂 GPU-reach 11.08～11.86 vs C 11.55／C2 11.73，噪音內），提案時只看了 tok/s screen 而漏看機制欄位；本輪是重複確認，非新資訊。

## 2026-10-30｜SPEED_PRIOR_ART_SEARCH（研究，Codex gpt-6.1-terra low＋web search；不連遠端）
- 品質定義寫明：同權重/量化值、同路由與 top-k、同 sampling、精確 speculative；只允許浮點加總順序差異。報告 state/speed-research-20261030/RESULT.md；協調者抽查 8 個來源連結皆真實且標題相符。
- 候選：MTP tree verification、Delayed tree expansion、OPT-Tree、SAM/SuffixDecoding、DirectStorage、IOCP 批次完成、llama.cpp PR#26348 Q2_0 VNNI、large pages、SP-MoE 預取、expert deferral、admission copy 消除。
- 協調者判讀：tree 三項被 10/14 MTP_OPTIONS 證據削弱——MTP 接受率約 87%，被拒位置 Top-2 rescue 0/41（full-head 也 0/41），且 verify 成本隨 T 陡增（T1/T2/T3 26.4/37.0/53.3 ms），多驗節點＝多 expert；suffix 類同 lookup-chain 家族（+1.59% 不穩、只 4.56% window 有 chain）；DirectStorage/IOCP 屬已暫停的 SSD 家族；Q2_0 VNNI 打 down，down 已 DRAM 受限；large pages、admission copy、預取、deferral 為已知或已受挫方向。結論：未找到新的、有證據可單獨接近 +10% 的方向。
- 旁註：current best 使用 ROUTE_TAIL_SKIP=7（CUDA 預設，跳過整個 window 都在 rank≥7 的 miss expert），嚴格說已不符合「同路由」定義；它是基準的一部分，品質定義應以 current best 為參照。

## 2026-10-30｜UPSTREAM_FORK_SEARCH（研究，Codex terra low＋web；不連遠端）
- 範圍：Niko1221/Strata release/PR/issue/社群跑分、fork（AdrianBM96/Strata3060、Lamina、Basalt、strata-4gpu），重點 4070。報告 state/upstream-search-20261030/RESULT.md；協調者抽查 #3724、#1922、llama.cpp #30553、v0.2.8 連結皆真實。未完成全量盤點（fork 清單、compare 頁抓取失敗）。
- 4070 相關：#1922 關 STRATA_LOOKAHEAD +19%（全常駐機器）→ 我方 live 已是 LOOKAHEAD=0，已在 baseline；#3724 llama.cpp #30553 MMQ Stream-K cap，4070S+2080Ti 雙卡單次 decode +12.66%，作者稱因果未明，且 MMQ 一般用於大 batch，我方 verify window 2–3 token 可能走 MMVQ，未確認；#3448 profile 更新在雜訊內；#4261 雙卡 stage trim 不適用；ROUTE_PRIOR 改路由排除。
- fork 多為多卡或 Blackwell 專用，不適用單 4070；Strata3060 無可核實 fork-only patch。
- 結論：未找到確認為新、符合品質、對本機有證據的候選；唯一線索是 #30553 是否命中我方 decode 路徑（需唯讀查 source），以及 0.2.8 相對 0.2.7.1 的 Qwen 變更（未歸因）。

## 2026-10-30｜CPU_KERNEL_SEARCH（研究，Codex terra low＋web；不連遠端）
- 報告 state/cpu-kernel-search-20261030/RESULT.md；協調者抽查 ik_llama #1474、KTransformers #2240/#2242、llama.cpp #27402/#25346 皆真實。
- 找到：ik #1474 是 R4 的 VNNI 路徑（已試家族）；KT #2240 的 IQ kernel 摘自 ik（同源，未給 nt=1 加速數字）；KT #2242 小視窗按 expert 合併 token（Q4_K、EPYC，1.09–1.14×，我方 nt≥2 已共用）；llama.cpp #27402 是大 batch prompt 的 int8 panel GEMM（非 decode，且報 0.24% PPL 差）；#25346 MSVC 偵測 AVX-VNNI（pp +32%、tg 不變，Q4_0）；T-MAC/Neural Speed 不支援原 IQ codebook 或同屬 LUT 家族；無 clang-cl vs MSVC 同 kernel 實測；無 Gracemont 專用方案。
- 結論：沒有合格候選。三次外部搜尋（一般、上游/fork、CPU kernel）均未找到在「同硬體、同權重、同路由、結果與 current best 相同」條件下的新方向。

## 2026-10-30｜POOL_INTERNALS_AND_UNTIMED_DIAG（事前登記；使用者「好」）
- 類型：結構診斷（不是加速方案；DIAG build 只加計時，輸出不應改變）。對應 PLUS10_REVISED_PLAN §3A「CPU 原生 pipeline 成本診斷」（當時列第一優先、未執行）＋ decode 迴圈未計時段。
- 問題：pipeline 上線後 CPU pool 段約 15.4 ms/w（GU＋quant＋down 重疊後 wall）內部從未拆過；window 中 commit＋未計時約 3.5 ms/w 也未拆。
- 要交付：(1) pool 內每層：host dispatch→第一個 worker 開始延遲、GU／quant／down busy（P 群、E 群分開）、worker 閒置等待、最後完成−最先完成（拖尾）、host 等 pool 完成時間、與 GPU 等待重疊；(2) decode 迴圈：suffix/lookup 草稿、apply_pending（adaptive swap）、commit 各子段、window 後處理、仍未歸屬的剩餘；(3) 守恆檢查（各段和 vs ms/window）；(4) 列出任何暴露在 critical path、可移除、≥1 ms/w 的具體成本，或明確說沒有。
- 設計：同 f520bc5 source 加計時（優先沿用 10/29 overnight 的 CPU_PHASE_DECODE／thread-own counter DIAG 機制），env 開關，關閉時行為不變。臂 C（A1E6）與 D（DIAG on），Hermes 3 題（p01/p05/p08）×512 原 sampling，C/D/C/D 兩輪；priority 2／AboveNormal、3153/20.00/20479。
- 停止／判讀：D 的 ms/window 比 C 慢 >5% → 標「計時擾動大」，數字只作相對參考；守恆誤差 >10% → 不下結論；build／identity／process gate 失敗即停。不加題、不加輪、不部署。
- Identity：A1E6…91AD8／060F…93D93；DIAG binary SHA 另記。
- 結果（2026-10-30，Codex terra low，第 4 次完成；前 3 次在實作前自行停止，未停 API）：DIAG binary DA40C93A…13D3（f520bc5＋計時 patch，本地 commit ed0b9d62），C/D/C/D 3 題×512。C 42.71／D 38.79 ms/w（D 較快 9%，sampling 輸出不同，非計時開銷估計）。Pool（D，每 worker 平均）：GU P 9.15／E 9.63、quant ≈0.01–0.04、down P 3.83／E 3.95 ms/w；host 等 pool 完成僅 0.173 ms/w（無明顯拖尾等待）。decode 迴圈：verify 35.43、MTP draft 1.67、apply_pending 0.68、commit+emit 0.06、suffix/lookup 0.001、未歸屬（含 window 後處理）0.94 ms/w；守恆以差額定義。未量：dispatch 延遲、idle/spin、skew、GPU 重疊、commit 子步驟。判讀：未計時段約 1.7 ms/w 已拆開，最大為 apply_pending 0.68，皆 <1 ms；pool 工作分配平衡、host 等待極小，CPU 段仍由 GU 解碼本身主導。沒有找到 ≥1 ms/w 可移除的成本。API 恢復並獨立核對（A1E6/060F、AboveNormal、3153、idle），排程已停用。

## 2026-10-30｜GPU_CLOCK_LOG＋GPU_KERNEL_BW_DIAG（事前登記；使用者「兩個都做」）
- 類型：診斷（不改 source、不改 live）。
- A 時脈：不停 API，live 送一個非串流請求（512 token），同時 nvidia-smi 每 100 ms 記 graphics/mem clock、P-state、功耗、使用率、溫度。問題：decode 期間 GPU 是否在 CPU post 段降頻、pre 段時脈是否低於 boost。判讀：pre 段時脈明顯低於閒置/最高 boost（>10%）或在 P2 以下來回 → 列「驅動電源模式／鎖時脈」為候選（需使用者改設定）；否則結案。
- B 頻寬：停 API，用 Nsight Compute（若遠端有 ncu）對 decode window 中主要 kernel（native_mmvq_il/multi、gr_up_multi、gr_down_staged、native_q5_k/q6_k_mmvq、attn_chunk）量 achieved DRAM GB/s、% of peak、duration；粗算依據 10/27 nsys：稠密投影約 300 GB/s（59%）、HC 約 350 GB/s（69%）。判讀：主要 kernel 已 ≥80% peak → GPU kernel 方向結案；若 ≤65% 且合計時間 ≥5 ms/w → 值得設計 kernel 改寫（上限約 2.5 ms/w）。ncu 會序列化 kernel，只看單 kernel 指標，不看 wall。
- Identity：A1E6/060F；B 另跑時 process gate、priority 2、finally 恢復 API。
- A 結果（2026-10-30 18:40:45–18:41:01，live PID22184，不停 API；1 請求 66→512 token，38.6 tok/s，draft 215/accepted 191；原始檔 state/gpu-clock-20261030/gpuclk.csv、req.json）：decode 期間 graphics clock 固定 2850 MHz（最高 3105，低 8.2%，<10% 門檻；2850 是 4070 負載下的正常持續 boost），整段沒有降頻、沒有 P-state 來回；P-state 一進 decode 就是 P2 並維持到結束，memory clock 10251 MHz。功耗 71–107 W（遠低於 200 W 上限）、溫度 42–52°C、nvidia-smi 使用率 71–100%（100 ms 取樣看不到 ms 級的 post 段閒置，但時脈沒掉）。閒置時 P8（210/405 MHz）；第一次使用從 P8 升到 P2 約 0.25 s，請求結束後約 2 s 降 P3、6 s 降 P5/P8——只影響請求開頭一次，不影響 steady-state。判讀：**不符合候選條件，時脈方向結案**。旁註：CUDA 程式預設被驅動放在 P2，memory 10251 MHz；4070 的 P0 一般是 10501 MHz（本次未記 clocks.max.mem，屬推定），差 2.4%。就算 GPU 段全部吃頻寬，上限約 0.27 ms/w（≈+0.7%，雜訊內），而且要使用者用 Profile Inspector 關「CUDA Force P2」，不列為候選。
- B 結果（2026-10-30，Codex terra low）：**未取得數據**。Nsight Compute 2026.1.1，elevated 一次性 task，priority 2，clock-control none。第 1 次多指標：kernel replay 無法保存記憶體（VRAM 只剩 254 MiB）而失敗（另有 prompt 參數腳本錯誤）；控制器未自動還原，Codex 確認程序退出後手動啟動 API。第 2 次只量 duration/read/write、短 prompt：注入下 3127 slots，引擎在 prefill「0 layers served」卡 60 s 觸發 stall report，退出碼 0xC0000409，無 report。推論（未驗證）：ncu 逐 kernel 序列化／replay 與此引擎的 CPU–GPU 交錯流程不相容。API 已恢復，協調者另核對 /metrics 3153 slots、只剩一個 strata.exe（PID 23184），無 ncu 殘留。stall dump strata-stall-8284.dmp 留在 build 資料夾。
- B' 改用 nsys（事前登記；使用者 2026-10-30「改用nsys」）：停 API，A1E6/060F 同 args/env，nsys profile/launch 加 `--gpu-metrics-devices=0`（GPU metrics 取樣，不序列化 kernel）＋ cuda trace，短 prompt GEN 512。量：GPU 忙碌區間（pre 段）的 DRAM read/write throughput 取樣均值與時間加權 GB/s、% of 504 GB/s；按 kernel 家族（mmvq 稠密、gr_* HC、attn、其他）用 kernel 時間區間對齊取樣算各自平均頻寬。槽數只記錄（10/27 先例 3135 已被接受）。判讀規則同 B：≥80% 結案；≤65% 且合計 ≥5 ms/w → 值得設計 kernel 改寫。nsys 加的 trace 開銷會讓 wall 變慢，只看 kernel 期間頻寬比例。
- B' 結果（2026-10-30 18:5x，Codex terra low）：**未取得數據**。nsys 2026.5.1、AD10x general set、20 kHz，注入下 3135 slots。短 prompt 只有 15 token，模型 13 token 就結束（DONE stop）；nsys start 在第一行 T 才同步觸發，太晚：kernel trace 為空（"No CUDA events collected"），GPU_METRICS 只涵蓋 0.18 s 且 GR Active 全為 0（協調者查 sqlite 確認，無可挽救資料）。確認可用：此版本 metrics 有 DRAM Read/Write Bandwidth %、GR/SM Active。API 已恢復（PID 22020、3153、SHA 一致，task 已註銷）。修正方向：用 10/27 neuro.tokens 長 prompt（已知能生成 512 token），nsys 從程序啟動就收集（不用 start/stop），事後按 T 行時間切出 decode 段。
- B'' 結果（2026-10-30 19:1x，協調者自己執行；terra 第 2 次前檢後停）：**取得數據**。nsys profile 全程、ad10x 10 kHz，neuro.tokens GEN 512 完整，decode 292 windows／44.4 tok/s／GPU-reach 12.78（與 live 相近）。每 window：dense mmvq 6.96 ms @69.4%（350 GB/s）、HC gr_* 3.66 ms @66.2%（334）、attention 1.26 @40%、GDN 0.95 @68%、router 0.25 @23%；wait_flag_ge（GPU 自旋等 CPU）16.3 ms/w。長 kernel 較可信：q5_k_mmvq 86.7%、mmvq_il 72.3%；短 kernel（10–17 µs）在 100 µs 取樣下只能粗估：native_gu_multi 39%、native_down_multi 26%。判讀：dense/HC 落在 65–80% 灰區，事前規則兩端都不觸發；拉到 85% 的上限約 2.1 ms/w（+5%），加上 GPU expert kernel 粗上限約 +1.5 ms/w，且只作用在 GPU-reach 段。API 還原 PID 5412／3153／A1E6，task 已移除。報告 state/gpu-bw-nsys-20261030/RESULT.md。

## 2026-10-30｜OVERLAP_NARROW_SEARCH（研究，Codex terra low＋web；不連遠端；使用者「好去讓他查一下」）
- 題目：batch=1、結果相同的 MoE CPU/GPU 重疊方法，排除已試／不合格七類。20 組搜尋。報告 state/overlap-search-20261030/RESULT.md（Codex 誤寫到 D:\strata\RESULT.md，協調者已移入）。
- 找到 5 類，協調者對照既有證據：(1) Fiddler 式依實際路由把 miss expert 搬到 GPU 算＝PIN8／PCIE_BALANCE 同機制，已測（CPU −2.2 ms、GPU-reach +1.4 ms 抵銷；balance −1.43%）；(2) 單一 expert 按中間維度 CPU/GPU 分算：GPU 仍需經 PCIe 取權重，是 (1) 的更細粒度版，同受 PCIe／GPU-reach 抵銷限制，無新證據；(3) 分段回傳／提早合併：今天 pool 診斷 host 等 pool 僅 0.17 ms/w，llama.cpp RFC #24528 同類實驗 −2.6～−6%；(4) 縮短交接（stream wait value／doorbell）：Windows GeForce（WDDM）上 cuStreamWaitValue 需 TCC（舊文件，未確認現況），pool dispatch 延遲尚未量，但估計 <1 ms/w；(5) Saguaro 驗證中預先 draft：MTP 需要 verify 最後一層的 hidden state，draft 本身 2.16 ms/w，依賴無法提前。
- 結論：沒有新的、可單獨預期 ≥3% 的方向；不排實驗。

## 2026-10-31｜UNTESTED5（事前登記；使用者「都幫我測一下叫terra low，全測」；Codex gpt-6.1-terra low 依序執行 S1→S2→S3）
- 類型：結構（家族：VRAM placement／MTP draft／編譯器；皆為輸出精確類：只影響 draft 接受率、expert 放置或浮點加總順序）
- 拆解來源：pipeline 後 39.18 ms/w（GPU-reach 11.63、pool 15.41、join 4.65、LRU 1.04、draft 1.76、其他約 3.5）；目標 +10% 需省 3.37 ms/w。
- S1：VRAM 未歸屬約 930 MiB 逐項盤點；draft 詞表 106,299→65,536／32,768（FR-Spec 式）A/B，5 輪輪替×10 Hermes×512；large-page 權限唯讀檢查（不改權限）。上限：draft 1.76 ms/w 中的 head 部分＋釋出 VRAM（每 100 MiB ≈ CPU expert 工作 −1.0～1.2%）。
- S2：clang-cl 對 MSVC 微基準（5 種 GU 型別×P/E×nt1–3＋down）；P-core 加權 ≥1.05× 才建整機並 A/B。上限：GU 1.1× ≈ 0.85 ms/w，1.2× ≈ 1.6 ms/w。
- S3：MTP 512 expert（675 MiB VRAM）路由分佈 DIAG＋top-N 常駐成本模型；估計淨 ≥ +1.5% 才做原型並 A/B。上限：+675 MiB ≈ CPU expert 工作 −8.0～9.6%（約 1.2–1.5 ms/w），未扣冷 expert 成本。
- 停止條件：各 stage brief 內定；V 臂 3 輪全負即剔除。API 由使用者關閉，全程不啟動、結束保持關閉。不部署。
- 2026-10-31 S1 結果（協調者由遠端 s1\ab\blocks.json 重算；state/untested5-20261031/s1-vram-vocab/RESULT.coordinator.md）：C/V64/V32 各 5 輪輪替、10 Hermes×512、原 sampling、exe A1E6。V64 −1.08%（CI −5.54～+3.38），V32 −2.47%（CI −6.64～+1.69）。機制：V64 draft 1.76→1.49 ms/w、tok/w 1.786→1.781；V32 draft 1.29 但 tok/w 1.726（−3.4%）。三臂 slots 都是 3153，縮小 head 釋出的 VRAM 沒有轉成 expert slot。詞表涵蓋率（過去 Hermes 輸出）現行 96.24%／V64 95.88%／V32 88.84%。判定 NO_GO（理論上限約 +0.7%）。S1.2 trace 拆分略過、S1.3 VRAM 逐項盤點只完成部分；SSH 帳號無 SeLockMemoryPrivilege（唯讀）。
- 2026-10-31 S3 進度：Codex 第一版 DIAG patch 無效（在 CUDA graph 錄製中的 record_rest 內做 cudaStreamSynchronize 與 pageable 複製），協調者改成錄進 graph 的 pinned host 複製、draft() 同步後印出，05:15 重新 build。
- 2026-10-31 S3 結果（state/untested5-20261031/s3-mtp-experts/RESULT.coordinator.md）：修正版 DIAG exe 4C0F2F8C…，10 Hermes×512，1198 次 draft、1924 個 draft step（約 1.61 step/window）、19,240 次 expert 呼叫，512 個 expert 用到 493 個。前 N 個常駐的涵蓋率：128→65.1%、192→78.1%、256→86.7%、384→97.1%。成本模型：釋出 VRAM 依 ruler 省 0.26～0.94 ms/w；扣掉冷 expert 的 PCIe 上傳（串行在 draft 鏈上，每個 70～90 µs）和 host 備份佔用 RAM 造成的 SSD 增量後，最佳淨效果約 +0.3 ms/w（約 +0.8%），低於 0.6 ms/w 門檻。另外 S1 顯示釋出的 VRAM 不會自動變成 slot。判定 NO_GO，原型與 A/B 依門檻略過。
- 2026-10-31 S2 結果（state/untested5-20261031/s2-clang/RESULT.coordinator.md）：
  - 微基準（層數加權）：P-core nt1／2／3 為 1.149×／1.019×／1.018×，E-core 為 1.075×／1.139×／1.094×；輸出 max_abs 1.19e-7。
  - 整機 clang-cl build：EF8AF397…（CPU source 用 clang-cl，CUDA 照舊）。
  - 整機 A/B（C 對 CL，5 輪輪替，10 Hermes×512）：每輪配對 tok/s +3.15%（CI −3.3～+9.6）；block 加權 CPU 22.01→20.00 ms/w、ms/window 39.01→36.99。
  - 逐點配對（n=50）：tok/s +0.62%（CI −3.27～+4.51）、CPU µs/expert −2.11%、tokens/window −3.17%（CI −5.11～−1.22，顯著，原因不明）。
  - 判定：方向正面、未確認；需要 10 輪確認，並查清接受率為何改變。
- 2026-10-31 S4 Phase 1 結果（輸出會改變的路由；exe A1E6 加 env；6 臂×3 輪，10 Hermes×512，原 sampling；s4-route-quality/p1-blocks.json）：每輪配對相對 C：
  - RP05 +21.9%（CI +7.8～+35.9）、RP10 +39.7%（+23.7～+55.6）、RP15 +57.9%（+35.3～+80.5）、RR10 +4.1%、RR20 +1.7%。
  - tok/s：C 約 46、RP15 約 73。CPU ms/w：C 22.27、RP05 14.61、RP10 10.23、RP15 6.19。每層每 window 的 CPU expert 數 6.36→1.49（RP15），GPU-reach 11.7→13.8。
  - Phase 2 品質測試選 RP15、RP10。
- 2026-10-31 ~10:00 依使用者「跑完先暫停」暫停 UNTESTED5：停掉本機 step driver；遠端沒有工作在跑；S4.3～S4.6（Phase 2 品質測試）未開始。API 已重新啟動並驗證：exe A1E6、config 060F、AboveNormal、loaded、3153 slots、arena 20479 MiB；我們建立的一次性排程（S1／S2／S3／S4 的 *-20261031）已全部移除。LLVM 23.1.4 留在遠端；clang build EF8AF397… 與 DIAG build 4C0F2F8C… 留在各自的 runs 目錄。
