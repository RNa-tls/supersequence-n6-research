/* Round T -- independent C check of an n = 8 word: every window with 8 distinct symbols is recorded by its base-8
   code in a 2^24 table; counts windows, distinct permutations, missing ones.  usage: check_word WORD.txt */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned char seen[1 << 24];
int main(int argc, char **argv) {
    FILE *f = fopen(argv[1], "rb"); if (!f) return 2;
    static char w[1 << 20]; long L = fread(w, 1, sizeof w, f); fclose(f);
    while (L && (w[L - 1] == '\n' || w[L - 1] == '\r')) L--;
    long occ = 0, distinct = 0, bad = 0;
    for (long i = 0; i < L; i++) if (w[i] < '0' || w[i] > '7') bad++;
    if (bad) { printf("{\"bad_symbols\": %ld}\n", bad); return 1; }
    for (long i = 0; i + 8 <= L; i++) {
        unsigned m = 0, code = 0;
        for (int j = 0; j < 8; j++) { m |= 1u << (w[i + j] - '0'); code = code * 8 + (unsigned)(w[i + j] - '0'); }
        if (m != 255) continue;
        occ++; if (!seen[code]) { seen[code] = 1; distinct++; }
    }
    long total = 0, missing = 0; int p[8];
    for (unsigned code = 0; code < (1u << 24); code++) {
        unsigned m = 0, c = code; for (int j = 7; j >= 0; j--) { p[j] = c & 7; c >>= 3; m |= 1u << p[j]; }
        if (m != 255) continue; total++; if (!seen[code]) missing++;
    }
    printf("{\"length\": %ld, \"bad_symbols\": %ld, \"perm_windows\": %ld, \"distinct\": %ld, \"permutations\": %ld, \"missing\": %ld}\n", L, bad, occ, distinct, total, missing);
    return missing == 0 ? 0 : 1;
}
