/* Round Z -- exact count of disjoint placements g(Y) (and g(rev Y)) of a chain Y next to a chain X, g in S8,
   split by the image of the symbol 8:  same symbol (g(8) = 8)  and  cross symbol (g(8) != 8).
   Written independently of rX/csrc/disjoint_bits.c (which counts all placements with bitsets over S8); the two must
   give the same totals (checked on the threshold-46 list).
   Chains are read in the format of the first-passage lists:  name nb entry_1 .. entry_nb  (entries: 8 hex digits).
   Rows: consecutive blocks D, D' with D' = door(exit(D)) belong to one row (a row is a maximal run of door steps).
   Every row lies in one 2-cycle (z, C): z = last digit of its entries, C = the cyclic order of the other seven.
   Exactness.  For g with g(8) = 8 the program first compares 2-cycles (as bitsets over the 5040 such g): a 2-cycle used by a row of X (size s1) and by
   a row of g(Y) (size s2) with s1 + s2 >= 8 forces a common class, so g is not disjoint.  Only if no such 2-cycle exists
   are the classes compared one by one.  For g(8) = s != 8 it uses the full-full lemma: a full row of X in world 8 and
   a full row of g(Y) in world s that lie in the same {8, s}-block share a class;  so if F_X[s] + F_Y[y] > 120
   (F_X[s] = number of {8,s}-blocks containing a full world-8 row of X, y = g^{-1}(8)) no g with g(8) = s, g(y) = 8 is
   disjoint;  otherwise all 720 such g are compared class by class.  Every g is therefore decided exactly.
   Output per pair:  nameX nameY same same_rev cross cross_rev  [| o:s:rank ...]  (LIST=1: the disjoint g as Lehmer
   ranks with o = orientation, s = g(8)).
   usage: disjoint_z LIST_X LIST_Y   (UPPER=1: one list, pairs x <= y)  (SAMEONLY=1: skip g(8) != 8) */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
typedef unsigned int u32; typedef uint64_t u64;
#define MAXC 60000
static int fact[9];
static int cindex[1 << 21];               /* code of the 7 symbols after 8 (0..7 coding, 8 -> 7) -> class number */
static int cw[5040][8];                  /* canonical word of class (symbol 7 first) */
static int c7index[1 << 18];             /* code of a 7-cycle on 0..6 rotated to start with 0 -> index 0..719 */
static inline int code7(const int *w) { int v = 0; for (int i = 1; i < 8; i++) v = v * 8 + w[i]; return v; }
static int f7[8] = {720, 120, 24, 6, 2, 1, 1, 1};
static inline int class_of_word(const int *w) { int p = 0; while (w[p] != 7) p++; int r = 0, used = 0; for (int i = 1; i < 8; i++) { int x = w[(p + i) & 7]; r += __builtin_popcount(((1u << x) - 1) & ~used) * f7[i - 1]; used |= 1u << x; } return r; }
static inline void word_of(u32 e, int *w) { for (int i = 0; i < 8; i++) w[i] = (int)((e >> (4 * (7 - i))) & 15u) - 1; }
static inline u32 exc(u32 c) { return (c & 15u) << 28 | c >> 4; }
static inline u32 door(u32 x) { return (x & 0xFFFFFFu) << 8 | ((x >> 24) & 15u) << 4 | x >> 28; }
static inline u32 revw(u32 w) { u32 o = 0; for (int i = 0; i < 8; i++) o = o << 4 | ((w >> (4 * i)) & 15u); return o; }
static inline int prank(const int *g) { int r = 0, used = 0; for (int i = 0; i < 8; i++) { int x = g[i]; r += __builtin_popcount(((1u << x) - 1) & ~used) * fact[7 - i]; used |= 1u << x; } return r; }
static void unrank(int r, int *g) { int avail[8] = {0, 1, 2, 3, 4, 5, 6, 7}, na = 8; for (int i = 0; i < 8; i++) { int f = fact[7 - i], d = r / f; r %= f; g[i] = avail[d]; for (int j = d; j < na - 1; j++) avail[j] = avail[j + 1]; na--; } }
/* 2-cycle of a block entry e (symbols 0..7, world z = last symbol): index z*720 + index of the 7-cycle of the others
   relabelled to 0..6 by order (the symbol z is removed) -- we only need world 7 (= symbol 8) exactly */
typedef struct { char name[64]; int nb, nrow; int *cls, *rcls;          /* classes of Y and of rev(Y) */
    int *g8, *g8s, *rg8, *rg8s; int ng8;                               /* world-7 rows: 2-cycle (0..719) and size */
    unsigned char inX[5040]; u64 G8[12];                               /* class bitmap; world-7 2-cycle bitmap */
    unsigned char s8[720];                                             /* size of the world-7 row in each 2-cycle */
    int F[8], Fr[8]; } chain_t;
static chain_t *L1, *L2;
static int cyc_index_world7(const int *w) {   /* w: block entry with w[7] == 7 (symbol 8 last) -> 7-cycle index */
    int p = 0; while (w[p] != 0) p++; int r[7]; for (int i = 0; i < 7; i++) r[i] = w[(p + i) % 7]; int v = 0; for (int i = 1; i < 7; i++) v = v * 8 + r[i]; return c7index[v]; }
static int block_of(const int *w, int s) {    /* the {7,s}-block of a world-7 row with entry w: the 6-cycle of the others */
    int o[6], k = 0; for (int i = 0; i < 7; i++) if (w[i] != s) o[k++] = w[i];
    int p = 0, m = 9; for (int i = 0; i < 6; i++) if (o[i] < m) { m = o[i]; p = i; }
    int v = 0; for (int i = 0; i < 6; i++) v = v * 8 + o[(p + i) % 6]; return v; }
static int load(const char *path, chain_t **out) {
    FILE *f = fopen(path, "r"); if (!f) return -1; chain_t *L = calloc(MAXC, sizeof(chain_t)); int n = 0; char buf[64];
    static u32 ent[8192];
    while (n < MAXC && fscanf(f, "%63s %d", L[n].name, &L[n].nb) == 2) {
        chain_t *c = &L[n]; for (int q = 0; q < c->nb; q++) { if (fscanf(f, "%63s", buf) != 1) return -1; ent[q] = (u32)strtoul(buf, 0, 16); }
        c->cls = malloc(sizeof(int) * c->nb); c->rcls = malloc(sizeof(int) * c->nb);
        for (int q = 0; q < c->nb; q++) { int w[8]; word_of(ent[q], w); c->cls[q] = class_of_word(w); word_of(revw(ent[q]), w); c->rcls[q] = class_of_word(w); c->inX[c->cls[q]] = 1; }
        /* rows */
        int *rs = malloc(sizeof(int) * c->nb), *rl = malloc(sizeof(int) * c->nb), nr = 0;
        for (int q = 0; q < c->nb; q++) { if (q > 0 && ent[q] == door(exc(ent[q - 1]))) rl[nr - 1]++; else { rs[nr] = q; rl[nr] = 1; nr++; } }
        c->nrow = nr; c->g8 = malloc(sizeof(int) * nr); c->g8s = malloc(sizeof(int) * nr); c->rg8 = malloc(sizeof(int) * nr); c->rg8s = malloc(sizeof(int) * nr); c->ng8 = 0;
        memset(c->s8, 0, 720);
        static int blk[8][1 << 18]; static int stamp = 0; stamp++;
        for (int s = 0; s < 8; s++) { c->F[s] = 0; c->Fr[s] = 0; }
        for (int k = 0; k < nr; k++) {
            int w[8]; word_of(ent[rs[k]], w);
            if (w[7] != 7) continue;                                       /* not a world-7 row */
            int gi = cyc_index_world7(w); c->g8[c->ng8] = gi; c->g8s[c->ng8] = rl[k];
            int rw[8]; word_of(revw(ent[rs[k]]), rw);                      /* the reversed row: its 2-cycle is rev(C) */
            int t[8]; for (int i = 0; i < 7; i++) t[i] = rw[i + 1]; t[7] = 7;   /* rev(entry) = 7 c6 .. c0 -> 2-cycle of the reversed 7-cycle */
            c->rg8[c->ng8] = cyc_index_world7(t); c->rg8s[c->ng8] = rl[k];
            c->ng8++; if (c->s8[gi] < rl[k]) c->s8[gi] = (unsigned char)rl[k]; c->G8[gi >> 6] |= 1ull << (gi & 63);
            if (rl[k] == 7) for (int s = 0; s < 7; s++) { int b = block_of(w, s); if (blk[s][b] != stamp) { blk[s][b] = stamp; c->F[s]++; } }
        }
        /* F for the reversed chain: the reversed full rows lie in the reversed blocks; their number is the same */
        for (int s = 0; s < 8; s++) c->Fr[s] = c->F[s];
        free(rs); free(rl); n++;
    }
    fclose(f); *out = L; return n;
}
static short *A8;                     /* A8[h * 720 + i]: image of the world-7 2-cycle i under h in Stab(7) (5040 ranks) */
static int stab_rank[5040];           /* Lehmer rank (in S8) of the h-th element of Stab(7) */
int main(int argc, char **argv) {
    fact[0] = 1; for (int i = 1; i <= 8; i++) fact[i] = fact[i - 1] * i;
    { int p[7] = {0, 1, 2, 3, 4, 5, 6}, n = 0; memset(cindex, 0xff, sizeof cindex);
      for (;;) { cw[n][0] = 7; for (int i = 0; i < 7; i++) cw[n][i + 1] = p[i]; cindex[code7(cw[n])] = n; n++;
          int i = 5; while (i >= 0 && p[i] > p[i + 1]) i--; if (i < 0) break; int j = 6; while (p[j] < p[i]) j--; int t = p[i]; p[i] = p[j]; p[j] = t;
          for (int a = i + 1, b = 6; a < b; a++, b--) { t = p[a]; p[a] = p[b]; p[b] = t; } }
      if (n != 5040) return 2; }
    { int p[6] = {1, 2, 3, 4, 5, 6}, n = 0; memset(c7index, 0xff, sizeof c7index);
      for (;;) { int v = 0; for (int i = 0; i < 6; i++) v = v * 8 + p[i]; c7index[v] = n++;
          int i = 4; while (i >= 0 && p[i] > p[i + 1]) i--; if (i < 0) break; int j = 5; while (p[j] < p[i]) j--; int t = p[i]; p[i] = p[j]; p[j] = t;
          for (int a = i + 1, b = 5; a < b; a++, b--) { t = p[a]; p[a] = p[b]; p[b] = t; } }
      if (n != 720) return 2; }
    int nx = load(argv[1], &L1), ny = (getenv("UPPER") ? (L2 = L1, nx) : load(argv[2], &L2)); if (nx < 0 || ny < 0) return 1;
    int upper = getenv("UPPER") != NULL, list = getenv("LIST") != NULL, sameonly = getenv("SAMEONLY") != NULL;
    /* Stab(7) and its action on 7-cycles */
    A8 = malloc(sizeof(short) * 5040 * 720);
    { int h = 0; for (int r = 0; r < 40320; r++) { int g[8]; unrank(r, g); if (g[7] != 7) continue; stab_rank[h] = r;
          for (int i = 0; i < 720; i++) {               /* 7-cycle i: decode by enumeration order */
              static int cyc[720][7]; static int built = 0;
              if (!built) { int p[6] = {1, 2, 3, 4, 5, 6}, n = 0; for (;;) { cyc[n][0] = 0; for (int a = 0; a < 6; a++) cyc[n][a + 1] = p[a]; n++;
                      int a = 4; while (a >= 0 && p[a] > p[a + 1]) a--; if (a < 0) break; int b = 5; while (p[b] < p[a]) b--; int t = p[a]; p[a] = p[b]; p[b] = t;
                      for (int x = a + 1, y = 5; x < y; x++, y--) { t = p[x]; p[x] = p[y]; p[y] = t; } } built = 1; }
              int w[8]; for (int a = 0; a < 7; a++) w[a] = g[cyc[i][a]]; w[7] = 7;
              A8[h * 720 + i] = (short)cyc_index_world7(w);
          }
          h++; }
      if (h != 5040) return 3; }
    /* for every g in S8: its rank, g(7) and g^{-1}(7) */
    static int gperm[40320][8], gs[40320], gy[40320];
    for (int r = 0; r < 40320; r++) { unrank(r, gperm[r]); gs[r] = gperm[r][7]; for (int i = 0; i < 8; i++) if (gperm[r][i] == 7) gy[r] = i; }
    static int byinv[8][8][720], nbyinv[8][8];
    for (int r = 0; r < 40320; r++) { int s = gs[r], y = gy[r]; if (s != 7) byinv[s][y][nbyinv[s][y]++] = r; }
    char **lines = calloc(nx, sizeof(char *));
    u64 tot_pairs = 0, tot_same = 0, tot_cross = 0, tot_exact_cross = 0;
    #pragma omp parallel reduction(+:tot_pairs, tot_same, tot_cross, tot_exact_cross)
    {
        u64 *Bx = malloc(sizeof(u64) * 7 * 720 * 79);
        #pragma omp for schedule(dynamic, 1)
        for (int x = 0; x < nx; x++) {
            chain_t *X = &L1[x]; size_t cap = 1 << 14, len = 0; char *buf = malloc(cap); buf[0] = 0;
            /* Bx[(t-1)*720 + i] = { h : X has a world-7 row of size >= t in the 2-cycle h(i) }, t = 1..7 */
            memset(Bx, 0, sizeof(u64) * 7 * 720 * 79);
            for (int hh = 0; hh < 5040; hh++) { const short *A = A8 + (size_t)hh * 720;
                for (int i = 0; i < 720; i++) { int v = X->s8[A[i]]; for (int t = 1; t <= v; t++) Bx[((size_t)(t - 1) * 720 + i) * 79 + (hh >> 6)] |= 1ull << (hh & 63); } }
            for (int yv = upper ? x : 0; yv < ny; yv++) {
                chain_t *Y = &L2[yv]; long cnt[4] = {0, 0, 0, 0}; static __thread char extra[1 << 16]; int el = 0; extra[0] = 0;
                tot_pairs++;
                for (int o = 0; o < 2; o++) {
                    const int *yc = o ? Y->rcls : Y->cls; const int *yg = o ? Y->rg8 : Y->g8; const int *ygs = o ? Y->rg8s : Y->g8s;
                    /* same symbol: bitset over h of the 2-cycle collisions, then classes for the survivors */
                    u64 Mh[79]; memset(Mh, 0, sizeof Mh);
                    for (int k = 0; k < Y->ng8; k++) { const u64 *b = Bx + ((size_t)(8 - ygs[k] - 1) * 720 + yg[k]) * 79; for (int q = 0; q < 79; q++) Mh[q] |= b[q];
                        if ((k & 7) == 7) { u64 a = ~0ull; for (int q = 0; q < 78; q++) a &= Mh[q]; if (a == ~0ull && (Mh[78] | ~((1ull << 48) - 1)) == ~0ull) break; } }
                    for (int h = 0; h < 5040; h++) {
                        if (Mh[h >> 6] >> (h & 63) & 1) continue;
                        int hit = 0;
                        const int *g = gperm[stab_rank[h]];
                        for (int q = 0; q < Y->nb && !hit; q++) { int w[8]; for (int i = 0; i < 8; i++) w[i] = g[cw[yc[q]][i]]; if (X->inX[class_of_word(w)]) hit = 1; }
                        if (!hit) { cnt[o]++; if (list && el < (1 << 16) - 64) el += snprintf(extra + el, (1 << 16) - el, " %d:7:%d", o, stab_rank[h]); }
                    }
                    if (sameonly) continue;
                    /* cross symbol */
                    for (int s = 0; s < 7; s++) for (int yy = 0; yy < 7; yy++) {
                        if (X->F[s] + (o ? Y->Fr[yy] : Y->F[yy]) > 120) continue;
                        tot_exact_cross++;
                        for (int k = 0; k < nbyinv[s][yy]; k++) {
                            const int *g = gperm[byinv[s][yy][k]]; int hit = 0;
                            for (int q = 0; q < Y->nb && !hit; q++) { int w[8]; for (int i = 0; i < 8; i++) w[i] = g[cw[yc[q]][i]]; if (X->inX[class_of_word(w)]) hit = 1; }
                            if (!hit) { cnt[2 + o]++; if (list && el < (1 << 16) - 64) el += snprintf(extra + el, (1 << 16) - el, " %d:%d:%d", o, s, byinv[s][yy][k]); }
                        }
                    }
                }
                tot_same += cnt[0] + cnt[1]; tot_cross += cnt[2] + cnt[3];
                if (cnt[0] | cnt[1] | cnt[2] | cnt[3] | (getenv("ALL") != NULL)) {
                    int need = (int)strlen(X->name) + (int)strlen(Y->name) + el + 96;
                    if (len + need + 1 > cap) { while (len + need + 1 > cap) cap *= 2; buf = realloc(buf, cap); }
                    len += snprintf(buf + len, cap - len, "%s %s %ld %ld %ld %ld%s%s\n", X->name, Y->name, cnt[0], cnt[1], cnt[2], cnt[3], el ? " |" : "", extra);
                }
            }
            lines[x] = buf;
        }
        free(Bx);
    }
    for (int x = 0; x < nx; x++) { fputs(lines[x], stdout); free(lines[x]); }
    fprintf(stderr, "pairs %llu same %llu cross %llu exact_cross_blocks %llu\n", (unsigned long long)tot_pairs, (unsigned long long)tot_same, (unsigned long long)tot_cross, (unsigned long long)tot_exact_cross);
    printf("# pairs %llu disjoint_same_symbol %llu disjoint_cross_symbol %llu\n", (unsigned long long)tot_pairs, (unsigned long long)tot_same, (unsigned long long)tot_cross);
    return 0;
}
