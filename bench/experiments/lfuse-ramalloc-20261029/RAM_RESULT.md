[LUNA_REPORT]
TASK_ID: LUNA-20261012-027
STATUS: COMPLETED
TASK_SOURCE: branch
TASK_BRANCH: coordination/task-027-file-tier-reuse-20261012
TASK_COMMIT_SHA: da28699a382304ec8afc87a547f9c37123985f77
BENCHMARK_RAW_PATH: NONE (local replay of preserved remote trace; no new engine run)

# 跨層 RAM 配額離線篩選：本輪不進實作

- 舊neuro trace完整8623 windows／11 requests；request0-4訓練選配額，5-10保留驗證。單一prompt重複，非Hermes/current-best實測。
- 固定既有adaptive GPU event stream、tail-skip與engine-exact LRU touch/tie-order/routed-protection/exchange語意，只改各層固定RAM配額／profile prefix。新vectorized simulator完整重現原11請求的reads與adaptive SSD counts，沒有改淘汰策略來混入收益。
- 每層容量grid16slots加baseline/max，動態規劃依miss bytes選擇；相對baseline的bytes增量向上取整到MiB，保證實際總bytes不增加。這是有限grid與保守離散預算模型，非所有allocation策略的全域上界。

| 結果 | SSD bytes減少 |
|---|---:|
| 前5請求選配額，在後6請求驗證 | 14.1055% |
| 同一配額，全11請求 | 17.8476% |
| 事後用全11請求選配額（保守DP模型、in-sample） | 18.6909% |

未過預註冊held-out>=25%門檻，判定NO_GO_BOUNDED_SCREEN，不改live RAM配額。SSD bytes降低不等於decode時間同比例降低；若僅為說明而套舊pipeline join約4.65ms/w，14.1%也只有約0.66ms/w的條件式量級，不是實測可省時間，且此時間拆解對現行build已過期。

Coverage：48層全部有限容量曲線；完整63,947,136-byte trace嚴格解析／hash驗證；全部11 baseline reads/adapt counts精確比對；兩組DP配額皆驗證實際bytes<=baseline。64.09秒完成。輸入、配額、per-request reads/bytes、curves與程式保存本目錄。

限制：只有舊neuro同題重複，沒有新Hermes trace或即時GPU/RAM state；未模擬跨層動態遷移成本／metadata／初始prefill影響；不包含grid間的所有整數容量，DP保守rounding可漏掉更佳可行配額；沒有新的模型tok/s／品質評估或source修改。因此結案範圍是本輪低成本配額篩選，不宣告所有跨層RAM管理無效。
