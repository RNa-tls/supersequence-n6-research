/* Independent port-by-port root-return enumeration. No R115 source include.
   Literal permutations and joints are generated directly. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static int words[720][6], ew[720], he[720], oq[720], bc[720][2];
static unsigned char usedh[720],usedq[720];
static int best[14],rootphase[720],path[120],plen,root,rootprefix;
static long long nodes,accepted[14];
static int lookup(int*x){for(int i=0;i<720;i++)if(!memcmp(x,words[i],6*sizeof(int)))return i;abort();}
static void init(void){
 int p[6]={0,1,2,3,4,5},ix=0;
 do {memcpy(words[ix++],p,sizeof p);int i=4;while(i>=0&&p[i]>=p[i+1])--i;if(i<0)break;
 int j=5;while(p[j]<=p[i])--j;int t=p[i];p[i]=p[j];p[j]=t;
 for(int a=i+1,b=5;a<b;a++,b--){t=p[a];p[a]=p[b];p[b]=t;}}while(ix<720);
 for(int i=0;i<720;i++){
  int *w=words[i],t[6]={w[1],w[2],w[3],w[4],w[0],w[5]};ew[i]=lookup(t);
  int h=i,q=i;memcpy(t,w,sizeof t);
  for(int k=0;k<6;k++){int r=lookup(t);if(r<h)h=r;int x=t[0];memmove(t,t+1,5*sizeof(int));t[5]=x;}
  memcpy(t,w,sizeof t);
  for(int k=0;k<5;k++){int r=lookup(t);if(r<q)q=r;int x=t[0];memmove(t,t+1,4*sizeof(int));t[4]=x;}
  he[i]=h;oq[i]=q;
  /* Endpoint of full pass is (w5,w0,w1,w2,w3,w4).
     Append 201 / 210, retaining the endpoint suffix of length three. */
  int a[6]={w[2],w[3],w[4],w[1],w[5],w[0]};bc[i][0]=lookup(a);
  int b[6]={w[2],w[3],w[4],w[1],w[0],w[5]};bc[i][1]=lookup(b);
 }
 memset(rootphase,-1,sizeof rootphase);int v=0;
 for(int i=0;i<5;i++){rootphase[v]=i;v=ew[v];}root=oq[0];
 for(int d=0;d<14;d++)best[d]=-1;
}
static void finish(int v,int deficit){
 int phase=rootphase[v];if(phase<rootprefix)return;
 int d=deficit+phase-rootprefix;if(d>13)return;
 int count=0;
 for(int j=phase;j<5;j++){if(usedh[he[v]])return;count++;v=ew[v];}
 accepted[d]++;if(plen+count>best[d])best[d]=plen+count;
}
static void step(int v,int runlen,int closeddef){
 nodes++;if(usedh[he[v]])return;
 usedh[he[v]]=1;path[plen++]=v;
 /* This is a port-level traversal: extending a run is a recursive edge. */
 if(runlen<5)step(ew[v],runlen+1,closeddef);
 int d=closeddef+5-runlen;
 if(d<=13)for(int k=0;k<2;k++){
  int t=bc[v][k],q=oq[t];
  if(q==root)finish(t,d);
  else if(!usedq[q]&&!usedh[he[t]]){usedq[q]=1;step(t,1,d);usedq[q]=0;}
 }
 plen--;usedh[he[v]]=0;
}
int main(void){
 init();usedq[root]=1;
 for(rootprefix=1;rootprefix<5;rootprefix++){
  memset(usedh,0,sizeof usedh);plen=0;int v=0,last=0;
  for(int j=0;j<rootprefix;j++){usedh[he[v]]=1;path[plen++]=v;last=v;v=ew[v];}
  for(int k=0;k<2;k++){int t=bc[last][k],q=oq[t];if(q!=root&&!usedh[he[t]]){usedq[q]=1;step(t,1,0);usedq[q]=0;}}
 }
 printf("{\"schema\":\"independent-port-root-return/1\",\"nodes\":%lld,\"capped\":false,\"rows\":[",nodes);
 for(int d=0;d<14;d++){if(d)printf(",");printf("{\"deficit\":%d,\"passes\":%d,\"accepted\":%lld}",d,best[d],accepted[d]);}
 puts("]}");return 0;
}
