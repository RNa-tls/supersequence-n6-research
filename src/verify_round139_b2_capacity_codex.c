/* Independent R115 N*(b,0,8), whole-run representation. Literal geometry is
   from the independent verifier, not R115. All non-E phase jumps cost one,
   including jumps that are only relaxed and not literal joints. */
#define main unused_marked_main
#include "verify_round139_marked_return_codex.c"
#undef main
typedef struct {int v[5],n,cost;} Option;
static Option opts[720][200];static int nopts[720],counts[720],usedorbits,limitb,bestb,witb[120],bpath[120],blen;
static long long bnodes,bcap=20000000000LL;static int bcapped;
static void generate(int start,Option r){
 if(nopts[start]>=200)abort();opts[start][nopts[start]++]=r;
 if(r.n==5)return;int v=r.v[r.n-1],t=ew[v];
 for(int k=0;k<4;k++,t=ew[t]){
  int extra=(k!=0),ok=1;if(r.cost+extra>limitb)continue;
  for(int j=0;j<r.n;j++)if(r.v[j]==t)ok=0;if(!ok)continue;
  Option s=r;s.v[s.n++]=t;s.cost+=extra;generate(start,s);
 }
}
static void whole(int start,int spent,int deficit){
 if(bcapped)return;if(++bnodes>bcap){bcapped=1;return;}
 int q=oq[start],fresh=(counts[q]==0);
 for(int i=0;i<nopts[start]&&!bcapped;i++){
  Option*r=&opts[start][i];int cost=spent+r->cost;if(cost>limitb)continue;int ok=1;
  for(int j=0;j<r->n;j++)if(usedh[he[r->v[j]]])ok=0;if(!ok)continue;
  int d=deficit+(fresh?5:0)-r->n;counts[q]+=r->n;usedorbits+=fresh;
  for(int j=0;j<r->n;j++){usedh[he[r->v[j]]]=1;bpath[blen++]=r->v[j];}
  if(d<=8&&blen>bestb){bestb=blen;memcpy(witb,bpath,blen*sizeof(int));}
  /* Future fresh runs add nonnegative final deficit. Each paid re-entry
     can erase at most the present deficit of one old orbit. Erasing the
     largest such deficits, even if unreachable, is optimistic. */
  int first=0,second=0;
  for(int z=0;z<720;z++)if(counts[z]){int x=5-counts[z];if(x>first){second=first;first=x;}else if(x>second)second=x;}
  int repair=(cost<limitb?first:0)+(cost+1<limitb?second:0);
  if(d-repair<=8){int last=r->v[r->n-1];
   for(int j=0;j<deg[last];j++)if(wt[last][j]==3){
    int t=adj[last][j],nq=oq[t],repeat=(counts[nq]>0);
    if(cost+repeat<=limitb&&!usedh[he[t]])whole(t,cost+repeat,d);
   }
  }
  for(int j=0;j<r->n;j++)usedh[he[r->v[j]]]=0;blen-=r->n;counts[q]-=r->n;usedorbits-=fresh;
 }
}
int main(int argc,char**argv){limitb=argc>1?atoi(argv[1]):2;if(argc>2)bcap=atoll(argv[2]);MODE=0;init();
 for(int i=0;i<720;i++){Option r={.v={i},.n=1,.cost=0};generate(i,r);}whole(0,0,0);
 printf("{\"b\":%d,\"g\":0,\"s\":8,\"passes\":%d,\"nodes\":%lld,\"capped\":%s,\"witness\":[",limitb,bestb,bnodes,bcapped?"true":"false");
 for(int i=0;i<bestb;i++){if(i)printf(",");printf("%d",witb[i]);}puts("]}");return bcapped?2:0;}
