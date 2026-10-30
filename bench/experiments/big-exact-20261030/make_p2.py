from pathlib import Path
R=Path(__file__).resolve().parent;D=R.parent/'big-lut-20261030';D.mkdir(exist_ok=True)
s=(R/'bench.cpp').read_text()
s=s.replace('extern "C" void p1_dot(int,int,bool,const unsigned char*,size_t,int,const void*const*,float*);','extern "C" void p2_init();\nextern "C" void p2_prepare(int,const void*const*);\nextern "C" void p2_gu(int,const unsigned char*,size_t,size_t,float*const*);')
s=s.replace('require(gt==21,"prototype_type21_only");','require(gt==16,"prototype_type16_only");p2_init();')
a=s.index('   p1_dot(');b=s.index('\n  }',a)
s=s[:a]+'''   p2_gu(nt,it.native,it.fmt.gu_row,it.fmt.up_off,fp);'''+s[b:]
a=s.index(' for(int nt=1;');s=s[:a]+'''
 for(int nt=2;nt<=3;nt++){
  p2_prepare(nt,ap);
  for(const auto& it:items){run(0,it,nt,true);std::vector<float> rh(h.begin(),h.begin()+nt*FF),ro(out.begin(),out.begin()+nt*H);run(1,it,nt,true);
   if(std::memcmp(rh.data(),h.data(),nt*FF*4)||std::memcmp(ro.data(),out.data(),nt*H*4)){printf("BITS_FAIL,%d,%d,%d,%d,%d\\n",gt,lp,nt,it.layer,it.expert);require(false,"p2_bits");}
  }
  printf("P2_BITS,%d,%d,%d,0\\n",gt,lp,nt);
  for(int ne: {1,4,8})for(int full=0;full<2;full++){
   std::vector<double> ts[2];
   for(int r=-1;r<5;r++)for(int k=0;k<2;k++){
    int arm=(r+k+2)%2;double t=now();
    for(size_t start=0;start<items.size();start+=ne){if(arm)p2_prepare(nt,ap);for(size_t i=start;i<std::min(items.size(),start+ne);i++)run(arm,items[i],nt,full!=0);}
    double us=(now()-t)/items.size();if(r>=0){ts[arm].push_back(us);printf("RAW,%d,%d,%d,%d,%d,%d,%.6f\\n",lp,nt,ne,full,r,arm,us);}
   }
   printf("P2_SUM,%d,%d,%d,%d,%.6f,%.6f,%.6f\\n",lp,nt,ne,full,med(ts[0]),med(ts[1]),med(ts[0])/med(ts[1]));
  }
 }
 printf("DONE,%d,%d\\n",gt,lp);return 0;
}
'''
(D/'bench.cpp').write_text(s)
p=(R/'prepare.py').read_text().replace("prefix+(R/'kernel_tail.cpp').read_text()","prefix+'} }\\n'+(R/'p2_tail.cpp').read_text()")
(D/'prepare.py').write_text(p)
(D/'p2_tail.cpp').write_text((R/'p2_tail.cpp').read_text())
(D/'build.cmd').write_text((R/'build.cmd').read_text().replace('p1bench','p2bench'))
c=(R/'controller.py').read_text().replace('p1bench.exe','p2bench.exe').replace("str(lp),'21'","str(lp),'16'").replace("'DONE,21,'","'DONE,16,'")
(D/'controller.py').write_text(c)
