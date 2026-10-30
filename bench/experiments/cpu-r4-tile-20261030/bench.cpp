#define NOMINMAX
#include "strata/kernels/cpu/native_expert.hpp"
#include "strata/kernels/cpu/iq_avx2.hpp"
#include "strata/kernels/cpu/expert_layout.hpp"
#include "ggml.h"
#include "ggml-cpu.h"
#include "ggml-quants.h"
#include <windows.h>
#include <malloc.h>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <random>
#include <sstream>
#include <string>
#include <vector>
namespace cpu=strata::kernels::cpu;
extern "C" size_t r4_size(int,int,int);
extern "C" void r4_pack(int,int,int,const void*,void*);
extern "C" void r4_unpack(int,int,int,const void*,void*);
extern "C" void r4_pack_fast(int,int,int,const void*,void*);
extern "C" void r4_unpack_fast(int,int,int,const void*,void*);
extern "C" void r4_dequant(int,int,int,const void*,float*);
extern "C" void r4_dot_variant(int,int,int,int,int,const void*,const void* const*,float*);
extern "C" void r4_dot_range(int,int,int,int,int,const void*,const void* const*,float*,int,int);
static void need(bool b,const char* s){if(!b){std::fprintf(stderr,"FAIL,%s\n",s);std::exit(3);}}
static double now(){static LARGE_INTEGER f{};if(!f.QuadPart)QueryPerformanceFrequency(&f);LARGE_INTEGER t;QueryPerformanceCounter(&t);return 1e6*double(t.QuadPart)/f.QuadPart;}
static double med(std::vector<double> a){std::sort(a.begin(),a.end());return a[a.size()/2];}
struct Layer{int layer,gu,down;uint64_t offset,bytes;};
struct Item{unsigned char* native;unsigned char* packed;cpu::NativeFmt fmt;int layer,expert;};
static constexpr int H=2560,FF=640;
static void original_dequant(int type,const void* p,float* out,int n){
 switch(type){case 16:dequantize_row_iq2_xxs((const block_iq2_xxs*)p,out,n);return;case 17:dequantize_row_iq2_xs((const block_iq2_xs*)p,out,n);return;case 22:dequantize_row_iq2_s((const block_iq2_s*)p,out,n);return;case 18:dequantize_row_iq3_xxs((const block_iq3_xxs*)p,out,n);return;case 21:dequantize_row_iq3_s((const block_iq3_s*)p,out,n);return;default:std::abort();}
}
static void mechanical(int gt,int lp,const std::vector<Item>& items){
 const size_t mat=items[0].fmt.up_off;std::vector<unsigned char> tmp(mat),inverse(2*mat);std::vector<float> a(size_t(H)*FF),b(size_t(H)*FF);size_t checked=0,values=0;
 for(const auto& it:items)for(int m=0;m<2;m++){
  const auto* orig=it.native+m*it.fmt.up_off;const auto* packed=it.packed+m*it.fmt.up_off;
  r4_pack_fast(gt,H,FF,orig,tmp.data());need(!std::memcmp(tmp.data(),packed,mat),"old_fast_pack_bytes");
  r4_unpack(gt,H,FF,packed,inverse.data());r4_unpack_fast(gt,H,FF,packed,inverse.data()+mat);
  need(!std::memcmp(inverse.data(),inverse.data()+mat,mat)&&!std::memcmp(orig,inverse.data(),mat),"old_fast_unpack_roundtrip");
  r4_unpack_fast(gt,H,FF,tmp.data(),inverse.data());need(!std::memcmp(orig,inverse.data(),mat),"fast_full_roundtrip");checked+=mat;
  for(int row=0;row<FF;row++)original_dequant(gt,orig+row*it.fmt.gu_row,a.data()+size_t(row)*H,H);
  r4_dequant(gt,H,FF,tmp.data(),b.data());for(size_t k=0;k<a.size();k++)need(a[k]==b[k],"decoded_weights");values+=a.size();
 }
 std::printf("PARITY,%d,%d,%zu,%zu,0,0\n",gt,lp,checked,values);
}
static void conversion(int gt,int lp,const std::vector<Item>& items){
 std::vector<unsigned char> inverse(items[0].fmt.down_off);
 for(int op=0;op<2;op++){
  auto pass=[&](int fast){for(const auto& it:items){
   if(op==0){
    if(fast){r4_pack_fast(gt,H,FF,it.native,it.packed);r4_pack_fast(gt,H,FF,it.native+it.fmt.up_off,it.packed+it.fmt.up_off);}
    else{r4_pack(gt,H,FF,it.native,it.packed);r4_pack(gt,H,FF,it.native+it.fmt.up_off,it.packed+it.fmt.up_off);}
   }else{
    if(fast){r4_unpack_fast(gt,H,FF,it.packed,inverse.data());r4_unpack_fast(gt,H,FF,it.packed+it.fmt.up_off,inverse.data()+it.fmt.up_off);}
    else{r4_unpack(gt,H,FF,it.packed,inverse.data());r4_unpack(gt,H,FF,it.packed+it.fmt.up_off,inverse.data()+it.fmt.up_off);}
   }
  }};
  pass(0);pass(1);std::vector<double> times[2];
  for(int r=0;r<5;r++)for(int k=0;k<2;k++){const int fast=r%2?1-k:k;double t=now();pass(fast);double dt=(now()-t)/items.size();times[fast].push_back(dt);std::printf("CONV_RAW,%d,%d,%d,%d,%d,%.6f\n",gt,lp,op,r,fast,dt);}
  std::printf("CONV_SUM,%d,%d,%d,%.6f,%.6f,%.9f\n",gt,lp,op,med(times[0]),med(times[1]),med(times[0])/med(times[1]));
 }
}
static void tile(int gt,int lp,const std::vector<Item>& items){
 std::mt19937 gen(12345);std::normal_distribution<float> nd(0,1);std::vector<float> x(3*H);for(auto& v:x)v=nd(gen);
 std::vector<unsigned char> acts(3*cpu::kNativeActBytes),hq(3*cpu::kNativeHBytes);const void* ap[3];const void* hp[3];float* fp[3];float* op[3];std::vector<float> h(3*FF),out(3*H),g(3*FF),u(3*FF);
 for(int t=0;t<3;t++){ap[t]=acts.data()+t*cpu::kNativeActBytes;hp[t]=hq.data()+t*cpu::kNativeHBytes;fp[t]=h.data()+t*FF;op[t]=out.data()+t*H;cpu::native_quant_act(items[0].fmt,x.data()+t*H,(void*)ap[t]);}
 cpu::ActQ qa[3];const cpu::ActQ* qap[3]={&qa[0],&qa[1],&qa[2]};
 auto rdots=[&](int variant,const Item& it,int nt,int parts,bool swiglu){
  for(int p=0;p<parts;p++){int r0=(FF/4)*p/parts*4,r1=(FF/4)*(p+1)/parts*4;
   r4_dot_range(variant,gt,H,FF,nt,it.packed,ap,g.data(),r0,r1);
   r4_dot_range(variant,gt,H,FF,nt,it.packed+it.fmt.up_off,ap,u.data(),r0,r1);
   if(swiglu)for(int t=0;t<nt;t++)for(int r=r0;r<r1;r++){int k=t*FF+r;h[k]=(g[k]/(1.f+std::exp(-g[k])))*u[k];}
  }
 };
 auto run=[&](int arm,const Item& it,int nt,int parts,bool full){
  if(!arm){for(int p=0;p<parts;p++)cpu::native_gu_rows(it.fmt,it.native,ap,nt,fp,FF*p/parts,FF*(p+1)/parts);}
  else rdots(arm,it,nt,parts,true);
  if(full){
   const auto* blob=arm?it.packed:it.native;
   if(cpu::q2_native_kernels(it.fmt.d_type)){for(int t=0;t<nt;t++)cpu::act_quant_any(fp[t],FF,qa[t]);cpu::q2_rows_any(blob+it.fmt.down_off,it.fmt.d_row,FF/64,qap,nt,op,0,H);}
   else{for(int t=0;t<nt;t++)cpu::native_quant_h(it.fmt,fp[t],(void*)hp[t]);cpu::native_down_rows(it.fmt,blob,hp,nt,op,0,H);}
  }
 };
 for(int parts:{30,4}){
  for(int p=0;p<parts;p++)std::printf("BOUND,%d,%d,%d,%d,%d,%d,%d,%d\n",gt,lp,parts,p,FF*p/parts,FF*(p+1)/parts,(FF/4)*p/parts*4,(FF/4)*(p+1)/parts*4);
  for(int nt=1;nt<=3;nt++){
   // Compare every partitioned dot output to its full-row counterpart, including the old variant.
   for(const auto& it:items)for(int v=0;v<=2;v++){
    std::vector<float> rg(nt*FF),ru(nt*FF);r4_dot_variant(v,gt,H,FF,nt,it.packed,ap,rg.data());r4_dot_variant(v,gt,H,FF,nt,it.packed+it.fmt.up_off,ap,ru.data());
    rdots(v,it,nt,parts,false);need(!std::memcmp(rg.data(),g.data(),nt*FF*4)&&!std::memcmp(ru.data(),u.data(),nt*FF*4),"range_vs_full_R4_bits");
   }
   // Check the nonzero starting-row/output-stride contract and writes outside each range.
   const float canary=1234567.25f;const auto& first=items[0];
   for(int v=0;v<=2;v++)for(int p=0;p<parts;p++){
    std::fill(g.begin(),g.end(),canary);int r0=(FF/4)*p/parts*4,r1=(FF/4)*(p+1)/parts*4;
    r4_dot_range(v,gt,H,FF,nt,first.packed,ap,g.data(),r0,r1);
    for(int t=0;t<3;t++)for(int r=0;r<FF;r++)if(t>=nt||r<r0||r>=r1)need(g[t*FF+r]==canary,"range_outside_canary");
   }
   std::printf("TILE_BITS,%d,%d,%d,%d,0\n",gt,lp,nt,parts);
   for(int arm=1;arm<=2;arm++){
    double maxH=0,diffH=0,maxO=0,diffO=0;size_t bitsH=0,bitsO=0;
    for(const auto& it:items){run(0,it,nt,parts,true);std::vector<float> rh(h.begin(),h.begin()+nt*FF),ro(out.begin(),out.begin()+nt*H);run(arm,it,nt,parts,true);
     for(int k=0;k<nt*FF;k++){need(std::isfinite(h[k])&&std::isfinite(rh[k]),"finite_h");maxH=std::max(maxH,std::fabs(double(rh[k])));diffH=std::max(diffH,std::fabs(double(rh[k])-h[k]));if(std::memcmp(&rh[k],&h[k],4))bitsH++;}
     for(int k=0;k<nt*H;k++){need(std::isfinite(out[k])&&std::isfinite(ro[k]),"finite_out");maxO=std::max(maxO,std::fabs(double(ro[k])));diffO=std::max(diffO,std::fabs(double(ro[k])-out[k]));if(std::memcmp(&ro[k],&out[k],4))bitsO++;}
    }
    std::printf("TILE_NUMERIC,%d,%d,%d,%d,%d,%.9g,%.9g,%zu,%.9g,%.9g,%zu\n",gt,lp,nt,parts,arm,maxH,diffH,bitsH,maxO,diffO,bitsO);need(diffH<=1e-4*std::max(1.,maxH),"h_numeric_screen");
   }
   std::vector<double> times[3];for(int arm=0;arm<=2;arm++)for(const auto& it:items)run(arm,it,nt,parts,true);
   for(int r=0;r<3;r++)for(int k=0;k<3;k++){int arm=(r+k)%3;double t=now();for(const auto& it:items)run(arm,it,nt,parts,true);double dt=(now()-t)/items.size();times[arm].push_back(dt);std::printf("TILE_RAW,%d,%d,%d,%d,%d,%d,%.6f\n",gt,lp,nt,parts,r,arm,dt);}
   for(int arm=1;arm<=2;arm++)std::printf("TILE_SUM,%d,%d,%d,%d,%d,%.6f,%.6f,%.9f\n",gt,lp,nt,parts,arm,med(times[0]),med(times[arm]),med(times[0])/med(times[arm]));
  }
 }
}
int main(int argc,char** argv){
 setvbuf(stdout,nullptr,_IONBF,0);need(argc==6,"args_mode_lp_type_experts_metadata");const std::string mode=argv[1];need(mode=="tile"||mode=="convert","explicit_mode");const int lp=std::atoi(argv[2]),gt=std::atoi(argv[3]);
 need(SetPriorityClass(GetCurrentProcess(),BELOW_NORMAL_PRIORITY_CLASS)!=0,"priority");need(SetThreadAffinityMask(GetCurrentThread(),DWORD_PTR(1)<<lp)!=0,"pin");need(GetCurrentProcessorNumber()==lp,"pin_readback");need(std::getenv("STRATA_IQ3S_MT1")&&std::string(std::getenv("STRATA_IQ3S_MT1"))=="1","live_MT1_env");need(!std::getenv("STRATA_IQ_MT_MIN"),"MT_MIN_absent");
 std::ifstream in(argv[5]);need(bool(in),"metadata_open");std::string line;std::vector<Layer> layers;while(std::getline(in,line)){if(line.empty()||line[0]=='#')continue;Layer x{};std::istringstream s(line);need(bool(s>>x.layer>>x.gu>>x.down>>x.offset>>x.bytes),"metadata_parse");if(x.gu==gt)layers.push_back(x);}
 need(layers.size()>=6,"six_layers");FILE* f=std::fopen(argv[4],"rb");need(f!=nullptr,"native_open");need(_fseeki64(f,0,SEEK_END)==0&&uint64_t(_ftelli64(f))==42912972800ull,"pack_geometry");
 const int epl=mode=="convert"?6:3;std::vector<Item> original,items;size_t nativeBytes=0,packedBytes=0;
 for(int li=0;li<6;li++){
  const auto& l=layers[li*layers.size()/6+layers.size()/12];cpu::NativeFmt fmt;std::string err;need(cpu::native_fmt(gt,l.down,H,FF,fmt,err),"native_fmt");need(fmt.bytes==l.bytes&&r4_size(gt,H,FF)==fmt.up_off,"native_geometry");
  for(int j=0;j<epl;j++){
   int ex=(11+37*j+5*l.layer)%512;auto* n=(unsigned char*)_aligned_malloc(fmt.bytes,64);auto* p=(unsigned char*)_aligned_malloc(fmt.bytes,64);need(n&&p,"alloc");need(_fseeki64(f,l.offset+uint64_t(ex)*l.bytes,SEEK_SET)==0&&std::fread(n,1,fmt.bytes,f)==fmt.bytes,"native_read");
   std::memcpy(p,n,fmt.bytes);r4_pack(gt,H,FF,n,p);r4_pack(gt,H,FF,n+fmt.up_off,p+fmt.up_off);original.push_back({n,p,fmt,l.layer,ex});nativeBytes+=fmt.bytes;packedBytes+=fmt.bytes;std::printf("ITEM,%s,%d,%d,%d,%d,%d,%zu\n",mode.c_str(),gt,lp,l.layer,ex,l.down,fmt.bytes);
  }
 }
 std::fclose(f);for(int j=0;j<epl;j++)for(int l=0;l<6;l++)items.push_back(original[l*epl+j]);
 std::printf("COVER,%s,%d,%d,%zu,%zu,%zu,%d,%d,%d\n",mode.c_str(),gt,lp,items.size(),nativeBytes,packedBytes,H,FF,cpu::iq256_variant());
 mechanical(gt,lp,items);if(mode=="convert")conversion(gt,lp,items);else tile(gt,lp,items);
 for(auto& it:items){_aligned_free(it.native);_aligned_free(it.packed);}
 std::printf("DONE,%s,%d,%d\n",mode.c_str(),gt,lp);return 0;
}
