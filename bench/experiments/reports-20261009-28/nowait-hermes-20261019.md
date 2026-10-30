# NoWait A/B on live Strata API with real Hermes contexts (2026-10-19)

## Setup
- Host DESKTOP-LKMLUPC verified. Running strata.exe PID 27340 = runs\ram-lru-20261013\build\strata.exe, SHA256 366A355E...5015E2 (matches current-best). Engine 0.1.42, Qwen3.8-Flash-Next-GSQ-RCO-IQ3_XXS.
- Extra processes (launcher start_task020_api.ps1, strata_memory_policy.py --run/--watch, serve.server) confirmed by coordinator as the normal API stack.
- Endpoint: /v1/chat/completions on <desktop-tailscale-ip>:8080. Returns reasoning_content separately, usage and timings (prompt_ms, predicted_ms). logit_bias accepted (token-id string keys). `seed` is accepted but NOT reproducible (3 identical seeded requests gave 93/74/86 tokens; speculative decoding / non-determinism), so C and N are not paired token-for-token; different seeds per rep.
- Sampling (config.yaml strata_medium): temperature 1.0, top_p 0.95, top_k 20, min_p 0, presence_penalty 0, chat_template_kwargs {enable_thinking:true, reasoning_effort:medium}. max_tokens 4096 (no Hermes value found; server --max-new 1024).
- Token list: paper (2506.08343) keywords (17): wait, alternatively, hmm, but, however, alternative, another, check, double-check, oh, maybe, verify, other, again, now, ah, any. Paper matches by substring over the vocab and then prunes by hand; I used exact-word tokens only (optional single leading space, any case). Read from the model GGUF vocab (gpt2/qwen35 BPE, 248320 tokens): 82 token ids, bias -100 (nowait_tokens.json). "double-check" has no single token. Bias applies to the whole output (reasoning, content, tool-call JSON) - the API has no thinking-only scope.
- Points: 10 real Hermes assistant turns (DB copy, read-only), reconstructed: system prompt from system_prompts table, active history, session_meta rows dropped. Prompt 6.6k-9.4k tokens. Tool definitions are NOT stored in the DB: rebuilt from the session's tool_names with minimal schemas (names + param keys inferred from past calls), so tool-call behaviour is approximate. p06's session had no tool list (no tools sent).
- Design: per point 1 primary pair (rep1) + 2 extra replicate pairs (r2, r3, new seeds) because single samples are very noisy; 60 requests total (more than the ~20 briefed; each took 2-20 s). Order alternated by point/rep. All requests were sent when /metrics was idle.
- Files: state\nowait-hermes-20261019\{requests,responses,results.json,points.json,nowait_tokens.json,*.py,view.txt}.

## Per-point (C = control, N = NoWait; mean over 3 reps; decode = timings.predicted_ms)
| pt | type | prompt tok | rep1 comp C->N | mean3 comp C->N | decode s C->N | banned words in C (3 reps) | tool valid C/N | quality |
|---|---|---|---|---|---|---|---|---|
| p01 | plain QA | 6649 | 50->71 (+42%) | 51->72 (+41%) | 1.5->1.9 (+31%) | 0 | - | same |
| p02 | plain QA (trivial ping) | 6646 | 86->194 | 104->119 (+15%) | 2.6->3.0 (+17%) | 5 | 2/2, 0/0 | minor-diff: C itself alternates tool call vs text; N always text |
| p03 | QA / tool | 6860 | 71->71 | 93->69 (-25%) | 2.0->1.5 (-28%) | 3 | 3/3, 3/3 | same (cronjob_manage list, 3/3) |
| p04 | multi-turn QA | 8953 | 154->179 | 146->166 (+13%) | 3.0->3.7 (+21%) | 2 | - | same (same conclusion) |
| p05 | QA, open-ended | 9010 | 397->657 (+65%) | 475->616 (+30%) | 11.7->14.9 (+27%) | 22 | 2/2, 2/2 | minor-diff: different strategy per run in both arms (direct answer vs tool lookup) |
| p06 | reasoning, no tools sent | 7429 | 162->221 | 168->178 (+6%) | 4.8->5.1 (+8%) | 0 | n/a | minor-diff (same intent, search_files/cronjob_manage varies) |
| p07 | tool | 7602 | 115->135 | 220->112 (-49%) | 5.6->2.7 (-51%) | 3 | 3/3, 3/3 | minor-diff (same beeper search/list family) |
| p08 | tool | 9428 | 245->219 | 178->214 (+20%) | 3.9->4.9 (+24%) | 1 | 3/3, 3/3 | minor-diff (terminal vs execute_code vs list_messages, all plausible) |
| p09 | tool | 6667 | 351->541 (+54%) | 275->329 (+20%) | 6.9->8.0 (+17%) | 9 | 3/3, 3/3 | minor-diff |
| p10 | tool / reasoning | 7156 | 402->383 | 456->330 (-28%) | 12.1->8.6 (-29%) | 12 | C 1/2, N 3/3 | minor-diff: C sometimes answers directly, N always does a lookup call |

Quality tally (judged on the reps per point): same 3 (p01, p03, p04), minor-diff 7, worse 0, better 0. Tool calls: all N calls parse and name defined tools (p06 has no tools defined, excluded); C had one call to a tool name not in the reconstructed list (p10 r2). Banned words in N output: 0 in all 30 runs (the bias works). No finish=length, no errors.

## Aggregate
- Completion tokens, rep1 only (10 pairs): median Delta +26.9%, mean +34.2% (sum 2033 -> 2671, +31%): NoWait longer.
- All 30 pairs: median +5.9%, mean +12.7%; sum 6499 -> 6620 (+1.9%).
- Per-point means over 3 reps: median +14.1%, mean +4.3% tokens; decode-time median +16.7%, mean +3.7%. Total decode time over all runs 163 s vs 163 s.
- Wall time is confounded (the second request of each pair hits the prefix cache: cached_tokens ~= prompt; first arm pays ~7-10 s prefill), so use decode time. Wall per-point median -3.9%, mean +6.1% = noise from ordering.
- Reasoning chars total: C 17.7k vs N 20.6k.
- Control run-to-run spread: mean within-point stdev of completion tokens 65 (~35% of mean), larger than any NoWait effect. Seeds do not reproduce.
- Quality regressions: 0 detected.

## Limitations
- Medium-effort Hermes turns produce short thinking (control median ~150 tokens, only 57 banned words in 6.5k tokens), so there is little "wait" overthinking to remove; the paper's gains come from long CoT.
- Bias covers the entire output including common words (but, now, any, other, check, maybe...) which cannot be avoided in tool arguments/final text; the model compensates by rewording, sometimes longer.
- Tool schemas approximated; Hermes max_tokens unknown; n=10 points x 3 reps; non-reproducible sampling; no ground truth beyond own side-by-side judgement; first-arm prefill vs cached-prefix confound for wall time.

## Recommendation
Do not adopt NoWait for the Hermes workload as configured: no token or time saving (pooled +2% tokens, 0% decode time, high variance), no measurable quality loss either. Revisit only for high reasoning-effort / long-CoT requests, ideally with a thinking-phase-only bias (needs engine support) and a larger sample.
