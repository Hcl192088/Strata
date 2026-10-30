// Inverse of the pinned direct repackers. Original packed codes must roundtrip byte-for-byte.
static uint8_t inverse_sign[128];
static void init_inverse(){static bool done=false;if(done)return;bool seen[128]={};for(int i=0;i<128;i++){int j=scrambled_sign(i);GGML_ASSERT(j<128&&!seen[j]);seen[j]=true;inverse_sign[j]=(uint8_t)i;}done=true;}
extern "C" void r4_unpack(int type,int h,int rows,const void* src,void* dst){
 init_inverse();const int nb=h/256;
 for(int r=0;r<rows;r+=4)for(int b=0;b<nb;b++)for(int k=0;k<4;k++){
  const int oi=(r+k)*nb+b,pi=(r/4)*nb+b;
  if(type==16){
   const auto& p=((const block_iq2_xxs_r4*)src)[pi];auto& o=((block_iq2_xxs*)dst)[oi];o.d=p.d[k];
   for(int j=0;j<8;j++){uint8_t q[4];for(int i=0;i<4;i++)q[i]=p.qs[16*j+4*k+i];std::memcpy(o.qs+4*j,q,4);
    uint32_t sas;std::memcpy(&sas,p.sas+4*(4*j+k),4);uint32_t z=0;for(int i=0;i<4;i++){uint8_t v=(uint8_t)(sas>>(8*i));z|=(uint32_t)inverse_sign[v>>1]<<(7*i);z|=(uint32_t)(v&1)<<(28+i);}std::memcpy(o.qs+4*j+2,&z,4);}
  }else if(type==17){
   const auto& p=((const block_iq2_xs_r4*)src)[pi];auto& o=((block_iq2_xs*)dst)[oi];o.d=p.d[k];
   for(int j=0;j<8;j++){o.scales[j]=p.scales[4*j+k];for(int i=0;i<4;i++){uint16_t v=p.qs[16*j+4*k+i];o.qs[4*j+i]=(v&511)|((uint16_t)inverse_sign[v>>9]<<9);}}
  }else if(type==22){
   const auto& p=((const block_iq2_s_r4*)src)[pi];auto& o=((block_iq2_s*)dst)[oi];o.d=p.d[k];
   for(int j=0;j<8;j++){o.scales[j]=p.scales[4*j+k];o.qh[j]=p.qh[4*j+k];for(int i=0;i<4;i++){o.qs[4*j+i]=p.qs[16*j+4*k+i];o.qs[32+4*j+i]=p.signs[16*j+4*k+i];}}
  }else if(type==18){
   const auto& p=((const block_iq3_xxs_r4*)src)[pi];auto& o=((block_iq3_xxs*)dst)[oi];o.d=p.d[k];
   for(int j=0;j<8;j++){for(int i=0;i<8;i++)o.qs[8*j+i]=p.qs[32*j+8*k+i];uint32_t sas;std::memcpy(&sas,p.sas+4*(4*j+k),4);uint32_t z=0;for(int i=0;i<4;i++){uint8_t v=(uint8_t)(sas>>(8*i));z|=(uint32_t)inverse_sign[v>>1]<<(7*i);z|=(uint32_t)(v&1)<<(28+i);}std::memcpy(o.qs+64+4*j,&z,4);}
  }else if(type==21){
   const auto& p=((const block_iq3_s_r4*)src)[pi];auto& o=((block_iq3_s*)dst)[oi];o.d=p.d[k];std::memset(o.signs,0,32);
   for(int j=0;j<4;j++){int z=8*j+k;int lo=(p.scales[(z+0)%16]>>(4*((z+0)/16)))&15,hi=(p.scales[(z+4)%16]>>(4*((z+4)/16)))&15;o.scales[j]=(uint8_t)(lo|(hi<<4));}
   for(int j=0;j<8;j++){o.qh[j]=p.qh[4*j+k];for(int i=0;i<4;i++){o.qs[8*j+i]=p.qs[32*j+k+8*i];o.qs[8*j+i+4]=p.qs[32*j+k+8*i+4];uint8_t s=p.signs[16*j+4*k+i];for(int t=0;t<4;t++){o.signs[4*j+t]|=((s>>(2*t))&1)<<i;o.signs[4*j+t]|=((s>>(2*t+1))&1)<<(4+i);}}}
  }else std::abort();
 }
}
