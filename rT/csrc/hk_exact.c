/* Round T -- exact optimum over ALL orders and ALL single-opening arcs of the 16 closed trails (checker A).
   Held-Karp over (set of trails, last arc).  J = sum cost(arc) + sum over joins (5 - overlap), overlap <= 7 is the
   longest suffix of the previous arc's last 7 letters that is a prefix of the next arc's first 7 letters.
   Word length = 46149 + J.
   Input: options file (trail start dropped cost head7 tail7 per line).  env MAXCOST (default 2) restricts the arcs,
   OVCAP (default 7) caps the overlap (5 = the external tool's join model), PLANT="i j v" forces join value v between
   options i and j (mutation / planted test).
   usage: hk_exact OPTIONS.txt OUT.json */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
#define T 16
#define MAXO 50000
#define INF 100
static int no, otr[MAXO], ost[MAXO], odr[MAXO], oco[MAXO]; static char ohd[MAXO][8], otl[MAXO][8];
static int hid[8][MAXO], tid[8][MAXO], nk[8], koff[9];
static int code(const char *s, int k) { int c = 0; for (int i = 0; i < k; i++) c = c * 8 + (s[i] - '0'); return c; }
int main(int argc, char **argv) {
    int maxcost = getenv("MAXCOST") ? atoi(getenv("MAXCOST")) : 2, ovcap = getenv("OVCAP") ? atoi(getenv("OVCAP")) : 7;
    int pi = -1, pj = -1, pv = 0; if (getenv("PLANT")) sscanf(getenv("PLANT"), "%d %d %d", &pi, &pj, &pv);
    FILE *f = fopen(argv[1], "r"); int t, s, d, c; char h[16], tl[16];
    while (fscanf(f, "%d %d %d %d %15s %15s", &t, &s, &d, &c, h, tl) == 6) { if (c > maxcost) continue; otr[no] = t; ost[no] = s; odr[no] = d; oco[no] = c; memcpy(ohd[no], h, 8); memcpy(otl[no], tl, 8); no++; }
    fclose(f);
    int first[T + 1]; { int q = 0; for (int tt = 0; tt <= T; tt++) { while (q < no && otr[q] < tt) q++; first[tt] = q; } }
    /* ids of head prefixes */
    for (int k = 1; k <= 7; k++) {
        int *map = malloc(sizeof(int) << (3 * k)); for (int i = 0; i < 1 << (3 * k); i++) map[i] = -1; nk[k] = 0;
        for (int o = 0; o < no; o++) { int cd = code(ohd[o], k); if (map[cd] < 0) map[cd] = nk[k]++; hid[k][o] = map[cd]; }
        for (int o = 0; o < no; o++) tid[k][o] = map[code(otl[o] + 7 - k, k)];
        free(map);
    }
    koff[1] = 1; for (int k = 1; k <= 7; k++) koff[k + 1] = koff[k] + nk[k]; int G = koff[8];      /* slot 0 = overall min */
    signed char *F = malloc((size_t)(1 << T) * no); if (!F) { fprintf(stderr, "memory\n"); return 2; }
    memset(F, INF, (size_t)(1 << T) * no);
    for (int o = 0; o < no; o++) F[(size_t)(1 << otr[o]) * no + o] = (signed char)oco[o];
    double t0 = omp_get_wtime();
    for (int p = 1; p < T; p++) {
        #pragma omp parallel
        {
            signed char *g = malloc(G);
            #pragma omp for schedule(dynamic, 8)
            for (int S = 1; S < 1 << T; S++) {
                if (__builtin_popcount(S) != p) continue;
                memset(g, INF, G); const signed char *fs = F + (size_t)S * no;
                for (int o = 0; o < no; o++) { int v = fs[o]; if (v >= INF) continue; if (v < g[0]) g[0] = v;
                    for (int k = 1; k <= ovcap; k++) { int id = tid[k][o]; if (id >= 0 && v < g[koff[k] + id]) g[koff[k] + id] = v; } }
                for (int tt = 0; tt < T; tt++) { if (S >> tt & 1) continue; signed char *fn = F + (size_t)(S | 1 << tt) * no;
                    for (int o = first[tt]; o < first[tt + 1]; o++) { int best = g[0] + 5;
                        for (int k = 1; k <= ovcap; k++) { int v = g[koff[k] + hid[k][o]] + 5 - k; if (v < best) best = v; }
                        if (o == pj && pi >= 0 && (S >> otr[pi] & 1) && fs[pi] < INF && fs[pi] + pv < best) best = fs[pi] + pv;
                        best += oco[o]; if (best > INF) best = INF;
                        #pragma omp critical(w)
                        { if (best < fn[o]) fn[o] = (signed char)best; }
                    } }
            }
            free(g);
        }
        fprintf(stderr, "layer %d done %.0fs\n", p, omp_get_wtime() - t0);
    }
    const signed char *ff = F + (size_t)((1 << T) - 1) * no; int best = INF, bo = -1; long hist[INF + 1] = {0};
    for (int o = 0; o < no; o++) { if (ff[o] < best) { best = ff[o]; bo = o; } }
    /* number of optimal end arcs and a witness by backtracking */
    int ord[T], S = (1 << T) - 1, o = bo, v = best;
    for (int p = T - 1; p >= 0; p--) { ord[p] = o; if (p == 0) break; int S2 = S & ~(1 << otr[o]); const signed char *fs = F + (size_t)S2 * no; int found = -1;
        for (int q = 0; q < no && found < 0; q++) { if (fs[q] >= INF) continue; int k = ovcap; while (k > 0 && memcmp(otl[q] + 7 - k, ohd[o], k)) k--;
            int j = 5 - k; if (q == pi && o == pj && pv < j) j = pv; if (fs[q] + j + oco[o] == v) { found = q; v = fs[q]; } }
        if (found < 0) { fprintf(stderr, "backtrack failed\n"); return 3; } S = S2; o = found; }
    for (int q = 0; q < no; q++) if (ff[q] < INF) hist[(int)ff[q]]++;
    FILE *fo = fopen(argv[2], "w");
    fprintf(fo, "{\"checker\": \"hk_exact (forward Held-Karp, C)\", \"options\": %d, \"max_arc_cost\": %d, \"overlap_cap\": %d, \"plant\": [%d, %d, %d],\n \"optimal_J\": %d, \"optimal_length\": %d,\n \"witness\": [", no, maxcost, ovcap, pi, pj, pv, best, 46149 + best);
    for (int p = 0; p < T; p++) fprintf(fo, "%s[%d, %d, %d]", p ? ", " : "", otr[ord[p]], ost[ord[p]], 3 - oco[ord[p]]);
    fprintf(fo, "],\n \"end_arcs_by_J\": {"); int fst = 1; for (int q = 0; q <= best + 3 && q < INF; q++) if (hist[q]) { fprintf(fo, "%s\"%d\": %ld", fst ? "" : ", ", q, hist[q]); fst = 0; }
    unsigned long long hsh = 1469598103934665603ULL; for (size_t i = 0; i < (size_t)(1 << T) * no; i++) { hsh ^= (unsigned char)F[i]; hsh *= 1099511628211ULL; }
    fprintf(fo, "},\n \"table_fnv1a64\": \"%016llx\", \"sec\": %.1f}\n", hsh, omp_get_wtime() - t0); fclose(fo);
    printf("options %d optimal J %d length %d (%.0fs)\n", no, best, 46149 + best, omp_get_wtime() - t0);
    return 0;
}
