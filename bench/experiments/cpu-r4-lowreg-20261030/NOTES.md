# IQ3_S low-register candidate

Status NOT_RUN_SCOPE_REFOCUSED. The user clarified that this stage should add substantial, untried, quality-preserving directions to the plan rather than run every small test. These local reviewable sources are saved; no compilation or benchmark is scheduled by this worker. Parent owns any future remote gates/build/run. No SSH, compilation, benchmark or source integration by this worker. Files are isolated copies under cpu-r4-lowreg-20261030; v2/cost/tile remain unchanged.

## Concrete mechanism and contract

Parent's compiled v2 assembly inspection found29 static YMM stack-access instructions in gathered IQ3_S nt3. That is evidence of register pressure, not proof that every access is a hot-path spill or that removing it speeds the engine. The previously measured token split2+1 was slower and does not count as successful spill reduction.

The new kernel keeps only one decoded qx/sign group live at a time. Each of the four compile-time stages decodes its existing eight grid indices, constructs its sign vector, and applies that vector across all tokens. Three temporary integer sums (at nt3) accumulate the same four byte-dot products in the original order. After those stages, multiply by the original scales and add to the original per-token isum. After all eight32-value chunks of a256-value block, retain the original float scale/FMA; at row end retain the original two-half float addition. The four-row R4 weight layout, Q8_K292-byte activation, codebook/sign/scale values and quantization do not change.

The tradeoff is intentional: each stage loads the same32-byte activation again, so up to four loads replace the previous one load per token/chunk. Weight decode remains once per stage shared across tokens, unlike split2+1. Compiler scheduling might still extend lifetimes or create spills; assembly and measured time must decide. No compiler barrier or speculative architecture layer was added.

## Explicit entry and scope

```cpp
extern "C" void r4_dot_lowreg(
 int variant,int type,int h,int rows,int nt,
 const void* packed,const void* const* acts,float* out);
```

Only type21,nt2/3,variant1/2 are supported. Variant1 retains scalar codebook decode;variant2 retains gather. Unsupported arguments assert/abort, never silently call an older kernel. Original exports remain available as explicit controls. The candidate includes the already delivered conversion include, but does not measure conversion here.

## Four suggested parent cases

```text
r4bench.exe 2  2 2 <actual experts.bin> <actual native_experts.txt>
r4bench.exe 2  3 2 <actual experts.bin> <actual native_experts.txt>
r4bench.exe 15 2 1 <actual experts.bin> <actual native_experts.txt>
r4bench.exe 15 3 1 <actual experts.bin> <actual native_experts.txt>
```

CLI arguments are lp,nt,explicit_old_variant,experts,metadata. Parent must reconfirm LP/core and VNNI capabilities, current-best/config/source identities, actual pack metadata, idle API and relevant process inventory before running. Each process pins before CPU feature probes, uses BelowNormal, preserves MT1=1/MT_MIN absent, loads18 real IQ3_S experts over six selected layers (same layer/expert formula as tile), and verifies actual pack geometry/weight byte roundtrip.

Arms0=native,1=oldR4 with explicit variant,2=new low-register with the same variant. Both old/new share the same packed GU/fullblob storage and actual unchanged down/activation dispatch. Native reads its original fullblob. Before performance, old/new gate/up/h and complete down outputs must match bitwise on every selected expert. Any difference aborts; no timing or switch to old after failure. Native-vs-new differences/finite values are separately recorded with the existing mechanical h-error screen; passing it does not establish semantic quality.

One warmup per arm, then three rotated passes A/B/C → B/C/A → C/A/B, separately GU-only and full GU+quant+down. Eighteen LOWREG_RAW per process, four LOWREG_SUM relative to native, two LOWREG_VS_OLD direct comparisons, one LOWREG_BITS/NUMERIC/DONE. Three passes are a bounded mechanism screen, not a formal engine speed claim. No tile/scheduler, I/O admission, model-quality evaluation or promotion.

build.cmd requests r4.asm. Inspect lowreg_iq3s<2/3,true/false> against the corresponding old gather/vnni::mul_mat_iq3_s_r4_q8_k<2/3>, distinguish static stack instructions from dynamic hot-loop occurrences, and report both low-register effect and extra activation-load cost. Static register-count reduction alone does not pass the speed gate.
