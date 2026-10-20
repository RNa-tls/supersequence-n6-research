// Round Q, section 15 -- exact "second bracket" neighbourhood of a single split (search for G <= 20, length <= 46182).
// A single split is a path P (with the anchor S1 at option a1) plus one cycle Z1 = (S1(b1), Z1'); in the word, the two
// pieces of S1 bracket the trails of Z1'.  A second bracket takes a contiguous block B of P (not containing S1) and a
// second split trail S2 in P \ B, and closes B into the cycle Z2 = (S2(b2), B):
//     G = 2 + [cut(first) = 2] + cost(P \ B) + C1(b1) + C2(b2),
//     C(b) = min closed walk  S(b) -> block -> S(b),   a1 != b1, a2 != b2 (same versions).
// Exact over all options (dynamic programming).  Pruning uses only valid lower bounds (version-restricted DPs without
// the a != b constraints, and C2(b2) >= min e(S2(b2) -> B_first) + cost(B) + min e(B_last -> S2(b2))); every candidate
// with bound <= THRG is evaluated exactly with the a != b constraints.  Rebuilds options and e from runs.bin.
// usage: bracket2_ls DIR(runs.bin) BASE.json(line: {"order": [...30], "junction_after": j, "anchor_pos": p}) THRG OUT.json
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#define NTR 30
#define BIGI (1 << 20)
static int mrun[NTR][2]; static uint8_t *runp[NTR][2];
static int NOPT, otr[16384], over_[16384], ocut[16384], tofs[NTR], tcnt[NTR];
static uint8_t oen[16384][8], oex[16384][8]; static int8_t *e; static uint8_t *hinT[NTR], *houtT[NTR];
static int wgt(const uint8_t *x, const uint8_t *y) { for (int s = 1; s < 8; s++) { int ok = 1; for (int i = 0; s + i < 8; i++) if (x[s + i] != y[i]) { ok = 0; break; } if (ok) return s; } return 8; }
#define E(a, b) ((int)e[(size_t)(a) * NOPT + (b)])
// path DP over the sequence seq[0..n-1] (trail ids) with per-position option masks (allow[i][q]); start cost [cut = 2]
// fw[i][q] = min cost of seq[0..i] ending at q; bw[i][q] = min cost of seq[i..n-1] starting at q (free end)
static void dp_fw(const int *seq, int n, int (*fw)[1400], const char (*allow)[1400]) {
    for (int i = 0; i < n; i++) { int t = seq[i];
        for (int q = 0; q < tcnt[t]; q++) { int o = tofs[t] + q, v = BIGI;
            if (!allow[i][q]) { fw[i][q] = BIGI; continue; }
            if (i == 0) v = ocut[o] == 2;
            else { int tp = seq[i - 1]; for (int q2 = 0; q2 < tcnt[tp]; q2++) { int d = fw[i - 1][q2]; if (d >= BIGI) continue; int w = d + E(tofs[tp] + q2, o); if (w < v) v = w; } }
            fw[i][q] = v; } } }
static void dp_bw(const int *seq, int n, int (*bw)[1400], const char (*allow)[1400]) {
    for (int i = n - 1; i >= 0; i--) { int t = seq[i];
        for (int q = 0; q < tcnt[t]; q++) { int o = tofs[t] + q, v = BIGI;
            if (!allow[i][q]) { bw[i][q] = BIGI; continue; }
            if (i == n - 1) v = 0;
            else { int tn = seq[i + 1]; for (int q2 = 0; q2 < tcnt[tn]; q2++) { int d = bw[i + 1][q2]; if (d >= BIGI) continue; int w = E(o, tofs[tn] + q2) + d; if (w < v) v = w; } }
            bw[i][q] = v; } } }
// closed walk S(b) -> blk[0..nb-1] -> S(b), exact; returns BIGI if > lim
static int cycle_cost(int ob, const int *blk, int nb, int (*buf)[1400]) {
    int t0 = blk[0]; for (int q = 0; q < tcnt[t0]; q++) buf[0][q] = E(ob, tofs[t0] + q);
    for (int i = 1; i < nb; i++) { int tp = blk[i - 1], t = blk[i];
        for (int q = 0; q < tcnt[t]; q++) { int o = tofs[t] + q, v = BIGI; for (int q2 = 0; q2 < tcnt[tp]; q2++) { int w = buf[i - 1][q2] + E(tofs[tp] + q2, o); if (w < v) v = w; } buf[i][q] = v; } }
    int tl = blk[nb - 1], c = BIGI; for (int q = 0; q < tcnt[tl]; q++) { int w = buf[nb - 1][q] + E(tofs[tl] + q, ob); if (w < c) c = w; } return c; }
int main(int argc, char **argv) {
    const char *dir = argv[1], *basep = argv[2]; int THRG = atoi(argv[3]); const char *outp = argv[4]; char p[2048]; double T0 = omp_get_wtime();
    snprintf(p, sizeof p, "%s/runs.bin", dir); FILE *f = fopen(p, "rb");
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int32_t m; if (fread(&m, 4, 1, f) != 1) return 2; mrun[t][v] = m; runp[t][v] = malloc(8 * m); if (fread(runp[t][v], 1, 8 * m, f) != (size_t)(8 * m)) return 2; }
    fclose(f);
    NOPT = 0;
    for (int t = 0; t < NTR; t++) { tofs[t] = NOPT; for (int v = 0; v < 2; v++) { int m = mrun[t][v];
        for (int k = 0; k < m; k++) { int o = NOPT++; otr[o] = t; over_[o] = v; memcpy(oen[o], runp[t][v] + 8 * k, 8); const uint8_t *pr = runp[t][v] + 8 * ((k + m - 1) % m);
            oex[o][0] = pr[7]; for (int i = 1; i < 8; i++) oex[o][i] = pr[i - 1]; ocut[o] = wgt(oex[o], oen[o]); } } tcnt[t] = NOPT - tofs[t]; }
    e = malloc((size_t)NOPT * NOPT);
    #pragma omp parallel for schedule(dynamic, 16)
    for (int a = 0; a < NOPT; a++) for (int b = 0; b < NOPT; b++) e[(size_t)a * NOPT + b] = (int8_t)(wgt(oex[a], oen[b]) - ocut[b] - 1);
    #pragma omp parallel for schedule(dynamic, 1)
    for (int t = 0; t < NTR; t++) { hinT[t] = malloc(NOPT); houtT[t] = malloc(NOPT);
        for (int o = 0; o < NOPT; o++) { int mi = 127, mo = 127; if (otr[o] != t) for (int q = 0; q < tcnt[t]; q++) { int x = tofs[t] + q; int a = E(x, o), b = E(o, x); if (a < mi) mi = a; if (b < mo) mo = b; }
            hinT[t][o] = (uint8_t)(mi < 0 ? 0 : mi); houtT[t][o] = (uint8_t)(mo < 0 ? 0 : mo); } }
    // base configuration
    f = fopen(basep, "r"); char line[8192]; if (!fgets(line, sizeof line, f)) return 3; fclose(f);
    int ord[NTR], jj = -1, p1 = -1; { char *s = strstr(line, "\"order\""); s = strchr(s, '['); for (int i = 0; i < NTR; i++) { ord[i] = (int)strtol(s + 1, &s, 10); }
        s = strstr(line, "\"junction_after\""); jj = atoi(strchr(s, ':') + 1); s = strstr(line, "\"anchor_pos\""); p1 = atoi(strchr(s, ':') + 1); }
    int P[NTR], nP = jj, Z1[NTR], nZ1 = NTR - jj; for (int i = 0; i < nP; i++) P[i] = ord[i]; for (int i = 0; i < nZ1; i++) Z1[i] = ord[jj + i];
    int S1 = P[p1];
    // C1(b1) for every option b1 of S1 (exact closed walks through Z1')
    int *C1 = malloc(4 * tcnt[S1]); int C1min[2] = {BIGI, BIGI};
    { int (*buf)[1400] = malloc(sizeof(int[1400]) * NTR);
      for (int q = 0; q < tcnt[S1]; q++) { C1[q] = cycle_cost(tofs[S1] + q, Z1, nZ1, buf); int v = over_[tofs[S1] + q]; if (C1[q] < C1min[v]) C1min[v] = C1[q]; } free(buf); }
    fprintf(stderr, "base: S1 = %d at %d, junction after %d, C1 min (v0, v1) = %d, %d, setup %.1fs\n", S1, p1, jj, C1min[0], C1min[1], omp_get_wtime() - T0);
    // single-split value of the base (sanity): 1 + min_{a1 != b1} path(P) + C1(b1)
    FILE *fo = fopen(outp, "w"); fprintf(fo, "{\"base_order\": ["); for (int i = 0; i < NTR; i++) fprintf(fo, "%s%d", i ? ", " : "", ord[i]); fprintf(fo, "], \"junction_after\": %d, \"anchor_pos\": %d, \"candidates\": [\n", jj, p1);
    int bestG = BIGI; long nmoves = 0, nexact = 0; int ncand = 0;
    // moves: block B = P[i..k] (not containing p1), S2 at position s2 in P \ B, s2 != p1
    #pragma omp parallel for schedule(dynamic, 1) reduction(+:nmoves, nexact)
    for (int s2 = 0; s2 < nP; s2++) { if (s2 == p1) continue; int S2 = P[s2];
        int (*fw)[1400] = malloc(sizeof(int[1400]) * NTR), (*bw)[1400] = malloc(sizeof(int[1400]) * NTR), (*buf)[1400] = malloc(sizeof(int[1400]) * NTR);
        char (*allow)[1400] = malloc(sizeof(char[1400]) * NTR);
        for (int v1 = 0; v1 < 2; v1++) for (int v2 = 0; v2 < 2; v2++) {
            if (C1min[v1] >= BIGI) continue;
            for (int i = 0; i < nP; i++) for (int q = 0; q < tcnt[P[i]]; q++) allow[i][q] = 1;
            for (int q = 0; q < tcnt[S1]; q++) allow[p1][q] = over_[tofs[S1] + q] == v1;
            for (int q = 0; q < tcnt[S2]; q++) allow[s2][q] = over_[tofs[S2] + q] == v2;
            dp_fw(P, nP, fw, (const char (*)[1400])allow); dp_bw(P, nP, bw, (const char (*)[1400])allow);
            for (int i = 0; i < nP; i++) for (int k = i; k < nP && k < i + 12; k++) {
                if ((p1 >= i && p1 <= k) || (s2 >= i && s2 <= k)) continue;
                if (i == 0 && k == nP - 1) continue;
                nmoves++;
                // path cost of P \ B (prefix ends at i-1, suffix starts at k+1), version-restricted, no a != b constraints
                int pc = BIGI;
                if (i == 0) { for (int q = 0; q < tcnt[P[k + 1]]; q++) { int v = bw[k + 1][q]; if (v >= BIGI) continue; v += ocut[tofs[P[k + 1]] + q] == 2; if (v < pc) pc = v; } }
                else if (k == nP - 1) { for (int q = 0; q < tcnt[P[i - 1]]; q++) if (fw[i - 1][q] < pc) pc = fw[i - 1][q]; }
                else { int tp = P[i - 1], tn = P[k + 1];
                    for (int q = 0; q < tcnt[tp]; q++) { int d = fw[i - 1][q]; if (d >= BIGI) continue; const int8_t *er = e + (size_t)(tofs[tp] + q) * NOPT + tofs[tn];
                        for (int q2 = 0; q2 < tcnt[tn]; q2++) { int b = bw[k + 1][q2]; if (b >= BIGI) continue; int w = d + er[q2] + b; if (w < pc) pc = w; } } }
                if (pc >= BIGI) continue;
                // B internal minimum (free start / end) and the C2 lower bound
                int blk[NTR], nb = k - i + 1; for (int u = 0; u < nb; u++) blk[u] = P[i + u];
                int lb2 = BIGI;
                { // internal cost of B
                  int (*bb)[1400] = buf; for (int q = 0; q < tcnt[blk[0]]; q++) bb[0][q] = 0;
                  for (int u = 1; u < nb; u++) { int tp = blk[u - 1], t = blk[u]; for (int q = 0; q < tcnt[t]; q++) { int o = tofs[t] + q, v = BIGI; for (int q2 = 0; q2 < tcnt[tp]; q2++) { int w = bb[u - 1][q2] + E(tofs[tp] + q2, o); if (w < v) v = w; } bb[u][q] = v; } }
                  int intB = BIGI; for (int q = 0; q < tcnt[blk[nb - 1]]; q++) if (bb[nb - 1][q] < intB) intB = bb[nb - 1][q];
                  for (int q = 0; q < tcnt[S2]; q++) { int ob = tofs[S2] + q; if (over_[ob] != v2) continue; int c = houtT[blk[0]][ob] + intB + hinT[blk[nb - 1]][ob]; if (c < lb2) lb2 = c; } }
                int LB = 2 + pc + C1min[v1] + lb2;
                if (LB > THRG) continue;
                // exact: enumerate b2 (version v2) with bound small enough, exact C2(b2); then exact path with a1 != b1, a2 != b2
                for (int q2 = 0; q2 < tcnt[S2]; q2++) { int ob2 = tofs[S2] + q2; if (over_[ob2] != v2) continue;
                    if (2 + pc + C1min[v1] + houtT[blk[0]][ob2] + hinT[blk[nb - 1]][ob2] > THRG) continue;
                    int c2 = cycle_cost(ob2, blk, nb, buf); if (2 + pc + C1min[v1] + c2 > THRG) continue;
                    for (int q1 = 0; q1 < tcnt[S1]; q1++) { int ob1 = tofs[S1] + q1; if (over_[ob1] != v1) continue; if (2 + pc + C1[q1] + c2 > THRG) continue;
                        nexact++;
                        // exact path of P \ B with S1 in v1 minus b1, S2 in v2 minus b2
                        int seq[NTR], ns = 0, ps1 = -1, ps2 = -1; for (int u = 0; u < nP; u++) { if (u >= i && u <= k) continue; if (u == p1) ps1 = ns; if (u == s2) ps2 = ns; seq[ns++] = P[u]; }
                        char (*al2)[1400] = malloc(sizeof(char[1400]) * NTR); int (*f2)[1400] = malloc(sizeof(int[1400]) * NTR);
                        for (int u = 0; u < ns; u++) for (int q = 0; q < tcnt[seq[u]]; q++) al2[u][q] = 1;
                        for (int q = 0; q < tcnt[S1]; q++) al2[ps1][q] = over_[tofs[S1] + q] == v1 && q != q1;
                        for (int q = 0; q < tcnt[S2]; q++) al2[ps2][q] = over_[tofs[S2] + q] == v2 && q != q2;
                        dp_fw(seq, ns, f2, (const char (*)[1400])al2); int pe = BIGI; for (int q = 0; q < tcnt[seq[ns - 1]]; q++) if (f2[ns - 1][q] < pe) pe = f2[ns - 1][q];
                        free(al2); free(f2);
                        int G = 2 + pe + C1[q1] + c2;
                        if (G <= THRG) {
                            #pragma omp critical
                            { if (G < bestG) bestG = G;
                              fprintf(fo, "%s{\"G\": %d, \"S2\": %d, \"s2\": %d, \"block\": [%d, %d], \"v1\": %d, \"b1\": %d, \"v2\": %d, \"b2\": %d, \"path\": %d, \"C1\": %d, \"C2\": %d}", ncand ? ",\n" : "", G, S2, s2, i, k, v1, q1, v2, q2, pe, C1[q1], c2); ncand++; fflush(fo); } } } }
            } }
        free(fw); free(bw); free(buf); free(allow); }
    fprintf(fo, "\n], \"moves\": %ld, \"exact_evaluations\": %ld, \"best_G_le_THRG\": %d, \"sec\": %.1f}\n", nmoves, nexact, bestG < BIGI ? bestG : -1, omp_get_wtime() - T0); fclose(fo);
    printf("{\"moves\": %ld, \"exact_evaluations\": %ld, \"candidates\": %d, \"best_G\": %d}\n", nmoves, nexact, ncand, bestG < BIGI ? bestG : -1);
    return 0;
}
