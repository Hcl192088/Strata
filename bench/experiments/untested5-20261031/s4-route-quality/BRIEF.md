# Stage S4 — output-changing routing knobs: speed screen + automatic quality metrics (current binary)

Read D:\strata\state\untested5-20261031\COMMON.md first; all its rules apply EXCEPT the "output exactness" rule: these arms deliberately change the output. The user asked on 2026-10-31 to test, after the exact items, the options previously described as quality-reducing. Folder: D:\strata\state\untested5-20261031\s4-route-quality\. Old draft plan for background only: D:\strata\state\QUALITY_EVAL_PLAN_20261027.md (its binaries 366A/8938 are obsolete; use the current-best exe A1E6 only).

Knobs present in the current source (C:\Users\User\native-pipe-generic-20261029, read only):
- STRATA_ROUTE_PRIOR=lambda (src/kernels/cuda/route_prior.cu, verify.cpp:1380): VRAM-resident experts get a logit bonus for SELECTION; weights stay the router's. Upstream 0.2.7 defaulted 1.5 on <=13 GiB cards, 0.2.8 reverted it because of repeated text in long conversations.
- STRATA_ROUTE_RESIDENT=margin (+ STRATA_ROUTE_RESIDENT_RANKS, default 6-9; verify.cpp:70-126, native_router.cu:180): a missed tail expert is swapped for the best resident one within the margin.
- ROUTE_BIAS / GATE_SKIP exist only in the old candidate patch: NOT in scope tonight (do not port).

## Phase 1 — speed screen (greedy, as in gpu6-ab)
Arms: C (current best), RP05 (ROUTE_PRIOR=0.5), RP10 (1.0), RP15 (1.5), RR10 (ROUTE_RESIDENT=1.0), RR20 (ROUTE_RESIDENT=2.0). Same exe/env otherwise. 3 rounds, arm order rotated, 10 Hermes points x 512, fresh engine per block, capacity gate 3153 / 20.00 GiB / 20479 for all. Report tok/s paired vs C, tokens/window, GPU-reach, CPU, join, ms/window, VRAM hit / CPU expert counters if logged, text equality vs C (expected to differ).

## Phase 2 — automatic quality metrics (production sampling)
Pick the 2 fastest arms with mean speed >= +5% vs C (if fewer qualify, take those; if none, stop after Phase 1). Blocks: C, A1, A2, C, A2, A1 (C twice = C-vs-C baseline). Production sampling exactly as the live server uses for Hermes (temperature 1.0, top_p 0.95, top_k 20, min_p 0, thinking enabled, reasoning effort medium — verify against the live server config / make_body), fresh engine per block, fixed seeds per request if the engine supports seeding (same seed across arms).
Request sets per block:
1. Hermes points p01–p10, max_tokens 2048.
2. Objective: the 20 items in objective.json (append its "suffix" to each question; single user turn; max_tokens 2048).
3. Long chains: Hermes p01, p05, p08 continued for 6 turns each: after each model answer append it as the assistant turn and a fixed user follow-up, cycling: 「請再詳細說明。」「還有其他做法嗎？」「請整理成重點。」「換個角度再說一次。」「請繼續。」; max_tokens 1024 per turn. This targets the upstream "repeated text in long conversations" failure.
Save every output (content and reasoning separately, finish reason, token counts) as JSON per block (local + remote; NEVER upload anywhere; Hermes content is private).
Automatic scoring (write score.py; test it on fake outputs first):
- Hard failures: empty answer; finish=length; tool-call JSON unparsable or unknown tool name (for Hermes points whose original answer was a tool call); within-answer loop (any 20-gram, by characters for CJK, appearing >= 3 times in the content, and separately in the reasoning); language drift (answer to a Traditional-Chinese prompt mostly English, or containing >= 5 simplified-only characters — use a fixed list of common simplified-only characters).
- Cross-turn repetition in chains: fraction of each turn's content 20-grams already present in earlier assistant turns of the same chain; report mean and max per arm vs C.
- Objective accuracy: parse the last 「答案：」 line; numeric compare (1e-6 relative) or trimmed exact string.
- Tool choice (Hermes points with tool calls): tool name equal to any tool used by C in either C block.
Verdict per arm (pre-registered): hard failures <= C(per-block mean) + 3; objective accuracy >= C − 1 item per block on average; chain cross-turn repetition mean <= C-vs-C range + 5 percentage points; tool choice not worse by > 1 per block. Report numbers even if they pass. Blind pairwise judging is NOT done by you (Claude will do it later from the saved outputs): just produce pairs.json with Hermes p01–p10 and chain answers paired (C vs arm, and C vs C), randomized X/Y with a separate key file.

Time cap: Phase 1 + Phase 2 together at most 6 hours; if time runs out, finish the current block, score what exists, and report.

Report RESULT.md (Traditional Chinese): Phase 1 table, arm selection, Phase 2 per-arm metrics vs C and C-vs-C, verdicts, limitations (only 10 Hermes points, no new DB extraction, judging pending), API left not running.
