/* Round V -- closed walks of rows in Pantone's completion for n = 8 (states = orderings of 0..5), enumerated by
   depth-first search from the start state 012345 (every walk can be relabelled to start there).
   A walk must pass distinct loops; rows v in {1,2,3,4,6} cost 6 - v.  Output: every closed walk with L <= LMAX rows
   and Q <= QMAX and Q * DEN <= NUM * L, as its row word, printed once per cyclic rotation class (least rotation),
   with Q and the number T of closed trails.  Pruning: at most 4 consecutive rows of length 6 fit in one orbit, so
   m more rows need at least 2 * ceil((m - a) / 5) letters, a = sixes still free in the current orbit.
   usage: walk_types LMAX QMAX NUM DEN > types.txt */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define K 6
static int LMAX, QMAX, NUM, DEN;
static int VS[5] = {6, 4, 3, 2, 1};
static char word[200]; static unsigned char used[720 * 8]; static long nfound, nodes;
static int loopid(const char *x) { /* canonical rotation starting with 0, as base-6 code */
    int i = 0; while (x[i] != 0) i++; int c = 0; for (int j = 0; j < K; j++) c = c * 6 + x[(i + j) % K]; return c; }
static unsigned char seenloop[46656];
static void step(const char *x, int v, char *y) {
    if (v == K) { y[0] = x[1]; y[1] = x[2]; y[2] = x[3]; y[3] = x[4]; y[4] = x[0]; y[5] = x[5]; return; }
    int p = 0; for (int i = v + 1; i < K; i++) y[p++] = x[i]; for (int i = 0; i < v - 1; i++) y[p++] = x[i]; y[p++] = x[v]; y[p++] = x[v - 1];
}
static int port_perm(int v, int j) { if (v == K) return (j + 4) % 5; if (j < v) return j + K - v - 1; if (j == v) return K - v - 2; return j - v - 1; }
static int trails(int L) { int p[5] = {0, 1, 2, 3, 4}; for (int i = 0; i < L; i++) for (int j = 0; j < 5; j++) p[j] = port_perm(word[i], p[j]);
    int seen[5] = {0}, n = 0; for (int j = 0; j < 5; j++) if (!seen[j]) { n++; int q = j; while (!seen[q]) { seen[q] = 1; q = p[q]; } } return n; }
static int least_rotation(int L) { for (int r = 1; r < L; r++) { int c = 0; for (int i = 0; i < L && !c; i++) c = word[(r + i) % L] - word[i]; if (c < 0) return 0; } return 1; }
static const char START[6] = {0, 1, 2, 3, 4, 5};
static void dfs(const char *x, int L, int Q, int sixrun) {
    nodes++;
    if (L > 0 && !memcmp(x, START, 6)) {
        if (Q * DEN <= NUM * L && least_rotation(L)) { nfound++; printf("%d %d %d ", L, Q, trails(L)); for (int i = 0; i < L; i++) putchar('0' + word[i]); putchar('\n'); }
        return; }
    if (L >= LMAX) return;
    int lid = loopid(x); if (seenloop[lid]) return; seenloop[lid] = 1;
    for (int vi = 0; vi < 5; vi++) { int v = VS[vi]; if (v == 6 && sixrun >= 4) continue; int q2 = Q + 6 - v; if (q2 > QMAX) continue;
        /* the walk must close with a ratio Q/L <= NUM/DEN for some L' in (L, LMAX]: necessary Q2 * DEN <= NUM * LMAX */
        if (q2 * DEN > NUM * LMAX) continue;
        char y[6]; step(x, v, y); word[L] = (char)v; dfs(y, L + 1, q2, v == 6 ? sixrun + 1 : 0); }
    seenloop[lid] = 0;
}
int main(int argc, char **argv) { LMAX = atoi(argv[1]); QMAX = atoi(argv[2]); NUM = atoi(argv[3]); DEN = atoi(argv[4]);
    dfs(START, 0, 0, 0); fprintf(stderr, "LMAX %d QMAX %d ratio %d/%d: %ld walk types, %ld nodes\n", LMAX, QMAX, NUM, DEN, nfound, nodes); return 0; }
