/* Round Z -- line search with a price on symbol changes.
   Model and order of the search: those of rX/csrc/dsearch_dump.c (Halfar's lineSearch for n = 8).  The value of a chain
   with r pieces, d holes and L seams of type b, c or f (the seams that change the moving symbol) is
        v' = a r - b d + lam L.
   v' is additive over the pieces (a piece entered through a b/c/f seam carries + lam), so the argument of Theorem D
   applies verbatim: cut a chain after its last prefix with v' <= 0; the rest has every prefix positive, i.e. it is kept
   by this search, and by symmetry it may be taken to start at 12345678.  Hence:
     if this search (keep = 0 < v' <= C on every prefix) finds no kept chain with v' > C, then every chain has v' <= C.
   With lam = 0 the search is Halfar's (visited and kept counts must equal his).
   Output: found, visited, kept, the largest v' among kept chains, the largest v' by number of symbol changes, and the
   chain that attains the largest v' (pieces, seam types, entries).
   usage: dsearch_lab a b c lam C [SPLIT]   (keep: 0 < v' <= C; with C = c and lam = 0 this is the line search) */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
typedef unsigned int u32; typedef unsigned long long u64;
#define K 8
#define FCAP 256
#define MAXL 40
static int A1, B1, C1, LAM, CC, SPLIT = 12;
static inline u32 exc(u32 c) { return (c & 15u) << 28 | c >> 4; }
static inline u32 door(u32 x) { return (x & 0xFFFFFFu) << 8 | ((x >> 24) & 15u) << 4 | x >> 28; }
static inline u32 cidx(u32 c) { while ((c >> 28) != K) c = c << 4 | c >> 28; u32 v = 0; for (int i = 6; i >= 0; i--) v = v * 8 + (((c >> (4 * i)) & 15u) - 1); return v; }
typedef struct { unsigned char *M; u64 chains, kept; int maxdepth, found; long best, bestlab[MAXL + 1]; int lab;
    int pst[2048]; char sty[2048]; int bestr, bestns; int bestpst[2048]; char beststy[2048]; u32 bestent[8192]; } ctx_t;
typedef struct { int r, d, lab; u32 y; int nm; u32 ent[FCAP]; int pst[32]; char sty[32]; } front_t;
static front_t *front; static long nfront, capfront;
static void go(ctx_t *c, int r, int d, u32 y, int collect, u32 *stack, int ns);
static void walk(ctx_t *c, int n, u32 D, int r, int d0, int collect, u32 *stack, int ns, int ps) {
    if (n == 0 || c->found) return;
    u32 ci = cidx(D); if (c->M[ci]) return;
    c->M[ci] = 1; stack[ns] = D;
    u32 x = exc(D);
    c->pst[r] = ps; c->pst[r + 1] = ns + 1;
    go(c, r + 1, d0 + (n - 1), x, collect, stack, ns + 1);
    if (!c->found) walk(c, n - 1, door(x), r, d0, collect, stack, ns + 1, ps);
    c->M[ci] = 0;
}
static void go(ctx_t *c, int r, int d, u32 y, int collect, u32 *stack, int ns) {
    if (collect && r == SPLIT) {
        if (ns > FCAP || r >= 32) { fprintf(stderr, "frontier chain too long\n"); exit(4); }
        #pragma omp critical
        { if (nfront == capfront) { capfront = capfront ? capfront * 2 : 1024; front = realloc(front, sizeof(front_t) * capfront); }
          front_t *f = &front[nfront++]; f->r = r; f->d = d; f->lab = c->lab; f->y = y; f->nm = ns; memcpy(f->ent, stack, sizeof(u32) * ns);
          memcpy(f->pst, c->pst, sizeof(int) * (r + 1)); memcpy(f->sty, c->sty, r + 1); }
        return; }
    c->chains++; if (r > c->maxdepth) c->maxdepth = r;
    if (r >= 2040 || ns >= 8100) { fprintf(stderr, "chain too long for the buffers\n"); exit(5); }
    long v = (long)A1 * r - (long)B1 * d + (long)LAM * c->lab;
    if (v > CC) { c->found = 1; return; }
    if (v <= 0) return;
    c->kept++;
    if (v > c->best) { c->best = v; c->bestr = r; c->bestns = ns; memcpy(c->bestpst, c->pst, sizeof(int) * (r + 1)); memcpy(c->beststy, c->sty, r + 1); memcpy(c->bestent, stack, sizeof(u32) * ns); }
    { int lb = c->lab < MAXL ? c->lab : MAXL; if (v > c->bestlab[lb]) c->bestlab[lb] = v; }
    u32 base = (y & 0xFFFFFu) << 12, a = y >> 28, b = (y >> 24) & 15u, cc = (y >> 20) & 15u;
    u32 six[6] = {base + (a << 8 | b << 4 | cc), base + (a << 8 | cc << 4 | b), base + (b << 8 | a << 4 | cc), base + (b << 8 | cc << 4 | a), base + (cc << 8 | a << 4 | b), base + (cc << 8 | b << 4 | a)};
    static const char tname[6] = {'0', 'c', 'b', 'e', 'f', 'd'};
    for (int i = 0; i < 6 && !c->found; i++) {
        int dl = (i == 1 || i == 2 || i == 4);
        c->lab += dl; c->sty[r] = tname[i];
        walk(c, K - 1, six[i], r, d, collect, stack, ns, ns);
        c->lab -= dl;
    }
}
int main(int argc, char **argv) {
    A1 = atoi(argv[1]); B1 = atoi(argv[2]); C1 = atoi(argv[3]); LAM = atoi(argv[4]); CC = atoi(argv[5]); if (argc > 6) SPLIT = atoi(argv[6]);
    double t0 = omp_get_wtime();
    ctx_t *top = calloc(1, sizeof(ctx_t)); top->M = calloc(1 << 21, 1); u32 stack[8192]; top->best = -1; for (int i = 0; i <= MAXL; i++) top->bestlab[i] = -1;
    walk(top, K - 1, 0x12345678u, 0, 0, 1, stack, 0, 0);
    ctx_t *tot = top; u64 chains = top->chains, kept = top->kept; int found = top->found, maxd = top->maxdepth;
    long bestlab[MAXL + 1]; for (int i = 0; i <= MAXL; i++) bestlab[i] = top->bestlab[i];
    ctx_t *bestc = top;
    #pragma omp parallel
    {
        ctx_t *c = calloc(1, sizeof(ctx_t)); c->M = calloc(1 << 21, 1); u32 st[8192]; c->best = -1; for (int i = 0; i <= MAXL; i++) c->bestlab[i] = -1;
        #pragma omp for schedule(dynamic, 1)
        for (long i = 0; i < nfront; i++) { if (found) continue; front_t *f = &front[i];
            for (int q = 0; q < f->nm; q++) { c->M[cidx(f->ent[q])] = 1; st[q] = f->ent[q]; }
            memcpy(c->pst, f->pst, sizeof(int) * (f->r + 1)); memcpy(c->sty, f->sty, f->r + 1); c->lab = f->lab;
            c->found = 0; go(c, f->r, f->d, f->y, 0, st, f->nm);
            for (int q = 0; q < f->nm; q++) c->M[cidx(f->ent[q])] = 0;
            if (c->found) {
                #pragma omp atomic write
                found = 1; } }
        #pragma omp critical
        { chains += c->chains; kept += c->kept; if (c->maxdepth > maxd) maxd = c->maxdepth;
          for (int i = 0; i <= MAXL; i++) if (c->bestlab[i] > bestlab[i]) bestlab[i] = c->bestlab[i];
          if (c->best > bestc->best) bestc = c; }
    }
    (void)tot;
    printf("{\"params\": [%d, %d, %d], \"lambda\": %d, \"keep_cap\": %d, \"found\": %s, \"chains_visited\": %llu, \"chains_with_keep\": %llu, \"greatest_number_of_pieces\": %d, \"sec\": %.1f,\n",
           A1, B1, C1, LAM, CC, found ? "true" : "false", chains, kept, maxd, omp_get_wtime() - t0);
    printf(" \"max_value\": %ld, \"max_value_by_symbol_changes\": [", bestc->best);
    for (int i = 0; i <= MAXL; i++) printf("%s%ld", i ? ", " : "", bestlab[i]);
    printf("],\n \"best_chain\": {\"r\": %d, \"pieces\": [", bestc->bestr);
    for (int k = 0; k < bestc->bestr; k++) printf("%s%d", k ? ", " : "", bestc->bestpst[k + 1] - bestc->bestpst[k]);
    printf("], \"seams\": \"");
    for (int k = 1; k < bestc->bestr; k++) putchar(bestc->beststy[k]);
    printf("\", \"entries\": [");
    for (int q = 0; q < bestc->bestns; q++) printf("%s\"%08x\"", q ? ", " : "", bestc->bestent[q]);
    printf("]}}\n");
    return 0;
}
