// Round R -- detour lemmas L1 and L2 on the option-level excess e (recomputed from runs.bin as in Round P checker B).
//   L1: for options x, u, y of three distinct trails:              e(x -> y) <= 1 + e(x -> u) + e(u -> y)
//   L2: for trails T1 != T2, x, u2 in T1 and u1, y in T2:          e(x -> y) <= 2 + e(x -> u1) + e(u1 -> u2) + e(u2 -> y)
// Both minima are computed by vectorisable min-plus loops per ordered trail pair (independent of bmat.c's loop order).
// Prints the largest value of e(x,y) - bound (<= 0 means the lemma holds) and the number of tight pairs.
// usage: l2check DIR
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#define NTR 30
static int mrun[NTR][2]; static uint8_t *runp[NTR][2];
static int NOPT, otr[16384], ocut[16384], tofs[NTR], tcnt[NTR]; static uint8_t oen[16384][8], oex[16384][8];
static int wgt(const uint8_t *x, const uint8_t *y) { for (int s = 1; s < 8; s++) { int ok = 1; for (int i = 0; s + i < 8; i++) if (x[s + i] != y[i]) { ok = 0; break; } if (ok) return s; } return 8; }
static inline void mp(uint8_t *dst, const uint8_t *src, uint8_t a, int n) { for (int i = 0; i < n; i++) { uint8_t v = (uint8_t)(a + src[i]); dst[i] = v < dst[i] ? v : dst[i]; } }
int main(int argc, char **argv) {
    char p[2048]; snprintf(p, sizeof p, "%s/runs.bin", argv[1]); FILE *f = fopen(p, "rb"); if (!f) return 2;
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int32_t m; if (fread(&m, 4, 1, f) != 1) return 2; mrun[t][v] = m; runp[t][v] = malloc(8 * m); if (fread(runp[t][v], 1, 8 * m, f) != (size_t)(8 * m)) return 2; }
    fclose(f);
    for (int t = 0; t < NTR; t++) { tofs[t] = NOPT; for (int v = 0; v < 2; v++) { int m = mrun[t][v];
        for (int k = 0; k < m; k++) { int o = NOPT++; otr[o] = t; memcpy(oen[o], runp[t][v] + 8 * k, 8); const uint8_t *pr = runp[t][v] + 8 * ((k + m - 1) % m);
            oex[o][0] = pr[7]; for (int i = 1; i < 8; i++) oex[o][i] = pr[i - 1]; ocut[o] = wgt(oex[o], oen[o]); } } tcnt[t] = NOPT - tofs[t]; }
    size_t N = NOPT; uint8_t *e = malloc(N * N); long neg = 0;
    #pragma omp parallel for schedule(dynamic, 16) reduction(+:neg)
    for (int a = 0; a < NOPT; a++) for (int b = 0; b < NOPT; b++) { int v = otr[a] == otr[b] ? 99 : wgt(oex[a], oen[b]) - ocut[b] - 1; if (v < 0) neg++; e[(size_t)a * N + b] = (uint8_t)v; }
    if (neg) { printf("negative cross e\n"); return 3; }
    int worst1 = -100, worst2 = -100; long tight1 = 0, tight2 = 0, pairs = 0;
    #pragma omp parallel for schedule(dynamic, 1) collapse(2) reduction(+:tight1, tight2, pairs)
    for (int t1 = 0; t1 < NTR; t1++) for (int t2 = 0; t2 < NTR; t2++) {
        if (t1 == t2) continue;
        int n1 = tcnt[t1], n2 = tcnt[t2];
        uint8_t *M = malloc((size_t)n2 * n2), *R = malloc(n2), *R1 = malloc(n2);
        // M[u1][y] = min over u2 in T1 of e(u1, u2) + e(u2, y)   (u1, y in T2)
        memset(M, 250, (size_t)n2 * n2);
        for (int i = 0; i < n2; i++) { int u1 = tofs[t2] + i;
            for (int k = 0; k < n1; k++) { int u2 = tofs[t1] + k; mp(M + (size_t)i * n2, e + (size_t)u2 * N + tofs[t2], e[(size_t)u1 * N + u2], n2); } }
        int w1 = -100, w2 = -100;
        for (int a = 0; a < n1; a++) { int x = tofs[t1] + a; const uint8_t *ex = e + (size_t)x * N;
            memset(R, 250, n2); for (int i = 0; i < n2; i++) mp(R, M + (size_t)i * n2, ex[tofs[t2] + i], n2);           // L2 minimum
            memset(R1, 250, n2); for (int u = 0; u < NOPT; u++) { if (otr[u] == t1 || otr[u] == t2) continue; mp(R1, e + (size_t)u * N + tofs[t2], ex[u], n2); }   // L1 minimum
            for (int j = 0; j < n2; j++) { int exy = ex[tofs[t2] + j];
                int d2 = exy - 2 - R[j]; if (d2 > w2) w2 = d2; if (d2 == 0) tight2++;
                int d1 = exy - 1 - R1[j]; if (d1 > w1) w1 = d1; if (d1 == 0) tight1++; pairs++; } }
        #pragma omp critical
        { if (w1 > worst1) worst1 = w1; if (w2 > worst2) worst2 = w2; }
        free(M); free(R); free(R1);
    }
    printf("{\"pairs\": %ld, \"L1_max_excess_over_bound\": %d, \"L1_tight\": %ld, \"L2_max_excess_over_bound\": %d, \"L2_tight\": %ld, \"L1_holds\": %s, \"L2_holds\": %s}\n",
           pairs, worst1, tight1, worst2, tight2, worst1 <= 0 ? "true" : "false", worst2 <= 0 ? "true" : "false");
    return 0;
}
