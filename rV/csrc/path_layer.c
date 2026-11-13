/* Round V -- exact best path through T <= 20 closed trails (one arc each), layered Held-Karp.
   Second implementation of the optimum computed by path_witness.c, written separately: the table is kept only for two
   consecutive layers (subsets of size p and p + 1, ranked in colex order), so T = 18 with ~40,000 arcs fits in ~4 GB.
   Arcs file: "trail start dropped cost head7 tail7" per line, sorted by trail.
   J(path) = sum of arc costs + sum over consecutive arcs (a, b) of (5 - overlap(tail7(a), head7(b))),
   overlap = longest k <= 7 with the last k letters of tail7(a) equal to the first k letters of head7(b).
   Optional THRESH: also count the end arcs whose best path has J <= THRESH.
   usage: path_layer ARCS.txt [THRESH]   -> one JSON line on stdout.  No witness. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define MAXT 20
#define MAXO 60000
#define INF 100
static int T, no, otr[MAXO], oco[MAXO], first[MAXT + 1];
static char ohd[MAXO][8], otl[MAXO][8];
static long long binom[MAXT + 1][MAXT + 1];
static long long rank_of(unsigned m) {           /* colex rank among subsets of the same size */
    long long r = 0; int i = 0;
    for (int e = 0; e < T; e++) if (m >> e & 1) { i++; r += binom[e][i]; }
    return r;
}
int main(int argc, char **argv) {
    FILE *f = fopen(argv[1], "r"); if (!f) return 2;
    int thresh = argc > 2 ? atoi(argv[2]) : -1000;
    int t, s, d, c; char h[16], tl[16];
    while (fscanf(f, "%d %d %d %d %15s %15s", &t, &s, &d, &c, h, tl) == 6) {
        if (no >= MAXO || strlen(h) != 7 || strlen(tl) != 7) { fprintf(stderr, "bad input\n"); return 2; }
        if (no && t < otr[no - 1]) { fprintf(stderr, "arcs not sorted by trail\n"); return 2; }
        otr[no] = t; oco[no] = c; memcpy(ohd[no], h, 8); memcpy(otl[no], tl, 8); no++; if (t + 1 > T) T = t + 1;
    }
    fclose(f);
    if (T > MAXT) return 2;
    for (int i = 0; i <= MAXT; i++) for (int j = 0; j <= MAXT; j++) binom[i][j] = j == 0 ? 1 : (i == 0 ? 0 : binom[i - 1][j - 1] + binom[i - 1][j]);
    { int q = 0; for (int tt = 0; tt <= T; tt++) { while (q < no && otr[q] < tt) q++; first[tt] = q; } }
    /* classes: for k = 1..7, the k-letter strings occurring as a head prefix; a tail suffix gets that class or -1 */
    static int hcl[8][MAXO], tcl[8][MAXO]; int nk[8], off[9];
    for (int k = 1; k <= 7; k++) {
        int sz = 1 << (3 * k); int *map = malloc(sizeof(int) * sz); for (int i = 0; i < sz; i++) map[i] = -1; nk[k] = 0;
        for (int o = 0; o < no; o++) { int cd = 0; for (int i = 0; i < k; i++) cd = cd * 8 + (ohd[o][i] - '0'); if (map[cd] < 0) map[cd] = nk[k]++; hcl[k][o] = map[cd]; }
        for (int o = 0; o < no; o++) { int cd = 0; for (int i = 7 - k; i < 7; i++) cd = cd * 8 + (otl[o][i] - '0'); tcl[k][o] = map[cd]; }
        free(map);
    }
    off[1] = 0; for (int k = 1; k <= 7; k++) off[k + 1] = off[k] + nk[k];
    int G = off[8]; signed char *g = malloc(G);
    /* layer 1 */
    signed char *cur = malloc((size_t)binom[T][1] * no); memset(cur, INF, (size_t)binom[T][1] * no);
    for (int o = 0; o < no; o++) cur[(size_t)rank_of(1u << otr[o]) * no + o] = (signed char)oco[o];
    for (int p = 1; p < T; p++) {
        size_t nn = (size_t)binom[T][p + 1]; signed char *nxt = malloc(nn * no);
        if (!nxt) { fprintf(stderr, "out of memory\n"); return 3; }
        memset(nxt, INF, nn * no);
        unsigned m = (1u << p) - 1; long long r = 0;
        while (m < (1u << T)) {
            const signed char *fs = cur + (size_t)r * no; int mn = INF;
            memset(g, INF, G);
            for (int tt = 0; tt < T; tt++) if (m >> tt & 1) for (int o = first[tt]; o < first[tt + 1]; o++) {
                int v = fs[o]; if (v >= INF) continue; if (v < mn) mn = v;
                for (int k = 1; k <= 7; k++) { int id = tcl[k][o]; if (id >= 0 && v < g[off[k] + id]) g[off[k] + id] = (signed char)v; }
            }
            if (mn < INF) for (int tt = 0; tt < T; tt++) {
                if (m >> tt & 1) continue;
                signed char *fn = nxt + (size_t)rank_of(m | 1u << tt) * no;
                for (int o = first[tt]; o < first[tt + 1]; o++) {
                    int best = mn + 5;
                    for (int k = 1; k <= 7; k++) { int v = g[off[k] + hcl[k][o]] + 5 - k; if (v < best) best = v; }
                    best += oco[o]; if (best < fn[o]) fn[o] = (signed char)best;
                }
            }
            /* next subset of the same size (Gosper) */
            unsigned cbit = m & -m, rr = m + cbit; m = (((rr ^ m) >> 2) / cbit) | rr; r++;
        }
        if (r != binom[T][p]) { fprintf(stderr, "rank mismatch\n"); return 4; }
        free(cur); cur = nxt;
    }
    int best = INF, nopt = 0, nthr = 0;
    for (int o = 0; o < no; o++) if (cur[o] < best) best = cur[o];
    for (int o = 0; o < no; o++) { if (cur[o] == best) nopt++; if (cur[o] <= thresh) nthr++; }
    printf("{\"trails\": %d, \"arcs\": %d, \"classes\": %d, \"optimal_J\": %d, \"optimal_end_arcs\": %d", T, no, G, best, nopt);
    if (thresh > -1000) printf(", \"thresh\": %d, \"end_arcs_le_thresh\": %d", thresh, nthr);
    printf("}\n");
    return 0;
}
