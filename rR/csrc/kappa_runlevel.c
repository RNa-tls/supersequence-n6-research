// Round R, section 12 -- independent checker for the kappa tables of kappa_dfs.c / kappa_dfs2.c.
// Works on runs only: no chains, no segments, no Theorem R7.  A single visit of one trail-version is a Hamiltonian path
// H = (h_1, ..., h_m) of its m runs; its cost relative to the single pieces is
//     kappa(H) = sum_{i < m} (w(h_i, h_{i+1}) - 2) - (N - 1),   N = sum over the m natural joins k -> k+1 of (w - 2),
// normalised so that the single piece entering at run k has kappa = 3 - w(k-1, k).
// Depth-first search one run at a time.  Lower bound on the rest of the sum: every maximal uncovered stretch of the
// w2 successor structure (an uncovered run whose w2 predecessor is covered or absent, or a w2 cycle with no covered run)
// must be entered once; the only w = 2 entry is from its w2 predecessor, so every stretch costs >= 1 except the one
// starting at the w2 successor of the current run.
// Output: m x m int8 least-kappa table for kappa <= B in the format of kappa_dfs.c (99 = none, -1 diagonal, single
// pieces (k, k-1) = 3 - w(k-1, k)).
// usage: kappa_runlevel DIR(runs.bin) TRAIL VERSION B OUT.bin
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#define NTR 30
static int mrun[NTR][2]; static uint8_t *runp[NTR][2];
static int wgt(const uint8_t *x, const uint8_t *y) { for (int s = 1; s < 8; s++) { int ok = 1; for (int i = 0; s + i < 8; i++) if (x[s + i] != y[i]) { ok = 0; break; } if (ok) return s; } return 8; }
static int m, B, N; static uint8_t *W; static int *nx, *pv;   // w2 successor / predecessor (-1 none)
static int *cyc_id, ncyc, *cyc_len;                           // w2 cycles (runs on a cycle of w2 arcs)
static int *adj_off, *adj;                                    // per run: next-run candidates by increasing w (w <= 3 + B)
typedef struct { int8_t *K; uint8_t *cov; int *cyc_cov; long nodes; long paths; } Ctx;
static int stretches_delta_cover(Ctx *C, int r) {
    // change of the stretch count when run r is covered
    int d = 0;
    if (cyc_id[r] >= 0 && C->cyc_cov[cyc_id[r]] == 0) d -= 1;                 // a whole uncovered w2 cycle was one stretch
    else if (pv[r] < 0 || C->cov[pv[r]]) d -= 1;                             // r started a stretch
    if (nx[r] >= 0 && !C->cov[nx[r]]) d += 1;                                // its successor starts one now
    return d;
}
static void dfs(Ctx *C, int x, int nv, int sum, int I, int y0) {
    C->nodes++;
    if (nv == m) { int k = sum - (N - 1); if (k <= B) { int8_t *e = &C->K[(size_t)y0 * m + x]; if (k < *e) *e = (int8_t)k; C->paths++; } return; }
    int free_next = nx[x] >= 0 && !C->cov[nx[x]];
    if (sum + I - free_next > N - 1 + B) return;
    for (int i = adj_off[x]; i < adj_off[x + 1]; i++) { int y = adj[i]; if (C->cov[y]) continue;
        int c = W[(size_t)x * m + y] - 2;
        int dI = stretches_delta_cover(C, y);
        if (sum + c + I + dI - (nx[y] >= 0 && !C->cov[nx[y]]) > N - 1 + B) continue;
        C->cov[y] = 1; if (cyc_id[y] >= 0) C->cyc_cov[cyc_id[y]]++;
        dfs(C, y, nv + 1, sum + c, I + dI, y0);
        C->cov[y] = 0; if (cyc_id[y] >= 0) C->cyc_cov[cyc_id[y]]--;
    }
}
int main(int argc, char **argv) {
    if (argc < 6) { fprintf(stderr, "usage: kappa_runlevel DIR TRAIL VERSION B OUT.bin\n"); return 1; }
    const char *dir = argv[1]; int T0 = atoi(argv[2]), V0 = atoi(argv[3]); B = atoi(argv[4]); const char *outp = argv[5]; char p[2048];
    snprintf(p, sizeof p, "%s/runs.bin", dir); FILE *f = fopen(p, "rb"); if (!f) return 2;
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int32_t mm; if (fread(&mm, 4, 1, f) != 1) return 2; mrun[t][v] = mm; runp[t][v] = malloc(8 * mm); if (fread(runp[t][v], 1, 8 * mm, f) != (size_t)(8 * mm)) return 2; }
    fclose(f);
    m = mrun[T0][V0];
    uint8_t (*fi)[8] = malloc(8 * m), (*la)[8] = malloc(8 * m);
    for (int k = 0; k < m; k++) { memcpy(fi[k], runp[T0][V0] + 8 * k, 8); la[k][0] = fi[k][7]; for (int i = 1; i < 8; i++) la[k][i] = fi[k][i - 1]; }
    W = malloc((size_t)m * m); for (int i = 0; i < m; i++) for (int j = 0; j < m; j++) W[(size_t)i * m + j] = i == j ? 99 : wgt(la[i], fi[j]);
    N = 0; for (int k = 0; k < m; k++) N += W[(size_t)k * m + (k + 1) % m] - 2;
    nx = malloc(4 * (size_t)m); pv = malloc(4 * (size_t)m); for (int i = 0; i < m; i++) nx[i] = pv[i] = -1;
    for (int i = 0; i < m; i++) for (int j = 0; j < m; j++) if (W[(size_t)i * m + j] == 2) { if (nx[i] >= 0 || pv[j] >= 0) { fprintf(stderr, "w2 arcs not a partial permutation\n"); return 3; } nx[i] = j; pv[j] = i; }
    cyc_id = malloc(4 * m); for (int i = 0; i < m; i++) cyc_id[i] = -1; cyc_len = calloc(m, 4); ncyc = 0;
    for (int i = 0; i < m; i++) { if (cyc_id[i] >= 0) continue; int r = i, L = 0; while (r >= 0 && L <= m) { r = nx[r]; L++; if (r == i) break; }
        if (r == i) { int q = i; do { cyc_id[q] = ncyc; q = nx[q]; } while (q != i); cyc_len[ncyc++] = L; } }
    adj_off = malloc(4 * (m + 1)); adj = malloc(4 * (size_t)m * m); int na = 0;
    for (int i = 0; i < m; i++) { adj_off[i] = na; for (int w = 2; w <= 3 + B && w <= 8; w++) for (int j = 0; j < m; j++) if (j != i && W[(size_t)i * m + j] == w) adj[na++] = j; } adj_off[m] = na;
    int nthr = omp_get_max_threads(); Ctx *ctx = calloc(nthr, sizeof(Ctx));
    for (int t = 0; t < nthr; t++) { ctx[t].K = malloc((size_t)m * m); memset(ctx[t].K, 99, (size_t)m * m); ctx[t].cov = calloc(m, 1); ctx[t].cyc_cov = calloc(m, 4); }
    // stretch count with nothing covered: w2 path heads + w2 cycles
    int I0 = ncyc; for (int r = 0; r < m; r++) if (pv[r] < 0) I0++;
    fprintf(stderr, "trail %d v%d: m %d, N %d, w2 cycles %d, stretches %d\n", T0, V0, m, N, ncyc, I0);
    double t0 = omp_get_wtime();
    #pragma omp parallel for schedule(dynamic, 1)
    for (int y0 = 0; y0 < m; y0++) { Ctx *C = &ctx[omp_get_thread_num()];
        int dI = stretches_delta_cover(C, y0); C->cov[y0] = 1; if (cyc_id[y0] >= 0) C->cyc_cov[cyc_id[y0]]++;
        dfs(C, y0, 1, 0, I0 + dI, y0);
        C->cov[y0] = 0; if (cyc_id[y0] >= 0) C->cyc_cov[cyc_id[y0]]--; }
    int8_t *K = malloc((size_t)m * m); memset(K, 99, (size_t)m * m); long nodes = 0, paths = 0;
    for (int t = 0; t < nthr; t++) { for (size_t i = 0; i < (size_t)m * m; i++) if (ctx[t].K[i] < K[i]) K[i] = ctx[t].K[i]; nodes += ctx[t].nodes; paths += ctx[t].paths; }
    long byk[16] = {0}; for (size_t i = 0; i < (size_t)m * m; i++) if (K[i] != 99) byk[K[i]]++;
    for (int k = 0; k < m; k++) { K[(size_t)k * m + k] = -1; K[(size_t)k * m + (k + m - 1) % m] = (int8_t)(3 - W[(size_t)((k + m - 1) % m) * m + k]); }
    f = fopen(outp, "wb"); fwrite(K, 1, (size_t)m * m, f); fclose(f);
    printf("{\"checker\": \"kappa_runlevel\", \"trail\": %d, \"version\": %d, \"B\": %d, \"N\": %d, \"paths\": %ld, \"pairs_by_least_kappa\": [", T0, V0, B, N, paths);
    for (int k = 0; k <= B; k++) printf("%s%ld", k ? ", " : "", byk[k]);
    printf("], \"nodes\": %ld, \"sec\": %.1f}\n", nodes, omp_get_wtime() - t0);
    return 0;
}
