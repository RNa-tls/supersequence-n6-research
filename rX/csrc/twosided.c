/* Round X -- two-sided piece-count lemma: which values v = a r - b d can a chain of r pieces have, given the census of
   kept chains of one line search (all non-empty prefixes of value in (0, c]) and the reversal symmetry of model chains.

   Facts used (each proved in rX/ROUND_X_REPORT.md, section E):
   (1) every contiguous part of a chain is a chain, and the reversal of a chain is a chain with the same pieces and
       deficits (blocks, doors and the six seam words are reversal-invariant);
   (2) a part all of whose non-empty prefixes have positive value ("forward-primitive") is a kept chain, so its
       (pieces, value) is a census point;  a part all of whose non-empty suffixes have positive value
       ("backward-primitive") reverses to a kept chain, so its (pieces, value) is a census point too.
   Let S_0 = 0, S_k the value of the first k pieces, S_r = v > 0;  j = last index with S_j <= 0, i = first index with
   S_i >= v.  (j, r] is forward-primitive and (0, i] backward-primitive.
     Case A (j < i): the core (j, i] is a prefix of (j, r], hence a census point (l, w);  (0, i] is a point (l', u'),
       (j, r] a point (l'', u);  l <= l', l <= l'', r = l' + l'' - l, v = u' + u - w, u' <= w, u <= w
       (head value h = u' - w <= 0, tail value t = u - w <= 0), empty head (l' = l) forces u' = w, empty tail forces
       u = w, and a part of m pieces has value >= (a - 6 b) m.
     Case B (i <= j): (0, i] is a point (l1, u1) with u1 >= v, (j, r] a point (l2, u2) with u2 >= v, and the middle
       (i, j] has m = r - l1 - l2 >= 1 pieces and value v - u1 - u2 >= (a - 6 b) m.
   A value v > 0 that fits neither case is impossible for r pieces.

   input  : census points file (rX/src/census_points.py):  "# line a b c ..." then lines "r v1 v2 ..."
   output : for every r <= RMAX the feasible positive values, with the case(s):  r v:A|B|AB ...
   With THETA (optional 4th argument): Case B is not used with u1 >= THETA and u2 >= THETA (two row-disjoint parts of
   value >= THETA contradict the exceptional-chain lemma), for the one chain that may hold parts of value >= THETA.
   usage  : twosided POINTS.txt RMAX [NTHREADS [THETA]] */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
#define LMAX 512
#define VMAX 320
static int a, b, c, nl[LMAX], vl[LMAX][16];
int main(int argc, char **argv) {
    FILE *f = fopen(argv[1], "r"); int RMAX = atoi(argv[2]); if (argc > 3) omp_set_num_threads(atoi(argv[3]));
    int THETA = argc > 4 ? atoi(argv[4]) : 1 << 29;
    char line[8192]; int maxl = 0;
    while (fgets(line, sizeof line, f)) {
        if (line[0] == '#') { sscanf(line, "# line %d %d %d", &a, &b, &c); continue; }
        char *p = line; int r, n; if (sscanf(p, "%d%n", &r, &n) < 1) continue; p += n;
        int v; while (sscanf(p, "%d%n", &v, &n) == 1) { vl[r][nl[r]++] = v; p += n; }
        if (r > maxl) maxl = r;
    }
    fclose(f);
    int lo = a - 6 * b;                                    /* least value of one piece */
    unsigned char *A = calloc((size_t)(RMAX + 1) * (VMAX + 1), 1), *B = calloc((size_t)(RMAX + 1) * (VMAX + 1), 1);
    #pragma omp parallel
    {
        unsigned char *Al = calloc((size_t)(RMAX + 1) * (VMAX + 1), 1);
        #pragma omp for schedule(dynamic, 1)
        for (int l = 1; l <= maxl; l++) for (int iw = 0; iw < nl[l]; iw++) {
            int w = vl[l][iw];
            for (int l1 = l; l1 <= maxl; l1++) for (int i1 = 0; i1 < nl[l1]; i1++) {
                int u1 = vl[l1][i1]; if (u1 > w) continue; if (l1 == l && u1 != w) continue;
                if (u1 - w < lo * (l1 - l)) continue;
                for (int l2 = l; l2 <= maxl; l2++) {
                    int r = l1 + l2 - l; if (r > RMAX) break;
                    for (int i2 = 0; i2 < nl[l2]; i2++) {
                        int u2 = vl[l2][i2]; if (u2 > w) continue; if (l2 == l && u2 != w) continue;
                        if (u2 - w < lo * (l2 - l)) continue;
                        int v = u1 + u2 - w; if (v > 0) Al[(size_t)r * (VMAX + 1) + v] = 1;
                    }
                }
            }
        }
        #pragma omp critical
        for (size_t q = 0; q < (size_t)(RMAX + 1) * (VMAX + 1); q++) A[q] |= Al[q];
        free(Al);
    }
    /* Case B: least r for each v */
    int Bmin[VMAX + 1]; for (int v = 0; v <= VMAX; v++) Bmin[v] = 1 << 29;
    for (int l1 = 1; l1 <= maxl; l1++) for (int i1 = 0; i1 < nl[l1]; i1++) for (int l2 = 1; l2 <= maxl; l2++) for (int i2 = 0; i2 < nl[l2]; i2++) {
        int u1 = vl[l1][i1], u2 = vl[l2][i2], mx = u1 < u2 ? u1 : u2;
        if (u1 >= THETA && u2 >= THETA) continue;
        for (int v = 1; v <= mx; v++) { int x = u1 + u2 - v, m = 1; while (x > -lo * m) m++; if (l1 + l2 + m < Bmin[v]) Bmin[v] = l1 + l2 + m; }
    }
    for (int r = 1; r <= RMAX; r++) for (int v = 1; v <= c; v++) if (((long)a * r - v) % b == 0 && r >= Bmin[v]) B[(size_t)r * (VMAX + 1) + v] = 1;
    printf("# twosided line %d %d %d maxl %d RMAX %d theta %d\n", a, b, c, maxl, RMAX, THETA);
    for (int r = 1; r <= RMAX; r++) {
        printf("%d", r);
        for (int v = 1; v <= c; v++) { int x = A[(size_t)r * (VMAX + 1) + v], y = B[(size_t)r * (VMAX + 1) + v]; if (x || y) printf(" %d:%s", v, x && y ? "AB" : x ? "A" : "B"); }
        printf("\n");
    }
    return 0;
}
