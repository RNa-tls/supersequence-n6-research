// Round P -- exact A-chain connector tables for chains of length a = 1..6 between phi options
// (consecutive A trails distinct; non-consecutive repeats allowed: a relaxation, never an overestimate).
//   K_a[y][x] = min over A_1..A_a (A_i != A_{i+1}) and their options of
//               E[y][o_1] + E[o_1][o_2] + ... + E[o_{a-1}][o_a] + E[o_a][x]
//   S_a[x]    = same with the chain at the start of the word (first option pays [cut = 2], no y)
//   Q_a[y]    = same with the chain at the end of the word (no x)
// output: Ka.bin (6 x P x P uint8), Sa.bin (6 x P), Qa.bin (6 x P)
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#define CAPV 60
static void *rd(const char *p, size_t *n) { FILE *f = fopen(p, "rb"); if (!f) { perror(p); exit(1); } fseek(f, 0, SEEK_END); size_t s = ftell(f); fseek(f, 0, SEEK_SET); void *b = malloc(s); if (fread(b, 1, s, f) != s) exit(2); fclose(f); *n = s; return b; }
static void wr(const char *dir, const char *nm, void *b, size_t s) { char p[1024]; snprintf(p, sizeof p, "%s/%s", dir, nm); FILE *f = fopen(p, "wb"); fwrite(b, 1, s, f); fclose(f); }
int main(int argc, char **argv) {
    const char *dir = argv[1]; char p[1024]; size_t s;
    snprintf(p, sizeof p, "%s/E.bin", dir); int8_t *E = rd(p, &s); int N = 0; while ((size_t)N * N < s) N++;
    snprintf(p, sizeof p, "%s/trail.bin", dir); int32_t *T = rd(p, &s);
    snprintf(p, sizeof p, "%s/cut.bin", dir); int32_t *cut = rd(p, &s);
    int Aid[6] = {1, 8, 15, 22, 28, 29}, alo[6], ahi[6];
    for (int a = 0; a < 6; a++) { alo[a] = -1; for (int o = 0; o < N; o++) if (T[o] == Aid[a]) { if (alo[a] < 0) alo[a] = o; ahi[a] = o + 1; } }
    int NA = ahi[0] - alo[0];
    int isA[30] = {0}; for (int a = 0; a < 6; a++) isA[Aid[a]] = 1;
    int P = 0; int *phi = malloc(sizeof(int) * N); for (int o = 0; o < N; o++) if (!isA[T[o]]) phi[P++] = o;
    // rows: y = 0..P-1 (phi options) plus one extra row y = P meaning "start of the word"
    int RWS = P + 1;
    uint8_t *cur = malloc((size_t)RWS * 6 * NA), *nxt = malloc((size_t)RWS * 6 * NA);
    uint8_t *Ka = malloc((size_t)6 * P * P), *Sa = malloc((size_t)6 * P), *Qa = malloc((size_t)6 * P);
    // level 1
    #pragma omp parallel for
    for (int y = 0; y < RWS; y++) for (int a = 0; a < 6; a++) for (int j = 0; j < NA; j++) {
        int o = alo[a] + j; int v = (y < P) ? E[(size_t)phi[y] * N + o] : (cut[o] == 2);
        cur[((size_t)y * 6 + a) * NA + j] = v; }
    for (int len = 1; len <= 6; len++) {
        // close: K_len, S_len, Q_len
        #pragma omp parallel for schedule(dynamic, 8)
        for (int y = 0; y < RWS; y++) {
            uint8_t row[4096]; memset(row, CAPV, P); int q = CAPV;
            for (int a = 0; a < 6; a++) for (int j = 0; j < NA; j++) {
                int v = cur[((size_t)y * 6 + a) * NA + j]; if (v >= CAPV) continue; if (v < q) q = v;
                const int8_t *er = E + (size_t)(alo[a] + j) * N;
                for (int x = 0; x < P; x++) { int w = v + er[phi[x]]; if (w < row[x]) row[x] = w; } }
            if (y < P) { memcpy(Ka + ((size_t)(len - 1) * P + y) * P, row, P); Qa[(size_t)(len - 1) * P + y] = q; }
            else memcpy(Sa + (size_t)(len - 1) * P, row, P);
        }
        if (len == 6) break;
        // extend: nxt[y][b][o_b] = min over a != b, o_a of cur[y][a][o_a] + E[o_a][o_b]
        #pragma omp parallel for schedule(dynamic, 8)
        for (int y = 0; y < RWS; y++) {
            uint8_t acc[6][2048]; memset(acc, CAPV, sizeof acc);
            for (int a = 0; a < 6; a++) for (int j = 0; j < NA; j++) {
                int v = cur[((size_t)y * 6 + a) * NA + j]; if (v >= CAPV) continue;
                const int8_t *er = E + (size_t)(alo[a] + j) * N;
                for (int b = 0; b < 6; b++) { if (b == a) continue; const int8_t *eb = er + alo[b]; uint8_t *ab = acc[b];
                    for (int k = 0; k < NA; k++) { int w = v + eb[k]; if (w < ab[k]) ab[k] = w; } } }
            for (int b = 0; b < 6; b++) memcpy(nxt + ((size_t)y * 6 + b) * NA, acc[b], NA);
        }
        uint8_t *tmp = cur; cur = nxt; nxt = tmp;
        fprintf(stderr, "length %d done\n", len + 1);
    }
    wr(dir, "Ka.bin", Ka, (size_t)6 * P * P); wr(dir, "Sa.bin", Sa, (size_t)6 * P); wr(dir, "Qa.bin", Qa, (size_t)6 * P);
    // sanity: K_1 vs K1.bin, K_2 vs K2.bin (K2.bin requires distinct, same as consecutive distinct for length 2)
    snprintf(p, sizeof p, "%s/K1.bin", dir); uint8_t *K1 = rd(p, &s); snprintf(p, sizeof p, "%s/K2.bin", dir); uint8_t *K2 = rd(p, &s);
    long d1 = 0, d2 = 0; for (size_t i = 0; i < (size_t)P * P; i++) { int y = i / P, x = i % P; if (T[phi[y]] == T[phi[x]]) continue; d1 += Ka[i] != K1[i]; d2 += Ka[(size_t)P * P + i] != K2[i]; }
    fprintf(stderr, "mismatch K1 %ld K2 %ld\n", d1, d2);
    return 0;
}
