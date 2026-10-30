#define NOMINMAX
#include "strata/platform/direct_file.hpp"
#include <windows.h>
#include <tlhelp32.h>
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
namespace io=strata::platform;
static void need(bool ok,const char* why){if(!ok){std::fprintf(stderr,"FAIL,%s\n",why);std::exit(3);}}
static double us(){static LARGE_INTEGER f{};if(!f.QuadPart)QueryPerformanceFrequency(&f);LARGE_INTEGER t;QueryPerformanceCounter(&t);return 1e6*double(t.QuadPart)/double(f.QuadPart);}
static int threads(){HANDLE s=CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD,0);need(s!=INVALID_HANDLE_VALUE,"thread_snapshot");THREADENTRY32 e{};e.dwSize=sizeof(e);int n=0;BOOL ok=Thread32First(s,&e);while(ok){if(e.th32OwnerProcessID==GetCurrentProcessId())n++;ok=Thread32Next(s,&e);}CloseHandle(s);return n;}
static double pct(std::vector<double> a,double p){need(!a.empty(),"empty_percentile");std::sort(a.begin(),a.end());double x=p*double(a.size()-1);size_t l=size_t(x),h=std::min(l+1,a.size()-1);return a[l]+(a[h]-a[l])*(x-double(l));}
struct Layer{int layer,gu,down;uint64_t offset,bytes;};
struct Range{int gu,layer,expert;uint64_t blob,blob_bytes,offset;uint32_t bytes;std::vector<unsigned char> oracle;};
struct Result{int issuing,batch,round;bool warmup;double total_us,wall_us,p50_us,p95_us;uint64_t bytes;};
static double campaign_start;
static constexpr uint64_t file_bytes=42912972800ull;
static constexpr uint64_t chunk_bytes=1ull<<20;
static constexpr uint64_t align_bytes=4096;
static constexpr int nranges=16;
static Result arm(const char* file,std::vector<Range>& rs,const std::array<void*,8>& buffers,int issuing,int batch,int round,bool warmup){
 need(us()-campaign_start<120e6,"campaign_120s_deadline");
 char setting[16];std::snprintf(setting,sizeof(setting),"%d",issuing);need(_putenv_s("STRATA_IO_THREADS",setting)==0,"set_io_threads");
 const char* got=std::getenv("STRATA_IO_THREADS");need(got&&std::string(got)==setting,"env_readback");
 const int before=threads();io::DirectFile f;std::string err;if(!f.open(file,err)){std::fprintf(stderr,"IO_ERROR,open,%s\n",err.c_str());need(false,"direct_open");}need(f.size()==file_bytes,"direct_size");const int opened=threads();
 double wall=us(),sum=0;uint64_t read_bytes=0;std::vector<double> times;
 for(size_t at=0;at<rs.size();at+=batch){
  const int n=std::min(batch,int(rs.size()-at));bool done[8]={};int pending=n;double start=us();
  for(int k=0;k<n;k++){auto& r=rs[at+k];if(!f.submit(r.offset,buffers[k],r.bytes,uint64_t(at+k+1),err)){std::fprintf(stderr,"IO_ERROR,submit,%s\n",err.c_str());need(false,"submit");}}
  while(pending){
   need(us()-start<20e6,"batch_20s_deadline");io::Completion completed[8];int count=f.wait(completed,8,1000);need(count>=0,"wait_error");
   for(int j=0;j<count;j++){
    auto& x=completed[j];need(x.tag>=at+1&&x.tag<at+size_t(n)+1,"completion_tag");int k=int(x.tag-at-1);
    need(!done[k]&&x.ok&&x.bytes==rs[at+k].bytes,"completion_bytes_or_status");done[k]=true;pending--;read_bytes+=x.bytes;
   }
  }
  double dt=us()-start;sum+=dt;times.push_back(dt);
  // Exact byte oracle comparison is outside each batch's timed interval.
  for(int k=0;k<n;k++)need(std::memcmp(buffers[k],rs[at+k].oracle.data(),rs[at+k].bytes)==0,"byte_mismatch");
 }
 wall=us()-wall;f.close();const int closed=threads();
 need(closed==before,"issue_threads_not_joined");
 Result r{issuing,batch,round,warmup,sum,wall,pct(times,.5),pct(times,.95),read_bytes};
 std::printf("ARM,%d,%d,%d,%d,%.6f,%.6f,%.6f,%.6f,%llu,0,%s,%d,%d,%d\n",round,issuing,batch,int(warmup),sum,wall,r.p50_us,r.p95_us,(unsigned long long)read_bytes,setting,before,opened,closed);
 return r;
}
int main(int argc,char** argv){
 setvbuf(stdout,nullptr,_IONBF,0);need(argc==3,"args_experts_bin_native_experts_txt");need(SetPriorityClass(GetCurrentProcess(),BELOW_NORMAL_PRIORITY_CLASS)!=0,"BelowNormal");
 campaign_start=us();std::ifstream meta(argv[2]);need(bool(meta),"metadata_open");std::vector<Layer> layers;std::string line;
 while(std::getline(meta,line)){if(line.empty()||line[0]=='#')continue;Layer l{};std::istringstream s(line);need(bool(s>>l.layer>>l.gu>>l.down>>l.offset>>l.bytes),"metadata_parse");layers.push_back(l);}
 const int types[5]={16,17,22,18,21};std::array<Layer,5> chosen{};
 for(int t=0;t<5;t++){std::vector<Layer> candidates;for(const auto& l:layers)if(l.gu==types[t])candidates.push_back(l);need(!candidates.empty(),"actual_format_missing");chosen[t]=candidates[candidates.size()/2];}
 FILE* ordinary=std::fopen(argv[1],"rb");need(ordinary!=nullptr,"oracle_open");need(_fseeki64(ordinary,0,SEEK_END)==0&&uint64_t(_ftelli64(ordinary))==file_bytes,"oracle_size");
 std::vector<Range> ranges;uint64_t pass_bytes=0;uint32_t largest=0;const int experts[3]={17,257,509};
 for(int i=0;i<nranges;i++){
  const int t=i==15?0:i%5,j=i==15?0:i/5;const auto& l=chosen[t];const int ex=i==15?101:experts[j];
  const uint64_t raw=l.offset+uint64_t(ex)*l.bytes,off=raw&~(align_bytes-1),prefix=std::min(l.bytes,chunk_bytes);
  const uint64_t bytes=(raw-off+prefix+align_bytes-1)&~(align_bytes-1);need(bytes<=UINT32_MAX&&off+bytes<=file_bytes,"range_geometry");
  Range r{l.gu,l.layer,ex,raw,l.bytes,off,uint32_t(bytes),std::vector<unsigned char>(size_t(bytes))};
  need(_fseeki64(ordinary,off,SEEK_SET)==0&&std::fread(r.oracle.data(),1,size_t(bytes),ordinary)==bytes,"oracle_read");
  std::printf("RANGE,%d,%d,%d,%d,%llu,%u,%llu,%llu,%llu\n",i,l.gu,l.layer,ex,(unsigned long long)off,r.bytes,(unsigned long long)raw,(unsigned long long)l.bytes,(unsigned long long)prefix);
  pass_bytes+=bytes;largest=std::max(largest,uint32_t(bytes));ranges.push_back(std::move(r));
 }
 std::fclose(ordinary);
 const uint64_t buffer_bytes=pass_bytes+8ull*largest,all_io=pass_bytes*(1+2+9*2*4);
 need(buffer_bytes<=32ull*1024*1024,"buffer_32MiB_budget");need(pass_bytes*4<=100ull*1024*1024,"arm_four_sizes_100MiB_budget");need(all_io<=2ull*1024*1024*1024,"total_2GiB_budget");
 std::printf("BUDGET,%llu,%llu,%llu,%llu\n",(unsigned long long)pass_bytes,(unsigned long long)(pass_bytes*4),(unsigned long long)buffer_bytes,(unsigned long long)all_io);
 std::array<void*,8> buffers{};for(auto& b:buffers){b=io::DirectFile::alloc_aligned(largest);need(b!=nullptr,"aligned_buffer");need(uintptr_t(b)%align_bytes==0,"aligned_pointer");}
 // One warmup per thread setting at batch8, after the ordinary-read byte oracle.
 arm(argv[1],ranges,buffers,4,8,-1,true);arm(argv[1],ranges,buffers,8,8,-1,true);
 std::vector<Result> results;
 for(int round=0;round<9;round++)for(int batch:{1,2,4,8})for(int k=0;k<2;k++){
  int issuing=((round%2?k==0:k==1)?8:4);results.push_back(arm(argv[1],ranges,buffers,issuing,batch,round,false));
 }
 for(int batch:{1,2,4,8}){
  std::vector<double> a,b,ratios;
  for(int round=0;round<9;round++){
   double at=0,bt=0;for(const auto& r:results)if(r.batch==batch&&r.round==round)(r.issuing==4?at:bt)=r.total_us;
   need(at>0&&bt>0,"pair_completeness");a.push_back(at);b.push_back(bt);ratios.push_back(at/bt);
  }
  std::printf("SUMMARY,%d,%.6f,%.6f,%.9f\n",batch,pct(a,.5),pct(b,.5),pct(ratios,.5));
 }
 for(auto b:buffers)io::DirectFile::free_aligned(b);
 std::printf("DONE,72,16,%.6f\n",(us()-campaign_start)/1e6);return 0;
}
