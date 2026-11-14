/* Round Z -- first-passage chains for several thresholds in one run of the line search.
   The search is that of rX/csrc/dsearch_dump.c (Halfar's lineSearch for n = 8: same model, same order, same pruning,
   so the visited/kept counts must equal Halfar's), with a frontier buffer of 256 entries (checked).
   For a list of thresholds T (environment THETAS, comma separated, e.g. "200,210,220") every kept chain Q of value
   v >= min T is printed once if it is a first-passage chain for at least one theta in T, i.e. v >= theta and every
   proper prefix of Q (cut after a piece) has value < theta.  The line lists those thetas:
     F <theta-list> r d v <pieces...> | <entries...>
   (pieces = blocks per piece; entries = hex block entries).  A summary line (S ...) with visited/kept counts ends
   the output.  Every kept chain of value >= theta has exactly one first-passage prefix for theta.
   usage: THETAS=t1,t2,... fpdump a b c [SPLIT] */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
typedef unsigned int u32; typedef unsigned long long u64;
#define K 8
#define FCAP 256
#define MAXT 16
static int A1, B1, C1, SPLIT = 9, NT, TH[MAXT], TMIN;
static inline u32 exc(u32 c) { return (c & 15u) << 28 | c >> 4; }
static inline u32 door(u32 x) { return (x & 0xFFFFFFu) << 8 | ((x >> 24) & 15u) << 4 | x >> 28; }
static inline u32 cidx(u32 c) { while ((c >> 28) != K) c = c << 4 | c >> 28; u32 v = 0; for (int i = 6; i >= 0; i--) v = v * 8 + (((c >> (4 * i)) & 15u) - 1); return v; }
typedef struct { unsigned char *M; u64 chains, kept, dumped[MAXT]; int maxdepth, found; int pst[1024]; long pmax[1024]; } ctx_t;
typedef struct { int r, d; u32 y; int nm; u32 ent[FCAP]; int pst[16]; long pmax[16]; } front_t;
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
    /* c->pmax[r] = largest value among the prefixes with 1..r-1 pieces (proper prefixes of this chain) */
    if (collect && r == SPLIT) {
        if (ns > FCAP) { fprintf(stderr, "frontier chain too long\n"); exit(4); }
        #pragma omp critical
        { if (nfront == capfront) { capfront = capfront ? capfront * 2 : 1024; front = realloc(front, sizeof(front_t) * capfront); }
          front_t *f = &front[nfront++]; f->r = r; f->d = d; f->y = y; f->nm = ns; memcpy(f->ent, stack, sizeof(u32) * ns);
          memcpy(f->pst, c->pst, sizeof(int) * (r + 1)); memcpy(f->pmax, c->pmax, sizeof(long) * (r + 1)); }
        return; }
    c->chains++; if (r > c->maxdepth) c->maxdepth = r;
    if (B1 * (long)d + C1 < A1 * (long)r) { c->found = 1; return; }
    if (!(B1 * (long)d < A1 * (long)r)) return;
    c->kept++;
    long v = (long)A1 * r - (long)B1 * d;
    long pm = c->pmax[r];
    if (v >= TMIN) {
        int hit[MAXT], nh = 0;
        for (int t = 0; t < NT; t++) if (v >= TH[t] && pm < TH[t]) hit[nh++] = TH[t];
        if (nh) {
            for (int t = 0; t < NT; t++) if (v >= TH[t] && pm < TH[t]) c->dumped[t]++;
            #pragma omp critical
            { printf("F ");
              for (int q = 0; q < nh; q++) printf("%s%d", q ? "," : "", hit[q]);
              printf(" %d %d %ld", r, d, v);
              for (int k = 0; k < r; k++) printf(" %d", c->pst[k + 1] - c->pst[k]);
              printf(" |");
              for (int q = 0; q < ns; q++) printf(" %08x", stack[q]);
              printf("\n"); }
        }
    }
    c->pmax[r + 1] = pm > v ? pm : v;
    u32 base = (y & 0xFFFFFu) << 12, a = y >> 28, b = (y >> 24) & 15u, cc = (y >> 20) & 15u;
    u32 six[6] = {base + (a << 8 | b << 4 | cc), base + (a << 8 | cc << 4 | b), base + (b << 8 | a << 4 | cc), base + (b << 8 | cc << 4 | a), base + (cc << 8 | a << 4 | b), base + (cc << 8 | b << 4 | a)};
    for (int i = 0; i < 6 && !c->found; i++) walk(c, K - 1, six[i], r, d, collect, stack, ns, ns);
}
int main(int argc, char **argv) {
    A1 = atoi(argv[1]); B1 = atoi(argv[2]); C1 = atoi(argv[3]); if (argc > 4) SPLIT = atoi(argv[4]);
    char *ts = getenv("THETAS"); if (!ts) { fprintf(stderr, "THETAS?\n"); return 1; }
    for (char *p = strtok(ts, ","); p && NT < MAXT; p = strtok(0, ",")) TH[NT++] = atoi(p);
    TMIN = TH[0]; for (int t = 1; t < NT; t++) if (TH[t] < TMIN) TMIN = TH[t];
    double t0 = omp_get_wtime();
    ctx_t *top = calloc(1, sizeof(ctx_t)); top->M = calloc(1 << 21, 1); u32 stack[8192];
    top->pmax[0] = top->pmax[1] = -1000000000L;
    walk(top, K - 1, 0x12345678u, 0, 0, 1, stack, 0, 0);
    u64 chains = top->chains, kept = top->kept, dumped[MAXT]; int found = top->found, maxd = top->maxdepth;
    for (int t = 0; t < NT; t++) dumped[t] = top->dumped[t];
    #pragma omp parallel
    {
        ctx_t *c = calloc(1, sizeof(ctx_t)); c->M = calloc(1 << 21, 1); u32 st[8192];
        #pragma omp for schedule(dynamic, 1)
        for (long i = 0; i < nfront; i++) { if (found) continue; front_t *f = &front[i];
            for (int q = 0; q < f->nm; q++) { c->M[cidx(f->ent[q])] = 1; st[q] = f->ent[q]; }
            memcpy(c->pst, f->pst, sizeof(int) * (f->r + 1)); memcpy(c->pmax, f->pmax, sizeof(long) * (f->r + 1));
            c->found = 0; go(c, f->r, f->d, f->y, 0, st, f->nm);
            for (int q = 0; q < f->nm; q++) c->M[cidx(f->ent[q])] = 0;
            if (c->found) {
                #pragma omp atomic write
                found = 1; } }
        #pragma omp critical
        { chains += c->chains; kept += c->kept; for (int t = 0; t < NT; t++) dumped[t] += c->dumped[t]; if (c->maxdepth > maxd) maxd = c->maxdepth; }
        free(c->M); free(c);
    }
    printf("S params %d %d %d found %s visited %llu kept %llu maxpieces %d sec %.1f firstpassage", A1, B1, C1, found ? "true" : "false", chains, kept, maxd, omp_get_wtime() - t0);
    for (int t = 0; t < NT; t++) printf(" %d:%llu", TH[t], dumped[t]);
    printf("\n");
    return 0;
}
