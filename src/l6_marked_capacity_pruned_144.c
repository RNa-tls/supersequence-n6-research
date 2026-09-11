/* L6 endgame — PRUNED variant of the independent marked-capacity checker.
 *
 * Adds two SOUND prunes to src/l6_marked_capacity_144.c (kept verbatim
 * otherwise), so that the large-deficit cells become reachable:
 *
 *  (S) suffix bound.  At any node let dc = 5Q-P be the current deficit and
 *      let t be the tokens still unspent.  Writing the remainder of the chain
 *      together with the current port as a chain S in its own right,
 *          D_final = dc + 5*q_new - n_new,   D_S = 5*Q_S - P_S,
 *          Q_S = q_new + 1 + r,  P_S = n_new + 1,  r <= t
 *      gives  D_S = D_final - dc + 4 + 5r <= DMAX - dc + 4 + 5t.
 *      Hence  P_S <= U(t, DMAX - dc + 4 + 5t)  for any valid upper bound U,
 *      and the whole chain has at most  P + U(...) - 1  ports.
 *
 *  (B) best-so-far.  Entries are only improvable while
 *      P + (suffix bound) - 1 > the cumulative record for the still-possible
 *      endpoint masks.  With (B) active ONLY the d = DMAX column is exact;
 *      smaller-deficit columns become lower bounds.  Without a -u table the
 *      program behaves exactly like the unpruned checker.
 *
 * Usage: ./l6cap_p b dmax [AB|A] [node_cap] [ubfile] [target]
 * ubfile lines: "b d value"; target>0 keeps only the question "is target
 * reachable?" and prunes everything that provably cannot reach it.
 *
 * ORIGINAL HEADER FOLLOWS.
 * L6 endgame — INDEPENDENT second checker for the marked capacities C(b,D,mask).
 *
 * Materially different state representation from src/l6_marked_capacity_144.py:
 *   - geometry derived ONLY by literal string-overlap scanning of all 720x720
 *     ordered pairs with explicit hidden-permutation-window detection (the
 *     Python side builds the same maps algebraically from tau and sigma);
 *   - flat arrays for hexagon occupancy, per-orbit phase masks and an
 *     incrementally maintained deficit, instead of Python dicts recomputed
 *     from a per-deficit histogram;
 *   - the optimistic token relaxation is recomputed from a small sorted
 *     histogram kept alongside the phase masks.
 *
 * Usage:  ./l6cap  b  dmax  [AB|A]  [node_cap]
 * node_cap = 0 means uncapped.  Prints one JSON object.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

#define NW 720
#define NQ 144
#define NH 120

static unsigned char W[NW][6];
static int nW;
static int hexid[NW], orbid[NW], phase[NW];
static int freetgt[NW], paidtgt[NW][5], paidkind[NW][5];
/* kinds: 0=120 (same orbit +2), 1=201, 2=210, 3=E_SIGMA, 4=SIGMA_E */
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
    if (nW != NW) { fprintf(stderr, "word gen\n"); exit(2); }
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
        if (phase[v] < 0) { fprintf(stderr, "phase\n"); exit(2); }
    }
    if (hc != NH || qc != NQ) { fprintf(stderr, "counts\n"); exit(2); }
    for (int v = 0; v < NW; ++v) {
        unsigned char e[6], raw[9];
        e[0] = W[v][5];
        for (int j = 1; j < 6; ++j) e[j] = W[v][j - 1];     /* sigma^{-1}(v) */
        int nf = 0, np = 0;
        freetgt[v] = -1;
        for (int t = 0; t < NW; ++t) {
            int gap = 6;
            for (int k = 1; k < 6; ++k) { if (!memcmp(e + k, W[t], (size_t)(6 - k))) { gap = k; break; } }
            if (gap != 2 && gap != 3) continue;
            memcpy(raw, e, 6); memcpy(raw + 6, W[t] + 6 - gap, (size_t)gap);
            int hid[2], nh = 0;
            for (int o = 1; o < gap; ++o) { int r = rankw(raw + o); if (r >= 0) hid[nh++] = r; }
            if (gap == 2) { if (!nh) { freetgt[v] = t; ++nf; } continue; }
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
            if (np >= 5) { fprintf(stderr, "paid overflow\n"); exit(2); }
            paidtgt[v][np] = t; paidkind[v][np++] = kind;
        }
        if (nf != 1 || np != 5) { fprintf(stderr, "catalogue v=%d nf=%d np=%d\n", v, nf, np); exit(2); }
        if (orbid[freetgt[v]] != orbid[v] || phase[freetgt[v]] != (phase[v] + 1) % 5) {
            fprintf(stderr, "free edge\n"); exit(2); }
        unsigned seen = 0; for (int i = 0; i < 5; ++i) seen |= 1u << paidkind[v][i];
        if (seen != 31u) { fprintf(stderr, "kinds v=%d seen=%u\n", v, seen); exit(2); }
        for (int i = 0; i < 5; ++i) if (paidkind[v][i] == 0 &&
            (orbid[paidtgt[v][i]] != orbid[v] || phase[paidtgt[v][i]] != (phase[v] + 2) % 5)) {
            fprintf(stderr, "120 edge\n"); exit(2); }
    }
}

static int BOUND_B, DMAX, ALLOW_CD, SHADOW, TARGET;
#define UBD 40
static int UB[8][UBD + 1];
static int have_ub;
static int ubound(int tok, int d) {
    if (!have_ub) return 120;
    if (tok > 7) tok = 7;
    if (d < 0) d = 0;
    if (d > UBD) d = UBD;
    return UB[tok][d];
}
static uint64_t NODECAP, nodes, capped;
static unsigned char hexu[NH];
static unsigned char phm[NQ];
static int opened[NQ], nopened;
static int deficit;                     /* 5*Q - P */
static int best[32][2][2];              /* [deficit][first_partial][last_partial] */

static int pc5(unsigned x) { int c = 0; while (x) { x &= x - 1; ++c; } return c; }

/* optimistic: each remaining token may complete one already-opened orbit */
static int feas(int tok, int skip) {
    int hist[5] = {0, 0, 0, 0, 0};
    for (int i = 0; i < nopened; ++i) {
        int q = opened[i];
        int d = 5 - pc5(phm[q]);
        if (q == skip) continue;
        hist[d]++;
    }
    int tot = 0, left = tok;
    for (int d = 4; d >= 1; --d) {
        int take = hist[d] < left ? hist[d] : left;
        left -= take; tot += (hist[d] - take) * d;
    }
    return tot <= DMAX;
}

static int record[2][2];    /* cumulative best over all deficits <= DMAX */

static int mixed;           /* retained type C/D edges used so far */

static void rec(int cur, int corb, int ports, int tok, int firstlen, int curlen, int nblk) {
    ++nodes;
    if (NODECAP && nodes > NODECAP) { capped = 1; return; }
    if (SHADOW && mixed > DMAX) return;          /* SHADOW: mixed_j <= D_j */
    if (deficit <= DMAX && !(SHADOW && mixed > deficit)) {
        int fl = (nblk > 1) ? firstlen : curlen;
        int fp = fl < 5, lp = curlen < 5;
        if (ports > best[deficit][fp][lp]) best[deficit][fp][lp] = ports;
        if (ports > record[fp][lp]) record[fp][lp] = ports;
    }
    if (!feas(tok, corb)) return;
    if (have_ub || TARGET) {
        int reach = ports + ubound(tok, DMAX - deficit + 4 + 5 * tok) - 1;
        if (TARGET && reach < TARGET) return;
        if (have_ub) {
            int lim;
            if (nblk > 1) {
                int fp = firstlen < 5;
                lim = record[fp][0] < record[fp][1] ? record[fp][0] : record[fp][1];
            } else {
                lim = record[0][0];
                for (int a = 0; a < 2; ++a) for (int c = 0; c < 2; ++c)
                    if (record[a][c] < lim) lim = record[a][c];
            }
            if (reach <= lim) return;
        }
    }
    int t = freetgt[cur];
    if (!hexu[hexid[t]] && !(phm[corb] >> phase[t] & 1)) {
        phm[corb] |= (unsigned char)(1u << phase[t]);
        hexu[hexid[t]] = 1; --deficit;
        rec(t, corb, ports + 1, tok, firstlen, curlen + 1, nblk);
        ++deficit; hexu[hexid[t]] = 0;
        phm[corb] &= (unsigned char)~(1u << phase[t]);
    }
    for (int i = 0; i < 5; ++i) {
        int kind = paidkind[cur][i];
        if (!ALLOW_CD && kind == 4) continue;
        if (SHADOW && kind >= 3 && mixed >= DMAX) continue;
        t = paidtgt[cur][i];
        if (hexu[hexid[t]]) continue;
        int q = orbid[t];
        int fresh = (phm[q] == 0);
        if (!fresh) { if (phm[q] >> phase[t] & 1) continue; if (tok < 1) continue; }
        unsigned char old = phm[q];
        phm[q] = (unsigned char)(old | (1u << phase[t]));
        if (fresh) { opened[nopened++] = q; deficit += 4; } else deficit -= 1;
        hexu[hexid[t]] = 1;
        int wasmixed = (kind >= 3);
        if (wasmixed) ++mixed;
        rec(t, q, ports + 1, tok - (fresh ? 0 : 1),
            (nblk > 1) ? firstlen : curlen, 1, nblk + 1);
        if (wasmixed) --mixed;
        hexu[hexid[t]] = 0;
        if (fresh) { --nopened; deficit -= 4; } else deficit += 1;
        phm[q] = old;
    }
}

int main(int argc, char **argv) {
    BOUND_B = argc > 1 ? atoi(argv[1]) : 0;
    DMAX = argc > 2 ? atoi(argv[2]) : 6;
    ALLOW_CD = (argc > 3 && !strcmp(argv[3], "A")) ? 0 : 1;
    SHADOW   = (argc > 3 && !strcmp(argv[3], "ABS")) ? 1 : 0;
    NODECAP = argc > 4 ? strtoull(argv[4], NULL, 10) : 0;
    for (int i = 0; i < 8; ++i) for (int j = 0; j <= UBD; ++j) UB[i][j] = 120;
    if (argc > 5 && strcmp(argv[5], "-")) {
        FILE *f = fopen(argv[5], "r");
        if (!f) { fprintf(stderr, "ubfile\n"); return 2; }
        int bb, dd, vv;
        while (fscanf(f, "%d %d %d", &bb, &dd, &vv) == 3)
            if (bb >= 0 && bb < 8 && dd >= 0 && dd <= UBD && vv < UB[bb][dd]) UB[bb][dd] = vv;
        fclose(f);
        for (int i = 0; i < 8; ++i)            /* monotone non-decreasing in d */
            for (int j = 1; j <= UBD; ++j) if (UB[i][j] < UB[i][j - 1]) UB[i][j] = UB[i][j - 1];
        have_ub = 1;
    }
    TARGET = argc > 6 ? atoi(argv[6]) : 0;
    if (DMAX > 30) { fprintf(stderr, "dmax too large\n"); return 2; }
    geometry();
    for (int d = 0; d < 32; ++d) for (int a = 0; a < 2; ++a) for (int b = 0; b < 2; ++b) best[d][a][b] = -1;
    memset(hexu, 0, sizeof hexu); memset(phm, 0, sizeof phm);
    int start = 0;
    hexu[hexid[start]] = 1; phm[orbid[start]] = (unsigned char)(1u << phase[start]);
    opened[nopened++] = orbid[start]; deficit = 4;
    clock_t t0 = clock();
    rec(start, orbid[start], 1, BOUND_B, 0, 1, 1);
    double secs = (double)(clock() - t0) / CLOCKS_PER_SEC;
    printf("{\"b\":%d,\"dmax\":%d,\"model\":\"%s\",\"nodes\":%llu,\"capped\":%s,"
           "\"seconds\":%.1f,\"table\":{",
           BOUND_B, DMAX, SHADOW ? "ABS" : (ALLOW_CD ? "AB" : "A"),
           (unsigned long long)nodes,
           capped ? "true" : "false", secs);
    int first = 1;
    for (int fp = 0; fp < 2; ++fp) for (int lp = 0; lp < 2; ++lp) {
        int run = -1;
        for (int d = 0; d <= DMAX; ++d) {
            int v = -1;
            for (int dd = 0; dd <= d; ++dd)
                for (int f2 = 0; f2 < 2; ++f2) for (int l2 = 0; l2 < 2; ++l2) {
                    if (fp && !f2) continue;
                    if (lp && !l2) continue;
                    if (best[dd][f2][l2] > v) v = best[dd][f2][l2];
                }
            if (v > run) run = v;
            printf("%s\"%d|%d%d\":%d", first ? "" : ",", d, fp, lp, run);
            first = 0;
        }
    }
    printf("},\"pruned\":%s,\"target\":%d,\"exact_columns\":\"%s\","
           "\"kinds\":[\"%s\",\"%s\",\"%s\",\"%s\",\"%s\"]}\n",
           have_ub ? "true" : "false", TARGET,
           have_ub ? "only d=dmax" : "all",
           KN[0], KN[1], KN[2], KN[3], KN[4]);
    return 0;
}
