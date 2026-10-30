# Hermes MT1 CPU 段：既有 log 離線拆解

日期：2026-10-29 Asia/Taipei。僅本機既有資料；未SSH、未改程序/服務/設定、未跑模型/benchmark。使用專案 strata-checklist。來源與全部數值見同目錄 JSON；可重算 `python D:\strata\state\iq3s-mt1-ab-20261028\decompose_cpu_offline.py`。

## 結果與語意

| 每window（以windows數加權） | MT1 | 語意 |
|---|---:|---|
| decode CPU timer | 23.903 ms | decode-only counter delta，含重疊pass 1計算、join、pass 2、LRU等 |
| sampled join | 約6.326 ms | 全request verifier helper累積計數按最後樣本作差，再除decode windows；**不是已分離prompt的精確decode計時** |
| CPU減sampled join | 約17.577 ms | 近似非join剩餘工作；不能叫純解碼 |
| helper run | 約10.133 ms | prefetch_split_run的helper執行緒時間，包含讀取/拷貝/管理；會和compute重疊，不能再加到CPU |
| ready expert pass | 約4.368 ms | 整個resident第一pass計算，不是read/compute真正交集時長 |

MT1全100請求9470 windows；CPU所算expert數按window加權為6.029/層-window。8.3是特定短請求值，不代表整組Hermes。CPU wall約82.60us/expert亦包含等待，不能當kernel latency。

decode file stats：114798 blobs／211175.5 MB，約12.122 blobs、22.299 MB/window。從engine log全request累積差分得到2817252 MB，是前者13.34倍；因含prefill讀取，不能拿它估decode SSD成本。

S2K/MT1/S2KB的CPU timer分別25.925/23.903/27.568ms/window，sampled join為6.102/6.326/6.987，非join剩餘19.823/17.577/20.581。各臂輸出、windows與cache軌跡不同，不能將這些差值視為同輸入kernel的因果改進；既有按輪A/B仍是速度證據。

## 邊界與source驗證

- `expert_source.cpp` 本機patch3 SHA F51BE9DED69C50CBEAEFEF05A922A3B63D2AF0B4190AE489E519D2C29259E485，與先前實際S2K來源核對值一致。c2/c3/c4及mo_ms證明：ms_jobs=(c3-c2)-mo_ms；ms_run=(c4-c3)+mo_ms。mo_ms包含resident計算與join。inline同步讀發生在jobs，時間沒有獨立記錄，不能把所有SSD等待都放CPU。
- helper_read計時包住prefetch_split_run，不是磁碟裝置service time。compute_while_read只是ra到rb的resident計算時間；不保證helper整段仍在讀，不能算helper_read-compute_while_read當純等待。
- progress只在split_calls=1 mod64時印出；末尾尚有0..63個split call未打印，時長未設可證上界。carry-last-sample差分有request歸屬誤差。
- p02..p09共80請求的**全request counter**單調邊界帶為6.283..6.431ms/window，這是取樣邊界範圍，不是統計CI，也不是decode-only界線。
- generate.cpp的DecSnap ds0在decode開始才截，且DONE file bytes/blob也在此截。相反MissStats沒有ds0；read_windows可以處理prompt短段且呼叫相同win_pool_fn，因此可能有prompt verifier污染。沒有counter快照與prompt window標記，不能離線精確扣除。不能用neuro比例補齊，也不補造時間戳。

## 每題MT1近似量級

| point | CPU ms/w | sampled join ms/w | 非join剩餘 ms/w | decode file MB/w |
|---|---:|---:|---:|---:|
| p01 | 40.800 | 16.177 | 24.623 | 58.624 |
| p02 | 20.952 | 4.838 | 16.114 | 14.461 |
| p03 | 35.469 | 12.231 | 23.238 | 45.980 |
| p04 | 26.879 | 7.336 | 19.542 | 30.841 |
| p05 | 19.857 | 4.223 | 15.634 | 14.619 |
| p06 | 29.827 | 7.731 | 22.096 | 33.785 |
| p07 | 29.655 | 9.073 | 20.582 | 29.497 |
| p08 | 22.789 | 4.959 | 17.830 | 18.052 |
| p09 | 22.200 | 7.776 | 14.424 | 19.820 |
| p10 | 19.727 | 4.275 | 15.453 | 13.459 |

CPU/w vs decode MB/w相關0.930、sampled join/w vs decode MB/w相關0.829。這是描述，不是SSD的因果占比：CPU expert量、型別、T、prefill/cache軌跡與題型同時變化；不從它擬合出「每省1GB必快幾tok/s」。

## 對下一步的判斷

1. 接受修正：不再把23.9ms稱純IQ解碼，不以neuro的pool13ms外推Hermes；撤回把不膨脹的IQ重排列為足以補滿差距的優先押注。
2. 尚不能誠實回答「純IQ解碼幾%、純SSD等待幾%」；目前只能觀察helper join約6ms/window級，非join約18ms/window級，且join有scope誤差。亦不能反過來宣稱SSD主導整個CPU段。
3. 補滿到50需約2.475ms/window。即使近似17.577ms的非join部分全都可優化，也需縮時14.1%（該部分吞吐提升16.4%）；真正IQ解碼只占其中一部分，所需提升更大。IQ2_S/IQ2_XS小改估0.3..0.5ms不足單獨補滿，不排長A/B。
4. 下一個必要診斷是**保持MT1設定**，在decode開始/結束各截helper join/read/inline計數與pool GU/quant/down快照，再報逐request delta；需要時才把inline read、LRU/copy時間補上。這能直接回答本輪缺口，不先做完整pipeline、IQ新格式或GPU融合。使用者遊戲期間不執行；未把此文件當新遠端授權。
5. IQ紙上表格需分開「code數值部分」、「完整gate/up block」、「整expert含down」三種膨脹率；+33%/+100%不直接套整20GiB arena。現有微基準是已測寫法的結果，不是所有同格式實作的數學上限，但也沒有證據承諾新寫法的大收益。GPU排在精確CPU拆解之後，21%門檻只作篩選。

## Checklist逐題

1. 50 vs既有46.9715tok/s，差1.2895ms/token；不是即時流量測速。
2. 使用10/28 MT1自身replay，不將neuro細分比例移植；decode CPU23.903、GPU-reach11.769、jobs0.275、draft1.825ms/window。
3. 本輪釐清CPU內I/O/非I/O；不能將含重疊的helper時間歸零計Amdahl。CPU全歸零算術上限113.20tok/s但非可達；小kernel項需其他段合力，單項不足。
4. 無新旋鈕/模型試驗，只對既有30block完整離線重算；不以重複掃參數補資料缺口。
5. 不重做PIN/AA/PATCH4、worker/affinity、MTP gate。沒有拿舊失敗當所有結構方向的反證。
6. miss/預讀先看精確stall，placement受tail-skip約束，重疊受共享資源約束，減少驗證量已有反例，mainline目前無新Windows/Qwen勝出證據；GPU融合先排後。
7. 最新失誤在計時語意與工作負載外推，已追source修正；不改最終表格掩蓋原計數無法分離prompt/decode。

第2節：沒有開A/B或benchmark，不登虛構實驗。第3節：沒有遠端工作、沒有agent；不查/停使用者桌機程序。第4節：已完成本輪現有log拆解；待辦改為decode邊界快照，IQ新格式/GPU融合延後，不再重做部署/認證。

## Coverage

完整處理300 rows、30正式block各meta/config/engine.log、300 request tail；所有tail的progress合併後逐項等於engine.log全部progress；1+64n步距、全部計數單調、無check_bad、三臂env/SHA/meta狀態皆核對。MT1 probe不屬100正式請求，明確排除。source僅targeted核對已保存patch3計時與generate的DecSnap/prompt windows/DONE欄位，generate為診斷快照而非新拉遠端source。未逐行讀全部自然語言輸出/私人prompt、未全面source audit、未實測SSD service、未做新phase profile或遠端驗證。大型原始log留在原位置，無截斷解析、無抽樣丟列。
