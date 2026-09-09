/* Complete fixed-length b=0 full-chain domains, not NR6 continuation. */
#define main unused_capacity_main
#include "chain_capacity_115.c"
#undef main
static int target_length,deficit_cap,trail[120],plen141,openq141[144];
static long long nodes141,answers141,cap141=20000000000LL;
static int stopped141;
static void emit141(void){
 if(answers141++)putchar(',');putchar('[');
 for(int i=0;i<plen141;i++){if(i)putchar(',');printf("%d",trail[i]);}putchar(']');
}
static void runs141(int v,int d,uint64_t lo,uint64_t hi){
 if(stopped141)return;if(++nodes141>cap141){stopped141=1;return;}
 int q=orbid[v];if(openq141[q])abort();openq141[q]=1;int begin=plen141,u=v;
 for(int l=1;l<=5;l++,u=word_at[q][(phse[u]+1)%5]){
  if((lo&hlo[u])||(hi&hhi[u]))break;
  lo|=hlo[u];hi|=hhi[u];trail[plen141++]=u;
  if(plen141>target_length)break;
  int nd=d+5-l;if(nd>deficit_cap)continue;
  if(plen141==target_length){emit141();continue;}
  int next[2]={mvW3b[u],mvW3c[u]};
  for(int j=0;j<2&&!stopped141;j++)if(!openq141[orbid[next[j]]])runs141(next[j],nd,lo,hi);
 }
 plen141=begin;openq141[q]=0;
}
int main(int argc,char**argv){
 if(argc<3)return 3;target_length=atoi(argv[1]);deficit_cap=atoi(argv[2]);
 if(argc>3)cap141=atoll(argv[3]);if(target_length<1||target_length>119)return 3;
 build();printf("{\"target\":%d,\"deficit\":%d,\"paths\":[",target_length,deficit_cap);
 runs141(0,0,0,0);
 printf("],\"nodes\":%lld,\"count\":%lld,\"capped\":%s}\n",nodes141,answers141,stopped141?"true":"false");
 return stopped141?2:0;
}
