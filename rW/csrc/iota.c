/* Round W -- lower bound on the insertion cost of every detached chain at letter level.
   A chain piece p (head H = first 7 letters, tail T = last 7, cut-link weight wi) between a predecessor x (tail X)
   and a successor y (head Y):
       ins = w(X, H) + w(T, Y) - w(X, Y) - wi = 8 - ov(X, H) - ov(T, Y) + ov(X, Y) - wi       (w = 8 - ov)
   at a path end:  ins = 8 - ov(T, Y) - wi  (p first)   or   8 - ov(X, H) - wi  (p last).
   Every head Y with ov(T, Y) = k (k >= 1) begins with s_k = the last k letters of T, so
       ov(X, Y) >= o_k(X) := max { j <= k : last j letters of X = first j letters of s_k },
   hence  max over Y of [ov(T, Y) - ov(X, Y)] <= max(0, max over k in K(p) of [k - o_k(X)]),  K(p) = { k >= 1 : some
   admissible head Y has ov(T, Y) = k }.  This gives a valid lower bound on ins for every admissible pair (X, Y).
   Admissible: tails/heads of pieces of other trails (NEIGH file), whose permutation does not lie in a class of the
   chain (no other piece of a route can end or start in one of the chain's classes).
   iota(c) = min over the pieces of c of the bound (interior, first, last).
   usage: iota PIECES NEIGH CLASSES OUT
     PIECES: "chain s k cost head7 tail7 wi";  NEIGH: "H string7" or "T string7";  CLASSES: "chain c0 .. c6"
     OUT: "chain iota piece_start case"  (case 0 interior, 1 first, 2 last)                                        */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
#define MAXP 40000
#define MAXN 300000
static int np, pc[MAXP], ps[MAXP], pw[MAXP]; static char ph[MAXP][8], pt[MAXP][8];
static int nh, nt; static char hs[MAXN][8], ts[MAXN][8]; static int hcl[MAXN], tcl[MAXN];
static int ncls[2000][7], nch;
static int ov(const char *a, const char *b) { for (int k = 7; k > 0; k--) if (!memcmp(a + 7 - k, b, k)) return k; return 0; }
static int clsof(const char *s, int head) {
    int seen = 0; for (int i = 0; i < 7; i++) seen |= 1 << (s[i] - '0'); int miss = 0; while (seen >> miss & 1) miss++;
    char p[8]; if (head) { memcpy(p, s, 7); p[7] = '0' + miss; } else { p[0] = '0' + miss; memcpy(p + 1, s, 7); }
    int z = 0; while (p[z] != '0') z++; int c = 0; for (int i = 1; i < 8; i++) c = c * 8 + (p[(z + i) % 8] - '0'); return c; }
int main(int argc, char **argv) {
    FILE *f = fopen(argv[1], "r"); int ci, s, k, cost, wi; char h[16], t[16];
    while (fscanf(f, "%d %d %d %d %15s %15s %d", &ci, &s, &k, &cost, h, t, &wi) == 7) { if (np >= MAXP) return 2; pc[np] = ci; ps[np] = s; pw[np] = wi; memcpy(ph[np], h, 8); memcpy(pt[np], t, 8); np++; }
    fclose(f);
    f = fopen(argv[2], "r"); char kind[4], str[16];
    while (fscanf(f, "%3s %15s", kind, str) == 2) { if (nh >= MAXN || nt >= MAXN) return 2;
        if (kind[0] == 'H') { memcpy(hs[nh], str, 8); hcl[nh] = clsof(str, 1); nh++; } else { memcpy(ts[nt], str, 8); tcl[nt] = clsof(str, 0); nt++; } }
    fclose(f);
    f = fopen(argv[3], "r"); int cc[7];
    while (fscanf(f, "%d %d %d %d %d %d %d %d", &ci, &cc[0], &cc[1], &cc[2], &cc[3], &cc[4], &cc[5], &cc[6]) == 8) { memcpy(ncls[ci], cc, sizeof cc); if (ci + 1 > nch) nch = ci + 1; }
    fclose(f);
    int *best = malloc(sizeof(int) * nch), *bestp = malloc(sizeof(int) * nch), *bestk = malloc(sizeof(int) * nch);
    for (int c = 0; c < nch; c++) { best[c] = 1000; bestp[c] = -1; bestk[c] = -1; }
    #pragma omp parallel for schedule(dynamic, 8)
    for (int q = 0; q < np; q++) {
        int c = pc[q]; const int *cl = ncls[c]; int present[8] = {0}, maxovT = -1;
        for (int j = 0; j < nh; j++) { int bad = 0; for (int i = 0; i < 7; i++) if (hcl[j] == cl[i]) bad = 1; if (bad) continue;
            int o = ov(pt[q], hs[j]); present[o] = 1; if (o > maxovT) maxovT = o; }
        int m = 1000, kindm = -1;
        if (maxovT >= 0) { int v = 8 - maxovT - pw[q]; if (v < m) { m = v; kindm = 1; } }
        for (int j = 0; j < nt; j++) { int bad = 0; for (int i = 0; i < 7; i++) if (tcl[j] == cl[i]) bad = 1; if (bad) continue;
            int oxh = ov(ts[j], ph[q]);
            { int v = 8 - oxh - pw[q]; if (v < m) { m = v; kindm = 2; } }
            int g = 0;                                                  /* upper bound on max_Y ov(T,Y) - ov(X,Y) */
            for (int kk = 1; kk <= 7; kk++) { if (!present[kk]) continue;
                const char *sk = pt[q] + 7 - kk; int o = 0;
                for (int jj = kk; jj >= 1; jj--) if (!memcmp(ts[j] + 7 - jj, sk, jj)) { o = jj; break; }
                if (kk - o > g) g = kk - o; }
            int v = 8 - oxh - pw[q] - g; if (v < m) { m = v; kindm = 0; } }
        #pragma omp critical
        { if (m < best[c] || (m == best[c] && ps[q] < bestp[c])) { best[c] = m; bestp[c] = ps[q]; bestk[c] = kindm; } }
    }
    f = fopen(argv[4], "w"); for (int c = 0; c < nch; c++) fprintf(f, "%d %d %d %d\n", c, best[c], bestp[c], bestk[c]); fclose(f);
    return 0;
}
