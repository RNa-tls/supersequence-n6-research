/* Round X -- fast form of rX/csrc/disjoint.c: does a class-disjoint placement exist for a pair of chains?
   Classes are numbered 0..5039.  For every chain Y of the second list and every relabeling g, the images of K classes of
   Y (in a fixed pseudo-random order) are tabulated, for g(Y) and g(reverse Y).  For a pair (X, Y), the relabeling g
   is rejected as soon as one tabulated image lies in X; only if none of the K images does, all classes of g(Y) are
   checked directly.  Output per pair: nameX nameY count_g count_g_rev (exact counts, as disjoint.c).
   With MODE=any (environment) the scan of a pair stops at the first disjoint placement (count 1 means "some").
   With UPPER=1 (environment, same list twice) only the pairs x <= y are done; YLO/YHI restrict the chains y.
   usage: disjoint_fast LIST_X LIST_Y [K] */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
typedef unsigned int u32;
#define K8 8
#define MAXC 20000
static inline u32 cidx(u32 c) { while ((c >> 28) != K8) c = c << 4 | c >> 28; u32 v = 0; for (int i = 6; i >= 0; i--) v = v * 8 + (((c >> (4 * i)) & 15u) - 1); return v; }
static inline u32 relabel(u32 w, const int *g) { u32 o = 0; for (int i = 7; i >= 0; i--) o = o << 4 | (u32)g[(w >> (4 * i)) & 15u]; return o; }
static inline u32 rev(u32 w) { u32 o = 0; for (int i = 0; i < 8; i++) o = o << 4 | ((w >> (4 * i)) & 15u); return o; }
static short *cnum;                 /* cidx -> 0..5039 */
static int perms[40320][9];
typedef struct { char name[64]; int nb; u32 *ent; } chain_t;
static int load(const char *p, chain_t *L) {
    FILE *f = fopen(p, "r"); if (!f) return -1; int n = 0; char buf[64];
    while (n < MAXC && fscanf(f, "%63s %d", L[n].name, &L[n].nb) == 2) {
        L[n].ent = malloc(sizeof(u32) * L[n].nb);
        for (int q = 0; q < L[n].nb; q++) { if (fscanf(f, "%63s", buf) != 1) return -1; L[n].ent[q] = (u32)strtoul(buf, 0, 16); }
        n++;
    }
    fclose(f); return n;
}
static chain_t LX[MAXC], LY[MAXC];
int main(int argc, char **argv) {
    int nx = load(argv[1], LX), ny = load(argv[2], LY); int K = argc > 3 ? atoi(argv[3]) : 24;
    int any = getenv("MODE") && !strcmp(getenv("MODE"), "any"); int upper = getenv("UPPER") != NULL;
    if (nx < 0 || ny < 0) return 1;
    cnum = malloc(sizeof(short) * (1 << 21)); memset(cnum, 0xff, sizeof(short) * (1 << 21));
    { int p[8] = {1, 2, 3, 4, 5, 6, 7, 8}, np = 0, nc = 0;
      for (;;) { perms[np][0] = 0; for (int i = 0; i < 8; i++) perms[np][i + 1] = p[i];
          u32 w = 0; for (int i = 0; i < 8; i++) w = w << 4 | (u32)p[i]; u32 ci = cidx(w); if (cnum[ci] < 0) cnum[ci] = (short)nc++;
          np++; int i = 6; while (i >= 0 && p[i] > p[i + 1]) i--; if (i < 0) break; int j = 7; while (p[j] < p[i]) j--; int t = p[i]; p[i] = p[j]; p[j] = t;
          for (int a = i + 1, b = 7; a < b; a++, b--) { t = p[a]; p[a] = p[b]; p[b] = t; } }
      if (np != 40320 || nc != 5040) return 2; }
    /* class bitmaps of the X chains (5040 bits = 79 words) */
    unsigned long long (*MX)[79] = calloc(nx, sizeof *MX);
    for (int x = 0; x < nx; x++) for (int q = 0; q < LX[x].nb; q++) { int c = cnum[cidx(LX[x].ent[q])]; MX[x][c >> 6] |= 1ull << (c & 63); }
    int ylo = getenv("YLO") ? atoi(getenv("YLO")) : 0, yhi = getenv("YHI") ? atoi(getenv("YHI")) : ny;
    for (int y = ylo; y < yhi && y < ny; y++) {
        chain_t *Y = &LY[y]; int k = K < Y->nb ? K : Y->nb;
        /* pseudo-random order of the blocks of Y */
        int *ord = malloc(sizeof(int) * Y->nb); for (int q = 0; q < Y->nb; q++) ord[q] = q;
        unsigned s = 12345u + (unsigned)y; for (int q = Y->nb - 1; q > 0; q--) { s = s * 1103515245u + 12345u; int r = (int)((s >> 8) % (unsigned)(q + 1)); int t = ord[q]; ord[q] = ord[r]; ord[r] = t; }
        short *TY = malloc(sizeof(short) * 40320 * k * 2);
        #pragma omp parallel for schedule(static)
        for (int gi = 0; gi < 40320; gi++) for (int q = 0; q < k; q++) {
            u32 e = Y->ent[ord[q]];
            TY[((size_t)gi * 2 + 0) * k + q] = cnum[cidx(relabel(e, perms[gi]))];
            TY[((size_t)gi * 2 + 1) * k + q] = cnum[cidx(relabel(rev(e), perms[gi]))];
        }
        for (int x = 0; x < nx; x++) {
            if (upper && x > y) break;
            long cnt[2] = {0, 0}; int stop = 0;
            #pragma omp parallel for schedule(static) reduction(+:cnt[:2])
            for (int gi = 0; gi < 40320; gi++) {
                if (any && stop) continue;
                for (int o = 0; o < 2; o++) {
                    const short *t = TY + ((size_t)gi * 2 + o) * k; int hit = 0;
                    for (int q = 0; q < k; q++) { int c = t[q]; if (MX[x][c >> 6] >> (c & 63) & 1) { hit = 1; break; } }
                    if (!hit) {                                   /* full check */
                        for (int q = 0; q < Y->nb && !hit; q++) { u32 e = Y->ent[q]; if (o) e = rev(e); int c = cnum[cidx(relabel(e, perms[gi]))]; if (MX[x][c >> 6] >> (c & 63) & 1) hit = 1; }
                    }
                    if (!hit) { cnt[o]++; if (any) stop = 1; }
                }
            }
            printf("%s %s %ld %ld\n", LX[x].name, Y->name, cnt[0], cnt[1]);
        }
        fflush(stdout); free(TY); free(ord);
    }
    return 0;
}
