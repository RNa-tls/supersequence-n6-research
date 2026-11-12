/* Round V -- all images (relabelings) of the walk types of TYPES.txt that lie inside a given set of free loops.
   FREE.txt: one loop per line, as the cyclic order starting with 0 (e.g. 012345).  Output: "L Q T word start"
   (start = the state at which the image of the walk starts), one line per distinct set of rows.
   usage: cols_within TYPES.txt FREE.txt > COLUMNS.txt */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef unsigned long long u64;
#define K 6
static int perms[720][6], nperm, perm_index[46656], step_tab[720][7], state_loopcode[720]; static unsigned char freeloop[46656];
static int code6(const int *x) { int c = 0; for (int i = 0; i < 6; i++) c = c * 6 + x[i]; return c; }
static void gen(int *a, int n) { if (n == 6) { memcpy(perms[nperm], a, sizeof(int) * 6); perm_index[code6(a)] = nperm++; return; }
    for (int i = n; i < 6; i++) { int t = a[n]; a[n] = a[i]; a[i] = t; gen(a, n + 1); t = a[n]; a[n] = a[i]; a[i] = t; } }
static void stepf(const int *x, int v, int *y) { if (v == K) { y[0] = x[1]; y[1] = x[2]; y[2] = x[3]; y[3] = x[4]; y[4] = x[0]; y[5] = x[5]; return; }
    int p = 0; for (int i = v + 1; i < K; i++) y[p++] = x[i]; for (int i = 0; i < v - 1; i++) y[p++] = x[i]; y[p++] = x[v]; y[p++] = x[v - 1]; }
static u64 mix(u64 x) { x ^= x >> 33; x *= 0xff51afd7ed558ccdULL; x ^= x >> 33; x *= 0xc4ceb9fe1a85ec53ULL; x ^= x >> 33; return x; }
static int cmpu(const void *a, const void *b) { u64 x = *(const u64 *)a, y = *(const u64 *)b; return x < y ? -1 : x > y; }
int main(int argc, char **argv) {
    int a[6] = {0, 1, 2, 3, 4, 5}; gen(a, 0);
    for (int s = 0; s < 720; s++) { int c[6], i0 = 0; while (perms[s][i0] != 0) i0++; for (int j = 0; j < 6; j++) c[j] = perms[s][(i0 + j) % 6]; state_loopcode[s] = code6(c); }
    for (int s = 0; s < 720; s++) for (int v = 1; v <= 6; v++) { if (v == 5) continue; int y[6]; stepf(perms[s], v, y); step_tab[s][v] = perm_index[code6(y)]; }
    FILE *f = fopen(argv[2], "r"); char buf[64]; while (fscanf(f, "%63s", buf) == 1) { int c[6]; for (int i = 0; i < 6; i++) c[i] = buf[i] - '0'; freeloop[code6(c)] = 1; } fclose(f);
    f = fopen(argv[1], "r"); int L, Q, T; char w[200]; long nout = 0;
    while (fscanf(f, "%d %d %d %199s", &L, &Q, &T, w) == 4) { u64 hs[720]; int nh = 0;
        for (int p = 0; p < 720; p++) { int s = p, ok = 1; u64 h = 0;
            for (int i = 0; i < L && ok; i++) { int v = w[i] - '0'; if (!freeloop[state_loopcode[s]]) ok = 0; h += mix((u64)s * 8 + v + 1); s = step_tab[s][v]; }
            if (!ok) continue; int dup = 0; for (int q = 0; q < nh; q++) if (hs[q] == h) dup = 1; if (dup) continue; hs[nh++] = h;
            printf("%d %d %d %s %d%d%d%d%d%d\n", L, Q, T, w, perms[p][0], perms[p][1], perms[p][2], perms[p][3], perms[p][4], perms[p][5]); nout++; } }
    fclose(f); fprintf(stderr, "columns inside the free loops: %ld\n", nout); return 0;
}
