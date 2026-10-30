# Direct R4 conversion candidate

Status: LOCAL_IMPLEMENTATION_READY; no C++ build, remote execution or timing by this worker. Parent owns staging, identity/process gates and compiled byte-parity validation. Only conversion_fast.inc and this note were added in this unit; delivered r4.cpp/inverse/build were not changed by the conversion work.

Parent can append `#include "conversion_fast.inc"` to its staged r4.cpp after existing definitions. New exports:

```cpp
extern "C" int r4_conversion_fast_supported(int type);
extern "C" void r4_pack_fast(int type,int h,int rows,const void* src,void* dst);
extern "C" void r4_unpack_fast(int type,int h,int rows,const void* src,void* dst);
```

Types16/17/18/21/22 are all directly implemented. Unsupported types return0 from supported(), and the conversion exports abort on unsupported input. They never call original r4_pack/r4_unpack or choose an implementation after failure. No new cache, expanded model format, persistent metadata, memory allocation, extra model copy, BMI2 or ISA gate is introduced. Scratch is fixed small stack/register data. The APIs retain the original non-overlapping input/output assumption.

## Mechanisms

- IQ2_XXS and IQ3_XXS: process four rows' sign/scale words together in128-bit SIMD. The pinned128-entry scrambled_sign table is exactly the7-bit prefix-XOR transform: `s ^= s<<1; s ^= s<<2; s ^= s<<4; s &=127`. Its inverse is `(s ^ (s<<1)) &127`. Expand the four7-bit fields into byte lanes, compute byte-local prefix XOR, then append the four existing scale bits. The inverse extracts scales and compresses fields back. No dequantization or floating-point conversion.
- IQ2_XS: the same prefix-XOR/one-XOR inverse removes sign table lookups while preserving the low9 codebook-index bits and all scales.
- IQ2_S: copy original four-byte code/sign chunks directly instead of copying each byte individually. Same interleave and scales; speedup is a hypothesis, not a claim.
- IQ3_S: no zero-fill/OR bit accumulation. Repack scales directly from the two contributing original scale bytes. Convert each four-byte sign word via bit-address permutation `j -> rotl5(j,3)`; four SIMD words are processed together. It is the composition of the delta swaps `(D,mask)=(1,0x22222222),(3,0x0a0a0a0a),(6,0x00cc00cc),(12,0x0000f0f0)`; reversing the four operations is the exact inverse. Each delta swap exchanges the relevant two bit positions, so every bit is preserved. Code bytes use a4×8 byte transpose plus column reorder0,4,1,5,2,6,3,7; inverse uses shuffle/unpack and copies exactly eight original bytes per row. Every qh/scales/sign/code byte is explicitly assigned.

## Local transform checks completed

These are deterministic Python algebra/index checks, not compiled C++ results:

- All128 scrambled_sign outputs and inverse values match the pinned table.
- SAS forward equals the original table/shift formula and inverse restores its input for100032 words, including all32 one-bit basis vectors and100000 seeded random words. SAS transform is linear over bits; the complete basis covers the bit mapping.
- IQ3_S sign SIMD formula equals the original nested shift/OR formula and inverses for the same100032 words. All32 basis vectors cover the full bit permutation.
- Symbolic4×8 code-byte transpose and inverse match every original row/column index.
- All65536 pairs of scale-byte values roundtrip exactly through direct scale packing.

Before timing, parent must run both directions against the original functions on every actual selected GU matrix/type, checking old_pack==fast_pack, old_unpack==fast_unpack and fast_unpack(fast_pack(original))==original. Retain the existing exact decoded-weight check as a separate safeguard. A failure must stop and be diagnosed; do not replace the failed fast function with an original call. Then measure pack and inverse in interleaved order on both core types and report actual costs separately from GU speed.
