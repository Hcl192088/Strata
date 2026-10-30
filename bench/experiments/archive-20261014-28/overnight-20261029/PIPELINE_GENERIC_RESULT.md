# Generic native pipeline：五輪完成，尚不採用

2026-10-29 約02:28，Task027夜間直接授權continuation。Goal仍active，截止07:00。

## 實測結果

Hermes既有十點、max512、每block新引擎，C/O/P旋轉五輪，正式150請求（每臂50）。C是原MT1 SHA385EF64E…30F5；O與P同binary3F98913E…7230，只有STRATA_NATIVE_PIPE off/on。sampling/worker9/affinity all/路由與量化不變。

| 指標 | C原MT1 | O新exe關閉交錯 | P開啟交錯 |
|---|---:|---:|---:|
| 合併tokens/合併decode時間 tok/s | 46.95884 | 47.21754 | 49.37278 |
| 五輪rate算術平均 | 46.94964 | 47.22684 | 49.24583 |
| P逐輪rate | — | — | 51.1625 / 48.6956 / 47.6817 / 49.4586 / 49.2308 |

P/C按輪平均+4.8930%，95% CI+1.5721..+8.2140%；按題跨輪聚合+5.3964%，CI+2.9447..+7.8481%。P/O按輪+4.3475%，CI-1.1478..+9.8428%；按題+4.4185%，CI+2.5893..+6.2476%。O/C按輪+0.6034%，CI-3.0422..+4.2490%。按輪df4、按題df9；不能把150個request當150個獨立repetition。

結論：對原best的整體收益正面；與同binary off的primary按輪CI仍跨0，未滿足事前嚴格採用gate。P只有首輪51.16，其餘不能概括為穩過50。保留候選與完整證據、不promote、不以首輪最好值代替五輪結果。

## 正確性、容量與覆蓋

SMOKE3點128+CHK10點128；獨立原分段GU/quant/down reference比較至少906,705,920個float values，零bitwise mismatch，覆蓋實際descriptor全部十種gu/down pair。這是CPU expert row parity，不是完整生成文字逐字一致的證明；C/O/P輸出長度/window mix確有不同，來源保留。

另OD/PD各十點512診斷，不納入正式速度判定：weighted combined pool17.5222→15.4123ms/window，十題各自比較平均省1.33ms/w、兩題變慢。CPU23.8169→21.1455；join5.0800→4.6511；LRU1.1888→1.0446。單輪diag且window mix不同，不能把這些差分全視作因果收益。helper/direct/copy等重疊項另列，pipeline_ms獨立combined wall，未冒充GU。

audit.json已完整核對19個block的meta/config/全部engine log（1,307,971 bytes/10,998行）、150正式rows、13檢查及20診斷請求，共183請求。所有running binary/AboveNormal/3153slots/20.00GiB/20479MiB通過；除PIPE/CHECK/DIAG之外env與args全部相同；十個request檔SHA與mtime已保存，不輸出私人prompt。全部log無pipeline fatal/mismatch。未逐行審閱自然語言responses、未全面source audit。

## 目前remote狀態

native-pipeline-20261029/campaign.json DONE、error null、completed19、verified=true。controller25144已不存在。finally已恢復原MT1，final_verify PID7724、AboveNormal、loaded、binary385E…30F5、configF23F…EB6F，無PIPE/CHECK/DIAG/MT_MIN。下一次遠端操作仍要重盤點，不把PID當永久有效。

權威raw root C:\Users\User\Strata-Adrian-control\runs\native-pipeline-20261029。小型結果下載至本機pipeline-results/，analysis.json可用analyze_pipeline.py重算；audit.json含全block/config/log hash。不要重啟Strata-Native-Pipeline-20261029。

## 下一步決策

距07:00尚有約4.5小時，繼續一個不同的具體資料流策略：P-core優先GU、E-core維持down優先，保留全部worker/core pin與原down cap3。新策略只改ready task的選取優先序，仍work-conserving，不掃quota。先補DIAG-only每worker GU/down work counters與actual CPU ID，驗證假設不是憑空歸因；同樣以原分段bitwise checker驗證十pair。正式新C/G/R五輪中C仍是385，不把尚未採用3F冒充current-best。G（新binary generic）也能作先前正面P/C的獨立確認，R/G才是role策略增益。

這個角色假設尚未證實：現有generic code所有worker先搶ready down，快P可能佔down、E仍GU；static source支持可能性，沒有每worker實測，不能稱已找出根因。實際topology/pin不符須停，不fallback。當前canonical main6251與build base61b raw hash不同，若最後採用要用精確base worktree/source commit/tag與build identity，不覆寫main或兩個無關dirty tools。Git pin/commit/push留待實驗收斂，不在A/B中build或checkout大量source。
