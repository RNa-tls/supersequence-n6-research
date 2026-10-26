// Round R, section 12 -- exact enumeration of every single visit of one trail-version with kappa <= B.
// Theorem R7: a single visit is a Hamiltonian path H through the m runs of the version, and
//     kappa(H) = (#maximal w2 segments - #chains) + sum_{non-w2 joins} (w - 3).
// Depth-first search over H, built segment by segment: a segment starts at an uncovered run y entered by a join of
// weight w = 3 + d (d >= 0; w = 2 is only the natural w2 successor, which continues the segment), and follows the
// unique w2 successors through uncovered runs of the same chain for any length >= 1.  Cost: d per join, +1 for every
// segment of a chain that already has one.  Lower bound for pruning: every maximal uncovered w2 interval of a touched
// chain needs one more (paid) segment.  Every complete path with kappa <= B is recorded as (entry run, exit run).
// Output: m x m int8 table (least kappa, 99 = none, -1 diagonal; single pieces (k, k-1) get 3 - c_k) for dominance.c,
// and a JSON line with counts.  B = 0 must give exactly the standard options at chain starts (kappa0_A_visits.py),
// B = 1 the table of kappa1_A_visits.py.
// usage: kappa_dfs DIR(runs.bin) TRAIL VERSION B OUT.bin
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#define NTR 30
#define MW 11
static int mrun[NTR][2]; static uint8_t *runp[NTR][2];
static int wgt(const uint8_t *x, const uint8_t *y) { for (int s = 1; s < 8; s++) { int ok = 1; for (int i = 0; s + i < 8; i++) if (x[s + i] != y[i]) { ok = 0; break; } if (ok) return s; } return 8; }
static int m, B; static uint8_t *W; static int *succ2, *pred2, *chainof, *chainlen, *isfull, nchain;
static int *tgt_off, *tgt;       // per run: candidate next entries with 3 <= w <= 3 + B
typedef struct { uint64_t v[MW]; } Set;
static inline int isv(const Set *s, int r) { return s->v[r >> 6] >> (r & 63) & 1; }
static inline void setv(Set *s, int r) { s->v[r >> 6] |= 1ull << (r & 63); }
static inline void clrv(Set *s, int r) { s->v[r >> 6] &= ~(1ull << (r & 63)); }
typedef struct { int8_t *K; long paths[8]; long nodes; int *segs; int *chainrun0; } Ctx;
// number of maximal uncovered w2 intervals of chain c (c touched)
static int intervals(const Set *vis, int c, const int *runs_of, int L) {
    int cnt = 0;
    for (int k = 0; k < L; k++) { int r = runs_of[k]; if (isv(vis, r)) continue; int p = pred2[r]; if (p < 0 || isv(vis, p)) cnt++; }
    if (cnt == 0) { int all = 1; for (int k = 0; k < L; k++) if (isv(vis, runs_of[k])) { all = 0; break; } if (all && L > 0 && isfull[c]) cnt = 1; }
    return cnt;
}
static int *crun, *crun_off;     // runs of every chain in w2 order
// incremental pruning bound: Hc = sum over touched chains of their uncovered w2 intervals (each needs a paid segment)
static void dfs(Ctx *C, int x, Set *vis, int nvis, int cost, int y0, int Hc, int *iv) {
    C->nodes++;
    if (nvis == m) { int8_t *k = &C->K[(size_t)y0 * m + x]; if (cost < *k) *k = (int8_t)cost; C->paths[cost]++; return; }
    if (cost + Hc > B) return;
    for (int ti = tgt_off[x]; ti < tgt_off[x + 1]; ti++) { int y = tgt[ti]; if (isv(vis, y)) continue;
        int d = W[(size_t)x * m + y] - 3; int c = chainof[y]; int s = C->segs[c] ? 1 : 0;
        if (cost + d + s > B) continue;
        int path[8], L = 0, r = y;
        while (r >= 0 && !isv(vis, r) && L < 8) { path[L++] = r; r = succ2[r]; if (r == y) break; }
        int old = C->segs[c] ? iv[c] : 0; int keep = iv[c];
        C->segs[c]++;
        for (int l = 1; l <= L; l++) { setv(vis, path[l - 1]);
            int nw = intervals(vis, c, crun + crun_off[c], chainlen[c]); iv[c] = nw;
            dfs(C, path[l - 1], vis, nvis + l, cost + d + s, y0, Hc - old + nw, iv); }
        for (int l = 0; l < L; l++) clrv(vis, path[l]);
        C->segs[c]--; iv[c] = keep;
    }
}
int main(int argc, char **argv) {
    const char *dir = argv[1]; int T0 = atoi(argv[2]), V0 = atoi(argv[3]); B = atoi(argv[4]); const char *outp = argv[5]; char p[2048];
    snprintf(p, sizeof p, "%s/runs.bin", dir); FILE *f = fopen(p, "rb"); if (!f) return 2;
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int32_t mm; if (fread(&mm, 4, 1, f) != 1) return 2; mrun[t][v] = mm; runp[t][v] = malloc(8 * mm); if (fread(runp[t][v], 1, 8 * mm, f) != (size_t)(8 * mm)) return 2; }
    fclose(f);
    m = mrun[T0][V0]; if (m > 64 * MW) return 4;
    uint8_t (*first)[8] = malloc(8 * m), (*last)[8] = malloc(8 * m);
    for (int k = 0; k < m; k++) { memcpy(first[k], runp[T0][V0] + 8 * k, 8); last[k][0] = first[k][7]; for (int i = 1; i < 8; i++) last[k][i] = first[k][i - 1]; }
    W = malloc((size_t)m * m); for (int i = 0; i < m; i++) for (int j = 0; j < m; j++) W[(size_t)i * m + j] = i == j ? 99 : wgt(last[i], first[j]);
    succ2 = malloc(4 * m); pred2 = malloc(4 * m); for (int i = 0; i < m; i++) succ2[i] = pred2[i] = -1;
    for (int i = 0; i < m; i++) for (int j = 0; j < m; j++) if (i != j && W[(size_t)i * m + j] == 2) { if (succ2[i] >= 0 || pred2[j] >= 0) { fprintf(stderr, "w2 not unique\n"); return 3; } succ2[i] = j; pred2[j] = i; }
    chainof = malloc(4 * m); for (int i = 0; i < m; i++) chainof[i] = -1; chainlen = calloc(m, 4); isfull = calloc(m, 4); nchain = 0;
    crun = malloc(4 * m); crun_off = malloc(4 * (m + 1)); int nr = 0;
    for (int i = 0; i < m; i++) { if (chainof[i] >= 0) continue; int h = i, guard = 0; while (pred2[h] >= 0 && pred2[h] != i && guard++ < m) h = pred2[h];
        int cyc = pred2[h] >= 0; crun_off[nchain] = nr; int x = h, L = 0; do { chainof[x] = nchain; crun[nr++] = x; L++; x = succ2[x]; } while (x >= 0 && x != h);
        chainlen[nchain] = L; isfull[nchain] = cyc; nchain++; }
    crun_off[nchain] = nr;
    tgt_off = malloc(4 * (m + 1)); tgt = malloc(4 * (size_t)m * m); int nt = 0;
    for (int i = 0; i < m; i++) { tgt_off[i] = nt; for (int w = 3; w <= 3 + B && w <= 8; w++) for (int j = 0; j < m; j++) if (j != i && W[(size_t)i * m + j] == w) tgt[nt++] = j; } tgt_off[m] = nt;
    int nthr = omp_get_max_threads(); Ctx *ctx = calloc(nthr, sizeof(Ctx));
    for (int t = 0; t < nthr; t++) { ctx[t].K = malloc((size_t)m * m); memset(ctx[t].K, 99, (size_t)m * m); ctx[t].segs = calloc(nchain, 4); }
    double t0 = omp_get_wtime();
    #pragma omp parallel for schedule(dynamic, 1)
    for (int y0 = 0; y0 < m; y0++) {
        Ctx *C = &ctx[omp_get_thread_num()]; Set vis; memset(&vis, 0, sizeof vis); int *iv = calloc(nchain, 4);
        int c = chainof[y0]; int path[8], L = 0, r = y0;
        while (r >= 0 && L < 8) { path[L++] = r; r = succ2[r]; if (r == y0) break; }
        C->segs[c] = 1;
        for (int l = 1; l <= L; l++) { setv(&vis, path[l - 1]); int nw = intervals(&vis, c, crun + crun_off[c], chainlen[c]); iv[c] = nw; dfs(C, path[l - 1], &vis, l, 0, y0, nw, iv); }
        for (int l = 0; l < L; l++) clrv(&vis, path[l]);
        C->segs[c] = 0; free(iv);
    }
    int8_t *K = malloc((size_t)m * m); memset(K, 99, (size_t)m * m); long paths[8] = {0}, nodes = 0;
    for (int t = 0; t < nthr; t++) { for (size_t i = 0; i < (size_t)m * m; i++) if (ctx[t].K[i] < K[i]) K[i] = ctx[t].K[i]; for (int k = 0; k < 8; k++) paths[k] += ctx[t].paths[k]; nodes += ctx[t].nodes; }
    long nonstd[8] = {0}, stdpairs = 0;
    for (int y = 0; y < m; y++) for (int x = 0; x < m; x++) { int k = K[(size_t)y * m + x]; if (k == 99) continue; if (x == (y + m - 1) % m) stdpairs++; else if (x != y) nonstd[k]++; }
    for (int k = 0; k < m; k++) { K[(size_t)k * m + k] = -1; K[(size_t)k * m + (k + m - 1) % m] = (int8_t)(3 - W[(size_t)((k + m - 1) % m) * m + k]); }
    f = fopen(outp, "wb"); fwrite(K, 1, (size_t)m * m, f); fclose(f);
    printf("{\"trail\": %d, \"version\": %d, \"B\": %d, \"chains\": %d, \"paths_by_kappa\": [", T0, V0, B, nchain);
    for (int k = 0; k <= B; k++) printf("%s%ld", k ? ", " : "", paths[k]);
    printf("], \"standard_pairs_found\": %ld, \"nonstandard_pairs_by_least_kappa\": [", stdpairs);
    for (int k = 0; k <= B; k++) printf("%s%ld", k ? ", " : "", nonstd[k]);
    printf("], \"nodes\": %ld, \"sec\": %.1f}\n", nodes, omp_get_wtime() - t0);
    return 0;
}
