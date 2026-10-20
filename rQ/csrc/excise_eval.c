// Round Q, section 3 -- exact evaluation of SINGLE ROTATED-CHAIN EXCISIONS on the junction patterns of ckT_search.c.
// An excision of trail T: V1 = the full chain C rotated at a mid-chain run a1 (acts as option T(a1)), R = T minus C as one
// fragment (entry option T(N_start), exit option T(C_start)).  When R is inserted between SIGMA_j and SIGMA_{j+1}, both
// different from T (R not adjacent to V1):  G = F_J + e(o_j -> T(N_start)) + e(T(C_start) -> o_{j+1}),
// F_J = [cut(o_1) = 2] + sum of the SIGMA edges except (j, j+1), T at option a1.  (One extra visit +1, one wrap -1.)
// Every such excision with G <= THRG has F_J <= THRG, so it lies in the patterns of ckT_search with THR >= THRG.
// For every pattern, every trail T not adjacent to the junction, every mid-chain run a1 of a full chain of either version:
// exact minimum over all other options (dynamic programming).  Rebuilds options and e from runs.bin (no shared code).
// usage: excise_eval DIR(runs.bin) PATTERNS THRG OUT.json
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
// mid-chain runs of full chains: for option o (trail t, version v, run k) with k inside a full chain C (not its start):
// rin[o] = option T(N_start), rout[o] = option T(C_start); -1 otherwise
static int rin[16384], rout[16384];
static int THRG; static long nseq = 0, ncand = 0; static int bestG = BIGI; static FILE *wit;
static int *fw[NTR], *bw[NTR];
#pragma omp threadprivate(fw, bw)
static int dpbuf[2][1400];
#pragma omp threadprivate(dpbuf)
static int eval_seq(const int *sq, int jj) {
    __atomic_add_fetch(&nseq, 1, __ATOMIC_RELAXED);
    // unforced forward over the whole sequence with a cut at jj: fw[i] for i < jj (P, word start), fw[i] for i >= jj (Z, free start)
    for (int i = 0; i < NTR; i++) { int t = sq[i];
        for (int q = 0; q < tcnt[t]; q++) { int o = tofs[t] + q, v;
            if (i == 0) v = ocut[o] == 2; else if (i == jj) v = 0;
            else { v = BIGI; int tp = sq[i - 1]; for (int q2 = 0; q2 < tcnt[tp]; q2++) { int w = fw[i - 1][q2] + E(tofs[tp] + q2, o); if (w < v) v = w; } }
            fw[i][q] = v; } }
    // unforced backward: bw[i] = min cost from option at i to the end of its part (P ends at jj-1, Z at 29), free end
    for (int i = NTR - 1; i >= 0; i--) { int t = sq[i];
        for (int q = 0; q < tcnt[t]; q++) { int o = tofs[t] + q, v;
            if (i == NTR - 1 || i == jj - 1) v = 0;
            else { v = BIGI; int tn = sq[i + 1]; for (int q2 = 0; q2 < tcnt[tn]; q2++) { int w = E(o, tofs[tn] + q2) + bw[i + 1][q2]; if (w < v) v = w; } }
            bw[i][q] = v; } }
    int tj = sq[jj - 1], tk = sq[jj];
    int minP = BIGI; for (int q = 0; q < tcnt[tj]; q++) if (fw[jj - 1][q] < minP) minP = fw[jj - 1][q];
    int minZ = BIGI; for (int q = 0; q < tcnt[tk]; q++) if (bw[jj][q] < minZ) minZ = bw[jj][q];
    if (minP + minZ > THRG) return BIGI;
    int best = BIGI;
    for (int s = 0; s < NTR; s++) { if (s == jj - 1 || s == jj) continue; int T = sq[s];
        for (int q = 0; q < tcnt[T]; q++) { int oa = tofs[T] + q; if (rin[oa] < 0) continue;
            int through = fw[s][q] + bw[s][q];                         // best cost of T's part with T at a1
            int lb = s < jj ? through + minZ : minP + through; if (lb > THRG) continue;
            __atomic_add_fetch(&ncand, 1, __ATOMIC_RELAXED);
            int Ri = rin[oa], Ro = rout[oa];
            // left value: min_{o_j} Pend(o_j) + e(o_j -> R_in);  right value: min_{o_{j+1}} e(R_out -> o_{j+1}) + Zstart(o_{j+1})
            int left = BIGI, right = BIGI;
            if (s < jj) {   // forced forward from s (only a1 alive) to jj-1
                int c = 0; for (int q2 = 0; q2 < tcnt[T]; q2++) dpbuf[c][q2] = q2 == q ? fw[s][q] : BIGI;
                for (int i = s + 1; i < jj; i++) { int tp = sq[i - 1], t = sq[i], nx = c ^ 1;
                    for (int q3 = 0; q3 < tcnt[t]; q3++) { int o = tofs[t] + q3, v = BIGI; for (int q2 = 0; q2 < tcnt[tp]; q2++) { int d = dpbuf[c][q2]; if (d >= BIGI) continue; int w = d + E(tofs[tp] + q2, o); if (w < v) v = w; } dpbuf[nx][q3] = v; }
                    c = nx; }
                for (int q2 = 0; q2 < tcnt[tj]; q2++) { int d = dpbuf[c][q2]; if (d >= BIGI) continue; int w = d + E(tofs[tj] + q2, Ri); if (w < left) left = w; }
                for (int q2 = 0; q2 < tcnt[tk]; q2++) { int w = E(Ro, tofs[tk] + q2) + bw[jj][q2]; if (w < right) right = w; } }
            else {          // forced backward from s (only a1 alive) to jj
                int c = 0; for (int q2 = 0; q2 < tcnt[T]; q2++) dpbuf[c][q2] = q2 == q ? bw[s][q] : BIGI;
                for (int i = s - 1; i >= jj; i--) { int t = sq[i], tn = sq[i + 1], nx = c ^ 1;
                    for (int q3 = 0; q3 < tcnt[t]; q3++) { int o = tofs[t] + q3, v = BIGI; for (int q2 = 0; q2 < tcnt[tn]; q2++) { int d = dpbuf[c][q2]; if (d >= BIGI) continue; int w = E(o, tofs[tn] + q2) + d; if (w < v) v = w; } dpbuf[nx][q3] = v; }
                    c = nx; }
                for (int q2 = 0; q2 < tcnt[tk]; q2++) { int d = dpbuf[c][q2]; if (d >= BIGI) continue; int w = E(Ro, tofs[tk] + q2) + d; if (w < right) right = w; }
                for (int q2 = 0; q2 < tcnt[tj]; q2++) { int w = fw[jj - 1][q2] + E(tofs[tj] + q2, Ri); if (w < left) left = w; } }
            int G = left + right;
            if (G < best) best = G;
            if (G <= THRG) {
                #pragma omp critical
                { fprintf(wit, "{\"G\": %d, \"trail\": %d, \"pos\": %d, \"a1_option\": %d, \"junction_after\": %d, \"order\": [", G, T, s, q, jj);
                for (int i = 0; i < NTR; i++) fprintf(wit, "%s%d", i ? ", " : "", sq[i]); fprintf(wit, "]}\n"); fflush(wit); } }
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
    // full chains and their mid runs
    long nmid = 0;
    for (int o = 0; o < NOPT; o++) { rin[o] = rout[o] = -1; int t = otr[o], v = over_[o], m = mrun[t][v], k = okk[o]; const uint8_t *V = runp[t][v];
        if (ocut[o] != 2) continue;                                   // a1 must be inside a chain
        int s = k, guard = 0; while (ocut[tofs[t] + v * mrun[t][0] + s] == 2 && guard++ < m) s = (s + m - 1) % m;   // back to the chain start
        int L = 1; while (L < m && ocut[tofs[t] + v * mrun[t][0] + (s + L) % m] == 2) L++;
        if (L != 7) continue;
        uint8_t x[8]; const uint8_t *pe = V + 8 * ((s + 6) % m); x[0] = pe[7]; for (int i = 1; i < 8; i++) x[i] = pe[i - 1];
        if (wgt(x, V + 8 * s) != 2) continue;                          // wrap C_end -> C_start
        rin[o] = tofs[t] + v * mrun[t][0] + (s + 7) % m; rout[o] = tofs[t] + v * mrun[t][0] + s; nmid++; }
    fprintf(stderr, "mid-chain runs of full chains: %ld, setup %.1fs\n", nmid, omp_get_wtime() - T0);
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
          if (done % 50000 == 0) fprintf(stderr, "patterns %ld / %ld, best G %d, %.1fs\n", done, nl, bestG, omp_get_wtime() - T0); } }
    fclose(in); fclose(wit);
    FILE *fo = fopen(outp, "w");
    fprintf(fo, "{\"checker\": \"excise_eval\", \"THRG\": %d, \"patterns\": %ld, \"sequences\": %ld, \"candidates\": %ld, \"best_G_found_le_THRG\": %d, \"G_hist_over_patterns\": {", THRG, npat, nseq, ncand, bestG < BIGI ? bestG : -1);
    int fz = 1; for (int g = 0; g < 64; g++) if (hist[g]) { fprintf(fo, "%s\"%d\": %d", fz ? "" : ", ", g, hist[g]); fz = 0; } fprintf(fo, "}, \"sec\": %.1f}\n", omp_get_wtime() - T0); fclose(fo);
    printf("{\"patterns\": %ld, \"sequences\": %ld, \"candidates\": %ld, \"best_G\": %d}\n", npat, nseq, ncand, bestG < BIGI ? bestG : -1);
    return 0;
}
