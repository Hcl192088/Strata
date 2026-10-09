# Handoff: adrian-spec-min-p-worker-sweep-2026-10-07

## Metadata

- Generated At: 2026-10-07T23:45:34+08:00
- Project Root: D:\strata
- Git Branch: unknown
- Head Commit: unknown

## Original Goal

在遠端 `DESKTOP-LKMLUPC` 的 RTX 4070 上，固定 Adrian binary、IQ2_XS model/MTP/prompt/context/KV/expert profile/cache/adapt/suffix/spec/pcie 與 `--resident-budget-gib 20`，找出 decode tok/s 最佳的 `--spec-min-p` 與 `--pool-workers`。本輪不修改 source、不開 FETCH_ADMIT、不調 resident/headroom 或其他 runtime 參數。

## Current State

Phase 1 與 Phase 2 已完成。最佳候選是 `--spec-min-p 0.60`、`--pool-workers 9`，但本輪有效 run 的實際 resident RAM 只有 17.85–18.46 GiB，pinned 全部 0.00 GiB；既有 41.62 tok/s reference 是 19.05–19.13 GiB resident，因此絕對速度比較受 RAM/file-tier 狀態影響，尚不能宣稱穩定 43 tok/s。

目前任務狀態：`blocked`。2026-10-08 連續 preflight 的 Available RAM 約 22.45–22.47 GiB，低於新 benchmark 規則要求的 23.75 GiB，因此沒有啟動任何新 run。RAM 狀態改變後，必須先重新做 strict preflight，不可直接沿用舊結果。

## Remote Connection and Strata Runbook

### 連線位置

- Remote user/host：`User@100.126.147.41`
- Remote hostname：`DESKTOP-LKMLUPC`
- Windows PowerShell 連線：

```powershell
ssh -o BatchMode=yes -o ConnectTimeout=10 User@100.126.147.41
```

- 在 Codex 的 Windows shell 執行 SSH 時使用 `sandbox_permissions="require_escalated"`。不要把密碼、token 或 credential 寫入 handoff。
- 遠端是 Windows PowerShell。若 inline SSH 的巢狀引號出錯，使用 encoded PowerShell：先把遠端 script 以 UTF-16LE (`[Text.Encoding]::Unicode`) 編成 Base64，再呼叫：

```text
ssh -o BatchMode=yes -o ConnectTimeout=10 User@100.126.147.41 "powershell.exe -NoProfile -EncodedCommand <UTF16LE-BASE64>"
```

這是本次已驗證的穩定方式；直接把 `powershell -Command` 巢狀塞進本地 PowerShell 曾造成 quoting 錯誤。

### Adrian binary 與固定輸入

- Binary：`C:\Users\User\Strata-Adrian-control-build\strata.exe`
- Binary SHA256：`E67EB500C2F43B0E75D3956A17BA71C425830B6D56E2C7C5C7A96559CDEEFA74`
- Workdir：`C:\Users\User\Strata-v038-prefill-seed-20261006`
- Authoritative baseline command：`C:\Users\User\adrian-budget20-repro3-20261007\source-command.json`
- Benchmark raw root：`C:\Users\User\adrian-spec-worker-sweep-20261007`
- Native model：`C:\Users\User\Strata-v0.1.34-mtp-test-20261002\models\IQ2_XS\Qwen3.8-Flash-Next-GSQ-RCO-IQ2_XS-00001-of-00002.gguf`
- PLE model：同目錄的 `Qwen3.8-Flash-Next-GSQ-RCO-IQ2_XS-00002-of-00002.gguf`
- MTP：`C:\Users\User\Strata-v0.1.34-mtp-test-20261002\mtp\rt`
- Expert profile：`C:\Users\User\Strata-v0.1.38-ab-20261003\work-note-transfer-chat-20261005\learned-heart.bin`
- Tokens input：`C:\Users\User\Strata-v0.1.38-ab-20261003\work-note-transfer-chat-20261005\neuro.tokens`
- Existing fixed args include `--pack ...\packs\iq2_xs`, `--spec 4`, `--max-context 100000`, `--kv q4_0`, `--kv-resident 20480`, `--expert-cache 3796`, `--pool-workers 9`, `--prefill auto`, `--stats`, `--max-new 1024`, `--suffix-draft 3`, `--resident-budget-gib 20`。

### 新 objective 的 strict preflight

目前 objective 與上一輪 sweep 不同：上一輪明確使用 headroom=4；新 objective 必須使用 `STRATA_RESIDENT_HEADROOM_GIB=3`。不要複製舊 runner 而忘記改這一點。

在每一輪啟動前，遠端先執行：

```powershell
$os = Get-CimInstance Win32_OperatingSystem
$freeGiB = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
"Available RAM: $freeGiB GiB"
Get-Process -Name strata,llama -ErrorAction SilentlyContinue |
  Select-Object Id,ProcessName,WorkingSet64,Path
nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free --format=csv,noheader,nounits
```

只有 `$freeGiB -ge 23.75` 且沒有殘留 Strata/llama 才能啟動。不可擅自停止其他程序；若 RAM 不足，標記 preflight blocked，等待外部 RAM 狀態改變。

### Strata 執行方法

不要用 `Start-Process` 來取得 native exit code；早期 runner 曾保存成 null。已驗證的方式是在 remote PowerShell 直接呼叫 native binary：

```powershell
$source = Get-Content -LiteralPath 'C:\Users\User\adrian-budget20-repro3-20261007\source-command.json' -Raw | ConvertFrom-Json
$exe = [string]$source.command[0]
$args = New-Object System.Collections.Generic.List[string]
foreach ($x in $source.command[1..($source.command.Count-1)]) { [void]$args.Add([string]$x) }

# 每個 arm 只替換指定的變數；其他 args 從 source-command.json 原樣沿用。
for ($i=0; $i -lt $args.Count; $i++) {
  if ($args[$i] -eq '--spec-min-p') { $args[$i+1] = '0.50' }
  if ($args[$i] -eq '--pool-workers') { $args[$i+1] = '9' }
}

$env:STRATA_FETCH_ADMIT = '0'
$env:STRATA_RESIDENT_HEADROOM_GIB = '3'
$env:STRATA_ADAPT_IF_MISS = '1'
$env:STRATA_EXPERT_FILE_CACHE = '1'
$env:STRATA_PF_FUSED = '1'

New-Item -ItemType Directory -Force -Path 'C:\Users\User\adrian-spec-worker-sweep-20261007\arm' | Out-Null
Push-Location 'C:\Users\User\Strata-v038-prefill-seed-20261006'
& $exe @args 1> 'C:\Users\User\adrian-spec-worker-sweep-20261007\arm\stdout.log' 2> 'C:\Users\User\adrian-spec-worker-sweep-20261007\arm\stderr.log'
$nativeExitCode = [int]$LASTEXITCODE
Pop-Location
"native exit code=$nativeExitCode"
```

實際 benchmark runner 必須為每輪建立獨立目錄，保存 `command.json`、`stdout.log`、`stderr.log`、`result.json`，並在 process 結束後再次檢查 `Get-Process -Name strata,llama`。每輪 fresh process、`--max-new 1024`；exit code 非 0、沒有完整 1024 tokens、startup resident 不符合範圍或 post-process 非空都不納入。

### Startup validity 與 log 解析

- 新規則 startup resident 必須從 stderr 的 `FileExpertSource: locked resident cache complement ready:` 行確認為 `19.98–20.02 GiB`；否則 INVALID，即使 process exit=0 也不算。
- 需要保存/解析的 stdout 行：`speculation`、`suffix drafts`、`verify window`、`adaptive tier`、`expert tiers`、`pcie experts`、`decode`、`the CPU expert pool`、`R4 expert-cache hits`。
- 需要保存/解析的 stderr 行：`RAM budget`、`locked resident cache`、`page-lock`、`expert-pool workers`、`expert cache`、file-tier startup 訊息。
- `speculation` 行提供 MTP proposed/accepted、acceptance 與 window 數；`accepted/window` 用 MTP accepted 除以 speculation rounds，必須和 suffix-draft windows 分開。
- `verify window` 的 wait/pool/host/commit 是每 round timing；目前 binary 沒有獨立 draft ms/window 欄位，不可自行把總時間當 draft time。

## Completed This Session

- 讀取並固定 baseline command：`C:\Users\User\Strata-Adrian-control-build\strata.exe`，binary SHA256 `E67EB500C2F43B0E75D3956A17BA71C425830B6D56E2C7C5C7A96559CDEEFA74`；原始 `--spec-min-p 0.5`、`--pool-workers 9`。
- 保持 model `Qwen3.8-Flash-Next-GSQ-RCO-IQ2_XS-00001/00002.gguf`、MTP `C:\Users\User\Strata-v0.1.34-mtp-test-20261002\mtp\rt`、context `100000`、KV `q4_0`、KV-resident `20480`、expert profile、expert cache、tokens file、`--spec 4`、suffix draft `3` 與 `--max-new 1024` 不變。
- 每輪明確設定 `STRATA_FETCH_ADMIT=0`、`STRATA_RESIDENT_HEADROOM_GIB=4`、`STRATA_ADAPT_IF_MISS=1`、`STRATA_EXPERT_FILE_CACHE=1`、`STRATA_PF_FUSED=1`；每輪 exit code=0，測試後無 Strata/llama 殘留。
- Phase 1 測試 min-p `0.50/0.60/0.70/0.75/0.80/0.85`；0.60 與 0.70 因差距小於 1% 各補到三輪。0.60 三輪為 `40.35/40.29/42.12`，平均 `40.92`、median `40.35`、minimum `40.29`；0.70 三輪為 `39.97/40.73/39.80`，平均 `40.17`。
- Phase 2 固定 min-p 0.60，測 workers `7/8/9`；7 與 8 均比 9 慢超過 1%，故依規則不測 6/10。workers 7 與 9 各補到三輪：7 為 `37.23/37.71/35.72`，平均 `36.89`；9 為 `38.36/40.34/39.85`，平均 `39.52`、median `39.85`、minimum `38.36`。
- 修正一個 benchmark runner 問題：初次 0.50 run 雖 raw log 完整但 native exit code 為 null，已排除；使用直接 native invocation + `$LASTEXITCODE` 重跑，`phase1-minp-050-control-rerun` exit 0。

## Validated

- Command: 遠端 `C:\Users\User\adrian-budget20-repro3-20261007\source-command.json`；各 run 的 `command.json`、`stdout.log`、`stderr.log`、`result.json` 位於 `C:\Users\User\adrian-spec-worker-sweep-20261007\phase1-*` 與 `phase2-*`。
- Result: 所有納入比較的 run 都是 1024 accepted tokens、exit code 0、post-process list 空；raw log 有 `decode ... tok/s`、MTP proposed/accepted、R4 cache hits、adaptive swaps、CPU expert pool 與 file-tier blob timing。
- Result: 所有本輪 run 都顯示 page-locking refused、pinned `0.00 GiB`、`pcie experts 0.00`；實際 resident 約 `17.85–18.46 GiB`。這與舊 reference run 的 `19.05–19.13 GiB` 不同。
- Result: 依 decode tok/s 而非 acceptance rate 判定，Phase 1 最佳 min-p 是 `0.60`；Phase 2 最佳 workers 是 `9`。

## Not Yet Validated

- Assumption: 在實際 resident 能穩定接近 19–20 GiB、或至少同一 resident fallback 水平下，0.60/9 仍是最佳設定；目前只完成本輪 sweep，未在相同 RAM 狀態下重做完整交錯 protocol。
- Risk: 目前與 41.62 reference 的負差距不能純歸因於 min-p 或 workers，因 resident RAM 少約 0.6–1.3 GiB 且 file-tier reads 變多。單次 `42.12 tok/s` 也不足以稱穩定 42/43。
- Draft ms/window 未由 Adrian raw log 單獨輸出；verify window 的 wait/pool/host/commit component 有記錄，但不能反推出獨立 draft 時間。

## Remaining Work

- [ ] 若要得到可與 41.62 嚴格比較的結論，先在不停止其他程序的前提下檢查/穩定可用 RAM，使 `--resident-budget-gib 20` 的實際 resident 至少回到約 19 GiB，再只重測 0.60/9 與必要的 0.70/9 control。
- [ ] 不要在沒有新 controlled run 前宣稱 43 tok/s，也不要把 acceptance rate 當成速度勝負依據。
- [ ] 若後續只要保留目前 provisional winner，設定為 `--spec-min-p 0.60 --pool-workers 9`；不要修改主 Strata repo 或 Adrian source。

## Decisions Made

- Decision: 採用 `--spec-min-p 0.60` 作為 provisional winner。
- Reason: 三輪平均 40.92 tok/s，高於 0.70 的 40.17；0.70 雖有較高 MTP acceptance，但完整 decode throughput 較低。
- Decision: 採用 workers=9 作為 provisional winner，不追加 6/10。
- Reason: one-shot 中 7/8 比 9 慢超過 1%，符合使用者指定的追加條件；workers=9 三輪平均 39.52，高於 workers=7 的 36.89。
- Decision: 不將本輪與 41.62 reference 視為嚴格公平速度比較。
- Reason: `--resident-budget-gib 20` 在本輪因 RAM fallback 實際只配置 17.85–18.46 GiB，reference 是 19.05–19.13 GiB。

## Blockers / Open Questions

- Current hard blocker：遠端 Available RAM 連續 preflight 約 22.45–22.47 GiB，低於新規則 23.75 GiB；在外部 RAM 狀態改變前不得啟動新 benchmark。
- 目前沒有 engine/source blocker；主要開放問題是遠端常駐程序與 RAM 狀態造成 resident fallback，是否掩蓋 0.60/9 在正常 19–20 GiB resident 下的實際速度。
- 未測 workers 6/10，因使用者規則要求只有 7/8 超過或接近 9（<1%）才追加；本輪 7/8 均未符合。

## Critical Files

- `D:\strata\.codex\handoffs\2026-10-07-234534-adrian-spec-min-p-worker-sweep-2026-10-07.md`
- `D:\strata\.codex\handoffs\2026-10-07-162724-adrian-4070-sm89-worker9-benchmark-2026-10-07.md`
- 遠端 source command：`C:\Users\User\adrian-budget20-repro3-20261007\source-command.json`
- 遠端 benchmark root：`C:\Users\User\adrian-spec-worker-sweep-20261007`
- 遠端 reference summary：`C:\Users\User\adrian-budget20-repro3-20261007\summary.json`

## Recent Commits

- 当前无可用 git 提交信息

## Modified Files

- `D:\strata` 不是 git repository；本次沒有修改 engine source、模型、binary 或主 Strata repo。
- 只建立了本 handoff；benchmark raw artifacts 寫入遠端 `C:\Users\User\adrian-spec-worker-sweep-20261007`。

## Context To Load

- 先讀本 handoff，再讀 `remote_AGENTS.md` 與遠端 `source-command.json`；不要從記憶重建 command。
- 若需重測，先唯讀檢查遠端 `strata/llama` processes、OS available RAM、binary SHA256，再逐輪保存 command/raw logs/result，且不可停止無法確認身份的程序。
- 舊 sweep 使用的 environment 是 `STRATA_FETCH_ADMIT=0`、`STRATA_RESIDENT_HEADROOM_GIB=4`、`STRATA_ADAPT_IF_MISS=1`、`STRATA_EXPERT_FILE_CACHE=1`、`STRATA_PF_FUSED=1`；目前新 objective 必須把 headroom 改為 `3`，其他值維持不變。

## Next Command

```text
ssh -o BatchMode=yes -o ConnectTimeout=10 User@100.126.147.41
```
