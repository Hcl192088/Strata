# Codex brief: NT1_EXT phase 2 whole-engine C/B A/B (Strata, LUNA-20261012-027 continuation, REPORT_LOCAL)

User authorized (2026-10-30): stop the live API for this A/B only, run it, restore the API. NOT authorized: deploying, changing live config/tasks permanently, source/git changes on the remote (except new run dir), pushing anything, GitHub publication, changing temperature/sampling.

## Rules
- Read D:\strata\AGENTS.md and remote C:\Users\User\Strata-Adrian-control\AGENTS.md first; obey them.
- SSH: `ssh User@<desktop-tailscale-ip>` (Tailscale, DESKTOP-LKMLUPC), strict host key checking. Remote default shell is cmd. Write scripts locally, scp them, run them; don't inline complex PowerShell over SSH.
- Disconnect: if SSH fails continuously > 10 minutes, stop retrying; run local `tailscale status` to tell laptop side (can't reach coordination server) vs desktop offline; write that into the report and stop. The remote controller must be detached (Task Scheduler) so it finishes and restores the API even if the laptop disconnects.
- Before anything remote: process gate (only the live API stack may exist: serve.server python, strata_memory_policy.py --run and --watch wrappers, strata.exe at C:\Users\User\Strata-Adrian-control\runs\native-pipe-deploy-prep-20261029\build\strata.exe). Live exe SHA256 must be A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8, config SHA 060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93. Any unknown Strata/bench/build/diag process or mismatch -> stop and report, do not kill.
- Candidate binary: C:\Users\User\nt1ext-20261030\build\strata.exe, must hash FD272B491C4498D4F6F31546B5E1E26BAAD744DE837174F6A507B98718FC129A (built from commit 27fa1c5 = f520bc5 + 36-line patch adding opt-in env STRATA_IQ_NT1_EXT). Do not rebuild.

## Harness (reuse, do not invent a new one)
Copy the pattern of remote C:\Users\User\Strata-Adrian-control\runs\r4-engine-20261030\controller.py and run.ps1 (local copies in D:\strata\state\r4-engine-20261030\). It imports `base` from runs\big-exact-20261030 (c.identity, c.gate, c.verify, c.run, c.rate, ns.stop_api, ns.restore_api). Create a NEW run dir C:\Users\User\Strata-Adrian-control\runs\nt1ext-ab-20261030 (assert it doesn't already contain campaign.json; no reruns over old dirs). Changes vs the R4 controller:
- No build phase.
- spec(arm): C = ns.EXE_C (current best A1E6), env {'STRATA_NATIVE_PIPE':'1'}; B = candidate exe above with sha checked, env {'STRATA_NATIVE_PIPE':'1','STRATA_IQ_NT1_EXT':'1'}. Everything else identical (strict_capacity True, split False, same serve dir, same sampling = original Hermes sampling from c.make_body, 10 points x 512 tokens). Verify by reading each block's effective env/config that both arms have STRATA_IQ3S_MT1=1, STRATA_IQ_MT_MIN absent, and only exe path/cwd/per-block log/the STRATA_IQ_NT1_EXT env differ. Allowed config diffs are exactly those.
- B blocks must contain the engine log line "STRATA_IQ_NT1_EXT active" (assert, else CANDIDATE_NOT_EXERCISED). C blocks must NOT contain it.
- Order: 5 rounds, alternating order: CB, BC, CB, BC, CB (10 blocks). c.gate before every block.
- Early stop: after round 3, if all 3 per-round paired B/C ratios are negative, or mean paired < -3%, stop adding rounds (still restore).
- Capacity must be 3153 slots / 20.00 GiB / 20479 MiB in every block; engine priority AboveNormal.
- Priority: register the Windows scheduled task with task Priority = 2 (NOT the default 7; P7 is known to be slower). Use the same principal as the existing API task (verified User principal; do not guess USERDOMAIN). After launch, confirm the task's priority setting reads 2 and the engine process is AboveNormal. Time limit 3 hours.
- finally: restore the live API exactly as before (ns.restore_api) and run c.verify; write restore.json, final_verify.json.

## Outputs per block
tok/s (c.rate), tokens, windows, and engine-reported per-window segments (GPU-reach wait, CPU ms/window, draft, ms/window) parsed from engine.log decode timing lines; output lengths; any errors.

## After it finishes, independently verify (separate SSH check)
Live API: single strata.exe, SHA A1E6, config 060F, AboveNormal, loaded, 3153/20479, /metrics idle, no leftover controller/bench processes, scheduled test task disabled or removed (only the test task you created).

## Report (write to D:\strata\state\nt1ext-ab-20261030\RESULT.md, also copy result.json/blocks.json/restore.json/final_verify.json there)
- gates, run dir, task name and its priority readback;
- per-block table and per-round paired B/C %, mean, 95% CI (t, df = rounds-1), engine CPU ms/window paired diff;
- output length difference C vs B;
- restore verification;
- any deviation. Do not claim deployment or quality; quality = float-order-only change, unconfirmed semantically.
Then stop. Do not deploy, do not start other experiments.

## Attempt 2 note
Attempt 1 stopped at the process gate on PID 17208 vctip.exe and PID 7312 mspdbsrv.exe. The coordinator verified both were created 14:05:46-47 by the phase-1 candidate build (exe written 14:16), parents gone, no active build, and stopped them under the user's standing authorization for stale Strata leftovers. Attempt 1 report kept as RESULT.attempt1-blocked.md. Re-run the full process gate fresh; if anything else unclassified appears, stop again. To avoid truncated process listings, write the full inventory to a file on the remote and copy it back.
