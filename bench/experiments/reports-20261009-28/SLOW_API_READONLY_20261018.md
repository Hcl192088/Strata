Read-only live diagnosis, 2026-10-18, DESKTOP-LKMLUPC.

One Strata engine PID30584, current binary SHA256
366A355E0E866B12D1793C9D8BE022925305B4560E1AE7DC47F8716C865015E2.
Python pairs are venv/base Python and policy/watch wrappers, not extra engines.
Current startup and subsequent request logs confirm resident20.00GiB,
VirtualLock20479MiB, CUDA pinned0,3153GPU slots. No restart/config mutation/test request.

Latest real Hermes:18241prompt,306output,21.6tok/s,49.0%GPU hit,
162/189drafts accepted;98.30ms/window,2.12tokens/window,
jobs24.03ms,CPU37.97ms,GPU-reach27.86ms,draft3.68ms.
Next:22618prompt,18236reused,146output,25.0tok/s,63.3%GPU hit,
74/82drafts accepted;81.11ms/window,2.03tokens/window,
jobs11.86ms,CPU29.41ms,GPU-reach32.31ms,draft3.10ms.
Decode-only fileMB5340.5 and1304.7, respectively. Cumulative engine file bytes
include prompt traffic and must not be attributed entirely to decode.

Historical remote candidate-01 command.json pins SAME binary SHA.
Its neuro output1024,48.5tok/s,69.4%hit,34.05ms/window,
1.65tokens/window,jobs2.69ms,CPU13.78ms,GPU-reach12.34ms.
Historical input/settings/cache state differ; this is a reference, not paired causal A/B.

Live Windows counters while API idle: RAM available346-440MiB,
committed61754384384/64228876288bytes. Hard page input varied7-1365pages/s;
this is evidence of pressure, not proof of continuous heavy pagefile thrashing.
Strata WDDM dedicated11543494656bytes,shared2011168768bytes;
GPU adapter shared2159964160bytes. Shared allocation alone does not prove
specific CUDA weight eviction or explain exact latency.
DWM dedicated counter1318420480bytes,Overwolf ow-obs246734848bytes;
WDDM per-process counters can include allocations/shared resources, not additive residency.
GPU clocks2535/10251MHz,43-44C,P2,PCIeGen4x16 while idle.
Idle clocks/temperature do not establish behavior during past completed requests.
ow-obs PID33420 verified Overwolf OBS executable. No application terminated.

Findings: expert capacity and draft acceptance do not account for restoration failure.
Both CPU/job time and GPU-reach wait are elevated; low system RAM and zero startup
CUDA headroom warrant checking WDDM residency/competition before more MTP tuning.
Introduced23GiB hard minimum has not been A/B validated for throughput; do not label
the memory-policy deployment a speed fix. Highest next diagnostic value is controlled
GPU-budget/headroom comparison with same input and RAM mode, subject to process and
current-best identity gates. No benchmark was launched in this read-only diagnosis.

Coverage: all4retained API request numeric records, full current config/argv/binary hash,
targeted latest110engine-log lines and historical candidate/control log tails,
live memory/GPU/process counters with3memory/shared samples. Not covered: per-kernel
GPU residency trace, load-time clock trace, matched Hermes replay, all historical logs,
game/OBS termination or any causal memory/VRAM A/B. Missing guessed confirmation
stderr/command paths were reported by shell; no evidence taken from those paths.
