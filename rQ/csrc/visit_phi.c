// Round Q -- exact single-visit catalog of every phi trail-version (independent of rN/src/visit_catalog.py).
// A single visit of trail T (version v) is a Hamiltonian path through its m runs (runs keep the version's starting
// rotation).  cost(path) = sum over its m-1 joins of (w - 2); kappa(y, x) = min over paths from run y to run x of
// cost - (k_T - 1), k_T = number of weight-3 joins of the version (kappa = 0 for link openings, 1 for F openings).
// Exact branch and bound: w2 arcs (F-steps, wraps) cost 0 and each run has at most one w2 successor; every
// further maximal w2-component of the unvisited runs needs at least one jump of cost >= 1 (lower bound).
// Output: OUT/kappa_phi.bin = for t in phi order, v in {0,1}: m x m int8 (kappa, -1 on the diagonal, 99 if > KMAX).
// usage: visit_phi DIR(runs.bin) OUT KMAX
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#define NTR 30
static int mrun[NTR][2]; static uint8_t *runp[NTR][2];
static int wgt(const uint8_t *x, const uint8_t *y) { for (int s = 1; s < 8; s++) { int ok = 1; for (int i = 0; s + i < 8; i++) if (x[s + i] != y[i]) { ok = 0; break; } if (ok) return s; } return 8; }
typedef struct { int m, kT, W[64][64], succ2[64], pred2[64]; } TV;
static int components(const TV *T, uint64_t U) {     // number of maximal w2-components (paths or cycles) in U
    int c = 0;
    for (int r = 0; r < T->m; r++) { if (!(U >> r & 1)) continue; int p = T->pred2[r];
        if (p < 0 || !(U >> p & 1)) c++; }        // r is the head of a path component
    // cycles (every vertex has its w2 predecessor in U): count them
    uint64_t seen = 0;
    for (int r = 0; r < T->m; r++) { if (!(U >> r & 1) || (seen >> r & 1)) continue;
        int p = T->pred2[r]; if (p < 0 || !(U >> p & 1)) { int x = r; while (x >= 0 && (U >> x & 1) && !(seen >> x & 1)) { seen |= 1ull << x; x = T->succ2[x]; } } }
    for (int r = 0; r < T->m; r++) { if (!(U >> r & 1) || (seen >> r & 1)) continue; c++; int x = r; while (!(seen >> x & 1)) { seen |= 1ull << x; x = T->succ2[x]; } }
    return c;
}
static void dfs(const TV *T, int cur, uint64_t vis, int cost, int *best, int BUD) {
    uint64_t full = (T->m == 64) ? ~0ull : ((1ull << T->m) - 1);
    if (vis == full) { if (cost < best[cur]) best[cur] = cost; return; }
    uint64_t U = full & ~vis; int s = T->succ2[cur];
    int lb = components(T, U) - ((s >= 0 && (U >> s & 1)) ? 1 : 0);
    if (cost + lb > BUD) return;
    for (int r = 0; r < T->m; r++) { if (!(U >> r & 1)) continue; int c = T->W[cur][r] - 2; if (c < 0) c = 0;
        if (cost + c > BUD) continue;
        dfs(T, r, vis | 1ull << r, cost + c, best, BUD); }
}
int main(int argc, char **argv) {
    const char *dir = argv[1], *out = argv[2]; int KMAX = atoi(argv[3]); char p[2048];
    snprintf(p, sizeof p, "%s/runs.bin", dir); FILE *f = fopen(p, "rb"); if (!f) return 2;
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int32_t m; if (fread(&m, 4, 1, f) != 1) return 2; mrun[t][v] = m; runp[t][v] = malloc(8 * m); if (fread(runp[t][v], 1, 8 * m, f) != (size_t)(8 * m)) return 2; }
    fclose(f);
    snprintf(p, sizeof p, "%s/kappa_phi.bin", out); FILE *fo = fopen(p, "wb");
    long hist[16] = {0}; int nphi = 0; int tl[NTR]; for (int t = 0; t < NTR; t++) if (mrun[t][0] <= 100) tl[nphi++] = t;
    int8_t (*KALL)[2][64][64] = malloc(sizeof(int8_t[2][64][64]) * nphi);
    #pragma omp parallel for schedule(dynamic, 1) collapse(2)
    for (int ti = 0; ti < nphi; ti++)
        for (int v = 0; v < 2; v++) { int t = tl[ti];
            TV T; T.m = mrun[t][v]; int m = T.m; uint8_t first[64][8], last[64][8];
            for (int k = 0; k < m; k++) { memcpy(first[k], runp[t][v] + 8 * k, 8); last[k][0] = first[k][7]; for (int i = 1; i < 8; i++) last[k][i] = first[k][i - 1]; }
            T.kT = 0;
            for (int i = 0; i < m; i++) { T.succ2[i] = -1; T.pred2[i] = -1; }
            for (int i = 0; i < m; i++) for (int j = 0; j < m; j++) { T.W[i][j] = i == j ? 99 : wgt(last[i], first[j]); }
            for (int k = 0; k < m; k++) if (T.W[(k + m - 1) % m][k] == 3) T.kT++;
            for (int i = 0; i < m; i++) for (int j = 0; j < m; j++) if (i != j && T.W[i][j] == 2) { if (T.succ2[i] >= 0 || T.pred2[j] >= 0) { fprintf(stderr, "w2 not unique\n"); exit(3); } T.succ2[i] = j; T.pred2[j] = i; }
            int8_t (*K)[64] = KALL[ti][v]; int best[64];
            int BUD = (T.kT - 1) + KMAX;
            for (int y = 0; y < m; y++) {
                for (int x = 0; x < m; x++) best[x] = 1 << 20;
                dfs(&T, y, 1ull << y, 0, best, BUD);
                for (int x = 0; x < m; x++) { if (x == y) { K[y][x] = -1; continue; } int kap = best[x] >= (1 << 20) ? 99 : best[x] - (T.kT - 1); K[y][x] = kap > KMAX ? 99 : kap; }
            }
        }
    for (int ti = 0; ti < nphi; ti++) for (int v = 0; v < 2; v++) { int m = mrun[tl[ti]][v];
        for (int y = 0; y < m; y++) { fwrite(KALL[ti][v][y], 1, m, fo); for (int x = 0; x < m; x++) { int k = KALL[ti][v][y][x]; if (k >= 0 && k < 16) hist[k]++; else if (k == 99) hist[15]++; } } }
    fclose(fo);
    printf("{\"phi_trails\": %d, \"kappa_hist\": {", nphi); for (int k = 0; k <= KMAX; k++) printf("%s\"%d\": %ld", k ? ", " : "", k, hist[k]); printf(", \"gt_KMAX\": %ld}}\n", hist[15]);
    return 0;
}
