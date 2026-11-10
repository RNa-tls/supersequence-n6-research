// Round S -- independent second implementation of the single-visit kappa searches of Round R
// (kappa_dfs.c / kappa_dfs2.c: exact tables for kappa <= B;  kappa_crit.c: undominated visits, kappa = 4, 5).
//
// Written from the mathematical statement, not from the Round R sources, and with the OPPOSITE search direction:
// a visit H = (y = r_1, r_2, ..., r_m = x) of one trail version (a Hamiltonian path of its m runs) is built BACKWARDS
// from its exit run x: the suffix r_i .. r_m is extended by prepending a whole w2 segment that ends at a run p with
// w(p, r_i) >= 3.
//     kappa(H) = sum over the joins (w - 2) - (K - 1) = (#maximal w2 segments - K) + sum over non-w2 joins (w - 3),
// K = number of chains (maximal w2 intervals of the version cycle); the w2 links are the natural w2 links and the wraps.
// Lower bound at a node (front run f = first run of the suffix, `cost` = kappa of the suffix counted with the chains
// touched so far):
//   (1) every maximal uncovered w2 interval of a TOUCHED chain needs a further segment of that chain: +1 each;
//   (2) exit-blocked units.  A unit is an untouched chain or an uncovered interval of a touched chain.  In H the last
//       run of a unit is followed by a join that leaves the unit and goes to f or to an uncovered run outside the unit.
//       If that join has weight 3 and leaves from an exit run of the unit (interval or path chain: its last run;
//       untouched full chain: any run, since a full chain may be rotated) it costs nothing; otherwise it costs >= 1
//       (weight >= 4, or the unit is left at another run and needs one more segment).  A unit none of whose exit runs
//       has a w3 link to an uncovered run outside the unit is BLOCKED and costs >= 1, except that f can receive the
//       join of one unit (f has one predecessor).
//   kappa(H) >= cost + (1) + #blocked - [f has a w3 in-link from an exit run of a blocked unit].
// Modes
//   exact  (no slack file):   table K[y][x] = least kappa <= B of a visit from y to x (99 = none), as kappa_dfs.c;
//   target (slack file S):    visits with kappa < S(y, x), kappa <= B.  Budget per exit run  B(x) = min(B, max_y S(y, x) - 1);
//                             a node with lower bound L is cut when no uncovered y has S(y, x) > L (the visit starts at
//                             an uncovered run and has kappa >= L).  Env SLACK_ADD, SKIP_BELOW as in kappa_crit.c.
// usage: kappa_rev DIR(runs.bin) TRAIL VERSION B OUT [X_FROM X_TO]         (env SLACK=path: target mode, OUT is json;
//                                                                            otherwise OUT is the m x m int8 table)
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#define NTR 30
#define MAXM 704
#define NWORD (MAXM / 64)
#define MAXB 7
static int mrun[NTR][2]; static uint8_t *runp[NTR][2];
static int ovw(const uint8_t *last, const uint8_t *first) { for (int s = 1; s < 8; s++) { int j = 0; while (s + j < 8 && last[s + j] == first[j]) j++; if (s + j == 8) return s; } return 8; }
static int m, B, nch;
static uint8_t W[MAXM][MAXM];
static int nxt2[MAXM], prv2[MAXM];          // w2 successor / predecessor (-1 if none)
static int ch[MAXM], chfull[MAXM], chlen[MAXM], chfirst[MAXM], chlast[MAXM], isexit0[MAXM];   // per run: chain id; per chain: data
static int *jin[MAXM], njin[MAXM];           // candidate predecessors p of a run f: 3 <= w(p, f) <= 3 + B
static int *o3[MAXM], no3[MAXM];             // w3 out-neighbours of a run in OTHER chains
static int *o3all[MAXM], no3all[MAXM];       // all w3 out-neighbours
typedef struct {
    uint64_t vis[NWORD]; int nvis;
    int seg[MAXM];                            // per chain: segments placed
    int cnto[MAXM];                           // per run: number of w3 out-links to uncovered runs of other chains
    int av[MAXM];                             // per chain: number of exit runs (untouched sense) with cnto > 0
    int nblk;                                 // untouched chains with av == 0
    int openc[MAXM], nopen, openpos[MAXM];    // touched chains that still have uncovered runs
    int ivcount[MAXM];                        // per chain: uncovered intervals (touched chains only)
    int startc[MAXB + 3];                     // number of uncovered y with S(y, x0) > t
    const int8_t *Scol;                       // Scol[y] = S(y, x0)
    int x0, Bx, sumiv;
    int8_t *K; long nodes, leaves, und; int8_t *U;
} St;
static inline int VIS(const St *s, int r) { return (int)(s->vis[r >> 6] >> (r & 63) & 1); }
static inline int exit_untouched(int r) { int c = ch[r]; return chfull[c] || r == chlast[c]; }
static void cover(St *s, int u) {
    s->vis[u >> 6] |= 1ull << (u & 63); s->nvis++;
    if (s->Scol) { int sv = s->Scol[u]; for (int t = 0; t < sv && t <= MAXB + 2; t++) s->startc[t]--; }
    // u is no longer an uncovered target: every run r with a w3 link r -> u (other chain) loses one
}
static int *i3[MAXM], ni3[MAXM];             // w3 in-neighbours of a run from OTHER chains
static void cover_counts(St *s, int u) {
    for (int i = 0; i < ni3[u]; i++) { int r = i3[u][i];
        if (--s->cnto[r] == 0 && exit_untouched(r)) { int c = ch[r]; if (--s->av[c] == 0 && s->seg[c] == 0) s->nblk++; } }
}
static void uncover_counts(St *s, int u) {
    for (int i = 0; i < ni3[u]; i++) { int r = i3[u][i];
        if (s->cnto[r]++ == 0 && exit_untouched(r)) { int c = ch[r]; if (s->av[c]++ == 0 && s->seg[c] == 0) s->nblk--; } }
}
static void uncover(St *s, int u) {
    s->vis[u >> 6] &= ~(1ull << (u & 63)); s->nvis--;
    if (s->Scol) { int sv = s->Scol[u]; for (int t = 0; t < sv && t <= MAXB + 2; t++) s->startc[t]++; }
}
// number of maximal uncovered w2 intervals of chain c (c touched)
static int count_iv(const St *s, int c) {
    int n = 0, r = chfirst[c];
    for (int k = 0; k < chlen[c]; k++, r = nxt2[r]) { if (VIS(s, r)) continue; int q = nxt2[r]; if (q < 0 || VIS(s, q)) n++; }
    return n;                                 // counted by their LAST runs (run uncovered, w2 successor covered or absent)
}
static void open_set(St *s, int c, int on) {
    int p = s->openpos[c];
    if (on && p < 0) { s->openpos[c] = s->nopen; s->openc[s->nopen++] = c; }
    else if (!on && p >= 0) { int l = s->openc[--s->nopen]; s->openc[p] = l; s->openpos[l] = p; s->openpos[c] = -1; }
}
// blocked intervals of the open chains; *resc = 1 if f can receive the join of some blocked unit
static int blocked_units(const St *s, int f, int *resc) {
    int nb = s->nblk, rs = 0;
    // untouched blocked chains that f rescues: an exit run of an untouched chain c with av[c] == 0 and a w3 link to f
    // intervals of open chains
    for (int oi = 0; oi < s->nopen; oi++) { int c = s->openc[oi]; int r = chfirst[c];
        for (int k = 0; k < chlen[c]; k++, r = nxt2[r]) { if (VIS(s, r)) continue; int q = nxt2[r]; if (!(q < 0 || VIS(s, q))) continue;
            // r is the last run of an interval; the interval is the set of uncovered runs reached backwards from r
            int ok = 0, tof = 0;
            for (int i = 0; i < no3all[r] && !ok; i++) { int t = o3all[r][i];
                if (t == f) { tof = 1; continue; }
                if (VIS(s, t)) continue;
                if (ch[t] == c) {            // same chain: allowed only if t is in a different interval
                    int z = r, same = 0; while (z >= 0 && !VIS(s, z)) { if (z == t) { same = 1; break; } z = prv2[z]; if (z == r) break; }
                    if (same) continue; }
                ok = 1; }
            if (!ok) { nb++; if (tof) rs = 1; } } }
    if (!rs && s->nblk > 0) {
        // does some exit run of a blocked untouched chain have a w3 link to f ?  (f's w3 in-neighbours)
        for (int i = 0; i < njin[f]; i++) { int p = jin[f][i]; if (W[p][f] != 3) break; if (VIS(s, p)) continue; int c = ch[p];
            if (s->seg[c] == 0 && s->av[c] == 0 && exit_untouched(p)) { rs = 1; break; } } }
    *resc = rs; return nb;
}
static void dfs(St *s, int f, int cost) {
    s->nodes++;
    if (s->nvis == m) { s->leaves++;
        if (s->K) { int8_t *k = &s->K[(size_t)f * m + s->x0]; if (cost < *k) *k = (int8_t)cost; }
        if (s->Scol && cost < s->Scol[f]) { s->und++; int8_t *k = &s->U[(size_t)f * m + s->x0]; if (cost < *k) *k = (int8_t)cost; }
        return; }
    int L = cost + s->sumiv; if (L > s->Bx) return;
    int resc; int nb = blocked_units(s, f, &resc); L += nb - resc; if (L > s->Bx) return;
    if (s->Scol && s->startc[L < 0 ? 0 : L] == 0) return;
    for (int i = 0; i < njin[f]; i++) { int p = jin[f][i]; if (VIS(s, p)) continue;
        int c = ch[p]; int d = W[p][f] - 3; int extra = s->seg[c] ? 1 : 0;
        if (cost + d + extra > s->Bx) continue;
        // the new segment: p, prv2(p), ... (all uncovered), every length
        int segr[8], len = 0, r = p;
        while (r >= 0 && !VIS(s, r) && len < 7) { segr[len++] = r; r = prv2[r]; if (r == p) break; }
        int was_touched = s->seg[c] > 0; int oldiv = was_touched ? s->ivcount[c] : 0;
        if (!was_touched && s->av[c] == 0) s->nblk--;         // c stops being an untouched (blocked) chain
        s->seg[c]++;
        for (int l = 0; l < len; l++) { int u = segr[l]; cover(s, u); cover_counts(s, u);
            int niv = count_iv(s, c); s->sumiv += niv - (l == 0 ? oldiv : s->ivcount[c]); s->ivcount[c] = niv; open_set(s, c, niv > 0);
            dfs(s, u, cost + d + extra); }
        // undo
        s->sumiv -= s->ivcount[c];
        for (int l = len - 1; l >= 0; l--) { uncover_counts(s, segr[l]); uncover(s, segr[l]); }
        s->seg[c]--;
        if (was_touched) { s->ivcount[c] = oldiv; s->sumiv += oldiv; open_set(s, c, oldiv > 0); }
        else { s->ivcount[c] = 0; open_set(s, c, 0); if (s->av[c] == 0) s->nblk++; }
    }
}
int main(int argc, char **argv) {
    if (argc < 6) { fprintf(stderr, "usage: kappa_rev DIR TRAIL VERSION B OUT [X_FROM X_TO]\n"); return 1; }
    int T0 = atoi(argv[2]), V0 = atoi(argv[3]); B = atoi(argv[4]); const char *outp = argv[5]; char p[2048];
    if (B > MAXB) return 1;
    snprintf(p, sizeof p, "%s/runs.bin", argv[1]); FILE *f = fopen(p, "rb"); if (!f) return 2;
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int32_t mm; if (fread(&mm, 4, 1, f) != 1) return 2; mrun[t][v] = mm; runp[t][v] = malloc(8 * mm); if (fread(runp[t][v], 1, 8 * mm, f) != (size_t)(8 * mm)) return 2; }
    fclose(f);
    m = mrun[T0][V0]; if (m > MAXM) return 4;
    int xf = argc > 7 ? atoi(argv[6]) : 0, xt = argc > 7 ? atoi(argv[7]) : m;
    const char *slp = getenv("SLACK"); int sadd = getenv("SLACK_ADD") ? atoi(getenv("SLACK_ADD")) : 0; int skip_below = getenv("SKIP_BELOW") ? atoi(getenv("SKIP_BELOW")) : 0;
    int8_t *S = NULL;
    if (slp) { S = malloc((size_t)m * m); FILE *fs = fopen(slp, "rb"); if (!fs || fread(S, 1, (size_t)m * m, fs) != (size_t)m * m) return 5; fclose(fs);
        for (size_t i = 0; i < (size_t)m * m; i++) if (S[i] > -100) S[i] = (int8_t)(S[i] + sadd); }
    // weights: last permutation of run i = (i_7, i_0, .., i_6)
    for (int i = 0; i < m; i++) { uint8_t la[8]; const uint8_t *a = runp[T0][V0] + 8 * i; la[0] = a[7]; for (int k = 1; k < 8; k++) la[k] = a[k - 1];
        for (int j = 0; j < m; j++) W[i][j] = i == j ? 99 : (uint8_t)ovw(la, runp[T0][V0] + 8 * j); }
    for (int i = 0; i < m; i++) nxt2[i] = prv2[i] = -1;
    for (int i = 0; i < m; i++) for (int j = 0; j < m; j++) if (W[i][j] == 2) { if (nxt2[i] >= 0 || prv2[j] >= 0) { fprintf(stderr, "w2 link not unique\n"); return 3; } nxt2[i] = j; prv2[j] = i; }
    // chains = components of the w2 graph (paths and 7-cycles)
    for (int i = 0; i < m; i++) ch[i] = -1; nch = 0;
    for (int i = 0; i < m; i++) { if (ch[i] >= 0) continue; int h = i, g = 0; while (prv2[h] >= 0 && prv2[h] != i && g++ < m) h = prv2[h];
        int cyc = prv2[h] >= 0; int c = nch++; chfull[c] = cyc; chfirst[c] = h; int x = h, len = 0, last = h;
        do { ch[x] = c; last = x; len++; x = nxt2[x]; } while (x >= 0 && x != h);
        chlen[c] = len; chlast[c] = last; }
    for (int fr = 0; fr < m; fr++) { jin[fr] = malloc(sizeof(int) * m); njin[fr] = 0;
        for (int w = 3; w <= 3 + B && w <= 8; w++) for (int q = 0; q < m; q++) if (q != fr && W[q][fr] == w) jin[fr][njin[fr]++] = q; }
    for (int r = 0; r < m; r++) { o3[r] = malloc(sizeof(int) * 16); o3all[r] = malloc(sizeof(int) * 16); i3[r] = malloc(sizeof(int) * 64); no3[r] = no3all[r] = ni3[r] = 0; }
    for (int r = 0; r < m; r++) for (int t = 0; t < m; t++) if (r != t && W[r][t] == 3) { if (no3all[r] >= 16) return 6; o3all[r][no3all[r]++] = t;
        if (ch[r] != ch[t]) { o3[r][no3[r]++] = t; if (ni3[t] >= 64) return 6; i3[t][ni3[t]++] = r; } }
    int *cnt0 = calloc(m, sizeof(int)), *av0 = calloc(nch, sizeof(int)); int nblk0 = 0;
    for (int r = 0; r < m; r++) cnt0[r] = no3[r];
    for (int r = 0; r < m; r++) if (cnt0[r] > 0 && exit_untouched(r)) av0[ch[r]]++;
    for (int c = 0; c < nch; c++) if (av0[c] == 0) nblk0++;
    int nthr = omp_get_max_threads(); St *st = calloc(nthr, sizeof(St));
    for (int t = 0; t < nthr; t++) { if (!S) { st[t].K = malloc((size_t)m * m); memset(st[t].K, 99, (size_t)m * m); } else { st[t].U = malloc((size_t)m * m); memset(st[t].U, 99, (size_t)m * m); } }
    long searched = 0, skipped = 0; long *nodes_x = calloc(m, sizeof(long)); double t0 = omp_get_wtime();
    fprintf(stderr, "trail %d v%d: m %d, chains %d (untouched blocked at start %d), exit runs [%d, %d), mode %s\n", T0, V0, m, nch, nblk0, xf, xt, S ? "target" : "exact");
    #pragma omp parallel for schedule(dynamic, 1) reduction(+:searched, skipped)
    for (int x0 = xf; x0 < xt; x0++) { St *s = &st[omp_get_thread_num()];
        int Bx = B; int8_t *col = NULL;
        if (S) { col = malloc(m); int smax = -100; for (int y = 0; y < m; y++) { col[y] = S[(size_t)y * m + x0]; if (col[y] > smax) smax = col[y]; }
            if (smax - 1 < Bx) Bx = smax - 1; if (Bx < 0 || Bx < skip_below) { skipped++; free(col); continue; } }
        searched++;
        memset(s->vis, 0, sizeof s->vis); s->nvis = 0; memset(s->seg, 0, sizeof(int) * nch); memcpy(s->cnto, cnt0, sizeof(int) * m); memcpy(s->av, av0, sizeof(int) * nch); s->nblk = nblk0;
        s->nopen = 0; for (int c = 0; c < nch; c++) { s->openpos[c] = -1; s->ivcount[c] = 0; } s->sumiv = 0; s->Scol = col; s->x0 = x0; s->Bx = Bx;
        if (col) for (int t = 0; t <= MAXB + 2; t++) { int n = 0; for (int y = 0; y < m; y++) if (col[y] > t) n++; s->startc[t] = n; }
        long before = s->nodes;
        // the last segment ends at x0: x0, prv2(x0), ...
        int c = ch[x0]; int segr[8], len = 0, r = x0; while (r >= 0 && len < 7) { segr[len++] = r; r = prv2[r]; if (r == x0) break; }
        if (s->av[c] == 0) s->nblk--;
        s->seg[c] = 1;
        for (int l = 0; l < len; l++) { int u = segr[l]; cover(s, u); cover_counts(s, u); int niv = count_iv(s, c); s->sumiv += niv - s->ivcount[c]; s->ivcount[c] = niv; open_set(s, c, niv > 0);
            dfs(s, u, 0); }
        nodes_x[x0] = s->nodes - before; if (col) free(col);
    }
    long nodes = 0, leaves = 0, und = 0; for (int t = 0; t < nthr; t++) { nodes += st[t].nodes; leaves += st[t].leaves; und += st[t].und; }
    if (getenv("NODES_OUT")) { FILE *fn = fopen(getenv("NODES_OUT"), "w"); for (int x = xf; x < xt; x++) fprintf(fn, "%d %ld\n", x, nodes_x[x]); fclose(fn); }
    if (!S) { int8_t *K = malloc((size_t)m * m); memset(K, 99, (size_t)m * m);
        for (int t = 0; t < nthr; t++) for (size_t i = 0; i < (size_t)m * m; i++) if (st[t].K[i] < K[i]) K[i] = st[t].K[i];
        FILE *fo = fopen(outp, "wb"); fwrite(K, 1, (size_t)m * m, fo); fclose(fo);
        long hist[MAXB + 1] = {0}, np = 0; for (size_t i = 0; i < (size_t)m * m; i++) if (K[i] <= B) { hist[K[i]]++; np++; }
        printf("{\"mode\": \"exact\", \"trail\": %d, \"version\": %d, \"B\": %d, \"x_range\": [%d, %d], \"pairs\": %ld, \"pairs_by_kappa\": [", T0, V0, B, xf, xt, np);
        for (int k = 0; k <= B; k++) printf("%s%ld", k ? ", " : "", hist[k]); printf("], \"complete_paths\": %ld, \"nodes\": %ld, \"sec\": %.1f}\n", leaves, nodes, omp_get_wtime() - t0); return 0; }
    int8_t *U = malloc((size_t)m * m); memset(U, 99, (size_t)m * m); for (int t = 0; t < nthr; t++) for (size_t i = 0; i < (size_t)m * m; i++) if (st[t].U[i] < U[i]) U[i] = st[t].U[i];
    FILE *fo = fopen(outp, "w"); long npairs = 0, byk[MAXB + 1] = {0}; int maxgain = -100;
    fprintf(fo, "{\"checker\": \"kappa_rev (backward search)\", \"trail\": %d, \"version\": %d, \"B\": %d, \"slack_add\": %d, \"x_range\": [%d, %d], \"undominated\": [", T0, V0, B, sadd, xf, xt);
    for (int y = 0; y < m; y++) for (int x = 0; x < m; x++) { int k = U[(size_t)y * m + x]; if (k == 99) continue; int g = S[(size_t)y * m + x] - k; if (g > maxgain) maxgain = g;
        fprintf(fo, "%s[%d, %d, %d, %d]", npairs ? ", " : "", y, x, k, g); npairs++; byk[k]++; }
    fprintf(fo, "], \"undominated_pairs\": %ld, \"undominated_pairs_by_kappa\": [", npairs); for (int k = 0; k <= B; k++) fprintf(fo, "%s%ld", k ? ", " : "", byk[k]);
    fprintf(fo, "], \"undominated_paths\": %ld, \"max_gain\": %d, \"exit_runs_searched\": %ld, \"exit_runs_skipped\": %ld, \"complete_paths_reached\": %ld, \"nodes\": %ld, \"sec\": %.1f}\n", und, npairs ? maxgain : 0, searched, skipped, leaves, nodes, omp_get_wtime() - t0); fclose(fo);
    printf("{\"mode\": \"target\", \"B\": %d, \"slack_add\": %d, \"x_range\": [%d, %d], \"undominated_pairs\": %ld, \"undominated_paths\": %ld, \"exit_runs_searched\": %ld, \"nodes\": %ld, \"sec\": %.1f}\n", B, sadd, xf, xt, npairs, und, searched, nodes, omp_get_wtime() - t0);
    return 0;
}
