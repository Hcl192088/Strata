[LUNA_REPORT]

# NATIVE_PIPE_PO_CONFIRM：PASS

TASK_ID：LUNA-20261012-027；使用者今日「同意」授權的 continuation，無新 claim。本次未操作 GitHub、remote git、source、模型或 current-best 部署。

執行時間（台北）：2026-10-29T08:32:04.027891+08:00 至 2026-10-29T08:48:25.776970+08:00；首次遠端 hostname／程序盤點時間 2026-10-29T08:29:16+08:00。原 API 正在生成時沿用 harness 等待 idle，08:34:51 停機後 process gate clean。

已驗證 hostname：DESKTOP-LKMLUPC。canonical root `C:\Users\User\Strata-Adrian-control` 是 junction，實際指向 `C:\Users\User\Strata-Adrian\repo\Strata-Adrian-control`。

Identity：

- live current-best binary SHA256：`385EF64EE24BDF3BD4B309264FA811901DF9256B92CE4589BAEC70B3F26B30F5`。
- 原 API config SHA256：`F23F1AAD8E385987708D6DFB854AD139D513FE398151CCCC5FBD43CFE303EB6F`。
- O/P 共用 binary SHA256：`3F98913EDB0B01D5D5DD3282412725141C298BF5CC9E890DD286AA0720C27230`。
- 啟動前 API engine PID 23540；API launcher/server/memory-policy 父子程序及 watch 均依名稱、PID、command line 分類，無未分類 Strata/Luna/benchmark/build 程序。Razer RzDiagnosticService.exe 為無關既有服務，未停止。每 block 與每 request 沿用原 process gate；其餘大 working-set 程序僅記錄。
- 沿用遠端原 harness，全部 Python 檔 SHA 相同；十個舊 O/P meta/config 全核對，完整 config 除輸出 log 路徑外相同。十題輸入 SHA 與原 audit 相同。
- Hermes 十題、max_tokens 512、每 block 新 engine、workers 9、affinity all；溫度及 sampling 完全沿用原 harness（原值 temperature=0），沒有調整。每個 engine 第一請求前設定 AboveNormal、每題重驗；容量嚴格 3153 slots／20.00 GiB／20479 MiB。
- 只有 O/P，無 C、SMOKE、CHK、OD、PD；無啟用 PIPE_CHECK／DIAG。既有停用的 STRATA_RAM_LRU_CHECK=0 原樣保留。

新增 block pooled tok/s = Σ engine_generated ×1000／Σ decode_ms：

| 輪次／順序 | 臂 | tokens | decode ms | windows | pooled tok/s |
|---|---|---:|---:|---:|---:|
| 6 | O | 1944 | 43121.8 | 1043 | 45.08160606 |
| 6 | P | 1782 | 39498.6 | 897 | 45.11552308 |
| 7 | P | 1905 | 39569.1 | 1012 | 48.14362722 |
| 7 | O | 1945 | 42411.6 | 1038 | 45.86009488 |

逐輪 P/O（%）：+10.662526 / +6.395232 / -1.072330 / +2.341537 / +3.410364 / +0.075235 / +4.979345。

Primary：七輪配對百分比的算術平均 **+3.827416%**，95% t-CI **+0.145269% 至 +7.509562%**，df=6，t=2.446911851。輪次是 repetition，未將 140 題當成獨立樣本。

Secondary：每題先跨七輪合併 tokens/decode time，再算 P/O，十題平均 +3.847191%，95% t-CI +1.038901..+6.655480%（df=9）。沿用舊分析『每題逐輪比值平均，再跨題』方法則為 +3.954082%，CI +1.688875..+6.219288%（df=9）；兩者均為次要指標。

跨日漂移（各 block pooled rate 的算術平均；新第6–7輪對舊第1–5輪）：

- O：舊 47.22684092 → 新 45.47085047 tok/s，-3.718204%。
- P：舊 49.24582655 → 新 46.62957515 tok/s，-5.312636%。

輸出長度／windows：

| 區間／臂 | requests | tokens | windows | tokens/window |
|---|---:|---:|---:|---:|
| old_O | 50 | 9044 | 4715 | 1.918134 |
| new_O | 20 | 3889 | 2081 | 1.868813 |
| combined_O | 70 | 12933 | 6796 | 1.903031 |
| old_P | 50 | 8740 | 4484 | 1.949153 |
| new_P | 20 | 3687 | 1909 | 1.931378 |
| combined_P | 70 | 12427 | 6393 | 1.943845 |

新增 P 比 O 少 202 tokens（-5.1941%）、少 172 windows（-8.2653%）。輸出/window mix 不同，且兩臂絕對速率均有負向漂移；未確認漂移成因，不把速度差解釋為固定相同輸出的純 kernel 收益。

停止規則：第7輪均值 ≥+3% 且 CI 下限 >0，故 **PASS，第8輪未跑**。未執行第9輪。依預註冊在第7輪檢視一次，必要時第8輪終止；標稱95% t-CI未校正 sequential look，型一錯誤略升。 CI 下限僅略高於零，未部署候選；promotion/source pin/fresh rebuild 不屬本次授權。

原 API 復原：controller finally 已執行，DONE／restored=true／verified=true。再次獨立 audit 核對 engine PID 13612、原 binary/config SHA、AboveNormal、health loaded=true、3153 slots／20.00 GiB／20479 MiB、STRATA_IQ3S_MT1=1，無 PIPE／PIPE_CHECK／DIAG／MT_MIN 啟用。

Coverage：完整讀取所有 4 個新增 meta/config/command/engine logs（325,359 bytes／2,795 行）及 40 正式 rows；原十個 O/P meta/config、harness／輸入 SHA 全比較。舊五輪數據來自實際遠端 rows，並與本機原 rows/analysis 比對。未逐字審閱自然語言 responses、未完整 source audit、未重跑既已證明的 bitwise parity；本次無大型 log 抽樣或截斷後作完整結論。

權威 remote raw：

- 新：`C:\Users\User\Strata-Adrian\repo\Strata-Adrian-control\runs\native-pipeline-po-confirm-20261029`（canonical junction 下同名 root）。
- 舊：`C:\Users\User\Strata-Adrian\repo\Strata-Adrian-control\runs\native-pipeline-20261029`。
- 新 block：`out\block-01-O-r6`、`out\block-02-P-r6`、`out\block-03-P-r7`、`out\block-04-O-r7`；各含 config/meta/results/engine.log、逐題 raw responses 與 tails。
- 本機保存 rows.json、analysis.json、comparison.json、campaign.json、audit.json、compatibility.json、initial_verify.json、final_verify.json、restore.json 與程序盤點。
