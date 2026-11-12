/* Round U -- checker B for the tables PATH[M] and CYC[U] of rT/csrc/cyc_tree.c (public selection, 16 trails).
   Written separately, with the recursion run BACKWARDS:
     p[S][o] = least cost of a path that starts with arc o and uses exactly the trails of S
     h[S][o] = least cost of: arc o first, then the other trails of S in some order, then the closing join into the
               fixed start arc s of the anchor trail (the lowest trail of the tour)
   Overlap keys are sorted strings with binary search (no 8^k code tables).
   usage: cyc_check_b OPTIONS.txt MAXCOST REFERENCE.bin  -> compares all 2 x 65536 entries, prints JSON */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
#define T 16
#define MAXO 6000
#define INF 100
typedef struct { char s[8]; } key_t8;
static int no, otr[MAXO], oco[MAXO], first[T + 1]; static char hd[MAXO][8], tl[MAXO][8];
static key_t8 *keys[8]; static int nkeys[8], hk[8][MAXO], tk[8][MAXO], off[9], G;
static int curk;
static int cmpk(const void *a, const void *b) { return memcmp(a, b, curk); }
static int find(int k, const char *s) { int lo = 0, hi = nkeys[k] - 1; while (lo <= hi) { int m = (lo + hi) / 2, c = memcmp(keys[k][m].s, s, k); if (!c) return m; if (c < 0) lo = m + 1; else hi = m - 1; } return -1; }
static int ov(const char *tail, const char *head) { for (int k = 7; k > 0; k--) if (!memcmp(tail + 7 - k, head, k)) return k; return 0; }
int main(int argc, char **argv) {
    int maxcost = atoi(argv[2]); FILE *f = fopen(argv[1], "r"); int t, s, d, c; char a[16], b[16];
    while (fscanf(f, "%d %d %d %d %15s %15s", &t, &s, &d, &c, a, b) == 6) { if (c > maxcost) continue; otr[no] = t; oco[no] = c; memcpy(hd[no], a, 8); memcpy(tl[no], b, 8); no++; }
    fclose(f); for (int i = 1; i < no; i++) if (otr[i] < otr[i - 1]) { fprintf(stderr, "arcs must be sorted by trail\n"); return 2; }
    { int q = 0; for (int tt = 0; tt <= T; tt++) { while (q < no && otr[q] < tt) q++; first[tt] = q; } }
    for (int k = 1; k <= 7; k++) {                 /* keys = distinct head prefixes of length k */
        keys[k] = malloc(sizeof(key_t8) * no); for (int o = 0; o < no; o++) { memset(keys[k][o].s, 0, 8); memcpy(keys[k][o].s, hd[o], k); }
        curk = k; qsort(keys[k], no, sizeof(key_t8), cmpk); int m = 0; for (int o = 0; o < no; o++) if (!m || memcmp(keys[k][m - 1].s, keys[k][o].s, k)) keys[k][m++] = keys[k][o];
        nkeys[k] = m; for (int o = 0; o < no; o++) { hk[k][o] = find(k, hd[o]); tk[k][o] = find(k, tl[o] + 7 - k); }
    }
    off[1] = 1; for (int k = 1; k <= 7; k++) off[k + 1] = off[k] + nkeys[k]; G = off[8];
    static signed char PATH[1 << T], CYC[1 << T], REF[2 << T]; memset(PATH, INF, sizeof PATH); memset(CYC, INF, sizeof CYC);
    double t0 = omp_get_wtime();
    /* PATH, backward */
    { signed char *P = malloc((size_t)(1 << T) * no), *m = malloc(G); memset(P, INF, (size_t)(1 << T) * no);
      for (int o = 0; o < no; o++) P[(size_t)(1 << otr[o]) * no + o] = (signed char)oco[o];
      for (int S = 1; S < 1 << T; S++) { const signed char *ps = P + (size_t)S * no; memset(m, INF, G); int best = INF;
        for (int o = 0; o < no; o++) { int v = ps[o]; if (v >= INF) continue; if (v < best) best = v; for (int k = 1; k <= 7; k++) { int id = off[k] + hk[k][o]; if (v < m[id]) m[id] = (signed char)v; } }
        PATH[S] = (signed char)best; m[0] = (signed char)best;
        for (int tt = 0; tt < T; tt++) { if (S >> tt & 1) continue; signed char *pn = P + (size_t)(S | 1 << tt) * no;
            for (int o = first[tt]; o < first[tt + 1]; o++) { int bs = m[0] + 5; for (int k = 1; k <= 7; k++) { int id = tk[k][o]; if (id >= 0) { int v = m[off[k] + id] + 5 - k; if (v < bs) bs = v; } }
                bs += oco[o]; if (bs < pn[o]) pn[o] = (signed char)(bs > INF ? INF : bs); } } }
      free(P); free(m); }
    /* CYC, backward, anchor = lowest trail */
    for (int i = 0; i < T - 1; i++) {
        int hb = T - 1 - i, nS = 1 << hb, lo = first[i + 1], nh = no - lo;
        #pragma omp parallel
        {
            signed char *H = malloc((size_t)nS * nh), *m = malloc(G), *best = malloc(nS);
            #pragma omp for schedule(dynamic, 1)
            for (int s0 = first[i]; s0 < first[i + 1]; s0++) {
                memset(H, INF, (size_t)nS * nh); memset(best, INF, nS);
                for (int b = 0; b < hb; b++) { int tt = i + 1 + b; for (int o = first[tt]; o < first[tt + 1]; o++) H[(size_t)(1 << b) * nh + o - lo] = (signed char)(oco[o] + 5 - ov(tl[o], hd[s0])); }
                for (int S = 1; S < nS; S++) { const signed char *hs = H + (size_t)S * nh; memset(m, INF, G); int mn = INF;
                    for (int o = 0; o < nh; o++) { int v = hs[o]; if (v >= INF) continue; if (v < mn) mn = v; for (int k = 1; k <= 7; k++) { int id = off[k] + hk[k][lo + o]; if (v < m[id]) m[id] = (signed char)v; } }
                    m[0] = (signed char)mn;
                    { int bs = m[0] + 5; for (int k = 1; k <= 7; k++) { int id = tk[k][s0]; if (id >= 0) { int v = m[off[k] + id] + 5 - k; if (v < bs) bs = v; } } bs += oco[s0]; best[S] = (signed char)(bs > INF ? INF : bs); }
                    for (int b = 0; b < hb; b++) { if (S >> b & 1) continue; int tt = i + 1 + b; signed char *hn = H + (size_t)(S | 1 << b) * nh;
                        for (int o = first[tt]; o < first[tt + 1]; o++) { int bs = m[0] + 5; for (int k = 1; k <= 7; k++) { int id = tk[k][o]; if (id >= 0) { int v = m[off[k] + id] + 5 - k; if (v < bs) bs = v; } }
                            bs += oco[o]; if (bs < hn[o - lo]) hn[o - lo] = (signed char)(bs > INF ? INF : bs); } } }
                #pragma omp critical
                for (int S = 1; S < nS; S++) { int U = (1 << i) | (S << (i + 1)); if (best[S] < CYC[U]) CYC[U] = best[S]; }
            }
            free(H); free(m); free(best);
        }
    }
    long dp = -1, dc = -1;
    if (argc > 3) { FILE *fr = fopen(argv[3], "rb"); if (fr && fread(REF, 1, sizeof REF, fr) == sizeof REF) { dp = dc = 0; for (int S = 0; S < 1 << T; S++) { dp += PATH[S] != REF[S]; dc += CYC[S] != REF[(1 << T) + S]; } } if (fr) fclose(fr); }
    printf("{\"checker\": \"cyc_check_b (backward)\", \"arcs\": %d, \"max_cost\": %d, \"PATH_all\": %d, \"CYC_all\": %d, \"PATH_differences\": %ld, \"CYC_differences\": %ld, \"entries_each\": %d, \"sec\": %.1f}\n",
           no, maxcost, PATH[(1 << T) - 1], CYC[(1 << T) - 1], dp, dc, 1 << T, omp_get_wtime() - t0);
    return (dp == 0 && dc == 0) ? 0 : 1;
}
