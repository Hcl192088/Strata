from pathlib import Path
import json,statistics as st
R=Path(__file__).resolve().parent;raw=R/'raw'
a=json.loads((R/'analysis.json').read_text());ex=json.loads((raw/'exactness.json').read_text(encoding='utf-8'));qa=json.loads((R/'qa.json').read_text());v=json.loads((raw/'independent-live-verify.json').read_text());camp=json.loads((raw/'campaign.json').read_text(encoding='utf-8'));restore=json.loads((raw/'restore.json').read_text());rows=json.loads((R/'rows.json').read_text());p=a['primary'];s=a['secondary']
lines=['[LUNA_REPORT]','','# SPEC_SPLIT A/B：完成，非候選','','TASK_ID：LUNA-20261012-027 continuation。STATUS：COMPLETED / REPORT_LOCAL；效能 verdict：NOT_CANDIDATE。TASK_SOURCE：2026-10-29 使用者直接 brief（Claude planner，授權「測」）；無新 GitHub claim，TASK_BRANCH／TASK_COMMIT_SHA coordination lock：不適用。依本次明確限制，無 source edits、build、live config 修改、commit、push 或 GitHub writes。',
f'',f'5 輪 C/S 全部完成，primary 按輪 S/C 平均 **{p["mean_pct"]:+.2f}%**，95% CI **{p["ci95_pct"][0]:+.2f}～{p["ci95_pct"][1]:+.2f}%（df={p["df"]}）**。未達平均 ≥+3% 且 CI 下限 >0 的候選門檻。前三輪非全負且平均 '+f'{st.mean(p["deltas_pct"][:3]):+.2f}% ≥−3%，所以未提前停止，按預登記完成 5 輪。',
'','## Identity 與 config audit','',r'- host 實讀：DESKTOP-LKMLUPC。canonical root：`C:\Users\User\Strata-Adrian-control`，junction 實體為 `C:\Users\User\Strata-Adrian\repo\Strata-Adrian-control`。',r'- 兩臂都用 `runs\native-pipe-deploy-prep-20261029\build\strata.exe`；SHA256：`'+v['binary_sha256']+'`。每 block 核對檔案與實際 engine binary。',r'- live config SHA256：`'+v['config_sha256']+'`；BEST.json 以 UTF-8-sig 讀取，每個 controller gate 重驗 binary/config 與 current-best manifest 相符。',r'- binary 對應 source：`C:\Users\User\native-pipe-generic-20261029`；commit/tag `f520bc5e9d31c93caeb296b059e3a3eaa16e493f`／`native-pipe-generic-20261029`，實讀 git status 無變更。canonical main HEAD `2f1e99872969c9b4586a2d41c7f1915f27e4f298`，已有 tools 修改與未追蹤檔，未處理。',
'- 正式 C＝live config；S＝同 binary、同 env、args 尾端只加 `--spec-split`。只允許 block log 路徑與 harness 設定 cwd；所有其他欄位逐一 equality audit。兩臂 PIPE=1、MT1=1；SMOKE/CHK 另有授權的 PIPE_CHECK=1。完整 config、args/env、input/harness hashes 在 raw/config-audit.json、inputs.json 與各 block command.json。',
'- 使用既有 Hermes 十題，max_tokens=512；沿用 harness greedy temperature=0，未改模型溫度或 live sampling。每 block fresh engine、AboveNormal；每 block startup 容量嚴格為 3153 slots／20.00 GiB／20479 MiB locked。',
'- 重用今日 PCIe controller/harness、scheduled-task detach、stop_api/finally restore_api/final_verify；只調整此實驗排程與單一 flag 的 config-copy wrapper，harness 增加實際 engine cmdline split 核對。不是 source 變更。',
'- 舊 `Strata-PCIE-Balance-20261029` 實讀 Ready、campaign DONE，於 old-task-cleanup.json 記錄後只刪該 task。新 `Strata-Spec-Split-20261029` 結束後保留 Ready，無仍執行 controller；未擅自刪除新 task。',
'','## SMOKE／CHK 與 split 啟用證據','','| block | 題目／上限 | 結果 | gu/down coverage |','|---|---|---|---|']
for arm,pts in [('SMOKE','p01/p05/p08 ×128'),('CHK','p01..p10 ×128')]:
 ch=json.loads((raw/f'check-{arm}.json').read_text());lines.append(f'| {arm} | {pts} | OK；零 bitwise mismatch、PIPE ACTIVE、無 fatal | {len(ch["seen"])} 組；missing={ch["missing"]} |')
lines += ['', '十組完整覆蓋：(16,20)、(16,42)、(17,20)、(17,42)、(18,20)、(18,42)、(21,20)、(21,42)、(22,20)、(22,42)。check summary 的 values 是累積 counter 相加，不當作不重複比較值總數。完整 engine logs 已下載並重新掃描 mismatch/fatal。',
'',r'對應 source `src/program/generate.cpp:1958` 解析 flag、`:7484` 將 o.spec_split 傳給 serve verifier；`src/core/verify.cpp:747` 為 Plan v0.3 P6 split 註解，record_window 的 `G=(split_ && T>=2 && !batch_rec_)?2:1` 並寫入 groups_[T]。每個 S/check block 的 meta.json 保存 engine 實際 command line，確有 `--spec-split`；C 沒有。',
'', '預設 log 沒有專用 split/group 標記；graph node 計數需額外 STRATA_VERIFY_NODES env，本次遵守設定差異限制而未加入，因此沒有 GPU graph count 實測。CHK p01 的 window timing：23 windows、avg T=1.74、63.96 ms/window、GPU-reach wait 4.99、CPU 50.81 ms/window。source 條件＋實際 runtime flag＋多 token window timing 支持 G=2 路徑已啟用；**G=2 是依 source/control flow 的推論，未以 group 專用 runtime counter 直接觀測**。split-active-SMOKE/CHK.json、split-source-evidence.txt 與 meta.json 保留此限制。',
'', '正式加權 GPU-reach wait：C 11.7888 → S 8.9628 ms/w；CPU：22.6725 → 24.7199 ms/w；tokens/window：1.9262 → 1.8659。這與工作分組改變相容，但輸出內容不同，不能把 timing 差值當成純機制收益或將 source 的 exact 註解視為本機證明。',
'', '## 正式 per-block pooled 指標','', 'pooled tok/s＝Σ metrics engine_generated ×1000／Σ metrics decode_ms；ms/window＝Σdecode_ms／Σwindows，tokens/window 同理。CPU／GPU-reach／experts 指標依 windows 加權，輸入為 engine timing 的四捨五入數字，故不是更高精度的原始計時。CPU experts 與 VRAM hits 是每層每 window 平均，不是不重複 expert 數。',
'', '| round | arm | tokens | windows | pooled tok/s | ms/w | tokens/w | CPU ms/w | GPU-reach ms/w | CPU experts/layer-w | VRAM hits/layer-w |','|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for b in a['blocks']:
 lines.append('| '+ ' | '.join([str(b['round']),b['arm'],str(b['tokens']),str(int(b['windows']))]+[f'{b[k]:.4f}' for k in ['pooled_tok_s','ms_window','tokens_window','cpu_ms','gpu_wait_ms','cpu_experts_per_layer_window','vram_hits_per_layer_window']])+' |')
lines+=['','## 逐輪 primary 與逐題 secondary','','| 輪 | 順序 | S/C Δ% |','|---:|---|---:|']
for rd,d in enumerate(p['deltas_pct'],1):lines.append(f'| {rd} | '+('C→S' if rd%2 else 'S→C')+f' | {d:+.4f} |')
lines += ['',f'Primary：五個配對輪次的百分比取算術平均；t={p["t"]:.6f}，df={p["df"]}，平均 {p["mean_pct"]:+.4f}%，95% CI [{p["ci95_pct"][0]:+.4f}, {p["ci95_pct"][1]:+.4f}]%。不以每輪十題當成 50 個獨立樣本。',
'',f'Secondary：每題先跨輪 pool tokens/time，再計算該題 S/C；十題平均 {s["mean_pct"]:+.4f}%，95% CI [{s["ci95_pct"][0]:+.4f}, {s["ci95_pct"][1]:+.4f}]%，t={s["t"]:.6f}，df={s["df"]}。secondary 不取代 ledger primary。',
'', '| 題 | C pooled tok/s | S pooled tok/s | S/C Δ% |','|---|---:|---:|---:|']
for q in s['questions']:lines.append(f'| {q["pid"]} | {q["rates"]["C"]:.4f} | {q["rates"]["S"]:.4f} | {q["delta_pct"]:+.4f} |')
lines+=['','## Exactness','','50 組同輪同題：reasoning＋content 完全一致 **0/50**；reasoning 一致 0/50、content 一致 37/50（包含兩邊皆空）。以下每格是 **reasoning 首差 / content 首差**，`=` 表示該欄位文字完全相同；數字是 zero-based token index。',
'', '以同一 server strata_tokenizer 與 live tokenizer files 將 API reasoning_content、content 各自重編碼後逐 token 比較；原始 engine token IDs、server 剝除的控制 token 未由既有 harness 保存，所以此表不是原始 engine 全 token 序列的 index。直接文字比較已足以證明這些輸出不 identical；每組首差 token ID/文字與 tokenizer hashes 在 exactness.json。**無法確認原始 hidden/control token exactness**；未因差異停測，也未改 tokenizer、溫度或 fallback。',
'', '| 題 | r1 | r2 | r3 | r4 | r5 |','|---|---|---|---|---|---|']
for pid in sorted({x['pid'] for x in ex['pairs']}):
 cells=[]
 for rd in range(1,6):
  x=next(x for x in ex['pairs'] if x['pid']==pid and x['round']==rd);z=[]
  for f in ['reasoning_content','content']:
   v0=x['fields'][f];z.append('=' if v0['identical'] else str(v0['first_differing_token_index_0based']))
  cells.append(' / '.join(z))
 lines.append('| '+pid+' | '+' | '.join(cells)+' |')
lines += ['', '未診斷輸出差異的根因：source 的 exact 註解未在此 live 設定下得到輸出一致證據；現有設定本來啟用 route-tail-skip，且同臂跨輪也有內容／長度變動。這些是歸因限制，不據此宣稱 split 算術有錯或擅改其他設定。',
'', '## Live finally 復原與操作紀錄','',f'- campaign phase={camp["phase"]}；completed={len(camp["completed"])} blocks（2 checks＋10 正式）；無 error；wrapper exit_code=0。restore 開始 {restore["started"]}，結束 {restore["finished"]}（桌機本地時間）。',
f'- controller final_verify 與後續獨立 verify 均成功。live PID {v["pid"]}；binary `{v["binary_sha256"]}`；config `{v["config_sha256"]}`；AboveNormal（32768）、loaded=true、3153 slots／20.00 GiB／20479 MiB；PIPE=1、MT1=1；實際 command line 無 `--spec-split`。',
'- API 停機與復原僅操作既有 API task 和經 command line 核對的 API processes；各測試 block 僅清理自身 server/engine。process gate 在 launch、pre-stop、after-stop、每 block、每 request、pre-restore 與收集前執行；保留 PID/name/command line 與 heavy RAM 觀測，未停止無關程序。',
'- 首次 launch 自動審查因推測會改寫 live config 而拒絕，該次未啟動。隨後唯讀核對實際 build_cfg/controller/restore_api，證明只寫 block config 副本、復原只啟動既有 task；提交同一動作及新證據後審查通過，正式 controller 只啟動一次。無繞路或 fallback。',
'', '## Coverage、未驗證與 raw paths','',f'要求範圍：SPEC_SPLIT 預登記 checks、5輪A/B、exactness、finally restore、report/ledger。本機已讀完整正式 rows（{qa["formal_rows"]} rows）、所有 {len(qa["blocks"])} 個 block configs/meta/startup/command、完整 engine logs 的必要 gate/計時輸出；對下載 raw manifest 的 {qa["manifest_files_verified"]} 個檔案核對 size/SHA256。全 50 組 API response 由 exactness script 讀取比較，非抽樣。config diff 與 priority/capacity 在本機再驗一次，qa.json 全通過。',
'', '摘要／局部閱讀：source 只檢查 flag parse、serve set_split、record_window/group 條件及 logging 路徑，沒有全倉庫 source audit；raw 自然語言 response 做程式化完整比較，未逐句人工語意審閱。大型 model/pack/build 不下載、不重 hash；保留既有 manifest 與路徑，未做 build 或效能 profiler。缺原始 engine token IDs／split group 專用 counter／graph count，限制如上。此結果只涵蓋這套 live binary/config 與 Hermes workload，不外推其他機器或設定。',
'', r'- 遠端權威 raw：`C:\Users\User\Strata-Adrian-control\runs\spec-split-20261029`；實體 `C:\Users\User\Strata-Adrian\repo\Strata-Adrian-control\runs\spec-split-20261029`。',
r'- 本機：`D:\strata\state\spec-split-20261029`；`rows.json`、`analysis.json`、`qa.json`、`evidence.zip`、`raw/`。',
'- raw 根目錄：controller.py、launch/wrap.ps1、campaign.json、rows.json、round-deltas.json、config-audit.json、inputs.json、checks、split-active summaries、source-identity/source-evidence、initial/final/independent verify、restore、old-task-cleanup、process inventories、raw-manifest.json。',
'- raw/out/block-00-SMOKE-r0、01-CHK-r0；正式 02-C-r1、03-S-r1、04-S-r2、05-C-r2、06-C-r3、07-S-r3、08-S-r4、09-C-r4、10-C-r5、11-S-r5；每個 block 包含 config／command／startup／meta／results／engine.log／tail-pXX.log／resp-pXX.json。',
'', '**判定：NOT_CANDIDATE；保留 live 原設定。** 沒有未完成測量或待復原事項；新實驗臨時 task 留在 Ready，沒有自動排程 trigger。']
(R/'RESULT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
