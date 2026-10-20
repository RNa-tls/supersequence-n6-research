// Round Q, section 3 -- exact evaluation of single two-piece splits built from given single-opening trail orders.
// A route with exactly one trail T cut into two fragments f1 = [a, b), f2 = [b, a) (same version, a != b) and all other
// trails single pieces has virtual cover  path (... -> T(a) -> ...)  +  cycle (T(b) -> B -> T(b)),  where B is the block of
// trails between the fragments; its unsplit order  (A, T, B, C)  or  (A, B, T, C)  has B adjacent to T.  Hence
//    J = 77 + G,   G = 1 + Path(a) + Cyc(b),   minimised over a != b of one version, all other options free.
// For every order pi in the input, every anchor position i and every nonempty block B adjacent to it (either side) this
// program computes min G exactly (fixed orders, all options optimal).  E = single-piece option excess matrix.
// usage: split1 PDPDIR(E.bin trail.bin cut.bin) ORDERS.txt OUT.json [THRESH]
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#define BIG 10000
static int N; static int8_t *E; static int *trail, *cutw; static int tofs[31], tcnt[30], mver[30];
static inline int ee(int a, int b) { int v = E[(size_t)a * N + b]; return v; }
typedef struct { int G, oi, i, dir, j, a, b, F; } Best;
int main(int argc, char **argv) {
    const char *D = argv[1], *ordp = argv[2], *outp = argv[3]; int THRESH = argc > 4 ? atoi(argv[4]) : 21; char p[2048];
    FILE *f; size_t sz;
    snprintf(p, sizeof p, "%s/trail.bin", D); f = fopen(p, "rb"); fseek(f, 0, SEEK_END); sz = ftell(f); fseek(f, 0, SEEK_SET); N = sz / 4; trail = malloc(sz); if (fread(trail, 4, N, f) != (size_t)N) return 2; fclose(f);
    snprintf(p, sizeof p, "%s/cut.bin", D); f = fopen(p, "rb"); cutw = malloc(4 * N); if (fread(cutw, 4, N, f) != (size_t)N) return 2; fclose(f);
    snprintf(p, sizeof p, "%s/E.bin", D); f = fopen(p, "rb"); E = malloc((size_t)N * N); if (fread(E, 1, (size_t)N * N, f) != (size_t)N * N) return 2; fclose(f);
    for (int t = 0; t < 30; t++) { tofs[t] = -1; tcnt[t] = 0; }
    for (int o = 0; o < N; o++) { int t = trail[o]; if (tofs[t] < 0) tofs[t] = o; tcnt[t]++; }
    for (int t = 0; t < 30; t++) { mver[t] = tcnt[t] / 2; for (int q = 0; q < tcnt[t]; q++) if (trail[tofs[t] + q] != t) { fprintf(stderr, "options not contiguous\n"); return 3; } }
    // sanity: same-trail entries must be unusable (large), cross-trail >= 0
    long neg = 0; for (int o = 0; o < N; o += 7) for (int o2 = 0; o2 < N; o2++) if (trail[o] != trail[o2] && ee(o, o2) < 0) neg++;
    if (neg) { fprintf(stderr, "negative cross-trail excess\n"); return 4; }
    // orders
    f = fopen(ordp, "r"); int cap = 4096, no = 0; int (*ord)[30] = malloc(sizeof(int[30]) * cap);
    while (1) { int ok = 1; for (int k = 0; k < 30; k++) if (fscanf(f, "%d%*[, ]", &ord[no][k]) != 1) { ok = 0; break; } if (!ok) break; no++; if (no == cap) { cap *= 2; ord = realloc(ord, sizeof(int[30]) * cap); } }
    fclose(f);
    fprintf(stderr, "options %d, orders %d\n", N, no);
    Best *bo = malloc(sizeof(Best) * no); long nconf = 0, nle = 0;
    #pragma omp parallel for schedule(dynamic, 1) reduction(+:nconf, nle)
    for (int oi = 0; oi < no; oi++) {
        int *pi = ord[oi]; int n = 30;
        int *fwd[30], *bwd[30];
        for (int k = 0; k < n; k++) { fwd[k] = malloc(4 * tcnt[pi[k]]); bwd[k] = malloc(4 * tcnt[pi[k]]); }
        for (int q = 0; q < tcnt[pi[0]]; q++) fwd[0][q] = cutw[tofs[pi[0]] + q] == 2;
        for (int k = 1; k < n; k++) { int A = pi[k - 1], Bt = pi[k];
            for (int q2 = 0; q2 < tcnt[Bt]; q2++) fwd[k][q2] = BIG;
            for (int q = 0; q < tcnt[A]; q++) { int v = fwd[k - 1][q]; const int8_t *er = E + (size_t)(tofs[A] + q) * N + tofs[Bt];
                for (int q2 = 0; q2 < tcnt[Bt]; q2++) { int c = v + er[q2]; if (c < fwd[k][q2]) fwd[k][q2] = c; } } }
        for (int q = 0; q < tcnt[pi[n - 1]]; q++) bwd[n - 1][q] = 0;
        for (int k = n - 2; k >= 0; k--) { int A = pi[k], Bt = pi[k + 1];
            for (int q = 0; q < tcnt[A]; q++) { int m = BIG; const int8_t *er = E + (size_t)(tofs[A] + q) * N + tofs[Bt];
                for (int q2 = 0; q2 < tcnt[Bt]; q2++) { int c = er[q2] + bwd[k + 1][q2]; if (c < m) m = c; } bwd[k][q] = m; } }
        int F = BIG; for (int q = 0; q < tcnt[pi[n - 1]]; q++) if (fwd[n - 1][q] < F) F = fwd[n - 1][q];
        Best b0 = {BIG, oi, -1, 0, -1, -1, -1, F};
        for (int i = 0; i < n; i++) { int T = pi[i], nT = tcnt[T];
            int *path = malloc(4 * nT), *cyc = malloc(4 * nT);
            for (int dir = 0; dir < 2; dir++) {
                // dir 0: B = pi[i+1 .. j-1] (after T), path = pi[0..i] + pi[j..]; dir 1: B = pi[j .. i-1], path = pi[0..j-1] + T + pi[i+1..]
                int lo = dir == 0 ? i + 2 : 0, hi = dir == 0 ? n : i - 1;
                if (dir == 0 && i + 1 >= n) continue; if (dir == 1 && i == 0) continue;
                int first = dir == 0 ? pi[i + 1] : pi[i - 1];
                int *S = malloc(4 * (size_t)nT * 1344), *S2 = malloc(4 * (size_t)nT * 1344); int ncur = tcnt[first];
                for (int bq = 0; bq < nT; bq++) for (int q = 0; q < ncur; q++)
                    S[(size_t)bq * 1344 + q] = dir == 0 ? ee(tofs[T] + bq, tofs[first] + q) : ee(tofs[first] + q, tofs[T] + bq);
                int cur = dir == 0 ? i + 1 : i - 1;
                while (1) {
                    // close the cycle at the current block end, evaluate, then extend
                    int j = dir == 0 ? cur + 1 : cur;    // dir 0: B = pi[i+1..cur], j = cur+1; dir 1: B = pi[cur..i-1], j = cur
                    int curT = pi[cur];
                    for (int bq = 0; bq < nT; bq++) { int m = BIG;
                        for (int q = 0; q < ncur; q++) { int c = S[(size_t)bq * 1344 + q] + (dir == 0 ? ee(tofs[curT] + q, tofs[T] + bq) : ee(tofs[T] + bq, tofs[curT] + q)); if (c < m) m = c; }
                        cyc[bq] = m; }
                    for (int aq = 0; aq < nT; aq++) {
                        int L, R;
                        if (dir == 0) { L = fwd[i][aq]; if (j >= n) R = 0; else { R = BIG; int Ct = pi[j]; const int8_t *er = E + (size_t)(tofs[T] + aq) * N + tofs[Ct]; for (int q = 0; q < tcnt[Ct]; q++) { int c = er[q] + bwd[j][q]; if (c < R) R = c; } } }
                        else { R = bwd[i][aq]; if (j == 0) L = cutw[tofs[T] + aq] == 2; else { L = BIG; int At = pi[j - 1]; for (int q = 0; q < tcnt[At]; q++) { int c = fwd[j - 1][q] + ee(tofs[At] + q, tofs[T] + aq); if (c < L) L = c; } } }
                        path[aq] = L + R; }
                    // combine: a != b, same version
                    int best = BIG, ba = -1, bb = -1;
                    for (int v = 0; v < 2; v++) { int m1 = BIG, i1 = -1, m2 = BIG, i2 = -1;     // two smallest cyc in version v
                        for (int q = v * mver[T]; q < (v + 1) * mver[T]; q++) { int c = cyc[q]; if (c < m1) { m2 = m1; i2 = i1; m1 = c; i1 = q; } else if (c < m2) { m2 = c; i2 = q; } }
                        for (int q = v * mver[T]; q < (v + 1) * mver[T]; q++) { int cb = q == i1 ? m2 : m1, ib = q == i1 ? i2 : i1; int c = path[q] + cb; if (c < best) { best = c; ba = q; bb = ib; } } }
                    int G = 1 + best; nconf++; if (G <= THRESH) nle++;
                    if (G < b0.G) { b0.G = G; b0.i = i; b0.dir = dir; b0.j = j; b0.a = ba; b0.b = bb; }
                    // extend the block
                    int nxt = dir == 0 ? cur + 1 : cur - 1;
                    if (dir == 0 && nxt > n - 1) break; if (dir == 1 && nxt < 0) break;
                    if (dir == 0 && nxt >= n) break;
                    int nt = pi[nxt], nn = tcnt[nt];
                    for (int bq = 0; bq < nT; bq++) { int *dst = S2 + (size_t)bq * 1344; for (int q2 = 0; q2 < nn; q2++) dst[q2] = BIG;
                        for (int q = 0; q < ncur; q++) { int v = S[(size_t)bq * 1344 + q]; if (v >= BIG) continue;
                            if (dir == 0) { const int8_t *er = E + (size_t)(tofs[curT] + q) * N + tofs[nt]; for (int q2 = 0; q2 < nn; q2++) { int c = v + er[q2]; if (c < dst[q2]) dst[q2] = c; } }
                            else { for (int q2 = 0; q2 < nn; q2++) { int c = v + ee(tofs[nt] + q2, tofs[curT] + q); if (c < dst[q2]) dst[q2] = c; } } } }
                    int *tmp = S; S = S2; S2 = tmp; ncur = nn; cur = nxt;
                    if (dir == 0 && cur == n - 1 && 0) break;
                    (void)lo; (void)hi;
                }
                free(S); free(S2);
            }
            free(path); free(cyc); }
        bo[oi] = b0;
        for (int k = 0; k < n; k++) { free(fwd[k]); free(bwd[k]); }
    }
    int gb = BIG, gi = -1; for (int oi = 0; oi < no; oi++) if (bo[oi].G < gb) { gb = bo[oi].G; gi = oi; }
    FILE *fo = fopen(outp, "w"); fprintf(fo, "{\"orders\": %d, \"configurations\": %ld, \"configs_le_thresh\": %ld, \"thresh\": %d, \"best_G\": %d, \"best\": ", no, nconf, nle, THRESH, gb);
    if (gi >= 0) { Best b = bo[gi]; fprintf(fo, "{\"order_index\": %d, \"F_order\": %d, \"anchor_pos\": %d, \"anchor_trail\": %d, \"dir\": %d, \"j\": %d, \"a\": %d, \"b\": %d, \"order\": [", b.oi, b.F, b.i, ord[b.oi][b.i], b.dir, b.j, b.a, b.b);
        for (int k = 0; k < 30; k++) fprintf(fo, "%s%d", k ? ", " : "", ord[b.oi][k]); fprintf(fo, "]}"); } else fprintf(fo, "null");
    fprintf(fo, ", \"per_order\": ["); for (int oi = 0; oi < no; oi++) fprintf(fo, "%s[%d, %d]", oi ? ", " : "", bo[oi].F, bo[oi].G); fprintf(fo, "]}\n"); fclose(fo);
    long hist[40] = {0}; for (int oi = 0; oi < no; oi++) { int g = bo[oi].G; if (g < 40) hist[g]++; }
    printf("{\"orders\": %d, \"configurations\": %ld, \"configs_le_thresh\": %ld, \"best_G\": %d, \"best_G_hist\": {", no, nconf, nle, gb);
    int first = 1; for (int g = 0; g < 40; g++) if (hist[g]) { printf("%s\"%d\": %ld", first ? "" : ", ", g, hist[g]); first = 0; } printf("}}\n");
    return 0;
}
