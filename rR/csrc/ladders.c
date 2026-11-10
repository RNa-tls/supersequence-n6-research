// Round S -- the ladder lemma (Lemma S1.4) of the Monge reduction, exhaustive check.
// In the reduction of a wrap-free route to a bracket tree the cuts are deleted one at a time; a deletion of v with cover
// neighbours l (before) and r (after) is UNSAFE when the new junction pred(l) -> r would have weight < 3, i.e. when
// (l, r) is a TIGHT PAIR of one trail version:
//     singleton pair  l = succ(r)                (the piece between the two cuts is the single run r; weight 1), or
//     wrap pair       l = succ(D_6), r = D_0     (D a full chain; weight 2).
// If every deletable cut is unsafe, the deletable cuts between two kept cuts d_0, d_{m+1} form a LADDER
//     d_0, d_1, ..., d_m, d_{m+1}:  m even, the even-indexed cuts in one trail T, the odd-indexed in another trail S,
//     (d_{i-1}, d_{i+1}) tight for i = 1..m,
// and the whole ladder is deleted in one step: the junctions pred(d_i) -> d_{i+1} (i = 0..m) are replaced by
// pred(d_0) -> d_{m+1} and the m natural links of d_1..d_m.  Its weight change is
//     Delta = w(pred d_0, d_{m+1}) + sum_{i=1..m} c(d_i) - sum_{i=0..m} w(pred d_i, d_{i+1}).
// All m + 1 junctions join different trails, so w >= c(target) + 1 and Delta <= 8 - (m + 1) - c(d_{m+1}) < 0 for m >= 6.
// This program checks Delta <= 0 for ALL ladders with m = 2 and m = 4 (and m = 6 as a sanity check) over all ordered
// pairs of different trails and all versions: T side = chain of tight pairs t_0 > t_1 > ... > t_{m/2}, S side likewise.
// usage: ladders DIR(runs.bin) OUT.json
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#define NTR 30
static int mrun[NTR][2]; static uint8_t *runp[NTR][2];
static int wgt(const uint8_t *x, const uint8_t *y) { for (int s = 1; s < 8; s++) { int ok = 1; for (int i = 0; s + i < 8; i++) if (x[s + i] != y[i]) { ok = 0; break; } if (ok) return s; } return 8; }
static int N, *pred, *succ, *tr, *ver, *cut, *wrapR;   // wrapR[l] = D_0 if l = succ(D_6) for a full chain D, else -1
static int8_t *W;
#define WW(a, b) ((int)W[(size_t)(a) * N + (b)])
typedef struct { int c[4]; int k; int types; } Side;   // c[0..k]: the chain of cuts; types: bit j = 1 if step j is a wrap
static Side *sides[4]; static long nsides[4];
static void gen(int k) {    // all chains of k tight steps
    long cap = (long)N * (1 << k) + 16; sides[k] = malloc(sizeof(Side) * cap); long n = 0;
    for (int t0 = 0; t0 < N; t0++) for (int mask = 0; mask < (1 << k); mask++) { Side s; s.c[0] = t0; s.k = k; s.types = mask; int ok = 1;
        for (int j = 0; j < k && ok; j++) { int l = s.c[j]; int r = (mask >> j & 1) ? wrapR[l] : pred[l]; if (r < 0) ok = 0; s.c[j + 1] = r; }
        if (!ok) continue;
        for (int i = 0; i <= k && ok; i++) for (int j = i + 1; j <= k; j++) if (s.c[i] == s.c[j]) ok = 0;
        if (ok) sides[k][n++] = s; }
    nsides[k] = n;
}
int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: ladders DIR OUT.json\n"); return 1; }
    char p[2048]; snprintf(p, sizeof p, "%s/runs.bin", argv[1]); FILE *f = fopen(p, "rb"); if (!f) return 2;
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int32_t m; if (fread(&m, 4, 1, f) != 1) return 2; mrun[t][v] = m; runp[t][v] = malloc(8 * m); if (fread(runp[t][v], 1, 8 * m, f) != (size_t)(8 * m)) return 2; }
    fclose(f);
    N = 0; for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) N += mrun[t][v];
    uint8_t (*first)[8] = malloc((size_t)8 * N), (*last)[8] = malloc((size_t)8 * N); pred = malloc(sizeof(int) * N); succ = malloc(sizeof(int) * N); tr = malloc(sizeof(int) * N); ver = malloc(sizeof(int) * N); cut = malloc(sizeof(int) * N); wrapR = malloc(sizeof(int) * N);
    { int o = 0; for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int m = mrun[t][v], base = o;
        for (int k = 0; k < m; k++, o++) { memcpy(first[o], runp[t][v] + 8 * k, 8); last[o][0] = first[o][7]; for (int i = 1; i < 8; i++) last[o][i] = first[o][i - 1]; pred[o] = base + (k + m - 1) % m; succ[o] = base + (k + 1) % m; tr[o] = t; ver[o] = v; } } }
    W = malloc((size_t)N * N);
    #pragma omp parallel for schedule(dynamic, 64)
    for (int a = 0; a < N; a++) for (int b = 0; b < N; b++) W[(size_t)a * N + b] = a == b ? 8 : (int8_t)wgt(last[a], first[b]);
    long nwrap = 0;
    for (int u = 0; u < N; u++) { cut[u] = WW(pred[u], u); wrapR[u] = -1; if (cut[u] != 2 && cut[u] != 3) return 3; }
    // full chains: a chain start q (cut 3) whose chain q, succ q, ... has 7 runs of w2 links and w(last, q) = 2
    for (int q = 0; q < N; q++) { if (cut[q] != 3) continue; int x = q, len = 1; while (cut[succ[x]] == 2 && len < 9) { x = succ[x]; len++; }
        if (len == 7 && WW(x, q) == 2) { wrapR[succ[x]] = q; nwrap++; } }
    for (int k = 1; k <= 3; k++) gen(k);
    FILE *o = fopen(argv[2], "w"); fprintf(o, "{\"runs\": %d, \"full_chains\": %ld,\n", N, nwrap);
    int allok = 1;
    for (int k = 1; k <= 3; k++) { int m = 2 * k; long nT = nsides[k]; const Side *S = sides[k];
        int nty = 1 << k; long cnt[8][8]; int mx[8][8]; long zero[8][8]; memset(cnt, 0, sizeof cnt); memset(zero, 0, sizeof zero); for (int i = 0; i < 8; i++) for (int j = 0; j < 8; j++) mx[i][j] = -100;
        #pragma omp parallel
        { long lc[8][8]; int lm[8][8]; long lz[8][8]; memset(lc, 0, sizeof lc); memset(lz, 0, sizeof lz); for (int i = 0; i < 8; i++) for (int j = 0; j < 8; j++) lm[i][j] = -100;
          #pragma omp for schedule(dynamic, 64)
          for (long i = 0; i < nT; i++) { const Side *T = &S[i]; int tt = tr[T->c[0]];
            // T side: kept t_0 = T->c[0], deleted t_1..t_k.   S side: deleted s_1..s_k = U->c[0..k-1], kept s_{k+1} = U->c[k]
            for (long j = 0; j < nT; j++) { const Side *U = &S[j]; if (tr[U->c[0]] == tt) continue;
                int d = WW(pred[T->c[0]], U->c[k]);
                for (int q = 0; q < k; q++) { d += cut[U->c[q]] + cut[T->c[q + 1]];
                    d -= WW(pred[T->c[q]], U->c[q]);          // pred(t_q) -> s_{q+1}
                    d -= WW(pred[U->c[q]], T->c[q + 1]); }    // pred(s_{q+1}) -> t_{q+1}
                d -= WW(pred[T->c[k]], U->c[k]);              // pred(t_k) -> s_{k+1}
                int a = T->types, b = U->types; lc[a][b]++; if (d > lm[a][b]) lm[a][b] = d; if (d == 0) lz[a][b]++; } }
          #pragma omp critical
          for (int a = 0; a < nty; a++) for (int b = 0; b < nty; b++) { cnt[a][b] += lc[a][b]; zero[a][b] += lz[a][b]; if (lm[a][b] > mx[a][b]) mx[a][b] = lm[a][b]; } }
        long tot = 0; int worst = -100; long z = 0;
        for (int a = 0; a < nty; a++) for (int b = 0; b < nty; b++) { tot += cnt[a][b]; z += zero[a][b]; if (cnt[a][b] && mx[a][b] > worst) worst = mx[a][b]; }
        fprintf(o, " \"m%d\": {\"sides\": %ld, \"ladders\": %ld, \"max_delta\": %d, \"delta_zero\": %ld, \"by_step_types_T_S\": [", m, nT, tot, worst, z);
        int firstp = 1;
        for (int a = 0; a < nty; a++) for (int b = 0; b < nty; b++) { if (!cnt[a][b]) continue; char ta[8], tb[8]; for (int q = 0; q < k; q++) { ta[q] = (a >> q & 1) ? 'w' : 's'; tb[q] = (b >> q & 1) ? 'w' : 's'; } ta[k] = tb[k] = 0;
            fprintf(o, "%s[\"%s\", \"%s\", %ld, %d]", firstp ? "" : ", ", ta, tb, cnt[a][b], mx[a][b]); firstp = 0; }
        fprintf(o, "]},\n");
        printf("m = %d: sides %ld, ladders %ld, max Delta %d, Delta = 0: %ld\n", m, nT, tot, worst, z);
        if (worst > 0) allok = 0; }
    fprintf(o, " \"ladder_lemma_holds\": %s}\n", allok ? "true" : "false"); fclose(o);
    return !allok;
}
