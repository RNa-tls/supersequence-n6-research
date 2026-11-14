/* Round Y -- budget-limited depth-first search (NOT exhaustive, NOT a proof): how far can an exact weight-3 chain go
   while its value A r - B d stays above -C0 (a "dip allowance")?  Same model as rX/csrc/dsearch_dump.c, but pieces
   are tried longest first and the search stops after NODES visited chains.  Reports, for every r reached, the
   least deficit seen.  usage: dip_dfs A B C0 NODES */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned int u32; typedef unsigned long long u64;
#define K 8
static int A1, B1; static long C0; static u64 NODES, nodes; static int maxr;
static int bestd[2048];
static inline u32 exc(u32 c) { return (c & 15u) << 28 | c >> 4; }
static inline u32 door(u32 x) { return (x & 0xFFFFFFu) << 8 | ((x >> 24) & 15u) << 4 | x >> 28; }
static inline u32 cidx(u32 c) { while ((c >> 28) != K) c = c << 4 | c >> 28; u32 v = 0; for (int i = 6; i >= 0; i--) v = v * 8 + (((c >> (4 * i)) & 15u) - 1); return v; }
static unsigned char M[1 << 21];
static void go(int r, int d, u32 y);
/* extend the current piece as far as possible first, then end it at each shorter length (longest first) */
static void walk(int n, u32 D, int r, int d0) {
    if (n == 0 || nodes >= NODES) return;
    u32 ci = cidx(D); if (M[ci]) return;
    M[ci] = 1; u32 x = exc(D);
    walk(n - 1, door(x), r, d0);
    if (nodes < NODES) go(r + 1, d0 + (n - 1), x);
    M[ci] = 0;
}
static void go(int r, int d, u32 y) {
    nodes++; if (r > maxr) maxr = r; if (r < 2048 && (bestd[r] < 0 || d < bestd[r])) bestd[r] = d;
    if ((long)A1 * r - (long)B1 * d < -C0) return;
    u32 base = (y & 0xFFFFFu) << 12, a = y >> 28, b = (y >> 24) & 15u, cc = (y >> 20) & 15u;
    u32 five[5] = {base + (cc << 8 | b << 4 | a), base + (a << 8 | cc << 4 | b), base + (b << 8 | a << 4 | cc), base + (cc << 8 | a << 4 | b), base + (b << 8 | cc << 4 | a)};
    for (int i = 0; i < 5 && nodes < NODES; i++) walk(K - 1, five[i], r, d);
}
int main(int argc, char **argv) {
    A1 = atoi(argv[1]); B1 = atoi(argv[2]); C0 = atol(argv[3]); NODES = strtoull(argv[4], 0, 10);
    memset(bestd, 0xff, sizeof bestd);
    walk(K - 1, 0x12345678u, 0, 0);
    printf("# dip_dfs A=%d B=%d C0=%ld nodes=%llu maxr=%d\n# r least_deficit v2 density\n", A1, B1, C0, nodes, maxr);
    for (int r = 1; r <= maxr && r < 2048; r++) if (bestd[r] >= 0) printf("%d %d %d %.4f\n", r, bestd[r], 17 * r - 38 * bestd[r], bestd[r] / (double)r);
    return 0;
}
