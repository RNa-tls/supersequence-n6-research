// Round R, section 12 -- undominated A single visits with kappa <= B (target-aware form of kappa_dfs2.c).
// A visit H from entry run y to exit run x is UNDOMINATED iff kappa(H) < S(y, x), the effective slack of
// rQ/csrc/dominance.c (max over neighbour contexts, start and end contexts included, single pieces of both versions,
// DOM_BOTH = 1; written by rR/csrc/dominance_slack.c).  This program finds every undominated H with kappa(H) <= B:
// the same depth-first search and lower bound as kappa_dfs2.c, with two more prunings that only discard dominated
// visits:  budget per start run  B(y0) = min(B, max_x S(y0, x) - 1),  and at a node with lower bound L the path is
// cut when no uncovered run x has S(y0, x) > L (every completion ends at such an x with kappa >= L).
// Env SLACK_ADD=a adds a to every slack (planted test: with a = 1 the output must be exactly the pairs with
// least kappa = S(y, x), read off the exact kappa tables).
// Lower bound at a node (path ends at x, next join has w >= 3):
//   Hc      = sum over touched chains of their maximal uncovered w2 intervals (each needs one more paid segment);
//   units   = the untouched chains and the uncovered intervals of touched chains; every unit must be entered by a
//             join from outside the unit, and these entry joins are distinct.  A unit is BLOCKED if none of its
//             entry runs (untouched full chain: any run; untouched path chain and interval: its first run) has a w3
//             in-arc from an uncovered run outside the unit.  A blocked unit costs >= 1 more: its entry join has
//             w >= 4, or it is entered at a non-entry run (one more segment of its chain);
//   dx      = 1 if x has a w3 arc into an entry run of a blocked unit (x serves at most one unit).
//   kappa(H) >= cost + Hc + #blocked - dx.
// usage: kappa_crit DIR(runs.bin) TRAIL VERSION B SLACK.bin OUT.json [Y0_FROM Y0_TO]
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#define NTR 30
#define MW 11
#define MAXB 7
static int mrun[NTR][2]; static uint8_t *runp[NTR][2];
static int wgt(const uint8_t *x, const uint8_t *y) { for (int s = 1; s < 8; s++) { int ok = 1; for (int i = 0; s + i < 8; i++) if (x[s + i] != y[i]) { ok = 0; break; } if (ok) return s; } return 8; }
static int m, B; static uint8_t *W; static int *succ2, *pred2, *chainof, *chainlen, *isfull, nchain, *posin;
static int *tgt_off, *tgt;            // per run: candidate next entries with 3 <= w <= 3 + B
static int *in3_off, *in3;            // per run: w3 in-neighbours (any chain)
static int *out3x_off, *out3x;        // per run: w3 out-neighbours in OTHER chains (for cnt updates)
static int *crun, *crun_off;          // runs of every chain in w2 order
typedef struct { uint64_t v[MW]; } Set;
static inline int isv(const Set *s, int r) { return s->v[r >> 6] >> (r & 63) & 1; }
static inline void setv(Set *s, int r) { s->v[r >> 6] |= 1ull << (r & 63); }
static inline void clrv(Set *s, int r) { s->v[r >> 6] &= ~(1ull << (r & 63)); }
static inline int isentry_untouched(int r) { int c = chainof[r]; return isfull[c] || posin[r] == 0; }
typedef struct {
    int8_t *K; long paths[MAXB + 1]; long nodes;
    int *segs, *iv;                   // segments placed per chain, uncovered intervals per touched chain
    int *cnt;                         // per run: uncovered w3 in-neighbours in other chains
    int *avail;                       // per chain: entry runs with cnt > 0
    int nblkU;                        // untouched chains with avail == 0
    int *open, *openpos, nopen;       // touched chains with uncovered runs
    int *tmp;                         // per run scratch (interval ids)
    Set vis;
    int endc[MAXB + 2];               // endc[t] = uncovered runs x with S(y0, x) > t
    const int8_t *Sy;                 // slack row of the current y0
    int8_t *U;                        // least undominated kappa per (y0, x), 99 = none
    long und;                         // undominated paths found
} Ctx;
static void open_add(Ctx *C, int c) { if (C->openpos[c] >= 0) return; C->openpos[c] = C->nopen; C->open[C->nopen++] = c; }
static void open_del(Ctx *C, int c) { int p = C->openpos[c]; if (p < 0) return; int l = C->open[--C->nopen]; C->open[p] = l; C->openpos[l] = p; C->openpos[c] = -1; }
// cover / uncover one run: update cnt, avail, nblkU
static void cover(Ctx *C, int u) {
    setv(&C->vis, u); { int sv = C->Sy[u]; for (int t = 0; t <= MAXB + 1 && t < sv; t++) C->endc[t]--; }
    for (int i = out3x_off[u]; i < out3x_off[u + 1]; i++) { int r = out3x[i];
        if (--C->cnt[r] == 0 && isentry_untouched(r)) { int c = chainof[r]; if (--C->avail[c] == 0 && C->segs[c] == 0) C->nblkU++; } }
}
static void uncover(Ctx *C, int u) {
    for (int i = out3x_off[u]; i < out3x_off[u + 1]; i++) { int r = out3x[i];
        if (C->cnt[r]++ == 0 && isentry_untouched(r)) { int c = chainof[r]; if (C->avail[c]++ == 0 && C->segs[c] == 0) C->nblkU--; } }
    clrv(&C->vis, u); { int sv = C->Sy[u]; for (int t = 0; t <= MAXB + 1 && t < sv; t++) C->endc[t]++; }
}
static void touch(Ctx *C, int c) { if (C->segs[c]++ == 0 && C->avail[c] == 0) C->nblkU--; }
static void untouch(Ctx *C, int c) { if (--C->segs[c] == 0 && C->avail[c] == 0) C->nblkU++; }
static int intervals(const Set *vis, int c) {
    int cnt = 0, L = chainlen[c]; const int *rr = crun + crun_off[c];
    for (int k = 0; k < L; k++) { int r = rr[k]; if (isv(vis, r)) continue; int p = pred2[r]; if (p < 0 || isv(vis, p)) cnt++; }
    return cnt;    // a touched chain has a covered run, so a full chain never counts as one uncovered cycle here
}
// blocked intervals of open chains, and whether x rescues one blocked unit
static int blocked_bound(Ctx *C, int x) {
    int nb = C->nblkU, rescue = 0;
    for (int oi = 0; oi < C->nopen; oi++) { int c = C->open[oi], L = chainlen[c]; const int *rr = crun + crun_off[c];
        // assign interval ids along the w2 order: start at a run whose pred2 is covered (or absent)
        for (int k = 0; k < L; k++) C->tmp[rr[k]] = -1;
        int id = 0;
        for (int k = 0; k < L; k++) { int r = rr[k]; if (isv(&C->vis, r)) continue; int p = pred2[r]; if (!(p < 0 || isv(&C->vis, p))) continue;
            for (int q = r; q >= 0 && !isv(&C->vis, q) && C->tmp[q] < 0; q = succ2[q]) C->tmp[q] = id;
            id++; }
        for (int k = 0; k < L; k++) { int f = rr[k]; if (isv(&C->vis, f)) continue; int p = pred2[f]; if (!(p < 0 || isv(&C->vis, p))) continue;
            int ok = 0;
            for (int i = in3_off[f]; i < in3_off[f + 1] && !ok; i++) { int u = in3[i]; if (isv(&C->vis, u)) continue; if (chainof[u] == c && C->tmp[u] == C->tmp[f]) continue; ok = 1; }
            if (!ok) { nb++; if (!rescue && W[(size_t)x * m + f] == 3) rescue = 1; } }
    }
    if (!rescue) for (int i = tgt_off[x]; i < tgt_off[x + 1]; i++) { int r = tgt[i]; if (W[(size_t)x * m + r] != 3) continue; if (isv(&C->vis, r)) continue;
        int c = chainof[r]; if (C->segs[c] == 0 && C->avail[c] == 0 && isentry_untouched(r)) { rescue = 1; break; } }
    return nb - rescue;
}
static void dfs(Ctx *C, int x, int nvis, int cost, int y0, int Hc, int Bv) {
    C->nodes++;
    if (nvis == m) { C->paths[cost]++; if (cost < C->Sy[x]) { int8_t *k = &C->U[(size_t)y0 * m + x]; if (cost < *k) *k = (int8_t)cost; C->und++; } return; }
    if (cost + Hc > Bv) return;
    int L = cost + Hc + blocked_bound(C, x); if (L > Bv) return;
    if (L < 0) L = 0;
    if (C->endc[L] == 0) return;
    for (int ti = tgt_off[x]; ti < tgt_off[x + 1]; ti++) { int y = tgt[ti]; if (isv(&C->vis, y)) continue;
        int d = W[(size_t)x * m + y] - 3; int c = chainof[y]; int s = C->segs[c] ? 1 : 0;
        if (cost + d + s > Bv) continue;
        int path[8], L = 0, r = y;
        while (r >= 0 && !isv(&C->vis, r) && L < 8) { path[L++] = r; r = succ2[r]; if (r == y) break; }
        int old = C->segs[c] ? C->iv[c] : 0; int keep = C->iv[c];
        touch(C, c);
        for (int l = 1; l <= L; l++) { cover(C, path[l - 1]);
            int nw = intervals(&C->vis, c); C->iv[c] = nw; if (nw > 0) open_add(C, c); else open_del(C, c);
            dfs(C, path[l - 1], nvis + l, cost + d + s, y0, Hc - old + nw, Bv); }
        for (int l = L - 1; l >= 0; l--) uncover(C, path[l]);
        untouch(C, c); C->iv[c] = keep; if (C->segs[c] && keep > 0) open_add(C, c); else open_del(C, c);
    }
}
int main(int argc, char **argv) {
    if (argc < 7) { fprintf(stderr, "usage: kappa_crit DIR TRAIL VERSION B SLACK.bin OUT.json [Y0_FROM Y0_TO]\n"); return 1; }
    const char *dir = argv[1]; int T0 = atoi(argv[2]), V0 = atoi(argv[3]); B = atoi(argv[4]); const char *slp = argv[5]; const char *outp = argv[6]; char p[2048];
    int sadd = getenv("SLACK_ADD") ? atoi(getenv("SLACK_ADD")) : 0;
    if (B > MAXB) return 1;
    snprintf(p, sizeof p, "%s/runs.bin", dir); FILE *f = fopen(p, "rb"); if (!f) return 2;
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int32_t mm; if (fread(&mm, 4, 1, f) != 1) return 2; mrun[t][v] = mm; runp[t][v] = malloc(8 * mm); if (fread(runp[t][v], 1, 8 * mm, f) != (size_t)(8 * mm)) return 2; }
    fclose(f);
    m = mrun[T0][V0]; if (m > 64 * MW) return 4;
    int yf = argc > 8 ? atoi(argv[7]) : 0, yt = argc > 8 ? atoi(argv[8]) : m;
    int8_t *S = malloc((size_t)m * m); { FILE *fs = fopen(slp, "rb"); if (!fs || fread(S, 1, (size_t)m * m, fs) != (size_t)m * m) return 5; fclose(fs); }
    for (size_t i = 0; i < (size_t)m * m; i++) if (S[i] > -100) S[i] = (int8_t)(S[i] + sadd);
    uint8_t (*first)[8] = malloc(8 * m), (*last)[8] = malloc(8 * m);
    for (int k = 0; k < m; k++) { memcpy(first[k], runp[T0][V0] + 8 * k, 8); last[k][0] = first[k][7]; for (int i = 1; i < 8; i++) last[k][i] = first[k][i - 1]; }
    W = malloc((size_t)m * m); for (int i = 0; i < m; i++) for (int j = 0; j < m; j++) W[(size_t)i * m + j] = i == j ? 99 : wgt(last[i], first[j]);
    succ2 = malloc(4 * m); pred2 = malloc(4 * m); for (int i = 0; i < m; i++) succ2[i] = pred2[i] = -1;
    for (int i = 0; i < m; i++) for (int j = 0; j < m; j++) if (i != j && W[(size_t)i * m + j] == 2) { if (succ2[i] >= 0 || pred2[j] >= 0) { fprintf(stderr, "w2 not unique\n"); return 3; } succ2[i] = j; pred2[j] = i; }
    chainof = malloc(4 * m); for (int i = 0; i < m; i++) chainof[i] = -1; chainlen = calloc(m, 4); isfull = calloc(m, 4); nchain = 0; posin = malloc(4 * m);
    crun = malloc(4 * m); crun_off = malloc(4 * (m + 1)); int nr = 0;
    for (int i = 0; i < m; i++) { if (chainof[i] >= 0) continue; int h = i, guard = 0; while (pred2[h] >= 0 && pred2[h] != i && guard++ < m) h = pred2[h];
        int cyc = pred2[h] >= 0; crun_off[nchain] = nr; int x = h, L = 0; do { chainof[x] = nchain; posin[x] = L; crun[nr++] = x; L++; x = succ2[x]; } while (x >= 0 && x != h);
        chainlen[nchain] = L; isfull[nchain] = cyc; nchain++; }
    crun_off[nchain] = nr;
    tgt_off = malloc(4 * (m + 1)); tgt = malloc(4 * (size_t)m * m); int nt = 0;
    for (int i = 0; i < m; i++) { tgt_off[i] = nt; for (int w = 3; w <= 3 + B && w <= 8; w++) for (int j = 0; j < m; j++) if (j != i && W[(size_t)i * m + j] == w) tgt[nt++] = j; } tgt_off[m] = nt;
    in3_off = malloc(4 * (m + 1)); in3 = malloc(4 * (size_t)m * m); nt = 0;
    for (int j = 0; j < m; j++) { in3_off[j] = nt; for (int i = 0; i < m; i++) if (i != j && W[(size_t)i * m + j] == 3) in3[nt++] = i; } in3_off[m] = nt;
    out3x_off = malloc(4 * (m + 1)); out3x = malloc(4 * (size_t)m * m); nt = 0;
    for (int i = 0; i < m; i++) { out3x_off[i] = nt; for (int j = 0; j < m; j++) if (j != i && W[(size_t)i * m + j] == 3 && chainof[j] != chainof[i]) out3x[nt++] = j; } out3x_off[m] = nt;
    // initial counters (all runs uncovered)
    int *cnt0 = calloc(m, 4), *avail0 = calloc(nchain, 4), nblk0 = 0;
    for (int i = 0; i < m; i++) for (int k = out3x_off[i]; k < out3x_off[i + 1]; k++) cnt0[out3x[k]]++;
    for (int r = 0; r < m; r++) if (cnt0[r] > 0 && isentry_untouched(r)) avail0[chainof[r]]++;
    for (int c = 0; c < nchain; c++) if (avail0[c] == 0) nblk0++;
    int nthr = omp_get_max_threads(); Ctx *ctx = calloc(nthr, sizeof(Ctx));
    for (int t = 0; t < nthr; t++) { Ctx *C = &ctx[t]; C->K = malloc((size_t)m * m); memset(C->K, 99, (size_t)m * m);
        C->segs = calloc(nchain, 4); C->iv = calloc(nchain, 4); C->cnt = malloc(4 * m); C->avail = malloc(4 * nchain);
        C->open = malloc(4 * nchain); C->openpos = malloc(4 * nchain); C->tmp = malloc(4 * m);
        C->U = malloc((size_t)m * m); memset(C->U, 99, (size_t)m * m); }
    long y0_run = 0, y0_skip = 0; long *ny0 = calloc(m, sizeof(long));   // nodes per start run (env NODES_OUT)
    fprintf(stderr, "trail %d v%d: m %d, chains %d, untouched chains blocked at start %d, y0 in [%d, %d)\n", T0, V0, m, nchain, nblk0, yf, yt);
    double t0 = omp_get_wtime();
    #pragma omp parallel for schedule(dynamic, 1) reduction(+:y0_run, y0_skip)
    for (int y0 = yf; y0 < yt; y0++) {
        Ctx *C = &ctx[omp_get_thread_num()];
        int smax = -100; for (int x = 0; x < m; x++) if (S[(size_t)y0 * m + x] > smax) smax = S[(size_t)y0 * m + x];
        int Bv = smax - 1 < B ? smax - 1 : B; if (Bv < 0) { y0_skip++; continue; } y0_run++;
        C->Sy = S + (size_t)y0 * m; for (int t = 0; t <= MAXB + 1; t++) { int n = 0; for (int x = 0; x < m; x++) if (C->Sy[x] > t) n++; C->endc[t] = n; }
        long nodes_before = C->nodes;
        memset(&C->vis, 0, sizeof C->vis); memcpy(C->cnt, cnt0, 4 * m); memcpy(C->avail, avail0, 4 * nchain); C->nblkU = nblk0;
        memset(C->segs, 0, 4 * nchain); memset(C->iv, 0, 4 * nchain); for (int c = 0; c < nchain; c++) C->openpos[c] = -1; C->nopen = 0;
        int c = chainof[y0]; int path[8], L = 0, r = y0;
        while (r >= 0 && L < 8) { path[L++] = r; r = succ2[r]; if (r == y0) break; }
        touch(C, c);
        for (int l = 1; l <= L; l++) { cover(C, path[l - 1]); int nw = intervals(&C->vis, c); C->iv[c] = nw; if (nw > 0) open_add(C, c); else open_del(C, c);
            dfs(C, path[l - 1], l, 0, y0, nw, Bv); }
        for (int l = L - 1; l >= 0; l--) uncover(C, path[l]);
        untouch(C, c); open_del(C, c); C->iv[c] = 0;
        ny0[y0] = C->nodes - nodes_before;
    }
    if (getenv("NODES_OUT")) { FILE *fn = fopen(getenv("NODES_OUT"), "w"); for (int y = yf; y < yt; y++) fprintf(fn, "%d %ld\n", y, ny0[y]); fclose(fn); }
    int8_t *U = malloc((size_t)m * m); memset(U, 99, (size_t)m * m); long nodes = 0, und = 0, leaves = 0;
    for (int t = 0; t < nthr; t++) { for (size_t i = 0; i < (size_t)m * m; i++) if (ctx[t].U[i] < U[i]) U[i] = ctx[t].U[i]; nodes += ctx[t].nodes; und += ctx[t].und; for (int k = 0; k <= MAXB; k++) leaves += ctx[t].paths[k]; }
    long npairs = 0, byk[MAXB + 1] = {0}; int maxgain = -100;
    f = fopen(outp, "w"); fprintf(f, "{\"trail\": %d, \"version\": %d, \"B\": %d, \"slack_add\": %d, \"y0_range\": [%d, %d], \"undominated\": [", T0, V0, B, sadd, yf, yt);
    for (int y = 0; y < m; y++) for (int x = 0; x < m; x++) { int k = U[(size_t)y * m + x]; if (k == 99) continue; int g = S[(size_t)y * m + x] - k; if (g > maxgain) maxgain = g;
        fprintf(f, "%s[%d, %d, %d, %d]", npairs ? ", " : "", y, x, k, g); npairs++; byk[k]++; }
    fprintf(f, "], \"undominated_pairs\": %ld, \"undominated_pairs_by_kappa\": [", npairs); for (int k = 0; k <= B; k++) fprintf(f, "%s%ld", k ? ", " : "", byk[k]);
    fprintf(f, "], \"undominated_paths\": %ld, \"max_gain\": %d, \"start_runs_searched\": %ld, \"start_runs_skipped\": %ld, \"complete_paths_reached\": %ld, \"nodes\": %ld, \"sec\": %.1f}\n",
            und, npairs ? maxgain : 0, y0_run, y0_skip, leaves, nodes, omp_get_wtime() - t0); fclose(f);
    printf("{\"B\": %d, \"slack_add\": %d, \"y0_range\": [%d, %d], \"undominated_pairs\": %ld, \"undominated_paths\": %ld, \"start_runs_searched\": %ld, \"nodes\": %ld, \"sec\": %.1f}\n", B, sadd, yf, yt, npairs, und, y0_run, nodes, omp_get_wtime() - t0);
    return 0;
}
