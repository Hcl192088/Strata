#define NOMINMAX
#include "strata/kernels/cpu/pool.hpp"
#include "strata/kernels/cpu/native_expert.hpp"
#include "strata/kernels/cpu/iq_avx2.hpp"
#include <windows.h>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
namespace cpu=strata::kernels::cpu;
extern "C" int r4_pool_arm;
extern "C" void r4_pack_fast(int,int,int,const void*,void*);
extern "C" void r4_pack(int,int,int,const void*,void*);
extern "C" void r4_unpack(int,int,int,const void*,void*);
extern "C" void r4_dot_lowreg(int,int,int,int,int,const void*,const void* const*,float*);
extern "C" void r4_dot_variant(int,int,int,int,int,const void*,const void* const*,float*);
static void need(bool b,const char*s){if(!b){fprintf(stderr,"FAIL,%s\n",s);exit(3);}}
static double now(){static LARGE_INTEGER f{};if(!f.QuadPart)QueryPerformanceFrequency(&f);LARGE_INTEGER t;QueryPerformanceCounter(&t);return 1e6*double(t.QuadPart)/f.QuadPart;}
static double med(std::vector<double> x){std::sort(x.begin(),x.end());return x[x.size()/2];}
int main(int argc,char**argv){
 setvbuf(stdout,nullptr,_IONBF,0);need(argc==3,"args");need(SetPriorityClass(GetCurrentProcess(),ABOVE_NORMAL_PRIORITY_CLASS),"priority");
 need(getenv("STRATA_NATIVE_PIPE")&&std::string(getenv("STRATA_NATIVE_PIPE"))=="1","pipe");
 std::ifstream meta(argv[2]);need(bool(meta),"meta");std::string line;int layer=-1,gt=0,down=0;unsigned long long offset=0,bytes=0;
 while(std::getline(meta,line)){if(line.empty()||line[0]=='#')continue;std::istringstream s(line);int l,g,d;unsigned long long o,z;if(s>>l>>g>>d>>o>>z && g==21){layer=l;gt=g;down=d;offset=o;bytes=z;break;}}
 need(layer>=0,"layer");cpu::NativeFmt fmt;std::string err;need(cpu::native_fmt(gt,down,cpu::H,cpu::FF,fmt,err),"fmt");need(fmt.bytes==bytes,"geometry");
 FILE* f=fopen(argv[1],"rb");need(f,"open");need(_fseeki64(f,0,SEEK_END)==0 && _ftelli64(f)==42912972800LL,"pack_size");
 std::vector<std::vector<unsigned char>> blob(18,std::vector<unsigned char>(fmt.bytes));
 for(int i=0;i<18;i++){int ex=(11+37*i+5*layer)%512;need(_fseeki64(f,offset+(unsigned long long)ex*bytes,SEEK_SET)==0 && fread(blob[i].data(),1,fmt.bytes,f)==fmt.bytes,"read");printf("ITEM,%d,%d,%d,%zu\n",layer,ex,down,fmt.bytes);}fclose(f);
 std::vector<std::vector<unsigned char>> packed(18,std::vector<unsigned char>(fmt.bytes));
 double setup_start=now();for(int i=0;i<18;i++)std::memcpy(packed[i].data(),blob[i].data(),fmt.bytes);double copy_us=now()-setup_start;
 double pack_start=now();for(int i=0;i<18;i++){r4_pack_fast(21,cpu::H,cpu::FF,blob[i].data(),packed[i].data());r4_pack_fast(21,cpu::H,cpu::FF,blob[i].data()+fmt.up_off,packed[i].data()+fmt.up_off);}double pack_us=now()-pack_start;
 printf("SETUP,experts=18,native_bytes=%zu,packed_bytes=%zu,copy_us=%.3f,pack_us=%.3f\n",18*fmt.bytes,18*fmt.bytes,copy_us,pack_us);
 std::vector<unsigned char> inv(fmt.up_off),oldmat(fmt.up_off);
 for(int i=0;i<18;i++){need(!memcmp(blob[i].data()+fmt.down_off,packed[i].data()+fmt.down_off,fmt.bytes-fmt.down_off),"down_bytes");for(int m=0;m<2;m++){auto src=blob[i].data()+m*fmt.up_off;auto dst=packed[i].data()+m*fmt.up_off;r4_pack(21,cpu::H,cpu::FF,src,oldmat.data());need(!memcmp(dst,oldmat.data(),fmt.up_off),"full_pack_bits");r4_unpack(21,cpu::H,cpu::FF,dst,inv.data());need(!memcmp(src,inv.data(),fmt.up_off),"roundtrip");}}
 std::vector<std::vector<unsigned char>> act(3,std::vector<unsigned char>(cpu::kNativeActBytes));std::vector<float> x(cpu::H);const void* ap[3];
 for(int t=0;t<3;t++){for(int i=0;i<cpu::H;i++)x[i]=std::sin((i+13*t)*.031f);cpu::native_quant_act(fmt,x.data(),act[t].data());ap[t]=act[t].data();}
 // Every 4-row direct slice must equal the old full-row dot with correct token stride.
 for(int i=0;i<18;i++)for(int m=0;m<2;m++)for(int nt=2;nt<=3;nt++)for(int v=1;v<=2;v++){
  auto w=packed[i].data()+m*fmt.up_off;std::vector<float> full(nt*cpu::FF);r4_dot_variant(v,21,cpu::H,cpu::FF,nt,w,ap,full.data());
  for(int r=0;r<cpu::FF;r+=4){float guard[14];std::fill(guard,guard+14,1234567.25f);r4_dot_lowreg(v,21,cpu::H,4,nt,w+size_t(r)*fmt.gu_row,ap,guard+1);need(guard[0]==1234567.25f && guard[1+nt*4]==1234567.25f,"range_canary");for(int t=0;t<nt;t++)need(!memcmp(full.data()+t*cpu::FF+r,guard+1+t*4,4*sizeof(float)),"range_full_bits");}
 }
 printf("PARITY,18,640,2matrices,nt2and3,bothisa,packed_roundtrip_down_range_canary,0\n");
 cpu::ExpertPool pool(9,true,true,cpu::PoolAffinity::All,0);auto pin=cpu::pin_current_thread(cpu::planned_host_core(cpu::PoolAffinity::All));need(pin.valid,"hostpin");printf("POOL,workers=%d,host=%d,scratch_each=8192\n",pool.workers(),pool.host_works());
 for(int nt=2;nt<=3;nt++)for(int n:{1,4,8,16}){
  std::vector<cpu::ExpertJobMulti> jobs(n);std::vector<float> out(size_t(n)*nt*cpu::H);
  for(int i=0;i<n;i++){jobs[i].blob=blob[i].data();jobs[i].nt=nt;for(int t=0;t<nt;t++){jobs[i].nact[t]=ap[t];jobs[i].out[t]=out.data()+(size_t(i)*nt+t)*cpu::H;}}
  auto setarm=[&](int arm){r4_pool_arm=arm;for(int i=0;i<n;i++)jobs[i].blob=(arm==1?packed[i].data():blob[i].data());};
  setarm(0);pool.run_split_multi_native(fmt,jobs.data(),n);auto native=out;
  setarm(1);pool.run_split_multi_native(fmt,jobs.data(),n);auto pre=out;
  setarm(2);pool.run_split_multi_native(fmt,jobs.data(),n);need(!memcmp(pre.data(),out.data(),out.size()*sizeof(float)),"prepacked_onthefly_pool_bits");
  double maxerr=0;size_t diff=0;for(size_t i=0;i<out.size();i++){need(std::isfinite(native[i])&&std::isfinite(out[i]),"finite");maxerr=std::max(maxerr,std::abs(double(native[i])-out[i]));if(memcmp(&native[i],&out[i],4))diff++;}printf("NUMERIC,%d,%d,%zu,%.9g\n",nt,n,diff,maxerr);printf("POOL_BITS,%d,%d,0\n",nt,n);
  std::vector<double> times[3];for(int r=0;r<5;r++)for(int k=0;k<3;k++){int arm=(r+k)%3;setarm(arm);double t=now();pool.run_split_multi_native(fmt,jobs.data(),n);double us=now()-t;times[arm].push_back(us);printf("RAW,%d,%d,%d,%d,%.6f\n",nt,n,r,arm,us);}
  printf("SUM,%d,%d,%.6f,%.6f,%.6f,%.9f,%.9f\n",nt,n,med(times[0]),med(times[1]),med(times[2]),med(times[0])/med(times[1]),med(times[2])/med(times[1]));

 }
 cpu::restore_thread_affinity(pin);printf("DONE\n");return 0;
}
