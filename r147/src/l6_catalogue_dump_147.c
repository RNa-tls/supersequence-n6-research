/* L6 endgame — COUPLED chain capacity CC(b, D, a).
 *
 * A "chain" is a whole nonpure beta component of the Round142 extraction,
 * BEFORE it is cut into hex-simple pieces: the type A (sigma) and type B
 * (sigma^2) dirty edges are RETAINED, and they are the only edges allowed to
 * land in an already visited rotation hexagon (their target's hexagon is the
 * source's, by construction).  Every other edge must land in a fresh hexagon.
 *
 * This removes the double counting of the piece model: the first port of the
 * piece after an A seam is not free, it is literally sigma(v).  In particular
 * the companion-hexagon lemma no longer has to be imposed by hand -- if the
 * block before the seam is full then E(v) is occupied, and the port
 * sigma^{-1}(E v) of the next orbit carries hex h(E v), so the next block
 * cannot be full either.  The searcher enforces that automatically.
 *
 * Budgets, all summed over the chains of one arithmetic row:
 *   sum over chains of tokens  = B* - s,      tokens = non-E entries into an
 *                                             already opened orbit
 *   sum over chains of deficit = 5k - G + 5s
 *   sum over chains of a       = D2 + Qs      (retained same-hex dirty edges)
 *   number of chains           = d + 1        (heavy joints kept INSIDE)
 *   sum of heavy cost sum(w-3) <= H
 *   sum of EXTRA hex reuses    = Z - Qs        (see below)
 *
 * EXTRA reuses.  A chain is NOT hexagon-simple: the piece decomposition also
 * cuts it at ordinary hexagon collisions.  Their number is bounded by the
 * within-component duplicate-hex excess R_int <= 2g minus the one collision
 * each retained A/B edge already forces, i.e. by 2g-D2-Qs+x+y <= Z-Qs.  So the
 * searcher takes a separate budget EMAX of collisions at ARBITRARY edges.
 * At Z = Qs (in particular at Z = 0) that budget is zero.  Taking amax = D2,
 * bmax = Qs and emax = Z-Qs at the same time is generous to the hypothetical
 * cover, hence sound.
 *
 * HEAVY joints.  A joint of weight w >= 4 was cut in the extraction, which
 * handed the piece model h <= H extra free objects.  Keeping it inside costs a
 * budget instead: its target ranges only over the 24 / 120 / 566 shortest
 * weight-4 / 5 / 6 connectors out of end(v), it obeys the same hexagon and
 * orbit rules as any other paid edge, and it consumes w-3 units of H.  With
 * HMAX = H the number of chains drops from d+1+h to d+1.
 *
 * WITNESS mode.  With a 10th argument (a path) the searcher dumps every chain
 * whose port count equals TARGET and whose deficit equals DMAX exactly, one
 * JSON object per line.  The best-so-far prune is switched OFF in that mode
 * (it could discard a chain that merely TIES the record), leaving only the
 * sound deficit, hexagon and target prunes, so the dump is exhaustive whenever
 * the run ends uncapped.
 *
 * ==========================================================================
 * ROUND 147 -- SOUND PRUNING TABLE (OPTION A: FULL BUDGET KEY).
 *
 * The round-144 table was keyed by the SUM of the remaining budgets,
 *     left = (AMAX-au) + (BMAX-bu) + (EMAX-eu),
 * while the generator emitted one line per SPLIT under that summed key and
 * this loader kept the MINIMUM.  A value keyed by a sum has to dominate EVERY
 * split with that sum; the minimum does the opposite, so the table handed the
 * search bounds BELOW the truth and the search over-pruned.  Measured:
 * b=0 d=0 e=9 recorded 45, true 50; e=10 recorded 40, true 55.
 * See research/ERRATA_146_CHAIN_UB.md.
 *
 * This version DISCARDS NOTHING: the table is keyed by the full remaining
 * budget vector
 *     UB[tok][d][a_left][bb_left][e_left][h_left]
 * so no aggregation over splits happens at all and no dominating-maximum
 * argument is needed.  Soundness of an entry reduces to: the value stored at a
 * key is an upper bound for the capacity of a chain with exactly those
 * budgets.  The generator only ever stores (i) an exact uncapped capacity of
 * that very key, (ii) an exact uncapped capacity of a key that DOMINATES it
 * componentwise (capacity is monotone non-decreasing in every budget), or
 * (iii) the analytic bound 120 + a + bb + e.
 *
 * FAIL-CLOSED LOADING.  The table file must start with the magic line
 *     UB7 <count>
 * and carry exactly <count> following rows of exactly 7 integers
 *     tok d a bb e h value
 * The loader aborts (exit 3) on: wrong magic, wrong arity, a short or long
 * file, an out-of-range index, a value outside [0,200], a DUPLICATE key whose
 * value differs from the one already seen, or a violation of the monotonicity
 * the table is required to satisfy (non-decreasing in d, a, bb, e, h).  It
 * never silently repairs anything -- in particular it does NOT monotonise the
 * table itself, because raising an entry to a neighbour's value is exactly the
 * operation that turned a sound file into an unsound one in round 144.
 *
 * (catalogue dumper build)
 * Usage: ./l6chain147 b dmax amax bmax emax hmax [node_cap] [ubfile] [target]
 *                     [witness] [bestprune]
 *   ubfile "-"      : no table at all (ubound == 120), for the no-UB controls
 *   bestprune 0/1   : best-so-far prune; defaults to 1 with a table, 0 without.
 *                     It is sound either way (it only ever discards states
 *                     whose PROVED reach cannot beat the record) -- the default
 *                     keeps the round-144/146 behaviour bit for bit so the
 *                     no-UB control runs are directly comparable.
 * Output: one JSON object.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

#define NW 720
#define NQ 144
#define NH 120
#define UBD 40
#define UBA 24          /* per-budget cap: a_left, bb_left, e_left each <= UBA */
#define UBH 6
#define UBT 5           /* tok index 0..UBT */

static unsigned char W[NW][6];
static int nW;
static int hexid[NW], orbid[NW], phase[NW];
static int freetgt[NW], paidtgt[NW][5], paidkind[NW][5];
static int dirtyA[NW], dirtyB[NW];
#define MAXHV 720
static int heavy[NW][MAXHV], heavycost[NW][MAXHV], nheavy[NW];
static const char *KN[5] = {"120", "201", "210", "E_SIGMA", "SIGMA_E"};

static int rankw(const unsigned char *p) {
    static const int f[6] = {120, 24, 6, 2, 1, 1};
    int r = 0; unsigned used = 0;
    for (int i = 0; i < 6; ++i) {
        if (p[i] > 5 || (used >> p[i] & 1)) return -1;
        int s = 0; for (int j = 0; j < p[i]; ++j) if (!(used >> j & 1)) ++s;
        r += s * f[i]; used |= 1u << p[i];
    }
    return r;
}
static void gen(int d, unsigned used, unsigned char *w) {
    if (d == 6) { memcpy(W[nW++], w, 6); return; }
    for (int v = 0; v < 6; ++v) if (!(used >> v & 1)) { w[d] = (unsigned char)v; gen(d + 1, used | 1u << v, w); }
}
static void geometry(void) {
    unsigned char w[6], p[6];
    gen(0, 0, w);
    if (nW != NW) exit(2);
    int hmap[NW], qmap[NW], hc = 0, qc = 0;
    for (int i = 0; i < NW; ++i) hmap[i] = qmap[i] = -1;
    for (int v = 0; v < NW; ++v) {
        int h = v, q = v;
        for (int s = 1; s < 6; ++s) { for (int j = 0; j < 6; ++j) p[j] = W[v][(j + s) % 6];
            int r = rankw(p); if (r < h) h = r; }
        for (int s = 1; s < 5; ++s) { for (int j = 0; j < 5; ++j) p[j] = W[v][(j + s) % 5];
            p[5] = W[v][5]; int r = rankw(p); if (r < q) q = r; }
        if (hmap[h] < 0) hmap[h] = hc++;
        if (qmap[q] < 0) qmap[q] = qc++;
        hexid[v] = hmap[h]; orbid[v] = qmap[q];
        phase[v] = -1;
        for (int s = 0; s < 5; ++s) { for (int j = 0; j < 5; ++j) p[j] = W[q][(j + s) % 5];
            p[5] = W[q][5]; if (!memcmp(p, W[v], 6)) phase[v] = s; }
        if (phase[v] < 0) exit(2);
    }
    if (hc != NH || qc != NQ) exit(2);
    for (int v = 0; v < NW; ++v) {
        unsigned char e[6], raw[9];
        e[0] = W[v][5];
        for (int j = 1; j < 6; ++j) e[j] = W[v][j - 1];
        int nf = 0, np = 0, na = 0, nb = 0;
        freetgt[v] = dirtyA[v] = dirtyB[v] = -1;
        for (int t = 0; t < NW; ++t) {
            int gap = 6;
            for (int k = 1; k < 6; ++k) if (!memcmp(e + k, W[t], (size_t)(6 - k))) { gap = k; break; }
            if (gap != 2 && gap != 3) continue;
            memcpy(raw, e, 6); memcpy(raw + 6, W[t] + 6 - gap, (size_t)gap);
            int hid[2], nh = 0;
            for (int o = 1; o < gap; ++o) { int r = rankw(raw + o); if (r >= 0) hid[nh++] = r; }
            if (gap == 2) {
                if (!nh) { freetgt[v] = t; ++nf; }
                else if (nh == 1 && hid[0] == v) { dirtyA[v] = t; ++na; }
                continue;
            }
            if (nh == 2 && hid[0] == v && hexid[t] == hexid[v]) { dirtyB[v] = t; ++nb; continue; }
            int kind = -1;
            if (!nh) {
                int d0[3];
                for (int j = 0; j < 3; ++j) { d0[j] = -1;
                    for (int x = 0; x < 3; ++x) if (W[t][3 + j] == e[x]) d0[j] = x; }
                int code = 100 * d0[0] + 10 * d0[1] + d0[2];
                if (code == 120) kind = 0; else if (code == 201) kind = 1;
                else if (code == 210) kind = 2;
            } else if (nh == 1 && hid[0] == v) kind = 3;
            else if (nh == 1) { for (int j = 0; j < 6; ++j) p[j] = W[hid[0]][(j + 1) % 6];
                if (!memcmp(p, W[t], 6)) kind = 4; }
            if (kind < 0) continue;
            if (np >= 5) exit(2);
            paidtgt[v][np] = t; paidkind[v][np++] = kind;
        }
        nheavy[v] = 0;
        for (int t = 0; t < NW; ++t) {
            if (t == v) continue;
            int gap = 6;
            for (int k = 1; k < 6; ++k) if (!memcmp(e + k, W[t], (size_t)(6 - k))) { gap = k; break; }
            if (gap < 4) continue;
            if (!memcmp(W[t], e, 6)) continue;      /* the identity connector */
            heavycost[v][nheavy[v]] = gap - 3;
            heavy[v][nheavy[v]++] = t;
        }
        if (nf != 1 || np != 5 || na != 1 || nb != 1) {
            fprintf(stderr, "catalogue v=%d nf=%d np=%d na=%d nb=%d\n", v, nf, np, na, nb); exit(2); }
        if (hexid[dirtyA[v]] != hexid[v] || hexid[dirtyB[v]] != hexid[v]) exit(2);
    }
}


/* ---------------------------------------------------------------------------
 * ROUND 147 -- catalogue dumper.  Prints the geometry tables this searcher
 * builds, so an INDEPENDENT reconstruction (r147/src/catalogue147.py, pure
 * string algebra on the 720 permutations) can be compared against them field
 * by field.  Nothing here searches.
 * ------------------------------------------------------------------------- */
int main(void) {
    geometry();
    printf("{\n \"n\": %d,\n", NW);
    printf(" \"words\": [");
    for (int v = 0; v < NW; ++v) {
        printf("%s\"", v ? "," : "");
        for (int j = 0; j < 6; ++j) printf("%d", W[v][j] + 1);
        printf("\"");
    }
    printf("],\n");
    printf(" \"hexid\": [");
    for (int v = 0; v < NW; ++v) printf("%s%d", v ? "," : "", hexid[v]);
    printf("],\n \"orbid\": [");
    for (int v = 0; v < NW; ++v) printf("%s%d", v ? "," : "", orbid[v]);
    printf("],\n \"phase\": [");
    for (int v = 0; v < NW; ++v) printf("%s%d", v ? "," : "", phase[v]);
    printf("],\n \"freetgt\": [");
    for (int v = 0; v < NW; ++v) printf("%s%d", v ? "," : "", freetgt[v]);
    printf("],\n \"dirtyA\": [");
    for (int v = 0; v < NW; ++v) printf("%s%d", v ? "," : "", dirtyA[v]);
    printf("],\n \"dirtyB\": [");
    for (int v = 0; v < NW; ++v) printf("%s%d", v ? "," : "", dirtyB[v]);
    printf("],\n \"paidtgt\": [");
    for (int v = 0; v < NW; ++v) {
        printf("%s[", v ? "," : "");
        for (int i = 0; i < 5; ++i) printf("%s%d", i ? "," : "", paidtgt[v][i]);
        printf("]");
    }
    printf("],\n \"paidkind\": [");
    for (int v = 0; v < NW; ++v) {
        printf("%s[", v ? "," : "");
        for (int i = 0; i < 5; ++i) printf("%s%d", i ? "," : "", paidkind[v][i]);
        printf("]");
    }
    printf("],\n \"heavy\": [");
    for (int v = 0; v < NW; ++v) {
        printf("%s[", v ? "," : "");
        for (int i = 0; i < nheavy[v]; ++i)
            printf("%s[%d,%d]", i ? "," : "", heavy[v][i], heavycost[v][i]);
        printf("]");
    }
    printf("]\n}\n");
    return 0;
}
