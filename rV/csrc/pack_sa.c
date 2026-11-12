/* Round V -- simulated annealing over packings of the 120 loops by images of closed walk types.
   objective = sum over chosen walks (Q + LW * T) + LR * (loops left without a row)
   Columns = all relabelings (720) of every walk type of the input with (Q + LW * T) / L <= DMAX, without repeats.
   Every packing whose objective is <= OUTTHR is written once (types and relabelings of its walks), so that it can
   be priced exactly afterwards.  usage: pack_sa TYPES.txt LW LR DMAX ITER SEED OUTTHR OUT.txt */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
typedef unsigned long long u64;
#define K 6
static int perms[720][6], nperm; static int loopid_of_code[46656], nloops;
static int step_tab[720][7];                   /* state index after a row of length v */
static int state_loop[720];
static int code6(const int *x) { int c = 0; for (int i = 0; i < 6; i++) c = c * 6 + x[i]; return c; }
static int perm_index[46656];
static void gen(int *a, int n) { if (n == 6) { memcpy(perms[nperm], a, sizeof(int) * 6); perm_index[code6(a)] = nperm++; return; }
    for (int i = n; i < 6; i++) { int t = a[n]; a[n] = a[i]; a[i] = t; gen(a, n + 1); t = a[n]; a[n] = a[i]; a[i] = t; } }
static void stepf(const int *x, int v, int *y) { if (v == K) { y[0] = x[1]; y[1] = x[2]; y[2] = x[3]; y[3] = x[4]; y[4] = x[0]; y[5] = x[5]; return; }
    int p = 0; for (int i = v + 1; i < K; i++) y[p++] = x[i]; for (int i = 0; i < v - 1; i++) y[p++] = x[i]; y[p++] = x[v]; y[p++] = x[v - 1]; }
typedef struct { u64 lo, hi; int Q, T, L, type, perm; u64 h; } col_t;
static col_t *cols; static long ncol, capcol;
static char (*tword)[130]; static int *tL, *tQ, *tT, ntype;
static u64 rs = 0x2545F4914F6CDD1DULL; static u64 rnd(void) { rs ^= rs << 13; rs ^= rs >> 7; rs ^= rs << 17; return rs; }
static u64 mix(u64 x) { x ^= x >> 33; x *= 0xff51afd7ed558ccdULL; x ^= x >> 33; x *= 0xc4ceb9fe1a85ec53ULL; x ^= x >> 33; return x; }
static int cmph(const void *a, const void *b) { u64 x = ((const col_t *)a)->h, y = ((const col_t *)b)->h; return x < y ? -1 : x > y; }
int main(int argc, char **argv) {
    double LW = atof(argv[2]), LR = atof(argv[3]), DMAX = atof(argv[4]); long iters = atol(argv[5]); rs ^= mix((u64)atol(argv[6]) + 1); double OUTTHR = atof(argv[7]);
    int a[6] = {0, 1, 2, 3, 4, 5}; gen(a, 0);
    memset(loopid_of_code, -1, sizeof loopid_of_code);
    for (int s = 0; s < 720; s++) { int c[6], i0 = 0; while (perms[s][i0] != 0) i0++; for (int j = 0; j < 6; j++) c[j] = perms[s][(i0 + j) % 6]; int cd = code6(c); if (loopid_of_code[cd] < 0) loopid_of_code[cd] = nloops++; state_loop[s] = loopid_of_code[cd]; }
    for (int s = 0; s < 720; s++) for (int v = 1; v <= 6; v++) { if (v == 5) continue; int y[6]; stepf(perms[s], v, y); step_tab[s][v] = perm_index[code6(y)]; }
    FILE *f = fopen(argv[1], "r"); int L, Q, T; char w[200]; int capt = 1 << 16; tword = malloc((size_t)capt * 130); tL = malloc(sizeof(int) * capt); tQ = malloc(sizeof(int) * capt); tT = malloc(sizeof(int) * capt);
    capcol = 1 << 20; cols = malloc(sizeof(col_t) * capcol);
    while (fscanf(f, "%d %d %d %199s", &L, &Q, &T, w) == 4) { if ((Q + LW * T) / L > DMAX || ntype >= capt || L > 128) continue;
        strcpy(tword[ntype], w); tL[ntype] = L; tQ[ntype] = Q; tT[ntype] = T; long first = ncol;
        for (int p = 0; p < 720; p++) { int s = p; u64 lo = 0, hi = 0, h = 0; int ok = 1;
            for (int i = 0; i < L; i++) { int v = w[i] - '0'; int l = state_loop[s]; if (l < 64) { if (lo >> l & 1) ok = 0; lo |= 1ULL << l; } else { if (hi >> (l - 64) & 1) ok = 0; hi |= 1ULL << (l - 64); } h += mix((u64)s * 8 + v + 1); s = step_tab[s][v]; }
            if (!ok || s != p) { fprintf(stderr, "type %s is not a simple closed walk\n", w); return 2; }
            if (ncol == capcol) { capcol *= 2; cols = realloc(cols, sizeof(col_t) * capcol); }
            cols[ncol++] = (col_t){lo, hi, Q, T, L, ntype, p, h}; }
        qsort(cols + first, ncol - first, sizeof(col_t), cmph); long m = first; for (long q = first; q < ncol; q++) if (q == first || cols[q].h != cols[m - 1].h) cols[m++] = cols[q]; ncol = m; ntype++; }
    fclose(f); fprintf(stderr, "types %d columns %ld loops %d\n", ntype, ncol, nloops);
    /* columns by loop */
    long *cnt = calloc(nloops + 1, sizeof(long)); for (long c = 0; c < ncol; c++) for (int l = 0; l < nloops; l++) if ((l < 64 ? cols[c].lo >> l : cols[c].hi >> (l - 64)) & 1) cnt[l + 1]++;
    for (int l = 0; l < nloops; l++) cnt[l + 1] += cnt[l]; int *byl = malloc(sizeof(int) * cnt[nloops]); long *fill = malloc(sizeof(long) * nloops); memcpy(fill, cnt, sizeof(long) * nloops);
    for (long c = 0; c < ncol; c++) for (int l = 0; l < nloops; l++) if ((l < 64 ? cols[c].lo >> l : cols[c].hi >> (l - 64)) & 1) byl[fill[l]++] = (int)c;
    int owner[128]; for (int l = 0; l < nloops; l++) owner[l] = -1; int chosen[128], nch = 0; double obj = LR * nloops, best = obj;
    FILE *fo = fopen(argv[8], "w"); u64 *seen = calloc(1 << 22, sizeof(u64)); long nout = 0;
    double T0 = 2.0, T1 = 0.15;
    for (long it = 0; it < iters; it++) { double temp = T0 * pow(T1 / T0, (double)(it % 20000000) / 20000000.0);
        int mv = rnd() % 8;
        if (mv == 0 && nch > 0) { int q = rnd() % nch; int c = chosen[q]; double d = -(cols[c].Q + LW * cols[c].T) + LR * cols[c].L;
            if (d <= 0 || (double)(rnd() % 1000000) / 1e6 < exp(-d / temp)) { for (int l = 0; l < nloops; l++) if (owner[l] == c) owner[l] = -1; chosen[q] = chosen[--nch]; obj += d; } }
        else { int l = rnd() % nloops; long nl = cnt[l + 1] - cnt[l]; if (!nl) continue; int c = byl[cnt[l] + rnd() % nl];
            int conf[32], nc = 0; double d = cols[c].Q + LW * cols[c].T - LR * cols[c].L;
            for (int q = 0; q < nloops; q++) if (((q < 64 ? cols[c].lo >> q : cols[c].hi >> (q - 64)) & 1) && owner[q] >= 0) { int o = owner[q], dup = 0; for (int z = 0; z < nc; z++) if (conf[z] == o) dup = 1; if (!dup && nc < 32) conf[nc++] = o; }
            for (int z = 0; z < nc; z++) d += -(cols[conf[z]].Q + LW * cols[conf[z]].T) + LR * cols[conf[z]].L;
            if (d <= 0 || (double)(rnd() % 1000000) / 1e6 < exp(-d / temp)) {
                for (int z = 0; z < nc; z++) { for (int q = 0; q < nloops; q++) if (owner[q] == conf[z]) owner[q] = -1; for (int y = 0; y < nch; y++) if (chosen[y] == conf[z]) { chosen[y] = chosen[--nch]; break; } }
                for (int q = 0; q < nloops; q++) if ((q < 64 ? cols[c].lo >> q : cols[c].hi >> (q - 64)) & 1) owner[q] = c; chosen[nch++] = c; obj += d; } }
        if (obj < best - 1e-9) best = obj;
        if (obj <= OUTTHR + 1e-9) { u64 h = 0; for (int y = 0; y < nch; y++) h += mix((u64)chosen[y] + 77); u64 slot = h & ((1 << 22) - 1); int known = 0;
            while (seen[slot]) { if (seen[slot] == h) { known = 1; break; } slot = (slot + 1) & ((1 << 22) - 1); }
            if (!known && nout < 2000000) { seen[slot] = h; nout++; int Qs = 0, Ts = 0, cov = 0; for (int y = 0; y < nch; y++) { Qs += cols[chosen[y]].Q; Ts += cols[chosen[y]].T; cov += cols[chosen[y]].L; }
                fprintf(fo, "%.2f %d %d %d", obj, Qs, Ts + nloops - cov, nloops - cov); for (int y = 0; y < nch; y++) fprintf(fo, " %s:%d", tword[cols[chosen[y]].type], cols[chosen[y]].perm); fprintf(fo, "\n"); } }
    }
    fclose(fo); fprintf(stderr, "best objective %.2f, packings written %ld\n", best, nout); return 0;
}
