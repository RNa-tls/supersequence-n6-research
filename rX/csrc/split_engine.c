/* Round X -- exact optimum J17 of the host-split two-wrap model for all non-adjacent chain pairs of one host.

   Pieces: the T = 15 other trails (letter arcs, one arc each, any order) and the two host pieces
     A(C1, C2) = head N0(C1), tail Q(C2), cost -1;   B(C1, C2) = head N0(C2), tail Q(C1), cost -1.
   J = sum of arc costs + sum over consecutive pieces of (5 - overlap(tail7, head7)).  A path is
     [S1] A [S2] B [S3]   or   [S1] B [S2] A [S3]   with S1, S2, S3 a partition of the 15 trails.
   Tables over subsets S of the 15 trails (all from layered Held-Karp DPs with the 7-letter class trick of
   rV/csrc/path_layer.c):
     Pre_C[S] = least cost of a path through S followed by the join into N0(C)      (Pre_C[{}] = 0)
     Suf_C[S] = least cost of the join from Q(C) followed by a path through S       (Suf_C[{}] = 0)
     Mid_C[S] = least cost of: join from Q(C), path through S, join into N0(C)      (Mid_C[{}] = join(Q(C), N0(C)))
     PS_C[U]  = min over S1 inside U of Pre_C[S1] + Suf_C[U - S1]
   Then  J_AB(C1, C2) = min_S2 Mid_C2[S2] + PS_C1[all - S2] - 2   (A first: Pre into N0(C1), Mid from Q(C2) to N0(C2),
   Suf from Q(C1)),  J_BA = the same with C1, C2 exchanged, and J17 = min(J_AB, J_BA).
   input : ARCS (15 trails, "trail start dropped cost head7 tail7", sorted), CHAINS (rX/src/split_chains.py)
   output: one line per non-adjacent pair "c1 c2 J_AB J_BA J17", then a JSON summary line.
   usage : split_engine ARCS CHAINS [NTHREADS] */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
#define T 15
#define FULL ((1u << T) - 1)
#define MAXO 45000
#define MAXC 160
#define INF 100
static int no, otr[MAXO], oco[MAXO], first[T + 1];
static char ohd[MAXO][8], otl[MAXO][8];
static int nc, cid[MAXC], nxt[MAXC], prv[MAXC]; static char qt[MAXC][8], nh[MAXC][8];
static long long binom[T + 1][T + 1];
static int hcl[8][MAXO], tcl[8][MAXO], nhc[8][MAXC], qtc[8][MAXC], nk[8], off[9], G;
static long long rank_of(unsigned m) { long long r = 0; int i = 0; for (int e = 0; e < T; e++) if (m >> e & 1) { i++; r += binom[e][i]; } return r; }
static int ovl(const char *t, const char *h) { for (int k = 7; k >= 1; k--) if (!memcmp(t + 7 - k, h, k)) return k; return 0; }
/* forward layered DP.  mode 0: free start; mode 1: start after the virtual tail qt[cs].  For every subset S the
   aggregated end values are handed to out(S, g, mn).  */
typedef void (*outf)(unsigned S, const signed char *g, int mn, void *ctx);
static void forward(int mode, int cs, outf out, void *ctx) {
    signed char *cur = malloc((size_t)binom[T][1] * no), *g = malloc(G);
    memset(cur, INF, (size_t)binom[T][1] * no);
    for (int o = 0; o < no; o++) {
        int v = oco[o];
        if (mode == 1) v += 5 - ovl(qt[cs], ohd[o]);
        cur[(size_t)rank_of(1u << otr[o]) * no + o] = (signed char)v;
    }
    for (int p = 1; p <= T; p++) {
        size_t nn = p < T ? (size_t)binom[T][p + 1] : 0; signed char *nx = nn ? malloc(nn * no) : NULL;
        if (nn) memset(nx, INF, nn * no);
        unsigned m = (1u << p) - 1; long long r = 0;
        while (m <= FULL) {
            const signed char *fs = cur + (size_t)r * no; int mn = INF; memset(g, INF, G);
            for (int tt = 0; tt < T; tt++) if (m >> tt & 1) for (int o = first[tt]; o < first[tt + 1]; o++) {
                int v = fs[o]; if (v >= INF) continue; if (v < mn) mn = v;
                for (int k = 1; k <= 7; k++) { int id = tcl[k][o]; if (id >= 0 && v < g[off[k] + id]) g[off[k] + id] = (signed char)v; }
            }
            out(m, g, mn, ctx);
            if (nn && mn < INF) for (int tt = 0; tt < T; tt++) if (!(m >> tt & 1)) {
                signed char *dst = nx + (size_t)rank_of(m | 1u << tt) * no;
                for (int o = first[tt]; o < first[tt + 1]; o++) {
                    int best = mn + 5;
                    for (int k = 1; k <= 7; k++) { int v = g[off[k] + hcl[k][o]] + 5 - k; if (v < best) best = v; }
                    best += oco[o]; if (best < dst[o]) dst[o] = (signed char)(best > INF ? INF : best);
                }
            }
            unsigned c = m & -m, rr = m + c; m = (((rr ^ m) >> 2) / c) | rr; r++;
            if (p == T) break;
        }
        free(cur); cur = nx;
    }
    free(g);
}
/* backward layered DP: Bk[S][o] = least cost of a path that starts with arc o and covers S; aggregated over heads */
static void backward(outf out, void *ctx) {
    signed char *cur = malloc((size_t)binom[T][1] * no), *h = malloc(G);
    memset(cur, INF, (size_t)binom[T][1] * no);
    for (int o = 0; o < no; o++) cur[(size_t)rank_of(1u << otr[o]) * no + o] = (signed char)oco[o];
    for (int p = 1; p <= T; p++) {
        size_t nn = p < T ? (size_t)binom[T][p + 1] : 0; signed char *nx = nn ? malloc(nn * no) : NULL;
        if (nn) memset(nx, INF, nn * no);
        unsigned m = (1u << p) - 1; long long r = 0;
        while (m <= FULL) {
            const signed char *fs = cur + (size_t)r * no; int mn = INF; memset(h, INF, G);
            for (int tt = 0; tt < T; tt++) if (m >> tt & 1) for (int o = first[tt]; o < first[tt + 1]; o++) {
                int v = fs[o]; if (v >= INF) continue; if (v < mn) mn = v;
                for (int k = 1; k <= 7; k++) { int id = hcl[k][o]; if (v < h[off[k] + id]) h[off[k] + id] = (signed char)v; }
            }
            out(m, h, mn, ctx);
            if (nn && mn < INF) for (int tt = 0; tt < T; tt++) if (!(m >> tt & 1)) {
                signed char *dst = nx + (size_t)rank_of(m | 1u << tt) * no;
                for (int o = first[tt]; o < first[tt + 1]; o++) {
                    int best = mn + 5;
                    for (int k = 1; k <= 7; k++) { int id = tcl[k][o]; if (id >= 0) { int v = h[off[k] + id] + 5 - k; if (v < best) best = v; } }
                    best += oco[o]; if (best < dst[o]) dst[o] = (signed char)(best > INF ? INF : best);
                }
            }
            unsigned c = m & -m, rr = m + c; m = (((rr ^ m) >> 2) / c) | rr; r++;
            if (p == T) break;
        }
        free(cur); cur = nx;
    }
    free(h);
}
static signed char Pre[MAXC][1 << T], Suf[MAXC][1 << T], Mid[MAXC][1 << T], PS[MAXC][1 << T];
static void out_pre(unsigned S, const signed char *g, int mn, void *ctx) {
    (void)ctx;
    for (int c = 0; c < nc; c++) { int best = mn + 5; for (int k = 1; k <= 7; k++) { int id = nhc[k][c]; if (id >= 0) { int v = g[off[k] + id] + 5 - k; if (v < best) best = v; } } Pre[c][S] = (signed char)(best > INF ? INF : best); }
}
static void out_suf(unsigned S, const signed char *h, int mn, void *ctx) {
    (void)ctx;
    for (int c = 0; c < nc; c++) { int best = mn + 5; for (int k = 1; k <= 7; k++) { int id = qtc[k][c]; if (id >= 0) { int v = h[off[k] + id] + 5 - k; if (v < best) best = v; } } Suf[c][S] = (signed char)(best > INF ? INF : best); }
}
static void out_mid(unsigned S, const signed char *g, int mn, void *ctx) {
    int c = *(int *)ctx; int best = mn + 5;
    for (int k = 1; k <= 7; k++) { int id = nhc[k][c]; if (id >= 0) { int v = g[off[k] + id] + 5 - k; if (v < best) best = v; } }
    Mid[c][S] = (signed char)(best > INF ? INF : best);
}
int main(int argc, char **argv) {
    FILE *f = fopen(argv[1], "r"); if (!f) return 2;
    int t, s, d, cst; char hh[16], tl[16];
    while (fscanf(f, "%d %d %d %d %15s %15s", &t, &s, &d, &cst, hh, tl) == 6) {
        if (no >= MAXO || t >= T || (no && t < otr[no - 1])) { fprintf(stderr, "bad arcs\n"); return 2; }
        otr[no] = t; oco[no] = cst; memcpy(ohd[no], hh, 8); memcpy(otl[no], tl, 8); no++;
    }
    fclose(f);
    f = fopen(argv[2], "r"); if (!f) return 2;
    int a1, a2, a3, a4, a5, a6; char q[16], n0[16];
    while (fscanf(f, "%d %d %d %d %d %15s %15s %d %d", &a1, &a2, &a3, &a4, &a5, q, n0, &a6, &d) == 9) {
        cid[nc] = a1; memcpy(qt[nc], q, 8); memcpy(nh[nc], n0, 8); nxt[nc] = a6; prv[nc] = d; nc++;
    }
    fclose(f);
    if (argc > 3) omp_set_num_threads(atoi(argv[3]));
    for (int i = 0; i <= T; i++) for (int j = 0; j <= T; j++) binom[i][j] = j == 0 ? 1 : (i == 0 ? 0 : binom[i - 1][j - 1] + binom[i - 1][j]);
    { int qq = 0; for (int tt = 0; tt <= T; tt++) { while (qq < no && otr[qq] < tt) qq++; first[tt] = qq; } }
    /* class ids: k-letter strings that occur as a head prefix of an arc or of some N0(C) */
    for (int k = 1; k <= 7; k++) {
        int sz = 1 << (3 * k); int *map = malloc(sizeof(int) * sz); for (int i = 0; i < sz; i++) map[i] = -1; nk[k] = 0;
        #define CODE(str, from) ({ int cd_ = 0; for (int i_ = 0; i_ < k; i_++) cd_ = cd_ * 8 + ((str)[(from) + i_] - '0'); cd_; })
        for (int o = 0; o < no; o++) { int cd = CODE(ohd[o], 0); if (map[cd] < 0) map[cd] = nk[k]++; hcl[k][o] = map[cd]; }
        for (int c = 0; c < nc; c++) { int cd = CODE(nh[c], 0); if (map[cd] < 0) map[cd] = nk[k]++; nhc[k][c] = map[cd]; }
        for (int o = 0; o < no; o++) tcl[k][o] = map[CODE(otl[o], 7 - k)];
        for (int c = 0; c < nc; c++) qtc[k][c] = map[CODE(qt[c], 7 - k)];
        free(map);
    }
    off[1] = 0; for (int k = 1; k <= 7; k++) off[k + 1] = off[k] + nk[k]; G = off[8];
    double t0 = omp_get_wtime();
    for (int c = 0; c < nc; c++) { Pre[c][0] = 0; Suf[c][0] = 0; Mid[c][0] = (signed char)(5 - ovl(qt[c], nh[c])); }
    #pragma omp parallel sections
    {
        #pragma omp section
        forward(0, 0, out_pre, NULL);
        #pragma omp section
        backward(out_suf, NULL);
    }
    double t1 = omp_get_wtime();
    #pragma omp parallel for schedule(dynamic, 1)
    for (int c = 0; c < nc; c++) { int cc = c; forward(1, c, out_mid, &cc); }
    double t2 = omp_get_wtime();
    #pragma omp parallel for schedule(dynamic, 1)
    for (int c = 0; c < nc; c++)
        for (unsigned U = 0; U <= FULL; U++) {
            int best = INF; unsigned S1 = U;
            for (;;) { int v = Pre[c][S1] + Suf[c][U ^ S1]; if (v < best) best = v; if (S1 == 0) break; S1 = (S1 - 1) & U; }
            PS[c][U] = (signed char)(best > INF ? INF : best);
        }
    int least = 1000, hist[64] = {0}, npairs = 0;
    for (int i = 0; i < nc; i++) for (int j = i + 1; j < nc; j++) {
        if (nxt[i] == cid[j] || nxt[j] == cid[i]) continue;            /* adjacent chains: not this model */
        int ab = 1000, ba = 1000;
        for (unsigned S2 = 0; S2 <= FULL; S2++) {
            int v = Mid[j][S2] + PS[i][FULL ^ S2] - 2; if (v < ab) ab = v;
            v = Mid[i][S2] + PS[j][FULL ^ S2] - 2; if (v < ba) ba = v;
        }
        int J = ab < ba ? ab : ba; if (J < least) least = J; if (J >= 0 && J < 64) hist[J]++; npairs++;
        printf("%d %d %d %d %d\n", cid[i], cid[j], ab, ba, J);
    }
    printf("{\"summary\": true, \"chains\": %d, \"arcs\": %d, \"pairs\": %d, \"least_J17\": %d, \"hist\": {", nc, no, npairs, least);
    int fst = 1; for (int x = 0; x < 64; x++) if (hist[x]) { printf("%s\"%d\": %d", fst ? "" : ", ", x, hist[x]); fst = 0; }
    printf("}, \"sec_pre_suf\": %.1f, \"sec_mid\": %.1f, \"sec_total\": %.1f}\n", t1 - t0, t2 - t1, omp_get_wtime() - t0);
    return 0;
}
