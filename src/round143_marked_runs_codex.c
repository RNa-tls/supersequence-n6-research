/* Whole-E-run marked capacities. Necessary relaxation, NOT a literal cover DFS.
   b = number of non-E entries into previously used orbits (includes same Q).
   D = 5*openedQ - entries; all hexagons distinct inside a piece.
   C and D dirty shadows have external-history obligations relaxed.
   argv: b D node_cap [mode=A|AB] [target_passes extrema.jsonl]
*/
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <inttypes.h>
static int pp[720][6],qn[720],hn[720],en[720],paid[720][5];
static int count=0,used[6],tmp[6],uq[144],uh[120],path[721],bestpath[721];
static int bcap,dcap,modeab=1,capflag=0,best=0,target=0;
static int first_run_length=0,endpoint_best[4];
static int rich_best[50],run_depth=0;
static int acap=0,usedA=0,port_seen[720];
static uint64_t nodes=0,limit=0,accepts=0,digest=UINT64_C(1469598103934665603),extrema=0;
static FILE *exportf=NULL;
static void perm(int d){if(d==6){memcpy(pp[count++],tmp,sizeof tmp);return;}for(int x=0;x<6;x++)if(!used[x]){used[x]=1;tmp[d]=x;perm(d+1);used[x]=0;}}
static int id(const int *p){int v=0;for(int i=0;i<6;i++){int less=0;for(int j=i+1;j<6;j++)less+=p[j]<p[i];v=v*(6-i)+less;}return v;}
static void init(void){
 perm(0);int qt[720],ht[720],nq=0,nh=0;for(int v=0;v<720;v++)qt[v]=ht[v]=-1;
 for(int v=0;v<720;v++){
  int qmin=720,hmin=720,p[6],s[6],tail[5][3]={{1,2,0},{2,0,1},{2,1,0},{0,2,1},{1,0,2}};
  for(int k=0;k<5;k++){for(int j=0;j<5;j++)p[j]=pp[v][(j+k)%5];p[5]=pp[v][5];int z=id(p);if(z<qmin)qmin=z;}
  for(int k=0;k<6;k++){for(int j=0;j<6;j++)p[j]=pp[v][(j+k)%6];int z=id(p);if(z<hmin)hmin=z;}
  if(qt[qmin]<0)qt[qmin]=nq++;if(ht[hmin]<0)ht[hmin]=nh++;
  qn[v]=qt[qmin];hn[v]=ht[hmin];for(int j=0;j<5;j++)p[j]=pp[v][(j+1)%5];p[5]=pp[v][5];en[v]=id(p);
  s[0]=pp[v][5];for(int j=1;j<6;j++)s[j]=pp[v][j-1];
  for(int t=0;t<5;t++){for(int j=0;j<3;j++)p[j]=s[j+3];for(int j=0;j<3;j++)p[j+3]=s[tail[t][j]];paid[v][t]=id(p);}
 }
 if(nq!=144||nh!=120){fprintf(stderr,"geometry count\n");exit(2);}
}
static void hashstep(uint64_t x){digest^=x;digest*=UINT64_C(1099511628211);}
static void rec(int v,int b,int D,int len,int allow_old_start){
 if(capflag)return;if(limit&&nodes>=limit){capflag=1;return;}nodes++;
 hashstep((uint64_t)v+720u*(b+16u*(D+80u*len)));
 hashstep((uint64_t)usedA);
 int q=qn[v],old=uq[q]>0,nb=b+old;if(nb>bcap)return;
 int nd=D+(old?0:5);uq[q]++;run_depth++;int taken[5],ptaken[5],n=0,np=0,u=v;
 for(int r=1;r<=5;r++){
  if(port_seen[u] || (uh[hn[u]] && !(r==1&&allow_old_start)))break;
  port_seen[u]=1;ptaken[np++]=u;
  if(!uh[hn[u]]){uh[hn[u]]=1;taken[n++]=hn[u];}
  path[len+r-1]=u;nd--;
  if(len==0)first_run_length=r;
  if(nd<=dcap && usedA==acap){accepts++;if(len+r>best){best=len+r;memcpy(bestpath,path,best*sizeof(int));}
   int mask=(first_run_length<5?1:0)|(r<5?2:0);if(len+r>endpoint_best[mask])endpoint_best[mask]=len+r;
   int rich=(first_run_length-1)*5+(r-1)+(run_depth==1?25:0);if(len+r>rich_best[rich])rich_best[rich]=len+r;
   if(target&&len+r==target){extrema++;if(exportf){fprintf(exportf,"[");for(int j=0;j<target;j++)fprintf(exportf,"%s%d",j?",":"",path[j]);fprintf(exportf,"]\n");}}
  }
  /* After ending this run, each remaining paid re-entry can fill at most4
     missing ports; new orbits add nonnegative final deficit. Overestimation
     of repairs makes this a safe necessary bound, including repeated q0. */
  if((!target||len+r<target)&&nd-4*(bcap-nb)<=dcap){
   for(int j=0;j<(modeab?5:4);j++){int t=paid[u][j];if(!uh[hn[t]]&&(nb+(uq[qn[t]]>0)<=bcap))rec(t,nb,nd,len+r,0);if(capflag)break;}
   if(!capflag && usedA<acap){int p[6];for(int j=0;j<6;j++)p[j]=pp[u][(j+1)%6];int t=id(p);
    if(!port_seen[t] && nb+(uq[qn[t]]>0)<=bcap){usedA++;rec(t,nb,nd,len+r,1);usedA--;}}
  }
  if(capflag)break;u=en[u];
 }
 for(int j=0;j<n;j++)uh[taken[j]]=0;for(int j=0;j<np;j++)port_seen[ptaken[j]]=0;uq[q]--;run_depth--;
}
int main(int argc,char **argv){
 if(argc<4){fprintf(stderr,"b D node_cap [A|AB] [target file]\n");return 2;}
 bcap=atoi(argv[1]);dcap=atoi(argv[2]);limit=strtoull(argv[3],NULL,10);if(argc>4)modeab=strcmp(argv[4],"A")!=0;
 if(argc>4 && strncmp(argv[4],"SIGMA:",6)==0)acap=atoi(argv[4]+6);
 if(argc>5){target=atoi(argv[5]);if(argc<7)return 2;exportf=fopen(argv[6],"wb");if(!exportf)return 2;}
 if(bcap<0||dcap<0||bcap>20||dcap>120)return 2;init();
 /* Initial block opens its orbit without consuming b. */
 rec(0,0,0,0,0);if(exportf)fclose(exportf);
 printf("{\"A_exact\":%d,",acap);
 printf("\"implementation\":\"whole-E-runs\",\"mode\":\"%s\",\"b\":%d,\"D\":%d,\"nodes\":%" PRIu64 ",\"capped\":%s,\"completed\":%s,\"max_passes\":%d,\"accepted_prefixes\":%" PRIu64 ",\"extrema\":%" PRIu64 ",\"transcript_fnv64\":\"%016" PRIx64 "\",\"witness\":[",modeab?"AB":"A",bcap,dcap,nodes,capflag?"true":"false",capflag?"false":"true",best,accepts,extrema,digest);
 for(int j=0;j<best;j++)printf("%s%d",j?",":"",bestpath[j]);printf("],\"endpoint_max_passes\":[%d,%d,%d,%d],\"rich_endpoint_max_passes\":[",endpoint_best[0],endpoint_best[1],endpoint_best[2],endpoint_best[3]);for(int j=0;j<50;j++)printf("%s%d",j?",":"",rich_best[j]);printf("]}\n");return 0;
}
