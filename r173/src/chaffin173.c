/* Round 173 -- independent implementation of Chaffin's method (NOT derived from
 * the archive's ChaffinMethod.c).  UNCONDITIONAL: uses no lemma of this project.
 *
 * f(w) = max number of distinct permutations visited by a string over {1..n}
 *        with at most w wasted windows (window = length-n substring; a window is
 *        wasted if it is not a permutation or repeats an earlier one).
 * A string with q distinct permutations and w wasted windows has length
 * q + w + n - 1, so  L_n = n! + n - 1 + min{ w : f(w) = n! }.
 *
 * WLOG the string starts with 12..n (relabel symbols).  With no waste the only
 * extension is the sigma-rotation, so every string begins with the forced
 * zero-waste run.  Pruning: right after a window that is a NEW permutation, with
 * u wasted windows used so far, the rest of the string (which starts at that
 * window) has at most w-u wasted windows and therefore visits at most f(w-u)
 * permutations, one of which is the current window:
 *        p_final <= p + f(w-u) - 1.
 * f(w-u) is known because u >= 1 at every such point after the forced run
 * (for u = 0 the string is the forced run itself and p <= n = f(0)).
 *
 * usage: chaffin173 n wmax
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int n, NF, W, target, best;
static int fw[4096];
static int permidx[1 << 21];        /* window code (base n) -> perm index or -1 */
static unsigned char visited[5040];
static int str[20000];
static long long nodes;

static int code_of(const int *s) { int c = 0; for (int i = 0; i < n; i++) c = c * n + s[i]; return c; }

static void build_table(void) {
    int total = 1; for (int i = 0; i < n; i++) total *= n;
    int k = 0, s[16];
    for (int c = 0; c < total; c++) {
        int x = c, used = 0, ok = 1;
        for (int i = n - 1; i >= 0; i--) { s[i] = x % n; x /= n; }
        for (int i = 0; i < n; i++) { if (used >> s[i] & 1) { ok = 0; break; } used |= 1 << s[i]; }
        permidx[c] = ok ? k++ : -1;
    }
    NF = k;
}

/* len = current string length; p = distinct perms; u = wasted windows used */
static int dfs(int len, int p, int u) {
    nodes++;
    if (p > best) best = p;
    if (best >= target) return 1;
    for (int c = 0; c < n; c++) {
        str[len] = c;
        int idx = permidx[code_of(&str[len + 1 - n])];
        if (idx >= 0 && !visited[idx]) {
            /* new permutation */
            if (u >= 1 && p + 1 + fw[W - u] - 1 < target) continue;
            visited[idx] = 1;
            int r = dfs(len + 1, p + 1, u);
            visited[idx] = 0;
            if (r) return 1;
        } else {
            if (u + 1 > W) continue;
            /* a wasted window: the continuation must eventually reach a new
               permutation; bound after the waste: at most f(W-u-1)+? handled at
               the next new permutation.  Cheap check: even visiting a new perm
               at every later window cannot exceed p + f(W-(u+1)). */
            if (p + fw[W - (u + 1)] < target) continue;
            int r = dfs(len + 1, p, u + 1);
            if (r) return 1;
        }
    }
    return 0;
}

int main(int argc, char **argv) {
    n = atoi(argv[1]);
    int wmax = atoi(argv[2]);
    build_table();
    fw[0] = n;
    printf("w\tf(w)\tnodes\n0\t%d\t0\n", n);
    for (W = 1; W <= wmax; W++) {
        /* f(W) >= f(W-1); search upward for the largest attainable target */
        best = fw[W - 1];
        int got = fw[W - 1];
        for (target = fw[W - 1] + 1; target <= NF; target++) {
            memset(visited, 0, sizeof visited);
            for (int i = 0; i < n; i++) str[i] = i;
            visited[permidx[code_of(str)]] = 1;
            best = 1;
            nodes = 0;
            if (!dfs(n, 1, 0)) break;
            got = target;
        }
        fw[W] = got;
        printf("%d\t%d\t%lld\n", W, got, nodes);
        fflush(stdout);
        if (got == NF) {
            printf("# L_%d = %d! + %d - 1 + %d = %d\n", n, n, n, W, NF + n - 1 + W);
            break;
        }
    }
    return 0;
}
