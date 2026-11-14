/* Round Y -- the line search of rX/csrc/dsearch_dump.c (Halfar's lineSearch for n = 8: same model, same order, same
   pruning, so the visited/kept counts must equal Halfar's), instrumented by chain TYPE.
   Seam types (from the last exit y = z v1 v2 y4..y8 to the next entry y4..y8 + pi(z v1 v2)):
     index 1 (z v2 v1) = c, 2 (v1 z v2) = b, 3 (v1 v2 z) = e, 4 (v2 z v1) = f, 5 (v2 v1 z) = d; index 0 = same class.
   b, c, f change the moving symbol (the last symbol of the entries), d and e keep it.
   For every kept chain (b d < a r <= b d + c) with value v = a r - b d we record its type
     t = [some b/c/f seam] + 2 [some e seam] + 4 [some piece of 6 blocks] + 8 [some piece of <= 4 blocks]
   and output, per type, the number of kept chains and the largest value, the largest value by the number of label
   changes (0..15+), and per type the largest value among chains of each number of pieces r (for r <= 400).
   usage: dsearch_types a b c [SPLIT] */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
typedef unsigned int u32; typedef unsigned long long u64;
#define K 8
#define RM 420
static int A1, B1, C1, SPLIT = 4;
static inline u32 exc(u32 c) { return (c & 15u) << 28 | c >> 4; }
static inline u32 door(u32 x) { return (x & 0xFFFFFFu) << 8 | ((x >> 24) & 15u) << 4 | x >> 28; }
static inline u32 cidx(u32 c) { while ((c >> 28) != K) c = c << 4 | c >> 28; u32 v = 0; for (int i = 6; i >= 0; i--) v = v * 8 + (((c >> (4 * i)) & 15u) - 1); return v; }
typedef struct { unsigned char *M; u64 chains, kept; int maxdepth, found;
    int lab, ne, n6, n4;                       /* counters of the current chain */
    u64 cnt[16]; long maxv[16]; long maxlab[17]; long maxr[16][RM]; } ctx_t;
typedef struct { int r, d; u32 y; int nm; u32 ent[64]; int lab, ne, n6, n4; } front_t;
static front_t *front; static long nfront, capfront;
static void go(ctx_t *c, int r, int d, u32 y, int collect, u32 *stack, int ns);
static void walk(ctx_t *c, int n, u32 D, int r, int d0, int collect, u32 *stack, int ns) {
    if (n == 0 || c->found) return;
    u32 ci = cidx(D); if (c->M[ci]) return;
    c->M[ci] = 1; stack[ns] = D;
    u32 x = exc(D);
    int size = 8 - n; int a6 = (size == 6), a4 = (size <= 4);
    c->n6 += a6; c->n4 += a4;
    go(c, r + 1, d0 + (n - 1), x, collect, stack, ns + 1);
    c->n6 -= a6; c->n4 -= a4;
    if (!c->found) walk(c, n - 1, door(x), r, d0, collect, stack, ns + 1);
    c->M[ci] = 0;
}
static void go(ctx_t *c, int r, int d, u32 y, int collect, u32 *stack, int ns) {
    if (collect && r == SPLIT) {
        #pragma omp critical
        { if (nfront == capfront) { capfront = capfront ? capfront * 2 : 1024; front = realloc(front, sizeof(front_t) * capfront); }
          front_t *f = &front[nfront++]; f->r = r; f->d = d; f->y = y; f->nm = ns; memcpy(f->ent, stack, sizeof(u32) * ns);
          f->lab = c->lab; f->ne = c->ne; f->n6 = c->n6; f->n4 = c->n4; }
        return; }
    c->chains++; if (r > c->maxdepth) c->maxdepth = r;
    if (B1 * (long)d + C1 < A1 * (long)r) { c->found = 1; return; }
    if (!(B1 * (long)d < A1 * (long)r)) return;
    c->kept++;
    long v = (long)A1 * r - (long)B1 * d;
    int t = (c->lab > 0) | (c->ne > 0) << 1 | (c->n6 > 0) << 2 | (c->n4 > 0) << 3;
    c->cnt[t]++; if (v > c->maxv[t]) c->maxv[t] = v;
    int lb = c->lab < 16 ? c->lab : 16; if (v > c->maxlab[lb]) c->maxlab[lb] = v;
    if (r < RM && v > c->maxr[t][r]) c->maxr[t][r] = v;
    u32 base = (y & 0xFFFFFu) << 12, a = y >> 28, b = (y >> 24) & 15u, cc = (y >> 20) & 15u;
    u32 six[6] = {base + (a << 8 | b << 4 | cc), base + (a << 8 | cc << 4 | b), base + (b << 8 | a << 4 | cc), base + (b << 8 | cc << 4 | a), base + (cc << 8 | a << 4 | b), base + (cc << 8 | b << 4 | a)};
    for (int i = 0; i < 6 && !c->found; i++) {
        int dl = (i == 1 || i == 2 || i == 4), de = (i == 3);
        c->lab += dl; c->ne += de;
        walk(c, K - 1, six[i], r, d, collect, stack, ns);
        c->lab -= dl; c->ne -= de;
    }
}
int main(int argc, char **argv) {
    A1 = atoi(argv[1]); B1 = atoi(argv[2]); C1 = atoi(argv[3]); if (argc > 4) SPLIT = atoi(argv[4]);
    double t0 = omp_get_wtime();
    ctx_t *top = calloc(1, sizeof(ctx_t)); top->M = calloc(1 << 21, 1); u32 stack[8192];
    for (int t = 0; t < 16; t++) top->maxv[t] = -1; for (int t = 0; t < 17; t++) top->maxlab[t] = -1;
    for (int t = 0; t < 16; t++) for (int r = 0; r < RM; r++) top->maxr[t][r] = -1;
    walk(top, K - 1, 0x12345678u, 0, 0, 1, stack, 0);
    ctx_t tot = *top; int found = top->found;
    #pragma omp parallel
    {
        ctx_t *c = calloc(1, sizeof(ctx_t)); c->M = calloc(1 << 21, 1); u32 st[8192];
        for (int t = 0; t < 16; t++) c->maxv[t] = -1; for (int t = 0; t < 17; t++) c->maxlab[t] = -1;
        for (int t = 0; t < 16; t++) for (int r = 0; r < RM; r++) c->maxr[t][r] = -1;
        #pragma omp for schedule(dynamic, 1)
        for (long i = 0; i < nfront; i++) { if (found) continue; front_t *f = &front[i];
            for (int q = 0; q < f->nm; q++) { c->M[cidx(f->ent[q])] = 1; st[q] = f->ent[q]; }
            c->lab = f->lab; c->ne = f->ne; c->n6 = f->n6; c->n4 = f->n4;
            c->found = 0; go(c, f->r, f->d, f->y, 0, st, f->nm);
            for (int q = 0; q < f->nm; q++) c->M[cidx(f->ent[q])] = 0;
            if (c->found) {
                #pragma omp atomic write
                found = 1; } }
        #pragma omp critical
        { tot.chains += c->chains; tot.kept += c->kept; if (c->maxdepth > tot.maxdepth) tot.maxdepth = c->maxdepth;
          for (int t = 0; t < 16; t++) { tot.cnt[t] += c->cnt[t]; if (c->maxv[t] > tot.maxv[t]) tot.maxv[t] = c->maxv[t];
              for (int r = 0; r < RM; r++) if (c->maxr[t][r] > tot.maxr[t][r]) tot.maxr[t][r] = c->maxr[t][r]; }
          for (int t = 0; t < 17; t++) if (c->maxlab[t] > tot.maxlab[t]) tot.maxlab[t] = c->maxlab[t]; }
        free(c->M); free(c);
    }
    printf("{\"params\": [%d, %d, %d], \"found\": %s, \"chains_visited\": %llu, \"chains_with_keep\": %llu, \"greatest_number_of_pieces\": %d, \"sec\": %.1f,\n",
           A1, B1, C1, found ? "true" : "false", tot.chains, tot.kept, tot.maxdepth, omp_get_wtime() - t0);
    printf(" \"type_bits\": \"1 = some b/c/f seam (moving symbol changes), 2 = some e seam, 4 = some 6-block piece, 8 = some piece of <= 4 blocks\",\n \"types\": {");
    for (int t = 0; t < 16; t++) printf("%s\"%d\": {\"kept\": %llu, \"max_value\": %ld}", t ? ", " : "", t, tot.cnt[t], tot.maxv[t]);
    printf("},\n \"max_value_by_label_changes\": [");
    for (int t = 0; t < 17; t++) printf("%s%ld", t ? ", " : "", tot.maxlab[t]);
    printf("],\n \"max_value_by_type_and_pieces\": {");
    for (int t = 0; t < 16; t++) { printf("%s\"%d\": [", t ? ", " : "", t); for (int r = 0; r < RM; r++) printf("%s%ld", r ? ", " : "", tot.maxr[t][r]); printf("]"); }
    printf("}}\n");
    return 0;
}
