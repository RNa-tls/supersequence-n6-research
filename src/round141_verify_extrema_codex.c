/* Independent port-prefix extreme enumeration, literal tuple geometry. */
#define main unused_marked_main
#include "verify_round139_marked_return_codex.c"
#undef main
static int goal141,D141,pth141[120],np141,stopped141;
static long long nn141,leaf141,cap141=20000000000LL;
static void port141(int v,int runlen,int closed){
 if(stopped141)return;if(++nn141>cap141){stopped141=1;return;}
 if(np141==goal141){
  if(closed+5-runlen<=D141){if(leaf141++)putchar(',');putchar('[');
   for(int i=0;i<np141;i++){if(i)putchar(',');printf("%d",pth141[i]);}putchar(']');}
  return;
 }
 int t=ew[v];
 if(runlen<5&&!usedh[he[t]]){
  usedh[he[t]]=1;pth141[np141++]=t;port141(t,runlen+1,closed);np141--;usedh[he[t]]=0;
 }
 int nd=closed+5-runlen;if(nd>D141)return;
 for(int j=0;j<deg[v]&&!stopped141;j++)if(wt[v][j]==3){t=adj[v][j];int q=oq[t];
  if(usedq[q]||usedh[he[t]])continue;
  usedq[q]=1;usedh[he[t]]=1;pth141[np141++]=t;port141(t,1,nd);np141--;usedh[he[t]]=0;usedq[q]=0;
 }
}
int main(int argc,char**argv){
 if(argc<3)return 3;goal141=atoi(argv[1]);D141=atoi(argv[2]);if(argc>3)cap141=atoll(argv[3]);
 if(goal141<1||goal141>=120)return 3;MODE=0;init();
 usedq[oq[0]]=1;usedh[he[0]]=1;pth141[0]=0;np141=1;
 printf("{\"target\":%d,\"deficit\":%d,\"paths\":[",goal141,D141);port141(0,1,0);
 printf("],\"nodes\":%lld,\"count\":%lld,\"capped\":%s}\n",nn141,leaf141,stopped141?"true":"false");
 return stopped141?2:0;
}
