from pathlib import Path
import json,hashlib,difflib
D=Path('state/deploy-prep-20261029');read=lambda n:json.loads((D/n).read_text(encoding='utf-8-sig'))
a=read('audit.json');pin=read('source-pin.json');src=read('source-comparison.json');build=read('build-result.json');binary=read('binary-comparison.json');live=read('live-detail.json');campaign=read('campaign.json')
root=r'C:\Users\User\Strata-Adrian-control\runs\native-pipe-deploy-prep-20261029'
original=r'C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\server-task020-8080-v0142-s2k-mt1.json'
fresh=build['binary_sha256'];old=build['original_binary_sha256'];best=a['live']['binary_sha256'];cfgsha=a['original_config_sha256']
raw=(D/'live-original.json').read_bytes();cand=(D/'candidate-live.json').read_bytes()
assert hashlib.sha256(raw).hexdigest().upper()==cfgsha
assert hashlib.sha256(cand).hexdigest().upper()==a['candidate_config_sha256']
x=json.loads(raw);y=json.loads(cand);z=json.loads(cand);z['exe']=x['exe'];del z['env']['STRATA_NATIVE_PIPE'];assert z==x
# Diff lines preserve text content; standard LF diff avoids duplicate CR on Windows.
diff=''.join(difflib.unified_diff(raw.decode().splitlines(True),cand.decode().splitlines(True),fromfile=original,tofile=root+r'\candidate-live.json')).replace('\r\n','\n')
(D/'candidate-config.diff').write_bytes(diff.encode())
rollback=f'''# 回滾程序（準備文件，未執行）

TASK LUNA-20261012-027 / NATIVE_PIPE_DEPLOY_PREP。目前 live 已是原版；此程序供未來獲准切換後回滾。

1. 先以 strict host-key SSH 確認 DESKTOP-LKMLUPC，盤點 PID／名稱／command line。只處理經分類的候選 API；發現其他未分類程序就停。先等待 API idle，不中斷使用者 request。
2. 驗證原 binary `{x['exe']}` SHA256=`{best}`，備份設定 `{root}\\live-original.json` SHA256=`{cfgsha}`。任何不符就停。
3. 使用既有 harness 的 `next_steps_ab_20261018.stop_api(run_root)` 暫停經核對的 API；它採 Stop-ScheduledTask Strata-Task020-API、核對 API PID、等待 process gate clean。不得用程序名稱廣泛殺除。
4. 若未來部署覆寫了 active config，將 `live-original.json` 以原 bytes 複製回 `{original}`；重驗 SHA256=`{cfgsha}`。本次未覆寫 live config，因此現在不需要執行複製。
5. 使用原 task action：powershell.exe `-NoProfile -NonInteractive -ExecutionPolicy Bypass -File C:\\Users\\User\\Strata-Adrian-control\\tools\\start_task020_api_s2k_mt1.ps1`。其原 launcher 已存 `live-original-launch.ps1`，task action 已存 `live-task-actions.json`。後續部署應保留此原 task action；若另行修改 task，必須另有可審閱的還原步驟。
6. 在 controller finally 使用既有 `restore_api(run_root)` / Start-ScheduledTask Strata-Task020-API。驗證唯一 engine binary SHA=`{best}`、config SHA=`{cfgsha}`、AboveNormal、health loaded=true、3153 slots／20.00 GiB／20479 MiB、workers 9／affinity all、STRATA_IQ3S_MT1=1；無 PIPE／PIPE_CHECK／DIAG／MT_MIN 啟用。既有 STRATA_RAM_LRU_CHECK=0 是停用值，保留。
7. 保存 restore、環境、capacity、process evidence；restore 失敗就回報失敗層級，不採 fallback、不改模型或 current-best build。

原 config 的 cwd/log/args/env 與 API 溫度均須還原為原 bytes；不要套 correctness 的 CHECK/DIAG 設定。此文件不授權現在部署或額外停服務。
'''
(D/'ROLLBACK.md').write_text(rollback,encoding='utf-8')
rows='\n'.join(f"| `{p}` | `{v['actual']}` | 完全相同；CRLF={v['crlf']}、LF={v['lf']} |" for p,v in src.items())
par='\n'.join(f"| {k} | {v['requests']} | {v['values_compared_at_least']:,} | {v['mismatches']} | {len(v['observed_pairs'])}/10 |" for k,v in a['blocks'].items())
cmd=(D/'build.cmd').read_text();cmd=cmd[cmd.index('cmake -S'):]
report=f'''[LUNA_REPORT]

# NATIVE_PIPE_DEPLOY_PREP：{a['verdict']}

TASK_ID：LUNA-20261012-027；TASK_SOURCE：使用者今日「準備部署 pipeline」直接授權 continuation，無新 GitHub claim。STATUS：REPORT_LOCAL。只準備部署，未切換正式 API、未 push、未修改 main。

執行至 {campaign['updated_utc']}（UTC）；hostname DESKTOP-LKMLUPC 已重新核對。canonical root 是 junction，實際來源 `C:\\Users\\User\\Strata-Adrian\\repo\\Strata-Adrian-control`。遠端 raw root：`{root}`（實際 junction target 下同名 runs 目錄）。

## Source pin

- worktree：`{pin['worktree']}`，在 main 工作樹之外。
- branch：`{pin['branch']}`。
- source commit：`{pin['commit']}`；annotated local tag：`{pin['tag']}`。
- base：`61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406`；僅套用 `2f1e99872969c9b4586a2d41c7f1915f27e4f298:bench/experiments/overnight-20261029/generic.patch`，沒有 roles patch。
- 全六檔與該 commit manifest 及原 build identity 相符；三個指定檔案 byte-for-byte 相同，未正規化換行或修補 hash。

| 檔案 | SHA256（expected=actual） | 結果／換行 |
|---|---|---|
{rows}

main HEAD 保持 `2f1e99872969c9b4586a2d41c7f1915f27e4f298`；兩個既有 dirty tools 的 bytes hash 與 tracked status 前後相同，沒有 stage/stash/reset。新 worktree clean。沒有推送或 GitHub 寫入。

## Fresh build

獨立 build：`{root}\\build`。原 current-best 與 3F98 build 未覆寫。沿用原 overnight build.cmd 的 configure flags，以及 build-shadow.cmd 的 `--target strata -j 2`；只替換 source/build 路徑。原 3F98 是增量 build，本次是 fresh build。

```bat
{cmd.strip()}
```

實讀 compiler/version：MSVC 19.44.35226 x64；CUDA 13.2 / V13.2.78；CMake 4.3.2。原始命令完整存 `build.cmd`，版本存 `compiler-version.log`／`cuda-version.log`／`cmake-version.log`。build exit code：{build['exit_code']}。

- fresh SHA256：`{fresh}`。
- 原測速 SHA256：`{old}`。
- fresh 大小 {binary['fresh']['bytes']:,} bytes；原 {binary['original']['bytes']:,} bytes。
- 已驗證差異：PE timestamp 原 `{binary['original']['pe_time_utc']}`、新 `{binary['fresh']['pe_time_utc']}`；將 COFF timestamp 歸零仍不相同，`.text`／`.rdata`／`.data`／CUDA fatbin／relocation 等 section hash 不同；`.pdata`、`.rsrc` 相同。完整值見 `binary-comparison.json`。
- 差異來源的已知條件：新 source/build 路徑與全新 object/link；原來是另一隔離路徑的增量 build。未完全定位全部差異到特定 compiler 產物，不能宣稱僅 timestamp，亦未證新 binary 與 3F98 的速度等同。未新增 rebuild 或速度測試來追差異。

## SMOKE／CHK

沿用原 harness／十題輸入，harness 與 request SHA 與原 generic campaign 全比對相同；SMOKE p01/p05/p08、CHK p01..p10，各上限128 tokens。沿用原 replay temperature=0 契約，未調整 live sampling。PIPE=1、PIPE_CHECK=1，既有 CPU_PHASE_DIAG 用於檢查紀錄；沒有正式速度輪。

| 組別 | 請求數 | 至少比較 float values | bitwise mismatches | pair coverage |
|---|---:|---:|---:|---:|
{par}

比較數取各 engine log 累計 counter 的最大值，因此是可證明下限；不是把重複累計行相加。SMOKE 缺 (16,20)，完整 CHK 已補齊，missing=[]。十種 pair：{a['blocks']['CHK']['observed_pairs']}。獨立原分段 GU／quant／down reference 全 bitwise 相等；不代表自然語言輸出必然逐字一致。

兩組皆 status OK，零 request error，無 NATIVE_PIPE fatal／mismatch。每組第一 request 前設定 AboveNormal，逐 request 沿用 priority/process gate；容量皆3153 slots／20.00 GiB／20479 MiB、workers9、affinity all。未引入新的 RAM/效能數值門檻；RAM 與 heavy processes 僅記錄。

## Live 恢復

controller finally 已恢復，campaign DONE／restored=true／verified=true；之後另行獨立核對通過：engine PID {a['live']['pid']}、AboveNormal、health loaded=true，binary `{best}`、config `{cfgsha}`，3153 slots／20.00 GiB／20479 MiB。MT1=1；無 PIPE/CHECK/DIAG/MT_MIN 啟用，既有 RAM_LRU_CHECK=0 保留。原 config 未修改。

`initial_verify.json`、`processes-source-pin.json`、`processes-build.json`、`processes-pre-stop.json`、block process/priority records、`restore.json`、`final_verify.json`、`independent-live-verify.json`、`live-detail.json`、`final-processes.json` 保存證據。無未分類 Strata/Luna/build/benchmark 程序；無關系統程序未停止。

## 候選設定（未套用）

remote：`{root}\\candidate-live.json`；本機：`D:\\strata\\state\\deploy-prep-20261029\\candidate-live.json`。

SHA256：`{a['candidate_config_sha256']}`。與原 live config 只差 `exe` 與 env PIPE=1；cwd/log/args/其他 env 都保持原值，沒有 CHECK/DIAG。備份原 config 是 `live-original.json`，原 launch/task action 另存。未進行候選 live launch。

Exact config diff（另存 `candidate-config.diff`）：

```diff
{diff.strip()}
```

## 回滾程序

{rollback[rollback.index('1. 先以'):].strip()}

另存 remote `{root}\\ROLLBACK.md` 及本機同名文件。

## Coverage 與剩餘限制

要求範圍：source pin／fresh build／SMOKE3+CHK10／restore／候選 config+rollback。實際完整處理：generic patch 六檔 SHA、commit/tag、兩組所有 meta/config/results（13 requests）與完整 engine logs（{a['engine_log_bytes']:,} bytes／{a['engine_log_lines']:,} 行）、十種 pair、所有十題 input/harness SHA、live identity/env/capacity、main 兩檔不變、config exact diff。大型 binary 全檔 hash 與全部 PE sections hash；build log保存，僅抽看進度與warning/末尾，未逐字審閱所有warning。私人 prompt/自然語言 response 未逐字審閱；不是完整全 source/dependency audit。沒有把截斷輸出當完整 log 結論。

原始資料：remote root 的 `out/block-00-SMOKE-r0`、`out/block-01-CHK-r0`、`build.log`、`build-result.json`、`source-comparison.json`、`source-pin.json`、`binary-comparison.json`、`audit.json` 與上述 restore/config 文件；兩組完整 raw 已複製本機 out/，build binary 留遠端。

剩餘風險：fresh binary SHA 不同且完整差異原因未定位；歷史速度證據只屬3F98，不是fresh測速。若需短 O/P 確認，由使用者另行決定，這次不自行追加或部署。
'''
(D/'RESULT.md').write_text(report,encoding='utf-8')
ledger=Path('state/EXPERIMENT_LEDGER.md')
append=f"\n- 2026-10-29 NATIVE_PIPE_DEPLOY_PREP 完成追加：**{a['verdict']}**。新 worktree `{pin['worktree']}`，branch/tag `{pin['tag']}`，commit `{pin['commit']}`；generic 六檔 SHA 全同、main/兩 dirty tools 未變、未 push。fresh build exit0、SHA `{fresh}`，不同於3F98，差異不限timestamp且完整來源未定位。SMOKE3×128至少{a['blocks']['SMOKE']['values_compared_at_least']:,}、CHK10×128至少{a['blocks']['CHK']['values_compared_at_least']:,} float values，零bitwise mismatch、CHK十pair全覆蓋；完整{a['engine_log_bytes']:,}bytes/{a['engine_log_lines']:,}lines engine logs驗收。原API finally恢復並獨立驗證PID{a['live']['pid']}、385E…30F5/F23F…EB6F、AboveNormal/loaded/3153/20.00/20479/MT1。候選config+exact diff+rollback已準備未套用；未跑正式速度。報告 `state/deploy-prep-20261029/RESULT.md`；raw `runs/native-pipe-deploy-prep-20261029`。fresh速度未驗證、需使用者另決定短O/P確認。\n"
assert 'NATIVE_PIPE_DEPLOY_PREP 完成追加' not in ledger.read_text(encoding='utf-8-sig')
with ledger.open('a',encoding='utf-8',newline='') as f:f.write(append)
print(a['verdict']);print(par)
