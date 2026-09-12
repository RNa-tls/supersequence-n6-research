/* Whole-E-block nonpure beta-CYCLE necessary exact-P query.
   One non-E closing joint is checked without appending the root vertex.
   b,D,R unchanged on closure; A/Qs/H include the closing joint.
   All shortest literal full-pass connectors, arbitrary old-hex arrivals paid
   by R. This is not a chronological word search or a sufficiency claim.
   b D cap A Qs R H P export.jsonl [certified_suffix_bounds.txt] */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <inttypes.h>
static int words[720][6],cnt=0,digits[6],used[6],qid[720],hid[720],E[720];
static int nt[720],to[720][720],da[720][720],dq[720][720],dh[720][720];
static int bmax,dmax,amax,qmax,rmax,hmax,P,maxdelta,phase_seen[720],uq[144],uh[120],path[720];
static uint64_t cap,nodes,hits,digest=UINT64_C(1469598103934665603),suffix_prunes;
static int capped=0,bound_enabled=0;static int *ub=NULL;static FILE *out;
static int terminal_port=-1;
static int capacity_mode=0,bestgrid[11][121],gridpath[11][121][151],maximum=0,gridcount=0;
static void fail(const char*s){fprintf(stderr,"%s\n",s);exit(2);}
static void perm(int n){if(n==6){memcpy(words[cnt++],digits,sizeof digits);return;}
 for(int v=0;v<6;v++)if(!used[v]){used[v]=1;digits[n]=v;perm(n+1);used[v]=0;}}
static int rankp(const int*p){int n=0;for(int i=0;i<6;i++){int less=0;for(int j=i+1;j<6;j++)less+=p[j]<p[i];n=n*(6-i)+less;}return n;}
static int boundary[6],tail[6],taken[6],current_v,current_w;
static void tailperm(int n){
 if(n<current_w){for(int j=0;j<current_w;j++)if(!taken[j]){taken[j]=1;tail[n]=boundary[j];tailperm(n+1);taken[j]=0;}return;}
 int t[6],v=current_v,w=current_w;
 for(int j=0;j<6-w;j++)t[j]=boundary[j+w];for(int j=0;j<w;j++)t[6-w+j]=tail[j];
 for(int small=1;small<w;small++){int equal=1;for(int j=0;j<6-small;j++)if(boundary[j+small]!=t[j])equal=0;if(equal)return;}
 int target=rankp(t);if(target==E[v])return;
 int nedge=nt[v]++;to[v][nedge]=target;dh[v][nedge]=w>3?w-3:0;
 da[v][nedge]=(w==2);dq[v][nedge]=0;
 if(w==3){int equal=1;for(int j=0;j<6;j++)if(t[j]!=words[v][(j+2)%6])equal=0;dq[v][nedge]=equal;}
}
static void geometry(void){
 perm(0);int qm[720],hm[720],nq=0,nh=0;for(int v=0;v<720;v++)qm[v]=hm[v]=-1;
 for(int v=0;v<720;v++){
  int minq=720,minh=720,t[6];
  for(int s=0;s<6;s++){for(int j=0;j<6;j++)t[j]=words[v][(j+s)%6];int r=rankp(t);if(r<minh)minh=r;}
  for(int s=0;s<5;s++){for(int j=0;j<5;j++)t[j]=words[v][(j+s)%5];t[5]=words[v][5];int r=rankp(t);if(r<minq)minq=r;}
  if(qm[minq]<0)qm[minq]=nq++;if(hm[minh]<0)hm[minh]=nh++;qid[v]=qm[minq];hid[v]=hm[minh];
  for(int j=0;j<5;j++)t[j]=words[v][(j+1)%5];t[5]=words[v][5];E[v]=rankp(t);
 }
 if(nq!=144||nh!=120)fail("bad geometry");
 for(int v=0;v<720;v++){current_v=v;boundary[0]=words[v][5];for(int j=1;j<6;j++)boundary[j]=words[v][j-1];
  for(current_w=2;current_w<=6&&current_w<=hmax+3;current_w++)tailperm(0);
  int ca=0,cq=0;for(int j=0;j<nt[v];j++){ca+=da[v][j];cq+=dq[v][j];}
  if(ca!=1||cq!=1)fail("incomplete A/B alphabet");
 }
 if(amax>0||qmax>0){int t[6],shift=amax>0?5:4;for(int j=0;j<6;j++)t[j]=words[0][(j+shift)%6];terminal_port=rankp(t);}
}
static size_t indexub(int a,int q,int r,int h,int b,int d){return (((((size_t)a*(qmax+1)+q)*(rmax+1)+r)*(hmax+1)+h)*(bmax+1)+b)*(maxdelta+1)+d;}
static void readbounds(const char *name){
 size_t size=(size_t)(amax+1)*(qmax+1)*(rmax+1)*(hmax+1)*(bmax+1)*(maxdelta+1);
 ub=malloc(size*sizeof(int));if(!ub)fail("bounds allocation failed");for(size_t j=0;j<size;j++)ub[j]=100000;
 FILE*f=fopen(name,"rb");if(!f)fail("missing bounds");int a,q,r,h,b,d,p,n=0;
 while(fscanf(f,"%d %d %d %d %d %d %d",&a,&q,&r,&h,&b,&d,&p)==7){
  if(a<0||q<0||r<0||h<0||b<0||d<0||p<0)fail("negative bound coordinate");
  if(a<=amax&&q<=qmax&&r<=rmax&&h<=hmax&&b<=bmax&&d<=maxdelta)ub[indexub(a,q,r,h,b,d)]=p;n++;
 }
 if(!feof(f)||!n)fail("malformed bounds");fclose(f);bound_enabled=1;
}
static void rec(int start,int length,int b,int D,int a,int q,int R,int H){
 if(capped)return;if(cap&&nodes>=cap){capped=1;return;}nodes++;
 digest^=(uint64_t)start+720u*(length+144u*(b+5u*(a+16u*(q+4u*(R+24u*H)))));digest*=UINT64_C(1099511628211);
 int orbit=qid[start],old=uq[orbit]>0,nb=b+old;if(nb>bmax)return;
 int nd=D+(old?0:5),rr=R,u=start,inserted[5],ni=0;uq[orbit]++;
 for(int run=1;run<=5&&length+run<=P;run++){
  if(phase_seen[u])break;int repeated=uh[hid[u]]>0;if(rr+repeated>rmax)break;
  phase_seen[u]=1;uh[hid[u]]++;inserted[ni++]=u;path[length+run-1]=u;rr+=repeated;nd--;
  if(capacity_mode||length+run==P){
   for(int j=0;j<nt[u];j++)if(to[u][j]==0&&(!(amax>0)||da[u][j])&&(!(amax==0&&qmax>0)||dq[u][j])&&a+da[u][j]==amax&&q+dq[u][j]==qmax&&H+dh[u][j]<=hmax&&nd<=dmax&&rr>=amax+qmax){
    hits++;
    if(capacity_mode){if(length+run>bestgrid[nb][nd]){bestgrid[nb][nd]=length+run;memcpy(gridpath[nb][nd],path,(length+run)*sizeof(int));}if(length+run>maximum)maximum=length+run;}
    else{fprintf(out,"[");for(int z=0;z<P;z++)fprintf(out,"%s%d",z?",":"",path[z]);fprintf(out,"]\n");}
   }
  }
  if(length+run<P&&u==terminal_port){break;}
  if(length+run<P&&nd-4*(bmax-nb)<=dmax){
   for(int j=0;j<nt[u]&&!capped;j++){
    int t=to[u][j],na=a+da[u][j],nq=q+dq[u][j],nh=H+dh[u][j];
    if(na>amax||nq>qmax||nh>hmax||phase_seen[t])continue;
    int oldt=uh[hid[t]]>0,rb=bmax-nb-(uq[qid[t]]>0),ar=amax-na,qr=qmax-nq,rrem=rmax-rr-oldt,hr=hmax-nh;
    if(rb<0||rrem<0)continue;
    int delta=dmax+5*bmax-nd-5*nb;
    int viable=0;
    /* Unknown closing joint: relax over clean w3, A, B, and heavy costs.
       Closing consumes no additional vertex or repeated-hex arrival. */
    for(int closure=0;closure<6;closure++){
     if(amax>0&&closure!=1)continue;
     if(amax==0&&qmax>0&&closure!=2)continue;
     int ca=closure==1,cq=closure==2,ch=closure>=3?closure-2:0;
     int ar2=ar-ca,qr2=qr-cq,hr2=hr-ch;
     if(ar2<0||qr2<0||hr2<0||rrem<ar2+qr2)continue;
     if(!bound_enabled||(delta>=0&&length+run+ub[indexub(ar2,qr2,rrem,hr2,rb,delta)]>=P)){viable=1;break;}
    }
    if(!viable){suffix_prunes++;continue;}
    rec(t,length+run,nb,nd,na,nq,rr,nh);
   }
  }
  if(capped)break;u=E[u];
 }
 for(int j=0;j<ni;j++){int v=inserted[j];phase_seen[v]=0;uh[hid[v]]--;}
 uq[orbit]--;
}
int main(int argc,char**argv){
 if(argc!=10&&argc!=11)fail("usage: b D cap A Qs R H P export [bounds]");
 bmax=atoi(argv[1]);dmax=atoi(argv[2]);cap=strtoull(argv[3],NULL,10);amax=atoi(argv[4]);qmax=atoi(argv[5]);rmax=atoi(argv[6]);hmax=atoi(argv[7]);P=atoi(argv[8]);
 if(bmax<0||bmax>10||dmax<0||dmax>120||amax<0||amax>20||qmax<0||qmax>10||rmax<0||rmax>30||hmax<0||hmax>3||P<0||P>150)fail("invalid arguments");
 if(P==0){capacity_mode=1;P=120+rmax;if(argc==11)fail("capacity mode cannot use exact-P suffix pruning");}
 maxdelta=dmax+5*bmax;FILE*old=fopen(argv[9],"rb");if(old){fclose(old);fail("refuse overwrite");}out=fopen(argv[9],"wb");if(!out)fail("export creation failed");
 if(argc==11)readbounds(argv[10]);geometry();rec(0,0,0,0,0,0,0,0);
 if(capacity_mode)for(int b=0;b<=bmax;b++)for(int d=0;d<=dmax;d++)if(bestgrid[b][d]){
  gridcount++;fprintf(out,"{\"b\":%d,\"D\":%d,\"P\":%d,\"entries\":[",b,d,bestgrid[b][d]);for(int z=0;z<bestgrid[b][d];z++)fprintf(out,"%s%d",z?",":"",gridpath[b][d][z]);fprintf(out,"]}\n");}
 if(fclose(out))fail("export close failed");
 printf("{\"schema\":\"round143-cycle-whole-runs-v2\",\"proof_query\":\"%s\",\"max_passes\":%d,\"accepted_cycles\":%"PRIu64",\"completed\":%s,\"capped\":%s,\"nodes\":%"PRIu64",\"exported_prefixes\":%"PRIu64",\"suffix_bound_enabled\":%s,\"suffix_bound_prunes\":%"PRIu64",\"transcript_fnv64\":\"%016"PRIx64"\"}\n",capacity_mode?"CYCLE_CAPACITY":"EXACT_CYCLE_P_NOT_CAPACITY",maximum,hits,capped?"false":"true",capped?"true":"false",nodes,capacity_mode?(uint64_t)gridcount:hits,bound_enabled?"true":"false",suffix_prunes,digest);
 free(ub);return 0;
}
