/* Round Y -- exhaustive check of the full-run lemma and the 6-row lemma on every chain visited by the line search of
   rX/csrc/dsearch_dump.c (same model and order; visited/kept counts must equal Halfar's).
   Seam indices of the next piece (from exit y = z v1 v2 ...): 1 = c, 2 = b, 3 = e, 4 = f, 5 = d (0 = same class).
   Checked on every visited chain (not only kept ones), at the moment a piece is closed:
   (R1) no run of 7 consecutive full pieces;
   (R2) a run of 6 consecutive full pieces starts at the first piece of the chain or right after a b or f seam;
   (R3) a seam leaving a full piece that ends a run of 6 is c or f;
   (S6) if a 6-block piece P_k is entered by a d seam and left by a d seam, then the next piece P_{k+1} starts in the
        2-cycle of P_{k-1} (same moving symbol and the same cyclic order of the other seven symbols).
   Also counted: visited chains with a 6-block piece entered and left by d seams (S6 instances).
   usage: dsearch_runs a b c [SPLIT] */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
typedef unsigned int u32; typedef unsigned long long u64;
#define K 8
#define MAXR 1024
static int A1, B1, C1, SPLIT = 4, MUT = 0;   /* MUT=1: claim runs <= 5 (must fail); MUT=2: compare with piece k-1 (must fail) */
static inline u32 exc(u32 c) { return (c & 15u) << 28 | c >> 4; }
static inline u32 door(u32 x) { return (x & 0xFFFFFFu) << 8 | ((x >> 24) & 15u) << 4 | x >> 28; }
static inline u32 cidx(u32 c) { while ((c >> 28) != K) c = c << 4 | c >> 28; u32 v = 0; for (int i = 6; i >= 0; i--) v = v * 8 + (((c >> (4 * i)) & 15u) - 1); return v; }
/* 2-cycle key of an entry D (last digit = moving symbol z): z and the cyclic order of the other seven, canonical */
static inline u64 gkey(u32 D) {
    int z = D & 15u, w[8], o[7], n = 0;
    for (int i = 0; i < 8; i++) w[i] = (D >> (4 * (7 - i))) & 15u;
    for (int i = 0; i < 8; i++) if (w[i] != z) o[n++] = w[i];
    int m = 0; for (int i = 1; i < 7; i++) if (o[i] < o[m]) m = i;
    u64 k = z; for (int i = 0; i < 7; i++) k = k << 4 | o[(m + i) % 7]; return k;
}
typedef struct { unsigned char *M; u64 chains, kept, viol[4], s6; int found, maxdepth;
    int psize[MAXR]; int stype[MAXR]; u64 gk[MAXR]; } ctx_t;   /* per piece: size, seam type entering it, 2-cycle key */
typedef struct { int r, d; u32 y; int nm; u32 ent[64]; int psize[16], stype[16]; u64 gk[16]; } front_t;
static front_t *front; static long nfront, capfront;
static void go(ctx_t *c, int r, int d, u32 y, int collect, u32 *stack, int ns, int st);
static void check(ctx_t *c, int r) {           /* piece r-1 (0-based) was just closed; chain has r pieces */
    int k = r - 1;
    int run = 0; for (int i = k; i >= 0 && c->psize[i] == 7; i--) run++;
    if (run >= (MUT == 1 ? 6 : 7)) c->viol[0]++;
    if (c->psize[k] == 7 && run == 6) { int first = k - 5; if (!(first == 0 || c->stype[first] == 2 || c->stype[first] == 4)) c->viol[1]++; }
    /* R3 and S6 look at the seam entering piece k from piece k-1 */
    if (k >= 1) {
        int prun = 0; for (int i = k - 1; i >= 0 && c->psize[i] == 7; i--) prun++;
        if (prun == 6 && !(c->stype[k] == 1 || c->stype[k] == 4)) c->viol[2]++;
        if (k >= 2 && c->psize[k - 1] == 6 && c->stype[k - 1] == 5 && c->stype[k] == 5) { c->s6++; if (c->gk[k] != c->gk[MUT == 2 ? k - 1 : k - 2]) c->viol[3]++; }
    }
}
static void walk(ctx_t *c, int n, u32 D, int r, int d0, int collect, u32 *stack, int ns, int st) {
    if (n == 0 || c->found) return;
    u32 ci = cidx(D); if (c->M[ci]) return;
    c->M[ci] = 1; stack[ns] = D;
    if (n == K - 1) { c->stype[r] = st; c->gk[r] = gkey(D); }
    u32 x = exc(D);
    c->psize[r] = 8 - n; check(c, r + 1);
    go(c, r + 1, d0 + (n - 1), x, collect, stack, ns + 1, st);
    if (!c->found) walk(c, n - 1, door(x), r, d0, collect, stack, ns + 1, st);
    c->M[ci] = 0;
}
static void go(ctx_t *c, int r, int d, u32 y, int collect, u32 *stack, int ns, int st) {
    if (collect && r == SPLIT) {
        #pragma omp critical
        { if (nfront == capfront) { capfront = capfront ? capfront * 2 : 1024; front = realloc(front, sizeof(front_t) * capfront); }
          front_t *f = &front[nfront++]; f->r = r; f->d = d; f->y = y; f->nm = ns; memcpy(f->ent, stack, sizeof(u32) * ns);
          memcpy(f->psize, c->psize, sizeof(int) * r); memcpy(f->stype, c->stype, sizeof(int) * r); memcpy(f->gk, c->gk, sizeof(u64) * r); }
        return; }
    c->chains++; if (r > c->maxdepth) c->maxdepth = r;
    if (B1 * (long)d + C1 < A1 * (long)r) { c->found = 1; return; }
    if (!(B1 * (long)d < A1 * (long)r)) return;
    c->kept++;
    u32 base = (y & 0xFFFFFu) << 12, a = y >> 28, b = (y >> 24) & 15u, cc = (y >> 20) & 15u;
    u32 six[6] = {base + (a << 8 | b << 4 | cc), base + (a << 8 | cc << 4 | b), base + (b << 8 | a << 4 | cc), base + (b << 8 | cc << 4 | a), base + (cc << 8 | a << 4 | b), base + (cc << 8 | b << 4 | a)};
    for (int i = 0; i < 6 && !c->found; i++) walk(c, K - 1, six[i], r, d, collect, stack, ns, i);
}
int main(int argc, char **argv) {
    A1 = atoi(argv[1]); B1 = atoi(argv[2]); C1 = atoi(argv[3]); if (argc > 4) SPLIT = atoi(argv[4]); if (getenv("MUT")) MUT = atoi(getenv("MUT"));
    double t0 = omp_get_wtime();
    ctx_t *top = calloc(1, sizeof(ctx_t)); top->M = calloc(1 << 21, 1); u32 stack[8192];
    walk(top, K - 1, 0x12345678u, 0, 0, 1, stack, 0, -1);
    u64 chains = top->chains, kept = top->kept, viol[4], s6 = top->s6; int found = top->found, maxd = top->maxdepth;
    for (int i = 0; i < 4; i++) viol[i] = top->viol[i];
    #pragma omp parallel
    {
        ctx_t *c = calloc(1, sizeof(ctx_t)); c->M = calloc(1 << 21, 1); u32 st[8192];
        #pragma omp for schedule(dynamic, 1)
        for (long i = 0; i < nfront; i++) { if (found) continue; front_t *f = &front[i];
            for (int q = 0; q < f->nm; q++) { c->M[cidx(f->ent[q])] = 1; st[q] = f->ent[q]; }
            memcpy(c->psize, f->psize, sizeof(int) * f->r); memcpy(c->stype, f->stype, sizeof(int) * f->r); memcpy(c->gk, f->gk, sizeof(u64) * f->r);
            c->found = 0; go(c, f->r, f->d, f->y, 0, st, f->nm, -1);
            for (int q = 0; q < f->nm; q++) c->M[cidx(f->ent[q])] = 0;
            if (c->found) {
                #pragma omp atomic write
                found = 1; } }
        #pragma omp critical
        { chains += c->chains; kept += c->kept; s6 += c->s6; for (int i = 0; i < 4; i++) viol[i] += c->viol[i]; if (c->maxdepth > maxd) maxd = c->maxdepth; }
        free(c->M); free(c);
    }
    printf("{\"params\": [%d, %d, %d], \"found\": %s, \"chains_visited\": %llu, \"chains_with_keep\": %llu, \"greatest_number_of_pieces\": %d, "
           "\"violations\": {\"R1_run7\": %llu, \"R2_run6_entry\": %llu, \"R3_run6_exit\": %llu, \"S6_return\": %llu}, \"S6_instances\": %llu, \"sec\": %.1f}\n",
           A1, B1, C1, found ? "true" : "false", chains, kept, maxd, viol[0], viol[1], viol[2], viol[3], s6, omp_get_wtime() - t0);
    return 0;
}
