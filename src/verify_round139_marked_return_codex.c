/* Independent WHOLE-RUN search. Literal lookup geometry, boolean hex marks,
   precomputed intra-orbit paths; does not include the producer or R115. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static int words[720][6],ew[720],he[720],oq[720],adj[720][32],wt[720][32],deg[720];
static unsigned char usedh[720],usedq[720];
typedef struct {int n,v[5],x;} Run;
static Run runs[720][40];static int nr[720],MODE,best[2][9],plen,phase[720];
static long long nodes,accepted[2][9],cap=20000000000LL;static int stopped;
static int lookup(int*x){for(int i=0;i<720;i++)if(!memcmp(x,words[i],6*sizeof(int)))return i;abort();}
static void pathgen(int start,Run r){
 if(nr[start]>=40)abort();runs[start][nr[start]++]=r;
 if(r.n==5)return;int v=r.v[r.n-1],next[2]={ew[v],ew[ew[v]]};
 for(int i=0;i<(MODE==1&&r.x==0?2:1);i++){
  int ok=1;for(int j=0;j<r.n;j++)if(r.v[j]==next[i])ok=0;if(!ok)continue;
  Run s=r;s.v[s.n++]=next[i];s.x+=i;pathgen(start,s);
 }
}
static void init(void){
 int p[6]={0,1,2,3,4,5},ix=0;
 do{memcpy(words[ix++],p,sizeof p);int i=4;while(i>=0&&p[i]>=p[i+1])--i;if(i<0)break;
 int j=5;while(p[j]<=p[i])--j;int t=p[i];p[i]=p[j];p[j]=t;
 for(int a=i+1,b=5;a<b;a++,b--){t=p[a];p[a]=p[b];p[b]=t;}}while(ix<720);
 for(int i=0;i<720;i++){
  int *w=words[i],t[6]={w[1],w[2],w[3],w[4],w[0],w[5]};ew[i]=lookup(t);
  int h=i,q=i;memcpy(t,w,sizeof t);
  for(int k=0;k<6;k++){int r=lookup(t);if(r<h)h=r;int x=t[0];memmove(t,t+1,5*sizeof(int));t[5]=x;}
  memcpy(t,w,sizeof t);
  for(int k=0;k<5;k++){int r=lookup(t);if(r<q)q=r;int x=t[0];memmove(t,t+1,4*sizeof(int));t[4]=x;}
  he[i]=h;oq[i]=q;
  int end[6]={w[5],w[0],w[1],w[2],w[3],w[4]};
  /* Generate tails by ordered selections of the removed prefix, not by
     the producer's scan over all candidate endpoint permutations. */
  for(int weight=3;weight<=4;weight++)for(int a=0;a<weight;a++)for(int b=0;b<weight;b++)
   for(int c=0;c<weight;c++)for(int d=0;d<(weight==4?weight:1);d++){
    if(a==b||a==c||b==c||(weight==4&&(d==a||d==b||d==c)))continue;
    int tail[4]={end[a],end[b],end[c],end[d]},raw[10];memcpy(raw,end,sizeof end);memcpy(raw+6,tail,weight*sizeof(int));
    int legal=1;for(int j=1;j<weight;j++){int seen=0;for(int k=0;k<6;k++)seen|=1<<raw[j+k];if(seen==63)legal=0;}
    if(!legal)continue;int dest=lookup(raw+weight);
    int j=deg[i]++;adj[i][j]=dest;wt[i][j]=weight;
   }
 }
 /* oq[] for a target used above may not have been initialized yet. Rebuild
    inter-orbit filtering once all representatives exist. */
 for(int i=0;i<720;i++){int n=0;for(int j=0;j<deg[i];j++)if(oq[adj[i][j]]!=oq[i]){adj[i][n]=adj[i][j];wt[i][n++]=wt[i][j];}deg[i]=n;}
 memset(phase,-1,sizeof phase);int v=0;for(int j=0;j<5;j++){phase[v]=j;v=ew[v];}
 for(int i=0;i<720;i++){Run r={.n=1,.v={i},.x=0};pathgen(i,r);}
 for(int i=0;i<2;i++)for(int d=0;d<9;d++)best[i][d]=-1;
}
static void enumerate(int start,int closeddef,int token,int stage,int rootcount){
 if(stopped)return;if(++nodes>cap){stopped=1;return;}
 int root=oq[0],q=oq[start];if(q!=root&&usedq[q])abort();if(q!=root)usedq[q]=1;
 for(int ri=0;ri<nr[start]&&!stopped;ri++){
  Run *r=&runs[start][ri];int nt=token+r->x;if(nt>1)continue;int ok=1;
  for(int j=0;j<r->n;j++)if(usedh[he[r->v[j]]])ok=0;
  if(!ok)continue;
  if(stage==0){for(int j=0;j<r->n;j++)if(phase[r->v[j]]==4)ok=0;if(!ok)continue;}
  int last=r->v[r->n-1];
  if(stage==2){if(phase[last]!=4)continue;int d=closeddef+5-rootcount-r->n;if(d>8)continue;
   accepted[nt][d]++;if(plen+r->n>best[nt][d])best[nt][d]=plen+r->n;continue;}
  int nd=closeddef+(q==root?0:5-r->n);if(nd>8)continue;
  for(int j=0;j<r->n;j++)usedh[he[r->v[j]]]=1;plen+=r->n;
  for(int j=0;j<deg[last];j++){
   int t=adj[last][j],nq=oq[t],heavy=(wt[last][j]==4);
   if(heavy&&MODE!=2)continue;if(nt+heavy>1||usedh[he[t]])continue;
   if(nq==root&&stage!=0)enumerate(t,nd,nt+heavy,2,rootcount);
   else if(!usedq[nq]&&nq!=root)enumerate(t,nd,nt+heavy,1,stage==0?r->n:rootcount);
  }
  plen-=r->n;for(int j=0;j<r->n;j++)usedh[he[r->v[j]]]=0;
 }
 if(q!=root)usedq[q]=0;
}
int main(int argc,char**argv){MODE=argc>1?atoi(argv[1]):0;if(argc>2)cap=atoll(argv[2]);init();enumerate(0,0,0,0,0);
 printf("{\"mode\":%d,\"nodes\":%lld,\"capped\":%s,\"rows\":[",MODE,nodes,stopped?"true":"false");
 for(int i=0;i<2;i++)for(int d=0;d<9;d++){if(i||d)printf(",");printf("{\"token\":%d,\"deficit\":%d,\"passes\":%d,\"accepted\":%lld}",i,d,best[i][d],accepted[i][d]);}
 puts("]}");return stopped?2:0;}
