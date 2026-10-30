[LUNA_REPORT]
TASK_ID: LUNA-20261012-027 (direct user-authorized MT1 deployment/current-best continuation)
STATUS: DEPLOYED_VERIFIED / COMMITTED_NOT_PUSHED (Git credential failure; no retry or authentication fallback)
BENCHMARK_RAW_PATH: NONE (no new benchmark; 3 bounded smoke requests only)

# S2K+MT1 deployment / current best — 2026-10-28

User explicitly requested deployment and best promotion after accepting the small floating-point accumulation-order differences. Existing IQ3S_MT1_AB measured +4.26% round-paired throughput (95% CI +2.15..+6.37, 10 rounds), 47.00 vs 45.10 tok/s, CPU -2.19 ms/window. Those are prior A/B results, not a new deployment benchmark. Weights/routing and temperature are unchanged; generated output need not be token-identical.

## Deployment and identity

- Host: DESKTOP-LKMLUPC, strict SSH host-key validation. Before switch only classified S2K API stack/watchers; idle and queued=0. No competing build/benchmark.
- Canonical main HEAD before deployment: e42e96ce1f2368835f466ebb67fd3189719b5dc3, differing from old local pointer. Unrelated tracked modifications and untracked files preserved.
- Binary unchanged: `runs/miss-overlap-20261027/build/strata.exe`, SHA256 `385EF64EE24BDF3BD4B309264FA811901DF9256B92CE4589BAEC70B3F26B30F5`.
- Build source base: `61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406`, with pre-existing expert_source.cpp/.hpp patches. Remote source file hashes match previous S2K records. Built-in MT1 opt-in confirmed in `src/kernels/cpu/native_expert.cpp`. No rebuild or source-code change.
- New config: `C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\server-task020-8080-v0142-s2k-mt1.json`, SHA256 `F23F1AAD8E385987708D6DFB854AD139D513FE398151CCCC5FBD43CFE303EB6F`.
- New launcher: `tools/start_task020_api_s2k_mt1.ps1`, SHA256 `192B016AAE303C61B1639833D2BA545804164FE12C44BC7904FD019CFCC564ED`.
- Existing `Strata-Task020-API` action now runs that launcher; priority 2 retained; existing task remains manually started (no recurring trigger added).
- Config comparison: exactly +`STRATA_IQ3S_MT1=1` and dedicated engine-log path. CLI args and all other config values equal S2K. `STRATA_IQ_MT_MIN` absent in config and actual engine environment.
- Deployment stop began 21:33:59 +08:00; smoke/receipt complete 21:35:06. This bounds the switch/validation period; exact loaded timestamp was not persisted, so do not label the whole period downtime.

## Verified

Standalone audit at 21:35:32 +08:00: /health loaded=true, one strata.exe PID 25900, exact binary SHA, actual config environment, AboveNormal, 3153 slots / RAM budget 20.00 GiB / locked 20479 MiB. Config and launcher checksums match receipt, old S2K files unchanged. Classified Python processes belong to current API/watchers; no lingering deployment controller after completion.

Three existing Hermes replay smoke requests p01/p02/p03, bounded to max_tokens=128, all HTTP success: completion tokens 103/112/67; finish stop/stop/tool_calls. The third returned a tool-call structure; no tool was executed. No private request/response text is included in this report.

## Durable state and future use

- Local `state/LIVE_DEPLOYMENT.json`, `CAMPAIGN_CURRENT_BEST.json`, `CURRENT_BEST_HISTORY.md` updated only after remote verification. Pre-MT1 full snapshots retained.
- Authoritative small deployment manifest: `bench/results/2026-10-28-s2k-mt1/BEST.json` (to be committed with this report and launcher). Source base plus patch/file hashes are recorded; a reproducible rebuild has NOT been validated.
- Updated MT1 identity helper copies: remote `runs/mt1-deploy-20261028/active-harness/`, local matching directory under `state/`. Identity checks include config hash, MT1=1 and absent MT_MIN because old/new share the same binary. Historical harnesses remain historical.
- Full receipts stay remote at `runs/mt1-deploy-20261028/out/{deploy_receipt.json,final_state.json,scheduled_task.before.xml}`. They include process details/private smoke heads and are not committed.
- Manual S2K rollback target is preserved in BEST.json; automatic fallback/rollback disabled. Re-verify processes and user authorization before any rollback.

## Coverage and limits

Complete checks: baseline/config/launcher hashes, classified process identities, pre-stop idle/queue, effective old/new config comparison, all 3 smoke statuses, actual engine environment/capacity/priority, task action, standalone post-deploy audit and unchanged old files. Raw smoke text not semantically assessed. No new A/B, long context, sustained traffic, full quality evaluation, rebuild reproduction or reboot/logon test. No temperature/system settings changed. Initial diagnostic mistakenly probed loopback despite existing server binding to the Tailscale address; it failed without service modification, then the actual bound endpoint was verified. Two guessed source paths and one guessed analysis path were absent; actual native source was located by filename and verified. No inference/backend fallback used.

## Next action

Verify the deployed MT1 manifest/config/env before any further benchmark. Kernel selection or gate/up–down interleaving remain future scoped work; do not rerun rejected PIN/AA/PATCH4 families without new evidence.

## Publication follow-up

Deployment commit `6251a722f9c98fbfde3465cb5f4639de589a008b` on main, annotated deployment tag `best-s2k-mt1-20261028`, source-base tag `s2k-mt1-source-base-20261028` pinning `61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406`. Canonical repository initially lacked that build-source commit object; the exact object was verified in the existing build-source repository and imported locally, with no branch/source replacement. Source patch SHA256 `9551CE3BA5A06BF4C7FE5AC06A4ACC036AD549578A20618A101313D68A2A933F`.

One atomic push of main and both tags failed before publication: wincredman could not persist credentials; noninteractive session could not prompt for GitHub username. No credential, remote, protocol or connector substitution; no retry. Runtime deployment and local current-best pointers remain valid. Coordination outbox was not published. Publication receipt: `runs/mt1-deploy-20261028/out/publication.json`.
