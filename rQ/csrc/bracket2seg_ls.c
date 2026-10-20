// Round Q, section 15 -- exact "second bracket from two blocks" neighbourhood of a single split (search for G <= 20).
// The 46183 words arise from the single-opening word a by moving TWO separate blocks of the order (trail 8 and the
// block 11 12 13) into the bracket of A trail 22.  This program applies the same kind of move a second time: from the
// path P of a single split (first bracket S1 with cycle Z1 kept), two disjoint blocks B1 = P[i1..k1], B2 = P[i2..k2]
// (k1 + 1 < i2, lengths <= LMAX) are removed and closed into a cycle through a second split trail S2 in the rest:
//     G = 2 + [cut(first) = 2] + cost(P \ (B1 u B2)) + C1(b1) + C2(b2),
//     C2(b2) = min closed walk S2(b2) -> B1 -> B2 -> S2(b2)   (also the order B2 then B1),   a != b, same versions.
// Exact over all options.  Pruning by valid lower bounds only:
//   cost(P \ B) >= m(0, i1-1) + m(k1+1, i2-1) + m(k2+1, n-1)  (exact free-end minima of the three remaining segments,
//   the first with [cut = 2]; the two new joins are >= 0),
//   C2(b2) >= houtT[first block trail][b2] + int(B1) + int(B2) + hinT[last block trail][b2].
// Candidates passing the bound are evaluated by full DPs with the a != b constraints.
// usage: bracket2seg_ls DIR(runs.bin) BASE.json THRG LMAX OUT.json
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
// exact min cost of the path seq[0..n-1] with option masks; start cost [cut = 2] if wstart
static int pathmin(const int *seq, int n, const char (*allow)[1400], int wstart, int (*buf)[1400]) {
    for (int i = 0; i < n; i++) { int t = seq[i];
        for (int q = 0; q < tcnt[t]; q++) { int o = tofs[t] + q, v = BIGI;
            if (!allow[i][q]) { buf[i & 1][q] = BIGI; continue; }
            if (i == 0) v = wstart ? (ocut[o] == 2) : 0;
            else { int tp = seq[i - 1]; for (int q2 = 0; q2 < tcnt[tp]; q2++) { int d = buf[(i - 1) & 1][q2]; if (d >= BIGI) continue; int w = d + E(tofs[tp] + q2, o); if (w < v) v = w; } }
            buf[i & 1][q] = v; } }
    int m = BIGI, t = seq[n - 1]; for (int q = 0; q < tcnt[t]; q++) if (buf[(n - 1) & 1][q] < m) m = buf[(n - 1) & 1][q]; return m; }
static int cycle_cost(int ob, const int *blk, int nb, int (*buf)[1400]) {
    int t0 = blk[0]; for (int q = 0; q < tcnt[t0]; q++) buf[0][q] = E(ob, tofs[t0] + q);
    for (int i = 1; i < nb; i++) { int tp = blk[i - 1], t = blk[i];
        for (int q = 0; q < tcnt[t]; q++) { int o = tofs[t] + q, v = BIGI; for (int q2 = 0; q2 < tcnt[tp]; q2++) { int w = buf[(i - 1) & 1][q2] + E(tofs[tp] + q2, o); if (w < v) v = w; } buf[i & 1][q] = v; } }
    int tl = blk[nb - 1], c = BIGI; for (int q = 0; q < tcnt[tl]; q++) { int w = buf[(nb - 1) & 1][q] + E(tofs[tl] + q, ob); if (w < c) c = w; } return c; }
int main(int argc, char **argv) {
    const char *dir = argv[1], *basep = argv[2]; int THRG = atoi(argv[3]), LMAX = atoi(argv[4]); const char *outp = argv[5]; char p[2048]; double T0 = omp_get_wtime();
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
    f = fopen(basep, "r"); char line[8192]; if (!fgets(line, sizeof line, f)) return 3; fclose(f);
    int ord[NTR], jj = -1, p1 = -1; { char *s = strstr(line, "\"order\""); s = strchr(s, '['); for (int i = 0; i < NTR; i++) ord[i] = (int)strtol(s + 1, &s, 10);
        s = strstr(line, "\"junction_after\""); jj = atoi(strchr(s, ':') + 1); s = strstr(line, "\"anchor_pos\""); p1 = atoi(strchr(s, ':') + 1); }
    int P[NTR], n = jj, Z1[NTR], nZ1 = NTR - jj; for (int i = 0; i < n; i++) P[i] = ord[i]; for (int i = 0; i < nZ1; i++) Z1[i] = ord[jj + i];
    int S1 = P[p1];
    int (*gbuf)[1400] = malloc(sizeof(int[1400]) * 2);
    int *C1 = malloc(4 * tcnt[S1]); int C1min[2] = {BIGI, BIGI};
    for (int q = 0; q < tcnt[S1]; q++) { C1[q] = cycle_cost(tofs[S1] + q, Z1, nZ1, gbuf); int v = over_[tofs[S1] + q]; if (C1[q] < C1min[v]) C1min[v] = C1[q]; }
    // segment minima m[v1][a][b] (free end; [cut = 2] if a == 0; S1 restricted to version v1 when inside), and block internals
    static int segm[2][NTR][NTR];
    for (int v1 = 0; v1 < 2; v1++)
        #pragma omp parallel for schedule(dynamic, 1)
        for (int a = 0; a < n; a++) { int (*buf)[1400] = malloc(sizeof(int[1400]) * 2); char (*al)[1400] = malloc(sizeof(char[1400]) * NTR);
            for (int b = a; b < n; b++) { int seq[NTR], ns = 0; for (int u = a; u <= b; u++) { int t = P[u]; for (int q = 0; q < tcnt[t]; q++) al[ns][q] = (u == p1) ? over_[tofs[t] + q] == v1 : 1; seq[ns++] = t; }
                segm[v1][a][b] = pathmin(seq, ns, (const char (*)[1400])al, a == 0, buf); }
            free(buf); free(al); }
    static int intm[NTR][NTR];   // free start / free end internal minimum of a block (no S1 inside blocks)
    #pragma omp parallel for schedule(dynamic, 1)
    for (int a = 0; a < n; a++) { int (*buf)[1400] = malloc(sizeof(int[1400]) * 2); char (*al)[1400] = malloc(sizeof(char[1400]) * NTR);
        for (int b = a; b < n && b < a + LMAX; b++) { int seq[NTR], ns = 0; for (int u = a; u <= b; u++) { for (int q = 0; q < tcnt[P[u]]; q++) al[ns][q] = 1; seq[ns++] = P[u]; }
            intm[a][b] = pathmin(seq, ns, (const char (*)[1400])al, 0, buf); }
        free(buf); free(al); }
    fprintf(stderr, "base S1 = %d at %d, C1 min %d %d, tables %.1fs\n", S1, p1, C1min[0], C1min[1], omp_get_wtime() - T0);
    FILE *fo = fopen(outp, "w"); fprintf(fo, "{\"base_order\": ["); for (int i = 0; i < NTR; i++) fprintf(fo, "%s%d", i ? ", " : "", ord[i]); fprintf(fo, "], \"junction_after\": %d, \"anchor_pos\": %d, \"LMAX\": %d, \"candidates\": [\n", jj, p1, LMAX);
    long nmoves = 0, npass = 0, nexact = 0; int bestG = BIGI, ncand = 0;
    #pragma omp parallel for schedule(dynamic, 1) reduction(+:nmoves, npass, nexact) collapse(2)
    for (int i1 = 0; i1 < n; i1++) for (int i2 = 0; i2 < n; i2++) {
        if (i2 < i1 + 2) continue;
        int (*buf)[1400] = malloc(sizeof(int[1400]) * 2); char (*al)[1400] = malloc(sizeof(char[1400]) * NTR);
        for (int k1 = i1; k1 < i1 + LMAX && k1 < i2 - 1; k1++) for (int k2 = i2; k2 < i2 + LMAX && k2 < n; k2++) {
            if ((p1 >= i1 && p1 <= k1) || (p1 >= i2 && p1 <= k2)) continue;
            if (i1 == 0 && k2 == n - 1 && k1 + 1 > i2 - 1) continue;
            int blk[NTR], nb = 0; for (int u = i1; u <= k1; u++) blk[nb++] = P[u]; int nb1 = nb; for (int u = i2; u <= k2; u++) blk[nb++] = P[u];
            int ib = intm[i1][k1] + intm[i2][k2];
            for (int v1 = 0; v1 < 2; v1++) { if (C1min[v1] >= BIGI) continue;
                // remaining segments: [0, i1-1], [k1+1, i2-1], [k2+1, n-1]
                int sl = 0; if (i1 > 0) sl += segm[v1][0][i1 - 1]; sl += (i1 == 0) ? segm[v1][k1 + 1][i2 - 1] : (k1 + 1 <= i2 - 1 ? segm[v1][k1 + 1][i2 - 1] - 0 : 0);
                if (i1 == 0) { /* the middle segment is first: its value already carries [cut = 2] */ }
                if (k2 + 1 <= n - 1) sl += segm[v1][k2 + 1][n - 1];
                for (int s2 = 0; s2 < n; s2++) { if (s2 == p1 || (s2 >= i1 && s2 <= k1) || (s2 >= i2 && s2 <= k2)) continue; int S2 = P[s2];
                    for (int v2 = 0; v2 < 2; v2++) { nmoves++;
                        int lbc = BIGI; for (int q = 0; q < tcnt[S2]; q++) { int ob = tofs[S2] + q; if (over_[ob] != v2) continue; int c = houtT[blk[0]][ob] + hinT[blk[nb - 1]][ob]; if (c < lbc) lbc = c; }
                        int lbc2 = BIGI; for (int q = 0; q < tcnt[S2]; q++) { int ob = tofs[S2] + q; if (over_[ob] != v2) continue; int c = houtT[blk[nb1]][ob] + hinT[blk[nb1 - 1]][ob]; if (c < lbc2) lbc2 = c; }
                        int lbcyc = (lbc < lbc2 ? lbc : lbc2) + ib;
                        if (2 + sl + C1min[v1] + lbcyc > THRG) continue;
                        npass++;
                        // exact: remaining path with S1 in v1 and S2 in v2 (no a != b yet) for a tighter bound
                        int seq[NTR], ns = 0, ps1 = -1, ps2 = -1; for (int u = 0; u < n; u++) { if ((u >= i1 && u <= k1) || (u >= i2 && u <= k2)) continue; if (u == p1) ps1 = ns; if (u == s2) ps2 = ns; seq[ns++] = P[u]; }
                        for (int u = 0; u < ns; u++) for (int q = 0; q < tcnt[seq[u]]; q++) al[u][q] = 1;
                        for (int q = 0; q < tcnt[S1]; q++) al[ps1][q] = over_[tofs[S1] + q] == v1;
                        for (int q = 0; q < tcnt[S2]; q++) al[ps2][q] = over_[tofs[S2] + q] == v2;
                        int pc = pathmin(seq, ns, (const char (*)[1400])al, 1, buf); if (2 + pc + C1min[v1] + lbcyc > THRG) continue;
                        for (int ordr = 0; ordr < 2; ordr++) {   // cycle order: B1 B2 or B2 B1
                            int cb[NTR], nc = 0; if (!ordr) { for (int u = 0; u < nb; u++) cb[nc++] = blk[u]; } else { for (int u = nb1; u < nb; u++) cb[nc++] = blk[u]; for (int u = 0; u < nb1; u++) cb[nc++] = blk[u]; }
                            for (int q2 = 0; q2 < tcnt[S2]; q2++) { int ob2 = tofs[S2] + q2; if (over_[ob2] != v2) continue;
                                if (2 + pc + C1min[v1] + houtT[cb[0]][ob2] + hinT[cb[nc - 1]][ob2] + ib > THRG) continue;
                                int c2 = cycle_cost(ob2, cb, nc, buf); if (2 + pc + C1min[v1] + c2 > THRG) continue;
                                for (int q1 = 0; q1 < tcnt[S1]; q1++) { int ob1 = tofs[S1] + q1; if (over_[ob1] != v1 || 2 + pc + C1[q1] + c2 > THRG) continue;
                                    nexact++;
                                    for (int q = 0; q < tcnt[S1]; q++) al[ps1][q] = over_[tofs[S1] + q] == v1 && q != q1;
                                    for (int q = 0; q < tcnt[S2]; q++) al[ps2][q] = over_[tofs[S2] + q] == v2 && q != q2;
                                    int pe = pathmin(seq, ns, (const char (*)[1400])al, 1, buf);
                                    for (int q = 0; q < tcnt[S1]; q++) al[ps1][q] = over_[tofs[S1] + q] == v1;
                                    for (int q = 0; q < tcnt[S2]; q++) al[ps2][q] = over_[tofs[S2] + q] == v2;
                                    int G = 2 + pe + C1[q1] + c2;
                                    if (G <= THRG) {
                                        #pragma omp critical
                                        { if (G < bestG) bestG = G;
                                          fprintf(fo, "%s{\"G\": %d, \"S2\": %d, \"s2\": %d, \"B1\": [%d, %d], \"B2\": [%d, %d], \"cycle_order\": %d, \"v1\": %d, \"b1\": %d, \"v2\": %d, \"b2\": %d, \"path\": %d, \"C1\": %d, \"C2\": %d}",
                                                  ncand ? ",\n" : "", G, S2, s2, i1, k1, i2, k2, ordr, v1, q1, v2, q2, pe, C1[q1], c2); ncand++; fflush(fo); } } } } } } } } }
        free(buf); free(al); }
    fprintf(fo, "\n], \"moves\": %ld, \"passed_bound\": %ld, \"exact_evaluations\": %ld, \"best_G_le_THRG\": %d, \"sec\": %.1f}\n", nmoves, npass, nexact, bestG < BIGI ? bestG : -1, omp_get_wtime() - T0); fclose(fo);
    printf("{\"moves\": %ld, \"passed_bound\": %ld, \"exact_evaluations\": %ld, \"candidates\": %d, \"best_G\": %d}\n", nmoves, npass, nexact, ncand, bestG < BIGI ? bestG : -1);
    return 0;
}
