/* Round W -- gap-arc path bounds at letter (or run) level, written independently of rV/csrc/gap_pairs.c.

   Model: the 16 trails of the public selection, each written as ONE piece (arcs file: "trail start dropped cost
   head7 tail7", sorted by trail).  J(path) = sum of arc costs + sum over consecutive pieces of (5 - overlap(tail7,
   head7)).  A gap arc g of chain C is the piece N0 .. Q_end of the host trail h(g) with C taken out ("id host head7
   tail7 cost" per line).
     beta1(g)       = least J over paths through all 16 trails in which the host of g is the piece g
     beta2(g1, g2)  = the same with two gap arcs of different hosts (either order)
   Method:
     PG[S][g] = least J of a path through exactly the trails S (S may be empty), plus the join into g   (forward)
     GS[S][g] = least J of a path through exactly S, plus the join from g into its first piece        (backward)
     for every representative g1 (host h1):
       forward  F[X][.]  over X subset of the 15 other trails: prefix over some A subset X, then g1, then X - A;
                FG[X][g2] = least F[X][s] + join(s, g2)
                beta(g1 -> g2) = min over X subset of U14 (= all - h1 - h2) of FG[X][g2] + cost(g2) + GS[U14 - X][g2]
       backward B[Y][.]  over Y: segment that starts with a piece, contains g1 and ends the path, covering Y + h1;
                BG[Y][g2] = least join(g2, s) + B[Y][s]
                beta(g2 -> g1) = min over Y subset of U14 of PG[U14 - Y][g2] + cost(g2) + BG[Y][g2]
     beta1(g1) = least F over the full set (the path ends with any state).
   Tables are kept for two consecutive layers (subset sizes) only.  OpenMP over the representatives.
   usage: beta_letter ARCS.txt GAPS.txt REPS.txt OUT_beta1.txt OUT_beta2.bin [NTHREADS]
          OUT_beta2.bin: int8 [nrep][ngap], 100 where the hosts coincide.                                       */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
#define NT 16
#define MAXO 60000
#define MAXG 4000
#define INF 100
typedef signed char i8;
static int no, otr[MAXO], oco[MAXO], ofirst[NT + 1];
static char ohd[MAXO][8], otl[MAXO][8];
static int ng, gid[MAXG], ghost[MAXG], gcost[MAXG];
static char ghd[MAXG][8], gtl[MAXG][8];
static int off[9], NC;
static int *ahc[8], *atc[8], ghc[8][MAXG], gtc[8][MAXG];
static long long binom[NT + 2][NT + 2];
static i8 *PG, *GS;                                   /* [65536][ng] */

static int code(const char *s, int k) { int c = 0; for (int i = 0; i < k; i++) c = c * 8 + (s[i] - '0'); return c; }

/* ---- a universe of trails, subsets ranked in colex order within each size ---- */
typedef struct { int u, tr[NT], na, ast[NT + 1]; } Univ;     /* ast: start of each universe trail's arcs in the local list */
static long long crank(unsigned m) { long long r = 0; int i = 0; for (int e = 0; m; e++, m >>= 1) if (m & 1) { i++; r += binom[e][i]; } return r; }
static unsigned tomask16(const Univ *U, unsigned m) { unsigned M = 0; for (int i = 0; i < U->u; i++) if (m >> i & 1) M |= 1u << U->tr[i]; return M; }
static void mkuniv(Univ *U, unsigned mask16) {
    U->u = 0; U->na = 0;
    for (int t = 0; t < NT; t++) if (mask16 >> t & 1) { U->tr[U->u] = t; U->ast[U->u] = U->na; U->na += ofirst[t + 1] - ofirst[t]; U->u++; }
    U->ast[U->u] = U->na;
}
/* local arc index j of universe trail position i  <->  global arc ofirst[tr[i]] + (j - ast[i]) */

/* Forward layered DP.  mode 0: plain (paths start anywhere; PG callback).  mode 1: with the special state g1
   (init value PG[S][g1] + cost(g1) at every subset; FG callback).  States: local arcs + 1 special slot (index na). */
static void forward(const Univ *U, int mode, int g1, i8 *outFG, int *beta1) {
    int u = U->u, na = U->na, W = na + 1; i8 *gt = malloc(NC); size_t cap = 0;
    for (int p = 0; p <= u; p++) if ((size_t)binom[u][p] > cap) cap = binom[u][p];
    i8 *cur = malloc(cap * W), *nxt = malloc(cap * W);
    /* layer 0 */
    memset(cur, INF, W);
    if (mode == 1) { int v = PG[(size_t)0 * ng + g1] + gcost[g1]; cur[na] = (i8)(v < INF ? v : INF); }
    for (int p = 0; p <= u; p++) {
        long long nl = binom[u][p], nn = p < u ? binom[u][p + 1] : 0;
        if (p < u) { memset(nxt, INF, (size_t)nn * W);
            if (mode == 1) { unsigned m = (1u << (p + 1)) - 1; for (long long r = 0; r < nn; r++) {
                unsigned M = tomask16(U, m); int v = PG[(size_t)M * ng + g1] + gcost[g1]; nxt[(size_t)r * W + na] = (i8)(v < INF ? v : INF);
                unsigned c = m & -m, rr = m + c; m = (((rr ^ m) >> 2) / c) | rr; } } }
        unsigned m = (1u << p) - 1;
        for (long long r = 0; r < nl; r++) {
            const i8 *fs = cur + (size_t)r * W; int mn = INF; unsigned M = tomask16(U, m);
            memset(gt, INF, NC);
            for (int i = 0; i < u; i++) if (m >> i & 1) { int t = U->tr[i];
                for (int j = U->ast[i]; j < U->ast[i + 1]; j++) { int v = fs[j]; if (v >= INF) continue; if (v < mn) mn = v;
                    int o = ofirst[t] + (j - U->ast[i]); for (int k = 1; k <= 7; k++) { int id = atc[k][o]; if (v < gt[id]) gt[id] = (i8)v; } } }
            if (mode == 1 && fs[na] < INF) { int v = fs[na]; if (v < mn) mn = v; for (int k = 1; k <= 7; k++) { int id = gtc[k][g1]; if (v < gt[id]) gt[id] = (i8)v; } }
            /* callback: joins into every gap arc */
            if (mode == 0) { i8 *row = PG + (size_t)M * ng;
                for (int g = 0; g < ng; g++) { int best;
                    if (p == 0) best = 0; else { best = mn + 5; for (int k = 1; k <= 7; k++) { int v = gt[ghc[k][g]] + 5 - k; if (v < best) best = v; } }
                    row[g] = (i8)(best < INF ? best : INF); } }
            else { i8 *row = outFG + (size_t)M * ng;
                for (int g = 0; g < ng; g++) { int best = mn + 5; for (int k = 1; k <= 7; k++) { int v = gt[ghc[k][g]] + 5 - k; if (v < best) best = v; }
                    row[g] = (i8)(best < INF ? best : INF); }
                if (p == u && beta1) *beta1 = mn; }
            /* transitions */
            if (p < u && (mn < INF || (mode == 0 && p == 0))) for (int i = 0; i < u; i++) { if (m >> i & 1) continue; int t = U->tr[i];
                i8 *fn = nxt + (size_t)crank(m | 1u << i) * W;
                for (int j = U->ast[i]; j < U->ast[i + 1]; j++) { int o = ofirst[t] + (j - U->ast[i]), best;
                    if (mode == 0 && p == 0) best = 0; else { best = mn + 5; for (int k = 1; k <= 7; k++) { int v = gt[ahc[k][o]] + 5 - k; if (v < best) best = v; } }
                    best += oco[o]; if (best < fn[j]) fn[j] = (i8)(best < INF ? best : INF); } }
            unsigned c = m & -m, rr = m + c; if (p > 0) m = (((rr ^ m) >> 2) / c) | rr; else m = 0;
        }
        i8 *tmp = cur; cur = nxt; nxt = tmp;
    }
    free(cur); free(nxt); free(gt);
}

/* Backward layered DP: B[S][o] = least J of a segment starting with o through exactly S (mode 0, GS callback),
   or (mode 1) a segment that starts with o, contains g1 (special slot) and ends the path (BG callback). */
static void backward(const Univ *U, int mode, int g1, i8 *outBG) {
    int u = U->u, na = U->na, W = na + 1; i8 *ht = malloc(NC); size_t cap = 0;
    for (int p = 0; p <= u; p++) if ((size_t)binom[u][p] > cap) cap = binom[u][p];
    i8 *cur = malloc(cap * W), *nxt = malloc(cap * W);
    memset(cur, INF, W);
    if (mode == 1) { int v = gcost[g1] + GS[(size_t)0 * ng + g1]; cur[na] = (i8)(v < INF ? v : INF); }
    for (int p = 0; p <= u; p++) {
        long long nl = binom[u][p], nn = p < u ? binom[u][p + 1] : 0;
        if (p < u) { memset(nxt, INF, (size_t)nn * W);
            if (mode == 1) { unsigned m = (1u << (p + 1)) - 1; for (long long r = 0; r < nn; r++) {
                unsigned M = tomask16(U, m); int v = gcost[g1] + GS[(size_t)M * ng + g1]; nxt[(size_t)r * W + na] = (i8)(v < INF ? v : INF);
                unsigned c = m & -m, rr = m + c; m = (((rr ^ m) >> 2) / c) | rr; } } }
        unsigned m = (1u << p) - 1;
        for (long long r = 0; r < nl; r++) {
            const i8 *fs = cur + (size_t)r * W; int mn = INF; unsigned M = tomask16(U, m);
            memset(ht, INF, NC);
            for (int i = 0; i < u; i++) if (m >> i & 1) { int t = U->tr[i];
                for (int j = U->ast[i]; j < U->ast[i + 1]; j++) { int v = fs[j]; if (v >= INF) continue; if (v < mn) mn = v;
                    int o = ofirst[t] + (j - U->ast[i]); for (int k = 1; k <= 7; k++) { int id = ahc[k][o]; if (v < ht[id]) ht[id] = (i8)v; } } }
            if (mode == 1 && fs[na] < INF) { int v = fs[na]; if (v < mn) mn = v; for (int k = 1; k <= 7; k++) { int id = ghc[k][g1]; if (v < ht[id]) ht[id] = (i8)v; } }
            if (mode == 0) { i8 *row = GS + (size_t)M * ng;
                for (int g = 0; g < ng; g++) { int best;
                    if (p == 0) best = 0; else { best = mn + 5; for (int k = 1; k <= 7; k++) { int v = ht[gtc[k][g]] + 5 - k; if (v < best) best = v; } }
                    row[g] = (i8)(best < INF ? best : INF); } }
            else { i8 *row = outBG + (size_t)M * ng;
                for (int g = 0; g < ng; g++) { int best = mn + 5; for (int k = 1; k <= 7; k++) { int v = ht[gtc[k][g]] + 5 - k; if (v < best) best = v; }
                    row[g] = (i8)(best < INF ? best : INF); } }
            if (p < u && (mn < INF || (mode == 0 && p == 0))) for (int i = 0; i < u; i++) { if (m >> i & 1) continue; int t = U->tr[i];
                i8 *fn = nxt + (size_t)crank(m | 1u << i) * W;
                for (int j = U->ast[i]; j < U->ast[i + 1]; j++) { int o = ofirst[t] + (j - U->ast[i]), best;
                    if (mode == 0 && p == 0) best = 0; else { best = mn + 5; for (int k = 1; k <= 7; k++) { int v = ht[atc[k][o]] + 5 - k; if (v < best) best = v; } }
                    best += oco[o]; if (best < fn[j]) fn[j] = (i8)(best < INF ? best : INF); } }
            unsigned c = m & -m, rr = m + c; if (p > 0) m = (((rr ^ m) >> 2) / c) | rr; else m = 0;
        }
        i8 *tmp = cur; cur = nxt; nxt = tmp;
    }
    free(cur); free(nxt); free(ht);
}

int main(int argc, char **argv) {
    if (argc < 6) { fprintf(stderr, "usage\n"); return 2; }
    int nth = argc > 6 ? atoi(argv[6]) : 4;
    FILE *f = fopen(argv[1], "r"); int t, s, d, c; char h[16], tl[16];
    while (fscanf(f, "%d %d %d %d %15s %15s", &t, &s, &d, &c, h, tl) == 6) {
        if (no >= MAXO || t < 0 || t >= NT || (no && t < otr[no - 1]) || strlen(h) != 7 || strlen(tl) != 7) { fprintf(stderr, "bad arcs\n"); return 2; }
        otr[no] = t; oco[no] = c; memcpy(ohd[no], h, 8); memcpy(otl[no], tl, 8); no++; }
    fclose(f);
    { int q = 0; for (int tt = 0; tt <= NT; tt++) { while (q < no && otr[q] < tt) q++; ofirst[tt] = q; } }
    f = fopen(argv[2], "r"); int ci;
    while (fscanf(f, "%d %d %15s %15s %d", &ci, &t, h, tl, &c) == 5) { if (ng >= MAXG) return 2; gid[ng] = ci; ghost[ng] = t; gcost[ng] = c; memcpy(ghd[ng], h, 8); memcpy(gtl[ng], tl, 8); ng++; }
    fclose(f);
    int nrep = 0, *rep = malloc(sizeof(int) * MAXG); f = fopen(argv[3], "r");
    while (fscanf(f, "%d", &ci) == 1) { int g = -1; for (int i = 0; i < ng; i++) if (gid[i] == ci) g = i; if (g < 0) { fprintf(stderr, "rep %d not a gap\n", ci); return 2; } rep[nrep++] = g; }
    fclose(f);
    /* classes: all k-strings occurring as head prefixes or tail suffixes of arcs and gap arcs, one id space per k */
    off[1] = 0;
    for (int k = 1; k <= 7; k++) {
        int sz = 1 << (3 * k), *map = malloc(sizeof(int) * sz), n = 0; for (int i = 0; i < sz; i++) map[i] = -1;
        ahc[k] = malloc(sizeof(int) * no); atc[k] = malloc(sizeof(int) * no);
        for (int o = 0; o < no; o++) { int a = code(ohd[o], k), b = code(otl[o] + 7 - k, k); if (map[a] < 0) map[a] = n++; if (map[b] < 0) map[b] = n++; ahc[k][o] = off[k] + map[a]; atc[k][o] = off[k] + map[b]; }
        for (int g = 0; g < ng; g++) { int a = code(ghd[g], k), b = code(gtl[g] + 7 - k, k); if (map[a] < 0) map[a] = n++; if (map[b] < 0) map[b] = n++; ghc[k][g] = off[k] + map[a]; gtc[k][g] = off[k] + map[b]; }
        off[k + 1] = off[k] + n; free(map);
    }
    NC = off[8];
    for (int i = 0; i <= NT + 1; i++) for (int j = 0; j <= NT + 1; j++) binom[i][j] = j == 0 ? 1 : (i == 0 ? 0 : binom[i - 1][j - 1] + binom[i - 1][j]);
    fprintf(stderr, "arcs %d gaps %d reps %d classes %d\n", no, ng, nrep, NC);
    PG = malloc((size_t)65536 * ng); GS = malloc((size_t)65536 * ng);
    memset(PG, INF, (size_t)65536 * ng); memset(GS, INF, (size_t)65536 * ng);
    Univ U16; mkuniv(&U16, 0xFFFF);
    #pragma omp parallel sections num_threads(2)
    {
        #pragma omp section
        forward(&U16, 0, -1, NULL, NULL);
        #pragma omp section
        backward(&U16, 0, -1, NULL);
    }
    fprintf(stderr, "PG, GS done\n");
    i8 *B2 = malloc((size_t)nrep * ng); int *B1 = malloc(sizeof(int) * nrep);
    #pragma omp parallel for schedule(dynamic, 1) num_threads(nth)
    for (int ri = 0; ri < nrep; ri++) {
        int g1 = rep[ri], h1 = ghost[g1]; Univ U; mkuniv(&U, 0xFFFF & ~(1u << h1));
        i8 *FG = malloc((size_t)65536 * ng), *BG = malloc((size_t)65536 * ng); memset(FG, INF, (size_t)65536 * ng); memset(BG, INF, (size_t)65536 * ng);
        int b1 = INF; forward(&U, 1, g1, FG, &b1); backward(&U, 1, g1, BG); B1[ri] = b1;
        for (int g2 = 0; g2 < ng; g2++) { int h2 = ghost[g2];
            if (h2 == h1) { B2[(size_t)ri * ng + g2] = INF; continue; }
            unsigned U14 = 0xFFFF & ~(1u << h1) & ~(1u << h2); int best = INF;
            for (unsigned X = U14; ; X = (X - 1) & U14) {            /* all subsets of U14 */
                int v1 = FG[(size_t)X * ng + g2] + gcost[g2] + GS[(size_t)(U14 & ~X) * ng + g2];
                int v2 = PG[(size_t)(U14 & ~X) * ng + g2] + gcost[g2] + BG[(size_t)X * ng + g2];
                if (v1 < best) best = v1; if (v2 < best) best = v2;
                if (X == 0) break; }
            B2[(size_t)ri * ng + g2] = (i8)(best < INF ? best : INF); }
        free(FG); free(BG);
        #pragma omp critical
        { fprintf(stderr, "rep %d (gap %d host %d) beta1 %d\n", ri, gid[g1], h1, b1); }
    }
    f = fopen(argv[4], "w"); for (int ri = 0; ri < nrep; ri++) fprintf(f, "%d %d %d\n", gid[rep[ri]], ghost[rep[ri]], B1[ri]); fclose(f);
    f = fopen(argv[5], "wb"); fwrite(B2, 1, (size_t)nrep * ng, f); fclose(f);
    return 0;
}
