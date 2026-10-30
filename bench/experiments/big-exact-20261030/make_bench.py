from pathlib import Path
R=Path(__file__).resolve().parent
s=(R.parent/'cpu-r4-v2-20261030/bench.cpp').read_text()
s=s.replace('extern "C" size_t r4_size(int,int,int);','extern "C" void p1_dot(int,int,bool,const unsigned char*,size_t,int,const void*const*,float*);')
start=s.index('   require(r4_size(');end=s.index('totalNative+=fmt.bytes;',start)
s=s[:start]+'''   std::memcpy(p,n,fmt.down_off);items.push_back({n,p,fmt,l.l,ex});'''+s[end:]
start=s.index(' size_t bytesChecked=');end=s.index(' std::mt19937 gen',start)
s=s[:start]+s[end:]
start=s.index('   int variant=');end=s.index('   for(int k=0;k<nt*FF;k++)',start)
s=s[:start]+'''   p1_dot(arm==1?2:4,nt,lp==2,it.native,it.fmt.gu_row,H,ap,g.data());
   p1_dot(arm==1?2:4,nt,lp==2,it.native+it.fmt.up_off,it.fmt.gu_row,H,ap,u.data());
'''+s[end:]
start=s.index('  const int arms=');end=s.index('  for(int full=0;',start)
s=s[:start]+'''  const int arms=3;
  for(const auto& it:items){run(0,it,nt,true);std::vector<float> rh(h.begin(),h.begin()+nt*FF),ro(out.begin(),out.begin()+nt*H);
   for(int arm=1;arm<=2;arm++){run(arm,it,nt,true);if(std::memcmp(rh.data(),h.data(),nt*FF*4)||std::memcmp(ro.data(),out.data(),nt*H*4)){printf("BITS_FAIL,%d,%d,%d,%d,%d,%d\\n",gt,lp,nt,arm,it.layer,it.expert);require(false,"native_vs_p1_bits");}}
  }
  printf("P1_BITS,%d,%d,%d,0\\n",gt,lp,nt);
'''+s[end:]
s=s.replace('require(argc==5,','require(argc==5,').replace('setvbuf(stdout,nullptr,_IONBF,0);','setvbuf(stdout,nullptr,_IONBF,0);')
s=s.replace('const int H=2560,FF=640;','const int H=2560,FF=640;require(gt==21,"prototype_type21_only");')
(R/'bench.cpp').write_text(s,encoding='utf-8')
