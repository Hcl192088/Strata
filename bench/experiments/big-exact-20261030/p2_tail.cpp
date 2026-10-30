#include <array>
#include <map>
#include <vector>
namespace strata::kernels::cpu { namespace {
std::vector<std::array<int16_t,4>> patterns;
uint16_t pattern_id[2][256][16];
std::vector<int16_t> coeff[4],lut;
void make_patterns(){
 std::map<std::array<int16_t,4>,int> ids;
 for(int half=0;half<2;half++)for(int q=0;q<256;q++)for(int sg=0;sg<16;sg++){
  std::array<int16_t,4> p;for(int k=0;k<4;k++)p[k]=int16_t((iq2xxs_grid[q]>>(8*(4*half+k)))&255)*(sg&(1<<k)?-1:1);
  auto it=ids.find(p);int id;
  if(it==ids.end()){id=int(patterns.size());patterns.push_back(p);ids[p]=id;}else id=it->second;
  pattern_id[half][q][sg]=(uint16_t)id;
 }
 if(patterns.size()!=1184)std::abort();
 for(int k=0;k<4;k++){coeff[k].resize(patterns.size());for(size_t i=0;i<patterns.size();i++)coeff[k][i]=patterns[i][k];}
}
template<int NT>void lut_gu(const uint8_t* w,size_t stride,size_t up,float*const* ff){
 const int P=(int)patterns.size();
 for(int row=0;row<640;row++){
  float g[NT],u[NT];
  for(int mat=0;mat<2;mat++){
   const auto* wr=w+row*stride+(mat?up:0);__m256 acc[NT];for(int t=0;t<NT;t++)acc[t]=_mm256_setzero_ps();
   for(int b=0;b<10;b++){
    const auto* block=wr+66*b;__m256i sums[NT];for(int t=0;t<NT;t++)sums[t]=_mm256_setzero_si256();
    for(int j=0;j<8;j++){
     const auto* q=block+2+8*j;uint32_t sas=u32(q+4);int idx[8];
     for(int z=0;z<4;z++){
      unsigned si=(sas>>(7*z))&127;unsigned sign=si|((__popcnt(si)&1)<<7);
      idx[2*z]=pattern_id[0][q[z]][sign&15];idx[2*z+1]=pattern_id[1][q[z]][sign>>4];
     }
     const auto scales=_mm256_set1_epi32(2*int(sas>>28)+1);
     for(int t=0;t<NT;t++){
      const int16_t* a=lut.data()+(t*640+b*64+j*8)*P;
      auto v=_mm256_setr_epi32(a[idx[0]],a[P+idx[1]],a[2*P+idx[2]],a[3*P+idx[3]],a[4*P+idx[4]],a[5*P+idx[5]],a[6*P+idx[6]],a[7*P+idx[7]]);
      sums[t]=_mm256_add_epi32(sums[t],_mm256_mullo_epi32(v,scales));
     }
    }
    const float dx=h2f(u16(block))*0.125f;
    // Scales filled by p2_prepare from exactly the original activation block.
    extern float lut_scales[3][10];
    for(int t=0;t<NT;t++)acc[t]=_mm256_fmadd_ps(_mm256_set1_ps(dx*lut_scales[t][b]),_mm256_cvtepi32_ps(sums[t]),acc[t]);
   }
   for(int t=0;t<NT;t++)(mat?u:g)[t]=hsum8(acc[t]);
  }
  for(int t=0;t<NT;t++)ff[t][row]=(g[t]/(1.f+std::exp(-g[t])))*u[t];
 }
}
float lut_scales[3][10];
} // anonymous
extern "C" void p2_init(){make_patterns();}
extern "C" void p2_prepare(int nt,const void*const* acts){
 const int P=(int)patterns.size();lut.resize(size_t(nt)*640*P);
 for(int t=0;t<nt;t++){
  const auto* y=(const block_q8_K*)acts[t];
  for(int b=0;b<10;b++){
   lut_scales[t][b]=y[b].d;
   for(int pos=0;pos<64;pos++){
    const int8_t* a=y[b].qs+4*pos;int16_t* dst=lut.data()+(t*640+b*64+pos)*P;
    for(int i=0;i<P;i+=16){
     auto sum=_mm256_setzero_si256();
     for(int k=0;k<4;k++){
      auto c=_mm256_loadu_si256((const __m256i*)(coeff[k].data()+i));
      auto term=_mm256_mullo_epi16(c,_mm256_set1_epi16(a[k]));
      if(a[k]==-128){auto negative=_mm256_and_si256(c,_mm256_cmpgt_epi16(_mm256_setzero_si256(),c));term=_mm256_add_epi16(term,_mm256_slli_epi16(negative,8));}
      sum=_mm256_add_epi16(sum,term);
     }
     _mm256_storeu_si256((__m256i*)(dst+i),sum);
    }
   }
  }
 }
}
extern "C" void p2_gu(int nt,const uint8_t*w,size_t stride,size_t up,float*const* ff){
 if(nt==2)lut_gu<2>(w,stride,up,ff);else if(nt==3)lut_gu<3>(w,stride,up,ff);else std::abort();
}
} // cpu
