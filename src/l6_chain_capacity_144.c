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
 *   number of chains           = d + 1 + h
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
 * Usage: ./l6chain b dmax amax bmax emax [node_cap] [ubfile] [target]
 * ubfile lines: "b d a value" with a = amax+bmax.  Output: one JSON object.
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
#define UBA 24

static unsigned char W[NW][6];
static int nW;
static int hexid[NW], orbid[NW], phase[NW];
static int freetgt[NW], paidtgt[NW][5], paidkind[NW][5];
static int dirtyA[NW], dirtyB[NW];
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
        if (nf != 1 || np != 5 || na != 1 || nb != 1) {
            fprintf(stderr, "catalogue v=%d nf=%d np=%d na=%d nb=%d\n", v, nf, np, na, nb); exit(2); }
        if (hexid[dirtyA[v]] != hexid[v] || hexid[dirtyB[v]] != hexid[v]) exit(2);
    }
}

static int BOUND_B, DMAX, AMAX, BMAX, EMAX, TARGET;
static uint64_t NODECAP, nodes, capped;
static unsigned char hexu[NH], phm[NQ];
static int opened[NQ], nopened, deficit;
static int best[UBD + 1];
static int record;
static int UB[6][UBD + 1][UBA + 1];
static int have_ub;

static int ubound(int tok, int d, int a) {
    if (!have_ub) return 120;
    if (tok > 5) tok = 5;
    if (d < 0) d = 0; if (d > UBD) d = UBD;
    if (a < 0) a = 0; if (a > UBA) a = UBA;
    return UB[tok][d][a];
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

static void step(int t, int corb, int ports, int tok, int au, int bu, int eu, int isdirty);

static void rec(int cur, int corb, int ports, int tok, int au, int bu, int eu) {
    ++nodes;
    if (NODECAP && nodes > NODECAP) { capped = 1; return; }
    if (deficit <= DMAX) {
        if (ports > best[deficit]) best[deficit] = ports;
        if (ports > record) record = ports;
    }
    if (!feas(tok, corb)) return;
    int reach = ports + ubound(tok, DMAX - deficit + 4 + 5 * tok,
                               (AMAX - au) + (BMAX - bu) + (EMAX - eu)) - 1;
    if (TARGET && reach < TARGET) return;
    if (have_ub && reach <= record) return;
    step(freetgt[cur], corb, ports, tok, au, bu, eu, -1);          /* free E */
    for (int i = 0; i < 5; ++i)
        step(paidtgt[cur][i], corb, ports, tok, au, bu, eu, 0);    /* paid */
    if (au < AMAX) step(dirtyA[cur], corb, ports, tok, au, bu, eu, 1);
    if (bu < BMAX) step(dirtyB[cur], corb, ports, tok, au, bu, eu, 2);
}

static void step(int t, int corb, int ports, int tok, int au, int bu, int eu, int isdirty) {
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
    if (newhex) hexu[hexid[t]] = 1;
    rec(t, q, ports + 1, tok - cost, au + (isdirty == 1), bu + (isdirty == 2),
        eu + spend_e);
    if (newhex) hexu[hexid[t]] = 0;
    if (fresh) { --nopened; deficit -= 4; } else deficit += 1;
    phm[q] = old;
}

int main(int argc, char **argv) {
    BOUND_B = argc > 1 ? atoi(argv[1]) : 0;
    DMAX    = argc > 2 ? atoi(argv[2]) : 6;
    AMAX    = argc > 3 ? atoi(argv[3]) : 0;
    BMAX    = argc > 4 ? atoi(argv[4]) : 0;
    EMAX    = argc > 5 ? atoi(argv[5]) : 0;
    NODECAP = argc > 6 ? strtoull(argv[6], NULL, 10) : 0;
    if (DMAX > UBD || AMAX + BMAX + EMAX > UBA) { fprintf(stderr, "budget too large\n"); return 2; }
    geometry();
    for (int i = 0; i < 6; ++i) for (int j = 0; j <= UBD; ++j) for (int a = 0; a <= UBA; ++a)
        UB[i][j][a] = 120;
    if (argc > 7 && strcmp(argv[7], "-")) {
        FILE *f = fopen(argv[7], "r");
        if (!f) { fprintf(stderr, "ubfile\n"); return 2; }
        int bb, dd, aa, vv;
        while (fscanf(f, "%d %d %d %d", &bb, &dd, &aa, &vv) == 4)
            if (bb >= 0 && bb < 6 && dd >= 0 && dd <= UBD && aa >= 0 && aa <= UBA
                && vv < UB[bb][dd][aa]) UB[bb][dd][aa] = vv;
        fclose(f);
        for (int i = 0; i < 6; ++i)            /* monotone in d and in a */
            for (int j = 0; j <= UBD; ++j) for (int a = 0; a <= UBA; ++a) {
                if (j && UB[i][j][a] < UB[i][j - 1][a]) UB[i][j][a] = UB[i][j - 1][a];
                if (a && UB[i][j][a] < UB[i][j][a - 1]) UB[i][j][a] = UB[i][j][a - 1];
            }
        have_ub = 1;
    }
    TARGET = argc > 8 ? atoi(argv[8]) : 0;
    for (int d = 0; d <= UBD; ++d) best[d] = -1;
    record = -1;
    memset(hexu, 0, sizeof hexu); memset(phm, 0, sizeof phm);
    hexu[hexid[0]] = 1; phm[orbid[0]] = (unsigned char)(1u << phase[0]);
    opened[nopened++] = orbid[0]; deficit = 4;
    clock_t t0 = clock();
    rec(0, orbid[0], 1, BOUND_B, 0, 0, 0);
    double secs = (double)(clock() - t0) / CLOCKS_PER_SEC;
    int run = -1, cum[UBD + 1];
    for (int d = 0; d <= DMAX; ++d) { if (best[d] > run) run = best[d]; cum[d] = run; }
    printf("{\"b\":%d,\"dmax\":%d,\"amax\":%d,\"bmax\":%d,\"emax\":%d,\"nodes\":%llu,\"capped\":%s,"
           "\"seconds\":%.1f,\"pruned\":%s,\"target\":%d,\"cc\":%d,\"table\":{",
           BOUND_B, DMAX, AMAX, BMAX, EMAX, (unsigned long long)nodes, capped ? "true" : "false",
           secs, have_ub ? "true" : "false", TARGET, cum[DMAX]);
    for (int d = 0; d <= DMAX; ++d) printf("%s\"%d\":%d", d ? "," : "", d, cum[d]);
    printf("},\"kinds\":[\"E\",\"%s\",\"%s\",\"%s\",\"%s\",\"%s\",\"A\",\"B\"]}\n",
           KN[0], KN[1], KN[2], KN[3], KN[4]);
    return 0;
}
