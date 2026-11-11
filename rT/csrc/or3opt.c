/* Round T -- exhaustive segment-relocation (pure 3-exchange) neighbourhood of a run-level route.
   Route p_1 .. p_n (runs given by their first permutation, in order); dummy ends with weight 0.
   For all cuts 0 <= i < j < k <= n the route  [..i][j+1..k][i+1..j][k+1..]  changes the weight by
       D = w(i, j+1) + w(k, i+1) + w(j, k+1) - w(i, i+1) - w(j, j+1) - w(k, k+1).
   Prints the least D and the number of moves with D < 0, D = 0.  usage: or3opt RUNS.txt OUT.json  (8 digits per line) */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
#define MAXN 5100
static char P[MAXN][9]; static signed char *M; static int n;
static int wt(const char *x, const char *y) { char last[8]; last[0] = x[7]; memcpy(last + 1, x, 7); for (int k = 7; k > 0; k--) if (!memcmp(last + 8 - k, y, k)) return 8 - k; return 8; }
int main(int argc, char **argv) {
    FILE *f = fopen(argv[1], "r"); n = 0; while (fscanf(f, "%8s", P[n + 1]) == 1) n++; fclose(f);
    int N = n + 2; M = malloc((size_t)N * N);
    for (int a = 0; a < N; a++) for (int b = 0; b < N; b++) M[(size_t)a * N + b] = (a == 0 || b == 0 || a == N - 1 || b == N - 1) ? 0 : (a == b ? 8 : (signed char)wt(P[a], P[b]));
    long tot = 0; for (int a = 1; a < n; a++) tot += M[(size_t)a * N + a + 1];
    long neg = 0, zero = 0, moves = 0; int best = 99, bi = 0, bj = 0, bk = 0; double t0 = omp_get_wtime();
    #pragma omp parallel for schedule(dynamic, 16) reduction(+:neg, zero, moves)
    for (int i = 0; i <= n; i++) {
        int lb = 99, li = 0, lj = 0, lk = 0;
        for (int j = i + 1; j <= n; j++) {
            int a = M[(size_t)i * N + j + 1] - M[(size_t)i * N + i + 1] - M[(size_t)j * N + j + 1]; const signed char *rj = M + (size_t)j * N;
            for (int k = j + 1; k <= n; k++) {
                int d = a + M[(size_t)k * N + i + 1] + rj[k + 1] - M[(size_t)k * N + k + 1];
                moves++; if (d < 0) neg++; else if (d == 0) zero++;
                if (d < lb) { lb = d; li = i; lj = j; lk = k; }
            }
        }
        #pragma omp critical
        if (lb < best) { best = lb; bi = li; bj = lj; bk = lk; }
    }
    FILE *fo = fopen(argv[2], "w");
    fprintf(fo, "{\"runs\": %d, \"route_weight\": %ld, \"length\": %ld, \"moves\": %ld, \"least_delta\": %d, \"improving_moves\": %ld, \"neutral_moves\": %ld, \"argmin\": [%d, %d, %d], \"sec\": %.1f}\n", n, tot, 35288 + tot, moves, best, neg, zero, bi, bj, bk, omp_get_wtime() - t0);
    fclose(fo); printf("n %d length %ld moves %ld least delta %d improving %ld neutral %ld (%.0fs)\n", n, 35288 + tot, moves, best, neg, zero, omp_get_wtime() - t0);
    return 0;
}
