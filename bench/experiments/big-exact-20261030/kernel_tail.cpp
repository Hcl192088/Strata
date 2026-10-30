// New original-layout row-group kernel. Reuses the pinned source's exact decoders/hsum.
template<int TY,int NT,int NR>
void grouped_rows(const uint8_t* w,size_t stride,int n,const void* const* a,float* out) {
 const block_q8_K* y[NT];for(int t=0;t<NT;t++)y[t]=(const block_q8_K*)a[t];
 for(int r=0;r<640;r+=NR){
  __m256 acc[NR][NT];for(int q=0;q<NR;q++)for(int t=0;t<NT;t++)acc[q][t]=_mm256_setzero_ps();
  for(int b=0;b<n/256;b++){
   __m256i sum[NR][NT];for(int q=0;q<NR;q++)for(int t=0;t<NT;t++)sum[q][t]=_mm256_setzero_si256();
   for(int j=0;j<4;j++)for(int half=0;half<2;half++){
    __m256i av[NT];for(int t=0;t<NT;t++)av[t]=_mm256_loadu_si256((const __m256i*)(y[t][b].qs+64*j+32*half));
    for(int q=0;q<NR;q++){
     const auto* blk=w+(r+q)*stride+b*Fmt32<TY>::bytes;__m256i g,sgn,sc;Fmt32<TY>::decode(blk,j,half,g,sgn,sc);
     for(int t=0;t<NT;t++)sum[q][t]=_mm256_dpwssd_avx_epi32(sum[q][t],_mm256_maddubs_epi16(g,_mm256_sign_epi8(av[t],sgn)),sc);
    }
   }
   for(int q=0;q<NR;q++){
    const auto* blk=w+(r+q)*stride+b*Fmt32<TY>::bytes;const float dx=h2f(u16(blk))*Fmt32<TY>::K;
    for(int t=0;t<NT;t++)acc[q][t]=_mm256_fmadd_ps(_mm256_set1_ps(dx*y[t][b].d),_mm256_cvtepi32_ps(sum[q][t]),acc[q][t]);
   }
  }
  for(int q=0;q<NR;q++)for(int t=0;t<NT;t++)out[t*640+r+q]=hsum8(acc[q][t]);
 }
}
template<int NT,int NR>void grouped(bool gather,const uint8_t*w,size_t s,int n,const void*const*a,float*out){
 if(gather)grouped_rows<121,NT,NR>(w,s,n,a,out);else grouped_rows<21,NT,NR>(w,s,n,a,out);
}
} // original anonymous namespace
extern "C" void p1_dot(int nr,int nt,bool gather,const uint8_t*w,size_t s,int n,const void*const*a,float*out){
 switch(nt){
#define CASE(N) case N: if(nr==2)grouped<N,2>(gather,w,s,n,a,out);else if(nr==4)grouped<N,4>(gather,w,s,n,a,out);else std::abort();return
 CASE(1);CASE(2);CASE(3);
#undef CASE
 default:std::abort();}
}
} // strata::kernels::cpu
