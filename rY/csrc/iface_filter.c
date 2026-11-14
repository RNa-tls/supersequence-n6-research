/* Round Y -- the interface filter for pairs of single-label chains (both anchored at the moving symbol 8).
   Interface lemma: if X (label 8) and g(Y) (label s = g(8) != 8) are class-disjoint, then
      sum over the 120 {8,s}-blocks of a_B(X) b_B(g(Y))  <=  H(X) + H(Y),
   where a_B, b_B count the label-8 (resp. label-s) groups used in the block and H counts holes.  b(g(Y)) is the
   {8,y}-profile of Y (y = g^-1(8)) carried to the {8,s}-blocks by g, so the left side is at least the rearrangement
   minimum  sum_{t,u >= 1} max(0, A_X^s(t) + A_Y^y(u) - 120),  A(t) = #blocks with >= t groups.
   A pair is RULED OUT when this minimum exceeds H(X) + H(Y) for all 49 choices of (s, y).
   Input: lines "name H A[1..7][1..6]" (rY/src/fp_profiles.py).  Output: number of pairs (x <= y) not ruled out, and
   with LIST=1 those pairs.  usage: iface_filter PROFILES.txt */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
#define MAXC 400000
static char nm[MAXC][48]; static int H[MAXC], A[MAXC][7][6];
int main(int argc, char **argv) {
    FILE *f = fopen(argv[1], "r"); if (!f) return 1; int n = 0;
    while (n < MAXC && fscanf(f, "%47s %d", nm[n], &H[n]) == 2) { for (int s = 0; s < 7; s++) for (int t = 0; t < 6; t++) if (fscanf(f, "%d", &A[n][s][t]) != 1) return 2; n++; }
    fclose(f); int list = getenv("LIST") != NULL;
    long long surv = 0, tot = 0;
    #pragma omp parallel for schedule(dynamic, 16) reduction(+:surv, tot)
    for (int x = 0; x < n; x++) for (int y = x; y < n; y++) {
        tot++; int lim = H[x] + H[y], ok = 1;           /* ok = ruled out so far */
        for (int s = 0; s < 7 && ok; s++) for (int yy = 0; yy < 7 && ok; yy++) {
            int m = 0;
            for (int t = 0; t < 6; t++) { int a = A[x][s][t] - 120; for (int u = 0; u < 6; u++) { int v = a + A[y][yy][u]; if (v > 0) m += v; } }
            if (m <= lim) ok = 0;
        }
        if (!ok) { surv++; if (list) {
            #pragma omp critical
            printf("%s %s\n", nm[x], nm[y]); } }
    }
    fprintf(stderr, "chains %d pairs %lld not_ruled_out %lld\n", n, tot, surv);
    printf("# chains %d pairs %lld not_ruled_out %lld\n", n, tot, surv);
    return 0;
}
