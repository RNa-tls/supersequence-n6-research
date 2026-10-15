/*
 * Round M -- user distance for LKH (EDGE_WEIGHT_TYPE : SPECIAL): the r = 0 GTSP of n = 8 after
 *   (1) the Noon-Bean transformation (cluster = cyclic class, its nodes = allowed run starts on a
 *       zero-cost cycle; the arc a_i -> y is charged with the out-cost of a_{i+1}, plus M), and
 *   (2) the standard ATSP -> STSP doubling: node x of the ATSP becomes in(x) = x + 1 and
 *       out(x) = n0 + x + 1; the twin edge {in(x), out(x)} is fixed; the edge {out(i), in(j)} is
 *       the ATSP arc i -> j.
 * Data file (little endian): int32 n0, int32 depot, int32 M, int32 BIG; then for every ATSP node x:
 *   int32 cluster, int32 succ (cluster successor), uint8 start[8], uint8 exitp[8]
 *   (exitp = last(start(succ(x))): the exit permutation charged on arcs leaving x).
 * Inter-cluster arc i -> j costs w(exitp[i], start[j]) + M, w = smallest k >= 1 with
 * exitp[k..7] == start[0..7-k] (8 if none).
 */
#include "LKH.h"
#include <stdint.h>

static int32_t R0_n0 = 0, R0_depot = -1, R0_M = 1000, R0_BIG = 100000;
static int32_t *R0_cluster = 0, *R0_succ = 0;
static uint64_t *R0_start = 0, *R0_exit = 0;   /* 8 symbols packed 8 bits each, symbol 0 in the top byte */

void R0_load(const char *path)
{
    FILE *f = fopen(path, "rb");
    int32_t hdr[4];
    int32_t x;
    if (!f) { fprintf(stderr, "cannot open %s\n", path); exit(1); }
    if (fread(hdr, sizeof(int32_t), 4, f) != 4) { fprintf(stderr, "bad header\n"); exit(1); }
    R0_n0 = hdr[0]; R0_depot = hdr[1]; R0_M = hdr[2]; R0_BIG = hdr[3];
    R0_cluster = (int32_t *) malloc(sizeof(int32_t) * R0_n0);
    R0_succ = (int32_t *) malloc(sizeof(int32_t) * R0_n0);
    R0_start = (uint64_t *) malloc(sizeof(uint64_t) * R0_n0);
    R0_exit = (uint64_t *) malloc(sizeof(uint64_t) * R0_n0);
    for (x = 0; x < R0_n0; x++) {
        int32_t cs[2]; uint8_t s[8], e[8]; int k;
        uint64_t a = 0, b = 0;
        if (fread(cs, sizeof(int32_t), 2, f) != 2 || fread(s, 1, 8, f) != 8 || fread(e, 1, 8, f) != 8) {
            fprintf(stderr, "bad record %d\n", x); exit(1);
        }
        R0_cluster[x] = cs[0]; R0_succ[x] = cs[1];
        for (k = 0; k < 8; k++) { a = (a << 8) | s[k]; b = (b << 8) | e[k]; }
        R0_start[x] = a; R0_exit[x] = b;
    }
    fclose(f);
}

/* w(x, y) = smallest k in 1..7 with x[k..7] == y[0..7-k], else 8 (x, y packed, symbol 0 on top) */
static inline int R0_w(uint64_t x, uint64_t y)
{
    int k;
    for (k = 1; k < 8; k++) {
        int m = 8 - k;                       /* overlap length */
        uint64_t xs = x & ((m == 8) ? ~0ULL : ((1ULL << (8 * m)) - 1));      /* last m symbols of x */
        uint64_t yp = y >> (8 * k);                                           /* first m symbols of y */
        if (xs == yp) return k;
    }
    return 8;
}

int R0_arc(int i, int j)                     /* ATSP (Noon-Bean) arc cost i -> j, 0-based */
{
    if (i == j) return R0_BIG;
    if (R0_cluster[i] == R0_cluster[j]) return R0_succ[i] == j ? 0 : R0_BIG;
    if (i == R0_depot || j == R0_depot) return R0_M;
    return R0_M + R0_w(R0_exit[i], R0_start[j]);
}

int Distance_SPECIAL(Node * Na, Node * Nb)
{
    int a = Na->Id, b = Nb->Id;
    int ain = a <= R0_n0, bin = b <= R0_n0;
    if (ain == bin) return 4 * R0_BIG;
    if (ain) { int t = a; a = b; b = t; }  /* now a = out node, b = in node */
    {
        int i = a - R0_n0 - 1, j = b - 1;
        if (i == j) return 0;                /* twin edge (also fixed) */
        return R0_arc(i, j);
    }
}
