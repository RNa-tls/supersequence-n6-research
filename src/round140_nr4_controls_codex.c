/* Complete normalized literal NR4 controls L<=39. No n6 full walk search. */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
static int p[24][4],adj[24][24],wt[24][24],deg[24],path[24];
static unsigned long long nodes=0,leaves=0,limit=2000000000ULL,hash=1469598103934665603ULL;
static int capped=0;
static int permutation(int *q){unsigned mask=0;for(int i=0;i<4;i++)mask|=1U<<q[i];return mask==15;}
static void visit(int v,uint32_t used,int depth,int length){
 if(++nodes>limit){capped=1;return;}
 if(length+24-depth>39)return;
 if(depth==24){
  int raw[96],len=4;for(int i=0;i<4;i++)raw[i]=p[path[0]][i];
  for(int i=1;i<24;i++){int a=path[i-1],b=path[i],w=wt[a][b];for(int j=4-w;j<4;j++)raw[len++]=p[b][j];}
  if(len!=length)abort();leaves++;
  for(int j=0;j<len;j++){putchar('0'+raw[j]);hash^=(unsigned)raw[j];hash*=1099511628211ULL;}
  putchar('\n');hash^=255;hash*=1099511628211ULL;return;
 }
 for(int i=0;i<deg[v]&&!capped;i++){int t=adj[v][i];if(used&(1U<<t))continue;
  int nl=length+wt[v][t];if(nl+23-depth>39)continue;path[depth]=t;visit(t,used|(1U<<t),depth+1,nl);
 }
}
int main(int argc,char**argv){if(argc>1)limit=strtoull(argv[1],0,10);int k=0;
 for(int a=0;a<4;a++)for(int b=0;b<4;b++)if(b!=a)for(int c=0;c<4;c++)if(c!=a&&c!=b){int d=6-a-b-c;p[k][0]=a;p[k][1]=b;p[k][2]=c;p[k++][3]=d;}
 for(int a=0;a<24;a++)for(int b=0;b<24;b++)if(a!=b){int w=4;
  for(int x=1;x<4;x++){int same=1;for(int j=x;j<4;j++)if(p[a][j]!=p[b][j-x])same=0;if(same){w=x;break;}}
  int raw[8],legal=1;for(int j=0;j<4;j++)raw[j]=p[a][j];for(int j=0;j<w;j++)raw[4+j]=p[b][4-w+j];
  for(int j=1;j<w;j++)if(permutation(raw+j))legal=0;
  wt[a][b]=w;if(legal)adj[a][deg[a]++]=b;
 }
 path[0]=0;visit(0,1,1,4);
 printf("{\"n\":4,\"max_length\":39,\"nodes\":%llu,\"walks\":%llu,\"capped\":%s,\"path_digest_fnv64\":\"%016llx\"}\n",nodes,leaves,capped?"true":"false",hash);
 return capped?2:0;
}
