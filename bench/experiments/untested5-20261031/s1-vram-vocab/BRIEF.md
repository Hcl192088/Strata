# Stage S1 — VRAM itemization + smaller MTP draft vocabulary A/B (items 5 and 2) + large-page privilege check (item 4, read-only)

Read D:\strata\state\untested5-20261031\COMMON.md first; all its rules apply. Folder: D:\strata\state\untested5-20261031\s1-vram-vocab\.

## Part A — itemize the ~930 MiB "unattributed" VRAM (read-only + one engine start)
1. From the current-best source copy (read only), list every device allocation at engine startup/decode: cudaMalloc/cudaMallocAsync/pools, cuBLAS/cuBLASLt workspaces, CUDA graph exec memory, GDN/SSM state, KV, verify buffers (sized by --spec), MTP K/V ring, staging buffers, expert cache arena. Give file:line and size formula with the live config values.
2. Start the current-best engine once (no API; same args/env as live config; not a benchmark) and record engine startup VRAM log lines, nvidia-smi used memory before/after, slots. Do not change source; use existing logs. Quit it.
3. Table: item, MiB, source, whether an EXISTING flag/env can shrink it without changing output, MiB freed, slots (0.60 slot/MiB). Explicitly estimate CUDA context/WDDM overhead (not reclaimable).
4. If any existing flag frees >= 50 MiB with output unchanged in principle (e.g. --spec 6 down to the max draft depth the live config can actually use — check it so tokens/window cannot change), add it as an arm in Part B's A/B. Otherwise just report.

## Part B — smaller draft vocabulary (FR-Spec style)
Background: MTP draft head = gather copy of 106,299 rows of the main Q5_K head (178.4 MiB, mtp.cpp ~652; ids in mtp\rt\draft_vocab.bin, 0.4 MB, via --mtp-draft-vocab / default path). Each draft step reads it. Verification is exact, so a smaller subset only changes acceptance/speed, not output.
1. From the existing nsys trace2.sqlite (remote), find the MTP draft kernels (draft head GEMV, draft layer, MoE) and report ms/window for the draft head vs the rest of the draft. No new nsys run.
2. Read the draft_vocab.bin format and how the engine loads it (size restrictions, ordering, alignment). Build two smaller files: V64 (top 65,536) and V32 (top 32,768) ids, subsets of the current 106,299. Frequency source: token ids from text/token data on the remote that is NOT the Hermes p01–p10 outputs used in this A/B (e.g. neuro.tokens prompt, other prompts, prior non-Hermes outputs, tokenized prompt text files already on disk). Always include special/control tokens present in the current subset. Report coverage: fraction of Hermes output tokens from PRIOR runs (existing raw outputs) inside V32/V64 (upper bound on lost acceptance).
3. Engine A/B with the gpu6-ab harness: arms C (current), V64, V32 (plus the Part A flag arm only if one qualified). Same exe A1E6 and env; only the --mtp-draft-vocab path differs. Freed VRAM raises slots at startup: expected and part of the benefit — record slots per block; gate C at 3153, all arms at 20.00 GiB / 20479 MiB. 5 rounds, arm order rotated each round, 10 Hermes points x 512. After round 3 drop any arm negative in all rounds.
4. Report per arm: tok/s, tokens/window, acceptance if logged, draft ms/w, GPU-reach, CPU, slots, ms/window, output lengths and text equality vs C on greedy points. Verdict: positive if CI lower bound > 0, or mean >= +1.5% with mechanism (draft ms down or slots up, tokens/window >= −1%).

## Part C — large pages (read-only)
Run `whoami /priv` as the account that runs Strata and grep an engine startup log for the large-page attempt message. Report whether SeLockMemoryPrivilege is present. Do NOT grant or change anything.

## Report
RESULT.md (Traditional Chinese): Part A table, Part B trace numbers, coverage, A/B tables and verdict, Part C finding, identity and process gates, API left not running (verified).
