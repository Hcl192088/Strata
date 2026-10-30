# NoWait A/B at xhigh, 5 more pairs per point (2026-10-19)

## Setup
- Host DESKTOP-LKMLUPC; running strata.exe = runs\ram-lru-20261013\build\strata.exe, SHA256 366A355E...5015E2 (match); process set unchanged (API stack incl. strata_memory_policy.py --watch). Each request waited for /metrics idle. No remote changes, no GitHub, no connection problems (0 blips).
- Same request shape as the earlier xhigh run (Hermes `strata_high`: reasoning_effort=high -> template xhigh, temperature 1.0, top_p 0.95, top_k 20, min_p 0, presence 0, max_tokens 32768), same 10 points, same 82-id ban list (-100, whole output), new seeds. 5 pairs per point, order alternated per point/rep, 100 requests, 0 finish_reason=length, 0 errors. Earlier xhigh run (2 pairs/point) kept separately in state\nowait-hermes-xhigh-20261019\.
- Bootstrap: 5000 resamples; resample the 10 points with replacement, and within each chosen point resample its C runs and N runs independently (arms are not seed-paired). Two statistics: "pooled" = sum over points of mean N / sum of mean C - 1 (token-weighted), "mean-of-points" = unweighted mean of per-point % changes. Reasoning vs final tokens are ESTIMATED from character share (API gives one total).
- Files: state\nowait-hermes-xhigh5-20261019\ (responses, requests, results.json, view.txt, analyze5.py).

## Pooled deltas with bootstrap 95% CI (NoWait vs control)
| Dataset | runs | completion tokens (pooled) | decode time (pooled) | est. reasoning tok | est. final tok | mean-of-points tokens |
|---|---|---|---|---|---|---|
| 2-pair run | 40 | -11.8% [-40, +17] | -11.5% [-40, +19] | -14.4% [-45, +16] | +11% [-31, +86] | -14.8% [-35, +14] |
| 5-pair run (new) | 100 | -9.2% [-29, +20] | -7.9% [-28, +21] | -10.0% [-32, +21] | -0.9% [-26, +43] | -5.6% [-25, +27] |
| Pooled 7 pairs/point | 140 | -9.8% [-25, +11] | -8.8% [-25, +12] | -11.0% [-28, +11] | +2.4% [-20, +39] | -9.1% [-23, +13] |

All CIs include 0. Point estimate is a ~9-10% reduction, consistent between the two runs, but not statistically distinguishable from no effect. Per run: tokens C 357 vs N 322, decode 8.6 s vs 7.9 s (pooled). Savings are in reasoning (est. -11%), final/tool-call tokens flat. For comparison, medium effort (30 pairs): +1.9% tokens, 0% decode (no benefit).

## Per-point medians (pooled, 7 runs per arm; tokens = completion tokens)
| pt | type | tok C->N (median) | decode s C->N | mean tok C->N | banned in C | banned in N | tool-call pattern / quality |
|---|---|---|---|---|---|---|---|
| p01 | QA | 142->86 (-39%) | 4.1->2.8 | 168->142 | 11 | 0 | same (mostly text answer) |
| p02 | QA ping | 132->129 (-2%) | 2.8->2.9 | 140->186 | 15 | 0 | same |
| p03 | QA/tool | 150->110 (-27%) | 3.7->2.8 | 149->125 | 18 | 0 | same (cronjob_manage list; C twice adds terminal) |
| p04 | QA | 329->272 (-17%) | 7.6->6.3 | 308->261 | 35 | 0 | same (all text, same conclusion) |
| p05 | QA open-ended | 876->851 (-3%) | 21.4->20.3 | 1046->884 | 138 | 0 | minor-diff: strategy varies in both arms (C web_search/web_fetch/browser_exec, N skill_view/terminal); N rep with `browser_exec {}` (missing action, earlier run) vs C `browser_exec {"command":"tabs"}` (wrong key): one odd call per arm |
| p06 | reasoning, no tools sent | 297->188 (-37%) | 6.9->3.9 | 268->179 | 23 | 1 | minor-diff (all runs inspect cron/workspace, tool choice varies) |
| p07 | tool | 300->274 (-9%) | 6.0->6.4 | 287->230 | 11 | 0 | same (beeper search/list in both) |
| p08 | tool | 255->198 (-22%) | 5.8->4.4 | 254->207 | 11 | 0 | minor-diff (N more often starts with search_files; one N list_messages with extra `messageID`) |
| p09 | tool | 458->378 (-17%) | 11.9->9.3 | 452->408 | 33 | 0 | same (skill_view + session_search +/- get_accounts) |
| p10 | tool | 493->631 (+28%) | 12.4->14.9 | 501->599 | 43 | 0 | minor-diff (N does web_extract lookup slightly more often: 3/5 vs 2/5 in new run); NoWait is longer here |

Heterogeneity: 8 of 10 points have median reduction (range -2% to -39%); p10 is the clear counter-example (+28%), p02 flat. Spread within arm is large (p05 completion 400-2000 tokens).

## Quality / tool-call hygiene (all 140 runs)
- Labels: same 6 (p01, p02, p03, p04, p07, p09), minor-diff 4 (p05, p06, p08, p10), worse 0 definite, better 0.
- Tool calls: calls with unparseable JSON or an undefined tool name: C 8, N 7 in raw counts, but 7 of each are p06 (no tools were sent, so every call is flagged); excluding p06, C 1 and N 0. Empty-arg calls: C 3, N 4, but 6 of the 7 are `get_accounts {}` / `browser_vault_list {}`, which legitimately take no arguments; genuine suspicious: `browser_exec {}` once in N (2-pair run, p05), and `browser_exec {"command":"tabs"}` once in C. Odd-key calls: C 2, N 2. No-tool-call (text) answers: C 18 vs N 20. Tool calls per run: C 1.27, N 1.11 (NoWait issues slightly fewer calls, mostly dropping redundant parallel lookups).
- Banned words: control 338 words (13.5 per 1k tokens; 11.3 in 2-pair run, 14.3 in 5-pair run; medium effort 8.8); NoWait 1 (one p06 reasoning occurrence formed through another token path), so the suppression works.

## Limitations
- Seeds not reproducible, so no matched-pair tests; bootstrap over independent runs. Only 10 points, one workload (Hermes personal assistant on one model); reasoning/final split estimated; tool schemas reconstructed; bias hits the whole output; quality by single-judge side-by-side only.
- Thinking at xhigh remains short (control ~357 tokens/run), so little "wait" overthinking exists to cut.

## Recommendation
Evidence for NoWait at xhigh: a consistent ~9-10% reduction in completion tokens and decode time (both runs agree), no detected quality regression, but CIs [-25%, +11%] include zero and one point (p10) gets longer. Not enough to enable by default; gains are small relative to run-to-run noise. Worth revisiting only for a thinking-phase-only bias or long-CoT tasks. At medium effort it does nothing.
