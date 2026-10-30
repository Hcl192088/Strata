# Strata 執行期開關盤點（decode 提速，2026-10-29，唯讀研究）

範圍：live 原始碼 `C:\Users\User\native-pipe-generic-20261029`（src／include／docs）上的 STRATA_* 環境變數與 CLI 旗標，只看 decode；prefill、debug／trace／test、多 GPU／layer split、HIP／AMD、圖片／HTTP、以及正在測的 `--spec-split` 都排除。
比對對象：`runs\iq3-campaign-020\server-task020-8080-v0142-s2k-mt1.json`（目前 live 設定，已含 MISS_OVERLAP=1、SPIN_US=2000、IQ3S_MT1=1、NATIVE_PIPE=1、LOOKAHEAD=0、RAM_LRU=1 等）。

## 方法與判定規則
- 原始碼：從 live src 抓出所有「被 getenv 的字串字面值」共 355 個真環境變數名（switches.txt 的 460 個含大量 macro／註解／測試名），再逐一讀 getenv 前後註解取得作用與預設值。另補了 include/（例如 `STRATA_DMA_BATCH` 定義在 include/strata/core/dma_batch.hpp）。
- 「已測」＝該開關出現在我們自己的 run 設定檔（遠端 `Strata-Adrian\runs`、`Strata-Adrian-control\runs` 下的 json／ps1／cmd／bat，約 8004 個檔），或 ledger／LUNA 報告有結果。**排除**路徑含 `upstream`、`bench`、`source`、`src`、`docs`、`tests`、`build`、`patched`、`orig`、`include` 的檔案：第一次掃描時這些把 upstream 社群 bench（AMD 卡）的設定當成我方 run，造成 n=19 的假「已測」，已修正。
- 「未測」的意思是：上述範圍內找不到。沒讀 run 資料夾裡的 .py／.md／.log 原文，所以有少數開關可能只在腳本內以其他形式測過，列在「限制」。

## (a) 未測、與 decode 相關的開關（依本機可能收益排序）

本機瓶頸回顧（來自 ledger）：window ≈ 37.7 ms = CPU experts ≈ 20.8 + GPU-reach wait ≈ 11.7（GPU 側每層 pre：attention + router 約 11.4 ms/window）；swap 拷貝約 1.8 ms/window；SSD join_wait 約 3 ms/window；CPU gate/up 是算力受限（單核約 3.8 GB/s）、down 已是 DRAM 受限（約 44 GB/s）。
「精確」＝不改輸出（位元相同或註解保證同值）；「近似」＝浮點順序或 expert 擺放不同；「改輸出」＝路由／跳過 expert，需品質評估。VRAM 欄：本機只剩約 254 MiB。

| # | 開關 | 作用（一行） | 預設 | 精確？ | 為什麼在本機可能有用 | VRAM | 原始碼 |
|---|---|---|---|---|---|---|---|
| 1 | `STRATA_DF_QB_Q4=1` | verify window 內，Q4_0 KV 也走「整個 window 一次 launch」的 q／norm／RoPE／旋轉路徑 | 關（Q4_0 KV 逐 token 做） | 精確（註解：row-wise 相同算術） | 我們 `--kv q4_0`，而 `qb = dec_batch && n>1 && ... && (!kv_q4 \|\| qb_q4)`，所以現在 T≥2 的 window（平均 T=2.12）在每個 attention 層都在逐 token launch；打開可減少 GPU 側 pre 段的 kernel 數，直接打 11.7 ms 的 GPU-reach wait | 無 | core/verify.cpp:1137-1140 |
| 2 | `STRATA_DF_BRANCH=1` | 混合器側分支放到圖內側 stream（a/b/z、q 與 indexer query 與 K/V 並行） | 關（因 Linux NVML 凍結，註解「Windows 從未見到」） | 精確 | 同樣針對 GPU pre 段的串行 kernel 鏈；Windows 無該風險 | 無（建 event／side stream） | core/verify.cpp:675-685, 800, 1042, 1142 |
| 3 | `STRATA_ROUTE_RESIDENT=<margin>`（+`STRATA_ROUTE_RESIDENT_RANKS=lo-hi`，預設 6-9） | 尾端 rank 的非常駐 expert，在 logit 差不超過 margin 時換成常駐的 | 關（margin=0） | 改輸出 | 10/20 的 ROUTE_PRIOR（全面加 bonus）已證明減 miss 可 +15～60%；這個只動 rank 6-9，扭曲比 PRIOR 小得多，但仍需品質評估。注意與已預設開啟的 TAIL_SKIP=7 會互相影響 | 無 | core/verify.cpp:122-130, 1385；program/generate.cpp:7257 |
| 4 | `STRATA_GDN_SPLIT=1` | GDN step／commit 用 4 blocks/head 切分 | 關（CUDA；AMD gfx1151 表才預設開） | 精確（註解 bitwise） | 註解量到：commit 每 call 快 8-19%，2+ rows window 快 3-13%；我們 T≥2 居多，且每層都有 GDN | 無 | kernels/cuda/verify_kernels.cu:921 |
| 5 | `STRATA_LFUSE=1`（子開關 `LFUSE_GATE`、`LFUSE_PAIR` 在 LFUSE 開時預設開） | shared expert 前後與 KV append 的 launch 融合 | 關 | 精確 | 減 launch；條件 `ar_on && native_moe_combine && dec_batch && n in 2..8 && shared_expert_native_bf16`，`--native` 都滿足；針對 GPU 小 kernel 多的 pre/post | 無 | core/verify.cpp:69, 132-133, 780-783 |
| 6 | `STRATA_QFUSE=1` | 激活的 q8_1 影像由生產者 kernel 直接寫（GDN 輸出 norm 等） | 關 | 精確（同 bytes） | 省掉獨立的量化 kernel；每個 window 每層都有 | 無（小暫存） | core/verify.cpp:139, 994, 1003, 1095, 1333；kernels/cuda/fused_gr.cu:177 |
| 7 | `STRATA_TSUM=1` | 多個 warp sum 改成轉置蝶形（GR、bf16 GEMV、mmvq、IQ expert） | 關 | 精確（註解 bitwise） | GR 讀 T=2,3,4 時註解 1.03/1.03/1.15×；影響面廣但每 call 增益小 | 無 | fused_gr.cu:1607；iq_kernels.cu:3463, 3477；native_bf16.cu:236；native_mmvq.cu:1158 |
| 8 | `STRATA_MMVF_ROWS=1` | bf16 multi-row GEMV，每 block 4 rows（2..8 tokens） | 關 | 精確（註解同條件同 bits） | 我們的 window 是 2-3 tokens；bf16 dense（router／indexer／shared gate）每層都在用 | 無 | kernels/cuda/native_bf16.cu:272, 302 |
| 9 | `STRATA_ATTN_LANECELL=1` | decode 注意力分數階段每 thread 一個 cell，免 shuffle 歸約 | 關 | 精確（註解 bit-identical） | attention 層的 GPU 時間；Q4_0 KV 路徑是否走此 kernel 要實測確認 | 無 | kernels/cuda/qsa_decode_attn.cu:638-640 |
| 10 | `STRATA_DMA_BATCH=1`（或 2） | adaptive tier 的 swap 拷貝／PCIe expert 上傳改 `cudaMemcpyBatchAsync`，WDDM 下一批只觸發一次中斷 | 0（逐個 cudaMemcpyAsync） | 精確（只搬 bytes） | 針對 nsys 量到的 swap 拷貝約 1.8 ms/window＋launch；CUDA 13.2 滿足需求。**風險**：註解寫「pinned expert uploads」，我們的 RAM 層是 VirtualLock 不是 CUDA 註冊，host alias 查不到時會退回逐個拷貝（等於 no-op，不會壞） | 無 | include/strata/core/dma_batch.hpp:30-35；program/generate.cpp:8215, 12609；core/verify.cpp:2243 |
| 11 | `STRATA_ROUTE_TAIL_SKIP=6`（或 5） | 把「整個 window 都排在 rank≥N 的 miss expert」跳過的門檻從 7 往下調 | CUDA 預設 7；我們只測過 0 與 7 | 改輸出（KL 約 0.003-0.006 是 7 的數字，更低 rank 會更大） | 少讀少算 miss；但 10/20 GATE_SKIP 顯示小幅放寬不夠、要到輸出明顯改變才有效，期望低 | 無 | program/generate.cpp:8068-8086；core/expert_source.cpp:3633-3645 |
| 12 | `STRATA_IO_THREADS=8`（或 16） | Windows DirectFile 發 overlapped 讀取的執行緒數，預設 4（= 佇列深度） | 4 | 精確（讀同樣 bytes） | SSD miss 讀取是 join_wait 約 3 ms/window 的來源；ledger 說「read_direct 已 overlapped、合併 32 MiB」但從未動過這個佇列深度。若 NVMe 在 QD4 吃不滿就有空間；也可能已飽和 | 無 | platform/direct_file.cpp:63-66, 187 |
| 13 | `--pool-affinity auto`（或 `p-cores`） | worker 放置：P-core 優先 → 其 SMT 兄弟 → E-core（目前 `all`＝每實體核一條） | all | 精確（只移 thread） | 10/18 有排 A9/A11/A13/A15 但被使用者遊戲中斷、之後未重跑；12600KF 的 LP 0-11 是 P-core 含 HT，E-core 12-15 較慢（單核 1.7-2.0 vs P 3.7 GB/s）。gate/up 算力受限，P-core 的 SMT 兄弟可能比 E-core 有用；但 6 條 P-core thread 已把 DRAM 吃滿 | 無 | program/generate.cpp:1868-1877 |
| 14 | `STRATA_ADAPT_LAG=2` | window 吃「兩個 window 前」的 swap，下一 window 不必等拷貝 | 1 | 近似（expert 擺放時間點不同，捨入不同） | 打 swap 拷貝等待 1.8 ms；與已測的 `--adapt-async 1`（+3.7% 後 +1.3%，結案）同家族，期望低 | 無 | program/generate.cpp:1314-1324 |
| 15 | `STRATA_EXPERT_V2=1`（可再加 `STRATA_TSUM=1`） | VRAM 常駐 expert 的 grouped decode kernel v2 | 關 | 精確（註解 bitwise） | **只適用** gate=IQ3_S(21) + down=IQ4_NL(20)、n_embd 2560、n_ff 640 的層（本 pack 13 層 IQ3_S）；只影響 GPU 命中的 expert，CPU 路徑不變，所以收益有限 | 無 | kernels/cuda/iq_kernels.cu:3460-3472 |
| 16 | `STRATA_IQ_PREFETCH=<bytes>`（0／4096／8192） | CPU IQ kernel 的軟體預取距離 | 2048 | 精確 | down phase 已 DRAM 受限（約 44 GB/s），預取距離可能還有微調空間；gate/up 算力受限，預期無感 | 無 | kernels/cpu/iq_avx2.cpp:183-188；iq_avx1.cpp:136 |
| 17 | `--mtp-q4 all`（或 `proj`／`head`） | draft layer 的 Q8_0 投影與 draft head 改用 Q4_0 副本（每步少讀 bytes） | 關 | 輸出精確（verify 照主模型；但 draft 品質可能變→接受率變） | 縮短 drafter 時間；dense.bin 110.7 MB，Q4 副本約再 +55-60 MB VRAM，落在 254 MiB 內，但會吃掉約 30 個 expert slot，破壞「容量 3153」嚴格閘門，要先決定是否放寬 | 約 +55-60 MiB | core/mtp.cpp:183-239；program/generate.cpp:2005 |
| 18 | `STRATA_FUSE_HEAD_GR=1` | 最後一層 combine 與 head 的 hyper-connection 讀融合（verify 與 MTP drafter 都有） | 關 | 精確（註解同 bits，未逐一核） | 每 window 一次的小節省 | 無 | core/verify.cpp:1469-1473；core/mtp.cpp:854 |
| 19 | `STRATA_DF_PLE=1` | window 的 PLE post-projection 步驟一次做完 | 關 | 精確（註解 bitwise per-token 迴圈） | 每 window 一次的小節省 | 無 | core/verify.cpp:935 |
| 20 | `STRATA_ADAPT_NOWAIT=1` | verify window 不等 adaptive tier 拷貝落地（0.1.37 行為，#463 的 A/B） | 關 | 近似（未完成的 swap 當不存在，擺放不同） | 同 ADAPT_LAG，期望低 | 無 | program/generate.cpp:1308-1312 |
| 21 | `STRATA_GR_DOWN_MAX4=1` | GR down 每個 block 4 組 | 關 | 精確 | 註解自己寫「RTX 5070 的 10 對交錯 A/B 沒看到 bench 的 +2.8-3.5%」→ 預期無 | 無 | kernels/cuda/fused_gr.cu:861 |
| 22 | `STRATA_ROPE_TABLE=1` | RoPE 角度改查表 | 關 | 改輸出（最後幾個 bit） | 單一小 kernel，收益微 | 無 | kernels/cuda/native_rope.cu:154 |

排序依據：1-2、4-9 是「GPU 側精確開關」，全部在 CUDA 預設關（AMD gfx1151 的預設表才開，見 core/arch_defaults.cpp:34-57，該表註明「CUDA 建置不會查它」），所以我們從未吃到；它們各自在 gfx1151／5070 的 harness 上量過，**在 RTX 4070 + Windows WDDM 上沒有數字**，每個預期只有 0.1-1 ms/window（約 0.3-3%），但全部精確、零 VRAM、改環境變數就能 A/B，可疊成一組做一次「GPU 精確組合」測試（建議 #1+#2+#4+#5+#6+#7+#8+#9）。3、11 是最大潛力但會改輸出。

## (b) 已測的 decode 相關開關

| 開關／旗標 | 值 | 出處（run 資料夾／日期） | 結果 |
|---|---|---|---|
| `STRATA_MISS_OVERLAP=1` | 1 | ledger 10/27 21:00；`miss-overlap-20261027`、`next4-20261028`、`s2k-confirm-20261028` | M vs D0 +2.05%（CI 跨 0）→ 當時不採用；搭配 SPIN 後見下列 |
| `STRATA_MISS_OVERLAP_SPIN_US` | 100000／2000／500 | ledger 10/27 22:xx、10/28 02:30、10/28 上午 | S2K≈S500 平台；8 輪 ABBA +8.49%（CI +5.9～+11.1）；已部署（S2K 為現行 best） |
| `STRATA_IQ3S_MT1=1` | 1 | ledger 10/28 21:xx；`iq3s-mt1-ab-20261028`、`mt1-deploy-20261028` | +4.26%（CI +2.15～+6.37），CPU 段 −2.19 ms；已部署 |
| `STRATA_IQ_MT_MIN` | 1（nt=1 走 iq256） | 10/08（ledger 引述）、`iq3s-mt1-ab` 以 null 清除 | 約 −6%（n=3，對照散佈 ±10%，證據弱）；改用 MT1 只動 IQ3_S |
| `STRATA_NATIVE_PIPE=1`（+`_CHECK`） | 1 | ledger 10/29；`native-pipe-deploy-*`、`native-pipeline-*` | 已部署為 live |
| `STRATA_PARTIAL_PIN`／`_GIB` | 1／6,8,16 | ledger 10/28 NEXT4、PINAA；`next4-20261028`、`pinaa-20261028`、`pcie-balance-20261029` | PIN8 先 +6.9% 後 −0.5%～+2.4%（CI 跨 0）→ 結案；PA 組合不穩 |
| `--adapt-async 1` | 1 | `next4-20261028`、`pinaa-20261028`、`calib-adapt-async-027-20261018` | +3.69% → +1.28%，CI 跨 0 → 結案 |
| `--adapt-every/--adapt-swaps/--adapt-decay` | 3／16／0.60（2 也試過） | `adapt-every-20261014`、多數 campaign | live 值；every 3 vs 2 已比 |
| `STRATA_RAM_LRU=1`（+`_CHECK`） | 1／0 | `ram-lru-20261013` 起，65 個 run | 已部署為預設 |
| `STRATA_ROUTE_TAIL_SKIP` | 0／7 | 多數 run（58 筆） | 7 為 CUDA 預設；其他 rank 值未測（見 #11） |
| `STRATA_ROUTE_PRIOR` | 0.25／0.5／1.0 | `replay-A/C-20261020`；ledger 10/20 | +15.7／+30.7／+59.6%，輸出改變，0.25 看似中性（小樣本） |
| GATE_SKIP、ROUTE_BIAS（候選 source，非現成環境變數） | tau .01～.10 | ledger 10/20 | tau≥0.075 才有效且輸出明顯變 |
| `STRATA_LOOKAHEAD`／`_K`、`STRATA_FS_*`、`STRATA_VERIFY_DEVICE_PLAN` | 0／10；各種 | `vram-prefetch-20261013`、`pap-live-20261015` | live 設 LOOKAHEAD=0；FS／lookahead 家族早期已掃 |
| `STRATA_FETCH_PVM`、`STRATA_FETCH_ADMIT` | 0 | `iq3-hotpath-optimization-007`、live 設定 | live 值 |
| `STRATA_RESIDENT_HEADROOM_GIB` | 0.25／3 | 多數 run | live 0.25 |
| `STRATA_PCIE_FRAC_DEFAULT=old`／`--pcie-frac` | old／N | `gpu-profile-20261015`、`pcie-pinned-ab-20261018`、`calib-adapt-async-027` | 掃描全在雜訊內 |
| `STRATA_MTP_TOP2`、`STRATA_MTP_FULL_HEAD` | 1 | `mtp-options-20261014` | 41 次前綴拒絕中 0 次救回；無益 |
| `STRATA_MTP_CATCHUP_ALL` | 0／1 | `mtp-api-settings-20261014` 等 13 個 run | 已比 |
| `--lookup-chain 3` | 3 | `mtp-options-20261014` | +1.59%，無穩定增益，不部署 |
| coupled draft（`--coupled-draft`／`STRATA_SPEC_COUPLED`） | 開（temperature 1.0） | `mtp-coupled-sampled-20261014` | −4.04%；greedy 下不啟用 |
| `--mtp-max-t` | 3 vs 4 | `mtp-depth-20261014` | 4 比 3 慢 6.04%（3 對全負） |
| `--mtp-hnorm` | pooled／stream | `mtp-hnorm-20261014`；live 用 stream | 已比 |
| `STRATA_SPEC_DEPTH=1` | 1 | `mtp-depth-20261014` | 只輸出計數，無速度效果 |
| `--pool-workers` | 9（掃描） | 85 個 run；ledger/calibrate | 9 最佳 |
| `--pool-tasks` | 192 | `iq3-cpu-campaign-015` | 早期單點；GU_TASKS 30／60（patched 非現成開關）10/15 拒絕（無 +3%） |
| `--pool-affinity` | all（auto/p-cores 只在 10/18 腳本裡，未跑完） | 85 個 run | 只有 all 有資料 |
| `--kv`／`--kv-resident` | int8／q4_0；32768／20480 | `iq3-campaign-014` 起 | live q4_0／20480 |
| `STRATA_VERIFY_PROFILE=1`、`STRATA_DECODE_TIMING=1` | 1 | `gpu-profile-20261015`；多數 | 診斷用 |
| `STRATA_HC_SPLIT=1` | 1 | `next-steps-ab-20261018-2132` 腳本出現 | 該 run 被使用者中止，結果未見；視為未驗證 |
| `STRATA_TIMER_RES`（patched 非現成開關） | 1／2 | ledger 10/28 04:10 | −1.5%／−2.6%，CI 跨 0 → 無效 |

## 預設已開（不必測，除非要反向 A/B）
`STRATA_SH_STREAM`（CUDA 預設開）、`STRATA_SH_FORK_LATE`、`STRATA_ONE_TOKEN_COMMIT`、`STRATA_MULTI_BLOCK_ARGMAX`、`STRATA_HEAD_MIX_MULTI`、`STRATA_MTP_SHARED_BRANCH`、`STRATA_DEC_BATCH`、`STRATA_GDN_COMMIT_SPLIT`、`STRATA_PLE_BATCH`、`STRATA_S2_SWIGLU_Q8`、`STRATA_FUSED_SWIGLU_Q81`、`STRATA_MMVQ_IL`、`STRATA_QSA_EARLY_EXIT`、`STRATA_SCORES_MULTI`、norm-rope（`STRATA_NO_NORM_ROPE` 關掉它）、`MMVQ_ROWS2`（`STRATA_NO_MMVQ_ROWS2` 關掉它）、`STRATA_NO_MULTI_GR`／`STRATA_NO_BATCH_KV_STEP`（反向開關）、`STRATA_MTP_PRIORITY`、`STRATA_ARENA_LOCK`、`STRATA_SSD_KEEPALIVE`（100 ms）、`STRATA_IQ_PREFETCH`（2048）、`STRATA_FILL_AHEAD`（256）、`STRATA_READ_AHEAD`、`STRATA_TG_FLUSH_US`（2000，註解「只用來發現故障」）。

## 本機不可行或不適用（直接排除）
- `STRATA_Q8_PACKED=1`、`STRATA_Q6_PACKED=1`：另存一份打包後的 Q8_0／Q6_K 權重在 VRAM（native_dense.cpp:302 起「a second, packed copy」），本機只剩約 254 MiB，會吃 expert slot。
- `STRATA_DF_PDL`、`STRATA_QSA_CLUSTER`、`STRATA_ARGMAX_MULTI`：需 sm_90+，RTX 4070 是 sm_89。
- `STRATA_CPU_YMM`／AVX-512 相關（`FORCE_AVX2`、`IQ_GATHER` zmm 路徑）：i5-12600KF 沒有 AVX-512。
- `--host-core last`／`STRATA_HOST_CORE`：說明寫「Not on hybrid CPUs」。`--aux-cpus`／`STRATA_AUX_CPUS`：docs 稱 Linux 才完整（/proc sweep），Windows 只有 `STRATA_ADAPT_JOB_CPU` 預設用 SMT 兄弟；12600KF 的 10 實體核已被 9 worker＋host 佔滿，無空閒可分。
- `STRATA_REMOTE_*`、`PEER_*`、`--layer-split`、`--pipeline-windows`、`--expert-cache-device*`：單 GPU。
- `STRATA_KV_ROT`：只對 int8 KV（q4_0 本來就旋轉）。
- `STRATA_NO_LARGEPAGES`：方向相反（預設會嘗試 large pages，非特權帳號被拒，現況是 4 KB 頁）。要讓 large pages 生效需 SeLockMemoryPrivilege＝改系統安全設定，不在此研究的權限內；僅在此註記「CPU 讀頻寬可能受 4 KB 頁影響」（iq_avx512.cpp 註解提到 DDR5 4 KB 頁），沒有本機證據。

## (c) 無法分類
- `STRATA_POOL_SPIN_US`（pool.cpp:441，「a test knob」）：worker 在無工作時 `_mm_pause` 自旋的上限，預設 20 ms；每層間隔遠短於此，worker 實際一直在自旋，縮短只會讓 worker 睡去。與 MISS_OVERLAP_SPIN（helper 的自旋）是兩個獨立旋鈕，且 TIMER_RES 已證明喚醒量化不是瓶頸，列為低優先、未歸入 (a)。
- `STRATA_SPEC_PROB`／`_DT`／`_GATE`、`STRATA_SPEC_MIN_TEMP`、`--coupled-draft`：只在取樣（temperature>0）時生效，Hermes 是否取樣未確認；greedy 下無作用。
- `STRATA_IQ256_GATHER=0/1`：全域強制，但實測 gather 對 IQ3_S 是 1.78× 而對 IQ2_S 反而 0.90×，沒有 per-type 開關；預設 auto 已是 per-thread（P-core 開、E-core 關）。全域改值必有人輸，歸為不可獨立測。
- `STRATA_EXCHANGE_ROTATE`：與 RAM LRU 互斥（程式直接回錯）。
- `STRATA_FETCH_THREADS`、`STRATA_STARTUP_UNBUFFERED`、`STRATA_DEFERRED_REGISTER`、`--no-ple-prefetch`、`--ple-*`：看起來只影響啟動／PLE 讀取，decode 路徑關係未逐一證實。
- `--short-read`、`--mtp-window`、`--expert-cache-per-layer`、`--resident-cpu-experts`、`--no-hit-poke`、`--shared-late`、`--no-token-graph`、`--no-fused-gr`、`--no-capture`：多為 A/B 對照臂或模式選擇（預設即較佳或功能不同），未歸入加速候選；`--expert-cache-per-layer` 說明提到會改 slot 分配（與 3153 容量閘門／profile 預載互動未研究）。
- `--mtp-draft-vocab`：live 的 `mtp\rt\draft_vocab.bin`（0.4 MB）存在，預設路徑已在用，沒有「更小子集」可試的現成檔案。

## 限制（沒檢查的）
- 沒讀 run 資料夾內的 .py／.md／.log 原文，也沒逐份讀 LUNA／ledger 所有結果；「未測」是依 run 設定檔 json／ps1／cmd／bat 與我手動 grep ledger 判定，可能漏掉只在腳本或口頭測過的。
- 沒編譯、沒跑任何測試；所有「精確」都是引用原始碼註解的聲明（多數寫 bitwise／bit-identical），沒有自己驗證。S25／S26 那批 GPU 開關的增益數字都來自 AMD gfx1151／RTX 5070 harness，4070／WDDM 上未知。
- 沒確認各開關在 `STRATA_NATIVE_PIPE=1` 的新 pipeline 路徑下是否仍走同一個程式碼分支（native-pipe-generic 是本次 live source，分支選擇條件我只讀 verify.cpp 一部分）。
- docs/DETAILS.md 只搜了幾個關鍵字，沒有全讀。
- 沒查本機 NVMe 型號與佇列深度行為（#12 IO_THREADS 的效益取決於此）。
