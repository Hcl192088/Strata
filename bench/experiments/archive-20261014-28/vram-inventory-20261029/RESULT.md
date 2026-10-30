# VRAM_WEIGHT_INVENTORY 結果（唯讀，2026-10-29）

來源：遠端 live source `C:\Users\User\native-pipe-generic-20261029`（行號皆此處）、pack `Strata-IQ3-20261008\packs\iq3_xxs\index.txt`、GGUF 兩個 shard 的 header（本機解析，原始檔在 `raw\`）、MTP `...\mtp\rt\dense.txt`／`experts.format`、live 設定 `server-task020-8080-v0142-s2k-mt1.json`。全程未停 API、未改任何東西。

## 1. 每一項的實際內容

- **canonical 1466 MiB（= pack 的 dense.bin 1538035200 B）**：單一 cudaMalloc 的 arena，全在 GPU（generate.cpp:2936-2943，pool_bytes）。777 個 tensor，全是 GGUF 原樣的 BF16／F32，沒有量化。
  - HC（hyper-connection）down/up 4 組 x 48 層 = 1200 MiB（BF16），inject 7.5、norm 3.8
  - router `ffn_gate_inp` 48 層 = 120 MiB（BF16）
  - PLE `ple_key` 50 + `ple_value` 12.5 MiB（BF16；pack 為 --compat-bf16，留在 arena，generate.cpp:2841）
  - indexer q/k 37.5、ssm alpha/beta 16.9、ssm_conv1d 5.6、其餘 <1
  - HC down/up 之外的 BF16 都是 router／PLE／indexer 類，碰了會直接動路由或分數
- **native 1781.11 MiB（300 個矩陣，與 log 完全吻合）**：全部是 GGUF 原生量化 bytes（NativeDense，native_dense.cpp:289-300），不是 BF16。依 dtype：Q6_K 824.4 MiB（71 個）、IQ4_XS 373.7（67）、Q4_K 283.2（45）、Q5_K 137.1（14）、IQ3_S 124.1（55）、IQ4_NL 35.2（40）、Q2_0 3.5（8，GGUF type 42）。依用途：attn_qkv 597、ssm_out 376、attn_gate 304、attn_q 226、attn_output 142、shared expert 115、attn_k/v 22。
- **另兩個被「served natively」跳過的**：`output.weight` Q5_K 416.8 MiB（437043200 B，GPU）；`token_embd` IQ3_S 260.5 MiB（在 host mapped memory，不佔 VRAM）。302 = 300 + 這 2 個。
- **重複**：主模型沒有。canonical 與 native 不重複（skip 機制，generate.cpp:2828-2846；`--keep-canonical` 才會雙載，live 沒開）。native 未啟用 `STRATA_Q8_PACKED`／`STRATA_Q6_PACKED`（無第二份 packed 副本，native_dense.cpp:302-320）。**唯一的重複在 MTP：draft head 178.4 MiB 是主 head（Q5_K）106299 列的 gather 複製品**（mtp.cpp:652 gather_rows，dtype 跟主 head 一樣）。
- **MTP draft layer 820 MiB**：experts 675 MiB（512 個 blob x 1,382,400 B，格式 q2_0 ≈ 2.25 bit，已經是最小格式；experts.format = q2_0；mtp.cpp:298-318 整包常駐 VRAM，blob 大小是編譯期常數 cpu::BLOB）；dense 110.7 MiB（Q8_0 投影 70.4 MiB + BF16 的 HC／router／gate 約 40 MiB）；其餘約 34 MiB 是 K/V ring 與 buffer。

## 2. 總表

VRAM 總量 12282 MiB（4070）；Strata 自己 11140.6 MiB、其他程式約 496 MiB、啟動時剩 254 MiB（10/18 盤點報告 LUNA-20261012-027.replay-vram-20261018.md 的 WDDM 計數）。每 1 MiB 約 0.60 個 slot（平均 slot 1.663 MiB）。

| 項目 | MiB | dtype | 在 GPU | 可縮（怎麼縮／到什麼） | 可釋出 MiB（≈slot） | 輸出是否不變 |
|---|---|---|---|---|---|---|
| expert cache | 5245 | IQ/q2 混合 blob | 是 | 目標容器 | - | - |
| canonical：HC down/up | 1200 | BF16 | 是 | 轉 Q8_0（34/64 B）；需新程式 | 約 563（約 338 slot） | 否（rounding 等級） |
| canonical：router gate_inp | 120 | BF16 | 是 | 不建議（動路由） | - | 否 |
| canonical：PLE key／value | 62.5 | BF16 | 是 | 轉 Q8_0 | 約 29 | 否 |
| canonical：其餘（inject/indexer/ssm/norm） | 約 84 | BF16/F32 | 是 | 不值得 | - | 否 |
| native 投影（Q6_K 部分） | 824.4 | Q6_K | 是 | 重量化成 IQ4_XS／Q5_K；需離線 requant 工具 | 291／134（175／80 slot） | 否（品質變） |
| native 投影（其餘） | 956.7 | IQ4_XS/Q4_K/Q5_K/IQ3_S/IQ4_NL | 是 | 已偏低，不建議 | - | 否 |
| 主 head | 416.8 | Q5_K | 是 | 降 Q4_K 約省 76；影響每個 token | 76 | 否 |
| token embedding | 260.5 | IQ3_S | 否（host mapped） | 不佔 VRAM | 0 | - |
| MTP experts | 675 | q2_0（2.25 bit） | 是 | 已最小；只能「只留熱門 expert 常駐、其餘走 host」，需新程式與 MTP 路由直方圖（沒量過） | 未知 | 是（只影響 acceptance／速度） |
| MTP dense（Q8_0 部分） | 70.4 | Q8_0 | 是 | 轉 Q4_0；可丟掉的原檔只有 q/o/shared/indexer 約 54 MiB（K/V 預填還要 Q8 的 fc_*、k/v） | 約 26 | 是 |
| MTP dense（BF16 部分） | 約 40 | BF16 | 是 | 不值得 | - | 是 |
| MTP 其餘 state／buffer | 約 34 | - | 是 | 不值得 | - | - |
| MTP draft head（主 head 的子集複製） | 178.4 | Q5_K | 是 | 見第 3 節：STRATA_MTP_FULL_HEAD=1 直接不配這份 | 178.4（約 107 slot） | 是（只影響 acceptance／速度） |
| verify buffers | 69.8 | - | 是 | --spec 6 降到 4 約省 60（舊報告） | 約 60 | 是 |
| KV（resident 20480 cell） | 約 135 | q4_0 | 是 | 已是下限（kv-resident 最小 20480） | 0 | - |
| 未歸屬（CUDA context、GDN state、buffers、graph） | 約 930 | - | 是 | 未逐項量過 | ? | - |
| 其他程式（WDDM） | 約 496 | - | 是 | 重啟前關 Razer／Steam／LGHub 等，約 110-120 slot（舊報告） | 約 180-200 | 是 |

## 3. 現有程式已支援的選項（file:line）

- **`STRATA_MTP_FULL_HEAD=1`**（mtp.cpp:457-462；mtp.cpp:638 條件 `!full_head_env()` 時不配 dhead_；mtp.cpp:492）：不複製 head 子集，改用主 head 全詞表做 draft。直接省 178.4 MiB（約 107 slot，+3.4%）。程式註解標明是「diagnostic」，用途是量測子集對 acceptance 的影響，不是正式功能。代價：每個 draft step 要讀 417 MiB 而非 178 MiB，draft 時間會變長（現在 draft 約 1.7-3.6 ms/window，粗估多 1-1.5 ms，沒實測）。輸出不變（draft 只影響 acceptance），所以這是一個可 A/B 的候選。
- **`--mtp-q4 all|proj|head`**（generate.cpp:2005、4337；mtp.hpp:61-64；mtp.cpp:184-242）：**不省 VRAM，反而多用**。proj：新配一份 Q4_0 副本（約 37 MiB），Q8_0 原檔仍保留（預填還要，mtp.hpp:63）；head：原地覆寫（mtp.cpp:232），cudaMalloc 大小不變，一個 byte 都沒釋出。目的是少讀 bytes（速度），不是省 VRAM。
- **`STRATA_HC_Q8=1`**（native_dense.cpp:41-52、323-348；verify.cpp:990、1608；fused_gr.cu:1168）：看似可以把 HC 改成 Q8_0，**但對這個模型是空操作**。程式只在「GGUF 裡的 tensor 型別本來就是 Q8_0」時才建 Q8_0 副本（native_dense.cpp:329 `tensor.type != 8` 則 continue），而這份 GGUF 的 HC 是 BF16，所以什麼都不會發生。就算發生，也是「額外多一份」（verify 用 Q8 讀取，BF16 仍留在 arena），因為預填還讀 BF16（prefill.cpp:2510 `wd->data`）。arch_defaults.hpp:8 註明這類是「rounding-level, KL-gated」。
- **`--keep-canonical`**（generate.cpp:760、2831）：反方向，是雙載，沒開。
- 沒有任何現有旗標可以讓 native 投影或 head 以更小 dtype 載入（native_dense 只照 GGUF 的 type 原樣上傳；native_mmvq_supported 只是列支援的 type，native_mmvq.cu:2420）。

## 4. 建議排序（只依 MiB、不測速度）

1. **STRATA_MTP_FULL_HEAD=1**：唯一零程式改動、輸出不變、有明確 MiB（178.4，約 +107 slot）的項目。要不要做取決於 draft 變慢是否吃掉 +3.4% slot 的好處，需要 A/B，且 acceptance 可能更高（全詞表）。
2. **關非 Strata 的 GPU 程式再重啟**（舊報告第 1 項）：約 +110-120 slot，免費，與上面可疊加。
3. **HC BF16 → Q8_0（1200 → 637 MiB，+563 MiB、約 +338 slot、+10.7%）**：最大的單一池子，但要改程式（載入時量化、arena 排除這些名稱、預填與 MTP 路徑要能用 Q8 或保留 BF16），而且輸出會有 rounding 等級的變化，需 KL 驗證。現成的 `STRATA_HC_Q8` 不適用，要改的是它的條件（native_dense.cpp:329）與預填讀取（prefill.cpp:2510）。
4. Q6_K 重量化（134-291 MiB）與 head 降級（76 MiB）：品質代價大，且沒有現成路徑，優先度低。
5. MTP experts 675 MiB 只能靠「熱門子集常駐」，沒有任何 MTP 路由分佈資料可以判斷值不值得；要先量 MTP 的 expert 命中分佈才能談。
6. `--mtp-q4`、MTP dense 降精度：合計 <30 MiB，不值得。

注意：以上「slot 數」是用 0.60 slot/MiB 估算；實際 slot 數由啟動時的剩餘 VRAM 決定（--expert-cache 3604 只是上限），改任何一項都要重啟才生效。「未歸屬約 930 MiB」尚未逐項量過，是這份盤點最大的缺口。
