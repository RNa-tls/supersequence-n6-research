/* Round T -- tables for the bracket-tree lower bound on the public 16-trail selection (run-level arcs: cost <= MAXCOST).
   PATH[M]  = least J-part of a path through the trails of M, one arc each:  sum cost(arc) + sum over joins (5 - ov)
   CYC[U]   = least cost of a CLOSED tour through the trails of U, one arc each: sum cost(arc) + sum over |U| cyclic joins
   A route in which trail t hosts a bracket with member set B (t cut a second time, the members inserted there) has
       J = (J-part of the rest, t taken as one arc) + CYC[B + {t}]      (cuts and joins are each counted once)
   so  J >= PATH[M] + sum over brackets CYC[B_i + {t_i}]  for every bracket tree (src/tree_bound.py does the partition DP).
   usage: cyc_tree OPTIONS.txt OUT.bin   (OUT.bin: int8 PATH[65536], int8 CYC[65536]; 100 = undefined) */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
#define T 16
#define MAXO 50000
#define INF 100
static int no, otr[MAXO], oco[MAXO]; static char ohd[MAXO][8], otl[MAXO][8];
static int hid[8][MAXO], tid[8][MAXO], nk[8], koff[9], G, first[T + 1];
static int code(const char *s, int k) { int c = 0; for (int i = 0; i < k; i++) c = c * 8 + (s[i] - '0'); return c; }
static int ovl(int a, int b) { int k = 7; while (k > 0 && memcmp(otl[a] + 7 - k, ohd[b], k)) k--; return k; }
int main(int argc, char **argv) {
    int maxcost = getenv("MAXCOST") ? atoi(getenv("MAXCOST")) : 1;
    FILE *f = fopen(argv[1], "r"); int t, s, d, c; char h[16], tl[16];
    while (fscanf(f, "%d %d %d %d %15s %15s", &t, &s, &d, &c, h, tl) == 6) { if (c > maxcost) continue; otr[no] = t; oco[no] = c; memcpy(ohd[no], h, 8); memcpy(otl[no], tl, 8); no++; }
    fclose(f);
    { int q = 0; for (int tt = 0; tt <= T; tt++) { while (q < no && otr[q] < tt) q++; first[tt] = q; } }
    for (int k = 1; k <= 7; k++) {
        int *map = malloc(sizeof(int) << (3 * k)); for (int i = 0; i < 1 << (3 * k); i++) map[i] = -1; nk[k] = 0;
        for (int o = 0; o < no; o++) { int cd = code(ohd[o], k); if (map[cd] < 0) map[cd] = nk[k]++; hid[k][o] = map[cd]; }
        for (int o = 0; o < no; o++) tid[k][o] = map[code(otl[o] + 7 - k, k)];
        free(map);
    }
    koff[1] = 1; for (int k = 1; k <= 7; k++) koff[k + 1] = koff[k] + nk[k]; G = koff[8];
    static signed char PATH[1 << T], CYC[1 << T]; memset(PATH, INF, sizeof PATH); memset(CYC, INF, sizeof CYC);
    double t0 = omp_get_wtime();
    /* ---- PATH: sequential over sets in numeric order (supersets are larger) */
    { signed char *F = malloc((size_t)(1 << T) * no); memset(F, INF, (size_t)(1 << T) * no); signed char *g = malloc(G);
      for (int o = 0; o < no; o++) F[(size_t)(1 << otr[o]) * no + o] = (signed char)oco[o];
      for (int S = 1; S < 1 << T; S++) { const signed char *fs = F + (size_t)S * no; memset(g, INF, G); int m = INF;
        for (int o = 0; o < no; o++) { int v = fs[o]; if (v >= INF) continue; if (v < m) m = v; for (int k = 1; k <= 7; k++) { int id = tid[k][o]; if (id >= 0 && v < g[koff[k] + id]) g[koff[k] + id] = v; } }
        PATH[S] = (signed char)m; g[0] = (signed char)m;
        for (int tt = 0; tt < T; tt++) { if (S >> tt & 1) continue; signed char *fn = F + (size_t)(S | 1 << tt) * no;
            for (int o = first[tt]; o < first[tt + 1]; o++) { int best = g[0] + 5; for (int k = 1; k <= 7; k++) { int v = g[koff[k] + hid[k][o]] + 5 - k; if (v < best) best = v; }
                best += oco[o]; if (best < fn[o]) fn[o] = (signed char)best; } } }
      free(F); free(g); }
    fprintf(stderr, "PATH done %.0fs, PATH[all] = %d\n", omp_get_wtime() - t0, PATH[(1 << T) - 1]);
    /* ---- CYC: anchor = lowest trail i of U, every start arc of i, DP over sets of trails above i */
    for (int i = 0; i < T - 1; i++) {
        int hb = T - 1 - i, nS = 1 << hb, lo = first[i + 1], nh = no - lo;          /* arcs of higher trails: lo .. no-1 */
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
        fprintf(stderr, "CYC anchor %d done %.0fs\n", i, omp_get_wtime() - t0);
    }
    FILE *fo = fopen(argv[2], "wb"); fwrite(PATH, 1, sizeof PATH, fo); fwrite(CYC, 1, sizeof CYC, fo); fclose(fo);
    printf("options %d (max cost %d): PATH[all] = %d, %.0fs\n", no, maxcost, PATH[(1 << T) - 1], omp_get_wtime() - t0);
    return 0;
}
