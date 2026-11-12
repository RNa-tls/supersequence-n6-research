/* Round U -- bracket-tree lower bound for a family of T <= 20 closed trails given by its run-level arcs.
   Same tables as rT/csrc/cyc_tree.c (PATH[M], CYC[U]) for any T, followed by the partition DP:
       LB = min over nonempty M of PATH[M] + g[all - M],  g[S] = min over partitions of S of sum c[B],
       c[B] = min over t not in B of CYC[B + {t}].
   Arcs may have negative cost (a cut at a skip link of weight 4 costs -1).  Trails should be numbered with the
   smallest trail first (the anchor of a closed tour is its lowest trail).
   usage: wrap_tree OPTIONS.txt   -> one JSON line on stdout */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
#define MAXT 20
#define MAXO 9000
#define INF 100
static int T, no, otr[MAXO], oco[MAXO]; static char ohd[MAXO][8], otl[MAXO][8];
static int hid[8][MAXO], tid[8][MAXO], nk[8], koff[9], G, first[MAXT + 1];
static int code(const char *s, int k) { int c = 0; for (int i = 0; i < k; i++) c = c * 8 + (s[i] - '0'); return c; }
static int ovl(int a, int b) { int k = 7; while (k > 0 && memcmp(otl[a] + 7 - k, ohd[b], k)) k--; return k; }
int main(int argc, char **argv) {
    FILE *f = fopen(argv[1], "r"); int t, s, d, c; char h[16], tl[16]; T = 0;
    while (fscanf(f, "%d %d %d %d %15s %15s", &t, &s, &d, &c, h, tl) == 6) { otr[no] = t; oco[no] = c; memcpy(ohd[no], h, 8); memcpy(otl[no], tl, 8); no++; if (t + 1 > T) T = t + 1; }
    fclose(f);
    { int q = 0; for (int tt = 0; tt <= T; tt++) { while (q < no && otr[q] < tt) q++; first[tt] = q; } }
    for (int k = 1; k <= 7; k++) {
        int *map = malloc(sizeof(int) << (3 * k)); for (int i = 0; i < 1 << (3 * k); i++) map[i] = -1; nk[k] = 0;
        for (int o = 0; o < no; o++) { int cd = code(ohd[o], k); if (map[cd] < 0) map[cd] = nk[k]++; hid[k][o] = map[cd]; }
        for (int o = 0; o < no; o++) tid[k][o] = map[code(otl[o] + 7 - k, k)];
        free(map);
    }
    koff[1] = 1; for (int k = 1; k <= 7; k++) koff[k + 1] = koff[k] + nk[k]; G = koff[8];
    int NS = 1 << T; signed char *PATH = malloc(NS), *CYC = malloc(NS); memset(PATH, INF, NS); memset(CYC, INF, NS);
    double t0 = omp_get_wtime();
    { signed char *F = malloc((size_t)NS * no); memset(F, INF, (size_t)NS * no); signed char *g = malloc(G);
      for (int o = 0; o < no; o++) F[(size_t)(1 << otr[o]) * no + o] = (signed char)oco[o];
      for (int S = 1; S < NS; S++) { const signed char *fs = F + (size_t)S * no; memset(g, INF, G); int m = INF;
        for (int o = 0; o < no; o++) { int v = fs[o]; if (v >= INF) continue; if (v < m) m = v; for (int k = 1; k <= 7; k++) { int id = tid[k][o]; if (id >= 0 && v < g[koff[k] + id]) g[koff[k] + id] = v; } }
        PATH[S] = (signed char)m; g[0] = (signed char)m;
        for (int tt = 0; tt < T; tt++) { if (S >> tt & 1) continue; signed char *fn = F + (size_t)(S | 1 << tt) * no;
            for (int o = first[tt]; o < first[tt + 1]; o++) { int best = g[0] + 5; for (int k = 1; k <= 7; k++) { int v = g[koff[k] + hid[k][o]] + 5 - k; if (v < best) best = v; }
                best += oco[o]; if (best < fn[o]) fn[o] = (signed char)best; } } }
      free(F); free(g); }
    for (int i = 0; i < T - 1; i++) {
        int hb = T - 1 - i, nS = 1 << hb, lo = first[i + 1], nh = no - lo;
        #pragma omp parallel
        {
            signed char *F = malloc((size_t)nS * nh), *g = malloc(G), *best = malloc(nS);
            #pragma omp for schedule(dynamic, 1)
            for (int os = first[i]; os < first[i + 1]; os++) {
                memset(F, INF, (size_t)nS * nh); memset(best, INF, nS);
                for (int S = 0; S < nS; S++) { memset(g, INF, G);
                    if (S == 0) { g[0] = (signed char)oco[os]; for (int k = 1; k <= 7; k++) { int id = tid[k][os]; if (id >= 0) g[koff[k] + id] = (signed char)oco[os]; } }
                    else { const signed char *fs = F + (size_t)S * nh; int m = INF, cl = INF;
                        for (int o = 0; o < nh; o++) { int v = fs[o]; if (v >= INF) continue; if (v < m) m = v; int c2 = v + 5 - ovl(lo + o, os); if (c2 < cl) cl = c2;
                            for (int k = 1; k <= 7; k++) { int id = tid[k][lo + o]; if (id >= 0 && v < g[koff[k] + id]) g[koff[k] + id] = v; } }
                        g[0] = (signed char)m; best[S] = (signed char)(cl > INF ? INF : cl); }
                    for (int b = 0; b < hb; b++) { if (S >> b & 1) continue; int tt = i + 1 + b; signed char *fn = F + (size_t)(S | 1 << b) * nh;
                        for (int o = first[tt]; o < first[tt + 1]; o++) { int bs = g[0] + 5; for (int k = 1; k <= 7; k++) { int v = g[koff[k] + hid[k][o]] + 5 - k; if (v < bs) bs = v; }
                            bs += oco[o]; if (bs < fn[o - lo]) fn[o - lo] = (signed char)(bs > INF ? INF : bs); } } }
                #pragma omp critical
                for (int S = 1; S < nS; S++) { int U = (1 << i) | (S << (i + 1)); if (best[S] < CYC[U]) CYC[U] = best[S]; }
            }
            free(F); free(g); free(best);
        }
    }
    /* partition DP */
    int *cb = malloc(sizeof(int) * NS), *g = malloc(sizeof(int) * NS);
    for (int B = 0; B < NS; B++) { int m = 1000; for (int tt = 0; tt < T; tt++) if (!(B >> tt & 1)) { int v = CYC[B | 1 << tt]; if (v < INF && v < m) m = v; } cb[B] = m; }
    g[0] = 0;
    for (int S = 1; S < NS; S++) { int low = S & -S, rest = S ^ low, sub = rest, best = 100000;
        for (;;) { int B = low | sub, v = cb[B] + g[S ^ B]; if (v < best) best = v; if (!sub) break; sub = (sub - 1) & rest; }
        g[S] = best; }
    int LB = 100000, LBb = 100000, mincyc = INF;
    for (int M = 1; M < NS; M++) { if (PATH[M] >= INF) continue; int v = PATH[M] + g[(NS - 1) ^ M]; if (v < LB) LB = v; if (M != NS - 1 && v < LBb) LBb = v; }
    for (int U = 1; U < NS; U++) if (CYC[U] < mincyc) mincyc = CYC[U];
    unsigned long long hsh = 1469598103934665603ULL; for (int i = 0; i < NS; i++) { hsh ^= (unsigned char)PATH[i]; hsh *= 1099511628211ULL; hsh ^= (unsigned char)CYC[i]; hsh *= 1099511628211ULL; }
    printf("{\"trails\": %d, \"arcs\": %d, \"PATH_all\": %d, \"least_closed_tour\": %d, \"tree_bound\": %d, \"tree_bound_with_a_bracket\": %d, \"tables_fnv1a64\": \"%016llx\", \"sec\": %.1f}\n",
           T, no, PATH[NS - 1], mincyc, LB, LBb, hsh, omp_get_wtime() - t0);
    if (argc > 2) { FILE *fo = fopen(argv[2], "wb"); fwrite(PATH, 1, NS, fo); fwrite(CYC, 1, NS, fo); fclose(fo); }
    return 0;
}
