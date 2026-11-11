// Round S -- exact evaluation of GAP-ANCHORED single brackets on the junction patterns of rQ/csrc/ckT_search.c
// (and, with STD=1, an independent re-implementation of the standard single-split evaluation of rQ/csrc/split_eval.c).
//
// Gap anchor.  Let C be a full chain of trail S (version v), Q_end the run before C_0 and N_0 the run after C_6.  In a
// route where C is detached (traversed elsewhere as a rotated block C_a .. C_6 C_0 .. C_{a-1}, a = 1..6) and the gap is
// CUT, the remainder S - C has the cut h = (entry N_0, exit Q_end) at the skip link (weight 4).  A bracket anchored at h:
//      ... [m .. Q_end] z_1 ... z_k [N_0 .. pred m] ...        (S - C cut at its main m and at the gap)
// By the Monge reduction (Theorem S1-S3) these gap cuts are exactly the wrap structures that are NOT reducible to bracket
// trees.  With SIGMA = P ++ Z' (junction after position j; P contains S with main option m of version v, m not in
// C + {N_0}), the identity  G = (P' - 30) + (3 - c'_1) + sum e'  for the family with C detached gives
//      G = 1 + F_J + beta_gap + ins(R),      beta_gap = e(z_k -> S(N_0)) + e(S(C_0) -> z_1),
//      F_J  = [cut(first) = 2] + sum of e over the edges of SIGMA except the junction,
//      ins(R) = e(x, R) + e(R, y) - e(x, y) >= -1   (R = rotated block of C = option S(C_a), inserted between x and y;
//               Monge with the weight-2 link C_{a-1} -> C_a; also >= -1 per piece if C is cut into several pieces).
// Hence  G >= pa + cz  with pa = exact P cost (anchor trail restricted) and cz = exact closing walk through the gap.
// SCREEN: all (sequence, anchor position, version, full chain) with pa + cz <= THRG are listed; for these the exact G
// (R as one block, all 31 insertion places, all 6 rotations) is computed.
//
// GAP2=1 (class G1''): the gap is the MAIN of S - C on the path (hybrid ports: entry N_0, exit Q_end) and the bracket hangs
// at another cut m of S (standard anchor), with the block of C inside the bracket.  Then
//      G = 1 + paH + cz(m) + ins(R) >= paH + cz(m),      paH = fw[s][S(N_0)] + bw[s][S(C_0)]
// (the forward value of the option cut at N_0 plus the backward value of the option cut at C_0).  Only the screen
// paH + cz <= THRG is evaluated, and only on the given patterns (sequences with standard F_J <= 20); sequences whose
// standard F_J is larger but whose hybrid path is cheaper are NOT covered -- a partial result.
// STD=1: standard anchors S(b) (b != main, same version):  G = 1 + pa + cz, cz = closing walk through S(b); witnesses
// with G <= THRG are written (must reproduce rQ/certs/single_split_exact_thr20.json: least G 21, 192 witnesses).
//
// Pattern tokens as in split_eval.c: phi trail ids, A groups (1100 + mask or 1164 + i*6+j: ordered; 1200 + mask: any
// order), -1 = junction.
// usage: gap_eval DIR(runs.bin) PATTERNS THRG OUT.json
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#define NTR 30
#define BIGI (1 << 20)
#define MAXOPT 1400
static int mrun[NTR][2]; static uint8_t *runp[NTR][2];
static int NOPT, otr[16384], over_[16384], ocut[16384], okk[16384], tofs[NTR], tcnt[NTR], isA[NTR], Alist[6], nA;
static uint8_t oen[16384][8], oex[16384][8]; static int8_t *e;
static int wgt(const uint8_t *x, const uint8_t *y) { for (int s = 1; s < 8; s++) { int ok = 1; for (int i = 0; s + i < 8; i++) if (x[s + i] != y[i]) { ok = 0; break; } if (ok) return s; } return 8; }
#define E(a, b) ((int)e[(size_t)(a) * NOPT + (b)])
// gaps: full chains
typedef struct { int tr, ver, oC, oN, opt[7]; } Gap;       // oC = option cut at C_0 (exit run Q_end), oN = option cut at N_0, opt[a] = option cut at C_a
static Gap *gaps; static int ngaps; static int gap_first[NTR][2], gap_cnt[NTR][2];
static uint8_t *ghin, *ghout;                                // per gap, per trail: min e(z -> S(N_0)), min e(S(C_0) -> y)
static uint8_t *hinT[NTR], *houtT[NTR];                      // standard anchors (as in split_eval)
static int THRG, STD, GAP2;
static long nseq = 0, nfeas = 0, ncand = 0, nsurv = 0, nwit = 0; static int bestLB = BIGI, bestG = BIGI; static long lbh[64]; static FILE *wit;
static int *fw[NTR + 2], *bw[NTR + 2], *fx[NTR + 2], *bx[NTR + 2];
#pragma omp threadprivate(fw, bw, fx, bx)
static int dz[2][MAXOPT];
#pragma omp threadprivate(dz)
// layered DP over a sequence of option lists: lists given as (base option index, count) or explicit arrays
typedef struct { int n; int o[MAXOPT]; } OL;
static OL *ol;
#pragma omp threadprivate(ol)
static void trail_list(OL *L, int t) { L->n = tcnt[t]; for (int q = 0; q < tcnt[t]; q++) L->o[q] = tofs[t] + q; }
static void block_list(OL *L, const Gap *g) { L->n = 6; for (int a = 1; a <= 6; a++) L->o[a - 1] = g->opt[a]; }
// forward / backward tables over lists ol[0..n-1]: F[i][q] = min cost of a path ending at option q of list i (first-vertex term included),
// B[i][q] = min cost from option q of list i to the end
static void fwbw(int n, int **F, int **B, int first_term) {
    for (int i = 0; i < n; i++) for (int q = 0; q < ol[i].n; q++) { int o = ol[i].o[q], v;
        if (i == 0) v = first_term ? (ocut[o] == 2) : 0;
        else { v = BIGI; for (int q2 = 0; q2 < ol[i - 1].n; q2++) { int w = F[i - 1][q2] + E(ol[i - 1].o[q2], o); if (w < v) v = w; } }
        F[i][q] = v; }
    for (int i = n - 1; i >= 0; i--) for (int q = 0; q < ol[i].n; q++) { int o = ol[i].o[q], v;
        if (i == n - 1) v = 0;
        else { v = BIGI; for (int q2 = 0; q2 < ol[i + 1].n; q2++) { int w = E(o, ol[i + 1].o[q2]) + B[i + 1][q2]; if (w < v) v = w; } }
        B[i][q] = v; }
}
// closing walk: from option `from` through lists ol[0..n-1] to option `to`
static int closing(int n, int from, int to) {
    int c2 = 0;
    for (int q = 0; q < ol[0].n; q++) dz[c2][q] = E(from, ol[0].o[q]);
    for (int i = 1; i < n; i++) { int nx = c2 ^ 1;
        for (int q = 0; q < ol[i].n; q++) { int o = ol[i].o[q], v = BIGI; for (int q2 = 0; q2 < ol[i - 1].n; q2++) { int w = dz[c2][q2] + E(ol[i - 1].o[q2], o); if (w < v) v = w; } dz[nx][q] = v; }
        c2 = nx; }
    int cz = BIGI; for (int q = 0; q < ol[n - 1].n; q++) { int w = dz[c2][q] + E(ol[n - 1].o[q], to); if (w < cz) cz = w; }
    return cz;
}
// exact G of a gap-anchored bracket with the detached chain as ONE rotated block, all insertion places
static int exact_gap(const int *sq, int jj, int s, const Gap *g, int *best_site) {
    int best = BIGI; *best_site = -1;
    // (a) block in the P part, before position i (i = 0..jj)
    for (int i = 0; i <= jj; i++) { int n = 0, spos = -1;
        for (int k = 0; k < jj; k++) { if (k == i) block_list(&ol[n++], g); if (k == s) spos = n; trail_list(&ol[n++], sq[k]); }
        if (i == jj) block_list(&ol[n++], g);
        fwbw(n, fx, bx, 1);
        int pa = BIGI; for (int q = 0; q < ol[spos].n; q++) { int o = ol[spos].o[q]; if (over_[o] != g->ver) continue; int ex = (o == g->oN); for (int a = 0; a < 7; a++) if (o == g->opt[a]) ex = 1; if (ex) continue;
            int v = fx[spos][q] + bx[spos][q]; if (v < pa) pa = v; }
        if (pa >= BIGI) continue;
        int m = 0; for (int k = jj; k < NTR; k++) trail_list(&ol[m++], sq[k]);
        int cz = closing(m, g->oC, g->oN);
        if (1 + pa + cz < best) { best = 1 + pa + cz; *best_site = i; } }
    // (b) block in the cycle, before position i (i = jj..NTR)
    { int n = 0, spos = -1; for (int k = 0; k < jj; k++) { if (k == s) spos = n; trail_list(&ol[n++], sq[k]); }
      fwbw(n, fx, bx, 1);
      int pa = BIGI; for (int q = 0; q < ol[spos].n; q++) { int o = ol[spos].o[q]; if (over_[o] != g->ver) continue; int ex = (o == g->oN); for (int a = 0; a < 7; a++) if (o == g->opt[a]) ex = 1; if (ex) continue;
          int v = fx[spos][q] + bx[spos][q]; if (v < pa) pa = v; }
      if (pa < BIGI) for (int i = jj; i <= NTR; i++) { int m = 0;
          for (int k = jj; k < NTR; k++) { if (k == i) block_list(&ol[m++], g); trail_list(&ol[m++], sq[k]); }
          if (i == NTR) block_list(&ol[m++], g);
          int cz = closing(m, g->oC, g->oN);
          if (1 + pa + cz < best) { best = 1 + pa + cz; *best_site = i + 100; } } }
    return best;
}
static int eval_seq(const int *sq, int jj) {
    __atomic_add_fetch(&nseq, 1, __ATOMIC_RELAXED);
    for (int i = 0; i < jj; i++) trail_list(&ol[i], sq[i]);
    fwbw(jj, fw, bw, 1);
    int minP = BIGI; for (int q = 0; q < ol[jj - 1].n; q++) if (fw[jj - 1][q] < minP) minP = fw[jj - 1][q];
    // Z part backward (free start, free end), stored in bw[jj..]
    for (int i = NTR - 1; i >= jj; i--) { int t = sq[i];
        for (int q = 0; q < tcnt[t]; q++) { int o = tofs[t] + q, v;
            if (i == NTR - 1) v = 0;
            else { v = BIGI; int tn = sq[i + 1]; for (int q2 = 0; q2 < tcnt[tn]; q2++) { int w = E(o, tofs[tn] + q2) + bw[i + 1][q2]; if (w < v) v = w; } }
            bw[i][q] = v; } }
    int minZ = BIGI; { int t = sq[jj]; for (int q = 0; q < tcnt[t]; q++) if (bw[jj][q] < minZ) minZ = bw[jj][q]; }
    int slackthr = STD ? THRG - 1 : THRG;                 // STD: 1 + pa + cz <= THRG;  gap screen: pa + cz <= THRG
    if (!GAP2 && minP + minZ > slackthr) return BIGI;     // (GAP2: the hybrid path may be cheaper than every standard one)
    if (GAP2 && minZ > THRG) return BIGI;
    __atomic_add_fetch(&nfeas, 1, __ATOMIC_RELAXED);
    int best = BIGI; int t1 = sq[jj], tl = sq[NTR - 1];
    // the P part lists are still in ol[0..jj-1]; closing walks need the Z lists: build them after the P scans
    static __thread int pv[MAXOPT];
    for (int s = 0; s < jj; s++) { int S = sq[s];
        for (int q = 0; q < tcnt[S]; q++) pv[q] = fw[s][q] + bw[s][q];
        if (STD) {
            int b1[2] = {BIGI, BIGI}, i1[2] = {-1, -1}, b2[2] = {BIGI, BIGI};
            for (int q = 0; q < tcnt[S]; q++) { int v = pv[q]; int ver = over_[tofs[S] + q]; if (v < b1[ver]) { b2[ver] = b1[ver]; b1[ver] = v; i1[ver] = q; } else if (v < b2[ver]) b2[ver] = v; }
            for (int qb = 0; qb < tcnt[S]; qb++) { int ob = tofs[S] + qb, ver = over_[ob];
                int pa = (i1[ver] == qb) ? b2[ver] : b1[ver]; if (pa >= BIGI) continue;
                int lim = (THRG - 1) - pa - minZ; if (lim < 0) continue;
                if ((int)houtT[t1][ob] + (int)hinT[tl][ob] > lim) continue;
                __atomic_add_fetch(&ncand, 1, __ATOMIC_RELAXED);
                int m = 0; for (int k = jj; k < NTR; k++) trail_list(&ol[NTR + 1], sq[k]), ol[m++] = ol[NTR + 1];
                int cz = closing(m, ob, ob);
                for (int i = 0; i < jj; i++) trail_list(&ol[i], sq[i]);
                int G = 1 + pa + cz; if (G < best) best = G;
                if (G <= THRG) {
                    #pragma omp critical
                    { nwit++; fprintf(wit, "{\"G\": %d, \"anchor_pos\": %d, \"anchor_trail\": %d, \"b_option\": %d, \"junction_after\": %d, \"order\": [", G, s, S, qb, jj);
                      for (int i = 0; i < NTR; i++) fprintf(wit, "%s%d", i ? ", " : "", sq[i]); fprintf(wit, "]}\n"); } } }
            continue; }
        if (GAP2) {
            for (int ver = 0; ver < 2; ver++) for (int gi = gap_first[S][ver]; gi < gap_first[S][ver] + gap_cnt[S][ver]; gi++) { const Gap *g = &gaps[gi];
                int paH = fw[s][g->oN - tofs[S]] + bw[s][g->oC - tofs[S]];
                if (paH + minZ > THRG) continue;
                for (int qb = 0; qb < tcnt[S]; qb++) { int ob = tofs[S] + qb; if (over_[ob] != ver || ob == g->oN) continue; int ex = 0; for (int a = 0; a < 7; a++) if (ob == g->opt[a]) ex = 1; if (ex) continue;
                    int lim = THRG - paH - minZ; if ((int)houtT[t1][ob] + (int)hinT[tl][ob] > lim) continue;
                    __atomic_add_fetch(&ncand, 1, __ATOMIC_RELAXED);
                    int m = 0; for (int k = jj; k < NTR; k++) { trail_list(&ol[NTR + 1], sq[k]); ol[m++] = ol[NTR + 1]; }
                    int cz = closing(m, ob, ob);
                    for (int i = 0; i < jj; i++) trail_list(&ol[i], sq[i]);
                    int LB = paH + cz; if (LB < best) best = LB;
                    if (LB <= THRG) {
                        #pragma omp critical
                        { nsurv++; fprintf(wit, "{\"class\": \"G1pp\", \"LB\": %d, \"anchor_pos\": %d, \"anchor_trail\": %d, \"version\": %d, \"gap_C0_option\": %d, \"b_option\": %d, \"junction_after\": %d, \"order\": [", LB, s, S, ver, g->oC - tofs[S], qb, jj);
                          for (int i = 0; i < NTR; i++) fprintf(wit, "%s%d", i ? ", " : "", sq[i]); fprintf(wit, "]}\n"); fflush(wit); } } } }
            continue; }
        for (int ver = 0; ver < 2; ver++) { if (!gap_cnt[S][ver]) continue;
            // the 9 best main options of this version (a chain excludes at most 8 of them)
            int bv[9], bq[9], nb = 0;
            for (int q = 0; q < tcnt[S]; q++) { if (over_[tofs[S] + q] != ver) continue; int v = pv[q];
                int k;
                if (nb < 9) k = nb++; else { if (v >= bv[8]) continue; k = 8; }
                while (k > 0 && bv[k - 1] > v) { bv[k] = bv[k - 1]; bq[k] = bq[k - 1]; k--; } bv[k] = v; bq[k] = q; }
            if (nb == 0 || bv[0] + minZ > THRG) continue;
            for (int gi = gap_first[S][ver]; gi < gap_first[S][ver] + gap_cnt[S][ver]; gi++) { const Gap *g = &gaps[gi];
                int pa = BIGI; for (int k = 0; k < nb; k++) { int o = tofs[S] + bq[k]; int ex = (o == g->oN); for (int a = 0; a < 7; a++) if (o == g->opt[a]) ex = 1; if (!ex) { pa = bv[k]; break; } }
                if (pa >= BIGI) continue;
                int lim = THRG - pa - minZ; if (lim < 0) continue;
                if ((int)ghout[(size_t)gi * NTR + t1] + (int)ghin[(size_t)gi * NTR + tl] > lim) continue;
                __atomic_add_fetch(&ncand, 1, __ATOMIC_RELAXED);
                int m = 0; for (int k = jj; k < NTR; k++) { trail_list(&ol[NTR + 1], sq[k]); ol[m++] = ol[NTR + 1]; }
                int cz = closing(m, g->oC, g->oN);
                int LB = pa + cz;
                if (LB < best) best = LB;
                if (LB <= THRG) { int site; int G = exact_gap(sq, jj, s, g, &site);
                    #pragma omp critical
                    { nsurv++; if (G < bestG) bestG = G;
                      fprintf(wit, "{\"LB\": %d, \"G_exact_one_block\": %d, \"block_site\": %d, \"anchor_pos\": %d, \"anchor_trail\": %d, \"version\": %d, \"gap_C0_option\": %d, \"gap_N0_option\": %d, \"junction_after\": %d, \"order\": [",
                              LB, G, site, s, S, ver, g->oC - tofs[S], g->oN - tofs[S], jj);
                      for (int i = 0; i < NTR; i++) fprintf(wit, "%s%d", i ? ", " : "", sq[i]); fprintf(wit, "]}\n"); fflush(wit); } }
                for (int i = 0; i < jj; i++) trail_list(&ol[i], sq[i]);
            } } }
    return best;
}
typedef struct { int tr[6]; int n; int unordered; int junction; } Tok;
static Tok tk[64]; static int ntk; static int pbest;
#pragma omp threadprivate(tk, ntk, pbest)
static void expand(int ti, int *sq, int len, int jj) {
    if (ti == ntk) { if (len != NTR || jj <= 0 || jj >= NTR) { fprintf(stderr, "bad pattern length %d junction %d\n", len, jj); exit(7); }
        { int seen[NTR] = {0}; for (int i = 0; i < NTR; i++) if (sq[i] < 0 || sq[i] >= NTR || seen[sq[i]]++) { fprintf(stderr, "pattern does not expand to a permutation of the 30 trails\n"); exit(9); } }
        int G = eval_seq(sq, jj); if (G < pbest) pbest = G; return; }
    Tok *t = &tk[ti];
    if (t->junction) { expand(ti + 1, sq, len, len); return; }
    if (!t->unordered || t->n <= 1) { for (int i = 0; i < t->n; i++) sq[len + i] = t->tr[i]; expand(ti + 1, sq, len + t->n, jj); return; }
    int p[6]; for (int i = 0; i < t->n; i++) p[i] = i; int c[6] = {0}, k = 0;
    for (int i = 0; i < t->n; i++) sq[len + i] = t->tr[p[i]]; expand(ti + 1, sq, len + t->n, jj);
    while (k < t->n) { if (c[k] < k) { int j = (k % 2 == 0) ? 0 : c[k]; int tmp = p[j]; p[j] = p[k]; p[k] = tmp;
            for (int i = 0; i < t->n; i++) sq[len + i] = t->tr[p[i]]; expand(ti + 1, sq, len + t->n, jj); c[k]++; k = 0; } else { c[k] = 0; k++; } }
}
int main(int argc, char **argv) {
    if (argc < 5) { fprintf(stderr, "usage: gap_eval DIR PATTERNS THRG OUT.json   (env STD=1: standard anchors)\n"); return 1; }
    const char *dir = argv[1], *pf = argv[2]; THRG = atoi(argv[3]); const char *outp = argv[4]; char p[2048]; double T0 = omp_get_wtime();
    STD = getenv("STD") && atoi(getenv("STD")); GAP2 = getenv("GAP2") && atoi(getenv("GAP2"));
    snprintf(p, sizeof p, "%s/runs.bin", dir); FILE *f = fopen(p, "rb"); if (!f) return 2;
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int32_t m; if (fread(&m, 4, 1, f) != 1) return 2; mrun[t][v] = m; runp[t][v] = malloc(8 * m); if (fread(runp[t][v], 1, 8 * m, f) != (size_t)(8 * m)) return 2; }
    fclose(f);
    NOPT = 0;
    for (int t = 0; t < NTR; t++) { tofs[t] = NOPT; for (int v = 0; v < 2; v++) { int m = mrun[t][v];
        for (int k = 0; k < m; k++) { int o = NOPT++; otr[o] = t; over_[o] = v; okk[o] = k; memcpy(oen[o], runp[t][v] + 8 * k, 8); const uint8_t *pr = runp[t][v] + 8 * ((k + m - 1) % m);
            oex[o][0] = pr[7]; for (int i = 1; i < 8; i++) oex[o][i] = pr[i - 1]; ocut[o] = wgt(oex[o], oen[o]); } } tcnt[t] = NOPT - tofs[t]; }
    nA = 0; for (int t = 0; t < NTR; t++) { isA[t] = mrun[t][0] > 100; if (isA[t]) Alist[nA++] = t; }
    e = malloc((size_t)NOPT * NOPT); long neg = 0;
    #pragma omp parallel for schedule(dynamic, 16) reduction(+:neg)
    for (int a = 0; a < NOPT; a++) for (int b = 0; b < NOPT; b++) { int v = wgt(oex[a], oen[b]) - ocut[b] - 1; if (otr[a] != otr[b] && v < 0) neg++; e[(size_t)a * NOPT + b] = (int8_t)v; }
    if (neg) { fprintf(stderr, "negative cross-trail excess %ld\n", neg); return 5; }
    // full chains of every trail version
    gaps = malloc(sizeof(Gap) * 2048); ngaps = 0;
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int m = mrun[t][v], base = tofs[t] + v * mrun[t][0]; gap_first[t][v] = ngaps; gap_cnt[t][v] = 0;
        for (int k = 0; k < m; k++) { if (ocut[base + k] != 3) continue; int len = 1; while (ocut[base + (k + len) % m] == 2 && len < 9) len++;
            if (len != 7) continue;
            // wrap weight: last permutation of run k+6 (= exit of option k+7) to the first permutation of run k
            if (wgt(oex[base + (k + 7) % m], oen[base + k]) != 2) continue;
            Gap *g = &gaps[ngaps++]; g->tr = t; g->ver = v; g->oC = base + k; g->oN = base + (k + 7) % m; for (int a = 0; a < 7; a++) g->opt[a] = base + (k + a) % m; gap_cnt[t][v]++;
            if (wgt(oex[g->oC], oen[g->oN]) != 4) { fprintf(stderr, "skip weight is not 4\n"); return 6; } } }
    ghin = malloc((size_t)ngaps * NTR); ghout = malloc((size_t)ngaps * NTR);
    #pragma omp parallel for schedule(dynamic, 8)
    for (int gi = 0; gi < ngaps; gi++) for (int t = 0; t < NTR; t++) { int mi = 127, mo = 127; const Gap *g = &gaps[gi];
        if (t != g->tr) for (int q = 0; q < tcnt[t]; q++) { int x = tofs[t] + q; int a = E(x, g->oN), b = E(g->oC, x); if (a < mi) mi = a; if (b < mo) mo = b; }
        ghin[(size_t)gi * NTR + t] = (uint8_t)(mi < 0 ? 0 : mi); ghout[(size_t)gi * NTR + t] = (uint8_t)(mo < 0 ? 0 : mo); }
    #pragma omp parallel for schedule(dynamic, 1)
    for (int t = 0; t < NTR; t++) { hinT[t] = malloc(NOPT); houtT[t] = malloc(NOPT);
        for (int o = 0; o < NOPT; o++) { int mi = 127, mo = 127; if (otr[o] != t) for (int q = 0; q < tcnt[t]; q++) { int x = tofs[t] + q; int a = E(x, o), b = E(o, x); if (a < mi) mi = a; if (b < mo) mo = b; }
            hinT[t][o] = (uint8_t)(mi < 0 ? 0 : mi); houtT[t][o] = (uint8_t)(mo < 0 ? 0 : mo); } }
    #pragma omp parallel
    { for (int i = 0; i < NTR + 2; i++) { fw[i] = malloc(4 * MAXOPT); bw[i] = malloc(4 * MAXOPT); fx[i] = malloc(4 * MAXOPT); bx[i] = malloc(4 * MAXOPT); } ol = malloc(sizeof(OL) * (NTR + 3)); }
    char wp[2100]; snprintf(wp, sizeof wp, "%s.witnesses", outp); wit = fopen(wp, "w");
    FILE *in = fopen(pf, "r"); if (!in) return 2; long cap = 1 << 16, nl = 0; char **lines = malloc(sizeof(char *) * cap); char line[8192];
    while (fgets(line, sizeof line, in)) { if (nl == cap) { cap *= 2; lines = realloc(lines, sizeof(char *) * cap); } lines[nl++] = strdup(line); }
    long npat = 0, done = 0; long hist[64] = {0};
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
        { if (pbest < 0) { fprintf(stderr, "negative value %d\n", pbest); exit(10); }
          if (pbest < bestLB) bestLB = pbest; if (pbest < 64) hist[pbest]++; done++;
          if (done % 10000 == 0) fprintf(stderr, "patterns %ld / %ld, least value %d, within budget %ld, candidates %ld, survivors %ld, %.1fs\n", done, nl, bestLB, nfeas, ncand, STD ? nwit : nsurv, omp_get_wtime() - T0); } }
    fclose(in); fclose(wit);
    FILE *fo = fopen(outp, "w");
    if (STD) fprintf(fo, "{\"checker\": \"gap_eval STD=1 (standard single splits, independent of split_eval.c)\", \"THRG\": %d, \"patterns\": %ld, \"sequences\": %ld, \"sequences_within_budget\": %ld, \"b_candidates\": %ld, \"witnesses_G_le_THRG\": %ld, \"least_G_found_le_THRG\": %d, \"least_G_hist_over_patterns\": {", THRG, npat, nseq, nfeas, ncand, nwit, bestLB < BIGI ? bestLB : -1);
    else fprintf(fo, "{\"checker\": \"gap_eval (%s)\", \"THRG\": %d, \"full_chains\": %d, \"patterns\": %ld, \"sequences\": %ld, \"sequences_within_budget\": %ld, \"gap_candidates\": %ld, \"screen_survivors_pa_plus_cz_le_THRG\": %ld, \"least_screen_value_found_le_THRG\": %d, \"least_exact_G_one_block\": %d, \"least_screen_hist_over_patterns\": {", GAP2 ? "class G1'': hybrid main with its own bracket, screen only, partial" : "gap-anchored single brackets", THRG, ngaps, npat, nseq, nfeas, ncand, nsurv, bestLB < BIGI ? bestLB : -1, bestG < BIGI ? bestG : -1);
    int fz = 1; for (int g = 0; g < 64; g++) if (hist[g]) { fprintf(fo, "%s\"%d\": %ld", fz ? "" : ", ", g, hist[g]); fz = 0; } fprintf(fo, "}, \"sec\": %.1f}\n", omp_get_wtime() - T0); fclose(fo);
    printf("{\"patterns\": %ld, \"sequences\": %ld, \"within_budget\": %ld, \"candidates\": %ld, \"survivors\": %ld, \"least\": %d, \"least_exact_G\": %d}\n", npat, nseq, nfeas, ncand, STD ? nwit : nsurv, bestLB < BIGI ? bestLB : -1, bestG < BIGI ? bestG : -1);
    return 0;
}
