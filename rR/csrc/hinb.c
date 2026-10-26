// Round R -- 2-hop anchor bounds.  For options x, y of different trails the exact closing of a bracket whose cycle
// ends at x and starts at y is >= B(x, y) = min_u e(x -> u) + e(u -> y) (u of a third trail).  Decoupled bounds:
//   hin(y)  = min_u e(u -> y),            hout(x)  = min_u e(x -> u)                  (B >= hout(x) + hin(y))
//   hinB(y) = min_u hin(u) + e(u -> y),   houtB(x) = min_u e(x -> u) + hout(u)        (B >= hinB(y), B >= houtB(x))
// (hin(u) taken over options of trails other than u's; every u of a third trail).  Prints the distributions and the
// distribution of B over all pairs versus max(hout + hin, hinB, houtB); writes hin, hout, hinB, houtB (uint8 each).
// usage: hinb DIR OUT.bin
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
    size_t N = NOPT; uint8_t *e = malloc(N * N);
    #pragma omp parallel for schedule(dynamic, 16)
    for (int a = 0; a < NOPT; a++) for (int b = 0; b < NOPT; b++) e[(size_t)a * N + b] = otr[a] == otr[b] ? 99 : (uint8_t)(wgt(oex[a], oen[b]) - ocut[b] - 1);
    uint8_t *hin = malloc(N), *hout = malloc(N), *hinB = malloc(N), *houtB = malloc(N);
    #pragma omp parallel for
    for (int o = 0; o < NOPT; o++) { int mi = 99, mo = 99; for (int u = 0; u < NOPT; u++) { if (otr[u] == otr[o]) continue; if (e[(size_t)u * N + o] < mi) mi = e[(size_t)u * N + o]; if (e[(size_t)o * N + u] < mo) mo = e[(size_t)o * N + u]; } hin[o] = mi; hout[o] = mo; }
    #pragma omp parallel for
    for (int o = 0; o < NOPT; o++) { int mi = 99, mo = 99; for (int u = 0; u < NOPT; u++) { if (otr[u] == otr[o]) continue; int a = hin[u] + e[(size_t)u * N + o], b = e[(size_t)o * N + u] + hout[u]; if (a < mi) mi = a; if (b < mo) mo = b; } hinB[o] = mi; houtB[o] = mo; }
    long h[4][8]; memset(h, 0, sizeof h);
    for (int o = 0; o < NOPT; o++) { h[0][hin[o] < 7 ? hin[o] : 7]++; h[1][hout[o] < 7 ? hout[o] : 7]++; h[2][hinB[o] < 7 ? hinB[o] : 7]++; h[3][houtB[o] < 7 ? houtB[o] : 7]++; }
    // B over all cross pairs vs the decoupled maximum
    long hb[8][8]; memset(hb, 0, sizeof hb);
    #pragma omp parallel
    { long loc[8][8]; memset(loc, 0, sizeof loc); uint8_t *row = malloc(N);
      #pragma omp for schedule(dynamic, 16)
      for (int x = 0; x < NOPT; x++) { memset(row, 250, N);
          for (int u = 0; u < NOPT; u++) { if (otr[u] == otr[x]) continue; uint8_t a = e[(size_t)x * N + u]; const uint8_t *er = e + (size_t)u * N; for (int y = 0; y < NOPT; y++) { uint8_t v = (uint8_t)(a + er[y]); if (otr[y] != otr[u] && v < row[y]) row[y] = v; } }
          for (int y = 0; y < NOPT; y++) { if (otr[y] == otr[x]) continue; int B = row[y] < 7 ? row[y] : 7; int d = hout[x] + hin[y]; if (hinB[y] > d) d = hinB[y]; if (houtB[x] > d) d = houtB[x]; if (d > 7) d = 7; loc[B][d]++; } }
      #pragma omp critical
      { for (int i = 0; i < 8; i++) for (int j = 0; j < 8; j++) hb[i][j] += loc[i][j]; } free(row); }
    printf("{\"hin\": [%ld,%ld,%ld,%ld,%ld,%ld,%ld,%ld], \"hout\": [%ld,%ld,%ld,%ld,%ld,%ld,%ld,%ld], \"hinB\": [%ld,%ld,%ld,%ld,%ld,%ld,%ld,%ld], \"houtB\": [%ld,%ld,%ld,%ld,%ld,%ld,%ld,%ld],\n \"B_vs_decoupled_max\": [",
        h[0][0],h[0][1],h[0][2],h[0][3],h[0][4],h[0][5],h[0][6],h[0][7], h[1][0],h[1][1],h[1][2],h[1][3],h[1][4],h[1][5],h[1][6],h[1][7],
        h[2][0],h[2][1],h[2][2],h[2][3],h[2][4],h[2][5],h[2][6],h[2][7], h[3][0],h[3][1],h[3][2],h[3][3],h[3][4],h[3][5],h[3][6],h[3][7]);
    for (int i = 0; i < 8; i++) { printf("%s[", i ? ", " : ""); for (int j = 0; j < 8; j++) printf("%s%ld", j ? ", " : "", hb[i][j]); printf("]"); }
    printf("]}\n");
    f = fopen(argv[2], "wb"); fwrite(hin, 1, N, f); fwrite(hout, 1, N, f); fwrite(hinB, 1, N, f); fwrite(houtB, 1, N, f); fclose(f);
    return 0;
}
