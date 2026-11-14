/* Round X -- the line search of rW/csrc/dsearch_rv.c (Halfar's lineSearch for n = 8, re-implemented), which in addition
   prints every kept chain whose value a r - b d is >= DUMP, with its pieces and block entries.
   Model (as in dsearch_rv.c): a block = the rotation class of its entry D (8 hex digits 1..8); exit = D with the last
   digit moved to the front; a piece = 1..7 blocks, each entered through the door of the previous exit (first two digits
   moved to the end in reverse order); the next piece starts at one of the six words y4..y8 + (a permutation of y1 y2 y3)
   of the last exit y; all classes distinct; first entry 12345678.  keep = b d < a r <= b d + c.
   Output: one JSON line per dumped chain {"r", "d", "v", "pieces": [blocks per piece], "entries": [hex entry per block]},
   then the summary line of dsearch_rv.c (found, chains visited, kept) for comparison.
   With FIRST=1 in the environment only first-passage chains are printed: value >= DUMP and every proper prefix of
   value < DUMP (every kept chain of value >= DUMP has exactly one first-passage prefix).
   usage: dsearch_dump a b c DUMP [SPLIT] */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
typedef unsigned int u32; typedef unsigned long long u64;
#define K 8
static int A1, B1, C1, DUMP, SPLIT = 4, FIRST = 0;
static inline u32 exc(u32 c) { return (c & 15u) << 28 | c >> 4; }
static inline u32 door(u32 x) { return (x & 0xFFFFFFu) << 8 | ((x >> 24) & 15u) << 4 | x >> 28; }
static inline u32 cidx(u32 c) { while ((c >> 28) != K) c = c << 4 | c >> 28; u32 v = 0; for (int i = 6; i >= 0; i--) v = v * 8 + (((c >> (4 * i)) & 15u) - 1); return v; }
typedef struct { unsigned char *M; u64 chains, kept, dumped; int maxdepth, found; int pst[1024]; } ctx_t;
typedef struct { int r, d; u32 y; int nm; u32 ent[64]; int pst[16]; } front_t;
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
        #pragma omp critical
        { if (nfront == capfront) { capfront = capfront ? capfront * 2 : 1024; front = realloc(front, sizeof(front_t) * capfront); }
          front_t *f = &front[nfront++]; f->r = r; f->d = d; f->y = y; f->nm = ns; memcpy(f->ent, stack, sizeof(u32) * ns); memcpy(f->pst, c->pst, sizeof(int) * (r + 1)); }
        return; }
    c->chains++; if (r > c->maxdepth) c->maxdepth = r;
    if (B1 * (long)d + C1 < A1 * (long)r) { c->found = 1; return; }
    if (!(B1 * (long)d < A1 * (long)r)) return;
    c->kept++;
    long v = (long)A1 * r - (long)B1 * d;
    if (v >= DUMP && FIRST) {          /* a proper prefix of value >= DUMP?  the prefix values are those after each piece */
        long s = 0; int seen = 0;
        for (int k = 0; k + 1 < r; k++) { s += (long)A1 - (long)B1 * (7 - (c->pst[k + 1] - c->pst[k])); if (s >= DUMP) { seen = 1; break; } }
        if (seen) goto nodump;
    }
    if (v >= DUMP) {
        c->dumped++;
        #pragma omp critical
        { printf("{\"r\": %d, \"d\": %d, \"v\": %ld, \"pieces\": [", r, d, v);
          for (int k = 0; k < r; k++) printf("%s%d", k ? ", " : "", c->pst[k + 1] - c->pst[k]);
          printf("], \"entries\": [");
          for (int q = 0; q < ns; q++) printf("%s\"%08x\"", q ? ", " : "", stack[q]);
          printf("]}\n"); fflush(stdout); }
    }
    nodump:;
    u32 base = (y & 0xFFFFFu) << 12, a = y >> 28, b = (y >> 24) & 15u, cc = (y >> 20) & 15u;
    u32 six[6] = {base + (a << 8 | b << 4 | cc), base + (a << 8 | cc << 4 | b), base + (b << 8 | a << 4 | cc), base + (b << 8 | cc << 4 | a), base + (cc << 8 | a << 4 | b), base + (cc << 8 | b << 4 | a)};
    for (int i = 0; i < 6 && !c->found; i++) walk(c, K - 1, six[i], r, d, collect, stack, ns, ns);
}
int main(int argc, char **argv) {
    A1 = atoi(argv[1]); B1 = atoi(argv[2]); C1 = atoi(argv[3]); DUMP = atoi(argv[4]); if (argc > 5) SPLIT = atoi(argv[5]);
    if (getenv("FIRST")) FIRST = atoi(getenv("FIRST"));
    double t0 = omp_get_wtime();
    ctx_t *top = calloc(1, sizeof(ctx_t)); top->M = calloc(1 << 21, 1); u32 stack[8192];
    walk(top, K - 1, 0x12345678u, 0, 0, 1, stack, 0, 0);
    u64 chains = top->chains, kept = top->kept, dumped = top->dumped; int found = top->found, maxd = top->maxdepth;
    #pragma omp parallel
    {
        ctx_t *c = calloc(1, sizeof(ctx_t)); c->M = calloc(1 << 21, 1); u32 st[8192];
        #pragma omp for schedule(dynamic, 1)
        for (long i = 0; i < nfront; i++) { if (found) continue; front_t *f = &front[i];
            for (int q = 0; q < f->nm; q++) { c->M[cidx(f->ent[q])] = 1; st[q] = f->ent[q]; }
            memcpy(c->pst, f->pst, sizeof(int) * (f->r + 1));
            c->found = 0; go(c, f->r, f->d, f->y, 0, st, f->nm);
            for (int q = 0; q < f->nm; q++) c->M[cidx(f->ent[q])] = 0;
            if (c->found) {
                #pragma omp atomic write
                found = 1; } }
        #pragma omp critical
        { chains += c->chains; kept += c->kept; dumped += c->dumped; if (c->maxdepth > maxd) maxd = c->maxdepth; }
        free(c->M); free(c);
    }
    printf("{\"summary\": true, \"params\": [%d, %d, %d], \"dump_threshold\": %d, \"found\": %s, \"chains_visited\": %llu, \"chains_with_keep\": %llu, \"dumped\": %llu, \"greatest_number_of_pieces\": %d, \"sec\": %.1f}\n",
           A1, B1, C1, DUMP, found ? "true" : "false", chains, kept, dumped, maxd, omp_get_wtime() - t0);
    return 0;
}
