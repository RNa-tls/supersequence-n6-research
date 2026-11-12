/* Round V -- heuristic assembly of T closed trails (any T): simulated annealing over the order of the trails, with
   the openings of a fixed order chosen exactly by dynamic programming (run-level arcs).
   J(order) = min over one arc per trail of  sum cost + sum (5 - overlap of consecutive arcs).
   Every value printed is the J of an actual order and choice of arcs (an upper bound on the optimum, not a proof).
   usage: jheur ARCS.txt ITER SEED OUT.json     (arcs: "trail start dropped cost head7 tail7", sorted by trail) */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#define MAXT 130
#define MAXO 6000
#define INF 10000
static int T, no, otr[MAXO], ost[MAXO], oco[MAXO], first[MAXT + 1]; static char ohd[MAXO][8], otl[MAXO][8];
static int hid[8][MAXO], tid[8][MAXO], nk[8], koff[9], G;
static int *gtab, *touched, ntouched; static int fval[MAXO];
static unsigned long long rs = 88172645463325252ULL;
static unsigned rnd(void) { rs ^= rs << 13; rs ^= rs >> 7; rs ^= rs << 17; return (unsigned)(rs >> 11); }
static int code(const char *s, int k) { int c = 0; for (int i = 0; i < k; i++) c = c * 8 + (s[i] - '0'); return c; }
static int ovl(int a, int b) { int k = 7; while (k > 0 && memcmp(otl[a] + 7 - k, ohd[b], k)) k--; return k; }
static int eval(const int *ord) {
    int t0 = ord[0], gmin = INF; for (int o = first[t0]; o < first[t0 + 1]; o++) fval[o] = oco[o];
    for (int i = 1; i < T; i++) { int tp = ord[i - 1], tc = ord[i];
        for (int q = 0; q < ntouched; q++) gtab[touched[q]] = INF; ntouched = 0; gmin = INF;
        for (int o = first[tp]; o < first[tp + 1]; o++) { int v = fval[o]; if (v < gmin) gmin = v;
            for (int k = 1; k <= 7; k++) { int id = tid[k][o]; if (id >= 0) { int g = koff[k] + id; if (gtab[g] == INF) touched[ntouched++] = g; if (v < gtab[g]) gtab[g] = v; } } }
        for (int o = first[tc]; o < first[tc + 1]; o++) { int best = gmin + 5; for (int k = 1; k <= 7; k++) { int v = gtab[koff[k] + hid[k][o]] + 5 - k; if (v < best) best = v; } fval[o] = best + oco[o]; } }
    int tl = ord[T - 1], best = INF; for (int o = first[tl]; o < first[tl + 1]; o++) if (fval[o] < best) best = fval[o];
    return best;
}
/* arcs of the best solution of an order (backward reconstruction with stored layers) */
static int witness(const int *ord, int *arc) {
    int *lay = malloc(sizeof(int) * no); int best = eval(ord);            /* recompute keeping all f (fval is per arc, arcs of different trails are disjoint) */
    /* fval now holds f for every arc of every trail of the order (each trail's arcs are written once) */
    int tl = ord[T - 1], cur = -1; for (int o = first[tl]; o < first[tl + 1]; o++) if (fval[o] == best) { cur = o; break; }
    arc[T - 1] = cur;
    for (int i = T - 1; i > 0; i--) { int tp = ord[i - 1], found = -1; for (int o = first[tp]; o < first[tp + 1] && found < 0; o++) if (fval[o] + 5 - ovl(o, cur) + oco[cur] == fval[cur]) found = o; arc[i - 1] = found; cur = found; }
    free(lay); return best;
}
int main(int argc, char **argv) {
    FILE *f = fopen(argv[1], "r"); long iters = atol(argv[2]); rs ^= (unsigned long long)atol(argv[3]) * 0x9E3779B97F4A7C15ULL; int t, s, d, c; char h[16], tl[16];
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
    gtab = malloc(sizeof(int) * G); touched = malloc(sizeof(int) * G); for (int i = 0; i < G; i++) gtab[i] = INF;
    int ord[MAXT], bestord[MAXT], nw[MAXT]; for (int i = 0; i < T; i++) ord[i] = i;
    for (int i = T - 1; i > 0; i--) { int j = rnd() % (i + 1); int x = ord[i]; ord[i] = ord[j]; ord[j] = x; }
    int cur = T > 1 ? eval(ord) : 0, best = cur; memcpy(bestord, ord, sizeof ord);
    if (T == 1) { best = INF; for (int o = 0; o < no; o++) if (oco[o] < best) best = oco[o]; }
    double T0 = 1.2, T1 = 0.08;
    for (long it = 0; it < iters && T > 1; it++) {
        double temp = T0 * pow(T1 / T0, (double)it / iters);
        memcpy(nw, ord, sizeof(int) * T); int mv = rnd() % 3, i = rnd() % T, j = rnd() % T; if (i == j) continue; if (i > j) { int x = i; i = j; j = x; }
        if (mv == 0) { int x = nw[i]; nw[i] = nw[j]; nw[j] = x; }
        else if (mv == 1) { int len = 1 + rnd() % 3; if (i + len > T) len = T - i; int buf[4]; memcpy(buf, nw + i, sizeof(int) * len);     /* move a block of up to 3 */
            int rest[MAXT], nr = 0; for (int q = 0; q < T; q++) if (q < i || q >= i + len) rest[nr++] = nw[q]; int pos = rnd() % (nr + 1), w = 0;
            for (int q = 0; q < pos; q++) nw[w++] = rest[q]; for (int q = 0; q < len; q++) nw[w++] = buf[q]; for (int q = pos; q < nr; q++) nw[w++] = rest[q]; }
        else { for (int a = i, b = j; a < b; a++, b--) { int x = nw[a]; nw[a] = nw[b]; nw[b] = x; } }
        int v = eval(nw);
        if (v <= cur || (double)(rnd() % 1000000) / 1e6 < exp((cur - v) / temp)) { cur = v; memcpy(ord, nw, sizeof(int) * T); if (v < best) { best = v; memcpy(bestord, nw, sizeof(int) * T); } }
    }
    FILE *fo = fopen(argv[4], "w"); fprintf(fo, "{\"trails\": %d, \"arcs\": %d, \"J\": %d, \"iterations\": %ld, \"witness\": [", T, no, best, iters);
    if (T > 1) { int arc[MAXT]; int chk = witness(bestord, arc); if (chk != best) { fprintf(stderr, "witness mismatch %d %d\n", chk, best); return 3; }
        for (int i = 0; i < T; i++) fprintf(fo, "%s{\"trail\": %d, \"start\": %d, \"cost\": %d}", i ? ", " : "", otr[arc[i]], ost[arc[i]], oco[arc[i]]); }
    else { for (int o = 0; o < no; o++) if (oco[o] == best) { fprintf(fo, "{\"trail\": 0, \"start\": %d, \"cost\": %d}", ost[o], oco[o]); break; } }
    fprintf(fo, "]}\n"); fclose(fo); printf("%d\n", best); return 0;
}
