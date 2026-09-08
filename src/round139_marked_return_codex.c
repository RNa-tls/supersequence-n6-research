/* Full-pass root-return model, exactly two root runs, normalized endpoints
   phase 0 and phase 4. At most one x OR one heavy w4; all nonroot runs fresh.
   Port-level enumeration; includes R115 geometry but NOT its DFS/pruning. */
#define main unused115
#include "chain_capacity_115.c"
#undef main
static int adj[720][32],weights[720][32],degree[720];
static int MODE,DS=8,path[120],plen,best139[2][9],wit139[2][9][120];
static long long visits139,accepted139[2][9],cap139=20000000000LL;
static int stop139;
static void joints139(void){
 for(int v=0;v<720;v++){
  int y[6];y[0]=perm[v][5];for(int j=1;j<6;j++)y[j]=perm[v][j-1];
  for(int t=0;t<720;t++){
   int w=1;for(;w<6;w++)if(!memcmp(y+w,perm[t],(6-w)*sizeof(int)))break;
   if(w<2||w>4)continue;
   int raw[10];memcpy(raw,y,6*sizeof(int));memcpy(raw+6,perm[t]+6-w,w*sizeof(int));
   int legal=1;
   for(int a=1;a<w;a++){int bits=0;for(int b=0;b<6;b++)bits|=1<<raw[a+b];if(bits==63)legal=0;}
   if(legal){int j=degree[v]++;adj[v][j]=t;weights[v][j]=w;if(degree[v]>32)abort();}
  }
 }
}
static void walk139(int v,int returning,int spent,int token){
 if(stop139)return;
 if(++visits139>cap139){stop139=1;return;}
 int q=orbid[v],root=orbid[0],mask=omask[q];
 if((HLO&hlo[v])||(HHI&hhi[v])||mask>>phse[v]&1)abort();
 omask[q]|=1<<phse[v];HLO|=hlo[v];HHI|=hhi[v];path[plen++]=v;
 if(returning&&phse[v]==4){
  int d=spent+5-__builtin_popcount(omask[root]);
  if(d<=DS){accepted139[token][d]++;if(plen>best139[token][d]){best139[token][d]=plen;memcpy(wit139[token][d],path,plen*sizeof(int));}}
 }else if(!(q==root&&!returning&&(omask[root]&16))){
  for(int j=0;j<degree[v];j++){
   int t=adj[v][j],nq=orbid[t],w=weights[v][j],extra=0;
   if((HLO&hlo[t])||(HHI&hhi[t]))continue;
   if(nq==q){if(w==4)continue;if(w==3){if(MODE!=1)continue;extra=1;}}
   else {if(w==2)abort();if(w==4){if(MODE!=2)continue;extra=1;}}
   if(token+extra>1)continue;
   if(returning&&nq!=root)continue;
   if(nq!=q&&omask[nq]&&nq!=root)continue;
   if(nq!=q&&nq==root&&returning)continue;
   int d=spent+(nq!=q&&q!=root?5-__builtin_popcount(omask[q]):0);
   if(d>DS)continue;
   walk139(t,returning||(nq==root&&q!=root),d,token+extra);
  }
 }
 --plen;HLO&=~hlo[v];HHI&=~hhi[v];omask[q]=mask;
}
int main(int argc,char**argv){
 MODE=argc>1?atoi(argv[1]):0;if(argc>2)cap139=atoll(argv[2]);build();joints139();
 for(int i=0;i<2;i++)for(int d=0;d<=DS;d++)best139[i][d]=-1;
 walk139(0,0,0,0);
 printf("{\"mode\":%d,\"deficit_cap\":8,\"nodes\":%lld,\"node_cap\":%lld,\"capped\":%s,\"rows\":[",MODE,visits139,cap139,stop139?"true":"false");
 for(int i=0;i<2;i++)for(int d=0;d<=DS;d++){
  if(i||d)printf(",");printf("{\"token\":%d,\"deficit\":%d,\"passes\":%d,\"accepted\":%lld,\"witness\":[",i,d,best139[i][d],accepted139[i][d]);
  for(int z=0;z<best139[i][d];z++){if(z)printf(",");printf("%d",wit139[i][d][z]);}printf("]}");
 }puts("]}");return stop139?2:0;
}
