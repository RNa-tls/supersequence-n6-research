/* Round V -- simulated annealing over selections at the level of rows (all closed walks of any length).
   A selection: rowv[x] = v for the chosen row (x, v) of a loop, at most one row per loop, balanced
   (step(x, v) is the row state of its loop; every row has exactly one predecessor).
   Objective  Q + LAM * T,  T = loops without a row + closed trails of the walks (port cycles).
   Moves (all keep the balance):
     X  exchange: rows a, b with successors sa, sb get new lengths with step(a) = sb, step(b) = sa   (merges or splits walks)
     I  insert a rowless loop: a -> sa becomes a -> y -> sa for a state y of that loop
     D  delete a row b: pred(b) -> b -> sb becomes pred(b) -> sb, the loop of b is left without a row
     R  replace b by another state y (same loop or a rowless loop): pred(b) -> y -> sb
     N  a new closed walk of two or three rowless loops (if one exists through the chosen states)
   Every selection with objective <= OUTTHR is written once ("Q T rowless | x:v ...").
   usage: sel_sa START.txt(or "-") LAM ITER SEED OUTTHR OUT.txt   START: lines "x v" (v = 0 rowless) */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
typedef unsigned long long u64;
#define K 6
static int perms[720][6], nperm, perm_index[46656], stepT[720][7], loopOf[720], nloops, loopcode[46656], loopStates[120][6];
static const int VS[5] = {6, 4, 3, 2, 1};
static int vto[720][720 / 720 + 0];          /* unused */
static signed char vfor[720][720];           /* vfor[x][y] = v with step(x, v) = y, or 0 */
static int rowv[720], lstate[120], predS[720];
static u64 rs = 0x9E3779B97F4A7C15ULL; static u64 rnd(void) { rs ^= rs << 13; rs ^= rs >> 7; rs ^= rs << 17; return rs; }
static u64 mix(u64 x) { x ^= x >> 33; x *= 0xff51afd7ed558ccdULL; x ^= x >> 33; x *= 0xc4ceb9fe1a85ec53ULL; x ^= x >> 33; return x; }
static int code6(const int *x) { int c = 0; for (int i = 0; i < 6; i++) c = c * 6 + x[i]; return c; }
static void gen(int *a, int n) { if (n == 6) { memcpy(perms[nperm], a, sizeof(int) * 6); perm_index[code6(a)] = nperm++; return; }
    for (int i = n; i < 6; i++) { int t = a[n]; a[n] = a[i]; a[i] = t; gen(a, n + 1); t = a[n]; a[n] = a[i]; a[i] = t; } }
static void stepf(const int *x, int v, int *y) { if (v == K) { y[0] = x[1]; y[1] = x[2]; y[2] = x[3]; y[3] = x[4]; y[4] = x[0]; y[5] = x[5]; return; }
    int p = 0; for (int i = v + 1; i < K; i++) y[p++] = x[i]; for (int i = 0; i < v - 1; i++) y[p++] = x[i]; y[p++] = x[v]; y[p++] = x[v - 1]; }
static int port_perm(int v, int j) { if (v == K) return (j + 4) % 5; if (j < v) return j + K - v - 1; if (j == v) return K - v - 2; return j - v - 1; }
static int evalQT(int *Qo, int *To, int *rowless) {      /* returns 0 if the selection is not a set of closed walks */
    int Q = 0, T = 0, rl = 0; static int seen[720]; static int stamp = 0; stamp++;
    for (int l = 0; l < nloops; l++) if (lstate[l] < 0) rl++;
    for (int l = 0; l < nloops; l++) { int x0 = lstate[l]; if (x0 < 0 || seen[x0] == stamp) continue;
        int p[5] = {0, 1, 2, 3, 4}; int x = x0, guard = 0;
        do { if (seen[x] == stamp || rowv[x] == 0 || lstate[loopOf[x]] != x) return 0; seen[x] = stamp; int v = rowv[x]; Q += 6 - v; for (int j = 0; j < 5; j++) p[j] = port_perm(v, p[j]); x = stepT[x][v]; if (++guard > 130) return 0; } while (x != x0);
        int sn[5] = {0}; for (int j = 0; j < 5; j++) if (!sn[j]) { T++; int q = j; while (!sn[q]) { sn[q] = 1; q = p[q]; } } }
    *Qo = Q; *To = T + rl; *rowless = rl; return 1;
}
static void setrow(int x, int v) { rowv[x] = v; lstate[loopOf[x]] = x; predS[stepT[x][v]] = x; }
int main(int argc, char **argv) {
    double LAM = atof(argv[2]); long iters = atol(argv[3]); rs ^= mix((u64)atol(argv[4]) + 12345); double OUTTHR = atof(argv[5]);
    int a0[6] = {0, 1, 2, 3, 4, 5}; gen(a0, 0); memset(loopcode, -1, sizeof loopcode);
    for (int s = 0; s < 720; s++) { int c[6], i0 = 0; while (perms[s][i0] != 0) i0++; for (int j = 0; j < 6; j++) c[j] = perms[s][(i0 + j) % 6]; int cd = code6(c); if (loopcode[cd] < 0) loopcode[cd] = nloops++; loopOf[s] = loopcode[cd]; }
    { int cnt[120] = {0}; for (int s = 0; s < 720; s++) loopStates[loopOf[s]][cnt[loopOf[s]]++] = s; }
    for (int s = 0; s < 720; s++) for (int i = 0; i < 5; i++) { int v = VS[i], y[6]; stepf(perms[s], v, y); stepT[s][v] = perm_index[code6(y)]; vfor[s][stepT[s][v]] = (signed char)v; }
    for (int l = 0; l < 120; l++) lstate[l] = -1; memset(predS, -1, sizeof predS);
    if (strcmp(argv[1], "-")) { FILE *f = fopen(argv[1], "r"); char buf[256];
        while (fgets(buf, sizeof buf, f)) { if (buf[0] == '#' || buf[0] == '\n') continue; char xs[32]; int v; if (sscanf(buf, "%31s %d", xs, &v) != 2 || v == 0) continue; int c[6]; for (int i = 0; i < 6; i++) c[i] = xs[i] - '0'; setrow(perm_index[code6(c)], v); }
        fclose(f); }
    int Q, T, RL; if (!evalQT(&Q, &T, &RL)) { fprintf(stderr, "start selection is not balanced\n"); return 2; }
    double cur = Q + LAM * T, best = cur; fprintf(stderr, "start Q %d T %d rowless %d objective %.2f\n", Q, T, RL, cur);
    FILE *fo = fopen(argv[6], "w"); u64 *seenh = calloc(1 << 22, sizeof(u64)); long nout = 0, acc = 0;
    int sv_rowv[8], sv_x[8], nsv; int sv_l[8], sv_ls[8], nsl;
    #define SAVE_ROW(x) { sv_x[nsv] = (x); sv_rowv[nsv++] = rowv[x]; }
    #define SAVE_LOOP(l) { sv_l[nsl] = (l); sv_ls[nsl++] = lstate[l]; }
    double T0 = 3.0, T1 = 0.25; long period = 4000000;
    for (long it = 0; it < iters; it++) { double temp = T0 * pow(T1 / T0, (double)(it % period) / period);
        nsv = nsl = 0; int mv = rnd() % 10, ok = 0;
        int la = rnd() % nloops, a = lstate[la]; int vp = VS[rnd() % 5];
        if (mv < 9 && a < 0) continue;
        if (mv < 4) { /* X: a gets the length vp; its new successor t had the predecessor b, which now goes to the old successor of a */
            if (vp == rowv[a]) continue; int t = stepT[a][vp]; if (lstate[loopOf[t]] != t) continue; int b = predS[t]; if (b < 0 || b == a) continue; int sa = stepT[a][rowv[a]]; int vb = vfor[b][sa]; if (!vb) continue;
            SAVE_ROW(a); SAVE_ROW(b); rowv[a] = vp; rowv[b] = vb; ok = 1; }
        else if (mv < 6) { /* I: a -> y -> sa with y = step(a, vp) in a rowless loop */
            int y = stepT[a][vp]; int l = loopOf[y]; if (lstate[l] >= 0) continue; int sa = stepT[a][rowv[a]]; int v2 = vfor[y][sa]; if (!v2) continue;
            SAVE_ROW(a); SAVE_ROW(y); SAVE_LOOP(l); rowv[a] = vp; rowv[y] = v2; lstate[l] = y; ok = 1; }
        else if (mv < 7) { /* I2: a -> y1 -> y2 -> sa through two rowless loops */
            int y1 = stepT[a][vp]; int l1 = loopOf[y1]; if (lstate[l1] >= 0) continue; int v1 = VS[rnd() % 5]; int y2 = stepT[y1][v1]; int l2 = loopOf[y2]; if (l2 == l1 || lstate[l2] >= 0) continue; int sa = stepT[a][rowv[a]]; int v2 = vfor[y2][sa]; if (!v2) continue;
            SAVE_ROW(a); SAVE_ROW(y1); SAVE_ROW(y2); SAVE_LOOP(l1); SAVE_LOOP(l2); rowv[a] = vp; rowv[y1] = v1; rowv[y2] = v2; lstate[l1] = y1; lstate[l2] = y2; ok = 1; }
        else if (mv < 8) { /* D: delete the successor b of a */
            int b = stepT[a][rowv[a]]; if (b == a) continue; int sb = stepT[b][rowv[b]]; if (sb == b || sb == a && stepT[b][rowv[b]] == a && 0) continue; int v = vfor[a][sb]; if (!v || sb == b) continue; if (sb == a && v == 0) continue;
            if (sb == a) continue;
            SAVE_ROW(a); SAVE_ROW(b); SAVE_LOOP(loopOf[b]); rowv[a] = v; rowv[b] = 0; lstate[loopOf[b]] = -1; ok = 1; }
        else if (mv < 9) { /* R: a -> y -> sb with y = step(a, vp) in a rowless loop or another state of the loop of b */
            int b = stepT[a][rowv[a]]; if (b == a) continue; int sb = stepT[b][rowv[b]]; if (sb == a || sb == b) continue; int y = stepT[a][vp]; if (y == b) continue; int l = loopOf[y]; if (lstate[l] >= 0 && l != loopOf[b]) continue; int v2 = vfor[y][sb]; if (!v2) continue;
            SAVE_ROW(a); SAVE_ROW(b); SAVE_ROW(y); SAVE_LOOP(loopOf[b]); SAVE_LOOP(l); rowv[a] = vp; rowv[b] = 0; lstate[loopOf[b]] = -1; rowv[y] = v2; lstate[l] = y; ok = 1; }
        else { /* N: a new closed walk of two or three rowless loops */
            int l1 = rnd() % nloops; if (lstate[l1] >= 0) continue; int y1 = loopStates[l1][rnd() % 6]; int y2 = stepT[y1][vp]; int l2 = loopOf[y2]; if (l2 == l1 || lstate[l2] >= 0) continue; int v2 = vfor[y2][y1];
            if (v2) { SAVE_ROW(y1); SAVE_ROW(y2); SAVE_LOOP(l1); SAVE_LOOP(l2); rowv[y1] = vp; rowv[y2] = v2; lstate[l1] = y1; lstate[l2] = y2; ok = 1; }
            else { int v1 = VS[rnd() % 5]; int y3 = stepT[y2][v1]; int l3 = loopOf[y3]; if (l3 == l1 || l3 == l2 || lstate[l3] >= 0) continue; int v3 = vfor[y3][y1]; if (!v3) continue;
                SAVE_ROW(y1); SAVE_ROW(y2); SAVE_ROW(y3); SAVE_LOOP(l1); SAVE_LOOP(l2); SAVE_LOOP(l3); rowv[y1] = vp; rowv[y2] = v1; rowv[y3] = v3; lstate[l1] = y1; lstate[l2] = y2; lstate[l3] = y3; ok = 1; } }
        if (!ok) continue;
        int Q2, T2, RL2; int valid = evalQT(&Q2, &T2, &RL2); double nv = Q2 + LAM * T2;
        if (valid && (nv <= cur || (double)(rnd() % 1000000) / 1e6 < exp((cur - nv) / temp))) { cur = nv; acc++; memset(predS, -1, sizeof predS); for (int l = 0; l < nloops; l++) if (lstate[l] >= 0) predS[stepT[lstate[l]][rowv[lstate[l]]]] = lstate[l]; Q = Q2; T = T2; RL = RL2; if (cur < best - 1e-9) { best = cur; fprintf(stderr, "it %ld best %.2f (Q %d T %d rowless %d)\n", it, best, Q, T, RL); }
            if (cur <= OUTTHR + 1e-9) { u64 h = 0; for (int l = 0; l < nloops; l++) if (lstate[l] >= 0) h += mix((u64)lstate[l] * 8 + rowv[lstate[l]]); u64 slot = h & ((1 << 22) - 1); int known = 0;
                while (seenh[slot]) { if (seenh[slot] == h) { known = 1; break; } slot = (slot + 1) & ((1 << 22) - 1); }
                if (!known && nout < 3000000) { seenh[slot] = h; nout++; fprintf(fo, "%d %d %d |", Q, T, RL); for (int l = 0; l < nloops; l++) if (lstate[l] >= 0) { int x = lstate[l]; fprintf(fo, " %d%d%d%d%d%d:%d", perms[x][0], perms[x][1], perms[x][2], perms[x][3], perms[x][4], perms[x][5], rowv[x]); } fprintf(fo, "\n"); } } }
        else { for (int q = nsl - 1; q >= 0; q--) lstate[sv_l[q]] = sv_ls[q]; for (int q = nsv - 1; q >= 0; q--) rowv[sv_x[q]] = sv_rowv[q]; }
    }
    fclose(fo); fprintf(stderr, "done: best %.2f, accepted %ld, selections written %ld\n", best, acc, nout); return 0;
}
