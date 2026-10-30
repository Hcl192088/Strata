# Task027 continuation: RAM quota / LFUSE

Status: STOPPED_BY_USER_NO_PROMOTION; REPORT_LOCAL. User requested early termination on 2026-10-29. No deployment.

LFUSE: six complete paired rounds / 120 formal requests, plus C/F/C smoke nine requests. Mean paired speed change -1.255%; five of six rounds negative. Pooled C 47.316, F 46.698 tok/s (different token totals, so primary is the paired-round mean). No useful acceleration observed; reject candidate for this configuration. This is not the preregistered eight-round result; no full-test CI or statistical significance claim.

|Round|C tok/s|LFUSE tok/s|Change|
|---|---:|---:|---:|
|1|48.753|48.275|-0.981%|
|2|48.162|46.922|-2.575%|
|3|45.584|45.664|+0.177%|
|4|46.987|46.370|-1.313%|
|5|47.182|46.661|-1.103%|
|6|47.086|46.268|-1.737%|

Coverage: all ten captured Hermes points in each of twelve complete fresh-engine formal blocks. Original temperature1.0/top_p.95/top_k20/min_p0/seeds1001..1010 preserved; max_tokens512 only. Same A1E6...91AD8 binary/config060F...93D93,3153slots/20GiB/20479MiB,AboveNormal; only candidate env STRATA_LFUSE=1. Complete blocks passed runtime/capacity/error/repetition guards. Source contract and smoke do not prove operator bitwise or semantic quality parity. Current runtime branch activation has no dedicated kernel counter. Partial round7 C six responses remains raw and is excluded; round7 F and round8 not run. Raw remote runs/lfuse-ab-20261029-attempt2; no private prompts/responses copied into this report.

Termination engineering record: stop.py first checked ownership but failed while inspecting an expired distant ancestor; it did not terminate any process. Its presence was detected by the live benchmark process gate, which stopped partial round7 and invoked existing cleanup/finally restore. A second stop check found campaign already restoring and performed no termination. Raw campaign phase FAILED/PROCESS_GATE is preserved, not rewritten as normal completion; analytical status STOPPED_BY_USER is separate. No unrelated process stopped. Initial attempt1 C smoke stopped because our broad MISMATCH guard matched normal check_mismatch_rows=0; guard corrected before fresh attempt2, old run retained and excluded.

Original API restored at19:30:12; independently rechecked PID1356,loaded,idle,AboveNormal,current-best binary/config hash,all original env,3153slots/20479MiB. No test process remained at independent process gate. No temperature/source/live-setting change.

RAM quota bounded offline screen: full8623-window old neuro trace/all48layers,engine-LRU baseline matched all11 requests. Training requests0-4 to heldout5-10 reduced SSDbytes14.1055%,below25%gate. All-data finite-grid conservative DP18.6909%,not a global upper bound. No live allocation change or tok/s forecast. Full coverage/limitations in RAM_RESULT.md.

Publication: reports remain local and in the same remote run directory. Earlier automatic approval review rejected report commit/push pending explicit payload-to-GitHub approval; no retry or alternate publication. No GitHub publication or deployment.
