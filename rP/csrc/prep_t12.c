// Round P -- exact per-identity A-transit tables for the identity-aware search.
//   T1[a][y][x]   = min_{o in A_a} E[y][o] + E[o][x]                       (phi options y, x)
//   T2[a][b][y][x]= min_{o in A_a, o' in A_b} E[y][o] + E[o][o'] + E[o'][x]  (a != b)
//   S1[a][x], S2[a][b][x]: chains at the start of the word ([cut(o_first) = 2] + links)
//   Q1[a][y], Q2[a][b][y]: chains at the end of the word
// all uint8, phi options in increasing global order (P = 2016).
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
static void *rd(const char *p, size_t *n) { FILE *f = fopen(p, "rb"); if (!f) { perror(p); exit(1); } fseek(f, 0, SEEK_END); size_t s = ftell(f); fseek(f, 0, SEEK_SET); void *b = malloc(s); if (fread(b, 1, s, f) != s) exit(2); fclose(f); *n = s; return b; }
static void wr(const char *dir, const char *nm, void *b, size_t s) { char p[1024]; snprintf(p, sizeof p, "%s/%s", dir, nm); FILE *f = fopen(p, "wb"); fwrite(b, 1, s, f); fclose(f); }
int main(int argc, char **argv) {
    const char *dir = argv[1]; char p[1024]; size_t s;
    snprintf(p, sizeof p, "%s/E.bin", dir); int8_t *E = rd(p, &s); int N = 0; while ((size_t)N * N < s) N++;
    snprintf(p, sizeof p, "%s/trail.bin", dir); int32_t *T = rd(p, &s);
    snprintf(p, sizeof p, "%s/cut.bin", dir); int32_t *cut = rd(p, &s);
    int Aid[6] = {1, 8, 15, 22, 28, 29}, alo[6];
    for (int a = 0; a < 6; a++) { alo[a] = -1; for (int o = 0; o < N; o++) if (T[o] == Aid[a]) { alo[a] = o; break; } }
    int NA = 1344; int isA[30] = {0}; for (int a = 0; a < 6; a++) isA[Aid[a]] = 1;
    int P = 0; int *phi = malloc(sizeof(int) * N); for (int o = 0; o < N; o++) if (!isA[T[o]]) phi[P++] = o;
    #define EE(i, j) ((int)E[(size_t)(i) * N + (j)])
    uint8_t *T1 = malloc((size_t)6 * P * P), *T2 = malloc((size_t)36 * P * P);
    uint8_t *S1 = malloc(6 * P), *S2 = malloc(36 * P), *Q1 = malloc(6 * P), *Q2 = malloc(36 * P);
    memset(T2, 120, (size_t)36 * P * P); memset(S2, 120, 36 * P); memset(Q2, 120, 36 * P);
    #pragma omp parallel for schedule(dynamic, 4)
    for (int y = 0; y < P; y++) {
        uint8_t m2[1344];
        for (int a = 0; a < 6; a++) {
            uint8_t row[2048]; memset(row, 120, P); int q1 = 120;
            for (int j = 0; j < NA; j++) { int v = EE(phi[y], alo[a] + j); if (v < q1) q1 = v; const int8_t *er = E + (size_t)(alo[a] + j) * N;
                for (int x = 0; x < P; x++) { int w = v + er[phi[x]]; if (w < row[x]) row[x] = w; } }
            memcpy(T1 + ((size_t)a * P + y) * P, row, P); Q1[a * P + y] = q1;
            for (int b = 0; b < 6; b++) { if (b == a) continue;
                memset(m2, 120, NA);
                for (int j = 0; j < NA; j++) { int v = EE(phi[y], alo[a] + j); const int8_t *er = E + (size_t)(alo[a] + j) * N + alo[b];
                    for (int k = 0; k < NA; k++) { int w = v + er[k]; if (w < m2[k]) m2[k] = w; } }
                int q2 = 120; memset(row, 120, P);
                for (int k = 0; k < NA; k++) { int v = m2[k]; if (v < q2) q2 = v; const int8_t *er = E + (size_t)(alo[b] + k) * N;
                    for (int x = 0; x < P; x++) { int w = v + er[phi[x]]; if (w < row[x]) row[x] = w; } }
                memcpy(T2 + ((size_t)(a * 6 + b) * P + y) * P, row, P); Q2[(a * 6 + b) * P + y] = q2;
            }
        }
    }
    // start chains
    for (int a = 0; a < 6; a++) {
        for (int x = 0; x < P; x++) { int m = 120; for (int j = 0; j < NA; j++) { int v = (cut[alo[a] + j] == 2) + EE(alo[a] + j, phi[x]); if (v < m) m = v; } S1[a * P + x] = m; }
        for (int b = 0; b < 6; b++) { if (b == a) continue;
            int m2[1344]; for (int k = 0; k < NA; k++) m2[k] = 120;
            for (int j = 0; j < NA; j++) { int v = (cut[alo[a] + j] == 2); for (int k = 0; k < NA; k++) { int w = v + EE(alo[a] + j, alo[b] + k); if (w < m2[k]) m2[k] = w; } }
            for (int x = 0; x < P; x++) { int m = 120; for (int k = 0; k < NA; k++) { int w = m2[k] + EE(alo[b] + k, phi[x]); if (w < m) m = w; } S2[(a * 6 + b) * P + x] = m; }
        }
    }
    wr(dir, "T1.bin", T1, (size_t)6 * P * P); wr(dir, "T2.bin", T2, (size_t)36 * P * P);
    wr(dir, "S1x.bin", S1, 6 * P); wr(dir, "S2x.bin", S2, 36 * P); wr(dir, "Q1x.bin", Q1, 6 * P); wr(dir, "Q2x.bin", Q2, 36 * P);
    // consistency with identity-free tables: K1 = min_a T1, K2 = min_{a!=b} T2
    snprintf(p, sizeof p, "%s/Ka.bin", dir); uint8_t *Ka = rd(p, &s);
    long bad1 = 0, bad2 = 0;
    for (size_t i = 0; i < (size_t)P * P; i++) { int y = i / P, x = i % P; if (T[phi[y]] == T[phi[x]]) continue;
        int m1 = 255, m2 = 255; for (int a = 0; a < 6; a++) { if (T1[(size_t)a * P * P + i] < m1) m1 = T1[(size_t)a * P * P + i];
            for (int b = 0; b < 6; b++) if (b != a && T2[(size_t)(a * 6 + b) * P * P + i] < m2) m2 = T2[(size_t)(a * 6 + b) * P * P + i]; }
        bad1 += m1 != Ka[i]; bad2 += m2 != Ka[(size_t)P * P + i]; }
    fprintf(stderr, "check: min_a T1 vs K_1 mismatches %ld, min T2 vs K_2 mismatches %ld\n", bad1, bad2);
    return 0;
}
