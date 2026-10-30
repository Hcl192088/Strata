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
extern "C" size_t r4_size(int,int,int);
extern "C" void r4_pack_fast(int,int,int,const void*,void*);
extern "C" void r4_unpack_fast(int,int,int,const void*,void*);
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
 std::vector<Item> items;size_t totalNative=0,totalPacked=0;const int H=2560,FF=640;
 for(int li=0;li<6;li++){
  const auto& l=layers[li*layers.size()/6+layers.size()/12];cpu::NativeFmt fmt;std::string err;require(cpu::native_fmt(gt,l.down,H,FF,fmt,err),"native_fmt");require(fmt.bytes==l.bytes,"native_geometry_bytes");
  for(int j=0;j<6;j++){const int ex=(11+37*j+5*l.l)%512;auto* n=(unsigned char*)_aligned_malloc(fmt.bytes,64);auto* p=(unsigned char*)_aligned_malloc(fmt.bytes,64);require(n&&p,"alloc");require(_fseeki64(f,l.offset+ex*l.bytes,SEEK_SET)==0,"seek");require(std::fread(n,1,fmt.bytes,f)==fmt.bytes,"read_native");
   require(r4_size(gt,H,FF)==fmt.up_off,"same_size");std::memcpy(p,n,fmt.bytes);r4_pack(gt,H,FF,n,p);r4_pack(gt,H,FF,n+fmt.up_off,p+fmt.up_off);items.push_back({n,p,fmt,l.l,ex});totalNative+=fmt.bytes;totalPacked+=fmt.bytes;printf("ITEM,%d,%d,%d,%d,%d,%zu\n",gt,lp,l.l,ex,l.down,fmt.bytes);
  }
 }
 std::fclose(f);std::vector<Item> order;for(int j=0;j<6;j++)for(int l=0;l<6;l++)order.push_back(items[l*6+j]);items=order;
 printf("COVER,%d,%d,%zu,%zu,%zu,%d,%d,%d\n",gt,lp,items.size(),totalNative,totalPacked,H,FF,cpu::iq256_variant());
 size_t bytesChecked=0,valuesChecked=0;std::vector<unsigned char> inverse(items[0].fmt.down_off);std::vector<float> da(size_t(FF)*H),db(size_t(FF)*H);
 for(const auto& it:items)for(int mat=0;mat<2;mat++){
  const auto* orig=it.native+mat*it.fmt.up_off;const auto* packed=it.packed+mat*it.fmt.up_off;r4_unpack(gt,H,FF,packed,inverse.data());require(std::memcmp(orig,inverse.data(),it.fmt.up_off)==0,"repack_roundtrip");bytesChecked+=it.fmt.up_off;
  for(int row=0;row<FF;row++)original_dequant(gt,orig+row*it.fmt.gu_row,da.data()+size_t(row)*H,H);
  r4_dequant(gt,H,FF,packed,db.data());for(size_t k=0;k<da.size();k++)require(da[k]==db[k],"decoded_weight_exact_value");valuesChecked+=da.size();
 }
 printf("PARITY,%d,%d,%zu,%zu,0,0\n",gt,lp,bytesChecked,valuesChecked);
 std::vector<double> pt,ut;for(int r=0;r<9;r++){
  double t=now();for(const auto& it:items){r4_pack(gt,H,FF,it.native,it.packed);r4_pack(gt,H,FF,it.native+it.fmt.up_off,it.packed+it.fmt.up_off);}pt.push_back((now()-t)/items.size());
  t=now();for(const auto& it:items){r4_unpack(gt,H,FF,it.packed,inverse.data());r4_unpack(gt,H,FF,it.packed+it.fmt.up_off,inverse.data()+it.fmt.up_off);}ut.push_back((now()-t)/items.size());
 }
 printf("CONVERT,%d,%d,%.6f,%.6f\n",gt,lp,med(pt),med(ut));
 std::vector<unsigned char> fastbuf(items[0].fmt.up_off),oldbuf(items[0].fmt.up_off);
 for(const auto& it:items)for(int m=0;m<2;m++){
  r4_pack_fast(gt,H,FF,it.native+m*it.fmt.up_off,fastbuf.data());require(!std::memcmp(fastbuf.data(),it.packed+m*it.fmt.up_off,it.fmt.up_off),"fast_pack_equal");
  r4_unpack_fast(gt,H,FF,fastbuf.data(),oldbuf.data());require(!std::memcmp(oldbuf.data(),it.native+m*it.fmt.up_off,it.fmt.up_off),"fast_unpack_equal");
 }
 std::vector<double> fpt,fut;for(int r=0;r<5;r++){
  double t=now();for(const auto& it:items){r4_pack_fast(gt,H,FF,it.native,fastbuf.data());r4_pack_fast(gt,H,FF,it.native+it.fmt.up_off,fastbuf.data());}fpt.push_back((now()-t)/items.size());
  t=now();for(const auto& it:items){r4_unpack_fast(gt,H,FF,it.packed,oldbuf.data());r4_unpack_fast(gt,H,FF,it.packed+it.fmt.up_off,oldbuf.data());}fut.push_back((now()-t)/items.size());
 }
 printf("FAST_CONVERT,%d,%d,%.6f,%.6f,0\n",gt,lp,med(fpt),med(fut));
 std::mt19937 gen(12345);std::normal_distribution<float> nd(0,1);std::vector<float> x(3*H);for(auto& z:x)z=nd(gen);
 const auto& fmt=items[0].fmt;std::vector<unsigned char> acts(3*cpu::kNativeActBytes),hq(3*cpu::kNativeHBytes);const void* ap[3];const void* hp[3];float* fp[3];float* op[3];std::vector<float> h(3*FF),out(3*H),g(3*FF),u(3*FF);
 for(int t=0;t<3;t++){ap[t]=acts.data()+t*cpu::kNativeActBytes;hp[t]=hq.data()+t*cpu::kNativeHBytes;fp[t]=h.data()+t*FF;op[t]=out.data()+t*H;cpu::native_quant_act(fmt,x.data()+t*H,(void*)ap[t]);}
 cpu::ActQ qa[3];const cpu::ActQ* qap[3]={&qa[0],&qa[1],&qa[2]};
 auto run=[&](int arm,const Item& it,int nt,bool full){
  if(!arm)cpu::native_gu_rows(it.fmt,it.native,ap,nt,fp,0,FF);
  else{
   int variant=arm==9?0:(arm==3?(lp==2?2:1):arm);
   if(arm==3 && nt>1){
    int first=nt-1;r4_dot_variant(variant,gt,H,FF,first,it.packed,ap,g.data());r4_dot_variant(variant,gt,H,FF,1,it.packed,ap+first,g.data()+first*FF);
    r4_dot_variant(variant,gt,H,FF,first,it.packed+it.fmt.up_off,ap,u.data());r4_dot_variant(variant,gt,H,FF,1,it.packed+it.fmt.up_off,ap+first,u.data()+first*FF);
   }else{r4_dot_variant(variant,gt,H,FF,nt,it.packed,ap,g.data());r4_dot_variant(variant,gt,H,FF,nt,it.packed+it.fmt.up_off,ap,u.data());}
   for(int k=0;k<nt*FF;k++)h[k]=(g[k]/(1.f+std::exp(-g[k])))*u[k];
  }
  if(full){
   if(cpu::q2_native_kernels(it.fmt.d_type)){
    for(int t=0;t<nt;t++)cpu::act_quant_any(fp[t],FF,qa[t]);
    cpu::q2_rows_any((arm?it.packed:it.native)+it.fmt.down_off,it.fmt.d_row,FF/64,qap,nt,op,0,H);
   }else{for(int t=0;t<nt;t++)cpu::native_quant_h(it.fmt,fp[t],(void*)hp[t]);cpu::native_down_rows(it.fmt,arm?it.packed:it.native,hp,nt,op,0,H);}
  }
 };

 for(int nt=1;nt<=3;nt++){
  const int arms=nt==1?3:4;
  // Exact integer-kernel substitution is checked against the original R4 path before performance work.
  for(const auto& it:items){run(9,it,nt,false);std::vector<float> rh(h.begin(),h.begin()+nt*FF);
   for(int arm=1;arm<=2;arm++){run(arm,it,nt,false);if(std::memcmp(rh.data(),h.data(),nt*FF*4)){printf("R4_BITS_FAIL,%d,%d,%d,%d,%d,%d\n",gt,lp,nt,arm,it.layer,it.expert);require(false,"old_vs_v2_bits");}}
  }
  printf("R4_BITS,%d,%d,%d,0\n",gt,lp,nt);
  for(int arm=1;arm<arms;arm++){
   double maxH=0,maxDiffH=0,maxO=0,maxDiffO=0;size_t diffH=0,diffO=0;
   for(const auto& it:items){run(0,it,nt,true);std::vector<float> rh(h.begin(),h.begin()+nt*FF),ro(out.begin(),out.begin()+nt*H);run(arm,it,nt,true);
    for(int k=0;k<nt*FF;k++){require(std::isfinite(h[k])&&std::isfinite(rh[k]),"finite_h");maxH=std::max(maxH,std::fabs(double(rh[k])));maxDiffH=std::max(maxDiffH,std::fabs(double(rh[k])-h[k]));if(std::memcmp(&rh[k],&h[k],4))diffH++;}
    for(int k=0;k<nt*H;k++){require(std::isfinite(out[k])&&std::isfinite(ro[k]),"finite_out");maxO=std::max(maxO,std::fabs(double(ro[k])));maxDiffO=std::max(maxDiffO,std::fabs(double(ro[k])-out[k]));if(std::memcmp(&ro[k],&out[k],4))diffO++;}
   }
   printf("NUMERIC,%d,%d,%d,%d,%.9g,%.9g,%zu,%.9g,%.9g,%zu\n",gt,lp,nt,arm,maxH,maxDiffH,diffH,maxO,maxDiffO,diffO);
   require(maxDiffH<=1e-4*std::max(1.,maxH),"h_numeric_screen");
  }
  for(int full=1;full<2;full++){
   std::vector<double> times[4];for(int arm=0;arm<arms;arm++)for(const auto& it:items)run(arm,it,nt,full!=0);
   for(int r=0;r<3;r++)for(int k=0;k<arms;k++){int arm=(r+k)%arms;double t=now();for(const auto& it:items)run(arm,it,nt,full!=0);double us=(now()-t)/items.size();times[arm].push_back(us);printf("RAW,%d,%d,%d,%d,%d,%d,%.6f\n",gt,lp,nt,full,r,arm,us);}
   for(int arm=1;arm<arms;arm++)printf("SUM,%d,%d,%d,%d,%d,%.6f,%.6f,%.6f\n",gt,lp,nt,full,arm,med(times[0]),med(times[arm]),med(times[0])/med(times[arm]));
  }
 }
 printf("DONE,%d,%d\n",gt,lp);return 0;
}

