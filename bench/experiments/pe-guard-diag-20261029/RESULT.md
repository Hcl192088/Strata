[LUNA_REPORT]
TASK_ID: LUNA-20261012-027
STATUS: REPORT_LOCAL / PE_GUARD_DIAG
TASK_SOURCE: 2026-10-29 使用者直接授權的 read-only + tiny probe continuation
TASK_BRANCH: 無新 claim；未讀寫 GitHub
TASK_COMMIT_SHA: 夜間保存來源 main 2f1e99872969c9b4586a2d41c7f1915f27e4f298
BENCHMARK_RAW_PATH: NONE（未獲准 benchmark；以下是獨立 placement probe）

# 結論

**ROOT_CAUSE_FOUND：新增 guard 的契約錯誤。** Host 使用 soft CPU Sets，guard 卻將瞬時 LP 必須等於單一 home LP 當成必要條件。相同 host API、相同 LP0／CPU Set ID256 的獨立 probe，選取成功且讀回正確，仍有 3465/10000（34.65%）取樣在集合外；硬 affinity 對照 0/10000。未發現 CPU Set ID 與 LP 混用。

**LIKELY：夜間 CHK 的 actual=1 是 soft placement 下的遷移／排程結果。** LP1 與 LP0 在目前查到的映射均為 CoreIndex0、EfficiencyClass1；此差異本身不是 P→E 身分錯誤。夜間沒有記錄 guard TID、當下 selected IDs、hard affinity 或 CPU Set flags，故不能證明當時一定是 scheduler override，亦不能完全排除 pin 呼叫失敗或其他程式庫改動 thread placement。不能把 probe 的 34.65% 當成 Strata 的遷移率。

# 執行邊界與 identity

已用既有 SSH host key（StrictHostKeyChecking=yes）連至 DESKTOP-LKMLUPC，讀 canonical 與 generic worktree 的 AGENTS.md。canonical HEAD 為上述 2f1e998；保留既有 dirty tools/run_mtp_depth_20261014.py、tools/run_task027_ram_lru.py 及未追蹤項，未修改遠端 source/git/config。generic worktree HEAD f520bc5e9d31c93caeb296b059e3a3eaa16e493f，git status --short 無輸出。

本次 live 已是 PID31512、native-pipe-deploy-prep-20261029/build/strata.exe，實測 SHA256 A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8；不能引用凌晨舊 live identity。ledger 末尾也記錄此候選已部署。本次不進行 Strata binary 比較、build 或 benchmark；無須以舊 best 啟動測試。

夜間 role binary 重新計算 SHA256 符合 165059E7A5F528B80D5B029C487741AD652E0F0C38F4B6E112F99F4AAC61A110。build_roles.py 證明實際編譯來源為 canonical runs/overnight-20261029/source，並非現在的 generic worktree。該 source 的 pool.cpp SHA256 9E0F3DD328C2B652E57523BB4E7297641698B95CC57D60FDA4F592C428A9FF07 與 roles patched/identity.json 相符。以下以此夜間 source 為 S，generic worktree 為 G，roles run root 為 R。

- S = C:\Users\User\Strata-Adrian-control\runs\overnight-20261029\source
- G = C:\Users\User\native-pipe-generic-20261029
- R = C:\Users\User\Strata-Adrian-control\runs\native-pipeline-roles-20261029

# Q1：placement 與映射

|位置（遠端檔案:行）|實際行為|
|---|---|
|S/src/core/session.cpp:549–552、556–557|planned_host_core → pin_current_thread，作用於呼叫 thread，保存 previous selection 與 valid|
|S/src/kernels/cpu/pool.cpp:372–383|GetThreadSelectedCpuSets → cpu_set_for_core → SetThreadSelectedCpuSets(GetCurrentThread(), &target, 1)，沒有 host hard mask|
|S/src/kernels/cpu/pool.cpp:398–406|恢復先前 selected IDs；空 selection 回到 process default/all-group eligibility|
|S/src/kernels/cpu/pool.cpp:357–360、469–475|每個新 worker 在自身 lambda 內 pin_this_thread，接著 worker(i)|
|S/src/kernels/cpu/pool_affinity_win.hpp:17–25|worker SetThreadGroupAffinity，Group=core/64、Mask=1<<(core&63)，硬限制|
|S/src/kernels/cpu/pool_affinity_win.hpp:28–36|GetThreadSelectedCpuSets 讀取先前 selection|
|S/src/kernels/cpu/pool_affinity_win.hpp:40–57|GetSystemCpuSetInformation，逐項依 Size 前進，以 Group 與 LogicalProcessorIndex 查到 CpuSet.Id；排除分配給其他 process 的 set|
|S/src/kernels/cpu/iq_avx2_parity.cpp:203|獨立 parity 測試使用 SetThreadAffinityMask，不是 host pipeline 路徑|
|S/src/kernels/cpu/pool_affinity_test.cpp:17|affinity 測試 helper 使用 SetThreadSelectedCpuSets，不是 live host 路徑|

G 中對應 host set／restore 為 pool.cpp:370／395，worker group affinity header 相同。S 與 G 的 pool_affinity_win.hpp SHA256 均 E179C53F0B02DDF250AE8244275D62DB20EFA5E1AC76A6D2DBD392BEE09C8CD8，故映射實作可直接核對。S pool.cpp 的拓樸區較 G 多 8 行；G pool.cpp:97–103 由 RelationProcessorCore 的 EfficiencyClass、group mask 建立 group*64+LP，135–145 依 performance class 排序、保留第一個實體 core 的 primary LP 給 host。這裡的 core 變數實際編碼為 LP，不是 opaque set ID。

實測 CPU Set ID256–271 對應 group0 的 LP0–15；LP0 的 set 是256而不是0。LP0/1 的 CoreIndex 都0、EfficiencyClass 都1；LP0–11 class1、LP12–15 class0。完整表含 flags 存 probe-result.json。guard 在 S/pool.cpp:806–814 將 PROCESSOR_NUMBER 編碼成 group*64+LP，與相同編碼的 topo_.host_core/worker_cores 比較，**沒有拿 CpuSet.Id 比較 LP**。

指定 API 搜尋在 S 的全部 src/include 文字檔與 G 的 src/include 均未找到 SetThreadIdealProcessor（含 Ex）呼叫；G 額外全樹限定 C/C++/Python 文字檔搜尋發現 bench/results/2026-10-03-windows-groups/windows_processor_groups_affinity_probe.py 的歷史測試 hard affinity 呼叫（129、135、150、152行），非 engine 路徑。Windows aux_cpus 是 no-op：S/include/strata/platform/aux_cpus.hpp:352–357，夜間 log 也列 not available，沒有另一個 Windows auxiliary placement API。

# Q2：soft 語意、thread 與時序

Microsoft 文件將 CPU Sets 定義為 soft affinity；set ID 與 home processor 是映射關係，hard mask 優先於衝突的 CPU Set assignment。parked／exclusive allocation 等狀態可讓執行離開 home LP。因此成功選取並不等於每次 GetCurrentProcessorNumberEx 都必須回 home LP。[CPU Sets](https://learn.microsoft.com/en-us/windows/win32/procthread/cpu-sets)、[SYSTEM_CPU_SET_INFORMATION](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-system_cpu_set_information)。本機 probe 也實際觀察到集合外執行。

host 沒有被此路徑硬限制。header:15–16 明確說明刻意只對 pool-owned worker 用 hard affinity，因 caller 的 implicit all-group affinity 不能靠 PreviousGroupAffinity 完整恢復；host 因而用 CPU Sets。直接改成 hard affinity 會更改既有語意與復原契約。

靜態呼叫鏈：S/src/program/generate.cpp:1686 是 main；5964–5974 建立並 init loop_scratch；S/src/core/session.cpp:551 在該 caller 上選取 CPU Set。S/src/kernels/cpu/pool.cpp:896 run_phase(7,threads) → 702–707 run_phase 在 caller 同步 drain(-1,...)；guard 位於 drain_native_pipe:798–814、每次進入該 drain 先取瞬時 LP。worker 則在自己的 thread 先 hard pin 再進 worker loop。S/generate.cpp:8651 開的 thread 是讀 stdin 的 input reader（8653起），不是執行 host pipeline 的 thread；沒有看到把 pipeline host 工作派到該 input reader 的程式碼。

已驗證的靜態設計是「setup caller pin → 同一主控制路徑處理 request/pool host drain」，不是在 worker constructor 錯 pin constructor thread。init 在 request pipeline 之前；free 在 session teardown 才恢復（session.cpp:564–570）。但夜間未留下 runtime TID 與 CPU Set readback，故不宣稱已動態證明當晚 placement 的 thread identity／成功狀態。新 guard 也沒有查 pinned.valid 或 selected IDs，而是直接檢查瞬時 LP。

# Q3：SMOKE 通過、CHK 首請求失敗

R/harness/replay_ab_20261027.py:1–4、163、194、213–224 明定每 block 新 serve.server + engine、核對 binary 及 priority。R/controller_roles.py:49–52 顯示 SMOKE/CHK 都開 ROLES、PIPE、CHECK、DIAG；144–145 依序 SMOKE 三題 p01/p05/p08、CHK 全題，均 max tokens128。不是 SMOKE 未開 guard。

R/out/block-00-SMOKE-r0/meta.json：engine PID22964，rows3，status OK；engine.log:1 開始於05:53:20，62行 roles active，64行 host id=-1 cpu=0。R/out/block-01-CHK-r0/meta.json：新 engine PID5376；engine.log:1 開始於05:55:01，62行 roles active，63行立即 fatal actual1 expected0。兩者 binary SHA 完全相同，workers 均 2,4,6,8,10,12,13,14,15，host0。CHK 尚未完成第一請求即 abort，後續 harness priority/ownership changed 是 engine 已死後的次生錯誤（harness:245），不是起因。

推論：新 engine 的排程／power 狀態與時間不同，soft affinity 並未承諾固定 LP，所以 SMOKE 成功不保證下個 engine 通過相同瞬時 guard。現存證據不支持「角色策略計算錯誤」或「CHK 特有的不同 host thread」結論；精確是哪次 scheduler 事件導致當晚 LP1 無法事後還原。

# Q4：tiny probe

遠端新建 C:\Users\User\Strata-Adrian-control\runs\pe-guard-probe-20261029，保留 probe.py、probe-result.json、process-gate.json；本機同名 report 目錄保存腳本、JSON 與 probe-console.txt。使用既有 Python312 stdlib/ctypes，未安裝套件。只對 probe 自身 current thread 設 placement。

執行前重查 process，准入清單逐一對應：API launcher 的 memory-policy run chain PID29880→3616，server chain10500→28628→strata31512；watch13944→32280。無另一個 Strata/Luna/benchmark/build/診斷工具程序命中，未停止任何程序。probe PID32616，SetPriorityClass BelowNormal 成功且 readback16384。初始 group0 mask65535，selected IDs 空。

精確模擬 host：GetSystemCpuSetInformation 查 group0 LP0 的可用 Id256 → GetThreadSelectedCpuSets 保存 → SetThreadSelectedCpuSets(current,[256],1) → readback[256]。每段100批、每批100次輕量取樣，批間 sleep 至20ms節奏，非持續滿載。soft 後先恢復空 CPU Set selection，再 SetThreadGroupAffinity(group0,mask1) 作對照，結束隨 probe process 退出。

|模式|取樣|集合外|比例|LP histogram|wall秒|process CPU秒|
|---|---:|---:|---:|---|---:|---:|
|CPU Set soft|10000|3465|34.65%|LP0=6535、LP11=3400、LP2=65|2.000381699996069|0.015625|
|group hard affinity|10000|0|0%|LP0=10000|2.00060080003459|0.0|

CPU 時間0.0是 Windows process_time 計時粒度下的讀值，不表示沒有耗用 CPU。soft 最初10個樣本都 LP0，後來仍離開，故不能只用 placement 後立即一個樣本作長期 pin 證明。此 probe 的集合外樣本全部仍為 P class；沒有觀察到 E class，也不能推出永遠不會到 E。這是樣本比例，不是時間比例；兩段先後執行、非統計 A/B，沒有重現 Strata GPU 等待／負載／AboveNormal 等完整環境。selection 只於 soft 取樣前讀回，未於每筆樣本重新讀回。沒有 ETW/power transition 記錄，不能定位 scheduler 內部原因。

probe 後 PID31512 未變，/health 回 status ok、loaded true、max_context100000。沒有生成請求、停止 API 或修改 API priority/config/env/temperature。

# Q5：建議最小 guard 與後續驗收（僅描述，未改碼）

建議**保留 host CPU Set 語意**，不要改成 hard affinity，也不要把瞬時 LP 改成「必須落在 singleton selected set」：後者仍等價於原本錯誤的 LP equality。

最小變更範圍是 role guard 及其一次性初始化證據：

1. 在實際 host setup caller 成功選取後，保存 expected set ID、caller TID、mapped Group/LP/CoreIndex/EfficiencyClass；確認 selected IDs 讀回符合規劃。pin失敗或查表失敗明確回報／拒絕 roles，不能忽略。guard 的 host 分支核對自身 TID 與 selection 配置，證明呼叫範圍正確。
2. host 瞬時 GetCurrentProcessorNumberEx 查表，檢查實際 EfficiencyClass 是否符合 P 身分（此 host 為最大 class1），不再要求特定 LP0；LP1 是同一 P core 的 sibling，LP11/2 也都是 P，不能報「P/E 錯誤」。記錄 configured placement 與 observed identity，避免把選取成功稱為硬 pin。
3. worker 保留 hard affinity 的精確 group/LP 檢查，並核對 mapped efficiency 與預期角色；既有 worker pin 呼叫結果目前未強制中止，guard不可因此省略。host roles 遇到不符合 P class 的樣本，明確 role-class violation；不得靜默接受、fallback 或自動改 affinity。

這只能證明配置及**取樣當下**的 P/E 身分，無法在 soft 語意下證明整段 tile 永不遷移。guard 通過後仍可能遷移；若設計要求整段工作必須在特定 P core，必須另行授權修改 placement／restore 契約，再選 hard group affinity。現有 header 明示 caller restoration 理由，故本次首選保留語意、承認證明範圍。是否把 P/E violation 作 abort 或單純診斷，應由 planner 先固定驗收契約；本建議保留 strict role-class violation，不偷偷放行 E。

後續需在新 root、固定修正來源 commit/tag/build SHA、核對 current-best identity 與 fresh process gate 後，重新做 SMOKE三題及完整CHK十題128：獨立 reference逐位元相等、十種實際 GU/down format pair全覆蓋、completion accounting、每個worker與host的TID/selection/observed class證據、跨多個新engine首次請求均正確。未通過不得正式測速。

之後才依原設計跑 C/G/R 五輪、每block十題512、新engine、AboveNormal、同容量3153 slots/20GiB/20479MiB及相同模型/prompts/args/env，僅以預定義臂開關區分 C=既有MT1、G=generic PIPE、R=PIPE+ROLES。primary比較 R/G，並報G/C與R/C、pooled及按輪差／信賴區間，沿用原事前採用gate，不事後調門檻。CHECK/DIAG不得混入正式速度臂；目前live已為generic新binary，屆時須重新明確固定各臂binary及current-best，不能把舊C當今日live。此處全是後續需求，本次未執行。

# Coverage、限制與操作失敗

要求範圍為 placement、guard、SMOKE/CHK差異與小probe。已完整搜尋 S/src、S/include 及 G/src、G/include 內指定 API 文字；另搜尋 G 全樹的 C/C++/Python 文字檔（排除.git與build目錄）以識別歷史測試。完整讀 placement header、指定placement／guard／run_phase／thread建立範圍、build_roles.py、兩block meta/startup，並抽取controller/harness必要呼叫行；未逐字audit整個引擎、第三方DLL或GPU code。

engine.log 以 placement/ROLES/WORKER/FATAL等pattern抽取並限制顯示前20個命中，未宣稱完整log內容審閱；private prompt/response未讀，無需上傳。大型binary只做SHA256，不解析PE；沒有trace/ETW或當晚runtime TID，故歷史精確遷移因果仍有限。本文不宣稱完整全repo audit。

第一次遠端 rg 搜尋失敗（rg未安裝），後續以PowerShell逐檔Select-String取得證據；這是搜尋工具替代，沒有替代任何Strata執行流程或修補最終輸出。最初本機工具封裝btoa不存在，在送出SSH前即失敗；後續採使用者指定的PowerShell EncodedCommand。無build、benchmark、API stop、source/git/config修改、GitHub或push。本機 D:\strata 沒有.git，未建立repo；本次明確禁止GitHub優先於一般自動push指示。遠端僅新增指定probe資料夾。
