# NoWait A/B at xhigh reasoning effort (2026-10-19)

## Setup
- Host DESKTOP-LKMLUPC, running strata.exe = runs\ram-lru-20261013\build\strata.exe, SHA256 366A355E...5015E2 (match). Process inventory identical to the earlier run (API stack incl. strata_memory_policy.py --watch only). Every request sent when /metrics was idle. No remote changes, no GitHub.
- Effort: Hermes profile `strata_high` sends reasoning_effort=high (top level and chat_template_kwargs). The chat template maps `high` to `xhigh` (supported values: xhigh, medium, low), so I sent exactly what Hermes sends ("high" = xhigh). Probe on p05 showed the prompt grows (xhigh instruction injected: +38 tokens) and thinking is longer (1457 completion tokens vs ~475 mean at medium).
- max_tokens 32768 (profile has none). Largest completion was 998 tokens, 0 finish_reason=length, 0 errors.
- Same 10 points / same 82-token ban list (bias -100 on the whole output) / same reconstruction (approximate tool schemas, seeds non-reproducible) as the medium run. 2 pairs per point, alternating C/N order, 40 requests (each 2-36 s, so no need to cut reps). Reasoning vs final tokens: the API gives only total completion tokens, so the split is ESTIMATED by character share of reasoning_content vs content+tool-call args.
- Files: state\nowait-hermes-xhigh-20261019\ (requests, responses, results.json, view.txt, scripts).

## Per-point (mean of 2 reps; comp = completion tokens)
| pt | type | prompt tok | comp C -> N | est. reasoning C -> N | est. final C -> N | decode s C -> N | banned words in C | tool valid C/N | quality |
|---|---|---|---|---|---|---|---|---|---|
| p01 | QA | 6687 | 207 -> 193 (-7%) | 200 -> 190 | 8 -> 3 | 5.3 -> 4.6 (-14%) | 2 | 1/1, 0/0 | same (C rep1 made a needless session_search) |
| p02 | QA | 6684 | 144 -> 105 (-27%) | 138 -> 102 | 6 -> 4 | 3.5 -> 2.3 (-34%) | 6 | -, - | same |
| p03 | QA/tool | 6898 | 134 -> 196 (+45%) | 130 -> 180 | 5 -> 15 | 3.3 -> 4.8 (+49%) | 5 | 2/2, 2/2 | minor-diff (N rep1 added an extra terminal call) |
| p04 | QA | 8991 | 251 -> 220 (-12%) | 168 -> 108 | 82 -> 113 | 5.8 -> 5.5 (-4%) | 8 | -, - | same |
| p05 | QA | 9048 | 694 -> 916 (+32%) | 686 -> 875 | 8 -> 42 | 16.7 -> 21.8 (+30%) | 23 | 2/2, 1/1 | minor-diff; borderline: N rep2 browser_exec with empty args |
| p06 | reasoning, no tools sent | 7467 | 172 -> 122 (-29%) | 78 -> 58 | 93 -> 64 | 4.5 -> 3.2 (-29%) | 1 | n/a | minor-diff (same intent, one rep identical) |
| p07 | tool | 7640 | 255 -> 100 (-61%) | 232 -> 88 | 22 -> 12 | 6.4 -> 2.6 (-60%) | 0 | 2/2, 2/2 | minor-diff (N skips search_chats, goes straight to list_messages) |
| p08 | tool | 9466 | 270 -> 188 (-30%) | 224 -> 160 | 46 -> 28 | 6.0 -> 4.3 (-29%) | 3 | 2/2, 2/2 | same (rep2 identical calls) |
| p09 | tool | 6705 | 467 -> 233 (-50%) | 438 -> 207 | 28 -> 26 | 11.1 -> 5.6 (-50%) | 11 | 2/2, 2/2 | minor-diff (N fewer/different lookups) |
| p10 | tool | 7194 | 544 -> 494 (-9%) | 527 -> 450 | 16 -> 44 | 12.8 -> 12.2 (-5%) | 12 | 2/2, 2/2 | minor-diff (same first skill_view, extra lookups vary) |

## Aggregate (20 pairs)
- Completion tokens: sum C 6274 -> N 5534 (-11.8%); per-point-mean delta median -19.5%, mean -14.8%.
- Decode time: sum 151 s -> 134 s; per-point median -21.3%, mean -14.6%. (Wall total 237 -> 219 s; wall is cache-order confounded, use decode.)
- Estimated reasoning tokens: sum 5644 -> 4834 (per-point median -25.8%, mean -18.4%); estimated final/tool-call tokens 630 -> 700 (flat).
- Banned words: control 71 (11.3 per 1k tokens; medium run was 8.8 per 1k), NoWait 0.
- Quality: same 4 (p01, p02, p04, p08), minor-diff 6, worse 0 definite (1 borderline: p05 N rep2 empty-args browser_exec). Tool calls all valid except where no tools were defined (p06); control also had no invalid calls here.
- Spread: same-arm reps differ a lot (e.g. p09 C 658 vs 276), so per-point deltas are noisy; 6 of 10 points favour N by >=12%, 2 are worse (p03 +45%, p05 +32%), 2 are roughly flat (p01, p10).

## Comparison with medium effort (earlier run, 30 pairs)
- Medium: NoWait +1.9% tokens (pooled), median per-point +14%, decode time flat (163 s vs 163 s) -> no benefit.
- xhigh: -11.8% tokens, -11% decode time (151 -> 134 s), banned-word density slightly higher in control. Direction is consistent with the paper (larger savings when thinking is longer), but xhigh thinking here is still short (control mean 314 tokens/run vs 217 at medium), so the effect is modest and within noise for individual points.

## Limitations
- n=10 points x 2 reps; seeds not reproducible; split of reasoning/final tokens estimated by characters; tool schemas reconstructed; bias hits the whole output (tool args, final answer), not just thinking; quality judged by me side by side only.
- Significance: not tested; the aggregate -12% is of the order of the control run-to-run spread (stdev ~35% per run), pooled over 20 pairs the standard error is roughly 8-10%.

## Recommendation
At medium effort NoWait is not worth it; at xhigh it showed a modest ~12% token/decode reduction with no detected quality loss but a weak statistical signal. If pursued, test with more reps (>=5 pairs per point) and, ideally, a thinking-phase-only bias so tool arguments and the final answer are not constrained. Not enough evidence to enable it by default.
