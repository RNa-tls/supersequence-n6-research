// Round Q -- minimal stand-alone superpermutation checker (shares no code with any other checker in the repository).
// Reads a word over the symbols '1'..'8' (whitespace ignored), counts the distinct windows of length 8 that are
// permutations (Lehmer rank in 0..40319, bitmap), and prints length, distinct count and OK.
// usage: permcheck WORD.txt
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int argc, char **argv) {
    FILE *f = fopen(argv[1], "r"); if (!f) return 2;
    static char w[1 << 20]; int n = 0, ch;
    while ((ch = fgetc(f)) != EOF) { if (ch == ' ' || ch == '\n' || ch == '\r' || ch == '\t') continue; if (ch < '1' || ch > '8') { printf("bad symbol %d\n", ch); return 3; } w[n++] = (char)(ch - '1'); }
    fclose(f);
    static unsigned char seen[40320]; int distinct = 0;
    static const int fact[8] = {5040, 720, 120, 24, 6, 2, 1, 1};
    for (int i = 0; i + 8 <= n; i++) {
        int used = 0, ok = 1; for (int k = 0; k < 8; k++) { int s = w[i + k]; if (used >> s & 1) { ok = 0; break; } used |= 1 << s; }
        if (!ok) continue;
        int rank = 0, rem = 0xFF;   // Lehmer code: position of each symbol among the remaining ones
        for (int k = 0; k < 7; k++) { int s = w[i + k]; int below = __builtin_popcount(rem & ((1 << s) - 1)); rank += below * fact[k]; rem &= ~(1 << s); }
        if (!seen[rank]) { seen[rank] = 1; distinct++; }
    }
    printf("{\"length\": %d, \"distinct_permutation_windows\": %d, \"OK\": %s}\n", n, distinct, distinct == 40320 ? "true" : "false");
    return distinct == 40320 ? 0 : 1;
}
