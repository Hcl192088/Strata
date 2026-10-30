# 未測單開開關短篩：2026-10-30

TASK_ID：LUNA-20261012-027 continuation。授權：本輪使用者要求完整 +10% 計畫並測其他未測候選。這是完整計畫內的有限初篩，不是正式效能／品質驗收，不部署。

固定順序：C → EXPERT_V2 → DF_PLE → FUSE_HEAD_GR → GR_DOWN_MAX4 → DF_QB_Q4 → DF_BRANCH → MMVF_ROWS → ATTN_LANECELL → C2。每個候選只加對應 `STRATA_*=1`，其餘完全沿用原設定。十臂各 fresh server/engine，原 p01/p05/p08 ×128，一輪，共30 requests；不加輪、不合併flags。

不測：GDN_SPLIT/TSUM數值尚未解、QFUSE broken、LFUSE六輪負面；DMA_BATCH原source有未准fallback，本輪不啟用；IO_THREADS/PREFETCH另由parent做isolated screen。EXPERT_V2型別pair適用性由parent實際source/pack核對，不將13個IQ3_S層全當適用。

假設：各單一旗標可能縮短對應CUDA資料處理，且不出現超出A/A基準的早期分歧或重複破碎。需要實測機制才可升格；環境送達不能證明對應kernel觸發。controller記 `kernel_branch_activation=NOT_MEASURED_NO_DEDICATED_COUNTER`，不冒稱命中。

Identity：fresh核對 current-best A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8、config060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93與遠端BEST；3153slots/20479MiB、20.00GiB、9workers/all、AboveNormal、MT1/PIPE=1、MT_MIN absent。parent已核對本輪啟動PID7888；controller不鎖死PID，而是每次按實際exe/parent/env核對。候選每次completion之前再核對owned engine binary/priority/capacity與完整config env、新舊flags只有預定一個。

Sampling：staging的base.py必須是已修正LFUSE版本，`rp.make_body is base.make_body`。prepare先實讀原capture與比較除max_tokens外全部欄位一致，assert temperature1.0/top_p.95/top_k20/min_p0/seeds1001/1005/1008；只把max_tokens設128，不能用harness原greedy建構。記sampling與request/harness/base/controller hashes，不輸出私人prompt或回應原文。

Process與復原：沿用既有harness processgate/API ownership與stop/restore；補實際R4 benchmark、link/nmake/nsys/wpr名稱檢查，防止同時量測污染。每臂前gate、每request前既有foreign processgate。啟動前API須idle/queued0。只停止已核對API與本controller自己fresh engine，finally用原既有排程還原；parent之後做獨立fresh核對。

停止規則：fatal/CUDA/NATIVE_PIPE_CHECK非零mismatch立即中止整campaign，保留raw，finally還原。transport/identity/capacity/process/block失敗同樣中止，不換臂或source。非致命候選重複文字只標REJECT_REPETITION，完成該臂後繼續下一個預定獨立候選；control重複則中止，因無有效對照。沒有任何失敗fallback。

輸出：campaign.json逐步落盤、每block meta/results/raw responses/engine logs、runtime-env核對、rows.json、blocks.json、result.json、raw-manifest SHA/bytes、restore/final_verify。只報preliminary pooled accepted tok/s與對C/C2百分比，無CI、不作正式speed gate。

A/A比較：每題記C/C2首差字元、是否全相同及長度；候選記對兩個control首差、長度、重複、是否比A/A更早。分類只有小screen未見額外偏離／數值未解／重複reject，不稱bitwise exact或語意品質通過。128-token reasoning截斷與固定先後順序限制必須保留。

Staging要求：同remote run根目錄放controller.py、base.py，以及harness/replay_ab_20261027.py與harness/next_steps_ab_20261018.py兩檔。base從已驗證遠端LFUSE/io-arrival run複製；不從不同版本拼替代品。controller只使用原binary，不build新引擎、不改live config、temperature、Git/GitHub或best。

本地驗證已通過：AST syntax、synthetic stub 驗證十臂只有預定單一flag、fatal regex不誤吃`check_mismatch_rows=0`且會擋非零/CUDA錯誤、preliminary rate缺值會拒絕。沒有import真實remote base或啟動流程、沒有remote calls。PLAN本身不代表screen已跑；原始結果由parent實際執行後補入總計畫/ledger。
