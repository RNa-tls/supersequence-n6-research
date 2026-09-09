/* NR hard core: exhaustive search for covering WALKS in the clean overlap
 * graph CG_n, allowing repeated vertices.
 *
 *   usage: ./nr_clean_walk n BUDGET [nodecap] [mode]
 *     BUDGET = max total walk weight (word length = n + BUDGET)
 *     mode 0 = report first solution with >=1 repeat, then keep counting
 *          1 = count all solutions by repeat count
 *
 * A walk step is a CLEAN edge (no permutation window strictly inside the
 * max-overlap spelling), so the walk's vertices are exactly the word's
 * permutation windows.  Start vertex fixed to 0 = identity by the proved
 * value-renaming symmetry.
 *
 * Prune: remaining weight >= (#uncovered) + (#hexagons still holding an
 * uncovered vertex, minus one if the current vertex's hexagon does).
 * Sound: every clean edge adds exactly one vertex occurrence, so covering u
 * new vertices needs >= u more edges of weight >=1; and each fresh hexagon
 * must be entered by a non-sigma edge, which costs >= 2. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

static int n, NP, BUD, MODE;
static long long NODECAP, nodes = 0; static int capped = 0;
static int *perm;           /* NP * n */
static int *W;              /* NP*NP weights */
static int *SIG;
static int *hexid;          /* sigma class */
static int NHEX;
static int *adjq, *adjw, *adjstart, *adjcnt;   /* clean adjacency */

static uint64_t cov[2];
static int covcnt;
static int *hexrem;         /* uncovered count per hexagon */
static int hexopen;         /* hexagons with uncovered > 0 */
static int *hexmask;        /* per hexagon: bitmask of UNCOVERED cycle slots */
static int *hexslot;        /* vertex -> its slot index inside its hexagon */
static int *ARCS;           /* mask -> number of maximal circular runs of 1s */
static int arcsum;          /* sum over hexagons of ARCS[hexmask[h]] */
static int *walk;           /* vertex sequence */
static int wlen;
static long long solcount[64];
static int bestrep = -1;
static int reported = 0;

static int rank_of(const int *p){
    int used[8]={0}, r=0, i, j, f;
    for(i=0;i<n;i++){
        int c=0;
        for(j=0;j<p[i];j++) if(!used[j]) c++;
        f=1; for(j=1;j<n-i;j++) f*=j;
        r += c*f; used[p[i]]=1;
    }
    return r;
}

static void build(void){
    int i,j,k;
    NP=1; for(i=2;i<=n;i++) NP*=i;
    perm=malloc(sizeof(int)*NP*n);
    int *tmp=malloc(sizeof(int)*n);
    for(i=0;i<n;i++) tmp[i]=i;
    for(i=0;i<NP;i++){
        memcpy(perm+(size_t)i*n,tmp,sizeof(int)*n);
        /* next permutation */
        int a=n-2; while(a>=0&&tmp[a]>=tmp[a+1]) a--;
        if(a>=0){ int b=n-1; while(tmp[b]<=tmp[a]) b--;
            int t=tmp[a];tmp[a]=tmp[b];tmp[b]=t;
            for(j=a+1,k=n-1;j<k;j++,k--){t=tmp[j];tmp[j]=tmp[k];tmp[k]=t;} }
    }
    free(tmp);
    W=malloc(sizeof(int)*NP*NP);
    SIG=malloc(sizeof(int)*NP);
    for(i=0;i<NP;i++){
        int s[8]; for(j=0;j<n;j++) s[j]=perm[(size_t)i*n+(j+1)%n];
        SIG[i]=rank_of(s);
        for(j=0;j<NP;j++){
            if(i==j){W[(size_t)i*NP+j]=0;continue;}
            int w=n;
            for(k=1;k<n;k++){
                int ok=1,t;
                for(t=0;t<n-k;t++) if(perm[(size_t)i*n+k+t]!=perm[(size_t)j*n+t]){ok=0;break;}
                if(ok){w=k;break;}
            }
            W[(size_t)i*NP+j]=w;
        }
    }
    /* hexagons = sigma cycles */
    hexid=malloc(sizeof(int)*NP);
    for(i=0;i<NP;i++) hexid[i]=-1;
    NHEX=0;
    for(i=0;i<NP;i++) if(hexid[i]<0){ int x=i; for(k=0;k<n;k++){hexid[x]=NHEX;x=SIG[x];} NHEX++; }
    /* clean adjacency */
    adjstart=malloc(sizeof(int)*(NP+1)); adjcnt=malloc(sizeof(int)*NP);
    int cap=NP*NP; adjq=malloc(sizeof(int)*cap); adjw=malloc(sizeof(int)*cap);
    int pos=0;
    int *s=malloc(sizeof(int)*(2*n));
    for(i=0;i<NP;i++){
        adjstart[i]=pos; adjcnt[i]=0;
        for(j=0;j<NP;j++){
            if(i==j) continue;
            int w=W[(size_t)i*NP+j];
            for(k=0;k<n;k++) s[k]=perm[(size_t)i*n+k];
            for(k=0;k<w;k++) s[n+k]=perm[(size_t)j*n+n-w+k];
            int dirty=0,off;
            for(off=1;off<w&&!dirty;off++){
                int seen=0,t,ok=1;
                for(t=0;t<n;t++){ int c=s[off+t]; if(seen>>c&1){ok=0;break;} seen|=1<<c; }
                if(ok) dirty=1;
            }
            if(!dirty){ adjq[pos]=j; adjw[pos]=w; pos++; adjcnt[i]++; }
        }
    }
    adjstart[NP]=pos; free(s);
    hexrem=malloc(sizeof(int)*NHEX);
    hexmask=malloc(sizeof(int)*NHEX);
    hexslot=malloc(sizeof(int)*NP);
    for(i=0;i<NP;i++) hexslot[i]=-1;
    for(i=0;i<NP;i++) if(hexslot[i]<0){ int x=i; for(k=0;k<n;k++){ hexslot[x]=k; x=SIG[x]; } }
    ARCS=malloc(sizeof(int)*(1<<n));
    for(i=0;i<(1<<n);i++){
        int c=0,b;
        for(b=0;b<n;b++){ int prev=(b+n-1)%n;
            if((i>>b&1)&&!((i>>prev)&1)) c++; }
        if(i==(1<<n)-1) c=1;      /* full circle is one arc */
        ARCS[i]=c;
    }
}

static inline int isc(int v){ return (cov[v>>6]>>(v&63))&1ULL; }

static void rec(int cur,int wt){
    if(++nodes>NODECAP){ capped=1; return; }
    if(capped) return;
    if(covcnt==NP){
        int rep=wlen-NP;
        if(rep<64) solcount[rep]++;
        if(rep>0&&!reported){
            reported=1;
            printf("{\"REPEAT_SOLUTION\":true,\"weight\":%d,\"repeats\":%d,\"walk\":[",wt,rep);
            for(int i=0;i<wlen;i++) printf("%s%d",i?",":"",walk[i]);
            printf("]}\n"); fflush(stdout);
        }
        if(rep>bestrep) bestrep=rep;
        return;
    }
    int u=NP-covcnt;
    /* remaining weight >= u + (sum of uncovered arcs) - 1.
       Each remaining edge adds <=1 new vertex, so #edges >= u; weight >=
       #edges + #non-sigma edges; #runs = #non-sigma + 1 counting from here;
       and #runs + #revisits >= arcsum since a run covers one contiguous
       stretch of one hexagon and bridging two arcs costs a revisit. */
    /* The one continuation run can only start covering an arc when the
       sigma-successor of the current vertex is still uncovered. */
    int lb=u+arcsum-(isc(SIG[cur])?0:1); if(lb<u) lb=u;
    if(wt+lb>BUD) return;
    int a=adjstart[cur],e=a+adjcnt[cur];
    for(;a<e;a++){
        int q=adjq[a], w=adjw[a];
        if(wt+w>BUD) continue;
        int fresh=!isc(q);
        cov[q>>6]|=1ULL<<(q&63);
        int oc=covcnt, oh=hexopen, oa=arcsum, hq=hexid[q], om=hexmask[hq];
        if(fresh){ covcnt++; if(--hexrem[hq]==0) hexopen--;
                   arcsum-=ARCS[om];
                   hexmask[hq]=om & ~(1<<hexslot[q]);
                   arcsum+=ARCS[hexmask[hq]]; }
        walk[wlen++]=q;
        rec(q,wt+w);
        wlen--;
        if(fresh){ covcnt=oc; hexopen=oh; arcsum=oa; hexmask[hq]=om;
                   hexrem[hq]++; cov[q>>6]&=~(1ULL<<(q&63)); }
        if(capped) return;
    }
}

int main(int argc,char**argv){
    if(argc<3){fprintf(stderr,"usage: %s n BUDGET [nodecap] [mode]\n",argv[0]);return 1;}
    n=atoi(argv[1]); BUD=atoi(argv[2]);
    NODECAP=argc>3?atoll(argv[3]):100000000000LL;
    MODE=argc>4?atoi(argv[4]):0;
    build();
    walk=malloc(sizeof(int)*(BUD+4));
    memset(solcount,0,sizeof(solcount));
    cov[0]=cov[1]=0; covcnt=0;
    for(int h=0;h<NHEX;h++){ hexrem[h]=n; hexmask[h]=(1<<n)-1; }
    hexopen=NHEX; arcsum=NHEX;      /* each full circle is one arc */
    cov[0]|=1ULL; covcnt=1;
    { int h0=hexid[0]; if(--hexrem[h0]==0) hexopen--;
      arcsum-=ARCS[hexmask[h0]]; hexmask[h0]&=~(1<<hexslot[0]);
      arcsum+=ARCS[hexmask[h0]]; }
    walk[0]=0; wlen=1;
    rec(0,0);
    printf("{\"n\":%d,\"budget\":%d,\"word_length\":%d,\"nodes\":%lld,\"capped\":%d,",
           n,BUD,n+BUD,nodes,capped);
    printf("\"solutions_by_repeats\":{");
    int first=1;
    for(int r=0;r<64;r++) if(solcount[r]){ printf("%s\"%d\":%lld",first?"":",",r,solcount[r]); first=0; }
    printf("},\"max_repeats_found\":%d}\n",bestrep);
    return 0;
}
