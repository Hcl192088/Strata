import json,datetime as dt
from pathlib import Path
R=Path(__file__).resolve().parent
a=json.loads((R/'analysis.json').read_text(encoding='utf-8'));s=json.loads((R/'campaign.json').read_text());audit=json.loads((R/'audit.json').read_text(encoding='utf-8'));vf=json.loads((R/'final_verify.json').read_text());compat=json.loads((R/'compatibility.json').read_text())
assert s['outcome']=='PASS' and not s['round8_ran'] and audit['verified'] and vf['verified'] and compat['verified']
assert a['primary']['mean_pct']==json.loads((R/'comparison.json').read_text())['mean_pct']
def local(t):return dt.datetime.fromisoformat(t).astimezone(dt.timezone(dt.timedelta(hours=8))).isoformat()
lines=['[LUNA_REPORT]','', '# NATIVE_PIPE_PO_CONFIRM：PASS','',
'TASK_ID：LUNA-20261012-027；使用者今日「同意」授權的 continuation，無新 claim。本次未操作 GitHub、remote git、source、模型或 current-best 部署。','',
f"執行時間（台北）：{local(s['started_utc'])} 至 {local(s['ended_utc'])}；首次遠端 hostname／程序盤點時間 2026-10-29T08:29:16+08:00。原 API 正在生成時沿用 harness 等待 idle，08:34:51 停機後 process gate clean。",'',
'已驗證 hostname：DESKTOP-LKMLUPC。canonical root `C:\\Users\\User\\Strata-Adrian-control` 是 junction，實際指向 `C:\\Users\\User\\Strata-Adrian\\repo\\Strata-Adrian-control`。','',
'Identity：', '',
f"- live current-best binary SHA256：`{vf['binary_sha256']}`。",
f"- 原 API config SHA256：`{vf['config_sha256']}`。",
'- O/P 共用 binary SHA256：`3F98913EDB0B01D5D5DD3282412725141C298BF5CC9E890DD286AA0720C27230`。',
'- 啟動前 API engine PID 23540；API launcher/server/memory-policy 父子程序及 watch 均依名稱、PID、command line 分類，無未分類 Strata/Luna/benchmark/build 程序。Razer RzDiagnosticService.exe 為無關既有服務，未停止。每 block 與每 request 沿用原 process gate；其餘大 working-set 程序僅記錄。',
'- 沿用遠端原 harness，全部 Python 檔 SHA 相同；十個舊 O/P meta/config 全核對，完整 config 除輸出 log 路徑外相同。十題輸入 SHA 與原 audit 相同。',
'- Hermes 十題、max_tokens 512、每 block 新 engine、workers 9、affinity all；溫度及 sampling 完全沿用原 harness（原值 temperature=0），沒有調整。每個 engine 第一請求前設定 AboveNormal、每題重驗；容量嚴格 3153 slots／20.00 GiB／20479 MiB。',
'- 只有 O/P，無 C、SMOKE、CHK、OD、PD；無啟用 PIPE_CHECK／DIAG。既有停用的 STRATA_RAM_LRU_CHECK=0 原樣保留。','',
'新增 block pooled tok/s = Σ engine_generated ×1000／Σ decode_ms：','',
'| 輪次／順序 | 臂 | tokens | decode ms | windows | pooled tok/s |',
'|---|---|---:|---:|---:|---:|']
for rd,arm in [(6,'O'),(6,'P'),(7,'P'),(7,'O')]:
 b=next(b for b in a['blocks'] if b['round']==rd and b['arm']==arm)
 lines.append(f"| {rd} | {arm} | {b['tokens']} | {b['decode_ms']:.1f} | {b['windows']:.0f} | {b['pooled_tok_s']:.8f} |")
lines+=['',f"逐輪 P/O（%）："+' / '.join(f'{x:+.6f}' for x in a['round_deltas_pct'])+'。', '',
f"Primary：七輪配對百分比的算術平均 **{a['primary']['mean_pct']:+.6f}%**，95% t-CI **{a['primary']['ci95_pct'][0]:+.6f}% 至 {a['primary']['ci95_pct'][1]:+.6f}%**，df=6，t=2.446911851。輪次是 repetition，未將 140 題當成獨立樣本。",'',
f"Secondary：每題先跨七輪合併 tokens/decode time，再算 P/O，十題平均 {a['secondary_point_pooled']['mean_pct']:+.6f}%，95% t-CI {a['secondary_point_pooled']['ci95_pct'][0]:+.6f}..{a['secondary_point_pooled']['ci95_pct'][1]:+.6f}%（df=9）。沿用舊分析『每題逐輪比值平均，再跨題』方法則為 {a['secondary_original_method']['mean_pct']:+.6f}%，CI {a['secondary_original_method']['ci95_pct'][0]:+.6f}..{a['secondary_original_method']['ci95_pct'][1]:+.6f}%（df=9）；兩者均為次要指標。",'',
'跨日漂移（各 block pooled rate 的算術平均；新第6–7輪對舊第1–5輪）：','']
for arm,d in a['drift'].items():lines.append(f"- {arm}：舊 {d['old_round_mean']:.8f} → 新 {d['new_round_mean']:.8f} tok/s，{d['change_pct']:+.6f}%。")
lines+=['','輸出長度／windows：','', '| 區間／臂 | requests | tokens | windows | tokens/window |', '|---|---:|---:|---:|---:|']
for k,v in a['length'].items():lines.append(f"| {k} | {v['requests']} | {v['tokens']} | {v['windows']:.0f} | {v['tokens_per_window']:.6f} |")
no=a['length']['new_O'];np=a['length']['new_P']
lines+=['',f"新增 P 比 O 少 {no['tokens']-np['tokens']} tokens（{100*(np['tokens']/no['tokens']-1):+.4f}%）、少 {no['windows']-np['windows']:.0f} windows（{100*(np['windows']/no['windows']-1):+.4f}%）。輸出/window mix 不同，且兩臂絕對速率均有負向漂移；未確認漂移成因，不把速度差解釋為固定相同輸出的純 kernel 收益。",'',
'停止規則：第7輪均值 ≥+3% 且 CI 下限 >0，故 **PASS，第8輪未跑**。未執行第9輪。'+a['sequential_look']+' CI 下限僅略高於零，未部署候選；promotion/source pin/fresh rebuild 不屬本次授權。','',
f"原 API 復原：controller finally 已執行，DONE／restored=true／verified=true。再次獨立 audit 核對 engine PID {audit['restore_pid']}、原 binary/config SHA、AboveNormal、health loaded=true、3153 slots／20.00 GiB／20479 MiB、STRATA_IQ3S_MT1=1，無 PIPE／PIPE_CHECK／DIAG／MT_MIN 啟用。",'',
f"Coverage：完整讀取所有 4 個新增 meta/config/command/engine logs（{audit['engine_log_bytes']:,} bytes／{audit['engine_log_lines']:,} 行）及 40 正式 rows；原十個 O/P meta/config、harness／輸入 SHA 全比較。舊五輪數據來自實際遠端 rows，並與本機原 rows/analysis 比對。未逐字審閱自然語言 responses、未完整 source audit、未重跑既已證明的 bitwise parity；本次無大型 log 抽樣或截斷後作完整結論。",'',
'權威 remote raw：','',
'- 新：`C:\\Users\\User\\Strata-Adrian\\repo\\Strata-Adrian-control\\runs\\native-pipeline-po-confirm-20261029`（canonical junction 下同名 root）。',
'- 舊：`C:\\Users\\User\\Strata-Adrian\\repo\\Strata-Adrian-control\\runs\\native-pipeline-20261029`。',
'- 新 block：`out\\block-01-O-r6`、`out\\block-02-P-r6`、`out\\block-03-P-r7`、`out\\block-04-O-r7`；各含 config/meta/results/engine.log、逐題 raw responses 與 tails。',
'- 本機保存 rows.json、analysis.json、comparison.json、campaign.json、audit.json、compatibility.json、initial_verify.json、final_verify.json、restore.json 與程序盤點。','']
(R/'RESULT.md').write_text('\n'.join(lines),encoding='utf-8')
ledger=R.parent/'EXPERIMENT_LEDGER.md'
assert ledger.read_text(encoding='utf-8').rfind('NATIVE_PIPE_PO_CONFIRM')>ledger.read_text(encoding='utf-8').rfind('NATIVE_PIPE_ROLE_PRIORITY')
entry=f"\n- 2026-10-29 08:48 完成追加驗證：第6輪 O45.08160606／P45.11552308（+0.075235%），第7輪 P48.14362722／O45.86009488（+4.979345%）；七輪 primary 平均+3.827416%，95% t-CI+0.145269..+7.509562%（df6），依預註冊 PASS，第8輪未跑。Sequential look 未校正，型一錯誤略升；未部署。\n- 漂移與驗收：新O平均45.47085047 vs舊47.22684092（-3.718204%）；新P46.62957515 vs舊49.24582655（-5.312636%）。4 blocks／40 rows、完整325359 bytes／2795 lines logs及舊O/P設定與harness/input SHA核對通過；原MT1 API PID13612、385E…30F5／F23F…EB6F、AboveNormal、loaded、3153／20.00／20479、MT1環境復原驗證通過。完整結果 state/po-confirm-20261029/RESULT.md；raw runs/native-pipeline-po-confirm-20261029。無GitHub／remote git操作。\n"
assert entry not in ledger.read_text(encoding='utf-8')
with ledger.open('a',encoding='utf-8') as f:f.write(entry)
