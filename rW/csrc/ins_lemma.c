/* Round W -- exhaustive check of the letter-level insertion lemma for permutation windows (n = 8).
   A piece p starts with the permutation P1 (head) and ends with T (tail); its cut link T -> P1 has weight wi.
   The predecessor ends with X (w(X, P1) = w1), the successor starts with Y (w(T, Y) = w2).  Removing p and
   joining X -> Y changes J by  -ins,  ins = w1 + w2 - w(X, Y) - wi.
   LEMMA: if w1 >= wi and w2 >= wi then ins >= 0, i.e. w(X, Y) <= w1 + w2 - wi.
   By relabeling, P1 = 01234567.  T ranges over all permutations with w(T, P1) = wi, X over w(X, P1) = w1, Y over
   w(T, Y) = w2 (all such are a[w:] + arrangement of a[:w], exactly w! of them, each of exact weight w).
   For every (wi, w1, w2) with wi <= 5 and w1, w2 <= 7 the minimum of ins is printed, so the cases outside the
   lemma's hypothesis are quantified too.  usage: ins_lemma  -> JSON on stdout */
#include <stdio.h>
#include <string.h>
static int ov(const unsigned char *a, const unsigned char *b) { for (int k = 7; k > 0; k--) if (!memcmp(a + 8 - k, b, k)) return k; return 0; }
static int nperm[9]; static unsigned char perms[9][40320][8];
static void gen(int w) {           /* all arrangements of 0..w-1 */
    int n = 0, idx[8]; for (int i = 0; i < w; i++) idx[i] = i;
    for (;;) { for (int i = 0; i < w; i++) perms[w][n][i] = (unsigned char)idx[i]; n++;
        int i = w - 2; while (i >= 0 && idx[i] > idx[i + 1]) i--; if (i < 0) break;
        int j = w - 1; while (idx[j] < idx[i]) j--; int t = idx[i]; idx[i] = idx[j]; idx[j] = t;
        for (int a = i + 1, b = w - 1; a < b; a++, b--) { t = idx[a]; idx[a] = idx[b]; idx[b] = t; } }
    nperm[w] = n; }
/* successor of a with weight w by arrangement s: a[w:] + a[s[0]], ..., a[s[w-1]] */
static void succ(const unsigned char *a, int w, const unsigned char *s, unsigned char *b) { memcpy(b, a + w, 8 - w); for (int i = 0; i < w; i++) b[8 - w + i] = a[s[i]]; }
/* predecessor of a with weight w by arrangement s: a[8-w+s[0]], ... + a[:8-w] */
static void pred(const unsigned char *a, int w, const unsigned char *s, unsigned char *b) { for (int i = 0; i < w; i++) b[i] = a[8 - w + s[i]]; memcpy(b + w, a, 8 - w); }
int main(void) {
    for (int w = 1; w <= 8; w++) gen(w);
    unsigned char P1[8] = {0, 1, 2, 3, 4, 5, 6, 7}, T[8], X[8], Y[8];
    long checked = 0, viol = 0; int first = 1; printf("{\"cases\": [");
    for (int wi = 1; wi <= 5; wi++) for (int w1 = 1; w1 <= 7; w1++) for (int w2 = 1; w2 <= 7; w2++) {
        int mn = 99; long cnt = 0;
        for (int a = 0; a < nperm[wi]; a++) { pred(P1, wi, perms[wi][a], T); if (8 - ov(T, P1) != wi) continue;
            for (int b = 0; b < nperm[w1]; b++) { pred(P1, w1, perms[w1][b], X); if (8 - ov(X, P1) != w1) continue;
                for (int c = 0; c < nperm[w2]; c++) { succ(T, w2, perms[w2][c], Y); if (8 - ov(T, Y) != w2) continue;
                    if (!memcmp(X, Y, 8)) continue;           /* X = Y would be one permutation designated twice */
                    int w3 = 8 - ov(X, Y), ins = w1 + w2 - w3 - wi; cnt++; if (ins < mn) mn = ins;
                    if (w1 >= wi && w2 >= wi) { checked++; if (ins < 0) viol++; } } } }
        printf("%s{\"wi\": %d, \"w1\": %d, \"w2\": %d, \"configs\": %ld, \"min_ins\": %d, \"hypothesis\": %s}", first ? "" : ", ", wi, w1, w2, cnt, mn, (w1 >= wi && w2 >= wi) ? "true" : "false"); first = 0; }
    printf("], \"checked_under_hypothesis\": %ld, \"violations\": %ld}\n", checked, viol);
    return viol != 0; }
