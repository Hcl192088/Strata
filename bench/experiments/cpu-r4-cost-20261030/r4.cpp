// Extracted from ik_llama.cpp d4c1f75533ec897f54944f2734ea0d0e89e4fe01.
// Copyright (C) 2024 Iwan Kawrakow; MIT license; see reference/LICENSE.
#include <immintrin.h>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
#define GGML_COMMON_DECL_C
#define GGML_COMMON_IMPL_C
#include "../cpu-r4-20261029/reference/ggml-common.h"
#define GGML_ASSERT(x) do {if(!(x)){std::fprintf(stderr,"R4_ASSERT %s\\n",#x);std::abort();}}while(0)
#define GGML_FP16_TO_FP32(x) _mm_cvtss_f32(_mm_cvtph_ps(_mm_cvtsi32_si128(x)))
#define MM256_SET_M128I(h,l) _mm256_inserti128_si256(_mm256_castsi128_si256(l),h,1)
#define MM256_SET1_M128I(x) MM256_SET_M128I(x,x)
struct DataInfo {float* out;const void* const* input;int rows;void store(int row,int token,__m128 v) const {_mm_storeu_ps(out+token*rows+row,v);}};
// Strata/llama.cpp Q8_K has no ik_llama.cpp-only `sum` float: preserve the live 292-byte ABI.
struct NativeQ8K {float d;int8_t qs[256];int16_t bsums[16];};
static_assert(sizeof(NativeQ8K)==292);
template<int N,typename B>struct Q8 {const NativeQ8K* y[N];Q8(const DataInfo& i){for(int t=0;t<N;t++)y[t]=(const NativeQ8K*)i.input[t];}float scale(int t,int b){return y[t][b].d;}};
inline uint8_t scrambled_sign(uint8_t s) {
    static const uint8_t k_table[128] = {
        0x00, 0x7f, 0x7e, 0x01, 0x7c, 0x03, 0x02, 0x7d, 0x78, 0x07, 0x06, 0x79, 0x04, 0x7b, 0x7a, 0x05,
        0x70, 0x0f, 0x0e, 0x71, 0x0c, 0x73, 0x72, 0x0d, 0x08, 0x77, 0x76, 0x09, 0x74, 0x0b, 0x0a, 0x75,
        0x60, 0x1f, 0x1e, 0x61, 0x1c, 0x63, 0x62, 0x1d, 0x18, 0x67, 0x66, 0x19, 0x64, 0x1b, 0x1a, 0x65,
        0x10, 0x6f, 0x6e, 0x11, 0x6c, 0x13, 0x12, 0x6d, 0x68, 0x17, 0x16, 0x69, 0x14, 0x6b, 0x6a, 0x15,
        0x40, 0x3f, 0x3e, 0x41, 0x3c, 0x43, 0x42, 0x3d, 0x38, 0x47, 0x46, 0x39, 0x44, 0x3b, 0x3a, 0x45,
        0x30, 0x4f, 0x4e, 0x31, 0x4c, 0x33, 0x32, 0x4d, 0x48, 0x37, 0x36, 0x49, 0x34, 0x4b, 0x4a, 0x35,
        0x20, 0x5f, 0x5e, 0x21, 0x5c, 0x23, 0x22, 0x5d, 0x58, 0x27, 0x26, 0x59, 0x24, 0x5b, 0x5a, 0x25,
        0x50, 0x2f, 0x2e, 0x51, 0x2c, 0x53, 0x52, 0x2d, 0x28, 0x57, 0x56, 0x29, 0x54, 0x2b, 0x2a, 0x55,
    };
    return k_table[s];
}
static void repack_iq2_xxs(int nrows, int n_per_row, const block_iq2_xxs * x, block_iq2_xxs_r4 * y, [[maybe_unused]] bool online) {
    GGML_ASSERT(nrows%4 == 0);
    GGML_ASSERT(n_per_row%QK_K == 0);
    int nblock = n_per_row/QK_K;
    const block_iq2_xxs * x4[4];
    uint32_t aux32[2];
    const uint8_t * aux8 = (const uint8_t *)aux32;
    for (int row = 0; row < nrows; row += 4) {
        for (int k = 0; k < 4; ++k) x4[k] = x + nblock*k;
        for (int ibl = 0; ibl < nblock; ++ibl) {
            auto ysas = (uint32_t *)y[ibl].sas;
            for (int k = 0; k < 4; ++k) {
                y[ibl].d[k] = x4[k][ibl].d;
                for (int ib = 0; ib < QK_K/32; ++ib) {
                    std::memcpy(aux32, x4[k][ibl].qs + 4*ib, 2*sizeof(uint32_t));
                    for (int i = 0; i < 4; ++i) {
                        y[ibl].qs[16*ib+4*k+i] = aux8[i];
                    }
                    uint8_t scale = aux32[1] >> 28;
                    uint8_t s1 = (scrambled_sign((aux32[1] >>  0) & 127) << 1) | ((scale >> 0) & 1);
                    uint8_t s2 = (scrambled_sign((aux32[1] >>  7) & 127) << 1) | ((scale >> 1) & 1);
                    uint8_t s3 = (scrambled_sign((aux32[1] >> 14) & 127) << 1) | ((scale >> 2) & 1);
                    uint8_t s4 = (scrambled_sign((aux32[1] >> 21) & 127) << 1) | ((scale >> 3) & 1);
                    aux32[1] = uint32_t(s1) | (uint32_t(s2) << 8) | (uint32_t(s3) << 16) | (uint32_t(s4) << 24);
                    ysas[4*ib+k] = aux32[1];
                }
            }
        }
        x += 4*nblock;
        y += nblock;
    }
}
void dequantize_row_iq2_xxs_r4(const block_iq2_xxs_r4 * x, float * y, int64_t k) {
    auto n_per_row = k/4;
    float * y4[4] = {y, y + n_per_row, y + 2*n_per_row, y + 3*n_per_row};
    int nblock = n_per_row/QK_K;
    uint32_t s32;
    const uint8_t * s8 = (const uint8_t *)&s32;
    for (int ibl = 0; ibl < nblock; ++ibl) {
        const uint32_t * sas = (const uint32_t *)x[ibl].sas;
        for (int k = 0; k < 4; ++k) {
            const float d = 0.125f*GGML_FP16_TO_FP32(x[ibl].d[k]);
            for (int ib = 0; ib < QK_K/32; ++ib) {
                uint32_t aux32 = sas[4*ib+k];
                s32 = aux32 & 0x01010101;
                uint8_t scale = s8[0] | (s8[1] << 1) | (s8[2] << 2) | (s8[3] << 3);
                float dl = d*(2*scale+1);
                aux32 &= 0xfefefefe;
                aux32 ^= (aux32 >> 1);
                for (int i = 0; i < 4; ++i) {
                    auto val = (const int8_t *)(iq2xxs_grid + x[ibl].qs[16*ib+4*k+i]);
                    for (int j = 0; j < 8; ++j) y4[k][QK_K*ibl+32*ib+8*i+j] = dl * val[j] * (aux32 & (1 << j) ? -1 : 1);
                    aux32 >>= 8;
                }
            }
        }
    }
}
static void repack_iq2_xs(int nrows, int n_per_row, const block_iq2_xs * x, block_iq2_xs_r4 * y, [[maybe_unused]] bool online) {
    GGML_ASSERT(nrows%4 == 0);
    GGML_ASSERT(n_per_row%QK_K == 0);
    int nblock = n_per_row/QK_K;
    const block_iq2_xs * x4[4];
    for (int row = 0; row < nrows; row += 4) {
        for (int k = 0; k < 4; ++k) x4[k] = x + nblock*k;
        for (int ibl = 0; ibl < nblock; ++ibl) {
            for (int k = 0; k < 4; ++k) {
                y[ibl].d[k] = x4[k][ibl].d;
                for (int ib = 0; ib < QK_K/32; ++ib) {
                    for (int i = 0; i < 4; ++i) {
                        uint16_t v = x4[k][ibl].qs[4*ib+i];
                        uint8_t s = v >> 9;
                        y[ibl].qs[16*ib+4*k+i] = (v & 511) | (scrambled_sign(s) << 9);
                    }
                    y[ibl].scales[4*ib+k] = x4[k][ibl].scales[ib];
                }
            }
        }
        x += 4*nblock;
        y += nblock;
    }
}
void dequantize_row_iq2_xs_r4(const block_iq2_xs_r4 * x, float * y, int64_t k) {
    auto n_per_row = k/4;
    float * y4[4] = {y, y + n_per_row, y + 2*n_per_row, y + 3*n_per_row};
    int nblock = n_per_row/QK_K;
    for (int ibl = 0; ibl < nblock; ++ibl) {
        for (int k = 0; k < 4; ++k) {
            const float d = 0.125f*GGML_FP16_TO_FP32(x[ibl].d[k]);
            for (int ib = 0; ib < QK_K/32; ++ib) {
                float dl1 = d * (2*(x[ibl].scales[4*ib+k] & 0xf) + 1);
                float dl2 = d * (2*(x[ibl].scales[4*ib+k] >>  4) + 1);
                for (int i = 0; i < 4; ++i) {
                    auto val = (const int8_t *)(iq2xs_grid + (x[ibl].qs[16*ib+4*k+i] & 511));
                    auto signs = x[ibl].qs[16*ib+4*k+i] >> 9;
                    signs ^= (signs << 1);
                    float dl = i < 2 ? dl1 : dl2;
                    for (int j = 0; j < 8; ++j) y4[k][QK_K*ibl+32*ib+8*i+j] = dl * val[j] * (signs & (1 << j) ? -1 : 1);
                }
            }
        }
    }
}
static void repack_iq2_s(int nrows, int n_per_row, const block_iq2_s * x, block_iq2_s_r4 * y, [[maybe_unused]] bool online) {
    GGML_ASSERT(nrows%4 == 0);
    GGML_ASSERT(n_per_row%QK_K == 0);
    int nblock = n_per_row/QK_K;
    const block_iq2_s * x4[4];
    for (int row = 0; row < nrows; row += 4) {
        for (int k = 0; k < 4; ++k) x4[k] = x + nblock*k;
        for (int ibl = 0; ibl < nblock; ++ibl) {
            for (int k = 0; k < 4; ++k) {
                auto signs = x4[k][ibl].qs + QK_K/8;
                y[ibl].d[k] = x4[k][ibl].d;
                for (int ib = 0; ib < QK_K/32; ++ib) {
                    y[ibl].scales[4*ib+k] = x4[k][ibl].scales[ib];
                    for (int i = 0; i < 4; ++i) {
                        y[ibl].qs[16*ib+4*k+i] = x4[k][ibl].qs[4*ib+i];
                        y[ibl].signs[16*ib+4*k+i] = signs[4*ib+i];
                    }
                    y[ibl].qh[4*ib+k] = x4[k][ibl].qh[ib];
                }
            }
        }
        x += 4*nblock;
        y += nblock;
    }
}
void dequantize_row_iq2_s_r4(const block_iq2_s_r4 * x, float * y, int64_t k) {
    auto n_per_row = k/4;
    float * y4[4] = {y, y + n_per_row, y + 2*n_per_row, y + 3*n_per_row};
    int nblock = n_per_row/QK_K;
    for (int ibl = 0; ibl < nblock; ++ibl) {
        for (int k = 0; k < 4; ++k) {
            const float d = 0.125f*GGML_FP16_TO_FP32(x[ibl].d[k]);
            for (int ib = 0; ib < QK_K/32; ++ib) {
                float dl1 = d * (2*(x[ibl].scales[4*ib+k] & 0xf) + 1);
                float dl2 = d * (2*(x[ibl].scales[4*ib+k] >>  4) + 1);
                for (int i = 0; i < 4; ++i) {
                    auto val = (const int8_t *)(iq2s_grid + (x[ibl].qs[16*ib+4*k+i] | ((x[ibl].qh[4*ib+k] << (8 - 2*i)) & 0x300)));
                    auto signs = x[ibl].signs[16*ib+4*k+i];
                    float dl = i < 2 ? dl1 : dl2;
                    for (int j = 0; j < 8; ++j) y4[k][QK_K*ibl+32*ib+8*i+j] = dl * val[j] * (signs & (1 << j) ? -1 : 1);
                }
            }
        }
    }
}
static void repack_iq3_xxs(int nrows, int n_per_row, const block_iq3_xxs * x, block_iq3_xxs_r4 * y, [[maybe_unused]] bool online) {
    GGML_ASSERT(nrows%4 == 0);
    GGML_ASSERT(n_per_row%QK_K == 0);
    int nblock = n_per_row/QK_K;
    const block_iq3_xxs * x4[4];
    uint32_t aux32;
    for (int row = 0; row < nrows; row += 4) {
        for (int k = 0; k < 4; ++k) x4[k] = x + nblock*k;
        for (int ibl = 0; ibl < nblock; ++ibl) {
            auto ysas = (uint32_t *)y[ibl].sas;
            for (int k = 0; k < 4; ++k) {
                y[ibl].d[k] = x4[k][ibl].d;
                auto xsas = x4[k][ibl].qs + QK_K/4;
                for (int ib = 0; ib < QK_K/32; ++ib) {
                    for (int i = 0; i < 8; ++i) {
                        y[ibl].qs[32*ib+8*k+i] = x4[k][ibl].qs[8*ib+i];
                    }
                    std::memcpy(&aux32, xsas + 4*ib, 4);
                    uint8_t scale = aux32 >> 28;
                    uint8_t s1 = (scrambled_sign((aux32 >>  0) & 127) << 1) | ((scale >> 0) & 1);
                    uint8_t s2 = (scrambled_sign((aux32 >>  7) & 127) << 1) | ((scale >> 1) & 1);
                    uint8_t s3 = (scrambled_sign((aux32 >> 14) & 127) << 1) | ((scale >> 2) & 1);
                    uint8_t s4 = (scrambled_sign((aux32 >> 21) & 127) << 1) | ((scale >> 3) & 1);
                    aux32 = uint32_t(s1) | (uint32_t(s2) << 8) | (uint32_t(s3) << 16) | (uint32_t(s4) << 24);
                    ysas[4*ib+k] = aux32;
                }
            }
        }
        x += 4*nblock;
        y += nblock;
    }
}
void dequantize_row_iq3_xxs_r4(const block_iq3_xxs_r4 * x, float * y, int64_t k) {
    auto n_per_row = k/4;
    float * y4[4] = {y, y + n_per_row, y + 2*n_per_row, y + 3*n_per_row};
    int nblock = n_per_row/QK_K;
    uint32_t s32;
    const uint8_t * s8 = (const uint8_t *)&s32;
    for (int ibl = 0; ibl < nblock; ++ibl) {
        const uint32_t * sas = (const uint32_t *)x[ibl].sas;
        for (int k = 0; k < 4; ++k) {
            const float d = 0.25f*GGML_FP16_TO_FP32(x[ibl].d[k]);
            for (int ib = 0; ib < QK_K/32; ++ib) {
                uint32_t aux32 = sas[4*ib+k];
                s32 = aux32 & 0x01010101;
                uint8_t scale = s8[0] | (s8[1] << 1) | (s8[2] << 2) | (s8[3] << 3);
                float dl = d*(2*scale+1);
                aux32 &= 0xfefefefe;
                aux32 ^= (aux32 >> 1);
                for (int i = 0; i < 8; ++i) {
                    auto val = (const int8_t *)(iq3xxs_grid + x[ibl].qs[32*ib+8*k+i]);
                    for (int j = 0; j < 4; ++j) y4[k][QK_K*ibl+32*ib+4*i+j] = dl * val[j] * (aux32 & (1 << j) ? -1 : 1);
                    aux32 >>= 4;
                }
            }
        }
    }
}
static void repack_iq3_s(int nrows, int n_per_row, const block_iq3_s * x, block_iq3_s_r4 * y, [[maybe_unused]] bool online) {
    GGML_ASSERT(nrows%4 == 0);
    GGML_ASSERT(n_per_row%QK_K == 0);
    int nblock = n_per_row/QK_K;
    const block_iq3_s * x4[4];
    for (int row = 0; row < nrows; row += 4) {
        for (int k = 0; k < 4; ++k) x4[k] = x + nblock*k;
        for (int ibl = 0; ibl < nblock; ++ibl) {
            std::memset(y[ibl].scales, 0, QK_K/16);
            std::memset(y[ibl].signs,  0, QK_K/2);
            std::memset(y[ibl].qh,     0, QK_K/8);
            for (int k = 0; k < 4; ++k) {
                y[ibl].d[k] = x4[k][ibl].d;
                for (int ib = 0; ib < QK_K/64; ++ib) {
                    int j = 8*ib + k;
                    y[ibl].scales[(j+0)%16] |= ((x4[k][ibl].scales[ib] & 0xf) << 4*((j+0)/16));
                    y[ibl].scales[(j+4)%16] |= ((x4[k][ibl].scales[ib] >>  4) << 4*((j+4)/16));
                }
                for (int ib = 0; ib < QK_K/32; ++ib) {
                    y[ibl].qh[4*ib+k] = x4[k][ibl].qh[ib]; // leave ot like this?
                    for (int i = 0; i < 4; ++i) {
                        y[ibl].qs[32*ib+k+8*i+0] = x4[k][ibl].qs[8*ib+i+0];
                        y[ibl].qs[32*ib+k+8*i+4] = x4[k][ibl].qs[8*ib+i+4];
                    }
                    for (int i = 0; i < 4; ++i) {
                        y[ibl].signs[16*ib+4*k+i] = (((x4[k][ibl].signs[4*ib+0] >> i) & 1) << 0) | (((x4[k][ibl].signs[4*ib+0] >> (4+i)) & 1) << 1) |
                                                    (((x4[k][ibl].signs[4*ib+1] >> i) & 1) << 2) | (((x4[k][ibl].signs[4*ib+1] >> (4+i)) & 1) << 3) |
                                                    (((x4[k][ibl].signs[4*ib+2] >> i) & 1) << 4) | (((x4[k][ibl].signs[4*ib+2] >> (4+i)) & 1) << 5) |
                                                    (((x4[k][ibl].signs[4*ib+3] >> i) & 1) << 6) | (((x4[k][ibl].signs[4*ib+3] >> (4+i)) & 1) << 7);
                    }
                }
            }
        }
        x += 4*nblock;
        y += nblock;
    }
}
void dequantize_row_iq3_s_r4(const block_iq3_s_r4 * x, float * y, int64_t k) {
    auto n_per_row = k/4;
    float * y4[4] = {y, y + n_per_row, y + 2*n_per_row, y + 3*n_per_row};
    int nblock = n_per_row/QK_K;
    for (int ibl = 0; ibl < nblock; ++ibl) {
        for (int k = 0; k < 4; ++k) {
            const float d = GGML_FP16_TO_FP32(x[ibl].d[k]);
            for (int ib = 0; ib < QK_K/32; ++ib) {
                int l = 4*ib + k;
                float dl = d * (1 + 2*((x[ibl].scales[l%16] >> 4*(l/16)) & 0xf));
                for (int i = 0; i < 4; ++i) {
                    auto grid1 = (const uint8_t *)(iq3s_grid + x[ibl].qs[32*ib+k+8*i+0] + ((x[ibl].qh[4*ib+k] << (8-i)) & 0x100));
                    auto grid2 = (const uint8_t *)(iq3s_grid + x[ibl].qs[32*ib+k+8*i+4] + ((x[ibl].qh[4*ib+k] << (4-i)) & 0x100));
                    for (int j = 0; j < 4; ++j) {
                        y4[k][QK_K*ibl+32*ib+4*i+ 0+j] = dl * grid1[j] * (x[ibl].signs[16*ib+4*k+j] & (1 << (i+0)) ? -1 : 1);
                        y4[k][QK_K*ibl+32*ib+4*i+16+j] = dl * grid2[j] * (x[ibl].signs[16*ib+4*k+j] & (1 << (i+4)) ? -1 : 1);
                    }
                }
            }
        }
    }
}

// Explicit AVX-VNNI experiment. The parent must gate CPUID before selecting variants 1/2.
static inline __m256i ggml_mm256_dpbusd_epi32(__m256i a,__m256i u,__m256i s){return _mm256_dpbusd_avx_epi32(a,u,s);}
static inline __m128i ggml_mm_dpbusd_epi32(__m128i a,__m128i u,__m128i s){return _mm_dpbusd_avx_epi32(a,u,s);}
static inline __m256i ggml_mm256_dpwssd_epi32(__m256i a,__m256i x,__m256i y){return _mm256_dpwssd_avx_epi32(a,x,y);}

namespace old {
template <int nrc_y>
static void mul_mat_iq2_xxs_r4_q8_k(int n, const void * vx, size_t bx, const DataInfo& info, int nrc_x) {
    GGML_ASSERT(nrc_x%4 == 0);
    Q8<nrc_y, block_q8_K> q8(info);
    int nbl = n / QK_K;
    auto smask = _mm256_set1_epi64x(0x8040201008040201);
    auto sign_shuffle = _mm256_set_epi64x(0x0303030303030303, 0x0202020202020202, 0x0101010101010101, 0x0000000000000000);
    auto m4 = _mm256_set1_epi8(4);
    auto m1 = _mm256_set1_epi16(1);
    __m256  acc[nrc_y] = {};
    __m256i isum[nrc_y] = {};
    __m256i qx[4];
    for (int ix = 0; ix < nrc_x; ix += 4) {
        auto iq2 = (const block_iq2_xxs_r4 *)((const char *)vx + (ix+0)*bx);
        for (int ibl = 0; ibl < nbl; ++ibl) { // Block of 256
            auto dl = _mm_cvtph_ps(_mm_loadl_epi64((const __m128i *)iq2[ibl].d));
            auto d4 = _mm256_set_m128(dl, dl);
            auto qs = iq2[ibl].qs;
            for (int ib = 0; ib < QK_K/32; ++ib) {
                qx[0] = _mm256_set_epi64x(iq2xxs_grid[qs[ 3]], iq2xxs_grid[qs[ 2]], iq2xxs_grid[qs[ 1]], iq2xxs_grid[qs[ 0]]);
                qx[1] = _mm256_set_epi64x(iq2xxs_grid[qs[ 7]], iq2xxs_grid[qs[ 6]], iq2xxs_grid[qs[ 5]], iq2xxs_grid[qs[ 4]]);
                qx[2] = _mm256_set_epi64x(iq2xxs_grid[qs[11]], iq2xxs_grid[qs[10]], iq2xxs_grid[qs[ 9]], iq2xxs_grid[qs[ 8]]);
                qx[3] = _mm256_set_epi64x(iq2xxs_grid[qs[15]], iq2xxs_grid[qs[14]], iq2xxs_grid[qs[13]], iq2xxs_grid[qs[12]]);
                qs += 16;
                auto sas = _mm_loadu_si128((const __m128i *)iq2[ibl].sas + ib);
                auto scales = _mm_and_si128(sas, _mm_set1_epi8(1));
                scales = _mm_maddubs_epi16(scales, _mm_set1_epi32(0x10080402));
                scales = _mm_add_epi32(_mm_madd_epi16(_mm_set1_epi16(1), scales), _mm_set1_epi32(1));
                auto scales32 = MM256_SET1_M128I(scales);
                auto signs128 = _mm_and_si128(sas, _mm_set1_epi8(-2)); // 0xfe = -2 as signed. Needed to shutup compiler warning.
                signs128 = _mm_xor_si128(signs128, _mm_srli_epi16(signs128, 1));
                auto signs = MM256_SET1_M128I(signs128);
                auto shuffle = sign_shuffle;
                auto s1 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s2 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s3 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s4 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                for (int iy = 0; iy < nrc_y; ++iy) {
                    auto y = _mm256_loadu_si256((const __m256i *)q8.y[iy][ibl].qs + ib);
                    auto sumi1 = _mm256_madd_epi16(m1, _mm256_maddubs_epi16(qx[0], _mm256_sign_epi8(y, s1)));
                    auto sumi2 = _mm256_madd_epi16(m1, _mm256_maddubs_epi16(qx[1], _mm256_sign_epi8(y, s2)));
                    auto sumi3 = _mm256_madd_epi16(m1, _mm256_maddubs_epi16(qx[2], _mm256_sign_epi8(y, s3)));
                    auto sumi4 = _mm256_madd_epi16(m1, _mm256_maddubs_epi16(qx[3], _mm256_sign_epi8(y, s4)));
                    auto s12 = _mm256_add_epi32(_mm256_unpacklo_epi32(sumi1, sumi2), _mm256_unpackhi_epi32(sumi1, sumi2)); // 0,1, 0,1, 0,1, 0,1
                    auto s34 = _mm256_add_epi32(_mm256_unpacklo_epi32(sumi3, sumi4), _mm256_unpackhi_epi32(sumi3, sumi4)); // 2,3, 2,3, 2,3, 2,3
                    auto sumi = _mm256_add_epi32(_mm256_unpacklo_epi64(s12, s34), _mm256_unpackhi_epi64(s12, s34)); // 0,1,2,3, 0,1,2,3
                    isum[iy] = _mm256_add_epi32(isum[iy], _mm256_mullo_epi32(scales32, sumi));
                }
            }
            for (int iy = 0; iy < nrc_y; ++iy) {
                acc[iy] = _mm256_fmadd_ps(_mm256_mul_ps(d4, _mm256_set1_ps(q8.scale(iy, ibl))), _mm256_cvtepi32_ps(isum[iy]), acc[iy]);
                isum[iy] = _mm256_setzero_si256();
            }
        }
        for (int iy = 0; iy < nrc_y; ++iy) {
            auto sum = _mm_add_ps(_mm256_castps256_ps128(acc[iy]), _mm256_extractf128_ps(acc[iy], 1));
            info.store(ix, iy, _mm_mul_ps(_mm_set1_ps(0.125f), sum));
            acc[iy] = _mm256_setzero_ps();
        }
    }
}
template <int nrc_y>
static void mul_mat_iq2_xs_r4_q8_k(int n, const void * vx, size_t bx, const DataInfo& info, int nrc_x) {
    GGML_ASSERT(nrc_x%4 == 0);
    Q8<nrc_y, block_q8_K> q8(info);
    int nbl = n / QK_K;
    auto smask = _mm256_set1_epi64x(0x8040201008040201);
    auto sign_shuffle = _mm256_set_epi64x(0x0303030303030303, 0x0202020202020202, 0x0101010101010101, 0x0000000000000000);
    auto m4 = _mm256_set1_epi8(4);
    __m256  acc[nrc_y] = {};
    __m256i shuffles[4] = {
        MM256_SET_M128I(_mm_set1_epi16(0x0302), _mm_set1_epi16(0x0100)),
        MM256_SET_M128I(_mm_set1_epi16(0x0706), _mm_set1_epi16(0x0504)),
        MM256_SET_M128I(_mm_set1_epi16(0x0b0a), _mm_set1_epi16(0x0908)),
        MM256_SET_M128I(_mm_set1_epi16(0x0f0e), _mm_set1_epi16(0x0d0c)),
    };
    __m256i isum[nrc_y == 1 ? 4 : nrc_y] = {};
    auto s_shuffle = _mm_set_epi64x(0x0f0d0b0907050301, 0x0e0c0a0806040200);
    __m256i qx[4];
    union { __m256i vec; uint16_t val[16]; } helper;
    for (int ix = 0; ix < nrc_x; ix += 4) {
        auto iq2 = (const block_iq2_xs_r4 *)((const char *)vx + (ix+0)*bx);
        for (int ibl = 0; ibl < nbl; ++ibl) { // Block of 256
            auto dl = _mm_cvtph_ps(_mm_loadl_epi64((const __m128i *)iq2[ibl].d));
            auto d4 = _mm256_set_m128(dl, dl);
            auto s32 = (const uint32_t *)iq2[ibl].scales;
            for (int ib = 0; ib < QK_K/32; ++ib) {
                auto val = _mm256_loadu_si256((const __m256i *)iq2[ibl].qs + ib);
                helper.vec = _mm256_and_si256(val, _mm256_set1_epi16(511));
                qx[0] = _mm256_set_epi64x(iq2xs_grid[helper.val[ 3]], iq2xs_grid[helper.val[ 2]], iq2xs_grid[helper.val[ 1]], iq2xs_grid[helper.val[ 0]]);
                qx[1] = _mm256_set_epi64x(iq2xs_grid[helper.val[ 7]], iq2xs_grid[helper.val[ 6]], iq2xs_grid[helper.val[ 5]], iq2xs_grid[helper.val[ 4]]);
                qx[2] = _mm256_set_epi64x(iq2xs_grid[helper.val[11]], iq2xs_grid[helper.val[10]], iq2xs_grid[helper.val[ 9]], iq2xs_grid[helper.val[ 8]]);
                qx[3] = _mm256_set_epi64x(iq2xs_grid[helper.val[15]], iq2xs_grid[helper.val[14]], iq2xs_grid[helper.val[13]], iq2xs_grid[helper.val[12]]);
                auto signs16 = _mm256_srli_epi16(val, 9);
                signs16 = _mm256_xor_si256(signs16, _mm256_slli_epi16(signs16, 1));
                auto signs128 = _mm_or_si128(_mm256_castsi256_si128(signs16), _mm_slli_epi16(_mm256_extracti128_si256(signs16, 1), 8));
                signs128 = _mm_shuffle_epi8(signs128, s_shuffle);
                auto scales = _mm_set1_epi32(s32[ib]);
                scales = _mm_and_si128(_mm_unpacklo_epi8(scales, _mm_srli_epi16(scales, 4)), _mm_set1_epi8(0xf));
                scales = _mm_or_si128(_mm_slli_epi16(scales, 1), _mm_set1_epi8(1));
                auto scales16 = _mm256_cvtepi8_epi16(scales);  // 0...7, 0...7
                auto signs = MM256_SET1_M128I(signs128);
                auto shuffle = sign_shuffle;
                auto s1 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s2 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s3 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s4 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                __m256i scs[4] = {
                    _mm256_shuffle_epi8(scales16, shuffles[0]), _mm256_shuffle_epi8(scales16, shuffles[1]),
                    _mm256_shuffle_epi8(scales16, shuffles[2]), _mm256_shuffle_epi8(scales16, shuffles[3]),
                };
                for (int iy = 0; iy < nrc_y; ++iy) {
                    auto y = _mm256_loadu_si256((const __m256i *)q8.y[iy][ibl].qs + ib);
                    if constexpr (nrc_y == 1) {
                        isum[0] = _mm256_add_epi32(isum[0], _mm256_madd_epi16(scs[0], _mm256_maddubs_epi16(qx[0], _mm256_sign_epi8(y, s1))));
                        isum[1] = _mm256_add_epi32(isum[1], _mm256_madd_epi16(scs[1], _mm256_maddubs_epi16(qx[1], _mm256_sign_epi8(y, s2))));
                        isum[2] = _mm256_add_epi32(isum[2], _mm256_madd_epi16(scs[2], _mm256_maddubs_epi16(qx[2], _mm256_sign_epi8(y, s3))));
                        isum[3] = _mm256_add_epi32(isum[3], _mm256_madd_epi16(scs[3], _mm256_maddubs_epi16(qx[3], _mm256_sign_epi8(y, s4))));
                    } else {
                        auto sumi1 = _mm256_madd_epi16(scs[0], _mm256_maddubs_epi16(qx[0], _mm256_sign_epi8(y, s1))); // blocks 4x0, 4x1, row 0
                        auto sumi2 = _mm256_madd_epi16(scs[1], _mm256_maddubs_epi16(qx[1], _mm256_sign_epi8(y, s2))); // blocks 4x2, 4x3, row 1
                        auto sumi3 = _mm256_madd_epi16(scs[2], _mm256_maddubs_epi16(qx[2], _mm256_sign_epi8(y, s3))); // blocks 4x4, 4x5, row 2
                        auto sumi4 = _mm256_madd_epi16(scs[3], _mm256_maddubs_epi16(qx[3], _mm256_sign_epi8(y, s4))); // blocks 4x6, 4x7, row 3
                        auto s12 = _mm256_add_epi32(_mm256_unpacklo_epi32(sumi1, sumi2), _mm256_unpackhi_epi32(sumi1, sumi2)); // 0,1, 0,1, 0,1, 0,1
                        auto s34 = _mm256_add_epi32(_mm256_unpacklo_epi32(sumi3, sumi4), _mm256_unpackhi_epi32(sumi3, sumi4)); // 2,3, 2,3, 2,3, 2,3
                        auto sumi = _mm256_add_epi32(_mm256_unpacklo_epi64(s12, s34), _mm256_unpackhi_epi64(s12, s34)); // 0,1,2,3, 0,1,2,3
                        isum[iy] = _mm256_add_epi32(isum[iy], sumi);
                    }
                }
            }
            for (int iy = 0; iy < nrc_y; ++iy) {
                if constexpr (nrc_y == 1) {
                    auto s12 = _mm256_add_epi32(_mm256_unpacklo_epi32(isum[0], isum[1]), _mm256_unpackhi_epi32(isum[0], isum[1]));
                    auto s34 = _mm256_add_epi32(_mm256_unpacklo_epi32(isum[2], isum[3]), _mm256_unpackhi_epi32(isum[2], isum[3]));
                    auto sumi = _mm256_add_epi32(_mm256_unpacklo_epi64(s12, s34), _mm256_unpackhi_epi64(s12, s34));
                    acc[iy] = _mm256_fmadd_ps(_mm256_mul_ps(d4, _mm256_set1_ps(q8.scale(iy, ibl))), _mm256_cvtepi32_ps(sumi), acc[iy]);
                    isum[0] = isum[1] = isum[2] = isum[3] = _mm256_setzero_si256();
                } else {
                    acc[iy] = _mm256_fmadd_ps(_mm256_mul_ps(d4, _mm256_set1_ps(q8.scale(iy, ibl))), _mm256_cvtepi32_ps(isum[iy]), acc[iy]);
                    isum[iy] = _mm256_setzero_si256();
                }
            }
        }
        for (int iy = 0; iy < nrc_y; ++iy) {
            auto sum = _mm_add_ps(_mm256_castps256_ps128(acc[iy]), _mm256_extractf128_ps(acc[iy], 1));
            info.store(ix, iy, _mm_mul_ps(_mm_set1_ps(0.125f), sum));
            acc[iy] = _mm256_setzero_ps();
        }
    }
}
template <int nrc_y>
static void mul_mat_iq2_s_r4_q8_k(int n, const void * vx, size_t bx, const DataInfo& info, int nrc_x) {
    GGML_ASSERT(nrc_x%4 == 0);
    Q8<nrc_y, block_q8_K> q8(info);
    int nbl = n / QK_K;
    auto smask = _mm256_set1_epi64x(0x8040201008040201);
    auto sign_shuffle = _mm256_set_epi64x(0x0303030303030303, 0x0202020202020202, 0x0101010101010101, 0x0000000000000000);
    auto m4 = _mm256_set1_epi8(4);
    __m256  acc[nrc_y] = {};
    __m256i shuffles[4] = {
        MM256_SET_M128I(_mm_set1_epi16(0x0302), _mm_set1_epi16(0x0100)),
        MM256_SET_M128I(_mm_set1_epi16(0x0706), _mm_set1_epi16(0x0504)),
        MM256_SET_M128I(_mm_set1_epi16(0x0b0a), _mm_set1_epi16(0x0908)),
        MM256_SET_M128I(_mm_set1_epi16(0x0f0e), _mm_set1_epi16(0x0d0c)),
    };
    __m256i isum[nrc_y == 1 ? 4 : nrc_y] = {};
    __m256i qx[4];
    auto grid = iq2s_grid;
    for (int ix = 0; ix < nrc_x; ix += 4) {
        auto iq2 = (const block_iq2_s_r4 *)((const char *)vx + (ix+0)*bx);
        for (int ibl = 0; ibl < nbl; ++ibl) { // Block of 256
            auto dl = _mm_cvtph_ps(_mm_loadl_epi64((const __m128i *)iq2[ibl].d));
            auto d4 = _mm256_set_m128(dl, dl);
            auto s32 = (const uint32_t *)iq2[ibl].scales;
            auto ql = iq2[ibl].qs;
            auto qh = iq2[ibl].qh;
            for (int ib = 0; ib < QK_K/32; ++ib) {
                qx[0] = _mm256_set_epi64x(grid[ql[ 3] | ((qh[0] << 2) & 0x300)], grid[ql[ 2] | ((qh[0] << 4) & 0x300)], grid[ql[ 1] | ((qh[0] << 6) & 0x300)], grid[ql[ 0] | ((qh[0] << 8) & 0x300)]);
                qx[1] = _mm256_set_epi64x(grid[ql[ 7] | ((qh[1] << 2) & 0x300)], grid[ql[ 6] | ((qh[1] << 4) & 0x300)], grid[ql[ 5] | ((qh[1] << 6) & 0x300)], grid[ql[ 4] | ((qh[1] << 8) & 0x300)]);
                qx[2] = _mm256_set_epi64x(grid[ql[11] | ((qh[2] << 2) & 0x300)], grid[ql[10] | ((qh[2] << 4) & 0x300)], grid[ql[ 9] | ((qh[2] << 6) & 0x300)], grid[ql[ 8] | ((qh[2] << 8) & 0x300)]);
                qx[3] = _mm256_set_epi64x(grid[ql[15] | ((qh[3] << 2) & 0x300)], grid[ql[14] | ((qh[3] << 4) & 0x300)], grid[ql[13] | ((qh[3] << 6) & 0x300)], grid[ql[12] | ((qh[3] << 8) & 0x300)]);
                ql += 16; qh += 4;
                auto signs128 = _mm_loadu_si128((const __m128i*)iq2[ibl].signs + ib);
                auto scales = _mm_set1_epi32(s32[ib]);
                scales = _mm_and_si128(_mm_unpacklo_epi8(scales, _mm_srli_epi16(scales, 4)), _mm_set1_epi8(0xf));
                scales = _mm_or_si128(_mm_slli_epi16(scales, 1), _mm_set1_epi8(1));
                auto scales16 = _mm256_cvtepi8_epi16(scales);  // 0...7, 0...7
                auto signs = MM256_SET1_M128I(signs128);
                auto shuffle = sign_shuffle;
                auto s1 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s2 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s3 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s4 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                __m256i scs[4] = {
                    _mm256_shuffle_epi8(scales16, shuffles[0]), _mm256_shuffle_epi8(scales16, shuffles[1]),
                    _mm256_shuffle_epi8(scales16, shuffles[2]), _mm256_shuffle_epi8(scales16, shuffles[3]),
                };
                for (int iy = 0; iy < nrc_y; ++iy) {
                    auto y = _mm256_loadu_si256((const __m256i *)q8.y[iy][ibl].qs + ib);
                    if constexpr (nrc_y == 1) {
                        isum[0] = _mm256_add_epi32(isum[0], _mm256_madd_epi16(scs[0], _mm256_maddubs_epi16(qx[0], _mm256_sign_epi8(y, s1))));
                        isum[1] = _mm256_add_epi32(isum[1], _mm256_madd_epi16(scs[1], _mm256_maddubs_epi16(qx[1], _mm256_sign_epi8(y, s2))));
                        isum[2] = _mm256_add_epi32(isum[2], _mm256_madd_epi16(scs[2], _mm256_maddubs_epi16(qx[2], _mm256_sign_epi8(y, s3))));
                        isum[3] = _mm256_add_epi32(isum[3], _mm256_madd_epi16(scs[3], _mm256_maddubs_epi16(qx[3], _mm256_sign_epi8(y, s4))));
                    } else {
                        auto sumi1 = _mm256_madd_epi16(scs[0], _mm256_maddubs_epi16(qx[0], _mm256_sign_epi8(y, s1))); // blocks 4x0, 4x1, row 0
                        auto sumi2 = _mm256_madd_epi16(scs[1], _mm256_maddubs_epi16(qx[1], _mm256_sign_epi8(y, s2))); // blocks 4x2, 4x3, row 1
                        auto sumi3 = _mm256_madd_epi16(scs[2], _mm256_maddubs_epi16(qx[2], _mm256_sign_epi8(y, s3))); // blocks 4x4, 4x5, row 2
                        auto sumi4 = _mm256_madd_epi16(scs[3], _mm256_maddubs_epi16(qx[3], _mm256_sign_epi8(y, s4))); // blocks 4x6, 4x7, row 3
                        auto s12 = _mm256_add_epi32(_mm256_unpacklo_epi32(sumi1, sumi2), _mm256_unpackhi_epi32(sumi1, sumi2)); // 0,1, 0,1, 0,1, 0,1
                        auto s34 = _mm256_add_epi32(_mm256_unpacklo_epi32(sumi3, sumi4), _mm256_unpackhi_epi32(sumi3, sumi4)); // 2,3, 2,3, 2,3, 2,3
                        auto sumi = _mm256_add_epi32(_mm256_unpacklo_epi64(s12, s34), _mm256_unpackhi_epi64(s12, s34)); // 0,1,2,3, 0,1,2,3
                        isum[iy] = _mm256_add_epi32(isum[iy], sumi);
                    }
                }
            }
            for (int iy = 0; iy < nrc_y; ++iy) {
                if constexpr (nrc_y == 1) {
                    auto s12 = _mm256_add_epi32(_mm256_unpacklo_epi32(isum[0], isum[1]), _mm256_unpackhi_epi32(isum[0], isum[1]));
                    auto s34 = _mm256_add_epi32(_mm256_unpacklo_epi32(isum[2], isum[3]), _mm256_unpackhi_epi32(isum[2], isum[3]));
                    auto sumi = _mm256_add_epi32(_mm256_unpacklo_epi64(s12, s34), _mm256_unpackhi_epi64(s12, s34));
                    acc[iy] = _mm256_fmadd_ps(_mm256_mul_ps(d4, _mm256_set1_ps(q8.scale(iy, ibl))), _mm256_cvtepi32_ps(sumi), acc[iy]);
                    isum[0] = isum[1] = isum[2] = isum[3] = _mm256_setzero_si256();
                } else {
                    acc[iy] = _mm256_fmadd_ps(_mm256_mul_ps(d4, _mm256_set1_ps(q8.scale(iy, ibl))), _mm256_cvtepi32_ps(isum[iy]), acc[iy]);
                    isum[iy] = _mm256_setzero_si256();
                }
            }
        }
        for (int iy = 0; iy < nrc_y; ++iy) {
            auto sum = _mm_add_ps(_mm256_castps256_ps128(acc[iy]), _mm256_extractf128_ps(acc[iy], 1));
            info.store(ix, iy, _mm_mul_ps(_mm_set1_ps(0.125f), sum));
            acc[iy] = _mm256_setzero_ps();
        }
    }
}
template <int nrc_y>
static void mul_mat_iq3_xxs_r4_q8_k(int n, const void * vx, size_t bx, const DataInfo& info, int nrc_x) {
    GGML_ASSERT(nrc_x%4 == 0);
    Q8<nrc_y, block_q8_K> q8(info);
    int nbl = n / QK_K;
    auto smask = _mm256_set1_epi64x(0x8040201008040201);
    auto sign_shuffle = _mm256_set_epi64x(0x0303030303030303, 0x0202020202020202, 0x0101010101010101, 0x0000000000000000);
    auto m4 = _mm256_set1_epi8(4);
    auto m1 = _mm256_set1_epi16(1);
    __m256  acc[nrc_y] = {};
    __m256i isum[nrc_y] = {};
    __m256i qx[4];
    for (int ix = 0; ix < nrc_x; ix += 4) {
        auto iq3 = (const block_iq3_xxs_r4 *)((const char *)vx + (ix+0)*bx);
        for (int ibl = 0; ibl < nbl; ++ibl) { // Block of 256
            auto dl = _mm_mul_ps(_mm_set1_ps(0.25f), _mm_cvtph_ps(_mm_loadl_epi64((const __m128i *)iq3[ibl].d))); // TODO: absorb the 0.25 factor into d when quantizing/repacking
            auto d4 = _mm256_set_m128(dl, dl);
            for (int ib = 0; ib < QK_K/32; ++ib) {
                qx[0] = _mm256_set_epi32(iq3xxs_grid[iq3[ibl].qs[32*ib+ 7]], iq3xxs_grid[iq3[ibl].qs[32*ib+ 6]], iq3xxs_grid[iq3[ibl].qs[32*ib+ 5]], iq3xxs_grid[iq3[ibl].qs[32*ib+ 4]],
                                         iq3xxs_grid[iq3[ibl].qs[32*ib+ 3]], iq3xxs_grid[iq3[ibl].qs[32*ib+ 2]], iq3xxs_grid[iq3[ibl].qs[32*ib+ 1]], iq3xxs_grid[iq3[ibl].qs[32*ib+ 0]]);
                qx[1] = _mm256_set_epi32(iq3xxs_grid[iq3[ibl].qs[32*ib+15]], iq3xxs_grid[iq3[ibl].qs[32*ib+14]], iq3xxs_grid[iq3[ibl].qs[32*ib+13]], iq3xxs_grid[iq3[ibl].qs[32*ib+12]],
                                         iq3xxs_grid[iq3[ibl].qs[32*ib+11]], iq3xxs_grid[iq3[ibl].qs[32*ib+10]], iq3xxs_grid[iq3[ibl].qs[32*ib+ 9]], iq3xxs_grid[iq3[ibl].qs[32*ib+ 8]]);
                qx[2] = _mm256_set_epi32(iq3xxs_grid[iq3[ibl].qs[32*ib+23]], iq3xxs_grid[iq3[ibl].qs[32*ib+22]], iq3xxs_grid[iq3[ibl].qs[32*ib+21]], iq3xxs_grid[iq3[ibl].qs[32*ib+20]],
                                         iq3xxs_grid[iq3[ibl].qs[32*ib+19]], iq3xxs_grid[iq3[ibl].qs[32*ib+18]], iq3xxs_grid[iq3[ibl].qs[32*ib+17]], iq3xxs_grid[iq3[ibl].qs[32*ib+16]]);
                qx[3] = _mm256_set_epi32(iq3xxs_grid[iq3[ibl].qs[32*ib+31]], iq3xxs_grid[iq3[ibl].qs[32*ib+30]], iq3xxs_grid[iq3[ibl].qs[32*ib+29]], iq3xxs_grid[iq3[ibl].qs[32*ib+28]],
                                         iq3xxs_grid[iq3[ibl].qs[32*ib+27]], iq3xxs_grid[iq3[ibl].qs[32*ib+26]], iq3xxs_grid[iq3[ibl].qs[32*ib+25]], iq3xxs_grid[iq3[ibl].qs[32*ib+24]]);
                auto sas = _mm_loadu_si128((const __m128i *)iq3[ibl].sas + ib);
                auto scales = _mm_and_si128(sas, _mm_set1_epi8(1));
                scales = _mm_maddubs_epi16(scales, _mm_set1_epi32(0x10080402));
                scales = _mm_add_epi32(_mm_madd_epi16(_mm_set1_epi16(1), scales), _mm_set1_epi32(1));
                //auto t1 = _mm_or_si128(_mm_and_si128(scales, _mm_set1_epi32(0x00000001)), _mm_srli_epi32(_mm_and_si128(scales, _mm_set1_epi32(0x00000100)), 7));
                //auto t2 = _mm_or_si128(_mm_srli_epi32(_mm_and_si128(scales, _mm_set1_epi32(0x00010000)), 14), _mm_srli_epi32(_mm_and_si128(scales, _mm_set1_epi32(0x01000000)), 21));
                //scales = _mm_or_si128(_mm_slli_epi32(_mm_or_si128(t1, t2), 1), _mm_set1_epi32(1));
                auto scales32 = MM256_SET1_M128I(scales);
                auto signs128 = _mm_and_si128(sas, _mm_set1_epi8(-2)); // 0xfe = -2 as signed. Needed to shutup compiler warning.
                signs128 = _mm_xor_si128(signs128, _mm_srli_epi16(signs128, 1));
                auto signs = MM256_SET1_M128I(signs128);
                auto shuffle = sign_shuffle;
                auto s1 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s2 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s3 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s4 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                for (int iy = 0; iy < nrc_y; ++iy) {
                    auto y = _mm256_loadu_si256((const __m256i *)q8.y[iy][ibl].qs + ib);
                    auto sumi1 = _mm256_madd_epi16(m1, _mm256_maddubs_epi16(qx[0], _mm256_sign_epi8(y, s1)));
                    auto sumi2 = _mm256_madd_epi16(m1, _mm256_maddubs_epi16(qx[1], _mm256_sign_epi8(y, s2)));
                    auto sumi3 = _mm256_madd_epi16(m1, _mm256_maddubs_epi16(qx[2], _mm256_sign_epi8(y, s3)));
                    auto sumi4 = _mm256_madd_epi16(m1, _mm256_maddubs_epi16(qx[3], _mm256_sign_epi8(y, s4)));
                    auto s12 = _mm256_add_epi32(_mm256_unpacklo_epi32(sumi1, sumi2), _mm256_unpackhi_epi32(sumi1, sumi2)); // 0,1, 0,1, 0,1, 0,1
                    auto s34 = _mm256_add_epi32(_mm256_unpacklo_epi32(sumi3, sumi4), _mm256_unpackhi_epi32(sumi3, sumi4)); // 2,3, 2,3, 2,3, 2,3
                    auto sumi = _mm256_add_epi32(_mm256_unpacklo_epi64(s12, s34), _mm256_unpackhi_epi64(s12, s34)); // 0,1,2,3, 0,1,2,3
                    isum[iy] = _mm256_add_epi32(isum[iy], _mm256_mullo_epi32(scales32, sumi));
                }
            }
            for (int iy = 0; iy < nrc_y; ++iy) {
                acc[iy] = _mm256_fmadd_ps(_mm256_mul_ps(d4, _mm256_set1_ps(q8.scale(iy, ibl))), _mm256_cvtepi32_ps(isum[iy]), acc[iy]);
                isum[iy] = _mm256_setzero_si256();
            }
        }
        for (int iy = 0; iy < nrc_y; ++iy) {
            auto sum = _mm_add_ps(_mm256_castps256_ps128(acc[iy]), _mm256_extractf128_ps(acc[iy], 1));
            info.store(ix, iy, sum);
            acc[iy] = _mm256_setzero_ps();
        }
    }
}
template <int nrc_y>
static void mul_mat_iq3_s_r4_q8_k(int n, const void * vx, size_t bx, const DataInfo& info, int nrc_x) {
    GGML_ASSERT(nrc_x%4 == 0);
    Q8<nrc_y, block_q8_K> q8(info);
    int nbl = n / QK_K;
    auto smask = _mm256_set1_epi8(1);
    union { __m256i vec; uint32_t val[8]; } helper;
    union { __m128i vec; uint16_t val[8]; } hidx;
    __m256  acc[nrc_y] = {};
    __m256i isum[nrc_y] = {};
    __m256i qx[4];
    for (int ix = 0; ix < nrc_x; ix += 4) {
        auto iq3 = (const block_iq3_s_r4 *)((const char *)vx + (ix+0)*bx);
        for (int ibl = 0; ibl < nbl; ++ibl) { // Block of 256
            auto dl = _mm_cvtph_ps(_mm_loadl_epi64((const __m128i *)iq3[ibl].d));
            auto d4 = _mm256_set_m128(dl, dl);
            auto qs = iq3[ibl].qs;
            auto qh = iq3[ibl].qh;
            auto scale_bits = _mm_loadu_si128((const __m128i *)iq3[ibl].scales);
            auto scales8 = MM256_SET_M128I(_mm_srli_epi16(scale_bits, 4), scale_bits);
            helper.vec = _mm256_or_si256(_mm256_slli_epi16(_mm256_and_si256(scales8, _mm256_set1_epi8(0xf)), 1), _mm256_set1_epi8(1));
            for (int ib = 0; ib < QK_K/32; ++ib) {
                auto qh32 = (const uint32_t *)qh;
                auto idx_h = _mm_sllv_epi64(_mm_cvtepu8_epi16(_mm_set1_epi32(qh32[0])), _mm_set_epi64x(4, 8));
                for (int i = 0; i < 4; ++i) {
                    auto idx_l = _mm_cvtepu8_epi16(_mm_loadl_epi64((const __m128i *)(qs + 8*i)));
                    hidx.vec = _mm_or_si128(idx_l, _mm_and_si128(idx_h, _mm_set1_epi16(0x100))); idx_h = _mm_srli_epi16(idx_h, 1);
                    qx[i] = _mm256_set_epi32(iq3s_grid[hidx.val[7]], iq3s_grid[hidx.val[6]], iq3s_grid[hidx.val[5]], iq3s_grid[hidx.val[4]],
                                             iq3s_grid[hidx.val[3]], iq3s_grid[hidx.val[2]], iq3s_grid[hidx.val[1]], iq3s_grid[hidx.val[0]]);
                }
                qs += 32; qh += 4;
                auto signs128 = _mm_loadu_si128((const __m128i*)iq3[ibl].signs + ib);
                auto signs = MM256_SET_M128I(_mm_srli_epi16(signs128, 4), signs128);
                auto scales16 = _mm256_cvtepi8_epi16(_mm_set1_epi32(helper.val[ib]));
                auto scales = _mm256_unpacklo_epi16(scales16, scales16);
                auto s1 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(signs, smask), smask), smask); signs = _mm256_srli_epi16(signs, 1);
                auto s2 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(signs, smask), smask), smask); signs = _mm256_srli_epi16(signs, 1);
                auto s3 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(signs, smask), smask), smask); signs = _mm256_srli_epi16(signs, 1);
                auto s4 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(signs, smask), smask), smask);
                for (int iy = 0; iy < nrc_y; ++iy) {
                    auto y = _mm256_loadu_si256((const __m256i *)q8.y[iy][ibl].qs + ib);
                    auto sumi = _mm256_setzero_si256();
                    sumi = _mm256_add_epi16(sumi, _mm256_maddubs_epi16(qx[0], _mm256_sign_epi8(_mm256_shuffle_epi32(y, 0x00), s1)));
                    sumi = _mm256_add_epi16(sumi, _mm256_maddubs_epi16(qx[1], _mm256_sign_epi8(_mm256_shuffle_epi32(y, 0x55), s2)));
                    sumi = _mm256_add_epi16(sumi, _mm256_maddubs_epi16(qx[2], _mm256_sign_epi8(_mm256_shuffle_epi32(y, 0xaa), s3)));
                    sumi = _mm256_add_epi16(sumi, _mm256_maddubs_epi16(qx[3], _mm256_sign_epi8(_mm256_shuffle_epi32(y, 0xff), s4)));
                    isum[iy] = _mm256_add_epi32(isum[iy], _mm256_madd_epi16(scales, sumi));
                }
            }
            for (int iy = 0; iy < nrc_y; ++iy) {
                acc[iy] = _mm256_fmadd_ps(_mm256_mul_ps(d4, _mm256_set1_ps(q8.scale(iy, ibl))), _mm256_cvtepi32_ps(isum[iy]), acc[iy]);
                isum[iy] = _mm256_setzero_si256();
            }
        }
        for (int iy = 0; iy < nrc_y; ++iy) {
            auto sum = _mm_add_ps(_mm256_castps256_ps128(acc[iy]), _mm256_extractf128_ps(acc[iy], 1));
            info.store(ix, iy, sum);
            acc[iy] = _mm256_setzero_ps();
        }
    }
}
}
namespace vnni {
template <int nrc_y>
static void mul_mat_iq2_xxs_r4_q8_k(int n, const void * vx, size_t bx, const DataInfo& info, int nrc_x) {
    GGML_ASSERT(nrc_x%4 == 0);
    Q8<nrc_y, block_q8_K> q8(info);
    int nbl = n / QK_K;
    auto smask = _mm256_set1_epi64x(0x8040201008040201);
    auto sign_shuffle = _mm256_set_epi64x(0x0303030303030303, 0x0202020202020202, 0x0101010101010101, 0x0000000000000000);
    auto m4 = _mm256_set1_epi8(4);
    auto m1 = _mm256_set1_epi16(1);
    __m256  acc[nrc_y] = {};
    __m256i isum[nrc_y] = {};
    __m256i qx[4];
    for (int ix = 0; ix < nrc_x; ix += 4) {
        auto iq2 = (const block_iq2_xxs_r4 *)((const char *)vx + (ix+0)*bx);
        for (int ibl = 0; ibl < nbl; ++ibl) { // Block of 256
            auto dl = _mm_cvtph_ps(_mm_loadl_epi64((const __m128i *)iq2[ibl].d));
            auto d4 = _mm256_set_m128(dl, dl);
            auto qs = iq2[ibl].qs;
            for (int ib = 0; ib < QK_K/32; ++ib) {
                qx[0] = _mm256_set_epi64x(iq2xxs_grid[qs[ 3]], iq2xxs_grid[qs[ 2]], iq2xxs_grid[qs[ 1]], iq2xxs_grid[qs[ 0]]);
                qx[1] = _mm256_set_epi64x(iq2xxs_grid[qs[ 7]], iq2xxs_grid[qs[ 6]], iq2xxs_grid[qs[ 5]], iq2xxs_grid[qs[ 4]]);
                qx[2] = _mm256_set_epi64x(iq2xxs_grid[qs[11]], iq2xxs_grid[qs[10]], iq2xxs_grid[qs[ 9]], iq2xxs_grid[qs[ 8]]);
                qx[3] = _mm256_set_epi64x(iq2xxs_grid[qs[15]], iq2xxs_grid[qs[14]], iq2xxs_grid[qs[13]], iq2xxs_grid[qs[12]]);
                qs += 16;
                auto sas = _mm_loadu_si128((const __m128i *)iq2[ibl].sas + ib);
                auto scales = _mm_and_si128(sas, _mm_set1_epi8(1));
                scales = _mm_maddubs_epi16(scales, _mm_set1_epi32(0x10080402));
                scales = _mm_add_epi32(_mm_madd_epi16(_mm_set1_epi16(1), scales), _mm_set1_epi32(1));
                auto scales32 = MM256_SET1_M128I(scales);
                auto signs128 = _mm_and_si128(sas, _mm_set1_epi8(-2)); // 0xfe = -2 as signed. Needed to shutup compiler warning.
                signs128 = _mm_xor_si128(signs128, _mm_srli_epi16(signs128, 1));
                auto signs = MM256_SET1_M128I(signs128);
                auto shuffle = sign_shuffle;
                auto s1 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s2 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s3 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s4 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                for (int iy = 0; iy < nrc_y; ++iy) {
                    auto y = _mm256_loadu_si256((const __m256i *)q8.y[iy][ibl].qs + ib);
                    auto sumi1 = ggml_mm256_dpbusd_epi32(_mm256_setzero_si256(), qx[0], _mm256_sign_epi8(y, s1));
                    auto sumi2 = ggml_mm256_dpbusd_epi32(_mm256_setzero_si256(), qx[1], _mm256_sign_epi8(y, s2));
                    auto sumi3 = ggml_mm256_dpbusd_epi32(_mm256_setzero_si256(), qx[2], _mm256_sign_epi8(y, s3));
                    auto sumi4 = ggml_mm256_dpbusd_epi32(_mm256_setzero_si256(), qx[3], _mm256_sign_epi8(y, s4));
                    auto s12 = _mm256_add_epi32(_mm256_unpacklo_epi32(sumi1, sumi2), _mm256_unpackhi_epi32(sumi1, sumi2)); // 0,1, 0,1, 0,1, 0,1
                    auto s34 = _mm256_add_epi32(_mm256_unpacklo_epi32(sumi3, sumi4), _mm256_unpackhi_epi32(sumi3, sumi4)); // 2,3, 2,3, 2,3, 2,3
                    auto sumi = _mm256_add_epi32(_mm256_unpacklo_epi64(s12, s34), _mm256_unpackhi_epi64(s12, s34)); // 0,1,2,3, 0,1,2,3
                    isum[iy] = _mm256_add_epi32(isum[iy], _mm256_mullo_epi32(scales32, sumi));
                }
            }
            for (int iy = 0; iy < nrc_y; ++iy) {
                acc[iy] = _mm256_fmadd_ps(_mm256_mul_ps(d4, _mm256_set1_ps(q8.scale(iy, ibl))), _mm256_cvtepi32_ps(isum[iy]), acc[iy]);
                isum[iy] = _mm256_setzero_si256();
            }
        }
        for (int iy = 0; iy < nrc_y; ++iy) {
            auto sum = _mm_add_ps(_mm256_castps256_ps128(acc[iy]), _mm256_extractf128_ps(acc[iy], 1));
            info.store(ix, iy, _mm_mul_ps(_mm_set1_ps(0.125f), sum));
            acc[iy] = _mm256_setzero_ps();
        }
    }
}
template <int nrc_y>
static void mul_mat_iq2_xs_r4_q8_k(int n, const void * vx, size_t bx, const DataInfo& info, int nrc_x) {
    GGML_ASSERT(nrc_x%4 == 0);
    Q8<nrc_y, block_q8_K> q8(info);
    int nbl = n / QK_K;
    auto smask = _mm256_set1_epi64x(0x8040201008040201);
    auto sign_shuffle = _mm256_set_epi64x(0x0303030303030303, 0x0202020202020202, 0x0101010101010101, 0x0000000000000000);
    auto m4 = _mm256_set1_epi8(4);
    __m256  acc[nrc_y] = {};
    __m256i shuffles[4] = {
        MM256_SET_M128I(_mm_set1_epi16(0x0302), _mm_set1_epi16(0x0100)),
        MM256_SET_M128I(_mm_set1_epi16(0x0706), _mm_set1_epi16(0x0504)),
        MM256_SET_M128I(_mm_set1_epi16(0x0b0a), _mm_set1_epi16(0x0908)),
        MM256_SET_M128I(_mm_set1_epi16(0x0f0e), _mm_set1_epi16(0x0d0c)),
    };
    __m256i isum[nrc_y == 1 ? 4 : nrc_y] = {};
    auto s_shuffle = _mm_set_epi64x(0x0f0d0b0907050301, 0x0e0c0a0806040200);
    __m256i qx[4];
    union { __m256i vec; uint16_t val[16]; } helper;
    for (int ix = 0; ix < nrc_x; ix += 4) {
        auto iq2 = (const block_iq2_xs_r4 *)((const char *)vx + (ix+0)*bx);
        for (int ibl = 0; ibl < nbl; ++ibl) { // Block of 256
            auto dl = _mm_cvtph_ps(_mm_loadl_epi64((const __m128i *)iq2[ibl].d));
            auto d4 = _mm256_set_m128(dl, dl);
            auto s32 = (const uint32_t *)iq2[ibl].scales;
            for (int ib = 0; ib < QK_K/32; ++ib) {
                auto val = _mm256_loadu_si256((const __m256i *)iq2[ibl].qs + ib);
                helper.vec = _mm256_and_si256(val, _mm256_set1_epi16(511));
                qx[0] = _mm256_set_epi64x(iq2xs_grid[helper.val[ 3]], iq2xs_grid[helper.val[ 2]], iq2xs_grid[helper.val[ 1]], iq2xs_grid[helper.val[ 0]]);
                qx[1] = _mm256_set_epi64x(iq2xs_grid[helper.val[ 7]], iq2xs_grid[helper.val[ 6]], iq2xs_grid[helper.val[ 5]], iq2xs_grid[helper.val[ 4]]);
                qx[2] = _mm256_set_epi64x(iq2xs_grid[helper.val[11]], iq2xs_grid[helper.val[10]], iq2xs_grid[helper.val[ 9]], iq2xs_grid[helper.val[ 8]]);
                qx[3] = _mm256_set_epi64x(iq2xs_grid[helper.val[15]], iq2xs_grid[helper.val[14]], iq2xs_grid[helper.val[13]], iq2xs_grid[helper.val[12]]);
                auto signs16 = _mm256_srli_epi16(val, 9);
                signs16 = _mm256_xor_si256(signs16, _mm256_slli_epi16(signs16, 1));
                auto signs128 = _mm_or_si128(_mm256_castsi256_si128(signs16), _mm_slli_epi16(_mm256_extracti128_si256(signs16, 1), 8));
                signs128 = _mm_shuffle_epi8(signs128, s_shuffle);
                auto scales = _mm_set1_epi32(s32[ib]);
                scales = _mm_and_si128(_mm_unpacklo_epi8(scales, _mm_srli_epi16(scales, 4)), _mm_set1_epi8(0xf));
                scales = _mm_or_si128(_mm_slli_epi16(scales, 1), _mm_set1_epi8(1));
                auto scales16 = _mm256_cvtepi8_epi16(scales);  // 0...7, 0...7
                auto signs = MM256_SET1_M128I(signs128);
                auto shuffle = sign_shuffle;
                auto s1 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s2 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s3 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s4 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                __m256i scs[4] = {
                    _mm256_shuffle_epi8(scales16, shuffles[0]), _mm256_shuffle_epi8(scales16, shuffles[1]),
                    _mm256_shuffle_epi8(scales16, shuffles[2]), _mm256_shuffle_epi8(scales16, shuffles[3]),
                };
                for (int iy = 0; iy < nrc_y; ++iy) {
                    auto y = _mm256_loadu_si256((const __m256i *)q8.y[iy][ibl].qs + ib);
                    if constexpr (nrc_y == 1) {
                        isum[0] = ggml_mm256_dpwssd_epi32(isum[0], scs[0], _mm256_maddubs_epi16(qx[0], _mm256_sign_epi8(y, s1)));
                        isum[1] = ggml_mm256_dpwssd_epi32(isum[1], scs[1], _mm256_maddubs_epi16(qx[1], _mm256_sign_epi8(y, s2)));
                        isum[2] = ggml_mm256_dpwssd_epi32(isum[2], scs[2], _mm256_maddubs_epi16(qx[2], _mm256_sign_epi8(y, s3)));
                        isum[3] = ggml_mm256_dpwssd_epi32(isum[3], scs[3], _mm256_maddubs_epi16(qx[3], _mm256_sign_epi8(y, s4)));
                    } else {
                        auto sumi1 = ggml_mm256_dpwssd_epi32(_mm256_setzero_si256(), scs[0], _mm256_maddubs_epi16(qx[0], _mm256_sign_epi8(y, s1))); // blocks 4x0, 4x1, row 0
                        auto sumi2 = ggml_mm256_dpwssd_epi32(_mm256_setzero_si256(), scs[1], _mm256_maddubs_epi16(qx[1], _mm256_sign_epi8(y, s2))); // blocks 4x2, 4x3, row 1
                        auto sumi3 = ggml_mm256_dpwssd_epi32(_mm256_setzero_si256(), scs[2], _mm256_maddubs_epi16(qx[2], _mm256_sign_epi8(y, s3))); // blocks 4x4, 4x5, row 2
                        auto sumi4 = ggml_mm256_dpwssd_epi32(_mm256_setzero_si256(), scs[3], _mm256_maddubs_epi16(qx[3], _mm256_sign_epi8(y, s4))); // blocks 4x6, 4x7, row 3
                        auto s12 = _mm256_add_epi32(_mm256_unpacklo_epi32(sumi1, sumi2), _mm256_unpackhi_epi32(sumi1, sumi2)); // 0,1, 0,1, 0,1, 0,1
                        auto s34 = _mm256_add_epi32(_mm256_unpacklo_epi32(sumi3, sumi4), _mm256_unpackhi_epi32(sumi3, sumi4)); // 2,3, 2,3, 2,3, 2,3
                        auto sumi = _mm256_add_epi32(_mm256_unpacklo_epi64(s12, s34), _mm256_unpackhi_epi64(s12, s34)); // 0,1,2,3, 0,1,2,3
                        isum[iy] = _mm256_add_epi32(isum[iy], sumi);
                    }
                }
            }
            for (int iy = 0; iy < nrc_y; ++iy) {
                if constexpr (nrc_y == 1) {
                    auto s12 = _mm256_add_epi32(_mm256_unpacklo_epi32(isum[0], isum[1]), _mm256_unpackhi_epi32(isum[0], isum[1]));
                    auto s34 = _mm256_add_epi32(_mm256_unpacklo_epi32(isum[2], isum[3]), _mm256_unpackhi_epi32(isum[2], isum[3]));
                    auto sumi = _mm256_add_epi32(_mm256_unpacklo_epi64(s12, s34), _mm256_unpackhi_epi64(s12, s34));
                    acc[iy] = _mm256_fmadd_ps(_mm256_mul_ps(d4, _mm256_set1_ps(q8.scale(iy, ibl))), _mm256_cvtepi32_ps(sumi), acc[iy]);
                    isum[0] = isum[1] = isum[2] = isum[3] = _mm256_setzero_si256();
                } else {
                    acc[iy] = _mm256_fmadd_ps(_mm256_mul_ps(d4, _mm256_set1_ps(q8.scale(iy, ibl))), _mm256_cvtepi32_ps(isum[iy]), acc[iy]);
                    isum[iy] = _mm256_setzero_si256();
                }
            }
        }
        for (int iy = 0; iy < nrc_y; ++iy) {
            auto sum = _mm_add_ps(_mm256_castps256_ps128(acc[iy]), _mm256_extractf128_ps(acc[iy], 1));
            info.store(ix, iy, _mm_mul_ps(_mm_set1_ps(0.125f), sum));
            acc[iy] = _mm256_setzero_ps();
        }
    }
}
template <int nrc_y>
static void mul_mat_iq2_s_r4_q8_k(int n, const void * vx, size_t bx, const DataInfo& info, int nrc_x) {
    GGML_ASSERT(nrc_x%4 == 0);
    Q8<nrc_y, block_q8_K> q8(info);
    int nbl = n / QK_K;
    auto smask = _mm256_set1_epi64x(0x8040201008040201);
    auto sign_shuffle = _mm256_set_epi64x(0x0303030303030303, 0x0202020202020202, 0x0101010101010101, 0x0000000000000000);
    auto m4 = _mm256_set1_epi8(4);
    __m256  acc[nrc_y] = {};
    __m256i shuffles[4] = {
        MM256_SET_M128I(_mm_set1_epi16(0x0302), _mm_set1_epi16(0x0100)),
        MM256_SET_M128I(_mm_set1_epi16(0x0706), _mm_set1_epi16(0x0504)),
        MM256_SET_M128I(_mm_set1_epi16(0x0b0a), _mm_set1_epi16(0x0908)),
        MM256_SET_M128I(_mm_set1_epi16(0x0f0e), _mm_set1_epi16(0x0d0c)),
    };
    __m256i isum[nrc_y == 1 ? 4 : nrc_y] = {};
    __m256i qx[4];
    auto grid = iq2s_grid;
    for (int ix = 0; ix < nrc_x; ix += 4) {
        auto iq2 = (const block_iq2_s_r4 *)((const char *)vx + (ix+0)*bx);
        for (int ibl = 0; ibl < nbl; ++ibl) { // Block of 256
            auto dl = _mm_cvtph_ps(_mm_loadl_epi64((const __m128i *)iq2[ibl].d));
            auto d4 = _mm256_set_m128(dl, dl);
            auto s32 = (const uint32_t *)iq2[ibl].scales;
            auto ql = iq2[ibl].qs;
            auto qh = iq2[ibl].qh;
            for (int ib = 0; ib < QK_K/32; ++ib) {
                qx[0] = _mm256_set_epi64x(grid[ql[ 3] | ((qh[0] << 2) & 0x300)], grid[ql[ 2] | ((qh[0] << 4) & 0x300)], grid[ql[ 1] | ((qh[0] << 6) & 0x300)], grid[ql[ 0] | ((qh[0] << 8) & 0x300)]);
                qx[1] = _mm256_set_epi64x(grid[ql[ 7] | ((qh[1] << 2) & 0x300)], grid[ql[ 6] | ((qh[1] << 4) & 0x300)], grid[ql[ 5] | ((qh[1] << 6) & 0x300)], grid[ql[ 4] | ((qh[1] << 8) & 0x300)]);
                qx[2] = _mm256_set_epi64x(grid[ql[11] | ((qh[2] << 2) & 0x300)], grid[ql[10] | ((qh[2] << 4) & 0x300)], grid[ql[ 9] | ((qh[2] << 6) & 0x300)], grid[ql[ 8] | ((qh[2] << 8) & 0x300)]);
                qx[3] = _mm256_set_epi64x(grid[ql[15] | ((qh[3] << 2) & 0x300)], grid[ql[14] | ((qh[3] << 4) & 0x300)], grid[ql[13] | ((qh[3] << 6) & 0x300)], grid[ql[12] | ((qh[3] << 8) & 0x300)]);
                ql += 16; qh += 4;
                auto signs128 = _mm_loadu_si128((const __m128i*)iq2[ibl].signs + ib);
                auto scales = _mm_set1_epi32(s32[ib]);
                scales = _mm_and_si128(_mm_unpacklo_epi8(scales, _mm_srli_epi16(scales, 4)), _mm_set1_epi8(0xf));
                scales = _mm_or_si128(_mm_slli_epi16(scales, 1), _mm_set1_epi8(1));
                auto scales16 = _mm256_cvtepi8_epi16(scales);  // 0...7, 0...7
                auto signs = MM256_SET1_M128I(signs128);
                auto shuffle = sign_shuffle;
                auto s1 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s2 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s3 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s4 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                __m256i scs[4] = {
                    _mm256_shuffle_epi8(scales16, shuffles[0]), _mm256_shuffle_epi8(scales16, shuffles[1]),
                    _mm256_shuffle_epi8(scales16, shuffles[2]), _mm256_shuffle_epi8(scales16, shuffles[3]),
                };
                for (int iy = 0; iy < nrc_y; ++iy) {
                    auto y = _mm256_loadu_si256((const __m256i *)q8.y[iy][ibl].qs + ib);
                    if constexpr (nrc_y == 1) {
                        isum[0] = ggml_mm256_dpwssd_epi32(isum[0], scs[0], _mm256_maddubs_epi16(qx[0], _mm256_sign_epi8(y, s1)));
                        isum[1] = ggml_mm256_dpwssd_epi32(isum[1], scs[1], _mm256_maddubs_epi16(qx[1], _mm256_sign_epi8(y, s2)));
                        isum[2] = ggml_mm256_dpwssd_epi32(isum[2], scs[2], _mm256_maddubs_epi16(qx[2], _mm256_sign_epi8(y, s3)));
                        isum[3] = ggml_mm256_dpwssd_epi32(isum[3], scs[3], _mm256_maddubs_epi16(qx[3], _mm256_sign_epi8(y, s4)));
                    } else {
                        auto sumi1 = ggml_mm256_dpwssd_epi32(_mm256_setzero_si256(), scs[0], _mm256_maddubs_epi16(qx[0], _mm256_sign_epi8(y, s1))); // blocks 4x0, 4x1, row 0
                        auto sumi2 = ggml_mm256_dpwssd_epi32(_mm256_setzero_si256(), scs[1], _mm256_maddubs_epi16(qx[1], _mm256_sign_epi8(y, s2))); // blocks 4x2, 4x3, row 1
                        auto sumi3 = ggml_mm256_dpwssd_epi32(_mm256_setzero_si256(), scs[2], _mm256_maddubs_epi16(qx[2], _mm256_sign_epi8(y, s3))); // blocks 4x4, 4x5, row 2
                        auto sumi4 = ggml_mm256_dpwssd_epi32(_mm256_setzero_si256(), scs[3], _mm256_maddubs_epi16(qx[3], _mm256_sign_epi8(y, s4))); // blocks 4x6, 4x7, row 3
                        auto s12 = _mm256_add_epi32(_mm256_unpacklo_epi32(sumi1, sumi2), _mm256_unpackhi_epi32(sumi1, sumi2)); // 0,1, 0,1, 0,1, 0,1
                        auto s34 = _mm256_add_epi32(_mm256_unpacklo_epi32(sumi3, sumi4), _mm256_unpackhi_epi32(sumi3, sumi4)); // 2,3, 2,3, 2,3, 2,3
                        auto sumi = _mm256_add_epi32(_mm256_unpacklo_epi64(s12, s34), _mm256_unpackhi_epi64(s12, s34)); // 0,1,2,3, 0,1,2,3
                        isum[iy] = _mm256_add_epi32(isum[iy], sumi);
                    }
                }
            }
            for (int iy = 0; iy < nrc_y; ++iy) {
                if constexpr (nrc_y == 1) {
                    auto s12 = _mm256_add_epi32(_mm256_unpacklo_epi32(isum[0], isum[1]), _mm256_unpackhi_epi32(isum[0], isum[1]));
                    auto s34 = _mm256_add_epi32(_mm256_unpacklo_epi32(isum[2], isum[3]), _mm256_unpackhi_epi32(isum[2], isum[3]));
                    auto sumi = _mm256_add_epi32(_mm256_unpacklo_epi64(s12, s34), _mm256_unpackhi_epi64(s12, s34));
                    acc[iy] = _mm256_fmadd_ps(_mm256_mul_ps(d4, _mm256_set1_ps(q8.scale(iy, ibl))), _mm256_cvtepi32_ps(sumi), acc[iy]);
                    isum[0] = isum[1] = isum[2] = isum[3] = _mm256_setzero_si256();
                } else {
                    acc[iy] = _mm256_fmadd_ps(_mm256_mul_ps(d4, _mm256_set1_ps(q8.scale(iy, ibl))), _mm256_cvtepi32_ps(isum[iy]), acc[iy]);
                    isum[iy] = _mm256_setzero_si256();
                }
            }
        }
        for (int iy = 0; iy < nrc_y; ++iy) {
            auto sum = _mm_add_ps(_mm256_castps256_ps128(acc[iy]), _mm256_extractf128_ps(acc[iy], 1));
            info.store(ix, iy, _mm_mul_ps(_mm_set1_ps(0.125f), sum));
            acc[iy] = _mm256_setzero_ps();
        }
    }
}
template <int nrc_y>
static void mul_mat_iq3_xxs_r4_q8_k(int n, const void * vx, size_t bx, const DataInfo& info, int nrc_x) {
    GGML_ASSERT(nrc_x%4 == 0);
    Q8<nrc_y, block_q8_K> q8(info);
    int nbl = n / QK_K;
    auto smask = _mm256_set1_epi64x(0x8040201008040201);
    auto sign_shuffle = _mm256_set_epi64x(0x0303030303030303, 0x0202020202020202, 0x0101010101010101, 0x0000000000000000);
    auto m4 = _mm256_set1_epi8(4);
    __m256  acc[nrc_y] = {};
    __m256i isum[nrc_y] = {};
    __m256i qx[4];
    for (int ix = 0; ix < nrc_x; ix += 4) {
        auto iq3 = (const block_iq3_xxs_r4 *)((const char *)vx + (ix+0)*bx);
        for (int ibl = 0; ibl < nbl; ++ibl) { // Block of 256
            auto dl = _mm_mul_ps(_mm_set1_ps(0.25f), _mm_cvtph_ps(_mm_loadl_epi64((const __m128i *)iq3[ibl].d))); // TODO: absorb the 0.25 factor into d when quantizing/repacking
            auto d4 = _mm256_set_m128(dl, dl);
            for (int ib = 0; ib < QK_K/32; ++ib) {
                qx[0] = _mm256_set_epi32(iq3xxs_grid[iq3[ibl].qs[32*ib+ 7]], iq3xxs_grid[iq3[ibl].qs[32*ib+ 6]], iq3xxs_grid[iq3[ibl].qs[32*ib+ 5]], iq3xxs_grid[iq3[ibl].qs[32*ib+ 4]],
                                         iq3xxs_grid[iq3[ibl].qs[32*ib+ 3]], iq3xxs_grid[iq3[ibl].qs[32*ib+ 2]], iq3xxs_grid[iq3[ibl].qs[32*ib+ 1]], iq3xxs_grid[iq3[ibl].qs[32*ib+ 0]]);
                qx[1] = _mm256_set_epi32(iq3xxs_grid[iq3[ibl].qs[32*ib+15]], iq3xxs_grid[iq3[ibl].qs[32*ib+14]], iq3xxs_grid[iq3[ibl].qs[32*ib+13]], iq3xxs_grid[iq3[ibl].qs[32*ib+12]],
                                         iq3xxs_grid[iq3[ibl].qs[32*ib+11]], iq3xxs_grid[iq3[ibl].qs[32*ib+10]], iq3xxs_grid[iq3[ibl].qs[32*ib+ 9]], iq3xxs_grid[iq3[ibl].qs[32*ib+ 8]]);
                qx[2] = _mm256_set_epi32(iq3xxs_grid[iq3[ibl].qs[32*ib+23]], iq3xxs_grid[iq3[ibl].qs[32*ib+22]], iq3xxs_grid[iq3[ibl].qs[32*ib+21]], iq3xxs_grid[iq3[ibl].qs[32*ib+20]],
                                         iq3xxs_grid[iq3[ibl].qs[32*ib+19]], iq3xxs_grid[iq3[ibl].qs[32*ib+18]], iq3xxs_grid[iq3[ibl].qs[32*ib+17]], iq3xxs_grid[iq3[ibl].qs[32*ib+16]]);
                qx[3] = _mm256_set_epi32(iq3xxs_grid[iq3[ibl].qs[32*ib+31]], iq3xxs_grid[iq3[ibl].qs[32*ib+30]], iq3xxs_grid[iq3[ibl].qs[32*ib+29]], iq3xxs_grid[iq3[ibl].qs[32*ib+28]],
                                         iq3xxs_grid[iq3[ibl].qs[32*ib+27]], iq3xxs_grid[iq3[ibl].qs[32*ib+26]], iq3xxs_grid[iq3[ibl].qs[32*ib+25]], iq3xxs_grid[iq3[ibl].qs[32*ib+24]]);
                auto sas = _mm_loadu_si128((const __m128i *)iq3[ibl].sas + ib);
                auto scales = _mm_and_si128(sas, _mm_set1_epi8(1));
                scales = ggml_mm_dpbusd_epi32(_mm_set1_epi32(1), scales, _mm_set1_epi32(0x10080402));
                auto scales32 = MM256_SET1_M128I(scales);
                auto signs128 = _mm_and_si128(sas, _mm_set1_epi8(-2)); // 0xfe = -2 as signed. Needed to shutup compiler warning.
                signs128 = _mm_xor_si128(signs128, _mm_srli_epi16(signs128, 1));
                auto signs = MM256_SET1_M128I(signs128);
                auto shuffle = sign_shuffle;
                auto s1 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s2 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s3 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s4 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                for (int iy = 0; iy < nrc_y; ++iy) {
                    auto y = _mm256_loadu_si256((const __m256i *)q8.y[iy][ibl].qs + ib);
                    auto sumi1 = ggml_mm256_dpbusd_epi32(_mm256_setzero_si256(), qx[0], _mm256_sign_epi8(y, s1));
                    auto sumi2 = ggml_mm256_dpbusd_epi32(_mm256_setzero_si256(), qx[1], _mm256_sign_epi8(y, s2));
                    auto sumi3 = ggml_mm256_dpbusd_epi32(_mm256_setzero_si256(), qx[2], _mm256_sign_epi8(y, s3));
                    auto sumi4 = ggml_mm256_dpbusd_epi32(_mm256_setzero_si256(), qx[3], _mm256_sign_epi8(y, s4));
                    auto s12 = _mm256_add_epi32(_mm256_unpacklo_epi32(sumi1, sumi2), _mm256_unpackhi_epi32(sumi1, sumi2)); // 0,1, 0,1, 0,1, 0,1
                    auto s34 = _mm256_add_epi32(_mm256_unpacklo_epi32(sumi3, sumi4), _mm256_unpackhi_epi32(sumi3, sumi4)); // 2,3, 2,3, 2,3, 2,3
                    auto sumi = _mm256_add_epi32(_mm256_unpacklo_epi64(s12, s34), _mm256_unpackhi_epi64(s12, s34)); // 0,1,2,3, 0,1,2,3
                    isum[iy] = _mm256_add_epi32(isum[iy], _mm256_mullo_epi32(scales32, sumi));
                }
            }
            for (int iy = 0; iy < nrc_y; ++iy) {
                acc[iy] = _mm256_fmadd_ps(_mm256_mul_ps(d4, _mm256_set1_ps(q8.scale(iy, ibl))), _mm256_cvtepi32_ps(isum[iy]), acc[iy]);
                isum[iy] = _mm256_setzero_si256();
            }
        }
        for (int iy = 0; iy < nrc_y; ++iy) {
            auto sum = _mm_add_ps(_mm256_castps256_ps128(acc[iy]), _mm256_extractf128_ps(acc[iy], 1));
            info.store(ix, iy, sum);
            acc[iy] = _mm256_setzero_ps();
        }
    }
}
template <int nrc_y>
static void mul_mat_iq3_s_r4_q8_k(int n, const void * vx, size_t bx, const DataInfo& info, int nrc_x) {
    GGML_ASSERT(nrc_x%4 == 0);
    Q8<nrc_y, block_q8_K> q8(info);
    int nbl = n / QK_K;
    auto smask = _mm256_set1_epi8(1);
    union { __m256i vec; uint32_t val[8]; } helper;
    union { __m128i vec; uint16_t val[8]; } hidx;
    __m256  acc[nrc_y] = {};
    __m256i isum[nrc_y] = {};
    __m256i qx[4];
    for (int ix = 0; ix < nrc_x; ix += 4) {
        auto iq3 = (const block_iq3_s_r4 *)((const char *)vx + (ix+0)*bx);
        for (int ibl = 0; ibl < nbl; ++ibl) { // Block of 256
            auto dl = _mm_cvtph_ps(_mm_loadl_epi64((const __m128i *)iq3[ibl].d));
            auto d4 = _mm256_set_m128(dl, dl);
            auto qs = iq3[ibl].qs;
            auto qh = iq3[ibl].qh;
            auto scale_bits = _mm_loadu_si128((const __m128i *)iq3[ibl].scales);
            auto scales8 = MM256_SET_M128I(_mm_srli_epi16(scale_bits, 4), scale_bits);
            helper.vec = _mm256_or_si256(_mm256_slli_epi16(_mm256_and_si256(scales8, _mm256_set1_epi8(0xf)), 1), _mm256_set1_epi8(1));
            for (int ib = 0; ib < QK_K/32; ++ib) {
                auto qh32 = (const uint32_t *)qh;
                auto idx_h = _mm_sllv_epi64(_mm_cvtepu8_epi16(_mm_set1_epi32(qh32[0])), _mm_set_epi64x(4, 8));
                for (int i = 0; i < 4; ++i) {
                    auto idx_l = _mm_cvtepu8_epi16(_mm_loadl_epi64((const __m128i *)(qs + 8*i)));
                    hidx.vec = _mm_or_si128(idx_l, _mm_and_si128(idx_h, _mm_set1_epi16(0x100))); idx_h = _mm_srli_epi16(idx_h, 1);
                    qx[i] = _mm256_set_epi32(iq3s_grid[hidx.val[7]], iq3s_grid[hidx.val[6]], iq3s_grid[hidx.val[5]], iq3s_grid[hidx.val[4]],
                                             iq3s_grid[hidx.val[3]], iq3s_grid[hidx.val[2]], iq3s_grid[hidx.val[1]], iq3s_grid[hidx.val[0]]);
                }
                qs += 32; qh += 4;
                auto signs128 = _mm_loadu_si128((const __m128i*)iq3[ibl].signs + ib);
                auto signs = MM256_SET_M128I(_mm_srli_epi16(signs128, 4), signs128);
                auto scales = _mm256_cvtepi8_epi32(_mm_set1_epi32(helper.val[ib]));
                auto s1 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(signs, smask), smask), smask); signs = _mm256_srli_epi16(signs, 1);
                auto s2 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(signs, smask), smask), smask); signs = _mm256_srli_epi16(signs, 1);
                auto s3 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(signs, smask), smask), smask); signs = _mm256_srli_epi16(signs, 1);
                auto s4 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(signs, smask), smask), smask);
                for (int iy = 0; iy < nrc_y; ++iy) {
                    auto y = _mm256_loadu_si256((const __m256i *)q8.y[iy][ibl].qs + ib);
                    auto sumi = _mm256_setzero_si256();
                    sumi = ggml_mm256_dpbusd_epi32(sumi, qx[0], _mm256_sign_epi8(_mm256_shuffle_epi32(y, 0x00), s1));
                    sumi = ggml_mm256_dpbusd_epi32(sumi, qx[1], _mm256_sign_epi8(_mm256_shuffle_epi32(y, 0x55), s2));
                    sumi = ggml_mm256_dpbusd_epi32(sumi, qx[2], _mm256_sign_epi8(_mm256_shuffle_epi32(y, 0xaa), s3));
                    sumi = ggml_mm256_dpbusd_epi32(sumi, qx[3], _mm256_sign_epi8(_mm256_shuffle_epi32(y, 0xff), s4));
                    isum[iy] = _mm256_add_epi32(isum[iy], _mm256_mullo_epi32(sumi, scales));
                }
            }
            for (int iy = 0; iy < nrc_y; ++iy) {
                acc[iy] = _mm256_fmadd_ps(_mm256_mul_ps(d4, _mm256_set1_ps(q8.scale(iy, ibl))), _mm256_cvtepi32_ps(isum[iy]), acc[iy]);
                isum[iy] = _mm256_setzero_si256();
            }
        }
        for (int iy = 0; iy < nrc_y; ++iy) {
            auto sum = _mm_add_ps(_mm256_castps256_ps128(acc[iy]), _mm256_extractf128_ps(acc[iy], 1));
            info.store(ix, iy, sum);
            acc[iy] = _mm256_setzero_ps();
        }
    }
}
}
namespace gather {
template <int nrc_y>
static void mul_mat_iq2_xxs_r4_q8_k(int n, const void * vx, size_t bx, const DataInfo& info, int nrc_x) {
    GGML_ASSERT(nrc_x%4 == 0);
    Q8<nrc_y, block_q8_K> q8(info);
    int nbl = n / QK_K;
    auto smask = _mm256_set1_epi64x(0x8040201008040201);
    auto sign_shuffle = _mm256_set_epi64x(0x0303030303030303, 0x0202020202020202, 0x0101010101010101, 0x0000000000000000);
    auto m4 = _mm256_set1_epi8(4);
    auto m1 = _mm256_set1_epi16(1);
    __m256  acc[nrc_y] = {};
    __m256i isum[nrc_y] = {};
    __m256i qx[4];
    for (int ix = 0; ix < nrc_x; ix += 4) {
        auto iq2 = (const block_iq2_xxs_r4 *)((const char *)vx + (ix+0)*bx);
        for (int ibl = 0; ibl < nbl; ++ibl) { // Block of 256
            auto dl = _mm_cvtph_ps(_mm_loadl_epi64((const __m128i *)iq2[ibl].d));
            auto d4 = _mm256_set_m128(dl, dl);
            auto qs = iq2[ibl].qs;
            for (int ib = 0; ib < QK_K/32; ++ib) {
                qx[0] = _mm256_set_epi64x(iq2xxs_grid[qs[ 3]], iq2xxs_grid[qs[ 2]], iq2xxs_grid[qs[ 1]], iq2xxs_grid[qs[ 0]]);
                qx[1] = _mm256_set_epi64x(iq2xxs_grid[qs[ 7]], iq2xxs_grid[qs[ 6]], iq2xxs_grid[qs[ 5]], iq2xxs_grid[qs[ 4]]);
                qx[2] = _mm256_set_epi64x(iq2xxs_grid[qs[11]], iq2xxs_grid[qs[10]], iq2xxs_grid[qs[ 9]], iq2xxs_grid[qs[ 8]]);
                qx[3] = _mm256_set_epi64x(iq2xxs_grid[qs[15]], iq2xxs_grid[qs[14]], iq2xxs_grid[qs[13]], iq2xxs_grid[qs[12]]);
                qs += 16;
                auto sas = _mm_loadu_si128((const __m128i *)iq2[ibl].sas + ib);
                auto scales = _mm_and_si128(sas, _mm_set1_epi8(1));
                scales = _mm_maddubs_epi16(scales, _mm_set1_epi32(0x10080402));
                scales = _mm_add_epi32(_mm_madd_epi16(_mm_set1_epi16(1), scales), _mm_set1_epi32(1));
                auto scales32 = MM256_SET1_M128I(scales);
                auto signs128 = _mm_and_si128(sas, _mm_set1_epi8(-2)); // 0xfe = -2 as signed. Needed to shutup compiler warning.
                signs128 = _mm_xor_si128(signs128, _mm_srli_epi16(signs128, 1));
                auto signs = MM256_SET1_M128I(signs128);
                auto shuffle = sign_shuffle;
                auto s1 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s2 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s3 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s4 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                for (int iy = 0; iy < nrc_y; ++iy) {
                    auto y = _mm256_loadu_si256((const __m256i *)q8.y[iy][ibl].qs + ib);
                    auto sumi1 = ggml_mm256_dpbusd_epi32(_mm256_setzero_si256(), qx[0], _mm256_sign_epi8(y, s1));
                    auto sumi2 = ggml_mm256_dpbusd_epi32(_mm256_setzero_si256(), qx[1], _mm256_sign_epi8(y, s2));
                    auto sumi3 = ggml_mm256_dpbusd_epi32(_mm256_setzero_si256(), qx[2], _mm256_sign_epi8(y, s3));
                    auto sumi4 = ggml_mm256_dpbusd_epi32(_mm256_setzero_si256(), qx[3], _mm256_sign_epi8(y, s4));
                    auto s12 = _mm256_add_epi32(_mm256_unpacklo_epi32(sumi1, sumi2), _mm256_unpackhi_epi32(sumi1, sumi2)); // 0,1, 0,1, 0,1, 0,1
                    auto s34 = _mm256_add_epi32(_mm256_unpacklo_epi32(sumi3, sumi4), _mm256_unpackhi_epi32(sumi3, sumi4)); // 2,3, 2,3, 2,3, 2,3
                    auto sumi = _mm256_add_epi32(_mm256_unpacklo_epi64(s12, s34), _mm256_unpackhi_epi64(s12, s34)); // 0,1,2,3, 0,1,2,3
                    isum[iy] = _mm256_add_epi32(isum[iy], _mm256_mullo_epi32(scales32, sumi));
                }
            }
            for (int iy = 0; iy < nrc_y; ++iy) {
                acc[iy] = _mm256_fmadd_ps(_mm256_mul_ps(d4, _mm256_set1_ps(q8.scale(iy, ibl))), _mm256_cvtepi32_ps(isum[iy]), acc[iy]);
                isum[iy] = _mm256_setzero_si256();
            }
        }
        for (int iy = 0; iy < nrc_y; ++iy) {
            auto sum = _mm_add_ps(_mm256_castps256_ps128(acc[iy]), _mm256_extractf128_ps(acc[iy], 1));
            info.store(ix, iy, _mm_mul_ps(_mm_set1_ps(0.125f), sum));
            acc[iy] = _mm256_setzero_ps();
        }
    }
}
template <int nrc_y>
static void mul_mat_iq2_xs_r4_q8_k(int n, const void * vx, size_t bx, const DataInfo& info, int nrc_x) {
    GGML_ASSERT(nrc_x%4 == 0);
    Q8<nrc_y, block_q8_K> q8(info);
    int nbl = n / QK_K;
    auto smask = _mm256_set1_epi64x(0x8040201008040201);
    auto sign_shuffle = _mm256_set_epi64x(0x0303030303030303, 0x0202020202020202, 0x0101010101010101, 0x0000000000000000);
    auto m4 = _mm256_set1_epi8(4);
    __m256  acc[nrc_y] = {};
    __m256i shuffles[4] = {
        MM256_SET_M128I(_mm_set1_epi16(0x0302), _mm_set1_epi16(0x0100)),
        MM256_SET_M128I(_mm_set1_epi16(0x0706), _mm_set1_epi16(0x0504)),
        MM256_SET_M128I(_mm_set1_epi16(0x0b0a), _mm_set1_epi16(0x0908)),
        MM256_SET_M128I(_mm_set1_epi16(0x0f0e), _mm_set1_epi16(0x0d0c)),
    };
    __m256i isum[nrc_y == 1 ? 4 : nrc_y] = {};
    auto s_shuffle = _mm_set_epi64x(0x0f0d0b0907050301, 0x0e0c0a0806040200);
    __m256i qx[4];
    union { __m256i vec; uint16_t val[16]; } helper;
    for (int ix = 0; ix < nrc_x; ix += 4) {
        auto iq2 = (const block_iq2_xs_r4 *)((const char *)vx + (ix+0)*bx);
        for (int ibl = 0; ibl < nbl; ++ibl) { // Block of 256
            auto dl = _mm_cvtph_ps(_mm_loadl_epi64((const __m128i *)iq2[ibl].d));
            auto d4 = _mm256_set_m128(dl, dl);
            auto s32 = (const uint32_t *)iq2[ibl].scales;
            for (int ib = 0; ib < QK_K/32; ++ib) {
                auto val = _mm256_loadu_si256((const __m256i *)iq2[ibl].qs + ib);
                helper.vec = _mm256_and_si256(val, _mm256_set1_epi16(511));
                qx[0] = _mm256_set_epi64x(iq2xs_grid[helper.val[ 3]], iq2xs_grid[helper.val[ 2]], iq2xs_grid[helper.val[ 1]], iq2xs_grid[helper.val[ 0]]);
                qx[1] = _mm256_set_epi64x(iq2xs_grid[helper.val[ 7]], iq2xs_grid[helper.val[ 6]], iq2xs_grid[helper.val[ 5]], iq2xs_grid[helper.val[ 4]]);
                qx[2] = _mm256_set_epi64x(iq2xs_grid[helper.val[11]], iq2xs_grid[helper.val[10]], iq2xs_grid[helper.val[ 9]], iq2xs_grid[helper.val[ 8]]);
                qx[3] = _mm256_set_epi64x(iq2xs_grid[helper.val[15]], iq2xs_grid[helper.val[14]], iq2xs_grid[helper.val[13]], iq2xs_grid[helper.val[12]]);
                auto signs16 = _mm256_srli_epi16(val, 9);
                signs16 = _mm256_xor_si256(signs16, _mm256_slli_epi16(signs16, 1));
                auto signs128 = _mm_or_si128(_mm256_castsi256_si128(signs16), _mm_slli_epi16(_mm256_extracti128_si256(signs16, 1), 8));
                signs128 = _mm_shuffle_epi8(signs128, s_shuffle);
                auto scales = _mm_set1_epi32(s32[ib]);
                scales = _mm_and_si128(_mm_unpacklo_epi8(scales, _mm_srli_epi16(scales, 4)), _mm_set1_epi8(0xf));
                scales = _mm_or_si128(_mm_slli_epi16(scales, 1), _mm_set1_epi8(1));
                auto scales16 = _mm256_cvtepi8_epi16(scales);  // 0...7, 0...7
                auto signs = MM256_SET1_M128I(signs128);
                auto shuffle = sign_shuffle;
                auto s1 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s2 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s3 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s4 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                __m256i scs[4] = {
                    _mm256_shuffle_epi8(scales16, shuffles[0]), _mm256_shuffle_epi8(scales16, shuffles[1]),
                    _mm256_shuffle_epi8(scales16, shuffles[2]), _mm256_shuffle_epi8(scales16, shuffles[3]),
                };
                for (int iy = 0; iy < nrc_y; ++iy) {
                    auto y = _mm256_loadu_si256((const __m256i *)q8.y[iy][ibl].qs + ib);
                    if constexpr (nrc_y == 1) {
                        isum[0] = ggml_mm256_dpwssd_epi32(isum[0], scs[0], _mm256_maddubs_epi16(qx[0], _mm256_sign_epi8(y, s1)));
                        isum[1] = ggml_mm256_dpwssd_epi32(isum[1], scs[1], _mm256_maddubs_epi16(qx[1], _mm256_sign_epi8(y, s2)));
                        isum[2] = ggml_mm256_dpwssd_epi32(isum[2], scs[2], _mm256_maddubs_epi16(qx[2], _mm256_sign_epi8(y, s3)));
                        isum[3] = ggml_mm256_dpwssd_epi32(isum[3], scs[3], _mm256_maddubs_epi16(qx[3], _mm256_sign_epi8(y, s4)));
                    } else {
                        auto sumi1 = ggml_mm256_dpwssd_epi32(_mm256_setzero_si256(), scs[0], _mm256_maddubs_epi16(qx[0], _mm256_sign_epi8(y, s1))); // blocks 4x0, 4x1, row 0
                        auto sumi2 = ggml_mm256_dpwssd_epi32(_mm256_setzero_si256(), scs[1], _mm256_maddubs_epi16(qx[1], _mm256_sign_epi8(y, s2))); // blocks 4x2, 4x3, row 1
                        auto sumi3 = ggml_mm256_dpwssd_epi32(_mm256_setzero_si256(), scs[2], _mm256_maddubs_epi16(qx[2], _mm256_sign_epi8(y, s3))); // blocks 4x4, 4x5, row 2
                        auto sumi4 = ggml_mm256_dpwssd_epi32(_mm256_setzero_si256(), scs[3], _mm256_maddubs_epi16(qx[3], _mm256_sign_epi8(y, s4))); // blocks 4x6, 4x7, row 3
                        auto s12 = _mm256_add_epi32(_mm256_unpacklo_epi32(sumi1, sumi2), _mm256_unpackhi_epi32(sumi1, sumi2)); // 0,1, 0,1, 0,1, 0,1
                        auto s34 = _mm256_add_epi32(_mm256_unpacklo_epi32(sumi3, sumi4), _mm256_unpackhi_epi32(sumi3, sumi4)); // 2,3, 2,3, 2,3, 2,3
                        auto sumi = _mm256_add_epi32(_mm256_unpacklo_epi64(s12, s34), _mm256_unpackhi_epi64(s12, s34)); // 0,1,2,3, 0,1,2,3
                        isum[iy] = _mm256_add_epi32(isum[iy], sumi);
                    }
                }
            }
            for (int iy = 0; iy < nrc_y; ++iy) {
                if constexpr (nrc_y == 1) {
                    auto s12 = _mm256_add_epi32(_mm256_unpacklo_epi32(isum[0], isum[1]), _mm256_unpackhi_epi32(isum[0], isum[1]));
                    auto s34 = _mm256_add_epi32(_mm256_unpacklo_epi32(isum[2], isum[3]), _mm256_unpackhi_epi32(isum[2], isum[3]));
                    auto sumi = _mm256_add_epi32(_mm256_unpacklo_epi64(s12, s34), _mm256_unpackhi_epi64(s12, s34));
                    acc[iy] = _mm256_fmadd_ps(_mm256_mul_ps(d4, _mm256_set1_ps(q8.scale(iy, ibl))), _mm256_cvtepi32_ps(sumi), acc[iy]);
                    isum[0] = isum[1] = isum[2] = isum[3] = _mm256_setzero_si256();
                } else {
                    acc[iy] = _mm256_fmadd_ps(_mm256_mul_ps(d4, _mm256_set1_ps(q8.scale(iy, ibl))), _mm256_cvtepi32_ps(isum[iy]), acc[iy]);
                    isum[iy] = _mm256_setzero_si256();
                }
            }
        }
        for (int iy = 0; iy < nrc_y; ++iy) {
            auto sum = _mm_add_ps(_mm256_castps256_ps128(acc[iy]), _mm256_extractf128_ps(acc[iy], 1));
            info.store(ix, iy, _mm_mul_ps(_mm_set1_ps(0.125f), sum));
            acc[iy] = _mm256_setzero_ps();
        }
    }
}
template <int nrc_y>
static void mul_mat_iq2_s_r4_q8_k(int n, const void * vx, size_t bx, const DataInfo& info, int nrc_x) {
    GGML_ASSERT(nrc_x%4 == 0);
    Q8<nrc_y, block_q8_K> q8(info);
    int nbl = n / QK_K;
    auto smask = _mm256_set1_epi64x(0x8040201008040201);
    auto sign_shuffle = _mm256_set_epi64x(0x0303030303030303, 0x0202020202020202, 0x0101010101010101, 0x0000000000000000);
    auto m4 = _mm256_set1_epi8(4);
    __m256  acc[nrc_y] = {};
    __m256i shuffles[4] = {
        MM256_SET_M128I(_mm_set1_epi16(0x0302), _mm_set1_epi16(0x0100)),
        MM256_SET_M128I(_mm_set1_epi16(0x0706), _mm_set1_epi16(0x0504)),
        MM256_SET_M128I(_mm_set1_epi16(0x0b0a), _mm_set1_epi16(0x0908)),
        MM256_SET_M128I(_mm_set1_epi16(0x0f0e), _mm_set1_epi16(0x0d0c)),
    };
    __m256i isum[nrc_y == 1 ? 4 : nrc_y] = {};
    __m256i qx[4];
    auto grid = iq2s_grid;
    for (int ix = 0; ix < nrc_x; ix += 4) {
        auto iq2 = (const block_iq2_s_r4 *)((const char *)vx + (ix+0)*bx);
        for (int ibl = 0; ibl < nbl; ++ibl) { // Block of 256
            auto dl = _mm_cvtph_ps(_mm_loadl_epi64((const __m128i *)iq2[ibl].d));
            auto d4 = _mm256_set_m128(dl, dl);
            auto s32 = (const uint32_t *)iq2[ibl].scales;
            auto ql = iq2[ibl].qs;
            auto qh = iq2[ibl].qh;
            for (int ib = 0; ib < QK_K/32; ++ib) {
                {
                    uint32_t lo; std::memcpy(&lo, ql+0, sizeof(lo));
                    auto indices = _mm_cvtepu8_epi32(_mm_cvtsi32_si128((int)lo));
                    auto hi = _mm_and_si128(_mm_srlv_epi32(_mm_set1_epi32(qh[0]), _mm_set_epi32(6,4,2,0)), _mm_set1_epi32(3));
                    indices = _mm_or_si128(indices, _mm_slli_epi32(hi,8));
                    qx[0] = _mm256_i32gather_epi64((const long long*)grid, indices, 8);
                }
                {
                    uint32_t lo; std::memcpy(&lo, ql+4, sizeof(lo));
                    auto indices = _mm_cvtepu8_epi32(_mm_cvtsi32_si128((int)lo));
                    auto hi = _mm_and_si128(_mm_srlv_epi32(_mm_set1_epi32(qh[1]), _mm_set_epi32(6,4,2,0)), _mm_set1_epi32(3));
                    indices = _mm_or_si128(indices, _mm_slli_epi32(hi,8));
                    qx[1] = _mm256_i32gather_epi64((const long long*)grid, indices, 8);
                }
                {
                    uint32_t lo; std::memcpy(&lo, ql+8, sizeof(lo));
                    auto indices = _mm_cvtepu8_epi32(_mm_cvtsi32_si128((int)lo));
                    auto hi = _mm_and_si128(_mm_srlv_epi32(_mm_set1_epi32(qh[2]), _mm_set_epi32(6,4,2,0)), _mm_set1_epi32(3));
                    indices = _mm_or_si128(indices, _mm_slli_epi32(hi,8));
                    qx[2] = _mm256_i32gather_epi64((const long long*)grid, indices, 8);
                }
                {
                    uint32_t lo; std::memcpy(&lo, ql+12, sizeof(lo));
                    auto indices = _mm_cvtepu8_epi32(_mm_cvtsi32_si128((int)lo));
                    auto hi = _mm_and_si128(_mm_srlv_epi32(_mm_set1_epi32(qh[3]), _mm_set_epi32(6,4,2,0)), _mm_set1_epi32(3));
                    indices = _mm_or_si128(indices, _mm_slli_epi32(hi,8));
                    qx[3] = _mm256_i32gather_epi64((const long long*)grid, indices, 8);
                }
                ql += 16; qh += 4;
                auto signs128 = _mm_loadu_si128((const __m128i*)iq2[ibl].signs + ib);
                auto scales = _mm_set1_epi32(s32[ib]);
                scales = _mm_and_si128(_mm_unpacklo_epi8(scales, _mm_srli_epi16(scales, 4)), _mm_set1_epi8(0xf));
                scales = _mm_or_si128(_mm_slli_epi16(scales, 1), _mm_set1_epi8(1));
                auto scales16 = _mm256_cvtepi8_epi16(scales);  // 0...7, 0...7
                auto signs = MM256_SET1_M128I(signs128);
                auto shuffle = sign_shuffle;
                auto s1 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s2 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s3 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s4 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                __m256i scs[4] = {
                    _mm256_shuffle_epi8(scales16, shuffles[0]), _mm256_shuffle_epi8(scales16, shuffles[1]),
                    _mm256_shuffle_epi8(scales16, shuffles[2]), _mm256_shuffle_epi8(scales16, shuffles[3]),
                };
                for (int iy = 0; iy < nrc_y; ++iy) {
                    auto y = _mm256_loadu_si256((const __m256i *)q8.y[iy][ibl].qs + ib);
                    if constexpr (nrc_y == 1) {
                        isum[0] = ggml_mm256_dpwssd_epi32(isum[0], scs[0], _mm256_maddubs_epi16(qx[0], _mm256_sign_epi8(y, s1)));
                        isum[1] = ggml_mm256_dpwssd_epi32(isum[1], scs[1], _mm256_maddubs_epi16(qx[1], _mm256_sign_epi8(y, s2)));
                        isum[2] = ggml_mm256_dpwssd_epi32(isum[2], scs[2], _mm256_maddubs_epi16(qx[2], _mm256_sign_epi8(y, s3)));
                        isum[3] = ggml_mm256_dpwssd_epi32(isum[3], scs[3], _mm256_maddubs_epi16(qx[3], _mm256_sign_epi8(y, s4)));
                    } else {
                        auto sumi1 = ggml_mm256_dpwssd_epi32(_mm256_setzero_si256(), scs[0], _mm256_maddubs_epi16(qx[0], _mm256_sign_epi8(y, s1))); // blocks 4x0, 4x1, row 0
                        auto sumi2 = ggml_mm256_dpwssd_epi32(_mm256_setzero_si256(), scs[1], _mm256_maddubs_epi16(qx[1], _mm256_sign_epi8(y, s2))); // blocks 4x2, 4x3, row 1
                        auto sumi3 = ggml_mm256_dpwssd_epi32(_mm256_setzero_si256(), scs[2], _mm256_maddubs_epi16(qx[2], _mm256_sign_epi8(y, s3))); // blocks 4x4, 4x5, row 2
                        auto sumi4 = ggml_mm256_dpwssd_epi32(_mm256_setzero_si256(), scs[3], _mm256_maddubs_epi16(qx[3], _mm256_sign_epi8(y, s4))); // blocks 4x6, 4x7, row 3
                        auto s12 = _mm256_add_epi32(_mm256_unpacklo_epi32(sumi1, sumi2), _mm256_unpackhi_epi32(sumi1, sumi2)); // 0,1, 0,1, 0,1, 0,1
                        auto s34 = _mm256_add_epi32(_mm256_unpacklo_epi32(sumi3, sumi4), _mm256_unpackhi_epi32(sumi3, sumi4)); // 2,3, 2,3, 2,3, 2,3
                        auto sumi = _mm256_add_epi32(_mm256_unpacklo_epi64(s12, s34), _mm256_unpackhi_epi64(s12, s34)); // 0,1,2,3, 0,1,2,3
                        isum[iy] = _mm256_add_epi32(isum[iy], sumi);
                    }
                }
            }
            for (int iy = 0; iy < nrc_y; ++iy) {
                if constexpr (nrc_y == 1) {
                    auto s12 = _mm256_add_epi32(_mm256_unpacklo_epi32(isum[0], isum[1]), _mm256_unpackhi_epi32(isum[0], isum[1]));
                    auto s34 = _mm256_add_epi32(_mm256_unpacklo_epi32(isum[2], isum[3]), _mm256_unpackhi_epi32(isum[2], isum[3]));
                    auto sumi = _mm256_add_epi32(_mm256_unpacklo_epi64(s12, s34), _mm256_unpackhi_epi64(s12, s34));
                    acc[iy] = _mm256_fmadd_ps(_mm256_mul_ps(d4, _mm256_set1_ps(q8.scale(iy, ibl))), _mm256_cvtepi32_ps(sumi), acc[iy]);
                    isum[0] = isum[1] = isum[2] = isum[3] = _mm256_setzero_si256();
                } else {
                    acc[iy] = _mm256_fmadd_ps(_mm256_mul_ps(d4, _mm256_set1_ps(q8.scale(iy, ibl))), _mm256_cvtepi32_ps(isum[iy]), acc[iy]);
                    isum[iy] = _mm256_setzero_si256();
                }
            }
        }
        for (int iy = 0; iy < nrc_y; ++iy) {
            auto sum = _mm_add_ps(_mm256_castps256_ps128(acc[iy]), _mm256_extractf128_ps(acc[iy], 1));
            info.store(ix, iy, _mm_mul_ps(_mm_set1_ps(0.125f), sum));
            acc[iy] = _mm256_setzero_ps();
        }
    }
}
template <int nrc_y>
static void mul_mat_iq3_xxs_r4_q8_k(int n, const void * vx, size_t bx, const DataInfo& info, int nrc_x) {
    GGML_ASSERT(nrc_x%4 == 0);
    Q8<nrc_y, block_q8_K> q8(info);
    int nbl = n / QK_K;
    auto smask = _mm256_set1_epi64x(0x8040201008040201);
    auto sign_shuffle = _mm256_set_epi64x(0x0303030303030303, 0x0202020202020202, 0x0101010101010101, 0x0000000000000000);
    auto m4 = _mm256_set1_epi8(4);
    __m256  acc[nrc_y] = {};
    __m256i isum[nrc_y] = {};
    __m256i qx[4];
    for (int ix = 0; ix < nrc_x; ix += 4) {
        auto iq3 = (const block_iq3_xxs_r4 *)((const char *)vx + (ix+0)*bx);
        for (int ibl = 0; ibl < nbl; ++ibl) { // Block of 256
            auto dl = _mm_mul_ps(_mm_set1_ps(0.25f), _mm_cvtph_ps(_mm_loadl_epi64((const __m128i *)iq3[ibl].d))); // TODO: absorb the 0.25 factor into d when quantizing/repacking
            auto d4 = _mm256_set_m128(dl, dl);
            for (int ib = 0; ib < QK_K/32; ++ib) {
                qx[0] = _mm256_i32gather_epi32((const int*)iq3xxs_grid, _mm256_cvtepu8_epi32(_mm_loadl_epi64((const __m128i*)(iq3[ibl].qs+32*ib+0))), 4);
                qx[1] = _mm256_i32gather_epi32((const int*)iq3xxs_grid, _mm256_cvtepu8_epi32(_mm_loadl_epi64((const __m128i*)(iq3[ibl].qs+32*ib+8))), 4);
                qx[2] = _mm256_i32gather_epi32((const int*)iq3xxs_grid, _mm256_cvtepu8_epi32(_mm_loadl_epi64((const __m128i*)(iq3[ibl].qs+32*ib+16))), 4);
                qx[3] = _mm256_i32gather_epi32((const int*)iq3xxs_grid, _mm256_cvtepu8_epi32(_mm_loadl_epi64((const __m128i*)(iq3[ibl].qs+32*ib+24))), 4);
                auto sas = _mm_loadu_si128((const __m128i *)iq3[ibl].sas + ib);
                auto scales = _mm_and_si128(sas, _mm_set1_epi8(1));
                scales = ggml_mm_dpbusd_epi32(_mm_set1_epi32(1), scales, _mm_set1_epi32(0x10080402));
                auto scales32 = MM256_SET1_M128I(scales);
                auto signs128 = _mm_and_si128(sas, _mm_set1_epi8(-2)); // 0xfe = -2 as signed. Needed to shutup compiler warning.
                signs128 = _mm_xor_si128(signs128, _mm_srli_epi16(signs128, 1));
                auto signs = MM256_SET1_M128I(signs128);
                auto shuffle = sign_shuffle;
                auto s1 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s2 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s3 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                shuffle = _mm256_add_epi8(shuffle, m4);
                auto s4 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(_mm256_shuffle_epi8(signs, shuffle), smask), smask), _mm256_set1_epi8(1));
                for (int iy = 0; iy < nrc_y; ++iy) {
                    auto y = _mm256_loadu_si256((const __m256i *)q8.y[iy][ibl].qs + ib);
                    auto sumi1 = ggml_mm256_dpbusd_epi32(_mm256_setzero_si256(), qx[0], _mm256_sign_epi8(y, s1));
                    auto sumi2 = ggml_mm256_dpbusd_epi32(_mm256_setzero_si256(), qx[1], _mm256_sign_epi8(y, s2));
                    auto sumi3 = ggml_mm256_dpbusd_epi32(_mm256_setzero_si256(), qx[2], _mm256_sign_epi8(y, s3));
                    auto sumi4 = ggml_mm256_dpbusd_epi32(_mm256_setzero_si256(), qx[3], _mm256_sign_epi8(y, s4));
                    auto s12 = _mm256_add_epi32(_mm256_unpacklo_epi32(sumi1, sumi2), _mm256_unpackhi_epi32(sumi1, sumi2)); // 0,1, 0,1, 0,1, 0,1
                    auto s34 = _mm256_add_epi32(_mm256_unpacklo_epi32(sumi3, sumi4), _mm256_unpackhi_epi32(sumi3, sumi4)); // 2,3, 2,3, 2,3, 2,3
                    auto sumi = _mm256_add_epi32(_mm256_unpacklo_epi64(s12, s34), _mm256_unpackhi_epi64(s12, s34)); // 0,1,2,3, 0,1,2,3
                    isum[iy] = _mm256_add_epi32(isum[iy], _mm256_mullo_epi32(scales32, sumi));
                }
            }
            for (int iy = 0; iy < nrc_y; ++iy) {
                acc[iy] = _mm256_fmadd_ps(_mm256_mul_ps(d4, _mm256_set1_ps(q8.scale(iy, ibl))), _mm256_cvtepi32_ps(isum[iy]), acc[iy]);
                isum[iy] = _mm256_setzero_si256();
            }
        }
        for (int iy = 0; iy < nrc_y; ++iy) {
            auto sum = _mm_add_ps(_mm256_castps256_ps128(acc[iy]), _mm256_extractf128_ps(acc[iy], 1));
            info.store(ix, iy, sum);
            acc[iy] = _mm256_setzero_ps();
        }
    }
}
template <int nrc_y>
static void mul_mat_iq3_s_r4_q8_k(int n, const void * vx, size_t bx, const DataInfo& info, int nrc_x) {
    GGML_ASSERT(nrc_x%4 == 0);
    Q8<nrc_y, block_q8_K> q8(info);
    int nbl = n / QK_K;
    auto smask = _mm256_set1_epi8(1);
    union { __m256i vec; uint32_t val[8]; } helper;
    union { __m128i vec; uint16_t val[8]; } hidx;
    __m256  acc[nrc_y] = {};
    __m256i isum[nrc_y] = {};
    __m256i qx[4];
    for (int ix = 0; ix < nrc_x; ix += 4) {
        auto iq3 = (const block_iq3_s_r4 *)((const char *)vx + (ix+0)*bx);
        for (int ibl = 0; ibl < nbl; ++ibl) { // Block of 256
            auto dl = _mm_cvtph_ps(_mm_loadl_epi64((const __m128i *)iq3[ibl].d));
            auto d4 = _mm256_set_m128(dl, dl);
            auto qs = iq3[ibl].qs;
            auto qh = iq3[ibl].qh;
            auto scale_bits = _mm_loadu_si128((const __m128i *)iq3[ibl].scales);
            auto scales8 = MM256_SET_M128I(_mm_srli_epi16(scale_bits, 4), scale_bits);
            helper.vec = _mm256_or_si256(_mm256_slli_epi16(_mm256_and_si256(scales8, _mm256_set1_epi8(0xf)), 1), _mm256_set1_epi8(1));
            for (int ib = 0; ib < QK_K/32; ++ib) {
                auto qh32 = (const uint32_t *)qh;
                auto idx_h = _mm_sllv_epi64(_mm_cvtepu8_epi16(_mm_set1_epi32(qh32[0])), _mm_set_epi64x(4, 8));
                for (int i = 0; i < 4; ++i) {
                    auto idx_l = _mm_cvtepu8_epi16(_mm_loadl_epi64((const __m128i *)(qs + 8*i)));
                    hidx.vec = _mm_or_si128(idx_l, _mm_and_si128(idx_h, _mm_set1_epi16(0x100))); idx_h = _mm_srli_epi16(idx_h, 1);
                    qx[i] = _mm256_i32gather_epi32((const int*)iq3s_grid, _mm256_cvtepu16_epi32(hidx.vec), 4);
                }
                qs += 32; qh += 4;
                auto signs128 = _mm_loadu_si128((const __m128i*)iq3[ibl].signs + ib);
                auto signs = MM256_SET_M128I(_mm_srli_epi16(signs128, 4), signs128);
                auto scales = _mm256_cvtepi8_epi32(_mm_set1_epi32(helper.val[ib]));
                auto s1 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(signs, smask), smask), smask); signs = _mm256_srli_epi16(signs, 1);
                auto s2 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(signs, smask), smask), smask); signs = _mm256_srli_epi16(signs, 1);
                auto s3 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(signs, smask), smask), smask); signs = _mm256_srli_epi16(signs, 1);
                auto s4 = _mm256_or_si256(_mm256_cmpeq_epi8(_mm256_and_si256(signs, smask), smask), smask);
                for (int iy = 0; iy < nrc_y; ++iy) {
                    auto y = _mm256_loadu_si256((const __m256i *)q8.y[iy][ibl].qs + ib);
                    auto sumi = _mm256_setzero_si256();
                    sumi = ggml_mm256_dpbusd_epi32(sumi, qx[0], _mm256_sign_epi8(_mm256_shuffle_epi32(y, 0x00), s1));
                    sumi = ggml_mm256_dpbusd_epi32(sumi, qx[1], _mm256_sign_epi8(_mm256_shuffle_epi32(y, 0x55), s2));
                    sumi = ggml_mm256_dpbusd_epi32(sumi, qx[2], _mm256_sign_epi8(_mm256_shuffle_epi32(y, 0xaa), s3));
                    sumi = ggml_mm256_dpbusd_epi32(sumi, qx[3], _mm256_sign_epi8(_mm256_shuffle_epi32(y, 0xff), s4));
                    isum[iy] = _mm256_add_epi32(isum[iy], _mm256_mullo_epi32(sumi, scales));
                }
            }
            for (int iy = 0; iy < nrc_y; ++iy) {
                acc[iy] = _mm256_fmadd_ps(_mm256_mul_ps(d4, _mm256_set1_ps(q8.scale(iy, ibl))), _mm256_cvtepi32_ps(isum[iy]), acc[iy]);
                isum[iy] = _mm256_setzero_si256();
            }
        }
        for (int iy = 0; iy < nrc_y; ++iy) {
            auto sum = _mm_add_ps(_mm256_castps256_ps128(acc[iy]), _mm256_extractf128_ps(acc[iy], 1));
            info.store(ix, iy, sum);
            acc[iy] = _mm256_setzero_ps();
        }
    }
}
}
extern "C" size_t r4_size(int type,int h,int rows) {switch(type){
case 16:return sizeof(block_iq2_xxs_r4)*(h/256)*(rows/4);
case 17:return sizeof(block_iq2_xs_r4)*(h/256)*(rows/4);
case 22:return sizeof(block_iq2_s_r4)*(h/256)*(rows/4);
case 18:return sizeof(block_iq3_xxs_r4)*(h/256)*(rows/4);
case 21:return sizeof(block_iq3_s_r4)*(h/256)*(rows/4);
default:std::abort();}}
extern "C" void r4_pack(int type,int h,int rows,const void* x,void* y){switch(type){
case 16:repack_iq2_xxs(rows,h,(const block_iq2_xxs*)x,(block_iq2_xxs_r4*)y,false);return;
case 17:repack_iq2_xs(rows,h,(const block_iq2_xs*)x,(block_iq2_xs_r4*)y,false);return;
case 22:repack_iq2_s(rows,h,(const block_iq2_s*)x,(block_iq2_s_r4*)y,false);return;
case 18:repack_iq3_xxs(rows,h,(const block_iq3_xxs*)x,(block_iq3_xxs_r4*)y,false);return;
case 21:repack_iq3_s(rows,h,(const block_iq3_s*)x,(block_iq3_s_r4*)y,false);return;
default:std::abort();}}
extern "C" void r4_dequant(int type,int h,int rows,const void* x,float* y){switch(type){
case 16:for(int r=0;r<rows;r+=4)dequantize_row_iq2_xxs_r4((const block_iq2_xxs_r4*)x+(r/4)*(h/256),y+r*h,4*h);return;
case 17:for(int r=0;r<rows;r+=4)dequantize_row_iq2_xs_r4((const block_iq2_xs_r4*)x+(r/4)*(h/256),y+r*h,4*h);return;
case 22:for(int r=0;r<rows;r+=4)dequantize_row_iq2_s_r4((const block_iq2_s_r4*)x+(r/4)*(h/256),y+r*h,4*h);return;
case 18:for(int r=0;r<rows;r+=4)dequantize_row_iq3_xxs_r4((const block_iq3_xxs_r4*)x+(r/4)*(h/256),y+r*h,4*h);return;
case 21:for(int r=0;r<rows;r+=4)dequantize_row_iq3_s_r4((const block_iq3_s_r4*)x+(r/4)*(h/256),y+r*h,4*h);return;
default:std::abort();}}

template<int V,int N>void r4_dot_n(int type,int h,int rows,const void* x,const void* const* a,float* out){
 DataInfo info{out,a,rows};const size_t bx=r4_size(type,h,4)/4;
#define R4_CALL(T,F) case T: if constexpr(V==0)old::F<N>(h,x,bx,info,rows);else if constexpr(V==1)vnni::F<N>(h,x,bx,info,rows);else gather::F<N>(h,x,bx,info,rows);return
 switch(type){
 R4_CALL(16,mul_mat_iq2_xxs_r4_q8_k);
 R4_CALL(17,mul_mat_iq2_xs_r4_q8_k);
 R4_CALL(22,mul_mat_iq2_s_r4_q8_k);
 R4_CALL(18,mul_mat_iq3_xxs_r4_q8_k);
 R4_CALL(21,mul_mat_iq3_s_r4_q8_k);
 default:std::abort();}
#undef R4_CALL
}
template<int V>void r4_dot_v(int type,int h,int rows,int nt,const void* x,const void* const* a,float* out){switch(nt){case 1:r4_dot_n<V,1>(type,h,rows,x,a,out);return;case 2:r4_dot_n<V,2>(type,h,rows,x,a,out);return;case 3:r4_dot_n<V,3>(type,h,rows,x,a,out);return;default:std::abort();}}
// 0 = pinned old AVX2, 1 = AVX-VNNI, 2 = AVX-VNNI + gathered codebook decode.
extern "C" void r4_dot_variant(int v,int type,int h,int rows,int nt,const void* x,const void* const* a,float* out){switch(v){case 0:r4_dot_v<0>(type,h,rows,nt,x,a,out);return;case 1:r4_dot_v<1>(type,h,rows,nt,x,a,out);return;case 2:r4_dot_v<2>(type,h,rows,nt,x,a,out);return;default:std::abort();}}
extern "C" void r4_dot(int type,int h,int rows,int nt,const void* x,const void* const* a,float* out){r4_dot_variant(0,type,h,rows,nt,x,a,out);}
#include "inverse.inc"
#include "conversion_fast.inc"
