# Task029 — Current IQ3 decode speed baseline

- Task: `MANUAL-20261018-IQ3-SPEED-BASELINE`
- Status: `MEASURED_BASELINE_ONLY`
- Decision: `DIAGNOSTIC_ONLY`; do not promote and do not update `CAMPAIGN_CURRENT_BEST`
- Host: `DESKTOP-LKMLUPC`
- Remote raw root: `C:\Users\User\Strata-Adrian-control\runs\manual-speed-20261018-iq3-baseline`
- Remote summary SHA256: `7668B49FE319B05273F270FE9AACDA8ABD8245487F31482ED2BC13BE6C09BEDD`

## Actual decode speed

All three runs used the same current live IQ3 binary, config, prompt hash, and 1,024-token target. All exited 0, accepted 1,024 tokens, and had no residual relevant process.

| run | decode tok/s | accepted | pool ms/token | file MB | elapsed s |
|---|---:|---:|---:|---:|---:|
| run-01 | 22.57 | 1024 | 48.428 | 16750.4 | 106.121 |
| run-02 | 21.92 | 1024 | 47.519 | 16313.0 | 106.129 |
| run-03 | 22.09 | 1024 | 51.036 | 17313.5 | 105.199 |

- Mean: **22.1933 tok/s**
- Median: **22.09 tok/s**
- Range: **21.92–22.57 tok/s**

## Identity and runtime

- Binary: `C:\Users\User\Strata-Adrian-control\runs\ram-lru-20261013\build\strata.exe`
- Binary SHA256: `366A355E0E866B12D1793C9D8BE022925305B4560E1AE7DC47F8716C865015E2`
- Config: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\server-task020-8080-v0142.json`
- Config SHA256: `C805B1206CDD23B22EE3CC66A80C52014EF9904CDB4314A6C6A17B8E00FFEA18`
- Model: `IQ3_XXS`; prompt: `neuro.tokens`, 28,912 tokens
- Prompt SHA256: `9350584440AD92D3FCE3BA024CAD33BB55BD950CAED12823F8B89E69CCA718BA`
- Context/KV: `100000`, `q4_0`, `--kv-resident 20480`
- Resident/cache: `20 GiB`, expert cache `3604`, CPU pool workers `9`, profile `learned-heart-chat`
- MTP: `--spec 6 --spec-min-p 0.75 --suffix-draft 3 --mtp-max-t 3 --mtp-hnorm stream`
- No sampling or temperature change was applied.
- LRU/cache environment was recorded in `TASK029_SPEED_BASELINE_20261018.json`.

## Evidence and limits

Per-run `command.json`, `stdout.log`, `stderr.log`, `result.json`, and GPU before/after files remain on the remote host. The launcher summary and each raw log/result SHA256 are recorded in the JSON state file.

The post-run process gate found zero relevant Strata/llama/python benchmark processes. The scheduled task remained `Ready` with no next run. The launcher did not create empty process snapshot files when the process query returned no rows; this is recorded as an evidence-format gap, not treated as a hidden process.

This is a real current-IQ3 decode baseline, not a speedup result. No matched current control binary was available, so historical IQ2 or different-binary measurements are deliberately excluded. The next valid comparison requires one control and one candidate with the same binary identity rules, prompt, runtime, and accepted-token/quality checks.

## Append-only correction — 2026-10-18 reproduction recheck

Original measurements above are retained. Fresh read-only raw-log inspection confirms actual resident17.01/17.35/17.44GiB and VirtualLock17415/17767/17856MiB, not20GiB. The three exit0/1024 runs completed but fail the matched20GiB capacity gate. Their CLI runner also omitted explicit tail-skip7, unlike the deployed serve default. Do not classify these as reproduced20GiB controls or compare them directly with historical50tok/s.

The separate serve raw run completed at28.0decode tok/s with17.55GiBresident/17968MiBlocked. Its result.json mistakenly stores932.5prefill tok/s as decode due to matching the first rate on the combined prompt/generated line. Original remote artifacts remain untouched; corrected evidence and SHA are in REPRODUCTION_FAILURE_RECHECK_20261018.json. Local runner parsers/capacity classifications were repaired and syntax/real-line regression checks passed; no new model run was performed. See .codex/handoffs/2026-10-18-strata-reproduction-runbook.md.
