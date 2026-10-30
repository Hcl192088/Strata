// Same pinned R4 layout; explicit conversion candidate, never a fallback.
// Include after r4.cpp's shared block definitions. Requires only AVX2/F16C baseline ISA.
// All five actual GU types are implemented here independently of r4_pack/r4_unpack.
namespace conversion_fast {
static inline uint32_t load32(const void* p){uint32_t v;std::memcpy(&v,p,4);return v;}
static inline void store32(void* p,uint32_t v){std::memcpy(p,&v,4);}
static inline uint8_t prefix7(uint8_t s){s^=s<<1;s^=s<<2;s^=s<<4;return s&127;}
static inline uint8_t unprefix7(uint8_t s){return (s^(s<<1))&127;}
// Four independent32-bit sign/scale words, one original row in each lane.
static inline __m128i sas_pack(__m128i z){
 auto q=_mm_or_si128(_mm_and_si128(z,_mm_set1_epi32(0x0000007f)),_mm_slli_epi32(_mm_and_si128(z,_mm_set1_epi32(0x00003f80)),1));
 q=_mm_or_si128(q,_mm_slli_epi32(_mm_and_si128(z,_mm_set1_epi32(0x001fc000)),2));
 q=_mm_or_si128(q,_mm_slli_epi32(_mm_and_si128(z,_mm_set1_epi32(0x0fe00000)),3));
 q=_mm_xor_si128(q,_mm_and_si128(_mm_slli_epi32(q,1),_mm_set1_epi32((int)0xfefefefe)));
 q=_mm_xor_si128(q,_mm_and_si128(_mm_slli_epi32(q,2),_mm_set1_epi32((int)0xfcfcfcfc)));
 q=_mm_xor_si128(q,_mm_and_si128(_mm_slli_epi32(q,4),_mm_set1_epi32((int)0xf0f0f0f0)));
 q=_mm_slli_epi32(_mm_and_si128(q,_mm_set1_epi32(0x7f7f7f7f)),1);
 auto scales=_mm_and_si128(_mm_srli_epi32(z,28),_mm_set1_epi32(1));
 scales=_mm_or_si128(scales,_mm_and_si128(_mm_srli_epi32(z,21),_mm_set1_epi32(0x100)));
 scales=_mm_or_si128(scales,_mm_and_si128(_mm_srli_epi32(z,14),_mm_set1_epi32(0x10000)));
 scales=_mm_or_si128(scales,_mm_and_si128(_mm_srli_epi32(z,7),_mm_set1_epi32(0x1000000)));
 return _mm_or_si128(q,scales);
}
static inline __m128i sas_unpack(__m128i z){
 auto q=_mm_and_si128(_mm_srli_epi32(z,1),_mm_set1_epi32(0x7f7f7f7f));
 q=_mm_and_si128(_mm_xor_si128(q,_mm_slli_epi32(q,1)),_mm_set1_epi32(0x7f7f7f7f));
 auto s=_mm_or_si128(_mm_and_si128(q,_mm_set1_epi32(0x7f)),_mm_and_si128(_mm_srli_epi32(q,1),_mm_set1_epi32(0x3f80)));
 s=_mm_or_si128(s,_mm_and_si128(_mm_srli_epi32(q,2),_mm_set1_epi32(0x1fc000)));
 s=_mm_or_si128(s,_mm_and_si128(_mm_srli_epi32(q,3),_mm_set1_epi32(0xfe00000)));
 s=_mm_or_si128(s,_mm_slli_epi32(_mm_and_si128(z,_mm_set1_epi32(1)),28));
 s=_mm_or_si128(s,_mm_slli_epi32(_mm_and_si128(z,_mm_set1_epi32(0x100)),21));
 s=_mm_or_si128(s,_mm_slli_epi32(_mm_and_si128(z,_mm_set1_epi32(0x10000)),14));
 return _mm_or_si128(s,_mm_slli_epi32(_mm_and_si128(z,_mm_set1_epi32(0x1000000)),7));
}
// Bit-address permutation j -> rotl5(j,3), applied in parallel to four words.
// Each delta swap exchanges address bits p/q:1,3,6,12 are (2^q-2^p).
template<int D,uint32_t Mask>static inline __m128i swap_bits(__m128i v){auto t=_mm_and_si128(_mm_xor_si128(v,_mm_srli_epi32(v,D)),_mm_set1_epi32((int)Mask));return _mm_xor_si128(v,_mm_xor_si128(t,_mm_slli_epi32(t,D)));}
static inline __m128i iq3s_sign_pack(__m128i v){
 v=swap_bits<1,0x22222222>(v);v=swap_bits<3,0x0a0a0a0a>(v);
 v=swap_bits<6,0x00cc00cc>(v);return swap_bits<12,0x0000f0f0>(v);
}
static inline __m128i iq3s_sign_unpack(__m128i v){
 v=swap_bits<12,0x0000f0f0>(v);v=swap_bits<6,0x00cc00cc>(v);
 v=swap_bits<3,0x0a0a0a0a>(v);return swap_bits<1,0x22222222>(v);
}
static inline __m128i lanes32(const void* a,const void* b,const void* c,const void* d){return _mm_set_epi32((int)load32(d),(int)load32(c),(int)load32(b),(int)load32(a));}
static inline void scatter32(__m128i v,void* a,void* b,void* c,void* d){uint32_t w[4];_mm_storeu_si128((__m128i*)w,v);store32(a,w[0]);store32(b,w[1]);store32(c,w[2]);store32(d,w[3]);}
}
extern "C" int r4_conversion_fast_supported(int type){return type==16||type==17||type==18||type==21||type==22;}
extern "C" void r4_pack_fast(int type,int h,int rows,const void* src,void* dst){
 using namespace conversion_fast;GGML_ASSERT(rows%4==0&&h%256==0);const int nb=h/256;
 for(int r=0;r<rows;r+=4)for(int b=0;b<nb;b++){
  const int oi=r*nb+b,pi=(r/4)*nb+b;
  if(type==16){
   auto* x=(const block_iq2_xxs*)src;auto& p=((block_iq2_xxs_r4*)dst)[pi];const block_iq2_xxs* a[4]={x+oi,x+oi+nb,x+oi+2*nb,x+oi+3*nb};
   for(int k=0;k<4;k++)p.d[k]=a[k]->d;
   for(int j=0;j<8;j++){
    _mm_storeu_si128((__m128i*)(p.qs+16*j),lanes32(a[0]->qs+4*j,a[1]->qs+4*j,a[2]->qs+4*j,a[3]->qs+4*j));
    auto z=lanes32(a[0]->qs+4*j+2,a[1]->qs+4*j+2,a[2]->qs+4*j+2,a[3]->qs+4*j+2);
    _mm_storeu_si128((__m128i*)(p.sas+16*j),sas_pack(z));
   }
  }else if(type==18){
   auto* x=(const block_iq3_xxs*)src;auto& p=((block_iq3_xxs_r4*)dst)[pi];const block_iq3_xxs* a[4]={x+oi,x+oi+nb,x+oi+2*nb,x+oi+3*nb};
   for(int k=0;k<4;k++)p.d[k]=a[k]->d;
   for(int j=0;j<8;j++){
    for(int k=0;k<4;k++)std::memcpy(p.qs+32*j+8*k,a[k]->qs+8*j,8);
    auto z=lanes32(a[0]->qs+64+4*j,a[1]->qs+64+4*j,a[2]->qs+64+4*j,a[3]->qs+64+4*j);
    _mm_storeu_si128((__m128i*)(p.sas+16*j),sas_pack(z));
   }
  }else if(type==17){
   auto* x=(const block_iq2_xs*)src;auto& p=((block_iq2_xs_r4*)dst)[pi];
   for(int k=0;k<4;k++){const auto& a=x[oi+k*nb];p.d[k]=a.d;for(int j=0;j<8;j++){p.scales[4*j+k]=a.scales[j];for(int i=0;i<4;i++){auto v=a.qs[4*j+i];p.qs[16*j+4*k+i]=(v&511)|((uint16_t)prefix7(v>>9)<<9);}}}
  }else if(type==22){
   auto* x=(const block_iq2_s*)src;auto& p=((block_iq2_s_r4*)dst)[pi];
   for(int k=0;k<4;k++){const auto& a=x[oi+k*nb];p.d[k]=a.d;for(int j=0;j<8;j++){p.scales[4*j+k]=a.scales[j];p.qh[4*j+k]=a.qh[j];std::memcpy(p.qs+16*j+4*k,a.qs+4*j,4);std::memcpy(p.signs+16*j+4*k,a.qs+32+4*j,4);}}
  }else if(type==21){
   auto* x=(const block_iq3_s*)src;auto& p=((block_iq3_s_r4*)dst)[pi];const block_iq3_s* a[4]={x+oi,x+oi+nb,x+oi+2*nb,x+oi+3*nb};
   for(int k=0;k<4;k++){p.d[k]=a[k]->d;for(int j=0;j<2;j++){p.scales[8*j+k]=(a[k]->scales[j]&15)|((a[k]->scales[j+2]&15)<<4);p.scales[8*j+k+4]=(a[k]->scales[j]>>4)|(a[k]->scales[j+2]&0xf0);}}
   for(int j=0;j<8;j++){
    for(int k=0;k<4;k++)p.qh[4*j+k]=a[k]->qh[j];
    auto x0=_mm_loadl_epi64((const __m128i*)(a[0]->qs+8*j));auto x1=_mm_loadl_epi64((const __m128i*)(a[1]->qs+8*j));
    auto x2=_mm_loadl_epi64((const __m128i*)(a[2]->qs+8*j));auto x3=_mm_loadl_epi64((const __m128i*)(a[3]->qs+8*j));
    auto l=_mm_unpacklo_epi8(x0,x1),u=_mm_unpacklo_epi8(x2,x3);
    auto c0=_mm_unpacklo_epi16(l,u),c1=_mm_unpackhi_epi16(l,u);
    _mm_storeu_si128((__m128i*)(p.qs+32*j),_mm_unpacklo_epi32(c0,c1));
    _mm_storeu_si128((__m128i*)(p.qs+32*j+16),_mm_unpackhi_epi32(c0,c1));
    auto s=lanes32(a[0]->signs+4*j,a[1]->signs+4*j,a[2]->signs+4*j,a[3]->signs+4*j);
    _mm_storeu_si128((__m128i*)(p.signs+16*j),iq3s_sign_pack(s));
   }
  }else std::abort();
 }
}
extern "C" void r4_unpack_fast(int type,int h,int rows,const void* src,void* dst){
 using namespace conversion_fast;GGML_ASSERT(rows%4==0&&h%256==0);const int nb=h/256;
 for(int r=0;r<rows;r+=4)for(int b=0;b<nb;b++){
  const int oi=r*nb+b,pi=(r/4)*nb+b;
  if(type==16){
   const auto& p=((const block_iq2_xxs_r4*)src)[pi];auto* y=(block_iq2_xxs*)dst;block_iq2_xxs* a[4]={y+oi,y+oi+nb,y+oi+2*nb,y+oi+3*nb};
   for(int k=0;k<4;k++)a[k]->d=p.d[k];
   for(int j=0;j<8;j++){
    scatter32(_mm_loadu_si128((const __m128i*)(p.qs+16*j)),a[0]->qs+4*j,a[1]->qs+4*j,a[2]->qs+4*j,a[3]->qs+4*j);
    auto s=sas_unpack(_mm_loadu_si128((const __m128i*)(p.sas+16*j)));
    scatter32(s,a[0]->qs+4*j+2,a[1]->qs+4*j+2,a[2]->qs+4*j+2,a[3]->qs+4*j+2);
   }
  }else if(type==18){
   const auto& p=((const block_iq3_xxs_r4*)src)[pi];auto* y=(block_iq3_xxs*)dst;block_iq3_xxs* a[4]={y+oi,y+oi+nb,y+oi+2*nb,y+oi+3*nb};
   for(int k=0;k<4;k++)a[k]->d=p.d[k];
   for(int j=0;j<8;j++){
    for(int k=0;k<4;k++)std::memcpy(a[k]->qs+8*j,p.qs+32*j+8*k,8);
    auto s=sas_unpack(_mm_loadu_si128((const __m128i*)(p.sas+16*j)));
    scatter32(s,a[0]->qs+64+4*j,a[1]->qs+64+4*j,a[2]->qs+64+4*j,a[3]->qs+64+4*j);
   }
  }else if(type==17){
   const auto& p=((const block_iq2_xs_r4*)src)[pi];auto* y=(block_iq2_xs*)dst;
   for(int k=0;k<4;k++){auto& a=y[oi+k*nb];a.d=p.d[k];for(int j=0;j<8;j++){a.scales[j]=p.scales[4*j+k];for(int i=0;i<4;i++){auto v=p.qs[16*j+4*k+i];a.qs[4*j+i]=(v&511)|((uint16_t)unprefix7(v>>9)<<9);}}}
  }else if(type==22){
   const auto& p=((const block_iq2_s_r4*)src)[pi];auto* y=(block_iq2_s*)dst;
   for(int k=0;k<4;k++){auto& a=y[oi+k*nb];a.d=p.d[k];for(int j=0;j<8;j++){a.scales[j]=p.scales[4*j+k];a.qh[j]=p.qh[4*j+k];std::memcpy(a.qs+4*j,p.qs+16*j+4*k,4);std::memcpy(a.qs+32+4*j,p.signs+16*j+4*k,4);}}
  }else if(type==21){
   const auto& p=((const block_iq3_s_r4*)src)[pi];auto* y=(block_iq3_s*)dst;block_iq3_s* a[4]={y+oi,y+oi+nb,y+oi+2*nb,y+oi+3*nb};
   for(int k=0;k<4;k++){a[k]->d=p.d[k];for(int j=0;j<2;j++){a[k]->scales[j]=(p.scales[8*j+k]&15)|((p.scales[8*j+k+4]&15)<<4);a[k]->scales[j+2]=(p.scales[8*j+k]>>4)|(p.scales[8*j+k+4]&0xf0);}}
   for(int j=0;j<8;j++){
    auto l=_mm_loadu_si128((const __m128i*)(p.qs+32*j)),u=_mm_loadu_si128((const __m128i*)(p.qs+32*j+16));
    auto c0=_mm_castps_si128(_mm_shuffle_ps(_mm_castsi128_ps(l),_mm_castsi128_ps(u),_MM_SHUFFLE(2,0,2,0)));
    auto c1=_mm_castps_si128(_mm_shuffle_ps(_mm_castsi128_ps(l),_mm_castsi128_ps(u),_MM_SHUFFLE(3,1,3,1)));
    for(int k=0;k<4;k++){
     a[k]->qh[j]=p.qh[4*j+k];
     auto mask=_mm_set_epi32(-1,-1,-1,(int)((k+12)<<24|(k+8)<<16|(k+4)<<8|k));
     auto row=_mm_unpacklo_epi32(_mm_shuffle_epi8(c0,mask),_mm_shuffle_epi8(c1,mask));
     _mm_storel_epi64((__m128i*)(a[k]->qs+8*j),row);
    }
    auto s=iq3s_sign_unpack(_mm_loadu_si128((const __m128i*)(p.signs+16*j)));
    scatter32(s,a[0]->signs+4*j,a[1]->signs+4*j,a[2]->signs+4*j,a[3]->signs+4*j);
   }
  }else std::abort();
 }
}
