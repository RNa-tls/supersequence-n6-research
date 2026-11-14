/* Round X -- third implementation of the disjoint-placement test, on bitsets over the symmetric group (written
   separately from disjoint.c and disjoint_fast.c).
   For a chain X and a class c', G_X(c') = { g in S8 : g(c') is a class of X } is computed as a 40320-bit set (for each
   class c of X and each of the 8 rotations, the relabeling sending the canonical word of c' to that rotation of the
   canonical word of c).  For a chain Y,  M = OR over the classes c' of Y of G_X(c')  is the set of relabelings g with
   X and g(Y) not disjoint; the placements g(Y) disjoint from X are the zeros of M.  The reversed orientation uses the
   classes of reverse(Y).  Output per pair: nameX nameY zeros zeros_rev (exact counts).
   With LIST=1 the Lehmer ranks of the disjoint relabelings are appended to each line with a nonzero count:
   "| o:rank o:rank ..." (o = 0 for g(Y), 1 for g(reverse Y)).
   usage: disjoint_bits LIST_X LIST_Y   (UPPER=1: same list twice, pairs x <= y only) */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
typedef unsigned int u32; typedef uint64_t u64;
#define NW 630                       /* 40320 / 64 */
#define MAXC 20000
static int cw[5040][8];              /* canonical cyclic word of each class (symbol 8 first), symbols 0..7 */
static int cindex[1 << 21];          /* code of a word rotated to start with 8 -> class number */
static int fact[9];
static inline int code7(const int *w) { int v = 0; for (int i = 1; i < 8; i++) v = v * 8 + w[i]; return v; }
static inline int class_of(u32 e) {  /* e: 8 hex digits 1..8 */
    int w[8]; for (int i = 0; i < 8; i++) w[i] = (int)((e >> (4 * (7 - i))) & 15u) - 1;
    int p = 0; while (w[p] != 7) p++;
    int r[8]; for (int i = 0; i < 8; i++) r[i] = w[(p + i) % 8];
    return cindex[code7(r)];
}
static inline u32 revw(u32 w) { u32 o = 0; for (int i = 0; i < 8; i++) o = o << 4 | ((w >> (4 * i)) & 15u); return o; }
static inline int prank(const int *g) {     /* Lehmer rank of the permutation g[0..7] of 0..7 */
    int r = 0, used = 0;
    for (int i = 0; i < 8; i++) { int x = g[i]; int smaller = __builtin_popcount(((1u << x) - 1) & ~used); r += smaller * fact[7 - i]; used |= 1u << x; }
    return r;
}
typedef struct { char name[64]; int nb; int *cls, *rcls; } chain_t;
static int load(const char *p, chain_t *L) {
    FILE *f = fopen(p, "r"); if (!f) return -1; int n = 0; char buf[64];
    while (n < MAXC && fscanf(f, "%63s %d", L[n].name, &L[n].nb) == 2) {
        L[n].cls = malloc(sizeof(int) * L[n].nb); L[n].rcls = malloc(sizeof(int) * L[n].nb);
        for (int q = 0; q < L[n].nb; q++) { if (fscanf(f, "%63s", buf) != 1) return -1; u32 e = (u32)strtoul(buf, 0, 16); L[n].cls[q] = class_of(e); L[n].rcls[q] = class_of(revw(e)); }
        n++;
    }
    fclose(f); return n;
}
static chain_t LX[MAXC], LY[MAXC];
int main(int argc, char **argv) {
    fact[0] = 1; for (int i = 1; i <= 8; i++) fact[i] = fact[i - 1] * i;
    { int p[7] = {0, 1, 2, 3, 4, 5, 6}, n = 0; memset(cindex, 0xff, sizeof cindex);
      for (;;) { cw[n][0] = 7; for (int i = 0; i < 7; i++) cw[n][i + 1] = p[i]; cindex[code7(cw[n])] = n; n++;
          int i = 5; while (i >= 0 && p[i] > p[i + 1]) i--; if (i < 0) break; int j = 6; while (p[j] < p[i]) j--; int t = p[i]; p[i] = p[j]; p[j] = t;
          for (int a = i + 1, b = 6; a < b; a++, b--) { t = p[a]; p[a] = p[b]; p[b] = t; } }
      if (n != 5040) return 2; }
    int nx = load(argv[1], LX), ny = load(argv[2], LY); if (nx < 0 || ny < 0) return 1;
    int upper = getenv("UPPER") != NULL, list = getenv("LIST") != NULL;
    /* inverse words: pos[c][s] = position of symbol s in cw[c] */
    static int pos[5040][8]; for (int c = 0; c < 5040; c++) for (int i = 0; i < 8; i++) pos[c][cw[c][i]] = i;
    /* class action table, transposed: TT[c2][g] = class of g(c2), g by Lehmer rank */
    unsigned short *TT = malloc(sizeof(unsigned short) * 5040 * 40320);
    #pragma omp parallel for schedule(static)
    for (int r = 0; r < 40320; r++) {
        int g[8], avail[8] = {0, 1, 2, 3, 4, 5, 6, 7}, rr = r, na = 8;       /* unrank */
        for (int i = 0; i < 8; i++) { int f = fact[7 - i], d = rr / f; rr %= f; g[i] = avail[d]; for (int j = d; j < na - 1; j++) avail[j] = avail[j + 1]; na--; }
        if (prank(g) != r) { fprintf(stderr, "rank error\n"); exit(3); }
        for (int c2 = 0; c2 < 5040; c2++) {
            int w[8]; for (int i = 0; i < 8; i++) w[i] = g[cw[c2][i]];
            int p = 0; while (w[p] != 7) p++;
            int rw[8]; for (int i = 0; i < 8; i++) rw[i] = w[(p + i) & 7];
            TT[(size_t)c2 * 40320 + r] = (unsigned short)cindex[code7(rw)];
        }
    }
    (void)pos;
    char **lines = calloc(nx, sizeof(char *));
    #pragma omp parallel
    {
        u64 *G = malloc(sizeof(u64) * 5040 * NW); unsigned char *inX = malloc(5040);
        #pragma omp for schedule(dynamic, 1)
        for (int x = 0; x < nx; x++) {
            memset(G, 0, sizeof(u64) * 5040 * NW); memset(inX, 0, 5040);
            for (int q = 0; q < LX[x].nb; q++) inX[LX[x].cls[q]] = 1;
            for (int c2 = 0; c2 < 5040; c2++) {
                const unsigned short *t = TT + (size_t)c2 * 40320; u64 *Gc = G + (size_t)c2 * NW;
                for (int w = 0; w < NW; w++) { u64 b = 0; for (int i = 0; i < 64; i++) b |= (u64)inX[t[w * 64 + i]] << i; Gc[w] = b; }
            }
            size_t cap = 1 << 16, len = 0; char *buf = malloc(cap);
            for (int y = upper ? x : 0; y < ny; y++) {
                long z[2]; char extra[4096]; int el = 0; extra[0] = 0;
                for (int o = 0; o < 2; o++) {
                    u64 M[NW]; memset(M, 0, sizeof M); const int *cl = o ? LY[y].rcls : LY[y].cls;
                    for (int q = 0; q < LY[y].nb; q++) {
                        const u64 *Gc = G + (size_t)cl[q] * NW; for (int w = 0; w < NW; w++) M[w] |= Gc[w];
                        if ((q & 15) == 15) { u64 a = ~0ull; for (int w = 0; w < NW; w++) a &= M[w]; if (a == ~0ull) break; }   /* all relabelings met */
                    }
                    long ones = 0; for (int w = 0; w < NW; w++) ones += __builtin_popcountll(M[w]);
                    z[o] = 40320 - ones;
                    if (list && z[o]) for (int w = 0; w < NW; w++) for (int i = 0; i < 64; i++) if (!(M[w] >> i & 1) && el < 4000) el += snprintf(extra + el, sizeof extra - el, " %d:%d", o, w * 64 + i);
                }
                char tmp[4400]; int l = snprintf(tmp, sizeof tmp, "%s %s %ld %ld%s%s\n", LX[x].name, LY[y].name, z[0], z[1], el ? " |" : "", extra);
                if (len + l + 1 > cap) { cap *= 2; buf = realloc(buf, cap); }
                memcpy(buf + len, tmp, l); len += l; buf[len] = 0;
            }
            lines[x] = buf;
        }
        free(G); free(inX);
    }
    for (int x = 0; x < nx; x++) { fputs(lines[x], stdout); free(lines[x]); }
    return 0;
}
