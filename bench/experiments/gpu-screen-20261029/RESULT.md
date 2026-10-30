# GPU_SWITCH_EXACT_SCREEN 結果

任務：LUNA-20261012-027 continuation；使用者授權的篩選（不做 A/B 速度跑）。env-only，無 source 修改、build、live config 改寫、push、GitHub 寫入。
遠端 run root：`C:\Users\User\Strata-Adrian-control\runs\gpu-screen-20261029`；本機 raw：`D:\strata\state\gpu-screen-20261029\raw\`（evidence.zip 206 檔 size/SHA 全數通過）。detached controller（排程 Strata-GPU-Screen-20261029）跑完 10 個 block，campaign.json phase=DONE、verdict=SCREEN_COMPLETE、restored=true、verified=true。

## 一、結論（分類）

判定方法：C 與 C2 本身不同（見第二節），所以依 ledger 改用「首差位置與 A/A 首差比較」：某臂某題只要與 C 或 C2 其中一個相同的前綴，長度不短於 C 與 C2 彼此相同的前綴（p01 完全相同；p05 前 246 字元；p08 前 51 字元），就視為落在 A/A 噪音內；較早分歧、且對 C 與 C2 都早於基準，才算超出噪音。

| 開關 | 分類 | 依據 |
|---|---|---|
| STRATA_DF_QB_Q4 | EXACT（A/A 噪音內，有限度） | p01 相同、p05 與 C 相同；p08 與 C 到 137 才分歧（基準 51），文字連貫 |
| STRATA_DF_BRANCH | EXACT（A/A 噪音內） | p01 相同；p05 對 C 分歧 @246（= C vs C2 基準）；p08 與 C2 相同 |
| STRATA_LFUSE | EXACT（三題與 C 逐字相同） | 唯一三題皆與 C 完全相同的開關 |
| STRATA_MMVF_ROWS | EXACT（A/A 噪音內） | p01 相同；p05 對 C @246、對 C2 @297；p08 對 C @60、對 C2 @51 |
| STRATA_ATTN_LANECELL | EXACT（A/A 噪音內） | p01 相同；p05 對 C @246、對 C2 @297；p08 對 C @51、對 C2 @147 |
| STRATA_GDN_SPLIT | UNCLEAR | p05 對 C 與 C2 都在 @136 分歧（早於基準 246），p01、p08 在噪音內；文字連貫、無迴圈，僅 1 題超出噪音，n 太小 |
| STRATA_TSUM | UNCLEAR | 同 GDN_SPLIT：p05 對 C 與 C2 都 @136，且與 GDN_SPLIT 的 p05 輸出彼此一致；其餘在噪音內 |
| STRATA_QFUSE | BROKEN | 三題都在前 7～15 字元分歧；p01 出現重複破碎（`" or change of direction" " or " or " or ...`，偵測器命中 `" or`）；p05 結尾語句破碎，p08 亦偏離 |

限制：每臂 3 題 x 128 token（reasoning 多半被截斷），比對的是 reasoning_content 與 content 串接字串（首差為字元索引）；n=1 次，C 與 C2 本身有差異，所以「EXACT」指「未觀察到超出 A/A 噪音的偏離」，不是 bitwise 證明。engine log 沒有任何含開關名稱的行（switch-active-*.json 皆空），只能證明 engine 收到 env（meta.effective_env 與 harness 的 effective-env 斷言通過），不能證明每個 kernel 分支都實際走到。

## 二、C vs C2（A/A 基準）

| 題 | C2 vs C | 首差 | 周圍（C2 / C） |
|---|---|---|---|
| p01 | 相同 | - | - |
| p05 | 不同 | @246（C2 長 569、C 長 589） | C2：`000 active threads per channel; archived threads don't count, but there's also a`<br>C：`000 active threads per channel, and archived threads don't count toward the limi` |
| p08 | 不同 | @51（C2 長 170、C 長 311） | C2：`se ID structure to understand the chat and message references, then I need to qu`<br>C：`se ID structure to understand what the numbers represent—it seems like the forma` |

C 與 C2 在同一 live binary／config 下 p05、p08 就不同，所以單一 C 不能當 bitwise 基準；基準首差：p01 無、p05 @246、p08 @51。

## 三、各臂 x 各題比較

| 臂 | 題 | 對 C | 對 C2 | 破碎/迴圈旗標 | 對 C 首差周圍（本臂 / C） |
|---|---|---|---|---|---|
| DF_QB_Q4 | p01 | 相同 | 相同 | 無 | - |
| DF_QB_Q4 | p05 | 相同 | 不同 @246 | 無 | - |
| DF_QB_Q4 | p08 | 不同 @137 | 不同 @51 | 無 | `t be beeper-line-<chat>-<start_msg>-<end_msg>, so chat 273 would be the channel `<br>`t be beeper-line-<chat>-<start>-<end>, but the cron report shows different value` |
| DF_BRANCH | p01 | 相同 | 相同 | 無 | - |
| DF_BRANCH | p05 | 不同 @246 | 不同 @257 | 無 | `000 active threads per channel; archived ones don't count, but there's also a li`<br>`000 active threads per channel, and archived threads don't count toward the limi` |
| DF_BRANCH | p08 | 不同 @51 | 相同 | 無 | `se ID structure to understand the chat and message references, then I need to qu`<br>`se ID structure to understand what the numbers represent—it seems like the forma` |
| GDN_SPLIT | p01 | 相同 | 相同 | 無 | - |
| GDN_SPLIT | p05 | 不同 @136 | 不同 @136 | 無 | `rd thread limits: 1000 active threads per channel (archived threads count toward`<br>`rd thread limits: 1000 active (non-archived) threads per channel (including arch` |
| GDN_SPLIT | p08 | 不同 @51 | 相同 | 無 | `se ID structure to understand the chat and message references, then I need to qu`<br>`se ID structure to understand what the numbers represent—it seems like the forma` |
| LFUSE | p01 | 相同 | 相同 | 無 | - |
| LFUSE | p05 | 相同 | 不同 @246 | 無 | - |
| LFUSE | p08 | 相同 | 不同 @51 | 無 | - |
| QFUSE | p01 | 不同 @10 | 不同 @10 | 迴圈：" or | `The user sent "[轉舵] 測試" — [R" — [course material testing ]" `<br>`The user said "[轉舵] 測試" — this looks like a test message. "轉` |
| QFUSE | p05 | 不同 @7 | 不同 @7 | 無 | `Ken is the question about Discord thread limit really cap`<br>`Ken is asking whether there's an upper limit on threads, ` |
| QFUSE | p08 | 不同 @15 | 不同 @15 | 無 | `I'm looking at a case ID that references a LINE chat 273 with mes`<br>`I'm looking at the case ID structure to understand what the numbe` |
| TSUM | p01 | 相同 | 相同 | 無 | - |
| TSUM | p05 | 不同 @136 | 不同 @136 | 無 | `rd thread limits: 1000 active threads per channel (archived threads count toward`<br>`rd thread limits: 1000 active (non-archived) threads per channel (including arch` |
| TSUM | p08 | 不同 @51 | 相同 | 無 | `se ID structure to understand the chat and message references, then I need to qu`<br>`se ID structure to understand what the numbers represent—it seems like the forma` |
| MMVF_ROWS | p01 | 相同 | 相同 | 無 | - |
| MMVF_ROWS | p05 | 不同 @246 | 不同 @297 | 無 | `000 active threads per channel; archived threads don't count, but there's also a`<br>`000 active threads per channel, and archived threads don't count toward the limi` |
| MMVF_ROWS | p08 | 不同 @60 | 不同 @51 | 無 | `ucture to understand what the chat number represents—it seems like 273 might be `<br>`ucture to understand what the numbers represent—it seems like the format might b` |
| ATTN_LANECELL | p01 | 相同 | 相同 | 無 | - |
| ATTN_LANECELL | p05 | 不同 @246 | 不同 @297 | 無 | `000 active threads per channel; archived threads don't count, but there's also a`<br>`000 active threads per channel, and archived threads don't count toward the limi` |
| ATTN_LANECELL | p08 | 不同 @51 | 不同 @147 | 無 | `se ID structure to understand the chat and message references, then I need to qu`<br>`se ID structure to understand what the numbers represent—it seems like the forma` |

人工檢視：QFUSE p01/p05 結尾明顯破碎（引號與 or 重複、語句不成句）；其餘臂的 reasoning 皆為連貫英文，無重複迴圈。偵測器（同 2～6 詞片段連續 4 次以上）只命中 QFUSE p01。finish_reason：C 為 stop/length/length；QB_Q4 為 stop/length/tool_calls；QFUSE 為 length/length/tool_calls。

## 四、粗略單次速度指標（n=1，3 題 x 128 token，非 A/B）

來源：raw/rows.json（engine 計時）；pooled tok/s = Σtokens x 1000 / Σdecode_ms；ms/w、tokens/w 為總和相除；CPU ms/w、GPU-reach(gpu_wait) ms/w 以 windows 加權。僅為粗略指標，不構成速度結論、不用於候選判定。

| 臂 | 與C相同題數 | tokens | windows | tok/s | vs C | vs C2 | ms/w | vs C | vs C2 | tok/w | vs C | CPU ms/w | vs C | GPU-reach ms/w | vs C |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C | 3/3 | 334 | 184 | 37.08 | +0.0% | +0.3% | 48.95 | +0.0% | -7.9% | 1.815 | +0.0% | 31.45 | +0.0% | 11.55 | +0.0% |
| DF_QB_Q4 | 2/3 | 317 | 173 | 38.46 | +3.7% | +4.0% | 47.65 | -2.7% | -10.3% | 1.832 | +0.9% | 30.93 | -1.6% | 11.58 | +0.3% |
| DF_BRANCH | 1/3 | 334 | 170 | 38.96 | +5.0% | +5.3% | 50.43 | +3.0% | -5.1% | 1.965 | +8.2% | 33.48 | +6.5% | 11.68 | +1.1% |
| GDN_SPLIT | 1/3 | 334 | 176 | 38.36 | +3.4% | +3.7% | 49.47 | +1.1% | -6.9% | 1.898 | +4.5% | 32.46 | +3.2% | 11.62 | +0.7% |
| LFUSE | 3/3 | 334 | 184 | 38.52 | +3.9% | +4.2% | 47.12 | -3.7% | -11.3% | 1.815 | +0.0% | 30.41 | -3.3% | 11.55 | +0.0% |
| QFUSE | 0/3 | 343 | 232 | 33.40 | -9.9% | -9.7% | 44.27 | -9.6% | -16.7% | 1.478 | -18.6% | 28.13 | -10.6% | 11.08 | -4.0% |
| TSUM | 1/3 | 334 | 168 | 34.06 | -8.1% | -7.9% | 58.37 | +19.2% | +9.9% | 1.988 | +9.5% | 41.37 | +31.6% | 11.72 | +1.5% |
| MMVF_ROWS | 1/3 | 334 | 182 | 36.02 | -2.9% | -2.6% | 50.95 | +4.1% | -4.1% | 1.835 | +1.1% | 33.92 | +7.9% | 11.74 | +1.6% |
| ATTN_LANECELL | 1/3 | 334 | 174 | 34.04 | -8.2% | -7.9% | 56.38 | +15.2% | +6.1% | 1.920 | +5.7% | 38.87 | +23.6% | 11.86 | +2.7% |
| C2 | 1/3 | 334 | 170 | 36.98 | -0.3% | +0.0% | 53.13 | +8.5% | +0.0% | 1.965 | +8.2% | 36.12 | +14.9% | 11.73 | +1.6% |

解讀限制：
- 只有輸出與 C 逐字相同的題，window／T 才可能一致、逐 window 比較才算 like-for-like；整臂三題全同的只有 LFUSE。即使如此，C 與 C2 的 windows 就差 184 vs 170、ms/w 差 +8.5%、CPU ms/w 差 +14.9%，單次噪音已大於多數開關間差異。
- 輸出不同的臂（含 QFUSE，其 tokens/windows 本身就不同：windows 232、tok/w 1.478）tokens、windows 與 T 分布不同，速度不可比。
- GPU-reach 各臂 11.08～11.86 ms/w，C 為 11.55、C2 為 11.73，差異在噪音內；本次不支持也不否定「單開縮短 GPU 段」。

## 五、config 審核與環境

- 八個開關 source getenv 位置沿用 gpu-bundle-20261029/RESULT.md 的證據；本次未重做 source 審核。
- controller 啟動前逐臂（C、8 個單開、C2）比對 config：與 live config 只允許該臂一個 env=1、per-block log 路徑、cwd 不同，config-audit.json 全數 equal_except_authorized=true。
- 每個 block 的 meta.effective_env：C／C2 只有 STRATA_NATIVE_PIPE=1、STRATA_IQ3S_MT1=1；單開臂另加且僅加該臂 env=1。10 個 block 皆 status=OK、PIPE ACTIVE、無 fatal／CUDA error／mismatch 文字、strict 容量 3153／20.00 GiB／20479 MiB、priority 32768（AboveNormal）、binary SHA A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8、config SHA 060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93（controller identity 檢查）。max_tokens 128、無 PIPE_CHECK、無輪次／停止規則。
- 順序：C、DF_QB_Q4、DF_BRANCH、GDN_SPLIT、LFUSE、QFUSE、TSUM、MMVF_ROWS、ATTN_LANECELL、C2；每臂新引擎。

## 六、live 還原與獨立核對

- 先刪舊排程 Strata-GPU-Bundle-20261029（Ready，紀錄於 raw/old-task-cleanup.json）。
- controller finally 還原 API：14:39:30 `API RESTORE OK`（restore.log）。final_verify.json 與之後另跑的 independent_verify.json 皆 verified=true：單一 strata.exe PID 18544、A1E6…、config 060F…、priority 32768（AboveNormal）、/health loaded（http://<tailscale-host>:8080）、/metrics expert_slots 3153／arena_mib 20479、env PIPE=1 且 MT1=1、八個開關皆無。
- 我的新排程 Strata-GPU-Screen-20261029 保留，狀態 Ready；無 controller 殘留。

## 七、原始檔

- 本機 raw：`D:\strata\state\gpu-screen-20261029\raw\`（campaign.json、rows.json、config-audit.json、out\block-*\resp-p*.json／meta.json／engine.log、final_verify.json、independent_verify.json、restore.log）
- 分析：analysis.json、analyze.py、report.py；controller.py、launch.ps1 為本次改編版。
- 未做：速度 A/B、source 審核、原始 token ID 比對（harness 未保留）。
