# User-requested same-layer RAM LRU API trial

Authorization: user explicitly requested starting the LRU candidate for their own Hermes test. This is a trial deployment, not a promotion or proof of Hermes speedup. No API request-content monitoring was enabled.

Host: DESKTOP-LKMLUPC (User@<desktop-tailscale-ip>).

Original 020-C binary SHA256: 803C1EA975038328716FD4AD37BD9A21268A66AC60EB1F5C26171074A14CEF39.
Candidate binary SHA256: 366A355E0E866B12D1793C9D8BE022925305B4560E1AE7DC47F8716C865015E2.
Candidate: C:\Users\User\Strata-Adrian-control\runs\ram-lru-20261013\build\strata.exe.
Source: isolated worktree at runs\ram-lru-20261013\source, base commit 61b3fb5dd3f1e8ec09cf7e4e05208bc6d3c46406, plus candidate.patch preserved beside it and as tools/task027_same_layer_ram_lru.patch.

Active API config: C:\Users\User\Strata-Adrian\runs\iq3-campaign-020\server-task020-8080-v0142.json.
Rollback config: C:\Users\User\Strata-Adrian-control\runs\ram-lru-20261013\api-before-user-lru.json.
Engine log: C:\Users\User\Strata-Adrian-control\runs\ram-lru-20261013\user-lru-api.engine.log.
Launcher: existing Strata-Task020-API; same venv and Python server source.

Only engine exe/cwd/log and STRATA_RAM_LRU=1, STRATA_RAM_LRU_CHECK=0 changed. Model, temperature, sampling defaults, MTP6, tail skip, existing GPU adaptive settings, workers9, ctx100000, explicit PLE direct and 20 GiB resident budget retained.

Implementation: same-layer LRU reuses equal-sized slots in the existing RAM arena after CPU jobs finish; current routed experts, GPU residents and pending adaptive exchanges are protected. There is no additional expert arena or global variable-size allocator. It is distinct from the earlier fixed-GPU global LRU simulation.

Earlier six sequential neuro runs completed with 1024 output tokens each and exit0. Original control: 49.05 and46.18 tok/s; unchecked LRU:48.51 and48.30 tok/s (aggregate +1.66%). Rebuilt-off42.50; byte-checked LRU44.80. Every admission in checked run passed memcpy/memcmp checking. Results do not establish Hermes improvement: output sequences diverged, including between original controls (first difference at output index84), and candidate file MB did not decrease. Raw evidence: runs\ram-lru-20261013\{control-01,rebuilt-off,candidate-checked,candidate-01,control-02,candidate-02}, each with command/result/tokens/stdout/stderr.

Deployment process gate confirmed one original engine and its two Python processes, no benchmark/build process. API was idle before pausing. Initial immediate post-stop gate observed a still-exiting Strata handle and blocked startup; reinspection confirmed all classified processes exited, then candidate was started. No second engine was launched at that gate. Final health and LRU startup verification recorded below.

Coverage: active process/config/binary identities and candidate startup, plus all six numeric neuro results and their detailed timing records. No actual Hermes performance or semantic-answer verification yet. Large logs/token outputs remain remote and outside Git.

Final verification: /health loaded=true; only engine PID30512 runs the candidate path. Startup explicitly reports RAM_LRU enabled, byte parity checks=0, RAM budget20.00GiB /12449 experts and locked resident20.00GiB. CUDA pinning remains0GiB; existing VirtualLock path reports20479MiB. This is not a new pinning improvement.
