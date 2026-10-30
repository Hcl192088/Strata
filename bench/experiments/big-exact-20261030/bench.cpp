#define NOMINMAX
#include "strata/kernels/cpu/native_expert.hpp"
#include "strata/kernels/cpu/iq_avx2.hpp"
#include "strata/kernels/cpu/expert_layout.hpp"
#include "ggml.h"
#include "ggml-cpu.h"
#include "ggml-quants.h"
#include <windows.h>
#include <malloc.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <algorithm>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>
#include <random>
namespace cpu=strata::kernels::cpu;
extern "C" void p1_dot(int,int,bool,const unsigned char*,size_t,int,const void*const*,float*);
extern "C" void r4_pack(int,int,int,const void*,void*);
extern "C" void r4_unpack(int,int,int,const void*,void*);
extern "C" void r4_dequant(int,int,int,const void*,float*);
extern "C" void r4_dot(int,int,int,int,const void*,const void* const*,float*);
extern "C" void r4_dot_variant(int,int,int,int,int,const void*,const void* const*,float*);
static void require(bool b,const char* msg){if(!b){std::fprintf(stderr,"FAIL %s\n",msg);std::exit(3);}}
static double now(){LARGE_INTEGER t,f;QueryPerformanceCounter(&t);QueryPerformanceFrequency(&f);return 1e6*double(t.QuadPart)/f.QuadPart;}
static double med(std::vector<double> v){std::sort(v.begin(),v.end());return v[v.size()/2];}
struct Layer{int l,gu,down;unsigned long long offset,bytes;};
struct Item{unsigned char* native;unsigned char* packed;cpu::NativeFmt fmt;int layer,expert;};
static void original_dequant(int type,const void* p,float* out,int n){
 switch(type){case 16:dequantize_row_iq2_xxs((const block_iq2_xxs*)p,out,n);return;case 17:dequantize_row_iq2_xs((const block_iq2_xs*)p,out,n);return;case 22:dequantize_row_iq2_s((const block_iq2_s*)p,out,n);return;case 18:dequantize_row_iq3_xxs((const block_iq3_xxs*)p,out,n);return;case 21:dequantize_row_iq3_s((const block_iq3_s*)p,out,n);return;default:std::abort();}
}
int main(int argc,char** argv){
 setvbuf(stdout,nullptr,_IONBF,0);require(argc==5,"args: lp type experts.bin native_experts.txt");
 const int lp=std::atoi(argv[1]),gt=std::atoi(argv[2]);require(SetPriorityClass(GetCurrentProcess(),BELOW_NORMAL_PRIORITY_CLASS),"priority");require(SetThreadAffinityMask(GetCurrentThread(),DWORD_PTR(1)<<lp)!=0,"pin");require(GetCurrentProcessorNumber()==lp,"pin_readback");
 require(std::getenv("STRATA_IQ3S_MT1")&&std::string(std::getenv("STRATA_IQ3S_MT1"))=="1","live_MT1_env");require(!std::getenv("STRATA_IQ_MT_MIN"),"MT_MIN_absent");
 std::vector<Layer> layers;std::ifstream in(argv[4]);std::string line;while(std::getline(in,line)){if(line.empty()||line[0]=='#')continue;std::istringstream s(line);Layer x{};s>>x.l>>x.gu>>x.down>>x.offset>>x.bytes;if(x.gu==gt)layers.push_back(x);}
 require(layers.size()>=6,"six_layers");FILE* f=std::fopen(argv[3],"rb");require(f,"open_native");
 std::vector<Item> items;size_t totalNative=0,totalPacked=0;const int H=2560,FF=640;require(gt==21,"prototype_type21_only");
 for(int li=0;li<6;li++){
  const auto& l=layers[li*layers.size()/6+layers.size()/12];cpu::NativeFmt fmt;std::string err;require(cpu::native_fmt(gt,l.down,H,FF,fmt,err),"native_fmt");require(fmt.bytes==l.bytes,"native_geometry_bytes");
  for(int j=0;j<6;j++){const int ex=(11+37*j+5*l.l)%512;auto* n=(unsigned char*)_aligned_malloc(fmt.bytes,64);auto* p=(unsigned char*)_aligned_malloc(fmt.down_off,64);require(n&&p,"alloc");require(_fseeki64(f,l.offset+ex*l.bytes,SEEK_SET)==0,"seek");require(std::fread(n,1,fmt.bytes,f)==fmt.bytes,"read_native");
   std::memcpy(p,n,fmt.down_off);items.push_back({n,p,fmt,l.l,ex});totalNative+=fmt.bytes;totalPacked+=fmt.down_off;printf("ITEM,%d,%d,%d,%d,%d,%zu\n",gt,lp,l.l,ex,l.down,fmt.bytes);
  }
 }
 std::fclose(f);std::vector<Item> order;for(int j=0;j<6;j++)for(int l=0;l<6;l++)order.push_back(items[l*6+j]);items=order;
 printf("COVER,%d,%d,%zu,%zu,%zu,%d,%d,%d\n",gt,lp,items.size(),totalNative,totalPacked,H,FF,cpu::iq256_variant());
 std::mt19937 gen(12345);std::normal_distribution<float> nd(0,1);std::vector<float> x(3*H);for(auto& z:x)z=nd(gen);
 const auto& fmt=items[0].fmt;std::vector<unsigned char> acts(3*cpu::kNativeActBytes),hq(3*cpu::kNativeHBytes);const void* ap[3];const void* hp[3];float* fp[3];float* op[3];std::vector<float> h(3*FF),out(3*H),g(3*FF),u(3*FF);
 for(int t=0;t<3;t++){ap[t]=acts.data()+t*cpu::kNativeActBytes;hp[t]=hq.data()+t*cpu::kNativeHBytes;fp[t]=h.data()+t*FF;op[t]=out.data()+t*H;cpu::native_quant_act(fmt,x.data()+t*H,(void*)ap[t]);}
 cpu::ActQ qa[3];const cpu::ActQ* qap[3]={&qa[0],&qa[1],&qa[2]};
 auto run=[&](int arm,const Item& it,int nt,bool full){
  if(!arm)cpu::native_gu_rows(it.fmt,it.native,ap,nt,fp,0,FF);
  else{
   p1_dot(arm==1?2:4,nt,lp==2,it.native,it.fmt.gu_row,H,ap,g.data());
   p1_dot(arm==1?2:4,nt,lp==2,it.native+it.fmt.up_off,it.fmt.gu_row,H,ap,u.data());
   for(int k=0;k<nt*FF;k++)h[k]=(g[k]/(1.f+std::exp(-g[k])))*u[k];
  }
  if(full){
   if(cpu::q2_native_kernels(it.fmt.d_type)){
    for(int t=0;t<nt;t++)cpu::act_quant_any(fp[t],FF,qa[t]);
    cpu::q2_rows_any(it.native+it.fmt.down_off,it.fmt.d_row,FF/64,qap,nt,op,0,H);
   }else{for(int t=0;t<nt;t++)cpu::native_quant_h(it.fmt,fp[t],(void*)hp[t]);cpu::native_down_rows(it.fmt,it.native,hp,nt,op,0,H);}
  }
 };

 for(int nt=1;nt<=3;nt++){
  const int arms=3;
  for(const auto& it:items){run(0,it,nt,true);std::vector<float> rh(h.begin(),h.begin()+nt*FF),ro(out.begin(),out.begin()+nt*H);
   for(int arm=1;arm<=2;arm++){run(arm,it,nt,true);if(std::memcmp(rh.data(),h.data(),nt*FF*4)||std::memcmp(ro.data(),out.data(),nt*H*4)){printf("BITS_FAIL,%d,%d,%d,%d,%d,%d\n",gt,lp,nt,arm,it.layer,it.expert);require(false,"native_vs_p1_bits");}}
  }
  printf("P1_BITS,%d,%d,%d,0\n",gt,lp,nt);
  for(int full=0;full<2;full++){
   std::vector<double> times[4];for(int arm=0;arm<arms;arm++)for(const auto& it:items)run(arm,it,nt,full!=0);
   for(int r=0;r<5;r++)for(int k=0;k<arms;k++){int arm=(r+k)%arms;double t=now();for(const auto& it:items)run(arm,it,nt,full!=0);double us=(now()-t)/items.size();times[arm].push_back(us);printf("RAW,%d,%d,%d,%d,%d,%d,%.6f\n",gt,lp,nt,full,r,arm,us);}
   for(int arm=1;arm<arms;arm++)printf("SUM,%d,%d,%d,%d,%d,%.6f,%.6f,%.6f\n",gt,lp,nt,full,arm,med(times[0]),med(times[arm]),med(times[0])/med(times[arm]));
  }
 }
 printf("DONE,%d,%d\n",gt,lp);return 0;
}
