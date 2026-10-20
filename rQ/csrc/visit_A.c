// Round Q, section 4 -- exact low-kappa single-visit catalog of one trail-version (written for the 672-run A trails;
// works for any trail).  kappa(y, x) = min over Hamiltonian paths of the trail's runs from y to x of
//   sum_{joins} (w - 2) - (k_T - 1)  =  sum_{non-w2 joins} (w - 3) + (#w2-segments - #chains).
// Search: DFS over paths in increasing order, f = g + h, g = sum (w - 2) so far, h = number of w2-components of the
// unvisited runs minus [w2 successor of the current run unvisited] (each such component needs an entering join of
// cost >= 1).  Paths with f > (k_T - 1) + KMAX are cut.  Memo: (current run, visited set) -> least g seen.
// Output: OUT = m x m int8: kappa (<= KMAX) or 99; -1 on the diagonal.  Prints the kappa histogram.
// usage: visit_A DIR(runs.bin) TRAIL VERSION KMAX OUT.bin [YFROM YTO]
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#define NTR 30
#define MW 11
static int mrun[NTR][2]; static uint8_t *runp[NTR][2];
static int wgt(const uint8_t *x, const uint8_t *y) { for (int s = 1; s < 8; s++) { int ok = 1; for (int i = 0; s + i < 8; i++) if (x[s + i] != y[i]) { ok = 0; break; } if (ok) return s; } return 8; }
static int m, kT, KMAX, BUD; static uint8_t *W; static int *succ2, *pred2, *chainof, *chainlen, *isfull; static int nchain;
static int *tgt_off, *tgt; // per run: targets sorted by w (non-w2 arcs), w <= 3 + KMAX + 1
typedef struct { uint64_t v[MW]; } Set;
// memo: open addressing hash of (cur, set) -> least g
typedef struct { uint64_t key[MW]; int cur; int g; } Ent;
typedef struct { Ent *t; size_t cap, n; } Memo;
static uint64_t hset(const Set *s, int cur) { uint64_t h = 1469598103934665603ull ^ (uint64_t)cur * 0x9E3779B97F4A7C15ull; for (int i = 0; i < MW; i++) { h ^= s->v[i]; h *= 1099511628211ull; h ^= h >> 29; } return h; }
static int memo_check(Memo *M, const Set *s, int cur, int g) {   // returns 1 if (cur, s) already seen with <= g; else records
    if (2 * (M->n + 1) > M->cap) { size_t nc = M->cap * 2; Ent *nt = calloc(nc, sizeof(Ent)); for (size_t i = 0; i < nc; i++) nt[i].cur = -1;
        for (size_t i = 0; i < M->cap; i++) if (M->t[i].cur >= 0) { Set q; memcpy(q.v, M->t[i].key, sizeof q.v); size_t h = hset(&q, M->t[i].cur) & (nc - 1); while (nt[h].cur >= 0) h = (h + 1) & (nc - 1); nt[h] = M->t[i]; }
        free(M->t); M->t = nt; M->cap = nc; }
    size_t h = hset(s, cur) & (M->cap - 1);
    while (M->t[h].cur >= 0) { if (M->t[h].cur == cur && !memcmp(M->t[h].key, s->v, sizeof s->v)) { if (M->t[h].g <= g) return 1; M->t[h].g = g; return 0; } h = (h + 1) & (M->cap - 1); }
    M->t[h].cur = cur; memcpy(M->t[h].key, s->v, sizeof s->v); M->t[h].g = g; M->n++; return 0;
}
static inline int isv(const Set *s, int r) { return s->v[r >> 6] >> (r & 63) & 1; }
static inline void setv(Set *s, int r) { s->v[r >> 6] |= 1ull << (r & 63); }
typedef struct { Memo M; int *best; long nodes; } Ctx;
// comps: number of w2-components among unvisited runs; unvis_in_chain[c] tracks fully-unvisited full chains (cycles)
static void dfs(Ctx *C, int cur, Set *vis, int nvis, int g, int comps, int *uc) {
    C->nodes++;
    if (nvis == m) { if (g < C->best[cur]) C->best[cur] = g; return; }
    int s = succ2[cur]; int sfree = (s >= 0 && !isv(vis, s));
    int h = comps - sfree; if (g + h > BUD) return;
    if (memo_check(&C->M, vis, cur, g)) return;
    // candidate next runs: the w2 successor (cost 0) and the listed non-w2 targets
    for (int ti = -1; ti < tgt_off[cur + 1] - tgt_off[cur]; ti++) {
        int r = ti < 0 ? s : tgt[tgt_off[cur] + ti]; if (r < 0 || isv(vis, r)) continue;
        int c = ti < 0 ? 0 : W[(size_t)cur * m + r] - 2; if (ti >= 0 && r == s) continue;
        // update components when visiting r
        int a = pred2[r], b = succ2[r]; int au = a >= 0 && !isv(vis, a), bu = b >= 0 && !isv(vis, b); int nc = comps;
        int ch = chainof[r]; int cyc = isfull[ch] && uc[ch] == chainlen[ch];
        if (cyc) nc += 0;                         // cycle -> path (or single run removed from a 1-cycle: impossible)
        else if (!au && !bu) nc -= 1;
        else if (au && bu) nc += 1;
        if (g + c + (nc - ((succ2[r] >= 0 && !isv(vis, succ2[r])) ? 1 : 0)) > BUD) continue;
        setv(vis, r); uc[ch]--;
        dfs(C, r, vis, nvis + 1, g + c, nc, uc);
        vis->v[r >> 6] &= ~(1ull << (r & 63)); uc[ch]++;
    }
}
int main(int argc, char **argv) {
    const char *dir = argv[1]; int T0 = atoi(argv[2]), V0 = atoi(argv[3]); KMAX = atoi(argv[4]); const char *outp = argv[5]; char p[2048];
    snprintf(p, sizeof p, "%s/runs.bin", dir); FILE *f = fopen(p, "rb"); if (!f) return 2;
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int32_t mm; if (fread(&mm, 4, 1, f) != 1) return 2; mrun[t][v] = mm; runp[t][v] = malloc(8 * mm); if (fread(runp[t][v], 1, 8 * mm, f) != (size_t)(8 * mm)) return 2; }
    fclose(f);
    m = mrun[T0][V0]; if (m > 64 * MW) return 4;
    int y0 = argc > 7 ? atoi(argv[6]) : 0, y1 = argc > 7 ? atoi(argv[7]) : m;
    uint8_t (*first)[8] = malloc(8 * m), (*last)[8] = malloc(8 * m);
    for (int k = 0; k < m; k++) { memcpy(first[k], runp[T0][V0] + 8 * k, 8); last[k][0] = first[k][7]; for (int i = 1; i < 8; i++) last[k][i] = first[k][i - 1]; }
    W = malloc((size_t)m * m); for (int i = 0; i < m; i++) for (int j = 0; j < m; j++) W[(size_t)i * m + j] = i == j ? 99 : wgt(last[i], first[j]);
    succ2 = malloc(4 * m); pred2 = malloc(4 * m); for (int i = 0; i < m; i++) succ2[i] = pred2[i] = -1;
    for (int i = 0; i < m; i++) for (int j = 0; j < m; j++) if (i != j && W[(size_t)i * m + j] == 2) { if (succ2[i] >= 0 || pred2[j] >= 0) { fprintf(stderr, "w2 not unique\n"); return 3; } succ2[i] = j; pred2[j] = i; }
    kT = 0; for (int k = 0; k < m; k++) if (W[(size_t)((k + m - 1) % m) * m + k] == 3) kT++;
    // chains = w2-components of the run graph (cycles: full chains; paths: short chains)
    chainof = malloc(4 * m); for (int i = 0; i < m; i++) chainof[i] = -1; chainlen = calloc(m, 4); isfull = calloc(m, 4); nchain = 0;
    for (int i = 0; i < m; i++) { if (chainof[i] >= 0) continue; int h = i, guard = 0; while (pred2[h] >= 0 && pred2[h] != i && guard++ < m) h = pred2[h];
        int cyc = pred2[h] >= 0; int x = h, L = 0; do { chainof[x] = nchain; L++; x = succ2[x]; } while (x >= 0 && x != h); chainlen[nchain] = L; isfull[nchain] = cyc; nchain++; }
    BUD = (kT - 1) + KMAX;
    // targets: non-w2 arcs with w <= 3 + KMAX (an arc of weight w adds w - 3 to kappa beyond the 1 per component)
    tgt_off = malloc(4 * (m + 1)); tgt = malloc(4 * (size_t)m * m); int nt = 0;
    for (int i = 0; i < m; i++) { tgt_off[i] = nt; for (int w = 3; w <= 3 + KMAX && w <= 8; w++) for (int j = 0; j < m; j++) if (j != i && W[(size_t)i * m + j] == w) tgt[nt++] = j; } tgt_off[m] = nt;
    fprintf(stderr, "trail %d v%d: runs %d, chains %d (k_T %d), targets %d\n", T0, V0, m, nchain, kT, nt);
    int8_t *K = malloc((size_t)m * m); memset(K, 99, (size_t)m * m); for (int i = 0; i < m; i++) K[(size_t)i * m + i] = -1;
    long totnodes = 0; double t0 = omp_get_wtime();
    #pragma omp parallel for schedule(dynamic, 1) reduction(+:totnodes)
    for (int y = y0; y < y1; y++) {
        Ctx C; C.M.cap = 1 << 16; C.M.n = 0; C.M.t = calloc(C.M.cap, sizeof(Ent)); for (size_t i = 0; i < C.M.cap; i++) C.M.t[i].cur = -1;
        C.best = malloc(4 * m); for (int x = 0; x < m; x++) C.best[x] = 1 << 20; C.nodes = 0;
        Set vis; memset(&vis, 0, sizeof vis); setv(&vis, y); int *uc = malloc(4 * nchain); for (int c = 0; c < nchain; c++) uc[c] = chainlen[c];
        int ch = chainof[y]; int comps = nchain;
        if (!isfull[ch]) { int a = pred2[y], b = succ2[y]; if (a >= 0 && b >= 0) comps += 1; else if (a < 0 && b < 0) comps -= 1; }
        uc[ch]--;
        dfs(&C, y, &vis, 1, 0, comps, uc);
        for (int x = 0; x < m; x++) if (x != y && C.best[x] < (1 << 20)) { int kap = C.best[x] - (kT - 1); K[(size_t)y * m + x] = kap <= KMAX ? kap : 99; }
        totnodes += C.nodes;
        if (y % 64 == 0) fprintf(stderr, "y %d done, nodes %ld, memo %zu, %.1fs\n", y, C.nodes, C.M.n, omp_get_wtime() - t0);
        free(C.M.t); free(C.best); free(uc);
    }
    FILE *fo = fopen(outp, "wb"); fwrite(K, 1, (size_t)m * m, fo); fclose(fo);
    long hist[8] = {0}; for (int y = y0; y < y1; y++) for (int x = 0; x < m; x++) { int k = K[(size_t)y * m + x]; if (k >= 0 && k <= KMAX) hist[k]++; }
    printf("{\"trail\": %d, \"version\": %d, \"KMAX\": %d, \"y_range\": [%d, %d], \"nodes\": %ld, \"kappa_hist\": [", T0, V0, KMAX, y0, y1, totnodes);
    for (int k = 0; k <= KMAX; k++) printf("%s%ld", k ? ", " : "", hist[k]); printf("], \"sec\": %.1f}\n", omp_get_wtime() - t0);
    return 0;
}
