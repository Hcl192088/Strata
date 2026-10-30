# Task027 continuation: lossless RAM screen and GPU packed-layout feasibility

Authorization: user 2026-10-29 "好去做", following the proposal to screen RAM compression first and inspect GPU packed layout. No live stop, inference requests, deployment, model/source modification, package installation, or system privilege change.

Current identity rechecked remotely: DESKTOP-LKMLUPC; unique live PID27744; binary A1E6123852A5138A9B3A5DE2F51FC273466B7E349819A5D2FCD49120D9491AD8; config 060F2FBCCC54543904C6A14660C78581782DD0DCA5B972D8DA27DF4946893D93; source f520bc5e9d31c93caeb296b059e3a3eaa16e493f, clean isolated source; canonical HEAD2f1e998 with unrelated dirty files preserved. Remote BEST manifest agrees. API loaded/idle,3153 slots/20479MiB arena. GitHub inbox011 and existing task branches are historical/consumed; direct continuation of LUNA-20261012-027, no new claim.

## Checklist direction answers
1. Goal50tok/s; recent historical pipeline46.66-49.37, gap0.26-1.43ms/token; no fresh throughput benchmark in this unit.
2. Old pre-pipeline join6.09ms/window, GU11.88,down5.16. Detailed decomposition stale for liveA1E6; not a current performance forecast.
3. Target SSD capacity misses and GPU quantized dense projection layout. Compression cannot save more than exposed I/O wait; current exposed fraction unknown. GPU old dense group6.24ms/window is stale; packed eligible subset unknown. No speed promise.
4. New lossless-representation screening, not a repeat of PCIe/workers/spec knob families.
5. Do not repeat mapping shadow/PATCH4/full-head. Codec availability checked first; zstd/lz4 absent. Preselect Windows XPRESS-Huffman(buffer mode),stdlib zlib level1 and lzma preset1 as three independent arms; no failure substitutions.
6. Miss,placement,overlap,work reduction and mainline reviewed; this unit only lossless storage and GPU representation feasibility.
7. Existing negative results retain their causes. Incompressible bytes/decoder cost closes only tested codecs; inability to discard original GPU layout is an engineering dependency, not negative kernel speed evidence.

## Registered compression design
- Structural feasibility diagnostic, not engine A/B. Read exact pack experts.bin using native_experts.txt layer offset/blob_bytes, never GGUF source offsets.
- 48 layers x experts0,257 =96 deterministic blobs, all10 gate/up-down type pairs. Read-only input; one expert live at a time. Single thread, BelowNormal, no CUDA.
- All three codecs compress each blob once; check exact decompressed bytes and SHA256; seven warm decompression timings per blob and byte-copy reference. Rotated codec order by sample index. Keep data only in memory, write small metrics/hashes only.
- Time budget240s; deadline stops own loop cleanly and records PARTIAL, no kill/relaunch. Before every layer: fresh process inventory, binary/config identity, live idle and availableRAM>=1GiB. Stop on unclassified diagnostic/build/inference process, identity change, active API generation, codec error or any mismatch. Preserve partial results, no codec substitution.
- Primary: aggregate compressed/raw ratio including each stream's framing; per-format ratios and decoder MB/s/ns per byte; theoretical20GiB capacity equivalent excluding metadata/scratch. Do not claim model tok/s.
- Screen gate: at least10% byte saving(ratio<=0.90) AND aggregate decoder throughput>=3.0GB/s(decimal), exact parity. This is a practical initial gate, not proof of net gain: >=10% capacity gain and less than~0.6ms/expert decode at1.8MB. Failing either means NO_GO_FOR_TESTED_CODEC in this unit; do not add codec levels or sample after seeing results. Passing only warrants accounting/simulation, not full implementation.
- Coverage:2/512 experts/layer(0.390625%),96/24576 experts. Full layer/type coverage, not full weights/resident/miss-frequency coverage. Decoder measured with Python allocation/wrapper costs, BelowNormal/live API idle; not multithreaded C++ or production latency.

## GPU layout inspection
Read pinned source only: native_dense,packed registry/kernels,TensorRef ownership,prefill/verify/MTP consumers and actual model dtype/shape metadata. Calculate eligible packed bytes; no pack/build/kernel microbench. Determine whether replacing original allocation is supported now and what must change. No new fallback or abstraction.

## Operations/action list
- Only this bounded screen may run; no subagents or background automations. SSH strict host-key and hostname verified.
- Record errors/progress/results under remote runs/lossless-screen-20261029 and local matching directory. Verify original live PID/config/binary/health after work.
- Complete screen,source feasibility,report and append-only Task027 follow-up; commit/push only task-scoped handoff/tool/report files per user instruction, preserving all unrelated changes. GitHub coordination outbox uses existing two-stage workflow if published; never direct Git outbox write.
