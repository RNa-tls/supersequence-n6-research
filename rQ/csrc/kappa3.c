// Round Q, section 3 -- exact kappa table of ALL single visits of one trail-version in exactly three pieces.
// Version cycle r_0..r_{m-1}; cut weight c_k = w(last r_{k-1}, r_k) (2 inside a chain, 3 at a chain start); jump term
// E'(i -> k) = w(last r_i, r_k) - c_k.  Three cuts u, p, q in cyclic order give the pieces A1 = [u, p), A2 = [p, q),
// A3 = [q, u).  The natural adjacencies A1 A2, A2 A3, A3 A1 merge pieces, so the only 3-piece visit orders are the three
// cyclic relabelings of  A1 A3 A2 :  entry u, exit q - 1, jumps p-1 -> q and u-1 -> p,
//     kappa = [c_u = 2] + E'(p-1 -> q) + E'(u-1 -> p).
// Enumerating every ordered (u, p, q) (u any start, then p, q at offsets 1 <= dp < dq <= m-1) covers all of them.
// Output: m x m int8 table K[y * m + x] = least kappa over 3-piece visits with entry y and exit x (99 = none), single
// pieces K[k * m + k-1] = 3 - c_k (as dominance.c expects), diagonal -1.  Also the histogram of the least kappa.
// FOUR PIECES (argument 4): cuts u1 < u2 < u3 < u4 (cyclic), pieces B_i = [u_i, u_{i+1}); with B1 first, the only orders
// without a natural adjacency are
//   (1,3,2,4): entry u1, exit u1 - 1 (the single piece's pair):  kappa = [c_u1 = 2] + T,
//              T = E'(u2-1 -> u3) + E'(u4-1 -> u2) + E'(u3-1 -> u4)   -> dominated by the single piece iff T >= 0;
//   (1,4,3,2): entry u1, exit u3 - 1:  kappa = [c_u1 = 2] + E'(u1-1 -> u3) + min_{u2 in (u1,u3), u4 in (u3,u1)} f(u2, u4),
//              f(u2, u4) = E'(u2-1 -> u4) + E'(u4-1 -> u2)   (prefix minima, O(m^3)).
// The table then holds the (1,4,3,2) minima; min T over all cyclic triples is reported (it bounds every u1).
// usage: kappa3 DIR(runs.bin) TRAIL VERSION OUT.bin [PIECES = 3 | 4]
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#define NTR 30
static int mrun[NTR][2]; static uint8_t *runp[NTR][2];
static int wgt(const uint8_t *x, const uint8_t *y) { for (int s = 1; s < 8; s++) { int ok = 1; for (int i = 0; s + i < 8; i++) if (x[s + i] != y[i]) { ok = 0; break; } if (ok) return s; } return 8; }
int main(int argc, char **argv) {
    const char *dir = argv[1]; int T0 = atoi(argv[2]), V0 = atoi(argv[3]); const char *outp = argv[4]; char p[2048];
    snprintf(p, sizeof p, "%s/runs.bin", dir); FILE *f = fopen(p, "rb"); if (!f) return 2;
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int32_t m; if (fread(&m, 4, 1, f) != 1) return 2; mrun[t][v] = m; runp[t][v] = malloc(8 * m); if (fread(runp[t][v], 1, 8 * m, f) != (size_t)(8 * m)) return 2; }
    fclose(f);
    int m = mrun[T0][V0]; const uint8_t *R = runp[T0][V0];
    uint8_t (*last)[8] = malloc(8 * m); for (int k = 0; k < m; k++) { last[k][0] = R[8 * k + 7]; for (int i = 1; i < 8; i++) last[k][i] = R[8 * k + i - 1]; }
    int8_t *W = malloc((size_t)m * m); for (int i = 0; i < m; i++) for (int k = 0; k < m; k++) W[(size_t)i * m + k] = (int8_t)wgt(last[i], R + 8 * k);
    int *c = malloc(4 * m); for (int k = 0; k < m; k++) c[k] = W[(size_t)((k + m - 1) % m) * m + k];
    int8_t *Ej = malloc((size_t)m * m); for (int i = 0; i < m; i++) for (int k = 0; k < m; k++) Ej[(size_t)i * m + k] = (int8_t)(W[(size_t)i * m + k] - c[k]);
    int8_t *K = malloc((size_t)m * m); memset(K, 99, (size_t)m * m);
    long nvis = 0; int kmin = 99; int npc = argc > 5 ? atoi(argv[5]) : 3; int Tmin = 99; long nT = 0;
    #define EJ(i, k) ((int)Ej[(size_t)(((i) % m + m) % m) * m + (((k) % m + m) % m)])
    if (npc == 4) {
        // (1,3,2,4): min over cyclic triples u2 < u3 < u4 of T
        for (int u2 = 0; u2 < m; u2++) for (int d3 = 1; d3 < m - 1; d3++) { int u3 = (u2 + d3) % m; int a = EJ(u2 - 1, u3);
            for (int d4 = d3 + 1; d4 <= m - 2; d4++) { int u4 = (u2 + d4) % m; int T = a + EJ(u4 - 1, u2) + EJ(u3 - 1, u4); nT++; if (T < Tmin) Tmin = T; } }
        // (1,4,3,2): for each u3, offsets o from u3: g(d) = min_{o2 in [d+1, m-1]} min_{o4 in [1, d-1]} f(u2, u4), u1 at offset d
        int *P = malloc(4 * (size_t)m * m), *g = malloc(4 * m);
        for (int u3 = 0; u3 < m; u3++) {
            for (int o2 = 1; o2 < m; o2++) { int u2 = (u3 + o2) % m; int run = 99; int *Pr = P + (size_t)o2 * m; Pr[0] = Pr[1] = 99;
                for (int d = 2; d < m; d++) { int u4 = (u3 + d - 1) % m; if (d - 1 < o2) { int fv = EJ(u2 - 1, u4) + EJ(u4 - 1, u2); if (fv < run) run = fv; } Pr[d] = run; } }
            for (int d = 2; d <= m - 2; d++) { int best = 99; for (int o2 = d + 1; o2 < m; o2++) { int v = P[(size_t)o2 * m + d]; if (v < best) best = v; } g[d] = best; }
            for (int d = 2; d <= m - 2; d++) { int u1 = (u3 + d) % m; if (g[d] >= 99) continue; int kap = (c[u1] == 2) + EJ(u1 - 1, u3) + g[d]; int x = (u3 + m - 1) % m;
                int8_t *kk = &K[(size_t)u1 * m + x]; if (kap < *kk) *kk = (int8_t)kap; nvis++; if (kap < kmin) kmin = kap; } }
        free(P); free(g);
    }
    else for (int u = 0; u < m; u++) { int mid = c[u] == 2, um1 = (u + m - 1) % m;
        for (int dp = 1; dp < m - 1; dp++) { int pp = (u + dp) % m, pm1 = (pp + m - 1) % m; int base = mid + Ej[(size_t)um1 * m + pp];
            const int8_t *row = Ej + (size_t)pm1 * m;
            for (int dq = dp + 1; dq <= m - 1; dq++) { int q = (u + dq) % m; int kap = base + row[q]; int x = (q + m - 1) % m;
                int8_t *kk = &K[(size_t)u * m + x]; if (kap < *kk) *kk = (int8_t)kap; nvis++; if (kap < kmin) kmin = kap; } } }
    long hist[16] = {0}; long npair = 0;
    for (int y = 0; y < m; y++) for (int x = 0; x < m; x++) { int k = K[(size_t)y * m + x]; if (k == 99) continue; npair++; hist[k < -3 ? 0 : (k > 11 ? 15 : k + 4)]++; }
    for (int k = 0; k < m; k++) { if (K[(size_t)k * m + (k + m - 1) % m] != 99) { fprintf(stderr, "a 3-piece visit has the single-piece (entry, exit) pair %d\n", k); }
        K[(size_t)k * m + (k + m - 1) % m] = (int8_t)(3 - c[k]); K[(size_t)k * m + k] = -1; }
    f = fopen(outp, "wb"); fwrite(K, 1, (size_t)m * m, f); fclose(f);
    if (npc == 4) printf("{\"pieces\": 4, \"trail\": %d, \"version\": %d, \"runs\": %d, \"order_1324_triples\": %ld, \"order_1324_min_T\": %d, \"order_1432_entries\": %ld, \"pairs\": %ld, \"kappa_min\": %d, \"kappa_hist_from_minus4\": [", T0, V0, m, nT, Tmin, nvis, npair, kmin);
    else printf("{\"trail\": %d, \"version\": %d, \"runs\": %d, \"three_piece_visits\": %ld, \"pairs\": %ld, \"kappa_min\": %d, \"kappa_hist_from_minus4\": [", T0, V0, m, nvis, npair, kmin);
    for (int b = 0; b < 16; b++) printf("%s%ld", b ? ", " : "", hist[b]); printf("]}\n");
    return 0;
}
