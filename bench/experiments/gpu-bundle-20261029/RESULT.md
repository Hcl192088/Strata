# GPU_EXACT_BUNDLE A/B 結果（接手收尾版）

任務：LUNA-20261012-027 continuation。使用者 2026-10-29 授權的 env-only benchmark；沒有 source 修改、build、live config 改寫、push、GitHub 寫入。
Codex 跑到 14:03 中斷；controller 為遠端 detached task，自行跑完 SMOKE＋3 輪並在 finally 還原 live API（14:13:18）。接手者只做收集、重算與獨立核對，未重啟 controller、未重跑任何 benchmark、未停任何程序。

## 結論

- 效能規則（ledger）：按輪 G/C tok/s 平均 **+8.93%**，95% CI **[+1.18, +16.67]%**（n=3，df=2）→ 平均 ≥+3% 且 CI 下限 >0，**形式上達候選門檻**。round3-decision.json：extend_to_5=false、early_stop=false，故只跑 3 輪（符合事前登記規則）。
- 但**輸出精確性失敗：同題同輪 G 與 C 完全相同 0/30**，且 reasoning 在第 0～7 個 token 內就分歧（30 組全部）。ledger 規定「輸出不同 → 記錄，候選前需二分找出不精確的開關」，所以**不能直接當候選**，需另行授權做開關二分。
- 假設的機制**未被支持**：GPU-reach wait 兩臂幾乎相同（C 11.81 vs G 11.81 ms/w，pooled）。G 的快是 CPU 端 ms/w 大降（22.90→12.04），伴隨 tokens/window 掉 22%（1.953→1.517）與 CPU experts/層-window 減半（6.14→3.22）。兩臂產生的文字不同（G 總 token 8507 vs C 5807，同一批題目），tok/s 比較混了「內容不同」；這個 +8.9% 不能直接視為同工作量下 kernel 變快。

## 八開關存在與啟用證據

source：`C:\Users\User\native-pipe-generic-20261029`，HEAD f520bc5e9d31c93caeb296b059e3a3eaa16e493f（source-identity.json，status clean）。switch-source-evidence.json 記錄八個名稱全部有 getenv，無刪除項：

| 開關 | getenv 位置 |
|---|---|
| STRATA_DF_QB_Q4 | src/core/verify.cpp:1137 |
| STRATA_DF_BRANCH | src/core/verify.cpp:678 |
| STRATA_GDN_SPLIT | src/kernels/cuda/verify_kernels.cu:921 |
| STRATA_LFUSE | src/core/verify.cpp:69 |
| STRATA_QFUSE | src/core/verify.cpp:139 |
| STRATA_TSUM | src/kernels/cuda/fused_gr.cu:1607 |
| STRATA_MMVF_ROWS | src/kernels/cuda/native_bf16.cu:272、302 |
| STRATA_ATTN_LANECELL | src/kernels/cuda/qsa_decode_attn.cu:638 |

啟用證據：每個 G／SMOKE block 的 meta.effective_env 八項皆為 "1"，C block 未設（qa.py 逐 block 檢查通過）。**engine log 沒有任何含這八個名稱的行**（switch-active-*.json 的 log_lines 全為空），沒有逐 kernel 計數器，所以只能證明「engine 收到 env」，不能證明每個 kernel 分支都實際走到。間接旁證：G 的輸出與 C 在第 0～7 token 就不同，且 CPU 端/窗口統計明顯改變，顯示 G 確實改變了計算路徑。

Config audit：controller 啟動前對 C／G／SMOKE 做 config 相等比對（config-audit.json），只允許八個 env、per-block log 路徑、cwd 不同；qa.py 對 7 個 block 的 config／meta／startup 重驗通過（3153 slots、20.00 GiB、20479 MiB locked、priority 32768＝AboveNormal、無 --spec-split、NATIVE_PIPE ACTIVE、無 FATAL／CUDA error、無 PIPE_CHECK）。

## SMOKE（G，×512）

block-00-SMOKE-r0 status=OK：p01 149 tokens／39.1 tok/s、p05 414／43.0、p08 333／52.2；PIPE ACTIVE、無 fatal／CUDA error、容量 3153／20.00／20479。不計入 primary。

## 每 block 指標（rows.json，60 列；pooled tok/s＝Σtokens×1000/Σdecode_ms；CPU／GPU-reach 以 windows 加權）

| 輪 | arm | tokens | windows | decode_ms | tok/s | ms/window | tokens/window | CPU ms/w | GPU-reach ms/w | CPU experts/層-window |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | C | 1912 | 968 | 39607.2 | 48.27 | 40.92 | 1.975 | 23.80 | 11.88 | 6.26 |
| 1 | G | 2603 | 1920 | 51178.4 | 50.86 | 26.66 | 1.356 | 10.54 | 11.99 | 2.76 |
| 2 | G | 2708 | 1718 | 49374.2 | 54.85 | 28.74 | 1.576 | 12.20 | 11.81 | 3.30 |
| 2 | C | 1689 | 855 | 33969.8 | 49.72 | 39.73 | 1.975 | 22.78 | 11.79 | 6.29 |
| 3 | C | 2206 | 1150 | 45137.4 | 48.87 | 39.25 | 1.918 | 22.22 | 11.77 | 5.93 |
| 3 | G | 3196 | 1970 | 58850.9 | 54.31 | 29.87 | 1.622 | 13.35 | 11.64 | 3.61 |

（順序：第 1、3 輪 C→G，第 2 輪 G→C。）全 arm pooled：C 48.92 tok/s、39.93 ms/w、1.953 tok/w、CPU 22.90、GPU-reach 11.81；G 53.37 tok/s、28.42 ms/w、1.517 tok/w、CPU 12.04、GPU-reach 11.81。

## 逐輪 G/C 與 95% CI

| 輪 | 順序 | tok/s Δ% | ms/window Δ% | tokens/window Δ% |
|---|---|---:|---:|---:|
| 1 | C→G | +5.36 | −34.85 | −31.36 |
| 2 | G→C | +10.31 | −27.66 | −20.21 |
| 3 | C→G | +11.12 | −23.89 | −15.43 |
| 平均 | | **+8.93** | −28.80 | −22.33 |
| 95% CI（t=4.3027，df=2） | | **[+1.18, +16.67]** | [−42.64, −14.96] | [−42.65, −2.02] |

三輪全正；趨勢逐輪變大（5.4→10.3→11.1），n=3 無法判斷是順序/暖機效應還是雜訊。

## 逐題 secondary（每題跨 3 輪 pool；十題平均 +11.83%，CI [−1.79, +25.46]，df=9；不取代 primary）

| 題 | C tok/s | G tok/s | Δ% |
|---|---:|---:|---:|
| p01 | 35.19 | 35.48 | +0.81 |
| p02 | 36.99 | 47.45 | +28.28 |
| p03 | 40.42 | 60.75 | +50.30 |
| p04 | 47.04 | 44.70 | −4.96 |
| p05 | 51.38 | 51.97 | +1.14 |
| p06 | 47.53 | 59.90 | +26.04 |
| p07 | 50.53 | 52.36 | +3.64 |
| p08 | 55.60 | 47.28 | −14.96 |
| p09 | 48.06 | 55.14 | +14.73 |
| p10 | 51.77 | 58.67 | +13.33 |

secondary CI 跨 0；10 題中 2 題為負（p04、p08），增益集中在 p03、p02、p06。

## 輸出長度（rows.json，每題 3 輪的 out tokens／finish）

C 幾乎每輪相同（如 p01 78/78/78、p02 41/41/41、p03 90/90/90，皆非 length 截斷，p05 第 3 輪與 p10 第 1 輪達 512 length）。G 長度明顯不同且較長：p03 為 512(length)/222/512(length)，p06 386(length)/176/512(length)，p09 131/426/509(length)，p10 三輪皆 512(length)。→ G 臂的 token 總量多 46%，是 pooled tok/s 與 tokens/window 都受內容影響的原因。

## Exactness（G vs C，同題同輪，reasoning_content＋content 逐字比對；exactness.json）

- 完全相同：**0/30**。reasoning_content 相同 0/30；content 相同 21/30（這 21 組都是雙方 content 皆空，非有內容的相同）。
- reasoning 首差 token index（zero-based，重新 tokenizer 編碼）：r1＝p01..p10：2,3,6,3,3,4,0,3,4,0；r2：2,3,4,3,3,4,0,7,4,0；r3：2,3,4,3,2,1,0,0,4,0。全部 ≤7。
- SMOKE 的 G 對 C 第 1 輪（非同輪配對，smoke-exactness.json）：p01 reasoning 2／content 5；p05 reasoning 3；p08 reasoning 26，同樣不同。
- C 本身重複性高（見上節長度），所以差異來自 G 的開關，不是 C 的隨機性。
- 限制：只比對 API 回傳文字，沒有原始 engine token IDs。沒有二分，不知道是八個中的哪幾個造成。source 註解宣稱 exact 與本實測不符；未驗證原因（可能與 tail-skip／native pipeline 的交互有關，純推測）。

## 判定（按 ledger 規則）

1. 前三輪沒有全負、平均也不小於 −3% → 不結案。
2. 平均 +8.93% >5%、CI 不跨 0 → 不延長到 5 輪（事前登記規則，controller 已套用）。
3. 平均 ≥+3% 且 CI 下限 +1.18 >0 → 效能面形式上是「候選」。
4. 輸出 0/30 一致 → 依 ledger「候選前需二分找出不精確的開關」。**暫不可部署／不可當 best**。GPU-reach 假設（上限 1～2.4 ms/w）被推翻：GPU-reach 持平，收益來自 CPU 端與窗口大小改變，且伴隨輸出改變。建議下一步（需使用者授權）：拆開關二分（先看 DF_QB_Q4／DF_BRANCH 這兩個直接動到 verify 路徑的），並用固定內容（例如強制 teacher-forcing 或比 draft 接受率）排除「內容不同」的混淆。

## Live 復原的獨立核對（接手者於 2026-10-29 14:16 自遠端查）

- strata.exe 僅 1 個，PID 19064，啟動時間 14:12:58；路徑經 `Strata-Adrian\repo\...` junction 指向 native-pipe-deploy-prep-20261029\build\strata.exe，SHA256 A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8（相符）。
- config server-task020-8080-v0142-s2k-mt1.json SHA256 060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93（相符）。
- priority 32768（AboveNormal）；環境 STRATA_NATIVE_PIPE=1、STRATA_IQ3S_MT1=1；八個 bundle env 一個都沒有；無 PIPE_CHECK；cmdline 無 --spec-split。
- /health：status ok、loaded true；/metrics：expert_slots 3153、arena_mib 20479、pool_workers 9、kv q4_0、spec 6。
- **注意：brief 寫的 127.0.0.1:8080 連不上（connection refused）**，因為 live API 是以 `--host <tailscale-host> --port 8080` 啟動（Tailscale IP，netstat 顯示只聽 <tailscale-host>:8080，PID 8480），這是 live config 本來的設定，不是還原失敗；我改用 <tailscale-host>:8080 查到上述 health／metrics。
- controller 自己的 final_verify.json 與 independent_verify.json（postprocess.py 產生）均 verified=true；restore.json：14:12:56 開始、載入 20.7 s、14:13:18 完成。memory-policy watch 程序（strata_memory_policy.py）與 API 同於 14:12:57 重新啟動，為原 live 設定的一部分。
- 排程：Strata-GPU-Bundle-20261029 State=Ready（無週期 trigger）；舊 Strata-Spec-Split-20261029 已由 launch.ps1 在實際為 Ready 時刪除（old-task-cleanup.json）。

## 中斷與接手說明、限制

- 接手時 controller 在跑第 2 輪；全程只用 SSH 輪詢 campaign.json／controller.log 並做 process gate（只見 controller 自己、自有 serve.server＋strata.exe 與 live API/watch 程序）。完成後上傳 postprocess.py、collect.ps1（新增兩檔，非原有檔案覆寫）到 run root 並執行：重新做 verify、exactness（全 30 組）、smoke-exactness、archive（evidence.zip，249 檔）。
- 本機重算：analyze.py（讀 rows.json，結果與 controller 的 round-deltas.json 一致：5.3595／10.3092／11.1181）、qa.py（evidence.zip 內 raw-manifest 逐檔 size／SHA256 通過、60 rows、30 對、7 block 全通過）。write_report.py 未採用，其樣板內含我未驗證的敘述，故此報告由我重寫。
- 未做：無 per-kernel 啟用計數；無原始 token IDs；未全面 audit source（僅依 switch-source-evidence）；未二分開關；model/pack 未重 hash。三輪 CI 很寬（df=2）。

## 檔案位置

- 遠端權威 raw：`C:\Users\User\Strata-Adrian-control\runs\gpu-bundle-20261029`
- 本機：`D:\strata\state\gpu-bundle-20261029`：rows.json、analysis.json、qa.json、exactness（raw\exactness.json）、evidence.zip、解壓目錄 raw\（含 out\block-*）。
