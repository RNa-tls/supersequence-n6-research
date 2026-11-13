/* Round V -- exact best path through T <= 20 closed trails (one arc each) with a witness.
   Arcs file: "trail start dropped cost head7 tail7" per line (sorted by trail).  J = sum cost + sum (5 - overlap).
   Forward Held-Karp with the full table kept for backtracking.  Optional THRESH: also count the end arcs with J <= THRESH.
   usage: path_witness ARCS.txt OUT.json */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define MAXT 20
#define MAXO 60000
#define INF 100
static int T, no, otr[MAXO], ost[MAXO], oco[MAXO]; static char ohd[MAXO][8], otl[MAXO][8];
static int hid[8][MAXO], tid[8][MAXO], nk[8], koff[9], G, first[MAXT + 1];
static int code(const char *s, int k) { int c = 0; for (int i = 0; i < k; i++) c = c * 8 + (s[i] - '0'); return c; }
static int ovl(int a, int b) { int k = 7; while (k > 0 && memcmp(otl[a] + 7 - k, ohd[b], k)) k--; return k; }
int main(int argc, char **argv) {
    FILE *f = fopen(argv[1], "r"); int t, s, d, c; char h[16], tl[16];
    while (fscanf(f, "%d %d %d %d %15s %15s", &t, &s, &d, &c, h, tl) == 6) { otr[no] = t; ost[no] = s; oco[no] = c; memcpy(ohd[no], h, 8); memcpy(otl[no], tl, 8); no++; if (t + 1 > T) T = t + 1; }
    fclose(f);
    { int q = 0; for (int tt = 0; tt <= T; tt++) { while (q < no && otr[q] < tt) q++; first[tt] = q; } }
    for (int k = 1; k <= 7; k++) {
        int *map = malloc(sizeof(int) << (3 * k)); for (int i = 0; i < 1 << (3 * k); i++) map[i] = -1; nk[k] = 0;
        for (int o = 0; o < no; o++) { int cd = code(ohd[o], k); if (map[cd] < 0) map[cd] = nk[k]++; hid[k][o] = map[cd]; }
        for (int o = 0; o < no; o++) tid[k][o] = map[code(otl[o] + 7 - k, k)];
        free(map);
    }
    koff[1] = 1; for (int k = 1; k <= 7; k++) koff[k + 1] = koff[k] + nk[k]; G = koff[8];
    size_t NS = (size_t)1 << T; signed char *F = malloc(NS * no), *g = malloc(G); memset(F, INF, NS * no);
    for (int o = 0; o < no; o++) F[((size_t)1 << otr[o]) * no + o] = (signed char)oco[o];
    for (size_t S = 1; S < NS; S++) { const signed char *fs = F + S * no; memset(g, INF, G); int m = INF;
        for (int o = 0; o < no; o++) { int v = fs[o]; if (v >= INF) continue; if (v < m) m = v; for (int k = 1; k <= 7; k++) { int id = tid[k][o]; if (id >= 0 && v < g[koff[k] + id]) g[koff[k] + id] = v; } }
        g[0] = (signed char)m;
        for (int tt = 0; tt < T; tt++) { if (S >> tt & 1) continue; signed char *fn = F + (S | (size_t)1 << tt) * no;
            for (int o = first[tt]; o < first[tt + 1]; o++) { int best = g[0] + 5; for (int k = 1; k <= 7; k++) { int v = g[koff[k] + hid[k][o]] + 5 - k; if (v < best) best = v; }
                best += oco[o]; if (best < fn[o]) fn[o] = (signed char)best; } } }
    const signed char *ff = F + (NS - 1) * no; int best = INF, bo = -1, nopt = 0;
    for (int o = 0; o < no; o++) if (ff[o] < best) { best = ff[o]; bo = o; }
    for (int o = 0; o < no; o++) if (ff[o] == best) nopt++;
    int ord[MAXT], jo[MAXT]; size_t S = NS - 1; int o = bo, v = best;
    for (int p = T - 1; p >= 0; p--) { ord[p] = o; jo[p] = 0; if (p == 0) break; size_t S2 = S & ~((size_t)1 << otr[o]); const signed char *fs = F + S2 * no; int found = -1;
        for (int q = 0; q < no && found < 0; q++) { if (fs[q] >= INF) continue; int j = 5 - ovl(q, o); if (fs[q] + j + oco[o] == v) { found = q; jo[p] = j; v = fs[q]; } }
        if (found < 0) { fprintf(stderr, "backtrack failed\n"); return 3; } S = S2; o = found; }
    FILE *fo = fopen(argv[2], "w");
    fprintf(fo, "{\"trails\": %d, \"arcs\": %d, \"optimal_J\": %d, \"optimal_end_arcs\": %d,\n \"witness\": [", T, no, best, nopt);
    for (int p = 0; p < T; p++) fprintf(fo, "%s{\"trail\": %d, \"start\": %d, \"cost\": %d, \"join\": %d}", p ? ", " : "", otr[ord[p]], ost[ord[p]], oco[ord[p]], jo[p]);
    fprintf(fo, "]}\n"); fclose(fo); printf("trails %d arcs %d optimal J %d (%d optimal end arcs)\n", T, no, best, nopt);
    return 0;
}
