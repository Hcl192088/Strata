# 下一個可執行工作：native GU/down pipeline

**02:28最新：generic五輪DONE，runner25144已退出、MT1已復原。先讀PIPELINE_GENERIC_RESULT.md，接著才是下方的條件式role-priority新候選；01:38的live字樣只是歷史，不可繼續等舊PID。**

**01:38更新：本文件下方設計已實作，不要重做。** 唯一live runner為remote `runs/native-pipeline-20261029/controller_pipeline.py`，PID25144/create1793208778.8993585，排程Strata-Native-Pipeline-20261029。campaign.json已記SMOKE3點及CHK10點OK，兩者missing format pairs均空，bitwise獨立reference通過、actual overlap_down_tiles>0、3153/20.00/20479 strict capacity。正在OD（新exe PIPE off DIAG on）→PD（PIPE on DIAG on）→C/O/P五輪正式A/B；沒有promotion。已實測live PID，不重啟。所有可重用新程式在本機controller_pipeline.py、pipeline-harness、prepare_pipeline.py、pipeline-patched；remote同root/harness與patched。

candidate SHA3F98913EDB0B01D5D5DD3282412725141C298BF5CC9E890DD286AA0720C27230；pool.cppAF976BB39DE0A47F68B559FDF985677CA46B17D7D83D50F92307A94B194E9453／pool.hpp8B993048979A551B885313F85853C157FED1C13AA4DE5EBA1E9B15D284216351／generate1F17C2E537DA102F4E4AA1D58F25C4DC083AEEA853369D979E23D5EB50E1B24B。expert_source還原DIAG2294，不含shadow實驗；原best/live source沒改。增量build exit0、舊DIAG C7F4 exe與source快照皆保存。

新增CPU_PHASE_DECODE的pipeline_ms是GU+quant+down重疊後combined wall，CPU守恆須加上它，不能冒充GU。SMOKE175windows：pipeline21.773ms/w、reference GU+Q+down22.312ms/w，但兩者順序/cache不同且CHECK額外重算，不是效能結論。正式評估要用rows.json/comparison.json的C/O/P配對；OD/PD機制另列。SMOKE確認超2.5億float values，全部零mismatch；完整CHK也通過，十種實際descriptor pair已覆蓋。

2026-10-29 約01:20，夜間goal active，截止07:00。上一輪有實際進度：精確phase完成；shadow方向被實際來源推翻並停止，非阻塞。

## 已核對狀態與不能重跑的事

unmapped-shadow-20261029/campaign.json FAILED，第一個BAD_PATH即停止；controller18972已退出，沒有正式性能樣本、沒有fallback。final_verify verified=true，MT1 API PID32084已恢復（其父server23300/23376、memory-policy17028/27860，watch30620/25496；每次操作仍須重新盤點）。原best binary385E…30F5、configF23F…EB6F不變。候選9268…8C42不採用。

真正CPU來源是pack/iq3_xxs/experts.bin，42,912,972,800 bytes。native_experts.txt仍描述GGUF offsets，但FileExpertSource::open優先使用存在的experts.bin；不能拿註解或--native路徑代替實際來源。Generate既有6704..6710預設drop_mapping，當前config沒有KEEP_MAPPING、實際API engine.log明確「mapped view … is closed」。因此微基準的mapping優勢已被current best實現，不能再拿來推候選收益。

錯誤建立的47GB GGUF shadow已按copy.json、檔案長度/非reparse、terminal runner核對後，僅刪除自己本輪建立的first-shard.direct；discarded.json留存，回收47,039,860,736 bytes，C free69.13GB。原始模型/pack沒動。未刪其他artifact。不要再啟動Strata-Shadow-20261029或重新複製GGUF。

## 目前有用的量測

Hermes D30requests/2838windows：CPU24.4965，GU11.8793，down5.1629，quant0.1438，join6.0902，LRU1.1957，殘差0.02459ms/window。GU含worker/記憶體stall，不是純解碼指令。要從46.97到50需約2.47ms/window；combined GU+down17.04需約14.5%縮時。理想完全重疊上限5.16ms，但真實受共享RAM頻寬/核數限制。LRU單項上限1.20不足差距一半，不單獨做長A/B。

## 已定位的source，勿重做探索

實際remote isolated source：runs/overnight-20261029/source。pool.cpp原始SHA4A7AE645E2D494F465772397724EE3290130F1A9CBD56E6D653939D5AF03650A，遠端GetItem/hash及SCP已核對；本機只保存src/pool.cpp供修改分析，不是權威來源。

- pool.cpp run_split_multi_native 761..791：每batch先run_phase(5,GU row tasks)，host逐expert/token量化，再run_phase(6,down row tasks)，三段全域barrier。
- native row kernel實作630..665：GU q2/native_gu_rows，down q2/native_down_rows。保留同kernel、同bytes、同per-row math。
- begin_batch約551，claim使用head_打包epoch/njobs/next，done_；run_phase在drain後等park，需讀其完整短方法再改。
- pool.hpp私有state約280..306：SplitBufMulti包含ff[MAXT][FF]/a2/hq，mjobs_、nfmt_、mrows_、mtasks_，固定kMaxSplitMulti buffers。
- worker約490，drain約600（下一步精讀完整drain/run_phase短段，非全repo掃描）。

## 最小結構候選設計（尚未實作，先登記再測）

增加opt-in STRATA_NATIVE_PIPE=1，不碰worker數/affinity/spin，也不改路由或GPU集合。每expert的GU tiles完成後，最後一個完成者量化該expert，再發布其down tiles；其他expert GU可繼續。所有expert down完成才能返回layer。

可使用mode7：run_phase發布n_workers+host個drain token；每token進共享pipeline scheduler，消耗ready down tiles或未執行GU tiles，直到全部down完成，外層done_仍按token計數。每expert原子gu_left、ready、down_next，加全域gu_next/down_done。gu_left最後fetch_sub(acq_rel)取得其他GU tile寫入，量化後ready.store(release)，down用acquire，down_done release/acquire保證輸出可見。禁止任何worker把未完成的ff交給quant/down，禁止改共享mrows_/nfmt_等到workers全park。

注意只把所有GU先claim完、再claim down，只能重疊GU尾巴，不是完整交錯。若down ready就讓所有worker搶down，又可能退化成幾個expert一批；須從第一性原理考慮保留GU進度與down頻寬的並行份額，不能盲掃配額。可先固定小down並行上限，或利用已存在P/E topology讓較弱GU核心做down；要先看現有worker pin/topology，不另建抽象層。這是結構假設，不可把固定份額當已知最優。共享RAM/AVX爭用可能使整體更慢，按停止條件接受負結果。

盡量不重構原mode5/6；新scheduler可沿用同native row kernel呼叫。default-off控制臂驗證新增binary本身開銷。新counter ms_multi_pipeline單獨列combined wall，不能塞進GU讓報告誤稱純GU；若新增diag欄位，snapshot/printf/analyzer同步納入CPU守恆。

正確性要有獨立reference：STRATA_NATIVE_PIPE_CHECK=1下每個native batch pipeline後保存所有out rows，再跑原有分段GU/quant/down路徑比較（遞迴guard或抽出原路徑均可）；bitwise比較預期可過，任何mismatch立即停、無數值容錯fallback。這比MISS_OVERLAP_CHECK重要，後者兩次都走新pipeline不能單獨證明其正確。先3點128tokens檢查涵蓋各layer type，再正式十點。

## 可重用harness與工程經驗

本機shadow-harness/replay_ab_20261027.py已改為health loaded後、第一request前核對running SHA/owner並set AboveNormal，每request再驗；這部分可重用。移除/改掉DIRECT_SHADOW專用env斷言與FATAL字串，不可直接帶錯env。next_steps_ab_20261018.py是MT1 identity copy，stop_api只核對idle與PID/command才停，finally restore_api已有實測成功。

controller_shadow.py是已結束候選專用，不能改campaign.json重跑；新root/new state/new task，不保留舊shadow身份。借用其hard deadline/watchdog/strict capacity/五輪C-O-candidate旋轉、前三輪一致負停止、結果持久化。不要為測試重新寫一套API協議。

增量build可用原overnight build；先保存原DIAG C7F4 exe並記source快照。初次PS Start-Process.WaitForExit的ExitCode是null，雖build100%仍誤判；已用既有venv Python Popen拿真exit_code=0解決。不要再用那個PS ExitCode取法；不要誤用system Python（沒有psutil）。既有venv路徑在harness.PY，VS2022/cmake命令在build-shadow.cmd。build與benchmark分開；新測試務必保存actualcandidate SHA且basename strata.exe（否則process/priority gate漏認）。

## 接續順序

1. 重新process/MT1 binary gate，確認source/header hash，針對drain/run_phase/topology短讀。
2. 登記pipeline假設/上限/固定策略/停止條件，實作與bounded check；不再研究shadow/磁碟副本。
3. 保留已接受FP順序差異界線，但以同row bitwise reference作強驗證；測不過就修上游排程/同步，不放寬容錯。
4. check過才C/O/P交錯A/B，足夠輪數判定；時間到前恢復MT1，紀錄實際結果。當前時間還約有5小時，不因一個候選失敗把目標縮成只有報告。
5. 最終task-scoped remote report/patch/handoff commit並正常push一次；已知wincredman問題不得認證fallback/重試打轉。GitHub outbox仍只connector兩階段，無connector就REPORT_LOCAL。

## 01:46 計時已完成，正式A/B正在跑
OD/PD各十點DIAG完成、CPU守恆通過。本機pipeline-results/phase-OD.json與phase-PD.json、analysis.json可重算（analyze_pipeline.py）。OD908 windows：CPU23.8169，GU+quant+down17.5222，join5.0800，LRU1.1888ms/window。PD900 windows：CPU21.1455，pipeline15.4123，join4.6511，LRU1.0446。weighted pool約省2.11ms，但十題各自比較後平均只省1.33ms/w，兩題變慢；輸出長度/window mix不同，不是性能定論。所有overlap helper項另列、不加到CPU。
正式block4 C-r1已完成，block5 O-r1正在跑，controller25144/creation1793208778.8993585於01:46:24即時確認live且無error；還沒有完整C/O/P配對輪，不能下速度結論。正式rows.json將由runner逐block原子落盤，comparison.json逐完整輪更新；五輪或預登記negative gate後才總結。新analyze_pipeline.py會同時算按輪df4及按題跨輪聚合df9 CI，避免pooled輸出長度mix誤導。不要重啟或插入其他GPU/RAM/SSD測試。

## 採用前的source pin提醒（條件式，A/B尚未完成）
01:55左右只讀核對canonical Git：main HEAD6251a722f9c98fbfde3465cb5f4639de589a008b；tracked dirty僅tools/run_mtp_depth_20261014.py與tools/run_task027_ram_lru.py（非本輪，勿動）。canonical pool.cpp EADD0793…3F2B、pool.hpp0080CB68…BAE、generate46D97566…D18F、expert_source9A297E29…CD9、headerE176F315…C4F6，與本輪build基底raw hash不同，內容等價尚未建立。**不要把舊source檔直接蓋到canonical main。**
若五輪正面，採用前需依remote AGENTS把精確source commit/tag與manifest釘住。原build base是61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406，原MISS source工作樹（不是本輪copy）仍可用Git diff查看其私有expert_source.hpp/cpp變更。可在canonical repo內建立該base的獨立worktree/分支，保存所有實際candidate差異（包含DIAG header、generate、pool及基底private header/cpp），保護main與兩個dirty tools；要證明完整編譯source/依賴內容一致，不只三個pipeline檔。新commit應記測試binary3F與實際build source/flags/dep identity。fresh rebuild若binary不同，不能直接拿舊3F成績當其驗證；需要以3F作bridge或原385作anchor做受控比較後才部署。這段尚未執行，不能稱reproduced/pinned。
current MT1 baseline385仍全程由runner每block hash核對；不可因準備Git pin而在A/B進行中build/checkout大量檔案或修改原source。先等現有runner完成並復原API，再做有必要的後續。GitHub source正常push與outbox connector兩階段是不同流程；不要用token/REST/gh fallback，已知wincredman問題不打轉。

## 條件式下一個結構候選，尚未登記/實作（不可中斷現有五輪）
若generic pipeline五輪仍約49或增益不穩，可研究task-type priority，而非掃worker/affinity。現有drain_native_pipe對所有core都先搶ready down，固定down cap=threads/3；快P-core可能搶到down、較慢E-core仍做GU。這是static hypothesis，尚無每worker實測，不能當已證根因。既有Windows detect_cpu_topology(All)在hybrid上已按efficiency降序排序，再去掉host；本機6P+4E，workers先5P後4E，host預留P。可重用這個既有topology、保持原pin與worker數、保持原cap3，只讓P-worker優先claim GU、E-worker仍down優先；沒有可claim GU時P仍可做down，無down ready時E仍可做GU，保持work-conserving。這是新pipeline的工作型態分配，不改輸出/路由/量化，不能用舊單phase cost rebalance的負結果直接代替實測。
若做此候選，先用新binary ROLE-off/ROLE-on相同DIAG加每worker GU/down tiles與busy時間（thread-own cacheline counters，僅DIAG開啟）確認工作分配機制，標清thread-sum不是wall、whole-request不是decode-only。列出actual CPU ID與原topology；不能假設pin成功或新建硬體偵測抽象層。嚴格不支持的topology須停而非fallback。用同一舊分段bitwise checker覆蓋十pair後才C（原385）/O（新exe PIPE on、roles off）/R（同新exe PIPE+roles on）五輪。原3F只是未採用候選，不可先把它當current-best替代385 identity gate。這個方案尚未授權外的新功能，屬原夜間效能範圍可自行判斷；啟動前要重新登記具體上限/固定策略/停止條件，不盲掃cap。若generic已穩定達標且採用證據充分，優先source pin/部署/驗收，不為填滿7點追加候選。
