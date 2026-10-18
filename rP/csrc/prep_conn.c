// Round P -- connector tables for the phi-subset DP (A trails eliminated).
// Input dir: E.bin (int8 N*N), trail.bin (int32 N), cut.bin (int32 N); A trail ids fixed below.
// Output (int8/uint8, phi options in the order of increasing global option index):
//   K1[y][x] = min over A, o_A of E[y][o_A] + E[o_A][x]                 (one-A connector)
//   K2[y][x] = min over A != A', o_A, o_A' of E[y][o_A]+E[o_A][o_A']+E[o_A'][x]   (two-A connector)
//   PRE[y]   = min over A,o_A of E[y][o_A] + min_{o' in another A} E[o_A][o']
//   SUF[x]   = min over A,o_A of min_{o' in another A} E[o'][o_A] + E[o_A][x]
//   S1[x], S2[x], S3[x]: start connectors (start cost [cut=2] of the first option), Q1[y], Q2[y]: end connectors
//   S3 = PRES + SUF[x] where PRES = min over A,o_A of [cut(o_A)=2] + min_{o' in another A} E[o_A][o']
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
    int Aid[6] = {1, 8, 15, 22, 28, 29}; int alo[6], ahi[6];
    for (int a = 0; a < 6; a++) { alo[a] = -1; for (int o = 0; o < N; o++) if (T[o] == Aid[a]) { if (alo[a] < 0) alo[a] = o; ahi[a] = o + 1; } }
    int isA[30] = {0}; for (int a = 0; a < 6; a++) isA[Aid[a]] = 1;
    int P = 0; int *phi = malloc(sizeof(int) * N); for (int o = 0; o < N; o++) if (!isA[T[o]]) phi[P++] = o;
    fprintf(stderr, "N=%d P=%d\n", N, P);
    #define EE(i, j) ((int)E[(size_t)(i) * N + (j)])
    uint8_t *K1 = malloc((size_t)P * P), *K2 = malloc((size_t)P * P); memset(K1, 120, (size_t)P * P); memset(K2, 120, (size_t)P * P);
    int na = ahi[0] - alo[0];
    // outA[a][o_A] = min over options of other A's of E[o_A][o'] ; inA[a][o_A] = min over other A's E[o'][o_A]
    int *outA = malloc(sizeof(int) * N), *inA = malloc(sizeof(int) * N);
    for (int a = 0; a < 6; a++) for (int o = alo[a]; o < ahi[a]; o++) {
        int bo = 99, bi = 99;
        for (int b = 0; b < 6; b++) if (b != a) for (int q = alo[b]; q < ahi[b]; q++) { int v = EE(o, q); if (v < bo) bo = v; v = EE(q, o); if (v < bi) bi = v; }
        outA[o] = bo; inA[o] = bi; }
    // K1
    #pragma omp parallel for schedule(dynamic, 8)
    for (int y = 0; y < P; y++) {
        uint8_t row[4096]; memset(row, 120, P);
        for (int a = 0; a < 6; a++) for (int o = alo[a]; o < ahi[a]; o++) {
            int iy = EE(phi[y], o); if (iy >= 6) continue;
            const int8_t *er = E + (size_t)o * N;
            for (int x = 0; x < P; x++) { int v = iy + er[phi[x]]; if (v < row[x]) row[x] = v; } }
        memcpy(K1 + (size_t)y * P, row, P); }
    fprintf(stderr, "K1 done\n");
    // K2: M1[y][o_A'] = min over A != A', o_A of E[y][o_A] + E[o_A][o_A'] ; then K2[y][x] = min over A', o_A' of M1 + E[o_A'][x]
    #pragma omp parallel for schedule(dynamic, 4)
    for (int y = 0; y < P; y++) {
        uint8_t row[4096]; memset(row, 120, P);
        int *M1 = malloc(sizeof(int) * na);
        for (int b = 0; b < 6; b++) {
            for (int j = 0; j < na; j++) M1[j] = 120;
            for (int a = 0; a < 6; a++) { if (a == b) continue;
                for (int o = alo[a]; o < ahi[a]; o++) { int iy = EE(phi[y], o); if (iy >= 5) continue;
                    const int8_t *er = E + (size_t)o * N + alo[b];
                    for (int j = 0; j < na; j++) { int v = iy + er[j]; if (v < M1[j]) M1[j] = v; } } }
            for (int j = 0; j < na; j++) { int m = M1[j]; if (m >= 6) continue; const int8_t *er = E + (size_t)(alo[b] + j) * N;
                for (int x = 0; x < P; x++) { int v = m + er[phi[x]]; if (v < row[x]) row[x] = v; } } }
        free(M1);
        memcpy(K2 + (size_t)y * P, row, P); }
    fprintf(stderr, "K2 done\n");
    uint8_t *PRE = malloc(P), *SUF = malloc(P), *S1 = malloc(P), *S2 = malloc(P), *S3 = malloc(P), *Q1 = malloc(P), *Q2 = malloc(P);
    int PRES = 99;
    for (int a = 0; a < 6; a++) for (int o = alo[a]; o < ahi[a]; o++) { int v = (cut[o] == 2) + outA[o]; if (v < PRES) PRES = v; }
    #pragma omp parallel for
    for (int y = 0; y < P; y++) {
        int pre = 99, suf = 99, s1 = 99, q1 = 99;
        for (int a = 0; a < 6; a++) for (int o = alo[a]; o < ahi[a]; o++) {
            int v = EE(phi[y], o) + outA[o]; if (v < pre) pre = v;
            v = inA[o] + EE(o, phi[y]); if (v < suf) suf = v;
            v = (cut[o] == 2) + EE(o, phi[y]); if (v < s1) s1 = v;
            v = EE(phi[y], o); if (v < q1) q1 = v; }
        PRE[y] = pre; SUF[y] = suf; S1[y] = s1; Q1[y] = q1; }
    // S2[x] = min over A != A' of [cut(o_A)=2] + E[o_A][o_A'] + E[o_A'][x] ; Q2[y] = min over A != A' of E[y][o_A] + E[o_A][o_A']
    int *st2 = malloc(sizeof(int) * N); // st2[o_A'] = min over other A, o_A of [cut=2] + E[o_A][o_A']
    for (int b = 0; b < 6; b++) for (int q = alo[b]; q < ahi[b]; q++) { int m = 99;
        for (int a = 0; a < 6; a++) if (a != b) for (int o = alo[a]; o < ahi[a]; o++) { int v = (cut[o] == 2) + EE(o, q); if (v < m) m = v; }
        st2[q] = m; }
    #pragma omp parallel for
    for (int x = 0; x < P; x++) { int m = 99, mq = 99;
        for (int b = 0; b < 6; b++) for (int q = alo[b]; q < ahi[b]; q++) { int v = st2[q] + EE(q, phi[x]); if (v < m) m = v; }
        // Q2: y=x as the last phi: E[y][o_A] + E[o_A][o_A'] minimal over A != A'
        for (int a = 0; a < 6; a++) for (int o = alo[a]; o < ahi[a]; o++) { int v = EE(phi[x], o) + outA[o]; if (v < mq) mq = v; }
        S2[x] = m; Q2[x] = mq; S3[x] = PRES + SUF[x]; }
    wr(dir, "K1.bin", K1, (size_t)P * P); wr(dir, "K2.bin", K2, (size_t)P * P);
    wr(dir, "PRE.bin", PRE, P); wr(dir, "SUF.bin", SUF, P); wr(dir, "S1.bin", S1, P); wr(dir, "S2.bin", S2, P); wr(dir, "S3.bin", S3, P);
    wr(dir, "Q1.bin", Q1, P); wr(dir, "Q2.bin", Q2, P);
    uint8_t *Ed = malloc((size_t)P * P);
    for (int y = 0; y < P; y++) for (int x = 0; x < P; x++) { int v = (T[phi[y]] == T[phi[x]]) ? 120 : EE(phi[y], phi[x]); Ed[(size_t)y * P + x] = v; }
    wr(dir, "Ed.bin", Ed, (size_t)P * P);
    fprintf(stderr, "PRES=%d done\n", PRES);
    return 0;
}
