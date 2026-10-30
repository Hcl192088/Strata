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
 std::vector<std::vector<unsigned char>> act(3,std::vector<unsigned char>(cpu::kNativeActBytes));std::vector<float> x(cpu::H);const void* ap[3];
 for(int t=0;t<3;t++){for(int i=0;i<cpu::H;i++)x[i]=std::sin((i+13*t)*.031f);cpu::native_quant_act(fmt,x.data(),act[t].data());ap[t]=act[t].data();}
 // Compare fast tile packing with existing pack and lowreg against old R4 for both ISAs, every GU row and sample.
 std::vector<unsigned char> fast(fmt.gu_row*4),old(fmt.gu_row*4);float a[12],b[12];
 for(auto& z:blob)for(int m=0;m<2;m++)for(int r=0;r<cpu::FF;r+=4){const auto *src=z.data()+m*fmt.up_off+size_t(r)*fmt.gu_row;r4_pack_fast(21,cpu::H,4,src,fast.data());r4_pack(21,cpu::H,4,src,old.data());need(!memcmp(fast.data(),old.data(),fast.size()),"pack_bits");for(int nt=2;nt<=3;nt++)for(int v=1;v<=2;v++){r4_dot_variant(v,21,cpu::H,4,nt,fast.data(),ap,a);r4_dot_lowreg(v,21,cpu::H,4,nt,fast.data(),ap,b);need(!memcmp(a,b,nt*4*sizeof(float)),"r4_bits");}}
 printf("PARITY,18,640,2matrices,nt2and3,bothisa,0\n");
 cpu::ExpertPool pool(9,true,true,cpu::PoolAffinity::All,0);auto pin=cpu::pin_current_thread(cpu::planned_host_core(cpu::PoolAffinity::All));need(pin.valid,"hostpin");printf("POOL,workers=%d,host=%d,scratch_each=8192\n",pool.workers(),pool.host_works());
 for(int nt=2;nt<=3;nt++)for(int n:{1,4,8,16}){
  std::vector<cpu::ExpertJobMulti> jobs(n);std::vector<float> out(size_t(n)*nt*cpu::H);
  for(int i=0;i<n;i++){jobs[i].blob=blob[i].data();jobs[i].nt=nt;for(int t=0;t<nt;t++){jobs[i].nact[t]=ap[t];jobs[i].out[t]=out.data()+(size_t(i)*nt+t)*cpu::H;}}
  r4_pool_arm=0;pool.run_split_multi_native(fmt,jobs.data(),n);auto ref=out;r4_pool_arm=1;pool.run_split_multi_native(fmt,jobs.data(),n);double maxerr=0;size_t diff=0;for(size_t i=0;i<out.size();i++){need(std::isfinite(ref[i])&&std::isfinite(out[i]),"finite");maxerr=std::max(maxerr,std::abs(double(ref[i])-out[i]));if(memcmp(&ref[i],&out[i],4))diff++;}printf("NUMERIC,%d,%d,%zu,%.9g\n",nt,n,diff,maxerr);
  std::vector<double> times[2];for(int r=0;r<5;r++)for(int k=0;k<2;k++){int arm=(r+k)%2;r4_pool_arm=arm;double t=now();pool.run_split_multi_native(fmt,jobs.data(),n);double us=now()-t;times[arm].push_back(us);printf("RAW,%d,%d,%d,%d,%.6f\n",nt,n,r,arm,us);}
  printf("SUM,%d,%d,%.6f,%.6f,%.9f\n",nt,n,med(times[0]),med(times[1]),med(times[0])/med(times[1]));
 }
 cpu::restore_thread_affinity(pin);printf("DONE\n");return 0;
}
