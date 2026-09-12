/* Round 143 independent nonpure beta-cycle necessary relaxation.
 * Closure is a non-E joint to the already stored first vertex; it spends
 * A/B/heavy resources but no vertex, repeat count, old-Q token, or deficit.
 *
 * Port-at-a-time recursion. Geometry is rebuilt from all 720 x 720 literal
 * endpoint/target maximum-overlap comparisons, not producer edge tables.
 * Hidden-window first-occurrence conditions are deliberately NOT imposed.
 * Distinct entry ports, exact A/Qs, and upper b/D/R/H are imposed. Repeated
 * hexagon ARRIVALS, including free-E arrivals, each spend one R unit.
 *
 * usage: exe b D node_cap A Qs R H P export.jsonl [bounds.txt]
 * A = dirty weight-2 sigma; Qs = dirty weight-3 sigma^2.
 * Bounds rows: a q r h b delta upper. Exact tuple lookup only; missing = INF.
 * These are exact-P queries, NEVER scalar capacity certificates.
 */
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define NW 720
#define NQ 144
#define NH 120
#define INF 1000000
enum { K_E, K_A, K_B, K_120, K_201, K_210, K_ES, K_SE, K_HEAVY };
static const char *names[] = {"E","DIRTY_A","DIRTY_B","CLEAN_120",
    "CLEAN_201","CLEAN_210","E_SIGMA","SIGMA_E","HEAVY"};
typedef struct { int target, weight, kind; } Edge;
typedef struct { int p, opened, deficit, b, a, q, repeats, heavy; } Counts;
typedef struct { int v[7]; } BoundRow;
static unsigned char word[NW][6];
static int orbit[NW], phase[NW], hexagon[NW], nedges[NW];
static Edge edge[NW][NW];
static unsigned char occupied[NW], qmask[NQ], hcount[NH];
static int trail[NW], weights[NW], kinds[NW];
static int BMAX, DMAX, AMAX, QMAX, RMAX, HMAX, PMAX;
static uint64_t limit, nodes, exports, repeat_prunes, port_prunes;
static uint64_t resource_prunes, deficit_prunes, suffix_prunes;
static uint64_t transcript=UINT64_C(14695981039346656037);
static uint64_t exported_digest=UINT64_C(14695981039346656037);
static uint64_t geometry_digest=UINT64_C(14695981039346656037);
static uint64_t bounds_digest=UINT64_C(14695981039346656037);
static int capped, max_depth, bound_mode;
static int terminal_port=-1;
static int capacity_mode,maximum,grid_count,grid_p[11][121],grid_trail[11][121][151],grid_weights[11][121][151],grid_kinds[11][121][151];
static Counts grid_counts[11][121];
static BoundRow *bounds;
static size_t nbounds;
static FILE *output;

static void die(const char *s) { fprintf(stderr,"%s\n",s); exit(2); }
static void hash_u64(uint64_t *h, uint64_t x) {
    for(int i=0;i<8;i++) { *h^=x&255; *h*=UINT64_C(1099511628211); x>>=8; }
}
static int parse_int(const char *s,int maximum) {
    char *end; errno=0; long v=strtol(s,&end,10);
    if(errno || end==s || *end || v<0 || v>maximum)die("Invalid integer argument");
    return (int)v;
}
static int rank_perm(const unsigned char *w) {
    int rank=0;
    for(int i=0;i<6;i++) {
        int less=0;
        for(int j=i+1;j<6;j++)less+=w[j]<w[i];
        rank=rank*(6-i)+less;
    }
    return rank;
}
static int next_permutation(unsigned char *w) {
    int i=4; while(i>=0 && w[i]>=w[i+1])i--;
    if(i<0)return 0;
    int j=5;while(w[j]<=w[i])j--;
    unsigned char t=w[i];w[i]=w[j];w[j]=t;
    for(int a=i+1,b=5;a<b;a++,b--) {t=w[a];w[a]=w[b];w[b]=t;}
    return 1;
}
static int popcount(unsigned x) {int n=0;for(;x;x&=x-1)n++;return n;}
static int tail_code(const unsigned char *endpoint,int target,int width) {
    int code=0;
    for(int i=6-width;i<6;i++) {
        int digit=0;while(digit<width && endpoint[digit]!=word[target][i])digit++;
        assert(digit<width);code=10*code+digit;
    }
    return code;
}
static void geometry(void) {
    unsigned char w[6]={0,1,2,3,4,5};int n=0;
    do {assert(rank_perm(w)==n);memcpy(word[n++],w,6);}while(next_permutation(w));
    assert(n==NW);
    int qmap[NW],hmap[NW],nq=0,nh=0;
    for(int i=0;i<NW;i++)qmap[i]=hmap[i]=-1;
    for(int v=0;v<NW;v++) {
        int hr=NW,qr=NW;
        for(int r=0;r<6;r++) {
            for(int i=0;i<6;i++)w[i]=word[v][(i+r)%6];
            int id=rank_perm(w);if(id<hr)hr=id;
        }
        for(int r=0;r<5;r++) {
            for(int i=0;i<5;i++)w[i]=word[v][(i+r)%5];w[5]=word[v][5];
            int id=rank_perm(w);if(id<qr)qr=id;
        }
        if(qmap[qr]<0)qmap[qr]=nq++;
        if(hmap[hr]<0)hmap[hr]=nh++;
        orbit[v]=qmap[qr];hexagon[v]=hmap[hr];phase[v]=-1;
        for(int r=0;r<5;r++) {
            for(int i=0;i<5;i++)w[i]=word[qr][(i+r)%5];w[5]=word[qr][5];
            if(!memcmp(w,word[v],6))phase[v]=r;
        }
        assert(phase[v]>=0);
    }
    assert(nq==NQ && nh==NH);
    for(int v=0;v<NW;v++) {
        unsigned char endpoint[6];endpoint[0]=word[v][5];
        for(int i=1;i<6;i++)endpoint[i]=word[v][i-1];
        int n_e=0,n_a=0,n_q=0,n_w3=0;
        for(int t=0;t<NW;t++) {
            int overlap=5;
            while(overlap>0 && memcmp(endpoint+6-overlap,word[t],(size_t)overlap))overlap--;
            int weight=6-overlap;
            if(weight<2 || weight>HMAX+3)continue;
            int kind=K_HEAVY;
            if(weight==2) {
                int code=tail_code(endpoint,t,2);
                if(code==10){kind=K_E;n_e++;}
                else {assert(code==1);kind=K_A;n_a++;}
            } else if(weight==3) {
                int code=tail_code(endpoint,t,3);n_w3++;
                switch(code) {
                    case 12:kind=K_B;n_q++;break;
                    case 21:kind=K_ES;break;
                    case 102:kind=K_SE;break;
                    case 120:kind=K_120;break;
                    case 201:kind=K_201;break;
                    case 210:kind=K_210;break;
                    default:die("Unexpected weight-3 tail");
                }
            }
            if(kind==K_E) {
                assert(orbit[t]==orbit[v] && phase[t]==(phase[v]+1)%5);
            } else if(kind==K_A || kind==K_B) {
                int shift=kind==K_A?1:2;
                for(int i=0;i<6;i++)w[i]=word[v][(i+shift)%6];
                assert(!memcmp(word[t],w,6) && hexagon[t]==hexagon[v]);
            }
            Edge e={t,weight,kind};edge[v][nedges[v]++]=e;
        }
        assert(n_e==1 && n_a==1 && n_q==1 && n_w3==6);
        hash_u64(&geometry_digest,v);hash_u64(&geometry_digest,orbit[v]);
        hash_u64(&geometry_digest,phase[v]);hash_u64(&geometry_digest,hexagon[v]);
        for(int i=0;i<nedges[v];i++) {
            hash_u64(&geometry_digest,edge[v][i].target);
            hash_u64(&geometry_digest,edge[v][i].weight);
            hash_u64(&geometry_digest,edge[v][i].kind);
        }
    }
    if(AMAX>0 || QMAX>0) {
        int shift=AMAX>0?5:4;
        for(int j=0;j<6;j++)w[j]=word[0][(j+shift)%6];
        terminal_port=rank_perm(w);
    }
}
static int compare_bounds(const void *a,const void *b) {
    const BoundRow *x=(const BoundRow*)a,*y=(const BoundRow*)b;
    for(int i=0;i<6;i++)if(x->v[i]!=y->v[i])return x->v[i]<y->v[i]?-1:1;
    return 0;
}
static void load_bounds(const char *path) {
    FILE *f=fopen(path,"rb");if(!f)die("Cannot open suffix bound table");
    size_t cap=0;char line[512];
    while(fgets(line,sizeof(line),f)) {
        BoundRow row;char extra;
        if(line[0]=='#' || line[0]=='\n' || line[0]=='\r')continue;
        int got=sscanf(line,"%d %d %d %d %d %d %d %c",&row.v[0],&row.v[1],
            &row.v[2],&row.v[3],&row.v[4],&row.v[5],&row.v[6],&extra);
        if(got!=7)die("Malformed suffix bound row");
        for(int j=0;j<7;j++)if(row.v[j]<0 || row.v[j]>INF)die("Suffix bound range");
        if(nbounds==cap) {
            cap=cap?cap*2:128;if(cap>1048576)die("Suffix table too large");
            BoundRow *p=(BoundRow*)realloc(bounds,cap*sizeof(*p));
            if(!p)die("Suffix table allocation failed");bounds=p;
        }
        bounds[nbounds++]=row;
    }
    if(ferror(f) || fclose(f))die("Suffix table read failed");
    if(!nbounds)die("Empty suffix bound table");
    qsort(bounds,nbounds,sizeof(*bounds),compare_bounds);
    for(size_t i=0;i<nbounds;i++) {
        if(i && !compare_bounds(bounds+i-1,bounds+i))die("Duplicate suffix tuple");
        for(int j=0;j<7;j++)hash_u64(&bounds_digest,(uint64_t)bounds[i].v[j]);
    }
    bound_mode=1;
}
static int suffix_bound(int a,int q,int r,int h,int b,int delta) {
    if(a<0 || q<0 || r<0 || h<0 || b<0 || delta<0)return -1;
    BoundRow key={{a,q,r,h,b,delta,0}};
    BoundRow *found=(BoundRow*)bsearch(&key,bounds,nbounds,sizeof(*bounds),compare_bounds);
    return found?found->v[6]:INF;
}
static void export_path(Counts c) {
    fprintf(output,"{\"P\":%d,\"b\":%d,\"D\":%d,\"O\":%d,\"A\":%d,\"Qs\":%d,\"R\":%d,\"H\":%d,\"entries\":[",
        c.p,c.b,c.deficit,c.opened,c.a,c.q,c.repeats,c.heavy);
    for(int i=0;i<c.p;i++) {
        fprintf(output,"%s%d",i?",":"",trail[i]);hash_u64(&exported_digest,trail[i]);
    }
    fputs("],\"edge_weights\":[",output);
    for(int i=1;i<c.p;i++)fprintf(output,"%s%d",i>1?",":"",weights[i]);
    fputs("],\"edge_kinds\":[",output);
    for(int i=1;i<c.p;i++)fprintf(output,"%s\"%s\"",i>1?",":"",names[kinds[i]]);
    fputs("]}\n",output);
    hash_u64(&exported_digest,NW); /* delimiter, impossible entry ID */
    if(ferror(output))die("Export write failed");exports++;
}
static void visit(int current,Counts c) {
    if(capped)return;
    if(limit && nodes>=limit){capped=1;return;}
    nodes++;if(c.p>max_depth)max_depth=c.p;
    assert(c.p<=NW && c.deficit==5*c.opened-c.p && c.deficit>=0);
    hash_u64(&transcript,current);hash_u64(&transcript,c.p);
    hash_u64(&transcript,c.b);hash_u64(&transcript,c.deficit);
    hash_u64(&transcript,c.a);hash_u64(&transcript,c.q);
    hash_u64(&transcript,c.repeats);hash_u64(&transcript,c.heavy);
    if(capacity_mode || c.p==PMAX) {
        for(int j=0;j<nedges[current];j++) {
            const Edge *close=&edge[current][j];
            if(close->target!=trail[0] || close->kind==K_E)continue;
            if(AMAX>0 && close->kind!=K_A)continue;
            if(AMAX==0 && QMAX>0 && close->kind!=K_B)continue;
            Counts closed=c;closed.a+=close->kind==K_A;closed.q+=close->kind==K_B;
            closed.heavy+=close->weight>3?close->weight-3:0;
            if(closed.a==AMAX && closed.q==QMAX && closed.heavy<=HMAX && closed.deficit<=DMAX && closed.repeats>=AMAX+QMAX){
                if(capacity_mode){
                    exports++;
                    if(c.p>maximum)maximum=c.p;
                    if(c.p>grid_p[c.b][c.deficit]){
                        grid_p[c.b][c.deficit]=c.p;grid_counts[c.b][c.deficit]=closed;
                        memcpy(grid_trail[c.b][c.deficit],trail,c.p*sizeof(int));
                        memcpy(grid_weights[c.b][c.deficit],weights,c.p*sizeof(int));
                        memcpy(grid_kinds[c.b][c.deficit],kinds,c.p*sizeof(int));
                    }
                }else export_path(closed);
            }
        }
    }
    if(c.p==PMAX)return;
    if(current==terminal_port)return;
    /* D is not monotone. Grant all current-orbit missing phases for free;
       every subsequent non-E old-orbit entry repairs at most four more. */
    int current_missing=5-popcount(qmask[orbit[current]]);
    if(c.deficit-current_missing-4*(BMAX-c.b)>DMAX){deficit_prunes++;return;}
    for(int i=0;i<nedges[current] && !capped;i++) {
        const Edge *e=&edge[current][i];int t=e->target;
        if(occupied[t]){port_prunes++;continue;}
        int repeated=hcount[hexagon[t]]!=0;
        Counts next=c;
        next.p++;next.a+=e->kind==K_A;next.q+=e->kind==K_B;
        next.repeats+=repeated;next.heavy+=e->weight>3?e->weight-3:0;
        if(next.repeats>RMAX){repeat_prunes++;continue;}
        unsigned char previous=qmask[orbit[t]];
        int fresh=previous==0;
        next.b+=e->kind!=K_E && !fresh;
        next.opened+=fresh;next.deficit+=fresh?4:-1;
        if(next.b>BMAX || next.a>AMAX || next.q>QMAX || next.heavy>HMAX) {
            resource_prunes++;continue;
        }
        if(bound_mode && e->kind!=K_E) {
            int delta=DMAX+5*BMAX-c.deficit-5*c.b;
            int bound=-1;
            /* Maximize over the unknown final non-E edge, without pretending
               its return to vertex0 appends an extra repeated hex. */
            for(int terminal=0;terminal<6;terminal++) {
                if(AMAX>0 && terminal!=1)continue;
                if(AMAX==0 && QMAX>0 && terminal!=2)continue;
                int a=AMAX-next.a-(terminal==1),q=QMAX-next.q-(terminal==2);
                int h=HMAX-next.heavy-(terminal>=3?terminal-2:0),r=RMAX-next.repeats;
                if(a<0||q<0||h<0||r<a+q)continue;
                int candidate=suffix_bound(a,q,r,h,BMAX-next.b,delta);
                if(candidate>bound)bound=candidate;
            }
            /* The suffix begins WITH t. Boundary cost was spent above, but
               no t-entry deficit is subtracted from the suffix delta. */
            if(bound<0 || c.p+bound<PMAX){suffix_prunes++;continue;}
        }
        occupied[t]=1;qmask[orbit[t]]=(unsigned char)(previous|(1U<<phase[t]));
        hcount[hexagon[t]]++;trail[c.p]=t;weights[c.p]=e->weight;kinds[c.p]=e->kind;
        visit(t,next);
        occupied[t]=0;qmask[orbit[t]]=previous;hcount[hexagon[t]]--;
    }
}
int main(int argc,char **argv) {
    if(argc!=10 && argc!=11) {
        fprintf(stderr,"usage: %s b D node_cap A Qs R H P export.jsonl [bounds.txt]\n",argv[0]);return 2;
    }
    BMAX=parse_int(argv[1],10);DMAX=parse_int(argv[2],120);
    char *end;errno=0;limit=strtoull(argv[3],&end,10);
    if(errno || end==argv[3] || *end || argv[3][0]=='-')die("Invalid node cap");
    AMAX=parse_int(argv[4],20);QMAX=parse_int(argv[5],10);
    RMAX=parse_int(argv[6],30);HMAX=parse_int(argv[7],3);PMAX=parse_int(argv[8],150);
    if(!PMAX){capacity_mode=1;PMAX=120+RMAX;if(argc==11)die("Capacity cannot use exact-P suffix table");}
    if(argc==11)load_bounds(argv[10]);
    /* C11 exclusive creation: never truncate any existing certificate. */
    output=fopen(argv[9],"wbx");if(!output)die("Cannot exclusively create export file");
    clock_t start=clock();geometry();
    occupied[0]=1;qmask[orbit[0]]=(unsigned char)(1U<<phase[0]);
    hcount[hexagon[0]]=1;trail[0]=0;weights[0]=0;kinds[0]=K_E;
    Counts initial={1,1,4,0,0,0,0,0};visit(0,initial);
    uint64_t accepted_cycles=exports;
    if(capacity_mode) {
        exports=0;
        for(int b=0;b<=BMAX;b++)for(int d=0;d<=DMAX;d++)if(grid_p[b][d]) {
            Counts c=grid_counts[b][d];
            memcpy(trail,grid_trail[b][d],c.p*sizeof(int));
            memcpy(weights,grid_weights[b][d],c.p*sizeof(int));
            memcpy(kinds,grid_kinds[b][d],c.p*sizeof(int));
            export_path(c);grid_count++;
        }
    }
    if(fclose(output))die("Export close failed");
    printf("{\"schema\":\"round143-cycle-independent-port-v2\",\"proof_query\":\"%s\",\"max_passes\":%d,\"accepted_cycles\":%" PRIu64 ","
        "\"b\":%d,\"D\":%d,\"A_exact\":%d,\"Qs_exact\":%d,\"R_cap\":%d,\"H_cap\":%d,\"target_passes\":%d,"
        "\"node_cap\":%" PRIu64 ",\"nodes\":%" PRIu64 ",\"max_depth\":%d,"
        "\"completed\":%s,\"capped\":%s,\"status\":\"%s\",\"exported_prefixes\":%" PRIu64 ",\"extrema_complete\":%s,"
        "\"port_collision_prunes\":%" PRIu64 ",\"repeat_budget_prunes\":%" PRIu64 ",\"resource_prunes\":%" PRIu64 ","
        "\"deficit_prunes\":%" PRIu64 ",\"suffix_bound_prunes\":%" PRIu64 ",\"suffix_bound_enabled\":%s,"
        "\"suffix_bound_rows\":%zu,\"suffix_bound_fnv64\":\"%016" PRIx64 "\","
        "\"geometry_comparisons\":518400,\"geometry_fnv64\":\"%016" PRIx64 "\","
        "\"transcript_fnv64\":\"%016" PRIx64 "\",\"export_fnv64\":\"%016" PRIx64 "\",\"cpu_seconds\":%.6f}\n",
        capacity_mode?"CYCLE_CAPACITY":"EXACT_CYCLE_P_NOT_CAPACITY",maximum,accepted_cycles,
        BMAX,DMAX,AMAX,QMAX,RMAX,HMAX,PMAX,limit,nodes,max_depth,
        capped?"false":"true",capped?"true":"false",capped?"UNKNOWN_CAP":"EXHAUSTED_FINITE_MODEL",exports,capped?"false":"true",
        port_prunes,repeat_prunes,resource_prunes,deficit_prunes,suffix_prunes,bound_mode?"true":"false",nbounds,bounds_digest,
        geometry_digest,transcript,exported_digest,(double)(clock()-start)/CLOCKS_PER_SEC);
    free(bounds);return 0;
}
