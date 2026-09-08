/* Exact LOCAL light-chain capacity. Root orbit occurs in two runs, first
 * entry phase 0, last entry phase 4; all other orbits fresh, no x arcs.
 * No 120-hex coverage target, no NR6 complete-word search.
 * Geometry is the preserved R115 literal geometry; new search is run-level.
 */
#define main unused_round115_main
#include "chain_capacity_115.c"
#undef main

static long long visits, caplimit=20000000000LL;
static int stopped, prefix, rootq, best[14], witness[14][120], wl[14];
static int stack[120], top;
static long long accepted[14];
static int occupied(int v){return (HLO&hlo[v])||(HHI&hhi[v]);}
static void root_suffix(int t,int paid_deficit){
    int ph=phse[t];
    if(ph<prefix)return;
    int d=paid_deficit+ph-prefix;
    if(d>13)return;
    for(int j=ph;j<5;j++)if(occupied(word_at[rootq][j]))return;
    int total=top+5-ph;accepted[d]++;
    if(total>best[d]){
        best[d]=total;wl[d]=total;
        memcpy(witness[d],stack,top*sizeof(int));
        for(int j=ph;j<5;j++)witness[d][top+j-ph]=word_at[rootq][j];
    }
}
static void fresh_run(int start,int deficit){
    if(stopped)return;
    if(++visits>caplimit){stopped=1;return;}
    int q=orbid[start], ph=phse[start], oldtop=top;
    uint64_t savedlo=HLO,savedhi=HHI;
    if(omask[q])abort();
    omask[q]=1;
    for(int len=1;len<=5;len++){
        int v=word_at[q][(ph+len-1)%5];
        if(occupied(v))break;
        HLO|=hlo[v];HHI|=hhi[v];stack[top++]=v;
        int d=deficit+5-len;
        if(d>13)continue; /* The loop may still grow this current run. */
        int tt[2]={mvW3b[v],mvW3c[v]};
        for(int i=0;i<2;i++){
            int t=tt[i],nq=orbid[t];
            if(nq==rootq)root_suffix(t,d);
            else if(!omask[nq]&&!occupied(t))fresh_run(t,d);
        }
        if(stopped)break;
    }
    omask[q]=0;top=oldtop;HLO=savedlo;HHI=savedhi;
}
int main(int argc,char**argv){
    if(argc>1)caplimit=atoll(argv[1]);
    build();rootq=orbid[0];
    if(phse[0]!=0)abort();
    for(int d=0;d<=13;d++)best[d]=-1;
    for(prefix=1;prefix<=4&&!stopped;prefix++){
        memset(omask,0,sizeof omask);omask[rootq]=1;HLO=HHI=0;top=0;
        for(int j=0;j<prefix;j++){
            int v=word_at[rootq][j];stack[top++]=v;HLO|=hlo[v];HHI|=hhi[v];
        }
        int last=stack[top-1],tt[2]={mvW3b[last],mvW3c[last]};
        for(int i=0;i<2;i++)if(!occupied(tt[i])&&orbid[tt[i]]!=rootq)fresh_run(tt[i],0);
    }
    printf("{\"schema\":\"codex/root-return-capacity/1\",\"nodes\":%lld,\"node_cap\":%lld,\"capped\":%s,\"rows\":[",visits,caplimit,stopped?"true":"false");
    for(int d=0;d<=13;d++){
        if(d)printf(",");
        printf("{\"deficit\":%d,\"passes\":%d,\"accepted\":%lld,\"witness\":[",d,best[d],accepted[d]);
        for(int j=0;j<wl[d];j++){if(j)printf(",");printf("%d",witness[d][j]);}
        printf("]}");
    }
    printf("]}\n");return stopped?2:0;
}
