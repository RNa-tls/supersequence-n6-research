/* Round 147 Phase 6 -- SECOND, INDEPENDENT implementation of the chain
 * capacity search.
 *
 * Independence from r147/src/l6_chain_capacity_147.c:
 *   GEOMETRY.  None is computed here.  The tables come from
 *   r147/src/catalogue147.h, which r147/src/genheader147.py emits from the
 *   pure string-algebra reconstruction in r147/src/catalogue147.py.  That
 *   reconstruction was compared field by field against the first
 *   implementation's internal tables and agrees on all ten of them
 *   (r147/certs/catalogue_agreement_147.json).
 *
 *   STATE.  The first implementation tracks a 5-bit PHASE MASK per tau-orbit
 *   and a 0/1 flag per hexagon.  This one tracks
 *       used[v]      a byte per PERMUTATION (ports are permutations, and
 *                    "distinct ports" is then a direct test, not a phase test)
 *       hcnt[hex]    a COUNT per hexagon (so "already used" is hcnt > 0 and
 *                    the number of distinct hexagons is a separate counter)
 *       ocnt[orbit]  a COUNT per orbit (so "fresh" is ocnt == 0)
 *   and it keeps an explicit DFS stack instead of recursing.
 *
 *   ORDER.  Moves are generated in the reverse order: heavy connectors first,
 *   then type B, type A, the five paid edges from last to first, and the free E
 *   edge last.  With the best-so-far prune on, a different order finds the
 *   record at a different time, so NODE COUNTS ARE EXPECTED TO DIFFER; only the
 *   capacity must agree.  With the best-so-far prune off and no table, the two
 *   searches visit the same set of states and the node counts must agree
 *   exactly.
 *
 * The pruning table format and semantics are identical (a sound bound is sound
 * for any implementation), so this build can consume the same UB7 file.
 *
 * Usage: ./chain2_147 b dmax amax bmax emax hmax [node_cap] [ubfile] [bestprune]
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
#include "catalogue147.h"

#define UBD 40
#define UBA 24
#define UBH 6
#define UBT 5
#define UBIDX(t, d, a, b, e, h) \
    ((((((size_t)(t) * (UBD + 1) + (d)) * (UBA + 1) + (a)) * (UBA + 1) + (b)) \
        * (UBA + 1) + (e)) * (UBH + 1) + (h))
#define UBSIZE ((size_t)(UBT + 1) * (UBD + 1) * (UBA + 1) * (UBA + 1) \
                * (UBA + 1) * (UBH + 1))

static int B0, DM, AM, BM, EM, HM, BESTP, SAFE;
static uint64_t NCAP, nodes, capped;
static int *UB;
static int have_ub;

static unsigned char used[NW2];
static int hcnt[NH2], ocnt[NQ2];
static int nhex, ndef, record;

static int ubound(int tok, int d, int a, int b, int e, int h) {
    if (!have_ub) return SAFE;
    if (tok < 0) tok = 0;
    if (tok > UBT) tok = UBT;
    if (d < 0) d = 0;
    if (d > UBD) d = UBD;
    if (a < 0) a = 0;
    if (a > UBA) a = UBA;
    if (b < 0) b = 0;
    if (b > UBA) b = UBA;
    if (e < 0) e = 0;
    if (e > UBA) e = UBA;
    if (h < 0) h = 0;
    if (h > UBH) h = UBH;
    return UB[UBIDX(tok, d, a, b, e, h)];
}

/* feasibility: the tokens left cannot absorb the deficit the opened orbits
 * still owe.  Same inequality as the first implementation, recomputed from the
 * per-orbit COUNTS instead of from phase masks. */
static int feas(int tok, int corb) {
    int hist[6] = {0, 0, 0, 0, 0, 0};
    for (int q = 0; q < NQ2; ++q) {
        if (!ocnt[q] || q == corb) continue;
        hist[5 - ocnt[q]]++;
    }
    int tot = 0, left = tok;
    for (int d = 4; d >= 1; --d) {
        int take = hist[d] < left ? hist[d] : left;
        left -= take;
        tot += (hist[d] - take) * d;
    }
    return tot <= DM;
}

struct fr { int cur, corb, ports, tok, au, bu, eu, hu, mv; int t, isd, newh, fr2, se; };
static struct fr st[900];

/* move index -> (target, kind) in the REVERSED order described above */
static int nextmove(int cur, int mv, int *isd) {
    int nh = HVOFF2[cur + 1] - HVOFF2[cur];
    if (mv < nh) { *isd = 3; return HV2[HVOFF2[cur] + mv]; }
    mv -= nh;
    if (mv == 0) { *isd = 2; return DB2[cur]; }
    if (mv == 1) { *isd = 1; return DA2[cur]; }
    if (mv < 7) { *isd = 0; return PAID2[cur * 5 + (6 - mv)]; }
    if (mv == 7) { *isd = -1; return FREE2[cur]; }
    return -2;
}
static int movecost(int cur, int mv) {
    int nh = HVOFF2[cur + 1] - HVOFF2[cur];
    return mv < nh ? HVC2[HVOFF2[cur] + mv] : 0;
}

static int search(void) {
    memset(used, 0, sizeof used);
    memset(hcnt, 0, sizeof hcnt);
    memset(ocnt, 0, sizeof ocnt);
    used[0] = 1; hcnt[HEX2[0]] = 1; ocnt[ORB2[0]] = 1;
    nhex = 1; ndef = 4; record = -1;
    int sp = 0;
    st[0] = (struct fr){0, ORB2[0], 1, B0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
    while (sp >= 0) {
        struct fr *f = &st[sp];
        if (f->mv == 0) {                       /* first visit to this node */
            ++nodes;
            if (NCAP && nodes > NCAP) { capped = 1; return record; }
            if (ndef <= DM && f->ports > record) record = f->ports;
            int reach = f->ports - 1 +
                ubound(f->tok, DM - ndef + 4 + 5 * f->tok, AM - f->au,
                       BM - f->bu, EM - f->eu, HM - f->hu);
            int reach2 = f->ports + (NH2 - nhex)
                + (AM - f->au) + (BM - f->bu) + (EM - f->eu);
            if (reach2 < reach) reach = reach2;
            if (!feas(f->tok, f->corb) || (BESTP && reach <= record)) {
                --sp;
                if (sp >= 0) {
                    struct fr *g = &st[sp];
                    --hcnt[HEX2[g->t]];
                    if (g->newh) --nhex;
                    if (g->fr2) ndef -= 4; else ndef += 1;
                    --ocnt[ORB2[g->t]];
                    used[g->t] = 0;
                }
                continue;
            }
        }
        int isd, t = nextmove(f->cur, f->mv, &isd);
        if (t == -2) {                          /* exhausted: pop */
            --sp;
            if (sp >= 0) {
                struct fr *g = &st[sp];
                --hcnt[HEX2[g->t]];
                if (g->newh) --nhex;
                if (g->fr2) ndef -= 4; else ndef += 1;
                --ocnt[ORB2[g->t]];
                used[g->t] = 0;
            }
            continue;
        }
        int cost_h = movecost(f->cur, f->mv);
        ++f->mv;
        if (t < 0) continue;
        if (used[t]) continue;                  /* ports are distinct */
        if (isd == 3 && f->hu + cost_h > HM) continue;
        int newh = (hcnt[HEX2[t]] == 0);
        int se = 0;
        if (!newh && (isd == 0 || isd == -1 || isd == 3)) {
            if (f->eu >= EM) continue;
            se = 1;
        }
        if (isd == 1 && f->au >= AM) continue;
        if (isd == 2 && f->bu >= BM) continue;
        int q = ORB2[t];
        int fresh = (ocnt[q] == 0);
        if (isd == -1 && q != f->corb) continue; /* the free E edge stays in */
        int cost = (isd == -1 || fresh) ? 0 : 1;
        if (cost > f->tok) continue;
        /* apply */
        used[t] = 1;
        ++ocnt[q];
        if (fresh) ndef += 4; else ndef -= 1;
        if (newh) ++nhex;
        ++hcnt[HEX2[t]];
        f->t = t; f->isd = isd; f->newh = newh; f->fr2 = fresh; f->se = se;
        ++sp;
        st[sp] = (struct fr){t, q, f->ports + 1, f->tok - cost,
                             f->au + (isd == 1), f->bu + (isd == 2),
                             f->eu + se, f->hu + (isd == 3 ? cost_h : 0),
                             0, 0, 0, 0, 0, 0};
    }
    return record;
}

int main(int argc, char **argv) {
    B0 = argc > 1 ? atoi(argv[1]) : 0;
    DM = argc > 2 ? atoi(argv[2]) : 0;
    AM = argc > 3 ? atoi(argv[3]) : 0;
    BM = argc > 4 ? atoi(argv[4]) : 0;
    EM = argc > 5 ? atoi(argv[5]) : 0;
    HM = argc > 6 ? atoi(argv[6]) : 0;
    NCAP = argc > 7 ? strtoull(argv[7], NULL, 10) : 0;
    if (DM > UBD || AM > UBA || BM > UBA || EM > UBA || HM > UBH
        || B0 < 0 || B0 > UBT) { fprintf(stderr, "budget\n"); return 2; }
    SAFE = 120 + AM + BM + EM;
    UB = malloc(UBSIZE * sizeof *UB);
    if (!UB) { fprintf(stderr, "alloc\n"); return 2; }
    for (size_t i = 0; i < UBSIZE; ++i) UB[i] = SAFE;
    if (argc > 8 && strcmp(argv[8], "-")) {
        FILE *fp = fopen(argv[8], "r");
        if (!fp) { fprintf(stderr, "ubfile\n"); return 3; }
        char magic[8]; long want = -1, got = 0;
        if (fscanf(fp, "%7s %ld", magic, &want) != 2 || strcmp(magic, "UB7")) {
            fprintf(stderr, "magic\n"); return 3; }
        int t, d, a, b, e, h, v;
        unsigned char *seen = calloc(UBSIZE, 1);
        while (fscanf(fp, "%d %d %d %d %d %d %d", &t, &d, &a, &b, &e, &h, &v) == 7) {
            if (t < 0 || t > UBT || d < 0 || d > UBD || a < 0 || a > UBA
                || b < 0 || b > UBA || e < 0 || e > UBA || h < 0 || h > UBH
                || v < 0 || v > SAFE) { fprintf(stderr, "range\n"); return 3; }
            size_t k = UBIDX(t, d, a, b, e, h);
            if (seen[k] && UB[k] != v) { fprintf(stderr, "dup\n"); return 3; }
            seen[k] = 1; UB[k] = v; ++got;
        }
        if (!feof(fp) || got != want) { fprintf(stderr, "rows\n"); return 3; }
        fclose(fp); free(seen); have_ub = 1;
    }
    BESTP = argc > 9 ? atoi(argv[9]) : have_ub;
    clock_t t0 = clock();
    int cc = search();
    printf("{\"impl\":\"C2_147\",\"b\":%d,\"dmax\":%d,\"amax\":%d,\"bmax\":%d,"
           "\"emax\":%d,\"hmax\":%d,\"cc\":%d,\"nodes\":%llu,\"capped\":%s,"
           "\"bestprune\":%d,\"pruned\":%s,\"seconds\":%.2f}\n",
           B0, DM, AM, BM, EM, HM, cc, (unsigned long long)nodes,
           capped ? "true" : "false", BESTP, have_ub ? "true" : "false",
           (double)(clock() - t0) / CLOCKS_PER_SEC);
    return 0;
}
