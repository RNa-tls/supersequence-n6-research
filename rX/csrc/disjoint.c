/* Round X -- class-disjoint placements of two chains under the relabelings of the symbols.
   A chain is given by the entry words of its blocks (8 hex digits 1..8); its class set is the set of rotation classes
   of the entries.  For chains X and Y, count the relabelings g of {1..8} (all 40320) such that the classes of X and the
   classes of g(Y) are disjoint; with REV = 1 also g(reverse(Y)), the reversal of every entry word (the class set of the
   reversed chain).  Prints  i j |X| |Y| count_g count_g_rev  for all pairs i <= j of the input chains.
   input: one line per chain:  name  n_blocks  e_1 ... e_n   (hex entries)
   With a second file: all pairs (x in CHAINS.txt, y in CHAINS2.txt) instead.
   usage: disjoint CHAINS.txt [CHAINS2.txt] */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
typedef unsigned int u32;
#define K 8
static inline u32 cidx(u32 c) { while ((c >> 28) != K) c = c << 4 | c >> 28; u32 v = 0; for (int i = 6; i >= 0; i--) v = v * 8 + (((c >> (4 * i)) & 15u) - 1); return v; }
static inline u32 relabel(u32 w, const int *g) { u32 o = 0; for (int i = 7; i >= 0; i--) o = o << 4 | (u32)g[(w >> (4 * i)) & 15u]; return o; }
static inline u32 rev(u32 w) { u32 o = 0; for (int i = 0; i < 8; i++) o = o << 4 | ((w >> (4 * i)) & 15u); return o; }
#define MAXC 4096
static int nch, nb[2 * MAXC]; static u32 *ent[2 * MAXC]; static char name[2 * MAXC][64];
static int perms[40320][9];
int main(int argc, char **argv) {
    char buf[64]; int nx = 0;
    for (int fi = 1; fi < argc && fi <= 2; fi++) {
        FILE *f = fopen(argv[fi], "r"); if (!f) return 1; int lim = fi == 1 ? MAXC : 2 * MAXC;
        while (nch < lim && fscanf(f, "%63s %d", name[nch], &nb[nch]) == 2) { ent[nch] = malloc(sizeof(u32) * nb[nch]); for (int q = 0; q < nb[nch]; q++) { if (fscanf(f, "%63s", buf) != 1) return 1; ent[nch][q] = (u32)strtoul(buf, 0, 16); } nch++; }
        fclose(f); if (fi == 1) nx = nch;
    }
    int two = argc > 2;
    int p[8] = {1, 2, 3, 4, 5, 6, 7, 8}, np = 0;
    /* all permutations (Heap's algorithm would do; use next_permutation) */
    for (;;) { perms[np][0] = 0; for (int i = 0; i < 8; i++) perms[np][i + 1] = p[i]; np++;
        int i = 6; while (i >= 0 && p[i] > p[i + 1]) i--; if (i < 0) break; int j = 7; while (p[j] < p[i]) j--; int t = p[i]; p[i] = p[j]; p[j] = t;
        for (int a = i + 1, b = 7; a < b; a++, b--) { t = p[a]; p[a] = p[b]; p[b] = t; } }
    if (np != 40320) return 2;
    for (int x = 0; x < (two ? nx : nch); x++) {
        unsigned char *M = calloc(1 << 21, 1); for (int q = 0; q < nb[x]; q++) M[cidx(ent[x][q])] = 1;
        for (int y = two ? nx : x; y < nch; y++) {
            long cnt = 0, cntr = 0;
            #pragma omp parallel for reduction(+:cnt, cntr) schedule(static)
            for (int gi = 0; gi < 40320; gi++) {
                const int *g = perms[gi]; int ok = 1, okr = 1;
                for (int q = 0; q < nb[y] && ok; q++) if (M[cidx(relabel(ent[y][q], g))]) ok = 0;
                for (int q = 0; q < nb[y] && okr; q++) if (M[cidx(relabel(rev(ent[y][q]), g))]) okr = 0;
                cnt += ok; cntr += okr;
            }
            printf("%s %s %d %d %ld %ld\n", name[x], name[y], nb[x], nb[y], cnt, cntr); fflush(stdout);
        }
        free(M);
    }
    return 0;
}
