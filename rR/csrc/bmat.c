// Round R -- anchor detour table.  For options x, y of different trails:
//     B(x, y) = min over options u of a third trail (trail(u) != trail(x), trail(y)) of e(x -> u) + e(u -> y),
//     ehat(x, y) = min(e(x, y), 1 + B(x, y)).
// e is recomputed from runs.bin exactly as in Round P checker B (e = w(exit(x), entry(y)) - cut(y) - 1, options in
// trail-major order (t, v, k)).  Writes B and ehat as NOPT x NOPT int8 (99 on the same-trail block) and prints
// statistics, and a mutation file (lines "x y ehat" for every pair with ehat < e) in the CKB_MUT format.
// usage: bmat DIR OUTPREFIX
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#define NTR 30
static int mrun[NTR][2]; static uint8_t *runp[NTR][2];
static int NOPT, otr[16384], ocut[16384]; static uint8_t oen[16384][8], oex[16384][8];
static int wgt(const uint8_t *x, const uint8_t *y) { for (int s = 1; s < 8; s++) { int ok = 1; for (int i = 0; s + i < 8; i++) if (x[s + i] != y[i]) { ok = 0; break; } if (ok) return s; } return 8; }
int main(int argc, char **argv) {
    char p[2048]; snprintf(p, sizeof p, "%s/runs.bin", argv[1]); FILE *f = fopen(p, "rb"); if (!f) return 2;
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int32_t m; if (fread(&m, 4, 1, f) != 1) return 2; mrun[t][v] = m; runp[t][v] = malloc(8 * m); if (fread(runp[t][v], 1, 8 * m, f) != (size_t)(8 * m)) return 2; }
    fclose(f);
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int m = mrun[t][v];
        for (int k = 0; k < m; k++) { int o = NOPT++; otr[o] = t; memcpy(oen[o], runp[t][v] + 8 * k, 8); const uint8_t *pr = runp[t][v] + 8 * ((k + m - 1) % m);
            oex[o][0] = pr[7]; for (int i = 1; i < 8; i++) oex[o][i] = pr[i - 1]; ocut[o] = wgt(oex[o], oen[o]); } }
    size_t N = NOPT; int8_t *e = malloc(N * N);
    #pragma omp parallel for schedule(dynamic, 16)
    for (int a = 0; a < NOPT; a++) for (int b = 0; b < NOPT; b++) e[(size_t)a * N + b] = otr[a] == otr[b] ? 99 : (int8_t)(wgt(oex[a], oen[b]) - ocut[b] - 1);
    // B via sparse lists: for each x, the u with small e(x -> u); B(x, y) <= 5 + 5 always, cap search at e <= 9
    int8_t *B = malloc(N * N); memset(B, 99, N * N);
    #pragma omp parallel for schedule(dynamic, 8)
    for (int x = 0; x < NOPT; x++) {
        int8_t *row = B + (size_t)x * N; int8_t best[16384]; for (int y = 0; y < NOPT; y++) best[y] = 99;
        for (int u = 0; u < NOPT; u++) { if (otr[u] == otr[x]) continue; int a = e[(size_t)x * N + u]; if (a >= 99) continue;
            const int8_t *er = e + (size_t)u * N;
            for (int y = 0; y < NOPT; y++) { if (otr[y] == otr[u] || otr[y] == otr[x]) continue; int v = a + er[y]; if (v < best[y]) best[y] = (int8_t)v; } }
        for (int y = 0; y < NOPT; y++) row[y] = otr[y] == otr[x] ? 99 : best[y];
    }
    int8_t *eh = malloc(N * N); long hist[16][16]; memset(hist, 0, sizeof hist); long nless = 0;
    snprintf(p, sizeof p, "%s_mut.txt", argv[2]); FILE *mf = fopen(p, "w");
    for (size_t a = 0; a < N; a++) for (size_t b = 0; b < N; b++) { size_t i = a * N + b; if (e[i] >= 99) { eh[i] = 99; continue; }
        int v = e[i], w = 1 + B[i]; eh[i] = (int8_t)(w < v ? w : v); hist[v][B[i] < 15 ? B[i] : 15]++; if (w < v) { nless++; fprintf(mf, "%zu %zu %d\n", a, b, w); } }
    fclose(mf);
    snprintf(p, sizeof p, "%s_B.bin", argv[2]); f = fopen(p, "wb"); fwrite(B, 1, N * N, f); fclose(f);
    snprintf(p, sizeof p, "%s_ehat.bin", argv[2]); f = fopen(p, "wb"); fwrite(eh, 1, N * N, f); fclose(f);
    printf("{\"options\": %d, \"pairs_with_ehat_less_than_e\": %ld, \"hist_e_by_B\": {", NOPT, nless);
    for (int v = 0; v < 6; v++) { printf("%s\"e=%d\": [", v ? ", " : "", v); for (int b = 0; b < 8; b++) printf("%s%ld", b ? ", " : "", hist[v][b]); printf("]"); }
    printf("}}\n");
    return 0;
}
