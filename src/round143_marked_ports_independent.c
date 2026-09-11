/* Independent PORT-at-a-time enumeration of marked full-pass chains.
 *
 * Geometry is discovered by scanning all literal endpoint/target overlaps
 * and hidden windows. No whole-E-run producer table or capacity is imported.
 *
 * Usage: executable b D node_cap [AB|A] [target_passes extrema.jsonl]
 * node_cap=0 means uncapped. A excludes SIGMA_E, AB includes both marked
 * dirty w3 types. Optional JSONL contains ALL admissible prefixes having
 * exactly target_passes, only exhaustive when capped=false. It refuses to
 * overwrite an existing extrema file. Output is a single JSON object.
 */
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
#define MAXP 120

enum { FREE_E=0, CLEAN_120=1, CLEAN_201=2, CLEAN_210=3,
       E_SIGMA=4, SIGMA_E=5 };
static const char *kind_name[] = {
    "E", "CLEAN_120", "CLEAN_201", "CLEAN_210", "E_SIGMA", "SIGMA_E"
};
static unsigned char words[NW][6];
static int word_count, hex_id[NW], orbit_id[NW], phase[NW];
static int free_target[NW], paid_target[NW][5], paid_kind[NW][5];
static uint64_t hex_lo[NW], hex_hi[NW];
static unsigned char phase_mask[NQ];
static uint64_t visited_lo, visited_hi;
static int trail[MAXP], trail_kind[MAXP], best_trail[MAXP], best_kind[MAXP];
static int BOUND_B, BOUND_D, ALLOW_D=1, TARGET_P=0;
static uint64_t NODE_CAP, nodes, accepted, cap_prunes, collision_prunes, token_prunes;
static uint64_t transcript=UINT64_C(14695981039346656037);
static uint64_t geometry_digest=UINT64_C(14695981039346656037);
static uint64_t extrema_count;
static int capped, best_passes, best_b, best_D, best_orbits;
static int endpoint_best[4];
static int rich_best[50];
static FILE *extrema;

static void fail(const char *message) {
    fprintf(stderr, "%s\n", message);
    exit(2);
}
static void hash_number(uint64_t *state, uint64_t value) {
    for (int j=0; j<8; ++j) {
        *state ^= value & UINT64_C(255);
        *state *= UINT64_C(1099511628211);
        value >>= 8;
    }
}
static int rank_word(const unsigned char *p) {
    static const int factorial[] = {120,24,6,2,1,1};
    int result=0, used=0;
    for (int i=0; i<6; ++i) {
        if (p[i]>5 || (used & (1<<p[i]))) return -1;
        int smaller=0;
        for (int j=0; j<p[i]; ++j) if (!(used & (1<<j))) ++smaller;
        result += smaller*factorial[i];
        used |= 1<<p[i];
    }
    return result;
}
static void generate_words(int depth, unsigned used, unsigned char *word) {
    if (depth==6) {
        assert(rank_word(word)==word_count);
        memcpy(words[word_count++],word,6);
        return;
    }
    for (int value=0; value<6; ++value) if (!(used & (1U<<value))) {
        word[depth]=(unsigned char)value;
        generate_words(depth+1,used|(1U<<value),word);
    }
}
static int same_word(const unsigned char *a, const unsigned char *b) {
    return memcmp(a,b,6)==0;
}
static int popcount5(unsigned x) {
    int count=0;
    for (; x; x &= x-1) ++count;
    return count;
}
static void geometry(void) {
    unsigned char p[6];
    generate_words(0,0,p);
    assert(word_count==NW);
    int hmap[NW], qmap[NW], hcount=0, qcount=0;
    int hrep[NW], qrep[NW];
    for (int i=0; i<NW; ++i) hmap[i]=qmap[i]=-1;
    for (int v=0; v<NW; ++v) {
        int h=v, q=v;
        for (int shift=1; shift<6; ++shift) {
            for (int j=0; j<6; ++j) p[j]=words[v][(j+shift)%6];
            int r=rank_word(p); if (r<h) h=r;
        }
        for (int shift=1; shift<5; ++shift) {
            for (int j=0; j<5; ++j) p[j]=words[v][(j+shift)%5];
            p[5]=words[v][5];
            int r=rank_word(p); if (r<q) q=r;
        }
        hrep[v]=h; qrep[v]=q;
        if (hmap[h]<0) hmap[h]=hcount++;
        if (qmap[q]<0) qmap[q]=qcount++;
        hex_id[v]=hmap[h]; orbit_id[v]=qmap[q];
        phase[v]=-1;
        for (int shift=0; shift<5; ++shift) {
            for (int j=0; j<5; ++j) p[j]=words[q][(j+shift)%5];
            p[5]=words[q][5];
            if (same_word(p,words[v])) phase[v]=shift;
        }
        assert(phase[v]>=0);
        hex_lo[v]=hex_id[v]<64 ? UINT64_C(1)<<hex_id[v] : 0;
        hex_hi[v]=hex_id[v]>=64 ? UINT64_C(1)<<(hex_id[v]-64) : 0;
    }
    assert(hcount==NH && qcount==NQ);
    for (int v=0; v<NW; ++v) {
        unsigned char endpoint[6], raw[9];
        endpoint[0]=words[v][5];
        for (int j=1; j<6; ++j) endpoint[j]=words[v][j-1];
        int nfree=0, npaid=0;
        free_target[v]=-1;
        for (int target=0; target<NW; ++target) {
            int gap;
            for (gap=1; gap<6; ++gap)
                if (memcmp(endpoint+gap,words[target],(size_t)(6-gap))==0) break;
            if (gap!=2 && gap!=3) continue;
            memcpy(raw,endpoint,6);
            memcpy(raw+6,words[target]+6-gap,(size_t)gap);
            int hidden[2], nhidden=0;
            for (int offset=1; offset<gap; ++offset) {
                int found=rank_word(raw+offset);
                if (found>=0) hidden[nhidden++]=found;
            }
            if (gap==2) {
                if (!nhidden) { free_target[v]=target; ++nfree; }
                continue;
            }
            int kind=-1;
            if (!nhidden) {
                int digits[3];
                for (int j=0; j<3; ++j) {
                    digits[j]=-1;
                    for (int x=0; x<3; ++x)
                        if (words[target][3+j]==endpoint[x]) digits[j]=x;
                    assert(digits[j]>=0);
                }
                int code=100*digits[0]+10*digits[1]+digits[2];
                if (code==120) kind=CLEAN_120;
                if (code==201) kind=CLEAN_201;
                if (code==210) kind=CLEAN_210;
                assert(kind>=0);
            } else if (nhidden==1 && hidden[0]==v) {
                kind=E_SIGMA;
            } else if (nhidden==1) {
                for (int j=0; j<6; ++j) p[j]=words[hidden[0]][(j+1)%6];
                if (same_word(p,words[target])) kind=SIGMA_E;
            }
            if (kind<0) continue;
            assert(npaid<5);
            paid_target[v][npaid]=target;
            paid_kind[v][npaid++]=kind;
        }
        assert(nfree==1 && npaid==5);
        assert(orbit_id[free_target[v]]==orbit_id[v]);
        assert(phase[free_target[v]]==(phase[v]+1)%5);
        unsigned types=0;
        for (int i=0; i<5; ++i) {
            assert(paid_target[v][i]!=free_target[v]);
            types|=1U<<paid_kind[v][i];
            if (paid_kind[v][i]==SIGMA_E) {
                int t=paid_target[v][i];
                for (int j=0; j<6; ++j) p[j]=words[free_target[v]][(j+1)%6];
                assert(same_word(p,words[t]));
            }
        }
        assert(types==62);
        hash_number(&geometry_digest,(uint64_t)v);
        hash_number(&geometry_digest,(uint64_t)hex_id[v]);
        hash_number(&geometry_digest,(uint64_t)orbit_id[v]);
        hash_number(&geometry_digest,(uint64_t)phase[v]);
        hash_number(&geometry_digest,(uint64_t)free_target[v]);
        for (int i=0; i<5; ++i) {
            hash_number(&geometry_digest,(uint64_t)paid_target[v][i]);
            hash_number(&geometry_digest,(uint64_t)paid_kind[v][i]);
        }
    }
    (void)hrep; (void)qrep;
}
static void print_path(FILE *stream, const int *path, const int *kinds, int length) {
    fputs("\"entries\":[",stream);
    for (int i=0; i<length; ++i) fprintf(stream,"%s%d",i?",":"",path[i]);
    fputs("],\"edge_kinds\":[",stream);
    for (int i=1; i<length; ++i) fprintf(stream,"%s\"%s\"",i>1?",":"",kind_name[kinds[i]]);
    fputs("]",stream);
}
static void export_prefix(int passes, int b, int deficit, int opened) {
    if (!extrema || passes!=TARGET_P) return;
    fprintf(extrema,"{\"P\":%d,\"b\":%d,\"D\":%d,\"O\":%d,",passes,b,deficit,opened);
    print_path(extrema,trail,trail_kind,passes);
    fputs("}\n",extrema);
    if (ferror(extrema)) fail("Extrema write failed");
    ++extrema_count;
}
static void dfs(int current, int used_b, int passes, int deficit, int opened);
static void add_target(int target, int kind, int used_b, int passes, int deficit, int opened) {
    if (capped) return;
    if ((visited_lo&hex_lo[target]) || (visited_hi&hex_hi[target])) { ++collision_prunes; return; }
    int q=orbit_id[target], bit=1<<phase[target];
    unsigned old=phase_mask[q];
    assert(!(old & (unsigned)bit));
    int fresh=old==0;
    int next_b=used_b + (kind!=FREE_E && !fresh);
    if (next_b>BOUND_B) { ++token_prunes; return; }
    phase_mask[q]=(unsigned char)(old|(unsigned)bit);
    visited_lo|=hex_lo[target]; visited_hi|=hex_hi[target];
    trail[passes]=target; trail_kind[passes]=kind;
    dfs(target,next_b,passes+1,deficit+(fresh?4:-1),opened+fresh);
    visited_lo&=~hex_lo[target]; visited_hi&=~hex_hi[target];
    phase_mask[q]=(unsigned char)old;
}
static void dfs(int current, int used_b, int passes, int deficit, int opened) {
    if (capped) return;
    if (NODE_CAP && nodes>=NODE_CAP) { capped=1; return; }
    ++nodes;
    assert(passes<=MAXP && deficit==5*opened-passes && deficit>=0);
    hash_number(&transcript,(uint64_t)current);
    hash_number(&transcript,(uint64_t)used_b);
    hash_number(&transcript,(uint64_t)passes);
    hash_number(&transcript,(uint64_t)deficit);
    hash_number(&transcript,(uint64_t)trail_kind[passes-1]);
    if (deficit<=BOUND_D) {
        ++accepted;
        int first_length=1,last_length=1;
        while(first_length<passes && trail_kind[first_length]==FREE_E) ++first_length;
        while(last_length<passes && trail_kind[passes-last_length]==FREE_E) ++last_length;
        int mask=(first_length<5?1:0)|(last_length<5?2:0);
        if(passes>endpoint_best[mask]) endpoint_best[mask]=passes;
        int rich=(first_length-1)*5+last_length-1+(first_length==passes?25:0);
        if(passes>rich_best[rich]) rich_best[rich]=passes;
        if (passes>best_passes) {
            best_passes=passes; best_b=used_b; best_D=deficit; best_orbits=opened;
            memcpy(best_trail,trail,(size_t)passes*sizeof(int));
            memcpy(best_kind,trail_kind,(size_t)passes*sizeof(int));
        }
        export_prefix(passes,used_b,deficit,opened);
    }
    if (passes==MAXP) return;
    /* Independent, deliberately loose deficit lower bound. Grant all
     * missing current-Q phases free. Each remaining non-E old-Q entry can
     * repair at most four phases elsewhere. New Q deficits are nonnegative.
     * Current deficit is NOT itself a monotone prune. */
    int current_deficit=5-popcount5(phase_mask[orbit_id[current]]);
    if (deficit-current_deficit-4*(BOUND_B-used_b)>BOUND_D) { ++cap_prunes; return; }
    add_target(free_target[current],FREE_E,used_b,passes,deficit,opened);
    for (int i=0; i<5 && !capped; ++i) {
        int kind=paid_kind[current][i];
        if (kind==SIGMA_E && !ALLOW_D) continue;
        add_target(paid_target[current][i],kind,used_b,passes,deficit,opened);
    }
}
static int integer_arg(const char *text, int maximum) {
    char *end; errno=0;
    long value=strtol(text,&end,10);
    if (errno || *end || value<0 || value>maximum) fail("Invalid integer argument");
    return (int)value;
}
int main(int argc, char **argv) {
    if (argc!=4 && argc!=5 && argc!=7) {
        fprintf(stderr,"usage: %s b D node_cap [AB|A] [target_passes extrema.jsonl]\n",argv[0]);
        return 2;
    }
    BOUND_B=integer_arg(argv[1],120); BOUND_D=integer_arg(argv[2],720);
    char *end; errno=0; NODE_CAP=strtoull(argv[3],&end,10);
    if (errno || *end || argv[3][0]=='-') fail("Invalid node cap");
    if (argc>=5) {
        if (strcmp(argv[4],"A")==0) ALLOW_D=0;
        else if (strcmp(argv[4],"AB")!=0) fail("Mode must be A or AB");
    }
    if (argc==7) {
        TARGET_P=integer_arg(argv[5],MAXP);
        if (!TARGET_P) fail("target_passes must be positive");
        FILE *exists=fopen(argv[6],"rb");
        if (exists) { fclose(exists); fail("Refusing to overwrite existing extrema file"); }
        extrema=fopen(argv[6],"wb");
        if (!extrema) fail("Cannot create extrema file");
    }
    clock_t started=clock();
    geometry();
    assert(rank_word(words[0])==0);
    phase_mask[orbit_id[0]]=(unsigned char)(1<<phase[0]);
    visited_lo=hex_lo[0]; visited_hi=hex_hi[0];
    trail[0]=0; trail_kind[0]=FREE_E;
    dfs(0,0,1,4,1);
    if (extrema && fclose(extrema)) fail("Extrema close failed");
    printf("{\"schema\":\"round143-marked-independent-port-v1\",\"mode\":\"%s\","
           "\"b\":%d,\"D\":%d,\"node_cap\":%" PRIu64 ",\"nodes\":%" PRIu64 ","
           "\"capped\":%s,\"completed\":%s,\"status\":\"%s\",\"max_passes\":%d,"
           "\"accepted_prefixes\":%" PRIu64 ",\"deficit_prunes\":%" PRIu64 ","
           "\"collision_prunes\":%" PRIu64 ",\"token_prunes\":%" PRIu64 ","
           "\"transcript_fnv64\":\"%016" PRIx64 "\",\"geometry_fnv64\":\"%016" PRIx64 "\","
           "\"target_passes\":%d,\"exported_prefixes\":%" PRIu64 ",\"extrema_complete\":%s,"
           "\"cpu_seconds\":%.6f,\"witness\":{\"b\":%d,\"D\":%d,\"O\":%d,",
           ALLOW_D?"AB":"A",BOUND_B,BOUND_D,NODE_CAP,nodes,
           capped?"true":"false",capped?"false":"true",capped?"UNKNOWN_CAP":"EXHAUSTED_FINITE_MODEL",best_passes,
           accepted,cap_prunes,collision_prunes,token_prunes,transcript,geometry_digest,
           TARGET_P,extrema_count,(TARGET_P && !capped)?"true":"false",(double)(clock()-started)/CLOCKS_PER_SEC,
           best_b,best_D,best_orbits);
    print_path(stdout,best_trail,best_kind,best_passes);
    printf("},\"endpoint_max_passes\":[%d,%d,%d,%d],\"rich_endpoint_max_passes\":[",endpoint_best[0],endpoint_best[1],endpoint_best[2],endpoint_best[3]);
    for(int j=0;j<50;j++) printf("%s%d",j?",":"",rich_best[j]);
    printf("]}\n");
    return 0;
}
