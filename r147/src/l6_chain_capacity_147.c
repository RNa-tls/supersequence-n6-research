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

static int BOUND_B, DMAX, AMAX, BMAX, EMAX, HMAX, TARGET;
static FILE *WIT;
static uint64_t witcount;
static int trail[800];
static uint64_t NODECAP, nodes, capped;
static unsigned char hexu[NH], phm[NQ];
static int opened[NQ], nopened, deficit, hexcount;
static int best[UBD + 1];
static int record;
static int *UB;                 /* [tok][d][a][bb][e][h], full budget vector */
static int have_ub, BESTPRUNE, SAFEUB;
#define UBIDX(t, d, a, b, e, h) \
    ((((((size_t)(t) * (UBD + 1) + (d)) * (UBA + 1) + (a)) * (UBA + 1) + (b)) \
        * (UBA + 1) + (e)) * (UBH + 1) + (h))
#define UBSIZE ((size_t)(UBT + 1) * (UBD + 1) * (UBA + 1) * (UBA + 1) \
                * (UBA + 1) * (UBH + 1))

/* UB[tok][d][a][bb][e][h] must bound the ports reachable by a chain with tok
 * tokens, deficit budget d, and a / bb / e / h units of type-A, type-B,
 * ordinary-collision and heavy budget left.  Nothing is aggregated, so there
 * is no split to dominate: each entry stands on its own.  Clamping UPWARD is
 * sound because capacity is monotone non-decreasing in every budget, and the
 * loader has verified that the stored table is monotone in the same directions. */
static int ubound(int tok, int d, int a, int b, int e, int h) {
    if (!have_ub) return SAFEUB;
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
static int pc5(unsigned x) { int c = 0; while (x) { x &= x - 1; ++c; } return c; }
static int feas(int tok, int skip) {
    int hist[5] = {0, 0, 0, 0, 0};
    for (int i = 0; i < nopened; ++i) {
        int q = opened[i]; if (q == skip) continue;
        hist[5 - pc5(phm[q])]++;
    }
    int tot = 0, left = tok;
    for (int d = 4; d >= 1; --d) { int take = hist[d] < left ? hist[d] : left;
        left -= take; tot += (hist[d] - take) * d; }
    return tot <= DMAX;
}

static void step(int t, int corb, int ports, int tok, int au, int bu, int eu,
                 int hu, int isdirty);

static void rec(int cur, int corb, int ports, int tok, int au, int bu, int eu,
                int hu) {
    ++nodes;
    if (NODECAP && nodes > NODECAP) { capped = 1; return; }
    if (deficit <= DMAX) {
        if (ports > best[deficit]) best[deficit] = ports;
        if (ports > record) record = ports;
        if (WIT && ports == TARGET && deficit == DMAX) {
            ++witcount;
            fputs("{\"ports\":[", WIT);
            for (int i = 0; i < ports; ++i) fprintf(WIT, "%s%d", i ? "," : "", trail[i]);
            fputs("]}\n", WIT);
            if (ferror(WIT)) { fprintf(stderr, "witness write\n"); exit(2); }
        }
    }
    if (!feas(tok, corb)) return;
    int left = (AMAX - au) + (BMAX - bu) + (EMAX - eu);
    int reach = ports + ubound(tok, DMAX - deficit + 4 + 5 * tok,
                               AMAX - au, BMAX - bu, EMAX - eu, HMAX - hu) - 1;
    /* every further port needs a fresh hexagon or one unit of the reuse budget */
    int reach2 = ports + (NH - hexcount) + left;   /* heavy edges need fresh hexes too */
    if (reach2 < reach) reach = reach2;
    if (TARGET && reach < TARGET) return;
    if (BESTPRUNE && !WIT && reach <= record) return;
    step(freetgt[cur], corb, ports, tok, au, bu, eu, hu, -1);      /* free E */
    for (int i = 0; i < 5; ++i)
        step(paidtgt[cur][i], corb, ports, tok, au, bu, eu, hu, 0);
    if (au < AMAX) step(dirtyA[cur], corb, ports, tok, au, bu, eu, hu, 1);
    if (bu < BMAX) step(dirtyB[cur], corb, ports, tok, au, bu, eu, hu, 2);
    for (int i = 0; i < nheavy[cur]; ++i)                          /* w >= 4 */
        if (hu + heavycost[cur][i] <= HMAX)
            step(heavy[cur][i], corb, ports, tok, au, bu, eu,
                 hu + heavycost[cur][i], 0);
}

static void step(int t, int corb, int ports, int tok, int au, int bu, int eu,
                 int hu, int isdirty) {
    if (capped) return;
    int newhex = !hexu[hexid[t]];
    int spend_e = 0;
    if (!newhex && isdirty <= 0) {              /* an ordinary hexagon collision */
        if (eu >= EMAX) return;
        spend_e = 1;
    }
    int q = orbid[t];
    if (phm[q] >> phase[t] & 1) return;         /* ports are distinct */
    int fresh = (phm[q] == 0);
    int cost = (isdirty == -1 || fresh) ? 0 : 1;   /* free E never costs */
    if (isdirty == -1 && q != corb) return;     /* the free E edge stays in the orbit */
    if (cost > tok) return;
    unsigned char old = phm[q];
    phm[q] = (unsigned char)(old | (1u << phase[t]));
    if (fresh) { opened[nopened++] = q; deficit += 4; } else deficit -= 1;
    if (newhex) { hexu[hexid[t]] = 1; ++hexcount; }
    trail[ports] = t;
    rec(t, q, ports + 1, tok - cost, au + (isdirty == 1), bu + (isdirty == 2),
        eu + spend_e, hu);
    if (newhex) { hexu[hexid[t]] = 0; --hexcount; }
    if (fresh) { --nopened; deficit -= 4; } else deficit += 1;
    phm[q] = old;
}

int main(int argc, char **argv) {
    BOUND_B = argc > 1 ? atoi(argv[1]) : 0;
    DMAX    = argc > 2 ? atoi(argv[2]) : 6;
    AMAX    = argc > 3 ? atoi(argv[3]) : 0;
    BMAX    = argc > 4 ? atoi(argv[4]) : 0;
    EMAX    = argc > 5 ? atoi(argv[5]) : 0;
    HMAX    = argc > 6 ? atoi(argv[6]) : 0;
    NODECAP = argc > 7 ? strtoull(argv[7], NULL, 10) : 0;
    if (DMAX > UBD || AMAX > UBA || BMAX > UBA || EMAX > UBA || HMAX > UBH
        || BOUND_B < 0 || BOUND_B > UBT) {
        fprintf(stderr, "budget out of range\n"); return 2; }
    geometry();
    /* PROVED unconditional bound, used where the table says nothing.
     * Every port of a chain occupies a distinct rotation hexagon unless it is
     * a type-A / type-B dirty edge or an ordinary hexagon collision, and those
     * are exactly what the a / bb / e budgets pay for.  Hence
     *     ports <= 120 + AMAX + BMAX + EMAX.
     * The round-144 code used the constant 120 here, which is NOT a bound when
     * the reuse budget is positive: with a target above 120 that pruned the
     * root and made the whole run vacuous (observed in the round-146 recheck
     * of cell 2|8|2|0|0: 1 node, "proved" CC <= 121). */
    SAFEUB = 120 + AMAX + BMAX + EMAX;
    UB = malloc(UBSIZE * sizeof *UB);
    if (!UB) { fprintf(stderr, "ub alloc\n"); return 2; }
    for (size_t i = 0; i < UBSIZE; ++i) UB[i] = SAFEUB;
    if (argc > 8 && strcmp(argv[8], "-")) {
        FILE *f = fopen(argv[8], "r");
        if (!f) { fprintf(stderr, "ubfile: cannot open %s\n", argv[8]); return 3; }
        char magic[8]; long want = -1;
        if (fscanf(f, "%7s %ld", magic, &want) != 2 || strcmp(magic, "UB7")
            || want < 0) {
            fprintf(stderr, "ubfile: bad magic (expected \"UB7 <count>\")\n");
            return 3; }
        unsigned char *seen = calloc(UBSIZE, 1);
        if (!seen) { fprintf(stderr, "seen alloc\n"); return 2; }
        long got = 0;
        int t, dd, aa, bb2, ee, hh, vv;
        while (fscanf(f, "%d %d %d %d %d %d %d",
                      &t, &dd, &aa, &bb2, &ee, &hh, &vv) == 7) {
            if (t < 0 || t > UBT || dd < 0 || dd > UBD || aa < 0 || aa > UBA
                || bb2 < 0 || bb2 > UBA || ee < 0 || ee > UBA
                || hh < 0 || hh > UBH || vv < 0 || vv > SAFEUB) {
                fprintf(stderr, "ubfile: row %ld out of range\n", got + 1);
                return 3; }
            size_t k = UBIDX(t, dd, aa, bb2, ee, hh);
            if (seen[k] && UB[k] != vv) {
                fprintf(stderr, "ubfile: duplicate key %d %d %d %d %d %d with "
                        "conflicting values %d and %d\n",
                        t, dd, aa, bb2, ee, hh, UB[k], vv);
                return 3; }
            seen[k] = 1; UB[k] = vv; ++got;
        }
        if (!feof(f)) { fprintf(stderr, "ubfile: malformed row %ld\n", got + 1);
                        return 3; }
        fclose(f);
        if (got != want) {
            fprintf(stderr, "ubfile: header says %ld rows, read %ld "
                    "(truncated or padded)\n", want, got); return 3; }
        /* VERIFY, never repair: the table must already be monotone
         * non-decreasing in d, a, bb, e and h. */
        for (int t2 = 0; t2 <= UBT; ++t2)
        for (int d2 = 0; d2 <= UBD; ++d2)
        for (int a2 = 0; a2 <= UBA; ++a2)
        for (int b2 = 0; b2 <= UBA; ++b2)
        for (int e2 = 0; e2 <= UBA; ++e2)
        for (int h2 = 0; h2 <= UBH; ++h2) {
            size_t k = UBIDX(t2, d2, a2, b2, e2, h2);
            int bad = 0;
            if (d2 && UB[k] < UB[UBIDX(t2, d2 - 1, a2, b2, e2, h2)]) bad = 1;
            if (a2 && UB[k] < UB[UBIDX(t2, d2, a2 - 1, b2, e2, h2)]) bad = 2;
            if (b2 && UB[k] < UB[UBIDX(t2, d2, a2, b2 - 1, e2, h2)]) bad = 3;
            if (e2 && UB[k] < UB[UBIDX(t2, d2, a2, b2, e2 - 1, h2)]) bad = 4;
            if (h2 && UB[k] < UB[UBIDX(t2, d2, a2, b2, e2, h2 - 1)]) bad = 5;
            if (bad) {
                fprintf(stderr, "ubfile: monotonicity violated (dir %d) at "
                        "%d %d %d %d %d %d\n", bad, t2, d2, a2, b2, e2, h2);
                return 3; }
        }
        free(seen);
        have_ub = 1;
    }
    BESTPRUNE = argc > 11 ? atoi(argv[11]) : have_ub;
    TARGET = argc > 9 ? atoi(argv[9]) : 0;
    if (argc > 10) {
        if (!TARGET) { fprintf(stderr, "witness mode needs a target\n"); return 2; }
        WIT = fopen(argv[10], "w");
        if (!WIT) { fprintf(stderr, "witness file\n"); return 2; }
    }
    for (int d = 0; d <= UBD; ++d) best[d] = -1;
    record = -1;
    memset(hexu, 0, sizeof hexu); memset(phm, 0, sizeof phm);
    hexu[hexid[0]] = 1; hexcount = 1;
    phm[orbid[0]] = (unsigned char)(1u << phase[0]);
    opened[nopened++] = orbid[0]; deficit = 4;
    clock_t t0 = clock();
    trail[0] = 0;
    rec(0, orbid[0], 1, BOUND_B, 0, 0, 0, 0);
    if (WIT) fclose(WIT);
    double secs = (double)(clock() - t0) / CLOCKS_PER_SEC;
    int run = -1, cum[UBD + 1];
    for (int d = 0; d <= DMAX; ++d) { if (best[d] > run) run = best[d]; cum[d] = run; }
    printf("{\"impl\":\"C147\",\"b\":%d,\"dmax\":%d,\"amax\":%d,\"bmax\":%d,\"emax\":%d,\"hmax\":%d,"
           "\"nodes\":%llu,\"capped\":%s,"
           "\"seconds\":%.1f,\"pruned\":%s,\"bestprune\":%d,"
           "\"target\":%d,\"cc\":%d,\"table\":{",
           BOUND_B, DMAX, AMAX, BMAX, EMAX, HMAX, (unsigned long long)nodes,
           capped ? "true" : "false",
           secs, have_ub ? "true" : "false", BESTPRUNE, TARGET, cum[DMAX]);
    for (int d = 0; d <= DMAX; ++d) printf("%s\"%d\":%d", d ? "," : "", d, cum[d]);
    printf("},\"witnesses\":%llu,\"heavy_targets\":%d,"
           "\"kinds\":[\"E\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"A\",\"B\",\"HEAVY\"]}\n",
           (unsigned long long)witcount, nheavy[0],
           KN[0], KN[1], KN[2], KN[3], KN[4]);
    return 0;
}
