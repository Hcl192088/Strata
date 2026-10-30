#define NOMINMAX
#include "strata/kernels/cpu/native_expert.hpp"
#include "strata/kernels/cpu/iq_avx2.hpp"
#include "strata/kernels/cpu/expert_layout.hpp"
#include "ggml.h"
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
extern "C" void r4_dot_variant(int,int,int,int,int,const void*,const void* const*,float*);
extern "C" void r4_dot_prefetch(int,int,int,int,int,const void*,const void* const*,float*);
extern "C" void r4_dot_lowreg(int,int,int,int,int,const void*,const void* const*,float*);
static void need(bool b,const char* s){if(!b){std::fprintf(stderr,"FAIL,%s\n",s);std::exit(3);}}
static double now(){static LARGE_INTEGER f{};if(!f.QuadPart)QueryPerformanceFrequency(&f);LARGE_INTEGER t;QueryPerformanceCounter(&t);return 1e6*double(t.QuadPart)/f.QuadPart;}
static double med(std::vector<double> a){std::sort(a.begin(),a.end());return a[a.size()/2];}
static constexpr int H=2560,FF=640,GT=21;
struct Layer{int layer,gu,down;uint64_t offset,bytes;};
struct Item{unsigned char* native;unsigned char* packed;cpu::NativeFmt fmt;int layer,expert;};
int main(int argc,char** argv){
 setvbuf(stdout,nullptr,_IONBF,0);need(argc==6,"args_lp_nt_oldvariant_experts_metadata");const int lp=std::atoi(argv[1]),nt=std::atoi(argv[2]),variant=std::atoi(argv[3]);need(nt==2||nt==3,"only_nt2_nt3");need(variant==1||variant==2,"explicit_oldvariant_1_or_2");
 need(SetPriorityClass(GetCurrentProcess(),BELOW_NORMAL_PRIORITY_CLASS)!=0,"priority");need(SetThreadAffinityMask(GetCurrentThread(),DWORD_PTR(1)<<lp)!=0,"pin");need(GetCurrentProcessorNumber()==lp,"pin_readback");need(std::getenv("STRATA_IQ3S_MT1")&&std::string(std::getenv("STRATA_IQ3S_MT1"))=="1","live_MT1_env");need(!std::getenv("STRATA_IQ_MT_MIN"),"MT_MIN_absent");
 std::ifstream meta(argv[5]);need(bool(meta),"metadata_open");std::string line;std::vector<Layer> layers;while(std::getline(meta,line)){if(line.empty()||line[0]=='#')continue;Layer l{};std::istringstream s(line);need(bool(s>>l.layer>>l.gu>>l.down>>l.offset>>l.bytes),"metadata_parse");if(l.gu==GT)layers.push_back(l);}
 need(layers.size()>=6,"six_IQ3S_layers");FILE* f=std::fopen(argv[4],"rb");need(f!=nullptr,"native_open");need(_fseeki64(f,0,SEEK_END)==0&&uint64_t(_ftelli64(f))==42912972800ull,"pack_geometry");std::vector<Item> items,original;size_t nativeBytes=0,packedBytes=0,roundtripBytes=0;
 for(int li=0;li<6;li++){
  const auto& l=layers[li*layers.size()/6+layers.size()/12];cpu::NativeFmt fmt;std::string err;need(cpu::native_fmt(GT,l.down,H,FF,fmt,err),"native_fmt");need(fmt.bytes==l.bytes&&r4_size(GT,H,FF)==fmt.up_off,"native_geometry");
  for(int j=0;j<3;j++){
   int ex=(11+37*j+5*l.layer)%512;auto* n=(unsigned char*)_aligned_malloc(fmt.bytes,64);auto* p=(unsigned char*)_aligned_malloc(fmt.bytes,64);need(n&&p,"alloc");need(_fseeki64(f,l.offset+uint64_t(ex)*l.bytes,SEEK_SET)==0&&std::fread(n,1,fmt.bytes,f)==fmt.bytes,"native_read");
   std::memcpy(p,n,fmt.bytes);r4_pack(GT,H,FF,n,p);r4_pack(GT,H,FF,n+fmt.up_off,p+fmt.up_off);std::vector<unsigned char> inv(fmt.down_off);
   r4_unpack(GT,H,FF,p,inv.data());r4_unpack(GT,H,FF,p+fmt.up_off,inv.data()+fmt.up_off);need(!std::memcmp(n,inv.data(),fmt.down_off),"weight_roundtrip");roundtripBytes+=fmt.down_off;
   original.push_back({n,p,fmt,l.layer,ex});nativeBytes+=fmt.bytes;packedBytes+=fmt.bytes;std::printf("ITEM,%d,%d,%d,%d,%d,%d,%d,%zu\n",GT,lp,nt,variant,l.layer,ex,l.down,fmt.bytes);
  }
 }
 std::fclose(f);for(int j=0;j<3;j++)for(int l=0;l<6;l++)items.push_back(original[l*3+j]);
 std::printf("COVER,%d,%d,%d,%d,%zu,%zu,%zu,%zu,%d\n",GT,lp,nt,variant,items.size(),nativeBytes,packedBytes,roundtripBytes,cpu::iq256_variant());
 std::mt19937 gen(12345);std::normal_distribution<float> nd(0,1);std::vector<float> x(nt*H);for(auto& z:x)z=nd(gen);
 std::vector<unsigned char> acts(nt*cpu::kNativeActBytes),hq(nt*cpu::kNativeHBytes);const void* ap[3];const void* hp[3];float* fp[3];float* op[3];std::vector<float> h(nt*FF),out(nt*H),g(nt*FF),u(nt*FF);
 for(int t=0;t<nt;t++){ap[t]=acts.data()+t*cpu::kNativeActBytes;hp[t]=hq.data()+t*cpu::kNativeHBytes;fp[t]=h.data()+t*FF;op[t]=out.data()+t*H;cpu::native_quant_act(items[0].fmt,x.data()+t*H,(void*)ap[t]);}
 cpu::ActQ qa[3];const cpu::ActQ* qap[3]={&qa[0],&qa[1],&qa[2]};
 auto run=[&](int arm,const Item& it,bool full){
  if(!arm)cpu::native_gu_rows(it.fmt,it.native,ap,nt,fp,0,FF);
  else{
   if(arm==1){r4_dot_variant(variant,GT,H,FF,nt,it.packed,ap,g.data());r4_dot_variant(variant,GT,H,FF,nt,it.packed+it.fmt.up_off,ap,u.data());}
   else if(arm==2){r4_dot_lowreg(variant,GT,H,FF,nt,it.packed,ap,g.data());r4_dot_lowreg(variant,GT,H,FF,nt,it.packed+it.fmt.up_off,ap,u.data());}
   else{r4_dot_prefetch(variant,GT,H,FF,nt,it.packed,ap,g.data());r4_dot_prefetch(variant,GT,H,FF,nt,it.packed+it.fmt.up_off,ap,u.data());}
   for(int k=0;k<nt*FF;k++)h[k]=(g[k]/(1.f+std::exp(-g[k])))*u[k];
  }
  if(full){const auto* blob=arm?it.packed:it.native;
   if(cpu::q2_native_kernels(it.fmt.d_type)){for(int t=0;t<nt;t++)cpu::act_quant_any(fp[t],FF,qa[t]);cpu::q2_rows_any(blob+it.fmt.down_off,it.fmt.d_row,FF/64,qap,nt,op,0,H);}
   else{for(int t=0;t<nt;t++)cpu::native_quant_h(it.fmt,fp[t],(void*)hp[t]);cpu::native_down_rows(it.fmt,blob,hp,nt,op,0,H);}
  }
 };
 // The new register arrangement must preserve oldR4 g/u/h and complete output bits.
 for(const auto& it:items){
  run(1,it,true);const auto rg=g,ru=u,rh=h,ro=out;run(3,it,true);
  if(std::memcmp(rg.data(),g.data(),g.size()*4)||std::memcmp(ru.data(),u.data(),u.size()*4)||std::memcmp(rh.data(),h.data(),h.size()*4)||std::memcmp(ro.data(),out.data(),out.size()*4)){
   std::printf("PREFETCH_BITS_FAIL,%d,%d,%d,%d,%d\n",lp,nt,variant,it.layer,it.expert);need(false,"prefetch_oldR4_bits");
  }
 }
 std::printf("PREFETCH_BITS,%d,%d,%d,%zu,0\n",lp,nt,variant,items.size());
 double maxH=0,diffH=0,maxO=0,diffO=0;size_t bitsH=0,bitsO=0;
 for(const auto& it:items){
  run(0,it,true);const auto rh=h,ro=out;run(2,it,true);
  for(int k=0;k<nt*FF;k++){need(std::isfinite(h[k])&&std::isfinite(rh[k]),"finite_h");maxH=std::max(maxH,std::fabs(double(rh[k])));diffH=std::max(diffH,std::fabs(double(rh[k])-h[k]));if(std::memcmp(&rh[k],&h[k],4))bitsH++;}
  for(int k=0;k<nt*H;k++){need(std::isfinite(out[k])&&std::isfinite(ro[k]),"finite_out");maxO=std::max(maxO,std::fabs(double(ro[k])));diffO=std::max(diffO,std::fabs(double(ro[k])-out[k]));if(std::memcmp(&ro[k],&out[k],4))bitsO++;}
 }
 std::printf("NUMERIC,%d,%d,%d,%.9g,%.9g,%zu,%.9g,%.9g,%zu\n",lp,nt,variant,maxH,diffH,bitsH,maxO,diffO,bitsO);need(diffH<=1e-4*std::max(1.,maxH),"h_numeric_screen");
 for(int full=0;full<2;full++){
  std::vector<double> times[4];for(int arm=0;arm<=3;arm++)for(const auto& it:items)run(arm,it,full!=0);
  for(int r=0;r<5;r++)for(int k=0;k<4;k++){int arm=(r+k)%4;double t=now();for(const auto& it:items)run(arm,it,full!=0);double dt=(now()-t)/items.size();times[arm].push_back(dt);std::printf("LOWREG_RAW,%d,%d,%d,%d,%d,%d,%.6f\n",lp,nt,variant,full,r,arm,dt);}
  for(int arm=1;arm<=3;arm++)std::printf("LOWREG_SUM,%d,%d,%d,%d,%d,%.6f,%.6f,%.9f\n",lp,nt,variant,full,arm,med(times[0]),med(times[arm]),med(times[0])/med(times[arm]));
  std::printf("LOWREG_VS_OLD,%d,%d,%d,%d,%.6f,%.6f,%.9f\n",lp,nt,variant,full,med(times[1]),med(times[2]),med(times[1])/med(times[2]));
 }
 for(auto& it:items){_aligned_free(it.native);_aligned_free(it.packed);}std::printf("DONE,%d,%d,%d\n",lp,nt,variant);return 0;
}

