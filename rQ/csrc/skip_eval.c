// Round Q, section 6.5 -- exact evaluation of the "skip" family on the junction patterns of ckT_search.c (THR = 20).
// One trail T is cut at u, alpha, beta (cyclic order u -> alpha -> beta -> u, same version) and visited twice:
//   the 2-piece visit [u, alpha) + jump (alpha-1 -> beta) + [beta, u)  acts as option T(u) (entry u, exit u-1),
//   the skipped piece [alpha, beta) (entry option T(alpha), exit option T(beta)) sits between SIGMA_j and SIGMA_{j+1}.
//   G = 1 + E' + F_J + e(o_j -> T(alpha)) + e(T(beta) -> o_{j+1}),  E' = w(last r_{alpha-1}, r_beta) - c_beta >= -1.
// E' = -1 is the wrap (rotated-chain excision, excise_eval.c); here every E' >= 0 is evaluated.  T adjacent to the
// junction gives one 3-piece visit (dominated, kappa3.c); the skipped piece at a word end gives G >= F >= 22.
// Every member with G <= THRG has F_J <= THRG - 1, so it lies in the patterns of the junction search with THR = THRG - 1.
// For every pattern sequence, every trail T not adjacent to the junction and every anchor option u: exact minimum over
// all other options and over all (alpha, beta) with E' >= 0 (dynamic programming, pruned only by exact bounds).
// Rebuilds options and e from runs.bin (no shared code with the search).  Exact pruning: a member with T at position s
// in version v pays at least 1 + (its part with T at u) + (the other part) + Bmin(s, v), Bmin = least E' + min_x e(x -> T(alpha))
// + min_y e(T(beta) -> y) over the jump pairs (x, y over all options of the two trails at the junction).
// usage: skip_eval DIR(runs.bin) PATTERNS THRG OUT.json
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#define NTR 30
#define BIGI (1 << 20)
static int mrun[NTR][2]; static uint8_t *runp[NTR][2];
static int NOPT, otr[16384], over_[16384], okk[16384], ocut[16384], tofs[NTR], tcnt[NTR], isA[NTR], Alist[6], nA, phl[24], nph;
static uint8_t oen[16384][8], oex[16384][8]; static int8_t *e;
static int wgt(const uint8_t *x, const uint8_t *y) { for (int s = 1; s < 8; s++) { int ok = 1; for (int i = 0; s + i < 8; i++) if (x[s + i] != y[i]) { ok = 0; break; } if (ok) return s; } return 8; }
#define E(a, b) ((int)e[(size_t)(a) * NOPT + (b)])
// jump pairs (alpha, beta) per trail-version with 0 <= E' <= EMAX: stored as run indices, sorted by E'
#define EMAX 20
typedef struct { int16_t a, b; int8_t ep; } JP;
static JP *jp[NTR][2]; static int njp[NTR][2];
// hinT[t1][o] = min over options x of trail t1 of e(x -> o);  houtT[t2][o] = min over options y of trail t2 of e(o -> y)
static uint8_t *hinT[NTR], *houtT[NTR];
static int THRG; static long nseq = 0, nfeas = 0, ncand = 0, nskipseq = 0; static int bestG = BIGI; static FILE *wit;
static int *fw[NTR], *bw[NTR];
#pragma omp threadprivate(fw, bw)
static int dpbuf[2][1400], lft[1400], rgt[1400], indep[2][1400];
#pragma omp threadprivate(dpbuf, lft, rgt, indep)
static int eval_seq(const int *sq, int jj) {
    __atomic_add_fetch(&nseq, 1, __ATOMIC_RELAXED);
    for (int i = 0; i < NTR; i++) { int t = sq[i];
        for (int q = 0; q < tcnt[t]; q++) { int o = tofs[t] + q, v;
            if (i == 0) v = ocut[o] == 2; else if (i == jj) v = 0;
            else { v = BIGI; int tp = sq[i - 1]; for (int q2 = 0; q2 < tcnt[tp]; q2++) { int w = fw[i - 1][q2] + E(tofs[tp] + q2, o); if (w < v) v = w; } }
            fw[i][q] = v; } }
    for (int i = NTR - 1; i >= 0; i--) { int t = sq[i];
        for (int q = 0; q < tcnt[t]; q++) { int o = tofs[t] + q, v;
            if (i == NTR - 1 || i == jj - 1) v = 0;
            else { v = BIGI; int tn = sq[i + 1]; for (int q2 = 0; q2 < tcnt[tn]; q2++) { int w = E(o, tofs[tn] + q2) + bw[i + 1][q2]; if (w < v) v = w; } }
            bw[i][q] = v; } }
    int tj = sq[jj - 1], tk = sq[jj];
    int minP = BIGI; for (int q = 0; q < tcnt[tj]; q++) if (fw[jj - 1][q] < minP) minP = fw[jj - 1][q];
    int minZ = BIGI; for (int q = 0; q < tcnt[tk]; q++) if (bw[jj][q] < minZ) minZ = bw[jj][q];
    if (1 + minP + minZ > THRG) return BIGI;
    __atomic_add_fetch(&nfeas, 1, __ATOMIC_RELAXED);
    int best = BIGI;
    // Bmin[s][v] = least E' + hinT[o_j trail][T(alpha)] + houtT[o_{j+1} trail][T(beta)] over the jump pairs of T's version v:
    // every member with T at position s pays at least  1 + (cost of its part with T at u) + (other part) + Bmin.
    int budget0 = THRG - 1 - minP - minZ, Bmin[NTR][2], anyok = 0;
    for (int s = 0; s < NTR; s++) { Bmin[s][0] = Bmin[s][1] = BIGI; if (s == jj - 1 || s == jj) continue; int T = sq[s];
        for (int v = 0; v < 2; v++) { int vb = tofs[T] + v * mrun[T][0]; const JP *L = jp[T][v]; int b = BIGI;
            for (int r = 0; r < njp[T][v] && L[r].ep <= budget0; r++) { int c = L[r].ep + hinT[tj][vb + L[r].a] + houtT[tk][vb + L[r].b]; if (c < b) b = c; }
            Bmin[s][v] = b; if (b <= budget0) anyok = 1; } }
    if (!anyok) { __atomic_add_fetch(&nskipseq, 1, __ATOMIC_RELAXED); return BIGI; }
    for (int s = 0; s < NTR; s++) { if (s == jj - 1 || s == jj) continue; int T = sq[s]; int have[2] = {0, 0};
        for (int q = 0; q < tcnt[T]; q++) { int ou = tofs[T] + q, v = over_[ou], m = mrun[T][v], u = okk[ou], vb = tofs[T] + v * mrun[T][0];
            if (Bmin[s][v] >= BIGI) continue;
            int through = fw[s][q] + bw[s][q]; int lb = 1 + (s < jj ? through + minZ : minP + through) + Bmin[s][v]; if (lb > THRG) continue;
            __atomic_add_fetch(&ncand, 1, __ATOMIC_RELAXED);
            // lft[k] = min_{o_j} Pend(o_j) + e(o_j -> T(k));  rgt[k] = min_{o_{j+1}} e(T(k) -> o_{j+1}) + Zstart(o_{j+1}), k = run index in version v.
            // The side away from the anchor does not depend on the anchor: computed once per (position, version).
            int *ind = indep[v];
            if (!have[v]) { have[v] = 1;
                if (s < jj) for (int k = 0; k < m; k++) { int b = BIGI; for (int q2 = 0; q2 < tcnt[tk]; q2++) { int w = E(vb + k, tofs[tk] + q2) + bw[jj][q2]; if (w < b) b = w; } ind[k] = b; }
                else for (int k = 0; k < m; k++) { int b = BIGI; for (int q2 = 0; q2 < tcnt[tj]; q2++) { int w = fw[jj - 1][q2] + E(tofs[tj] + q2, vb + k); if (w < b) b = w; } ind[k] = b; } }
            if (s < jj) {   // forced forward from s to jj-1
                int c = 0; for (int q2 = 0; q2 < tcnt[T]; q2++) dpbuf[c][q2] = q2 == q ? fw[s][q] : BIGI;
                for (int i = s + 1; i < jj; i++) { int tp = sq[i - 1], t = sq[i], nx = c ^ 1;
                    for (int q3 = 0; q3 < tcnt[t]; q3++) { int o = tofs[t] + q3, vv = BIGI; for (int q2 = 0; q2 < tcnt[tp]; q2++) { int d = dpbuf[c][q2]; if (d >= BIGI) continue; int w = d + E(tofs[tp] + q2, o); if (w < vv) vv = w; } dpbuf[nx][q3] = vv; }
                    c = nx; }
                int lim = THRG - 1 - minZ;   // lft beyond this cannot give G <= THRG
                for (int k = 0; k < m; k++) lft[k] = BIGI;
                for (int q2 = 0; q2 < tcnt[tj]; q2++) { int d = dpbuf[c][q2]; if (d > lim) continue; const int8_t *er = e + (size_t)(tofs[tj] + q2) * NOPT + vb;
                    for (int k = 0; k < m; k++) { int w = d + er[k]; if (w < lft[k]) lft[k] = w; } }
                for (int k = 0; k < m; k++) rgt[k] = ind[k]; }
            else {          // forced backward from s to jj
                int c = 0; for (int q2 = 0; q2 < tcnt[T]; q2++) dpbuf[c][q2] = q2 == q ? bw[s][q] : BIGI;
                for (int i = s - 1; i >= jj; i--) { int t = sq[i], tn = sq[i + 1], nx = c ^ 1;
                    for (int q3 = 0; q3 < tcnt[t]; q3++) { int o = tofs[t] + q3, vv = BIGI; for (int q2 = 0; q2 < tcnt[tn]; q2++) { int d = dpbuf[c][q2]; if (d >= BIGI) continue; int w = E(o, tofs[tn] + q2) + d; if (w < vv) vv = w; } dpbuf[nx][q3] = vv; }
                    c = nx; }
                int lim = THRG - 1 - minP;
                int live[1400], nlv = 0; for (int q2 = 0; q2 < tcnt[tk]; q2++) if (dpbuf[c][q2] <= lim) live[nlv++] = q2;
                for (int k = 0; k < m; k++) { int b = BIGI; for (int li = 0; li < nlv; li++) { int q2 = live[li]; int w = E(vb + k, tofs[tk] + q2) + dpbuf[c][q2]; if (w < b) b = w; } rgt[k] = b; }
                for (int k = 0; k < m; k++) lft[k] = ind[k]; }
            int ml = BIGI, mr = BIGI; for (int k = 0; k < m; k++) { if (lft[k] < ml) ml = lft[k]; if (rgt[k] < mr) mr = rgt[k]; }
            int emax = THRG - 1 - ml - mr; if (emax < 0) continue;
            const JP *L = jp[T][v]; int nL = njp[T][v];
            for (int r = 0; r < nL && L[r].ep <= emax; r++) { int a = L[r].a, b = L[r].b;
                int da = (a - u + m) % m, db = (b - u + m) % m; if (da < 1 || db <= da) continue;   // u -> alpha -> beta -> u, pieces nonempty
                int G = 1 + L[r].ep + lft[a] + rgt[b];
                if (G < best) best = G;
                if (G <= THRG) {
                    #pragma omp critical
                    { fprintf(wit, "{\"G\": %d, \"trail\": %d, \"pos\": %d, \"version\": %d, \"u\": %d, \"alpha\": %d, \"beta\": %d, \"Ep\": %d, \"junction_after\": %d, \"order\": [", G, T, s, v, u, a, b, L[r].ep, jj);
                    for (int i = 0; i < NTR; i++) fprintf(wit, "%s%d", i ? ", " : "", sq[i]); fprintf(wit, "]}\n"); fflush(wit); } } }
        } }
    return best;
}
typedef struct { int tr[6]; int n; int unordered; int junction; } Tok;
static Tok tk[64]; static int ntk; static int pbest;
#pragma omp threadprivate(tk, ntk, pbest)
static void expand(int ti, int *sq, int len, int jj) {
    if (ti == ntk) { if (len != NTR || jj <= 0 || jj >= NTR) { fprintf(stderr, "bad pattern\n"); exit(7); }
        { int seen[NTR] = {0}; for (int i = 0; i < NTR; i++) if (sq[i] < 0 || sq[i] >= NTR || seen[sq[i]]++) { fprintf(stderr, "pattern does not expand to a permutation of the 30 trails\n"); exit(9); } } int G = eval_seq(sq, jj); if (G < pbest) pbest = G; return; }
    Tok *t = &tk[ti];
    if (t->junction) { expand(ti + 1, sq, len, len); return; }
    if (!t->unordered || t->n <= 1) { for (int i = 0; i < t->n; i++) sq[len + i] = t->tr[i]; expand(ti + 1, sq, len + t->n, jj); return; }
    int p[6]; for (int i = 0; i < t->n; i++) p[i] = i; int c[6] = {0}, k = 0;
    for (int i = 0; i < t->n; i++) sq[len + i] = t->tr[p[i]]; expand(ti + 1, sq, len + t->n, jj);
    while (k < t->n) { if (c[k] < k) { int j = (k % 2 == 0) ? 0 : c[k]; int tmp = p[j]; p[j] = p[k]; p[k] = tmp;
            for (int i = 0; i < t->n; i++) sq[len + i] = t->tr[p[i]]; expand(ti + 1, sq, len + t->n, jj); c[k]++; k = 0; } else { c[k] = 0; k++; } }
}
static int jcmp(const void *x, const void *y) { return ((const JP *)x)->ep - ((const JP *)y)->ep; }
int main(int argc, char **argv) {
    const char *dir = argv[1], *pf = argv[2]; THRG = atoi(argv[3]); const char *outp = argv[4]; char p[2048]; double T0 = omp_get_wtime();
    snprintf(p, sizeof p, "%s/runs.bin", dir); FILE *f = fopen(p, "rb");
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int32_t m; if (fread(&m, 4, 1, f) != 1) return 2; mrun[t][v] = m; runp[t][v] = malloc(8 * m); if (fread(runp[t][v], 1, 8 * m, f) != (size_t)(8 * m)) return 2; }
    fclose(f);
    NOPT = 0;
    for (int t = 0; t < NTR; t++) { tofs[t] = NOPT; for (int v = 0; v < 2; v++) { int m = mrun[t][v];
        for (int k = 0; k < m; k++) { int o = NOPT++; otr[o] = t; over_[o] = v; okk[o] = k; memcpy(oen[o], runp[t][v] + 8 * k, 8); const uint8_t *pr = runp[t][v] + 8 * ((k + m - 1) % m);
            oex[o][0] = pr[7]; for (int i = 1; i < 8; i++) oex[o][i] = pr[i - 1]; ocut[o] = wgt(oex[o], oen[o]); } } tcnt[t] = NOPT - tofs[t]; }
    nA = nph = 0; for (int t = 0; t < NTR; t++) { isA[t] = mrun[t][0] > 100; if (isA[t]) Alist[nA++] = t; else phl[nph++] = t; }
    e = malloc((size_t)NOPT * NOPT);
    #pragma omp parallel for schedule(dynamic, 16)
    for (int a = 0; a < NOPT; a++) for (int b = 0; b < NOPT; b++) e[(size_t)a * NOPT + b] = (int8_t)(wgt(oex[a], oen[b]) - ocut[b] - 1);
    #pragma omp parallel for schedule(dynamic, 1)
    for (int t = 0; t < NTR; t++) { hinT[t] = malloc(NOPT); houtT[t] = malloc(NOPT);
        for (int o = 0; o < NOPT; o++) { int mi = 127, mo = 127; if (otr[o] != t) for (int q = 0; q < tcnt[t]; q++) { int x = tofs[t] + q; int a = E(x, o), b = E(o, x); if (a < mi) mi = a; if (b < mo) mo = b; }
            hinT[t][o] = (uint8_t)(mi < 0 ? 0 : mi); houtT[t][o] = (uint8_t)(mo < 0 ? 0 : mo); } }
    // jump pairs: alpha, beta runs of one version, beta != alpha (non-natural jump alpha-1 -> beta), 0 <= E' <= EMAX
    long nj = 0, nwrap = 0;
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int m = mrun[t][v], vb = tofs[t] + v * mrun[t][0]; jp[t][v] = malloc(sizeof(JP) * (size_t)m * m); njp[t][v] = 0;
        for (int a = 0; a < m; a++) for (int b = 0; b < m; b++) { if (b == a) continue; int am1 = (a + m - 1) % m;
            int ep = wgt(oex[vb + a], oen[vb + b]) - ocut[vb + b];   // oex[option a] = last(run a-1)
            (void)am1; if (ep < 0) { nwrap++; continue; } if (ep > EMAX) continue;
            JP *J = &jp[t][v][njp[t][v]++]; J->a = (int16_t)a; J->b = (int16_t)b; J->ep = (int8_t)ep; }
        qsort(jp[t][v], njp[t][v], sizeof(JP), jcmp); nj += njp[t][v]; }
    fprintf(stderr, "jump pairs with E' >= 0: %ld, wraps (E' = -1, excluded here): %ld, setup %.1fs\n", nj, nwrap, omp_get_wtime() - T0);
    #pragma omp parallel
    { for (int i = 0; i < NTR; i++) { fw[i] = malloc(4 * 1400); bw[i] = malloc(4 * 1400); } }
    char wp[2100]; snprintf(wp, sizeof wp, "%s.witnesses", outp); wit = fopen(wp, "w");
    FILE *in = fopen(pf, "r"); long cap = 1 << 16, nl = 0; char **lines = malloc(sizeof(char *) * cap); char line[8192];
    while (fgets(line, sizeof line, in)) { if (nl == cap) { cap *= 2; lines = realloc(lines, sizeof(char *) * cap); } lines[nl++] = strdup(line); }
    long npat = 0; int hist[64] = {0}; long done = 0;
    #pragma omp parallel for schedule(dynamic, 16) reduction(+:npat)
    for (long li = 0; li < nl; li++) { ntk = 0; char *s = lines[li]; int v, nch;
        while (sscanf(s, "%d%n", &v, &nch) == 1) { s += nch; Tok *t = &tk[ntk++]; memset(t, 0, sizeof *t);
            if (v == -1) t->junction = 1;
            else if (v < 1000) { if (v >= NTR || isA[v]) { fprintf(stderr, "bad phi token %d (phi tokens are trail ids)\n", v); exit(8); } t->tr[0] = v; t->n = 1; }
            else if (v >= 1200) { int m = v - 1200; for (int i = 0; i < 6; i++) if (m >> i & 1) t->tr[t->n++] = Alist[i]; t->unordered = 1; }
            else { int d = v - 1100; if (d < 64) { for (int i = 0; i < 6; i++) if (d >> i & 1) t->tr[t->n++] = Alist[i]; } else { d -= 64; t->tr[0] = Alist[d / 6]; t->tr[1] = Alist[d % 6]; t->n = 2; } } }
        if (!ntk) continue;
        int sq[NTR]; pbest = BIGI; expand(0, sq, 0, -1); npat++;
        #pragma omp critical
        { if (pbest < bestG) bestG = pbest; if (pbest < 64) hist[pbest]++; done++;
          if (done % 20000 == 0) fprintf(stderr, "patterns %ld / %ld, best G %d, within budget %ld, %.1fs\n", done, nl, bestG, nfeas, omp_get_wtime() - T0); } }
    fclose(in); fclose(wit);
    FILE *fo = fopen(outp, "w");
    fprintf(fo, "{\"checker\": \"skip_eval\", \"THRG\": %d, \"patterns\": %ld, \"sequences\": %ld, \"sequences_within_budget\": %ld, \"closed_by_insertion_bound\": %ld, \"anchor_candidates\": %ld, \"best_G_found_le_THRG\": %d, \"G_hist_over_patterns\": {", THRG, npat, nseq, nfeas, nskipseq, ncand, bestG < BIGI ? bestG : -1);
    int fz = 1; for (int g = 0; g < 64; g++) if (hist[g]) { fprintf(fo, "%s\"%d\": %d", fz ? "" : ", ", g, hist[g]); fz = 0; } fprintf(fo, "}, \"sec\": %.1f}\n", omp_get_wtime() - T0); fclose(fo);
    printf("{\"patterns\": %ld, \"sequences\": %ld, \"within_budget\": %ld, \"candidates\": %ld, \"best_G\": %d}\n", npat, nseq, nfeas, ncand, bestG < BIGI ? bestG : -1);
    return 0;
}
