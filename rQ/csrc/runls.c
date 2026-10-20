// Round Q, section 22 -- exhaustive exact run-level neighbourhoods of an r = 0 word (fixed run starts), in C.
// The word is a Hamiltonian path of runs (run = start s with its 8 left rotations); cost = sum of inter-run
// weights w(last(s), t); L = 35288 + cost; J = L - 46085.  Every multi-opening word of the closed-trail family with
// the same version (start) choice is such a path, so these moves include every split / excision / re-insertion of
// trail fragments.  The path is closed through a depot (zero arcs), so moves at the ends are included.
//   OR(l):  move one segment of l <= LMAX consecutive runs to any other position (exhaustive);
//   SWAP:   exchange two adjacent segments of lengths <= SMAX;
//   OR2:    move two disjoint segments (lengths <= L2MAX) to two arbitrary positions -- not here (see runls2).
// With DESCENT=1 the best improving move is applied repeatedly until none improves (best-improvement descent).
// usage: runls STARTS.bin(N x 8 bytes, route order) LMAX SMAX [DESCENT] [OUTSTARTS.bin]
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
static int N, M; static uint8_t *Wd; static int *tour;
static int wgt(const uint8_t *x, const uint8_t *y) { for (int s = 1; s < 8; s++) { int ok = 1; for (int i = 0; s + i < 8; i++) if (x[s + i] != y[i]) { ok = 0; break; } if (ok) return s; } return 8; }
#define WD(a, b) Wd[(size_t)(a) * M + (b)]
static long cost(void) { long c = 0; for (int p = 0; p < M; p++) c += WD(tour[p], tour[(p + 1) % M]); return c; }
int main(int argc, char **argv) {
    FILE *f = fopen(argv[1], "rb"); fseek(f, 0, SEEK_END); N = ftell(f) / 8; fseek(f, 0, SEEK_SET);
    uint8_t (*S)[8] = malloc(8 * N); if (fread(S, 8, N, f) != (size_t)N) return 2; fclose(f);
    int LMAX = atoi(argv[2]), SMAX = atoi(argv[3]), DESC = argc > 4 ? atoi(argv[4]) : 0; M = N + 1;
    uint8_t (*X)[8] = malloc(8 * N); for (int i = 0; i < N; i++) { X[i][0] = S[i][7]; for (int k = 1; k < 8; k++) X[i][k] = S[i][k - 1]; }
    Wd = calloc((size_t)M * M, 1);
    #pragma omp parallel for schedule(dynamic, 64)
    for (int i = 0; i < N; i++) for (int j = 0; j < N; j++) WD(i, j) = i == j ? 8 : wgt(X[i], S[j]);
    tour = malloc(4 * M); for (int p = 0; p < M; p++) tour[p] = p;      // runs 0..N-1 in route order, depot = N
    long base = cost(); fprintf(stderr, "N %d, cost %ld, L %ld, J %ld\n", N, base, 35288 + base, 35288 + base - 46085);
    int iter = 0;
    for (;;) {
        long bestd = 0; int bl = -1, bi = -1, bk = -1, btype = 0;
        #pragma omp parallel
        { long md = 0; int ml = -1, mi = -1, mk = -1, mt = 0;
          #pragma omp for schedule(dynamic, 8) collapse(2)
          for (int l = 1; l <= LMAX; l++) for (int i = 0; i < M; i++) {
              if (l >= M - 2) continue;
              int j = (i + l - 1) % M, p = (i - 1 + M) % M, q = (j + 1) % M;
              int Bf = tour[i], Bl = tour[j], P = tour[p], Q = tour[q];
              long rem = (long)WD(P, Bf) + WD(Bl, Q) - WD(P, Q);
              for (int t = 0; t < M - l - 1; t++) { int k = (q + t) % M; int a = tour[k], b = tour[(k + 1) % M];
                  long d = (long)WD(a, Bf) + WD(Bl, b) - WD(a, b) - rem; if (d < md) { md = d; ml = l; mi = i; mk = k; mt = 1; } } }
          #pragma omp for schedule(dynamic, 8) collapse(2)
          for (int l1 = 1; l1 <= SMAX; l1++) for (int l2 = 1; l2 <= SMAX; l2++) { if (l1 + l2 >= M - 1) continue;
              for (int i = 0; i < M; i++) { int pa = (i - 1 + M) % M, b1 = (i + l1 - 1) % M, c0 = (i + l1) % M, c1 = (i + l1 + l2 - 1) % M, d0 = (i + l1 + l2) % M;
                  int A_ = tour[pa], B0 = tour[i], B1 = tour[b1], C0 = tour[c0], C1 = tour[c1], D0 = tour[d0];
                  long d = ((long)WD(A_, C0) + WD(C1, B0) + WD(B1, D0)) - ((long)WD(A_, B0) + WD(B1, C0) + WD(C1, D0));
                  if (d < md) { md = d; ml = l1; mi = i; mk = l2; mt = 2; } } }
          #pragma omp critical
          { if (md < bestd) { bestd = md; bl = ml; bi = mi; bk = mk; btype = mt; } } }
        printf("{\"iter\": %d, \"cost\": %ld, \"L\": %ld, \"best_delta\": %ld, \"type\": %d, \"l\": %d, \"i\": %d, \"k\": %d}\n", iter, cost(), 35288 + cost(), bestd, btype, bl, bi, bk);
        fflush(stdout);
        if (bestd >= 0 || !DESC) break;
        // apply
        int *nt = malloc(4 * M); int n = 0;
        if (btype == 1) { int l = bl, i = bi, k = bk; char *inseg = calloc(M, 1); for (int t = 0; t < l; t++) inseg[(i + t) % M] = 1;
            // walk from position after the segment, emitting; after emitting position k insert the segment
            int start = (i + l) % M; for (int t = 0; t < M; t++) { int pos = (start + t) % M; if (inseg[pos]) continue; nt[n++] = tour[pos]; if (pos == k) for (int u = 0; u < l; u++) nt[n++] = tour[(i + u) % M]; }
            free(inseg); }
        else { int l1 = bl, l2 = bk, i = bi; int start = (i + l1 + l2) % M; // D... A then C then B
            for (int t = 0; t < M - l1 - l2; t++) nt[n++] = tour[(start + t) % M];
            for (int u = 0; u < l2; u++) nt[n++] = tour[(i + l1 + u) % M]; for (int u = 0; u < l1; u++) nt[n++] = tour[(i + u) % M]; }
        if (n != M) { fprintf(stderr, "apply error %d\n", n); return 5; }
        memcpy(tour, nt, 4 * M); free(nt); iter++;
    }
    if (argc > 5) { // write runs in route order starting after the depot
        int dp = 0; for (int p = 0; p < M; p++) if (tour[p] == N) dp = p;
        FILE *fo = fopen(argv[5], "wb"); for (int t = 1; t < M; t++) fwrite(S[tour[(dp + t) % M]], 8, 1, fo); fclose(fo); }
    return 0;
}
