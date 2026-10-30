[LUNA_REPORT]
TASK_ID: LUNA-20261012-027
STATUS: COMPLETED
TASK_SOURCE: branch
TASK_BRANCH: coordination/task-027-file-tier-reuse-20261012
TASK_COMMIT_SHA: da28699a382304ec8afc87a547f9c37123985f77
AUTHORIZATION: Direct user continuation, 2026-10-29 "好去做"; bounded lossless compression screening and read-only GPU packed feasibility. No new GitHub claim.
BENCHMARK_RAW_PATH: C:\Users\User\Strata-Adrian-control\runs\lossless-screen-20261029
PUBLICATION_STATUS: REPORT_LOCAL. Existing guard requires task027 to be the current RUNNING/REPORT_LOCAL claim; durable state is finalized task028. No state rewrite, re-claim, guard modification, or direct outbox write was used. Remote source handoff commit/push receipt is separate.

Git publication receipt: BLOCKED_AUTO_REVIEW. The shell containing report upload/commit/push was rejected before launch, so no Git commit or push occurred. Automatic review requires explicit approval for the report payload (remote paths, binary/config hashes, non-secret environment/settings/statistics) to Hcl192088/Strata main. User was asked; no alternate publication route or retry. git-receipt.json records this separately from the successful experiment.

# 結果：三種 RAM 無損壓縮不採用；GPU packed 尚非可用候選

## 1. 已驗證身分與操作範圍
- 主機 DESKTOP-LKMLUPC；strict host-key SSH。原 live PID27744，binary A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8、config060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93，均與遠端 bench/results/2026-10-29-native-pipe/BEST.json 相符。
- 實際 build source C:\Users\User\native-pipe-generic-20261029，HEAD f520bc5e9d31c93caeb296b059e3a3eaa16e493f；該 source clean。canonical main 起始 HEAD2f1e99872969c9b4586a2d41c7f1915f27e4f298；兩個既有 dirty tools 及 untracked files 保留。
- API live idle、3153 GPU slots、20479MiB arena、9 workers。每層重新 process/identity/idle gate；沒有停 API、送生成請求、載入另一個模型、build、CUDA 量測、改 source/model/config/temperature 或安裝套件。
- 現有 zstd/lz4 Python 套件與 CLI 不存在；試驗開始前明確選定 XPRESS-Huffman、zlib1、LZMA1 三個獨立臂，沒有失敗後換 codec。

## 2. RAM 壓縮：NO_GO_FOR_TESTED_CODECS

實際 CPU 權重來源：pack experts.bin，42,912,972,800 bytes；以 native_experts.txt 的 layer offset + expert*blob_bytes 讀取，不以 GGUF role offsets 代替。48層各expert0/257，共96個blob、167,628,800 bytes（159.86MiB）；全部10種gu/down組合。

| Codec | compressed/raw | 節省bytes | 解壓GB/s（十進位） | 每expert解壓中位ms | 20GiB理想容量等值 |
|---|---:|---:|---:|---:|---:|
| XPRESS-Huffman buffer mode | 0.984414 | 1.559% | 0.2400 | 7.385 | 20.317GiB |
| zlib level1 | 0.984631 | 1.537% | 0.3164 | 5.259 | 20.312GiB |
| LZMA preset1 | 0.988383 | 1.162% | 0.0462 | 28.253 | 20.235GiB |

- 288個sample/codec rows、每row七次還原，共2016次byte比較，全部一致；每row最終SHA亦一致。解壓計時不含byte比較/SHA；包含Python wrapper及輸出配置。每個codec每blob壓一次，輪替codec先後；warm decode七次取中位，再按bytes與時間加總得GB/s。
- 單執行緒BelowNormal，128.59秒完成；peak working set49.59MiB。不是模型decode benchmark；沒有新tok/s或品質優於baseline的宣稱。
- 預註冊門檻ratio<=0.90且decode>=3.0GB/s，三臂皆兩項不符。即使忽略decoder成本，樣本的理想容量僅多0.235-0.317GiB，尚未扣metadata與scratch。此結果不支持寫壓縮RAM cache，依停止條件結案，不掃levels。
- raw results.json SHA256 7CE94346B0D4BC0FF1F8B16E311EB76FE5919D5B290FA09527A35829A363D95D，SCP下載後本機hash相同。

## 3. GPU packed：現成旗標不適用；替換原副本需新工程

1. pinned native_dense.cpp:302-303明確保留GGUF原副本給prompt GEMM；:360/364/369/371將native_data與packed分別發布/保有。prefill/prefill.cpp:1890-1893實際將native_data、native_type交給gm.native，不能刪掉原格式後假裝prefill仍正常。
2. 完整精確符號搜尋src/include共333個C/C++/CUDA檔、6,459,821bytes：native_q6_k_pack實際呼叫只在native_head.cpp:67-68及mtp.cpp:659-661，且只對type14(Q6_K)的heads。native_dense並未呼叫Q6 pack。
3. 重新讀兩個實際GGUF的完整header：output.weight是type13(Q5_K)、2560x248320；MTP draft head沿用此head型別。兩個主模型shard中Q8_0二維矩陣數為0。因此Q6_PACKED在目前heads不啟用，Q8_PACKED在主模型dense無對象；不能藉這兩個env直接加速824MiB的Q6_K dense。
4. 主模型Q6_K二維矩陣71個、864,460,800bytes(824.41MiB)；依現有Q6 kernel形狀條件(n_in%256==0、n_in/256>=4、n_out>=2048)有52個、842,956,800bytes(803.91MiB)合格。這是shape eligibility，不是loader支援或速度證明。
5. Q6 packed平面由ql/qh/scales/d原bytes重排，單一packed payload與原格式幾乎同大小（僅alignment），但現成實作另配副本並以原pointer作registry key。要同VRAM，至少要讓dense loader支援、prefill dequant/GEMM與其他讀取者接受新layout、更新ownership/registry/free契約，並驗證ncols/shape/parity。這不是刪一行cudaMalloc能完成的優化。

判定：NO_GO_CURRENT_FLAGS；新layout替換DEFER_PENDING_KERNEL_COST_AND_CONSUMER_PROOF。不build、不部署，也沒有將舊GPU dense6.24ms整段乘上某個倍率作新速度預估。

## 4. Coverage、限制及收尾
- 壓縮覆蓋48/48層、10/10型別對；每層2/512 expert，總96/24576=0.390625%。抽樣是確定性0/257，不是隨機或按live miss熱度抽樣；不宣稱全pack相同比率。
- 檢查完整288行指標、全部2016次解壓parity及48個layer gate。沒有權重/私人prompt/response下載或發布；全pack只核對size/mtime與metadata hash，沒有重hash42.9GB。
- 未測zstd、LZ4、字典/bitplane專用無損壓縮、跨expert相關壓縮或原生多執行緒decoder；本結論僅關閉已測三臂。Python配置/BelowNormal會影響吞吐，ratio本身不受此限制。
- GPU僅完整精確呼叫點掃描及指定消費者區段的語意核對，非全source correctness audit；GGUF完整header解析，未載入/驗證所有tensor內容，未量packed CUDA kernel或prefill成本。
- 初次讀取src/core/prefill.cpp發現該路徑不存在，已查實際目錄並讀取src/prefill/prefill.cpp；沒有以其他版本檔案代替。
- 原live PID/binary/config/capacity在screen及audit前後gate一致；獨立final_verify與Git收尾receipt另存本目錄。新來源檔只限probe/report/handoff，未改engine source與live。

## 5. Checklist收尾
目標仍50；沒有新增整機速度，舊phase拆解不升格為現況。新screen不是已結案旋鈕重掃；失敗原因已量到(低壓縮率/慢解碼)，不擴成快取實作。GPU候選缺的是實際kernel收益及全消費者契約，不宣告整個無損layout方向無效。無subagent、無背景排程；本輪工作結束，不啟動下一個實驗。
