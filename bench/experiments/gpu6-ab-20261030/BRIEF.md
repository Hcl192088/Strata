# Codex brief: GPU6_BUNDLE_AB whole-engine C/B A/B (Strata, LUNA-20261012-027 continuation, REPORT_LOCAL)

User authorized (2026-10-30): stop the live API for this A/B only, run it, restore the API. NOT authorized: deploying, permanent live config/task changes, source/git changes, rebuilding, pushing, GitHub publication, changing sampling/temperature.

## Rules (same as the previous NT1_EXT run, which you executed successfully: D:\strata\state\nt1ext-ab-20261030\ has your BRIEF, controller.py, preflight.py, launch.ps1, inventory.ps1, RESULT.md — reuse them)
- Read D:\strata\AGENTS.md and remote C:\Users\User\Strata-Adrian-control\AGENTS.md first.
- SSH `ssh User@<desktop-tailscale-ip>` (DESKTOP-LKMLUPC), strict host key. Remote shell is cmd; scp scripts and run them.
- Disconnect: SSH failing continuously > 10 min -> stop retrying, run local `tailscale status` to tell laptop side vs desktop offline, report and stop. Controller must be detached (Task Scheduler) so it restores the API even if the laptop disconnects.
- Full process gate before anything (write full inventory to a remote file and copy back; no truncation). Only the live API stack may exist. Live exe SHA A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8, config SHA 060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93. Unknown process or mismatch -> stop and report, do not kill.

## Design
- New run dir C:\Users\User\Strata-Adrian-control\runs\gpu6-ab-20261030 (assert no existing campaign.json).
- BOTH arms use the current-best exe A1E6 (ns.EXE_C). C env = {'STRATA_NATIVE_PIPE':'1'} as in current best. B env = C env plus exactly: STRATA_DF_BRANCH=1, STRATA_MMVF_ROWS=1, STRATA_DF_QB_Q4=1, STRATA_DF_PLE=1, STRATA_ATTN_LANECELL=1, STRATA_EXPERT_V2=1. Nothing else differs except per-block log/cwd if the harness does that. Verify from each block's config audit / process environment that both arms have STRATA_IQ3S_MT1=1, STRATA_IQ_MT_MIN absent, and B has exactly those six extra vars, C has none of them. Do NOT include GDN_SPLIT, TSUM, LFUSE, QFUSE, FUSE_HEAD_GR, GR_DOWN_MAX4 (known broken/unresolved).
- 5 rounds alternating CB, BC, CB, BC, CB; 10 Hermes points x 512, original sampling via c.make_body. c.gate before every block. Capacity 3153 / 20.00 GiB / 20479 MiB, engine AboveNormal every block.
- Early stop after round 3: all three paired B/C negative, or mean < -3%.
- Abort the run (and restore) on any fatal/CUDA error in an engine log, or if a B response shows an obvious repetition loop (same >=30-char span repeated >=4 times consecutively); record which.
- Scheduled task priority = 2 (read it back), same principal as the existing API task, PT3H. Disable the test task at the end.
- finally: ns.restore_api, c.verify; write restore.json, final_verify.json.

## Report: D:\strata\state\gpu6-ab-20261030\RESULT.md (+ copies of result.json, blocks.json, restore.json, final_verify.json)
Per-block table (tok/s, tokens, windows, GPU-reach wait, CPU, draft, ms/window, output lengths, errors); per-round paired B/C % and paired GPU-reach diff; mean, 95% t CI (df = rounds-1); output-length comparison; restore + independent post-run verification (single strata.exe, A1E6, 060F, AboveNormal, loaded, 3153/20479, idle, no leftovers, test task disabled); deviations. No deployment, no quality claim. Then stop.
