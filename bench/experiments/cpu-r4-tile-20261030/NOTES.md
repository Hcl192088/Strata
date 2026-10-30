# R4 row-tile proxy and fair conversion screen

Status LOCAL_READY_NOT_COMPILED. Parent owns remote process/identity gates, build, execution and reporting. This worker performed no SSH/build/benchmark. All prior experiment files remain unchanged.

## New range API

```cpp
extern "C" void r4_dot_range(
 int variant,int type,int h,int totalRows,int nt,
 const void* packed,const void* const* acts,float* out,int r0,int r1);
```

r0/r1 must be within the output geometry and divisible by4. Packed byte offset is `r0 * original_row_bytes`; R4 contains the same row bytes, stored as four-row groups. DataInfo is `{out+r0,acts,totalRows}` while each kernel receives `r1-r0` local rows. Therefore token stride remains totalRows, the output writes the original row coordinates, and no dot block or floating accumulation order is changed. Variants0/1/2 remain old/VNNI/VNNI+gather. Invalid variant/range aborts; there is no implementation selected after a failure.

The candidate copies the delivered v2 r4.cpp, inverse.inc, conversion_fast.inc into this isolated folder, appends conversion include and the new range API. Reference common header remains ../cpu-r4-20261029/reference/ggml-common.h. Parent should verify its existing immutable pinned reference hash and retain its MIT LICENSE. build.cmd still uses the current-best CPU/ggml libraries and emits r4.asm; all paths require parent live verification.

## Independent CLI modes

```text
r4bench.exe tile    2 16 <actual experts.bin> <actual native_experts.txt>
r4bench.exe convert 2 16 <actual experts.bin> <actual native_experts.txt>
```

Replace LP2 with LP15 for E core, and type16 with17/22/18/21. Pinning occurs before any CPU feature call. Environment must preserve live STRATA_IQ3S_MT1=1 and absent STRATA_IQ_MT_MIN. BelowNormal, native geometry2560×640, exact42912972800-byte pack-size assertion. Parent verifies executable/metadata/library/current-best identities and absence of interfering processes before each process. These modes do not stop/restart an API or change model temperature.

Every mode first checks old-pack==fast-pack, old-unpack==fast-unpack==original, fast-unpack(fast-pack(original))==original and exact decoded weight values, for both GU matrices and every loaded expert. Byte and decoded-value totals appear in PARITY. Full packed blobs contain R4 GU and an unchanged copied down matrix; numerical/timing paths use that candidate blob's unchanged down bytes.

## `tile`: source-derived task geometry, not scheduler integration

Actual source formula supplied by parent: phase_tasks=3×(9workers+host)=30, gu_parts=ceil(30/nb). nb1/4/8/16 thus parts30/8/4/2. This bounded screen measures **parts30 and4**, representing nb1 and8, and explicitly omits parts8 and2. It does not run a concurrent nb-expert pool.

- Six selected layers/type,three experts/layer=18experts per process. Samples use the first three of the existing six expert IDs, preserving native metadata source and layer selection.
- A calls the actual native_gu_rows on original part bounds `FF*p/parts .. FF*(p+1)/parts`.
- B1/B2 use the same number of parts but distribute the160 indivisible R4 groups by `floor(160*p/parts)*4`. Boundaries cover every row exactly once, with no overlap, dropped edge or padding computation. B1=VNNI;B2=VNNI+gather, both explicit benchmark arms.
- The full R4 kernel and all range calls have the same per-row integer/floating dot order. Before timing, every selected expert,variant0/1/2,nt1/2/3,parts30/4 compares both gate and up float outputs bitwise against its full-row counterpart. First-expert tests also fill output with a canary and verify each individual part does not write rows outside [r0,r1), unrelated tokens, or the wrong token stride. TILE_BITS is emitted only after these gates.
- Each B also compares complete GU h and down output to partitioned native A, checks finite values and retains the existing mechanical h-error threshold. Record all bit differences/max absolute errors; do not call semantic quality preserved. The original down/activation dispatch remains act_quant_any/q2_rows_any for type42, native_quant_h/native_down_rows otherwise. Down itself is not partitioned in this screen and is identical across arms.
- Each nt/parts cell gets one warmup per A/B1/B2 and three timed passes, order A,B1,B2 → B1,B2,A → B2,A,B1. Six nt/parts cells per process;54 timed passes. TILE_SUM reports median us/expert and A/B ratio. This is only a short mechanism screen; do not assign a formal confidence interval or whole-engine +10% gain.
- No multiworker synchronization, cache contention, actual pool balancing, GPU work, I/O admission or end-to-end language workload is measured. Differently aligned R4 part boundaries are an explicit candidate scheduling requirement, not an already-implemented production scheduler.

## `convert`: fair working set and paired timing

Uses six selected layers/type,six experts/layer=36experts per process, matching the original stream. Old and fast pack both write exactly each Item.packed gate/up locations across that same full36-expert stream. Old and fast unpack both read the same packed stream and write the same inverse buffer's gate and up halves. The one-buffer fast-pack advantage of the earlier cost experiment is eliminated; those earlier mismatched-working-set conversion ratios must not be cited.

Separate pack and unpack tests:one pass per implementation as warmup, then five paired AB/BA passes,0→1/1→0 alternating. CONV_RAW records type,LP,operation(0pack/1unpack),pair,implementation(0old/1fast),us/expert; CONV_SUM records old_us,fast_us,old/fast ratio. Includes both GU matrices per expert. No GU/down timings are repeated in this mode. A slow fast candidate remains reported as slow; no automatic switch to old.

## Expected output completeness per process

- tile:18 ITEM,one COVER/PARITY,34 BOUND,6 TILE_BITS,12 TILE_NUMERIC,54 TILE_RAW,12 TILE_SUM,one DONE.
- convert:36 ITEM,one COVER/PARITY,20 CONV_RAW,2 CONV_SUM,one DONE.

Parent can run the modes independently, preserve raw logs/source hashes, and parse these counts to catch partial output. All five formats×P/E means ten processes/mode. No claim of compiled correctness or measured speed is made until parent completes the declared gates.
