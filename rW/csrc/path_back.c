/* Round W -- exact best path through T <= 20 closed trails (one arc each), BACKWARD layered Held-Karp.
   Second implementation for the optimum computed by rV/csrc/path_layer.c (forward, tail-suffix classes) and
   rV/csrc/path_witness.c (forward, full table): here Q[S][o] = least J of a path that STARTS with arc o and goes
   through exactly the trails S; Q[S][o] = cost(o) + min over the first arc o' of the rest of (5 - ov(tail o, head o'))
   + Q[S - t(o)][o'], with the rest summarised by head-PREFIX classes (min Q over the arcs whose first k letters are
   a given string).  Only two consecutive layers are kept.
   Output: optimum, number of start arcs attaining it, number of start arcs with value <= THRESH, and the number of
   (subset, arc) states of the last two layers with finite value <= THRESH.
   usage: path_back ARCS.txt [THRESH]  -> one JSON line                                                          */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define MAXT 20
#define MAXO 60000
#define INF 100
typedef signed char i8;
static int T, no, otr[MAXO], oco[MAXO], first[MAXT + 1];
static char ohd[MAXO][8], otl[MAXO][8];
static long long binom[MAXT + 1][MAXT + 1];
static long long crank(unsigned m) { long long r = 0; int i = 0; for (int e = 0; m; e++, m >>= 1) if (m & 1) { i++; r += binom[e][i]; } return r; }
int main(int argc, char **argv) {
    FILE *f = fopen(argv[1], "r"); if (!f) return 2; int thresh = argc > 2 ? atoi(argv[2]) : -1000;
    int t, s, d, c; char h[16], tl[16];
    while (fscanf(f, "%d %d %d %d %15s %15s", &t, &s, &d, &c, h, tl) == 6) {
        if (no >= MAXO || (no && t < otr[no - 1]) || strlen(h) != 7 || strlen(tl) != 7) { fprintf(stderr, "bad input\n"); return 2; }
        otr[no] = t; oco[no] = c; memcpy(ohd[no], h, 8); memcpy(otl[no], tl, 8); no++; if (t + 1 > T) T = t + 1; }
    fclose(f);
    for (int i = 0; i <= MAXT; i++) for (int j = 0; j <= MAXT; j++) binom[i][j] = j == 0 ? 1 : (i == 0 ? 0 : binom[i - 1][j - 1] + binom[i - 1][j]);
    { int q = 0; for (int tt = 0; tt <= T; tt++) { while (q < no && otr[q] < tt) q++; first[tt] = q; } }
    /* head-prefix classes per k; a tail suffix is looked up in the same map */
    static int hp[8][MAXO], ts[8][MAXO]; int off[9]; off[1] = 0;
    for (int k = 1; k <= 7; k++) {
        int sz = 1 << (3 * k), *map = malloc(sizeof(int) * sz), n = 0; for (int i = 0; i < sz; i++) map[i] = -1;
        for (int o = 0; o < no; o++) { int cd = 0; for (int i = 0; i < k; i++) cd = cd * 8 + (ohd[o][i] - '0'); if (map[cd] < 0) map[cd] = n++; hp[k][o] = off[k] + map[cd]; }
        for (int o = 0; o < no; o++) { int cd = 0; for (int i = 7 - k; i < 7; i++) cd = cd * 8 + (otl[o][i] - '0'); ts[k][o] = map[cd] < 0 ? -1 : off[k] + map[cd]; }
        off[k + 1] = off[k] + n; free(map); }
    int G = off[8]; i8 *ht = malloc(G);
    size_t cap = 0; for (int p = 0; p <= T; p++) if ((size_t)binom[T][p] > cap) cap = binom[T][p];
    i8 *cur = malloc(cap * no), *nxt = malloc(cap * no);
    /* layer 1: Q[{t}][o] = cost(o) */
    memset(cur, INF, (size_t)binom[T][1] * no);
    for (int o = 0; o < no; o++) cur[(size_t)crank(1u << otr[o]) * no + o] = (i8)oco[o];
    long long states_le = 0;
    for (int p = 1; p < T; p++) {
        size_t nn = (size_t)binom[T][p + 1]; memset(nxt, INF, nn * no);
        unsigned m = (1u << p) - 1;
        for (long long r = 0; r < binom[T][p]; r++) {
            const i8 *qs = cur + (size_t)r * no; int mn = INF; memset(ht, INF, G);
            for (int tt = 0; tt < T; tt++) if (m >> tt & 1) for (int o = first[tt]; o < first[tt + 1]; o++) { int v = qs[o]; if (v >= INF) continue; if (v < mn) mn = v;
                if (p >= T - 1 && v <= thresh) states_le++;
                for (int k = 1; k <= 7; k++) { int id = hp[k][o]; if (v < ht[id]) ht[id] = (i8)v; } }
            if (mn < INF) for (int tt = 0; tt < T; tt++) { if (m >> tt & 1) continue; i8 *qn = nxt + (size_t)crank(m | 1u << tt) * no;
                for (int o = first[tt]; o < first[tt + 1]; o++) { int best = mn + 5;
                    for (int k = 1; k <= 7; k++) { int id = ts[k][o]; if (id >= 0) { int v = ht[id] + 5 - k; if (v < best) best = v; } }
                    best += oco[o]; if (best < qn[o]) qn[o] = (i8)(best < INF ? best : INF); } }
            unsigned cb = m & -m, rr = m + cb; m = (((rr ^ m) >> 2) / cb) | rr; }
        i8 *tmp = cur; cur = nxt; nxt = tmp; }
    int best = INF, nopt = 0, nle = 0;
    for (int o = 0; o < no; o++) { if (cur[o] < best) best = cur[o]; }
    for (int o = 0; o < no; o++) { if (cur[o] == best) nopt++; if (cur[o] <= thresh) { nle++; states_le++; } }
    printf("{\"trails\": %d, \"arcs\": %d, \"optimal_J\": %d, \"optimal_start_arcs\": %d", T, no, best, nopt);
    if (thresh > -1000) printf(", \"thresh\": %d, \"start_arcs_le_thresh\": %d, \"last_two_layer_states_le_thresh\": %lld", thresh, nle, states_le);
    printf("}\n"); return 0; }
