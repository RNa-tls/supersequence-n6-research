/* Round V -- independent re-implementation of the chain search of Halfar's lower-bound proof for n = 8
   (proofs/lean/n7/LowerBounds/DSearch.lean: lineSearch / zoneSearch), written from the definitions, in C.
   Model: a word = permutation of 1..8 (8 hex digits).  A block = the rotation class of its entry D; its exit is D with
   the last digit moved to the front.  A piece = 1..7 blocks, each entered through the door of the previous exit (first
   two digits moved to the end in reverse order), all classes unused; a piece of b blocks has deficit 7 - b.
   A chain = pieces, each starting at one of the six words  y4..y8 + (a permutation of y1 y2 y3)  of the last exit y.
   The first entry is 12345678.  The search visits every chain all of whose non-empty proper prefixes satisfy keep(r, d)
   and reports whether a visited chain is bad(r, d)   (r pieces, d total deficit).
     line a b c       : keep = b d < a r <= b d + c,   bad = b d + c < a r
     zone a1 b1 c1 u1 a2 b2 c2 u2 : keep = b1 d <= a1 r + u1 && b2 d <= a2 r + u2,
                                     bad  = b1 d + c1 <= a1 r + u1 && b2 d + c2 <= a2 r + u2 && a1 r != b1 d + c1
   Output: found (0/1), number of chains visited (calls of the search below a chain), chains with keep, greatest depth.
   Parallel: the chains with SPLIT pieces are collected first, then searched independently.
   usage: dsearch line a b c | zone a1 b1 c1 u1 a2 b2 c2 u2   [SPLIT] */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
typedef unsigned int u32; typedef unsigned long long u64;
#define K 8
static int mode, A1, B1, C1, U1, A2, B2, C2, U2, SPLIT = 4;
static inline int keepf(long r, long d) { if (mode == 0) return B1 * d < A1 * r && A1 * r <= B1 * d + C1; return B1 * d <= A1 * r + U1 && B2 * d <= A2 * r + U2; }
static inline int badf(long r, long d) { if (mode == 0) return B1 * d + C1 < A1 * r; return B1 * d + C1 <= A1 * r + U1 && B2 * d + C2 <= A2 * r + U2 && A1 * r != B1 * d + C1; }
static inline u32 exc(u32 c) { return (c & 15u) << 28 | c >> 4; }
static inline u32 door(u32 x) { return (x & 0xFFFFFFu) << 8 | ((x >> 24) & 15u) << 4 | x >> 28; }
static inline u32 cidx(u32 c) { while ((c >> 28) != K) c = c << 4 | c >> 28; u32 v = 0; for (int i = 6; i >= 0; i--) v = v * 8 + (((c >> (4 * i)) & 15u) - 1); return v; }
typedef struct { unsigned char *M; u64 chains, kept; int maxdepth, found; u64 *hv, *tight; int *minr; } ctx_t;
#define HV 4096
#define HR 512
typedef struct { int r, d; u32 y; int nm; u32 marks[256]; } front_t;
static front_t *front; static long nfront, capfront; static u64 top_chains, top_kept; static int top_found;
static void go(ctx_t *c, int r, int d, u32 y, int collect, u32 *stack, int ns);
static void walk(ctx_t *c, int n, u32 D, int r, int d0, int collect, u32 *stack, int ns) {
    /* pieces that begin with the block of entry D; n = blocks that may still be added */
    if (n == 0 || c->found) return;
    u32 ci = cidx(D); if (c->M[ci]) return;
    c->M[ci] = 1; stack[ns] = ci;
    u32 x = exc(D);
    go(c, r + 1, d0 + (n - 1), x, collect, stack, ns + 1);
    if (!c->found) walk(c, n - 1, door(x), r, d0, collect, stack, ns + 1);
    c->M[ci] = 0;
}
static void go(ctx_t *c, int r, int d, u32 y, int collect, u32 *stack, int ns) {
    if (collect && r == SPLIT) {
        #pragma omp critical
        { if (nfront == capfront) { capfront = capfront ? capfront * 2 : 1024; front = realloc(front, sizeof(front_t) * capfront); }
          front_t *f = &front[nfront++]; f->r = r; f->d = d; f->y = y; f->nm = ns; memcpy(f->marks, stack, sizeof(u32) * ns); }
        return; }
    c->chains++; if (r > c->maxdepth) c->maxdepth = r;
    if (badf(r, d)) { c->found = 1; return; }
    if (!keepf(r, d)) return;
    c->kept++;
    if (c->hv) { long v = (long)A1 * r - (long)B1 * d; if (v >= 0 && v < HV) { c->hv[v]++; if (r < c->minr[v]) c->minr[v] = r; } if (mode == 0 && v == C1 && r < HR) c->tight[r]++; }
    u32 base = (y & 0xFFFFFu) << 12, a = y >> 28, b = (y >> 24) & 15u, cc = (y >> 20) & 15u;
    u32 six[6] = {base + (a << 8 | b << 4 | cc), base + (a << 8 | cc << 4 | b), base + (b << 8 | a << 4 | cc), base + (b << 8 | cc << 4 | a), base + (cc << 8 | a << 4 | b), base + (cc << 8 | b << 4 | a)};
    for (int i = 0; i < 6 && !c->found; i++) walk(c, K - 1, six[i], r, d, collect, stack, ns);
}
int main(int argc, char **argv) {
    if (!strcmp(argv[1], "line")) { mode = 0; A1 = atoi(argv[2]); B1 = atoi(argv[3]); C1 = atoi(argv[4]); if (argc > 5) SPLIT = atoi(argv[5]); }
    else { mode = 1; A1 = atoi(argv[2]); B1 = atoi(argv[3]); C1 = atoi(argv[4]); U1 = atoi(argv[5]); A2 = atoi(argv[6]); B2 = atoi(argv[7]); C2 = atoi(argv[8]); U2 = atoi(argv[9]); if (argc > 10) SPLIT = atoi(argv[10]); }
    double t0 = omp_get_wtime(); int census = getenv("CENSUS") != NULL; u64 *HVg = calloc(HV, sizeof(u64)), *TGg = calloc(HR, sizeof(u64)); int *MRg = malloc(sizeof(int) * HV); for (int i = 0; i < HV; i++) MRg[i] = 1 << 30;
    ctx_t top = {calloc(1 << 21, 1), 0, 0, 0, 0, census ? HVg : NULL, census ? TGg : NULL, MRg}; u32 stack[4096];
    walk(&top, K - 1, 0x12345678u, 0, 0, 1, stack, 0);            /* the first piece; chains with SPLIT pieces are collected */
    top_chains = top.chains; top_kept = top.kept; top_found = top.found; int maxd = top.maxdepth; u64 chains = top.chains, kept = top.kept; int found = top.found;
    #pragma omp parallel
    {
        ctx_t c = {calloc(1 << 21, 1), 0, 0, 0, 0, census ? calloc(HV, sizeof(u64)) : NULL, census ? calloc(HR, sizeof(u64)) : NULL, malloc(sizeof(int) * HV)}; for (int i = 0; i < HV; i++) c.minr[i] = 1 << 30; u32 st[4096];
        #pragma omp for schedule(dynamic, 1)
        for (long i = 0; i < nfront; i++) { if (found) continue; front_t *f = &front[i];
            for (int q = 0; q < f->nm; q++) { c.M[f->marks[q]] = 1; st[q] = f->marks[q]; }
            c.found = 0; go(&c, f->r, f->d, f->y, 0, st, f->nm);
            for (int q = 0; q < f->nm; q++) c.M[f->marks[q]] = 0;
            if (c.found) { 
                #pragma omp atomic write
                found = 1; } }
        #pragma omp critical
        { chains += c.chains; kept += c.kept; if (c.maxdepth > maxd) maxd = c.maxdepth; if (census) { for (int i = 0; i < HV; i++) { HVg[i] += c.hv[i]; if (c.minr[i] < MRg[i]) MRg[i] = c.minr[i]; } for (int i = 0; i < HR; i++) TGg[i] += c.tight[i]; } }
        free(c.M);
    }
    printf("{\"search\": \"%s\", \"params\": [", argv[1]); for (int i = 2; i < (mode ? 10 : 5); i++) printf("%s%s", i > 2 ? ", " : "", argv[i]);
    printf("], \"found\": %s, \"chains_visited\": %llu, \"chains_with_keep\": %llu, \"greatest_number_of_pieces\": %d, \"split_depth\": %d, \"frontier\": %ld, \"sec\": %.1f}\n",
           found ? "true" : "false", chains, kept, maxd, SPLIT, nfront, omp_get_wtime() - t0);
    if (census) { printf("{\"kept_chains_by_value\": {"); int fst = 1; for (int i = 0; i < HV; i++) if (HVg[i]) { printf("%s\"%d\": %llu", fst ? "" : ", ", i, HVg[i]); fst = 0; }
        printf("}, \"least_pieces_by_value\": {"); fst = 1; for (int i = 0; i < HV; i++) if (HVg[i]) { printf("%s\"%d\": %d", fst ? "" : ", ", i, MRg[i]); fst = 0; }
        printf("}, \"tight_chains_by_pieces\": {"); fst = 1; for (int i = 0; i < HR; i++) if (TGg[i]) { printf("%s\"%d\": %llu", fst ? "" : ", ", i, TGg[i]); fst = 0; } printf("}}\n"); }
    return 0;
}
