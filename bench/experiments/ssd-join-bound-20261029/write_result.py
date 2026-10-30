import json,hashlib,datetime
from pathlib import Path
O=Path('state/ssd-join-bound-20261029');a=json.loads((O/'analysis.json').read_text());p=json.loads(Path('state/overnight-20261029/phase_analysis.json').read_text());live=json.loads(next(l.split('FINAL_LIVE_JSON ',1)[1] for l in (O/'live-and-read-evidence.txt').read_text(encoding='utf-8-sig').splitlines() if l.startswith('FINAL_LIVE_JSON ')))
assert live['binary_sha256']=='385EF64EE24BDF3BD4B309264FA811901DF9256B92CE4589BAEC70B3F26B30F5'
assert live['config_sha256']=='F23F1AAD8E385987708D6DFB854AD139D513FE398151CCCC5FBD43CFE303EB6F'
assert live['health']['loaded'] and live['engine']['expert_slots']==3153 and live['engine']['arena_mib']==20479 and live['priority']['PriorityClass']==32768
lines=['[LUNA_REPORT]','','# SSD_JOIN_BOUND：CONTINUE（oracle 分析上限；Hermes 轉移尚未驗證）','','TASK_ID：LUNA-20261012-027 continuation。使用者直接授權分析；REPORT_LOCAL。無 GitHub、claim、Git、build、效能 A/B 或 source/config 修改。',
'','## 判定與適用範圍',
'',f"重用 Task027 完整 trace 與既有 OPT 結果；現行策略在**同一舊 trace** 的每請求 SSD bytes 最大誤差 {a['validation']['max_abs_error_pct']:.3f}%，通過預註冊 20% gate。強制 admission 的 Belady 省 bytes 比例 {a['policy_summary']['OPT_forced']['saved_fraction']:.3%}，乘 Hermes phase 的 issue_wait 比率得到 **{a['policy_summary']['OPT_forced']['conditional_phase_issue_ms_window']:.3f} ms/window**，高於計畫的 1.2 ms/window。機制是避免同層 RAM 容量循環造成的重讀。這是跨工作負載的條件式估算／oracle headroom，**不是 Hermes 已驗證上限或可達改善，也不是預測達到 50 tok/s**。", 
'', '停止規則：同 trace 模型未觸發 >20%；舊 trace oracle 未觸發 <1.2。故分析方向 CONTINUE；若要求「Hermes 同軌跡、同 current-best 的定量上限」則目前證據不足，不能給已驗證 CONTINUE。依「已有 trace/最佳快取上限則沿用不重做」，本次不再捕捉 Hermes，不把舊 trace 偷換成 Hermes。未新增門檻。',
'','## Live 與 trace identity',
'',f"遠端 hostname {live['hostname']}，核對時間 {live['time_utc']}；唯一 engine PID27444、AboveNormal（32768），health loaded=true；binary `{live['binary_sha256']}`，config `{live['config_sha256']}`。3153 GPU slots／arena 20479 MiB。config 維持 resident-budget=20 GiB、MT1=1，沒有 PIPE 開關；本次未讀取 engine 內部環境區塊，所以 inherited MT1 以既有部署證據與當前 config 為依據，未新做記憶體內環境驗證。API 未停止，無需 restore。", 
'', 'process gate：只見既有 API serve、memory-policy --run/--watch 的 venv/base wrapper pairs、engine，以及本次 SSH 診斷的 python；未見其他 Strata/Luna/build/benchmark。未停止任何程序。SSH hostname/strict host-key 通過；無持續連線故障。',
'',f"重用 `runs\\ram-policy-trace-20261018-162909\\capture-01\\routing-dump.bin`：63,947,136 bytes，SHA256 `{a['trace_sha']}`（遠端與既有本機檔本輪均核對）。726,672 records、8,623 windows、11 requests＝neuro 10×1024 + 1×4096；原 binary 366A…15E2，不是現行 385E。原 capacity gate 3153／20.00／20479。原 RAM-LRU runner 的六次比較沒有 dump-routing；後續 capture 與 warm 模擬報告已有完整 trace/OPT，故沿用。", 
'',f"容量釐清：3153 是 VRAM expert slots；RAM 是 {a['ram_experts']:,} 個依 layer blob 尺寸配置的 expert，實用 {a['ram_bytes']:,} bytes，不能用 20GiB/3153 定義 RAM slot。blob sizes（bytes）：{a['layer_blob_sizes']}。profile/native_experts.txt 本機與遠端 SHA 分別完全一致：AA28BA08…5829510F／AE28CF7A…7D462C0EE。",
'','## Q1：join 的確切意義',
'', '以下行號均指遠端 `C:\\Users\\User\\Strata-Adrian-control\\runs\\miss-overlap-20261027\\source\\`；build/CMakeCache.txt 的 CMAKE_HOME_DIRECTORY 已核對指向此樹。`src/core/expert_source.cpp` SHA256 F51BE9DE…259E485。',
'', '- `src/core/expert_source.cpp:3935–3956`：收集 CPU routes，prefetch_split_begin 分出 pending；有 ready CPU expert 才啟動 MissIo helper。',
'- `src/core/expert_source.cpp:3973–3985`：先 run_split_multi_native 計算 ready experts；rb→rc 僅包住 mo_join.join，累積為 join_ms。這不是 pool worker std::thread::join。',
'- `src/core/expert_source.cpp:3686–3689`、`:3633–3646`：join 等 helper 的 done acquire flag，採 pause spin；是 helper 完成同步。',
'- `src/core/expert_source.cpp:3669–3674`：helper 執行 prefetch_split_run，返回後才發布 done；`:1477` 進 fill_many；`:1518–1536` 包含 read_direct、stage publish 及可能的批次讀取 thread joins。',
'- `src/core/expert_source.cpp:1901–1924`：ReadFile 發出全部 requests，GetOverlappedResult 等完成，再 memcpy 至 stage buffers。故 join 可包含未遮蔽 SSD/OS I/O、copy、publish 與喚醒／排程延遲；不能全歸為 SSD device service。正式 native GU/quant/down 的其他 pool 同步不在這個 join counter。',
'', 'phase 診斷的計時邊界見 `state/overnight-20261029/prepare_diag.py`：issue_wait 包住 issue + GetOverlappedResult，copy 另計。helper/direct/copy/issue_wait 重疊，不能相加。原生來源可能讀 GGUF 分散角色 ranges，不應一律說是 experts.bin 單檔連續讀取。',
'','## Q2：Hermes phase 每 window miss 與 bytes',
'', '來源：`state/overnight-20261029/{rows.json,phases.json,phase_analysis.json}`，30 個 D requests 依順序配對並核對 windows。miss 取 decode 專用 m_file_blobs，未用包含 prefill 的 cumulative counters。下表是每題跨三輪加權平均；不是個別 window 的分佈。',
'', '|題|windows|SSD experts/w|useful MB/w|issued MB/w|join ms/w|issue_wait ms/w|','|---|---:|---:|---:|---:|---:|---:|']
for k,z in a['phase_by_point'].items():
 w=z['windows'];lines.append(f"|{k}|{w:.0f}|{z['misses_per_window']:.3f}|{z['useful_bytes']/w/1e6:.3f}|{z['issued_bytes']/w/1e6:.3f}|{z['join_ms']/w:.3f}|{z['issue_wait_ms']/w:.3f}|")
miss=sum(z['misses'] for z in a['phase_by_point'].values());lines += ['',f"總計 {miss:,} file blobs／2838 windows＝{miss/2838:.6f} experts/w；useful {p['useful_GB']:.9f} GB，issued {p['issued_GB']:.9f} GB＝{p['issued_GB']*1000/2838:.6f} MB/w。API decode file MB 合計 {sum(z['api_MB'] for z in a['phase_by_point'].values()):.1f}，與 useful 67,967.8464 MB 僅顯示 rounding 差；read amplification {p['read_amplification']:.9f}。join {p['components_ms_window']['join_ms']:.6f}、issue_wait {p['separate_overlapping_ms_window']['issue_wait_ms']:.6f} ms/w。每個具體 window 的 miss/bytes 無 Hermes trace，不能由平均值還原。",
'','## Q3：同 trace 現行策略與 Belady',
'', '重用 `state/ram-policy-sim-20261018/capture-01/warm_policies.json`；現行策略另用既有 simulator 重放，確認讀取數／bytes。既有模型包含 tail-skip、adaptive GPU exchanges、同層固定 RAM 與 LRU tie rule；假設 swap 下 window 已落地、prefill 後初態為 profile。OPT 是同一 filtered event stream 的 per-layer oracle；非全系統最佳調度證明。',
'', '|policy|RAM hits|SSD reads|RAM hit rate*|SSD GB|miss/w|省 bytes|','|---|---:|---:|---:|---:|---:|---:|']
for n,z in a['policy_summary'].items():lines.append(f"|{n}|{z['hits']:,}|{z['reads']:,}|{z['RAM_hit_rate']:.4%}|{z['bytes_rounded']/1e9:.6f}|{z['misses_per_window']:.6f}|{z['saved_fraction']:.3%}|")
lines += ['', '*分母為 distinct CPU-path expert accesses；不是每 token 全 routing 命中率；VRAM hit 與 tail skip 已先過濾。bytes 表格沿用既有 mb_req（0.01MB rounding），adaptive SSD reads 另列，沒有混入 CPU misses。',
'',f"現行策略本輪重放：{a['sim_reads']:,} reads，{a['sim_bytes']:,} useful bytes；與原 41009 reads 相符。逐請求 measured/sim MB 與誤差完整存 analysis.json；最大絕對誤差 {a['validation']['max_abs_error_pct']:.3f}%（20% gate 通過），逐請求均通過。adaptive 額外讀取：LRU {a['policy_summary']['LRU_engine']['adaptive_extra_reads']}、OPT forced {a['policy_summary']['OPT_forced']['adaptive_extra_reads']}、OPT bypass {a['policy_summary']['OPT_bypass']['adaptive_extra_reads']} blobs；既有 runner 未累計其 bytes，故省讀比例對這小部分不完整。",
'', '不能以 neuro 的總 bytes 和 Hermes 68.08 GB 直接比較 gate：請求長度、路由及 windows 不同。通過的是同 trace 的實測校驗；現行 MT1/Hermes 的模擬校驗未完成。',
'','## Q4：K=10 預取可預測性',
'', '本輪於既有 trace 做因果可用的簡單基線：①前一 verify window 最後一個 evaluated position 的同層 top10（request 邊界清空）；②當前 L 層 routed ids 頻次最高10個 expert index，直接猜 L+1 同 index。②無訓練／未偷看 L+1 labels；不同層 index 未必相關，這是弱基線。①不是已接受 token 的完整軌跡，含 rejected speculative positions，不能冒稱精確 previous accepted-token predictor。trace 沒有 layer hidden，沒有做「L hidden 跑 L+1 router」。',
'', 'precision/recall 對 next layer-window 的 distinct routed union；實際 SSD 估算先排除當下 VRAM/RAM 已有 experts。extra bytes 是預取後本 window 未用到的非 resident experts（假設完整 blob、無污染、無後續回收），未包含 4KiB 對齊／merge amplification；不是量測 I/O。prefetch 不改變重放快取狀態。',
'', '|predictor|events|precision|recall|SSD miss byte recall|extra GB|extra MB/w|rescued GB|','|---|---:|---:|---:|---:|---:|---:|---:|']
for n,z in a['prefetch'].items():lines.append(f"|{n}|{z['events']:,}|{z['precision']:.3%}|{z['recall']:.3%}|{z['byte_recall']:.3%}|{z['extra_bytes']/1e9:.6f}|{z['extra_bytes_per_window']/1e6:.6f}|{z['rescued_bytes']/1e9:.6f}|")
lines += ['', '逐層/window 的路由 union 與預取成本不是逐 token precision。沒有訓練其他 predictor、掃 K 或使用 held-out labels 排名。額外 bytes 可能遠大於 rescued bytes，故不得把 recall 直接當淨收益。',
'','## Q5：換算估計與 1.2 ms/window',
'', f"Hermes 實測比率＝8.016346582 ms/w ÷ (68.080484352 GB / 2838 w)＝**{a['estimate']['issue_wait_ms_per_GB']:.6f} ms/GB**。要抵 1.2 ms/w，相當省 {a['estimate']['required_GB_saved_window']*1000:.6f} MB/w，或 {a['estimate']['required_fraction']:.3%} 的 issue_wait 等量 bytes。此比率含 OS issue/wait 且與 CPU overlap，非 SSD bandwidth，也不是速度線性因果係數。",
'', '|mechanism|條件式 issue_wait 等量 ms/w|','|---|---:|']
for n in ['OPT_forced','OPT_bypass']:lines.append(f"|{n}|{a['policy_summary'][n]['conditional_phase_issue_ms_window']:.6f}|")
for n,z in a['prefetch'].items():lines.append(f"|{n}（不扣 extra 成本）|{z['conditional_phase_issue_ms_window']:.6f}|")
lines += ['', '真正 wall-time 可移除量受 join 上限 6.090162 ms/w 限制，而且需看預取完成時刻／CPU overlap；上述值只能作樂觀篩選。額外 I/O、cache pollution、future knowledge 不可實現部分均會降低效益。1.2 是計畫指定 gap，並未重新確認部署後速度；pipeline 尚未切換 live。',
'','## 若 CONTINUE，最小實作方向（只有描述）',
'', '避免直接移植 oracle。最小候選是同層 RAM admission／victim 選擇時使用可事先得知的下一次使用估計，保留既有 arena、容量與即時 admission 契約；先以 Hermes trace 校驗現行策略及該估計，再決定是否實作。簡單同 index 跨層與 previous-window 預取需先扣除 extra bytes，現有數據不足以授權上線。若下一步要嚴格重建當前 Hermes 狀態，最小診斷擴充是記錄 request/window/layer、路由、初始 RAM/VRAM membership、交換/落地事件及實際 SSD fill bytes；現有 --dump-routing 只記 ids/weights，沒有 hidden 或 tier masks。本次沒有寫 source、build 或新快取程式。',
'','## 來源、raw paths 與 coverage',
'', '- 遠端 source/build：`C:\\Users\\User\\Strata-Adrian-control\\runs\\miss-overlap-20261027\\{source,build}`。',
'- 遠端 trace、capture-manifest/result/capacity-gate、engine logs：`C:\\Users\\User\\Strata-Adrian-control\\runs\\ram-policy-trace-20261018-162909\\capture-01`。',
'- 遠端原 RAM-LRU 六次結果：`C:\\Users\\User\\Strata-Adrian-control\\runs\\ram-lru-20261013\\results.json` 與子目錄；pre-attention 的 accepted.pap / offline-budget 是不同研究資料，未混入本分析。',
'- Hermes phase raw：`C:\\Users\\User\\Strata-Adrian-control\\runs\\overnight-20261029`；本輪讀本機既有 phase receipts，未重新整批核對遠端 engine logs。',
'- 本機：analysis.json（含8623 windows逐一 miss/bytes）、analyze.py、analysis-stdout.json、source-inventory.txt、dispatch-trace.txt、helper-evidence.txt、live-and-read-evidence.txt、build-input-evidence.txt；以及既有 warm_policies.json、兩份 ram-policy 報告。',
'', 'Coverage：完整讀本機預註冊條目、followup、部署 RESULT、phase_analysis、30 D rows／30 phase receipts、舊 trace 全檔 hash與完整 strict EOF parse、全部 8623 windows；讀既有全部 policy summaries，現行策略重放，兩個預取基線全 events。遠端完整讀 AGENTS、active config、health/metrics、相關 process inventory、原 RAM-LRU results/capture manifests，指定 expert source/trace/helper/read 路徑與 build source pin；source 以關鍵區段讀取，非全 repo audit。首次 inventory 意外列到 pre-attention .venv 的檔名/大小，未讀依賴內容，該長 metadata 不用於結論；工具顯示截斷部分未當作已閱讀內容。大型 trace 留原遠端與既有本機檔，未新增下載／複製原始 trace；未讀 PAP payload、模型全檔、其他歷史 run 或全部 build logs。',
'', '剩餘盲點：舊 binary/neuro 與 current MT1/Hermes 的轉移、prefill 對初態、adaptive 落地時刻、stage-cache reuse、OPT 實作的同步／保護約束、adaptive read bytes、預取污染與 lead time。故 CONTINUE 僅表示 oracle 方向未被本輪排除，不表示已完成當前 Hermes 的 cache-policy 決策。',
'', '執行環境紀錄：遠端預設與 base Python 缺 psutil，初始唯讀檢查在 import 失敗；改以標準函式庫及既有 PowerShell process API 取得同項唯讀資料，未安裝或啟用任何 runtime fallback。本機預設 Python 缺 numpy，離線分析使用已有 numpy 1.26.4 的 Python3.12；未改 source/runtime。',
]
(O/'RESULT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
entry=f"\n- 2026-10-29 SSD_JOIN_BOUND 完成追加（REPORT_LOCAL；分析）：重用 Task027 63,947,136-byte／8623-window trace 與既有 Belady；同 trace 現行 SSD bytes 校驗最大誤差 {a['validation']['max_abs_error_pct']:.3f}% <20%。Hermes phase {miss:,} SSD experts／2838 windows，issued 68.080484352 GB、join 6.090162／issue_wait 8.016347 ms/w。OPT forced 省 {a['policy_summary']['OPT_forced']['saved_fraction']:.3%} bytes，按 phase 比率條件式估 {a['policy_summary']['OPT_forced']['conditional_phase_issue_ms_window']:.3f} ms/w >1.2，**CONTINUE 僅為舊 trace oracle headroom**；current MT1/Hermes 轉移未驗證，不代表可達速度。兩種 K10 預取 precision/recall／extra bytes 見 `state/ssd-join-bound-20261029/RESULT.md`。live PID27444、385E…30F5／F23F…EB6F／AboveNormal／loaded／3153／20479 核對；API未停，無新capture、source/build/config/git/GitHub 操作。\n"
with Path('state/EXPERIMENT_LEDGER.md').open('a',encoding='utf-8') as f:f.write(entry)
print('RESULT and ledger written')
