from pathlib import Path
R=Path(__file__).resolve().parent
s=(R.parent/'cpu-r4-20261029/bench.cpp').read_text()
s=s.replace('extern "C" void r4_dot(int,int,int,int,const void*,const void* const*,float*);','extern "C" void r4_dot(int,int,int,int,const void*,const void* const*,float*);\nextern "C" void r4_dot_variant(int,int,int,int,int,const void*,const void* const*,float*);')
s=s.replace('else{r4_dot(gt,H,FF,nt,it.packed,ap,g.data());r4_dot(gt,H,FF,nt,it.packed+it.fmt.up_off,ap,u.data());for(int k=0;k<nt*FF;k++)h[k]=(g[k]/(1.f+std::exp(-g[k])))*u[k];}', '''else{
   int variant=arm==9?0:(arm==3?(lp==2?2:1):arm);
   if(arm==3 && nt>1){
    int first=nt-1;r4_dot_variant(variant,gt,H,FF,first,it.packed,ap,g.data());r4_dot_variant(variant,gt,H,FF,1,it.packed,ap+first,g.data()+first*FF);
    r4_dot_variant(variant,gt,H,FF,first,it.packed+it.fmt.up_off,ap,u.data());r4_dot_variant(variant,gt,H,FF,1,it.packed+it.fmt.up_off,ap+first,u.data()+first*FF);
   }else{r4_dot_variant(variant,gt,H,FF,nt,it.packed,ap,g.data());r4_dot_variant(variant,gt,H,FF,nt,it.packed+it.fmt.up_off,ap,u.data());}
   for(int k=0;k<nt*FF;k++)h[k]=(g[k]/(1.f+std::exp(-g[k])))*u[k];
  }''')
at=s.index(' for(int nt=1;nt<=3;nt++){')
s=s[:at]+'''
 for(int nt=1;nt<=3;nt++){
  const int arms=nt==1?3:4;
  // Exact integer-kernel substitution is checked against the original R4 path before performance work.
  for(const auto& it:items){run(9,it,nt,false);std::vector<float> rh(h.begin(),h.begin()+nt*FF);
   for(int arm=1;arm<=2;arm++){run(arm,it,nt,false);if(std::memcmp(rh.data(),h.data(),nt*FF*4)){printf("R4_BITS_FAIL,%d,%d,%d,%d,%d,%d\\n",gt,lp,nt,arm,it.layer,it.expert);require(false,"old_vs_v2_bits");}}
  }
  printf("R4_BITS,%d,%d,%d,0\\n",gt,lp,nt);
  for(int arm=1;arm<arms;arm++){
   double maxH=0,maxDiffH=0,maxO=0,maxDiffO=0;size_t diffH=0,diffO=0;
   for(const auto& it:items){run(0,it,nt,true);std::vector<float> rh(h.begin(),h.begin()+nt*FF),ro(out.begin(),out.begin()+nt*H);run(arm,it,nt,true);
    for(int k=0;k<nt*FF;k++){require(std::isfinite(h[k])&&std::isfinite(rh[k]),"finite_h");maxH=std::max(maxH,std::fabs(double(rh[k])));maxDiffH=std::max(maxDiffH,std::fabs(double(rh[k])-h[k]));if(std::memcmp(&rh[k],&h[k],4))diffH++;}
    for(int k=0;k<nt*H;k++){require(std::isfinite(out[k])&&std::isfinite(ro[k]),"finite_out");maxO=std::max(maxO,std::fabs(double(ro[k])));maxDiffO=std::max(maxDiffO,std::fabs(double(ro[k])-out[k]));if(std::memcmp(&ro[k],&out[k],4))diffO++;}
   }
   printf("NUMERIC,%d,%d,%d,%d,%.9g,%.9g,%zu,%.9g,%.9g,%zu\\n",gt,lp,nt,arm,maxH,maxDiffH,diffH,maxO,maxDiffO,diffO);
   require(maxDiffH<=1e-4*std::max(1.,maxH),"h_numeric_screen");
  }
  for(int full=0;full<2;full++){
   std::vector<double> times[4];for(int arm=0;arm<arms;arm++)for(const auto& it:items)run(arm,it,nt,full!=0);
   for(int r=0;r<5;r++)for(int k=0;k<arms;k++){int arm=(r+k)%arms;double t=now();for(const auto& it:items)run(arm,it,nt,full!=0);double us=(now()-t)/items.size();times[arm].push_back(us);printf("RAW,%d,%d,%d,%d,%d,%d,%.6f\\n",gt,lp,nt,full,r,arm,us);}
   for(int arm=1;arm<arms;arm++)printf("SUM,%d,%d,%d,%d,%d,%.6f,%.6f,%.6f\\n",gt,lp,nt,full,arm,med(times[0]),med(times[arm]),med(times[0])/med(times[arm]));
  }
 }
 printf("DONE,%d,%d\\n",gt,lp);return 0;
}
'''
(R/'bench.cpp').write_text(s,encoding='utf-8')
