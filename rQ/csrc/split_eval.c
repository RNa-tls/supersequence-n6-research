// Round Q, section 3 -- exact evaluation of the single-split patterns written by ckT_search.c.
// Independent of ckT.c / ckT_search.c / ckB*: rebuilds options and the excess e (all pairs, same-trail pairs
// included but never used across a split) from runs.bin.
// A pattern is a token line: phi trail ids, A groups (1100 + mask or 1164 + i*6+j: ordered; 1200 + mask: any
// order), -1 = junction.  Every concrete trail sequence SIGMA (unordered groups expanded into all orders) with
// junction after position j is a family of single splits:
//   G = 1 + [cut(o_1) = 2] + sum_{i < j} e(o_i -> o_i+1) + sum_{i > j} e(o_i -> o_i+1)
//         + e(o_30 -> S(b)) + e(S(b) -> o_{j+1}),   S = SIGMA_s (s <= j) at option o_s = a,  b != a, same version.
// Every single split arises this way (delete S(b) from the virtual cycle).  The minimum over all option choices is
// computed exactly (dynamic programming; anchors and b enumerated, pruned only by the exact bound G <= THRG).
// usage: split_eval DIR(runs.bin) PATTERNS THRG OUT.json
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#define NTR 30
#define BIGI (1 << 20)
static int mrun[NTR][2]; static uint8_t *runp[NTR][2];
static int NOPT, otr[16384], over_[16384], ocut[16384], tofs[NTR], tcnt[NTR], isA[NTR], Alist[6], nA, phl[24], nph;
static uint8_t oen[16384][8], oex[16384][8]; static int8_t *e;
static int wgt(const uint8_t *x, const uint8_t *y) { for (int s = 1; s < 8; s++) { int ok = 1; for (int i = 0; s + i < 8; i++) if (x[s + i] != y[i]) { ok = 0; break; } if (ok) return s; } return 8; }
#define E(a, b) ((int)e[(size_t)(a) * NOPT + (b)])
static int THRG; static long nseq = 0, nfeas = 0; static int bestG = BIGI; static int bestSeq[NTR], bestJ, bestS, bestA, bestB, bestOpt[NTR]; static FILE *wit;
// exact evaluation of one concrete sequence (trails sq[0..29]) with junction after position jj (P = 0..jj-1)
static int *fw[NTR], *bw[NTR];   // per position option arrays (max 1344)
#pragma omp threadprivate(fw, bw)
static int dz[2][1400];
#pragma omp threadprivate(dz)
static int eval_seq(const int *sq, int jj) {
    __atomic_add_fetch(&nseq, 1, __ATOMIC_RELAXED);
    // P part forward / backward
    for (int i = 0; i < jj; i++) { int t = sq[i];
        for (int q = 0; q < tcnt[t]; q++) { int o = tofs[t] + q, v;
            if (i == 0) v = ocut[o] == 2;
            else { v = BIGI; int tp = sq[i - 1]; for (int q2 = 0; q2 < tcnt[tp]; q2++) { int w = fw[i - 1][q2] + E(tofs[tp] + q2, o); if (w < v) v = w; } }
            fw[i][q] = v; } }
    for (int i = jj - 1; i >= 0; i--) { int t = sq[i];
        for (int q = 0; q < tcnt[t]; q++) { int o = tofs[t] + q, v;
            if (i == jj - 1) v = 0;
            else { v = BIGI; int tn = sq[i + 1]; for (int q2 = 0; q2 < tcnt[tn]; q2++) { int w = E(o, tofs[tn] + q2) + bw[i + 1][q2]; if (w < v) v = w; } }
            bw[i][q] = v; } }
    int minP = BIGI; { int t = sq[jj - 1]; for (int q = 0; q < tcnt[t]; q++) if (fw[jj - 1][q] < minP) minP = fw[jj - 1][q]; }
    // Z part: positions jj..29, free start, free end; zb[i][q] = min cost from option q at i to the end
    for (int i = NTR - 1; i >= jj; i--) { int t = sq[i];
        for (int q = 0; q < tcnt[t]; q++) { int o = tofs[t] + q, v;
            if (i == NTR - 1) v = 0;
            else { v = BIGI; int tn = sq[i + 1]; for (int q2 = 0; q2 < tcnt[tn]; q2++) { int w = E(o, tofs[tn] + q2) + bw[i + 1][q2]; if (w < v) v = w; } }
            bw[i][q] = v; } }
    int minZ = BIGI; { int t = sq[jj]; for (int q = 0; q < tcnt[t]; q++) if (bw[jj][q] < minZ) minZ = bw[jj][q]; }
    int budget = (THRG - 1) - minP - minZ;               // G = 1 + P + Z + beta <= THRG  <=>  beta <= budget (at best)
    if (budget < 0) return BIGI;
    __atomic_add_fetch(&nfeas, 1, __ATOMIC_RELAXED);
    int best = BIGI; int t1 = sq[jj], tl = sq[NTR - 1];
    for (int s = 0; s < jj; s++) { int S = sq[s];
        // best and second-best P cost per version of S (a = anchor's option in P), for the b != a constraint
        int b1[2] = {BIGI, BIGI}, i1[2] = {-1, -1}, b2[2] = {BIGI, BIGI};
        // P cost with the anchor at option a: prefix (fw) + P suffix from position s (bw[s], positions < jj untouched by the Z pass)
        for (int q = 0; q < tcnt[S]; q++) { int v = fw[s][q] + bw[s][q]; int ver = over_[tofs[S] + q];
            if (v < b1[ver]) { b2[ver] = b1[ver]; b1[ver] = v; i1[ver] = q; } else if (v < b2[ver]) b2[ver] = v; }
        int minPS = b1[0] < b1[1] ? b1[0] : b1[1]; if (minPS + minZ + 1 > THRG) continue;
        for (int qb = 0; qb < tcnt[S]; qb++) { int ob = tofs[S] + qb, ver = over_[ob];
            int pa = (i1[ver] == qb) ? b2[ver] : b1[ver]; if (pa >= BIGI) continue;   // best P with a != b, same version
            int lim = (THRG - 1) - pa - minZ; if (lim < 0) continue;              // beta <= lim needed
            // closing walk: S(b) -> o_{jj} ... -> o_29 -> S(b);  forward DP from the entry of position jj
            int any = 0; for (int q = 0; q < tcnt[t1]; q++) if (E(ob, tofs[t1] + q) <= lim) { any = 1; break; } if (!any) continue;
            any = 0; for (int q = 0; q < tcnt[tl]; q++) if (E(tofs[tl] + q, ob) <= lim) { any = 1; break; } if (!any) continue;
            int (*d)[1400] = dz; int c2 = 0;
            for (int q = 0; q < tcnt[t1]; q++) d[c2][q] = E(ob, tofs[t1] + q);
            for (int i = jj + 1; i < NTR; i++) { int tp = sq[i - 1], t = sq[i]; int nx = c2 ^ 1;
                for (int q = 0; q < tcnt[t]; q++) { int o = tofs[t] + q, v = BIGI; for (int q2 = 0; q2 < tcnt[tp]; q2++) { int w = d[c2][q2] + E(tofs[tp] + q2, o); if (w < v) v = w; } d[nx][q] = v; }
                c2 = nx; }
            int cz = BIGI; for (int q = 0; q < tcnt[tl]; q++) { int w = d[c2][q] + E(tofs[tl] + q, ob); if (w < cz) cz = w; }
            int G = 1 + pa + cz;
            if (G < best) best = G;
            if (G <= THRG) {
                #pragma omp critical
                { fprintf(wit, "{\"G\": %d, \"anchor_pos\": %d, \"anchor_trail\": %d, \"b_option\": %d, \"junction_after\": %d, \"order\": [", G, s, S, qb, jj);
                for (int i = 0; i < NTR; i++) fprintf(wit, "%s%d", i ? ", " : "", sq[i]); fprintf(wit, "]}\n"); fflush(wit); } }
        } }
    return best;
}
// pattern expansion: groups with any order -> all permutations
typedef struct { int tr[6]; int n; int unordered; int junction; } Tok;
static Tok tk[64]; static int ntk; static int pbest;
#pragma omp threadprivate(tk, ntk, pbest)
static void expand(int ti, int *sq, int len, int jj) {
    if (ti == ntk) { if (len != NTR || jj <= 0 || jj >= NTR) { fprintf(stderr, "bad pattern length %d junction %d\n", len, jj); exit(7); }
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
    const char *dir = argv[1], *pf = argv[2]; THRG = atoi(argv[3]); const char *outp = argv[4]; char p[2048]; double T0 = omp_get_wtime();
    snprintf(p, sizeof p, "%s/runs.bin", dir); FILE *f = fopen(p, "rb");
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int32_t m; if (fread(&m, 4, 1, f) != 1) return 2; mrun[t][v] = m; runp[t][v] = malloc(8 * m); if (fread(runp[t][v], 1, 8 * m, f) != (size_t)(8 * m)) return 2; }
    fclose(f);
    NOPT = 0;
    for (int t = 0; t < NTR; t++) { tofs[t] = NOPT; for (int v = 0; v < 2; v++) { int m = mrun[t][v];
        for (int k = 0; k < m; k++) { int o = NOPT++; otr[o] = t; over_[o] = v; memcpy(oen[o], runp[t][v] + 8 * k, 8); const uint8_t *pr = runp[t][v] + 8 * ((k + m - 1) % m);
            oex[o][0] = pr[7]; for (int i = 1; i < 8; i++) oex[o][i] = pr[i - 1]; ocut[o] = wgt(oex[o], oen[o]); } } tcnt[t] = NOPT - tofs[t]; }
    nA = nph = 0; for (int t = 0; t < NTR; t++) { isA[t] = mrun[t][0] > 100; if (isA[t]) Alist[nA++] = t; else phl[nph++] = t; }
    e = malloc((size_t)NOPT * NOPT); long neg = 0;
    #pragma omp parallel for schedule(dynamic, 16) reduction(+:neg)
    for (int a = 0; a < NOPT; a++) for (int b = 0; b < NOPT; b++) { int v = wgt(oex[a], oen[b]) - ocut[b] - 1; if (otr[a] != otr[b] && v < 0) neg++; e[(size_t)a * NOPT + b] = (int8_t)v; }
    if (neg) { fprintf(stderr, "negative cross-trail excess %ld\n", neg); return 5; }
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
            else if (v < 1000) { t->tr[0] = phl[v]; t->n = 1; }
            else if (v >= 1200) { int m = v - 1200; for (int i = 0; i < 6; i++) if (m >> i & 1) t->tr[t->n++] = Alist[i]; t->unordered = 1; }
            else { int d = v - 1100; if (d < 64) { for (int i = 0; i < 6; i++) if (d >> i & 1) t->tr[t->n++] = Alist[i]; } else { d -= 64; t->tr[0] = Alist[d / 6]; t->tr[1] = Alist[d % 6]; t->n = 2; } } }
        if (!ntk) continue;
        int sq[NTR]; pbest = BIGI; expand(0, sq, 0, -1); npat++;
        #pragma omp critical
        { if (pbest < bestG) bestG = pbest; if (pbest < 64) hist[pbest]++; done++;
          if (done % 50000 == 0) fprintf(stderr, "patterns %ld / %ld, best G %d, %.1fs\n", done, nl, bestG, omp_get_wtime() - T0); } }
    fclose(in); fclose(wit);
    FILE *fo = fopen(outp, "w");
    fprintf(fo, "{\"checker\": \"split_eval\", \"THRG\": %d, \"patterns\": %ld, \"sequences\": %ld, \"sequences_within_budget\": %ld, \"best_G_found_le_THRG\": %d, \"G_hist_over_patterns\": {", THRG, npat, nseq, nfeas, bestG < BIGI ? bestG : -1);
    int fz = 1; for (int g = 0; g < 64; g++) if (hist[g]) { fprintf(fo, "%s\"%d\": %d", fz ? "" : ", ", g, hist[g]); fz = 0; } fprintf(fo, "}, \"sec\": %.1f}\n", omp_get_wtime() - T0); fclose(fo);
    printf("{\"patterns\": %ld, \"sequences\": %ld, \"within_budget\": %ld, \"best_G\": %d}\n", npat, nseq, nfeas, bestG < BIGI ? bestG : -1);
    return 0;
}
