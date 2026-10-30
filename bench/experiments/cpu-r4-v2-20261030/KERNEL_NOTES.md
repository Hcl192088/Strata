# R4 v2 kernel candidate

Status: IMPLEMENTED LOCALLY; no SSH, compilation, benchmark, engine integration or quality claim by this worker.

Owned files: r4.cpp, inverse.inc, build.cmd, this note. Parent owns all harness/controllers/plans/reports and remote gates. Prior experiment files were not changed.

## API and explicit variants

All existing exports remain: r4_size, r4_pack, r4_unpack, r4_dequant, r4_dot. Existing r4_dot deliberately remains the pinned old AVX2 implementation. New benchmark entry:

```cpp
extern "C" void r4_dot_variant(
    int variant, int type, int h, int rows, int nt,
    const void* packed, const void* const* activation, float* output);
```

- variant0: old AVX2 kernel, selected from the pinned source's non-AVX512/non-VNNI branches.
- variant1: same R4 layout with AVX-VNNI integer dot/accumulation.
- variant2: variant1 plus gathered codebook loads for IQ2_S, IQ3_XXS and IQ3_S.

Invalid variants abort. No error-triggered implementation change. Parent must verify AVX-VNNI CPUID support before invoking variants1/2. Type16/17 variant2 intentionally equals variant1; these do not gain a new gather implementation in this unit. The unchanged quantized activation ABI is NativeQ8K292 bytes, without ik_llama.cpp's additional `sum` float.

## Concrete changes

1. IQ2_XXS: replace `madd_epi16(ones,maddubs_epi16(u8,s8))` with `dpbusd_avx(zero,u8,s8)`; original lane permutation, scales and floating accumulation stay in place.
2. IQ2_XS/IQ2_S: combine original signed16 dot and signed32 accumulation with `dpwssd_avx`; nt>1 retains the four independent scaled partials and their original merge order.
3. IQ3_XXS/IQ3_S: enable the reference source's existing AVX-VNNI256 arithmetic branches and provide the MSVC `_mm256_dpbusd_avx_epi32` helper. IQ3_S thereby accumulates four byte-dot groups in signed32 rather than signed16, which is equivalent over its proven range.
4. IQ3_XXS gather: eight original byte indices become eight32-bit indices; scale4 reads the original32-bit grid entries in the same lane order.
5. IQ3_S gather: the unchanged eight assembled16-bit indices are widened and gathered at scale4.
6. IQ2_S gather: four byte indices plus their2-bit upper codes become four32-bit indices; scale8 reads original64-bit grid entries in the same order. No weight transform changed.

## Static correctness evidence

Parsed every codebook constant from the pinned reference/ggml-common.h:

| Codebook | Entries | Byte range | Max absolute unsigned/signed pair dot, using signed input magnitude128 |
|---|---:|---:|---:|
| IQ2_XXS |256|8..43|11008|
| IQ2_XS |512|8..43|11008|
| IQ2_S |1024|8..43|11008|
| IQ3_XXS |256|4..62|15872|
| IQ3_S |512|1..15|3840|

Each pair is below signed16 saturation32767, so removing `maddubs` saturation in the direct dpbusd replacements does not change valid codebook results. The four IQ3_S pairs sum to at most15360, also within signed16. IQ2_XS/S retains `maddubs` and changes only the following dot/accumulate. No claim that an arbitrary unsigned8 codebook has this property.

Exhaustive local arithmetic check of all256 IQ2_S upper-code bytes ×4 lanes ×256 low-code bytes =262144 combinations confirms gathered indices equal the original shift/mask expressions. IQ3 gather uses the original already-assembled indices directly. This is a transform check, not a compiled-kernel parity result.

Removed unreachable HAVE_FANCY_SIMD branches from the candidate copies; no AVX512 intrinsics are retained. Separate namespaces keep variant0's arithmetic intact. Common repack, inverse and dequantization code is shared and unchanged from the previous mechanically validated candidate.

## Build and required parent verification

`build.cmd` uses the previously verified current-best CPU/ggml libraries and source header paths; these are historical parameters until parent revalidates them. It includes ../cpu-r4-20261029/reference/ggml-common.h, whose pinned commit is d4c1f75533ec897f54944f2734ea0d0e89e4fe01. Parent must preserve reference/LICENSE and verify/stage this dependency on the remote run. build.cmd expects parent-provided bench.cpp. Candidate compilation is `/arch:AVX2`, with explicit AVX-VNNI intrinsics; assembly listing r4.asm is requested to inspect nt2/3 spills.

Before timing: compare variants1/2 bitwise against variant0 on identical quantized inputs and full GU outputs, all five types/nt1..3/selected real experts, plus roundtrip/dequant gates. Also compare all variants to current live native GU/down, recording the already-known floating order differences rather than treating matching weights as quality proof. Variant0/1/2 are expected bitwise equivalent but that has not been compiled/verified yet. Gate every format/core separately. After correctness, measure GU-only and combined with the actual pool's Q2_0 down/act_quant_any path, plus pack/inverse costs. Gather being faster on P cores is a test hypothesis, not a hardcoded performance claim.
