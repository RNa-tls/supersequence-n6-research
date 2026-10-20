// Round Q, section 6.2 -- exact F_J of given trail orders at every junction position (a check of the junction lemma).
// F_J(SIGMA, j) = min over options of [cut(o_1) = 2] + sum of the SIGMA edges except (j, j+1)
//              = (exact minimum of the prefix path o_1..o_j, word start) + (exact minimum of the suffix path, free start).
// Rebuilds options and e from runs.bin.  Prints, per order, F and min_j F_J, and the histogram of min_j F_J.
// usage: fj_orders DIR(runs.bin) ORDERS.txt OUT.json
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#define NTR 30
#define BIGI (1 << 28)
static int mrun[NTR][2]; static uint8_t *runp[NTR][2];
static int NOPT, otr[16384], ocut[16384], tofs[NTR], tcnt[NTR]; static uint8_t oen[16384][8], oex[16384][8]; static int8_t *e;
static int wgt(const uint8_t *x, const uint8_t *y) { for (int s = 1; s < 8; s++) { int ok = 1; for (int i = 0; s + i < 8; i++) if (x[s + i] != y[i]) { ok = 0; break; } if (ok) return s; } return 8; }
int main(int argc, char **argv) {
    const char *dir = argv[1], *ordp = argv[2], *outp = argv[3]; char p[2048];
    snprintf(p, sizeof p, "%s/runs.bin", dir); FILE *f = fopen(p, "rb");
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int32_t m; if (fread(&m, 4, 1, f) != 1) return 2; mrun[t][v] = m; runp[t][v] = malloc(8 * m); if (fread(runp[t][v], 1, 8 * m, f) != (size_t)(8 * m)) return 2; }
    fclose(f);
    NOPT = 0;
    for (int t = 0; t < NTR; t++) { tofs[t] = NOPT; for (int v = 0; v < 2; v++) { int m = mrun[t][v];
        for (int k = 0; k < m; k++) { int o = NOPT++; otr[o] = t; memcpy(oen[o], runp[t][v] + 8 * k, 8); const uint8_t *pr = runp[t][v] + 8 * ((k + m - 1) % m);
            oex[o][0] = pr[7]; for (int i = 1; i < 8; i++) oex[o][i] = pr[i - 1]; ocut[o] = wgt(oex[o], oen[o]); } } tcnt[t] = NOPT - tofs[t]; }
    e = malloc((size_t)NOPT * NOPT);
    #pragma omp parallel for schedule(dynamic, 16)
    for (int a = 0; a < NOPT; a++) for (int b = 0; b < NOPT; b++) e[(size_t)a * NOPT + b] = (int8_t)(wgt(oex[a], oen[b]) - ocut[b] - 1);
    f = fopen(ordp, "r"); int cap = 4096, no = 0; int (*ord)[NTR] = malloc(sizeof(int[NTR]) * cap);
    while (1) { int ok = 1; for (int k = 0; k < NTR; k++) if (fscanf(f, "%d%*[, ]", &ord[no][k]) != 1) { ok = 0; break; } if (!ok) break; no++; if (no == cap) { cap *= 2; ord = realloc(ord, sizeof(int[NTR]) * cap); } }
    fclose(f);
    int *Fo = malloc(4 * no), *FJo = malloc(4 * no), *Jo = malloc(4 * no);
    #pragma omp parallel for schedule(dynamic, 1)
    for (int oi = 0; oi < no; oi++) { const int *pi = ord[oi];
        // pre[i][q]: min cost of o_1..o_i ending at option q (word start); suf[i][q]: min cost of o_i..o_30 from q (free start)
        int (*pre)[1400] = malloc(sizeof(int[1400]) * NTR), (*suf)[1400] = malloc(sizeof(int[1400]) * NTR);
        for (int q = 0; q < tcnt[pi[0]]; q++) pre[0][q] = ocut[tofs[pi[0]] + q] == 2;
        for (int i = 1; i < NTR; i++) { int a = pi[i - 1], b = pi[i]; for (int q2 = 0; q2 < tcnt[b]; q2++) pre[i][q2] = BIGI;
            for (int q = 0; q < tcnt[a]; q++) { int v = pre[i - 1][q]; const int8_t *er = e + (size_t)(tofs[a] + q) * NOPT + tofs[b];
                for (int q2 = 0; q2 < tcnt[b]; q2++) { int c = v + er[q2]; if (c < pre[i][q2]) pre[i][q2] = c; } } }
        for (int q = 0; q < tcnt[pi[NTR - 1]]; q++) suf[NTR - 1][q] = 0;
        for (int i = NTR - 2; i >= 0; i--) { int a = pi[i], b = pi[i + 1];
            for (int q = 0; q < tcnt[a]; q++) { int best = BIGI; const int8_t *er = e + (size_t)(tofs[a] + q) * NOPT + tofs[b];
                for (int q2 = 0; q2 < tcnt[b]; q2++) { int c = er[q2] + suf[i + 1][q2]; if (c < best) best = c; } suf[i][q] = best; } }
        int F = BIGI; for (int q = 0; q < tcnt[pi[NTR - 1]]; q++) if (pre[NTR - 1][q] < F) F = pre[NTR - 1][q];
        int best = BIGI, bj = -1;
        for (int j = 1; j < NTR; j++) { int mp = BIGI, ms = BIGI;      // junction after j elements
            for (int q = 0; q < tcnt[pi[j - 1]]; q++) if (pre[j - 1][q] < mp) mp = pre[j - 1][q];
            for (int q = 0; q < tcnt[pi[j]]; q++) if (suf[j][q] < ms) ms = suf[j][q];
            if (mp + ms < best) { best = mp + ms; bj = j; } }
        Fo[oi] = F; FJo[oi] = best; Jo[oi] = bj; free(pre); free(suf); }
    int hist[64] = {0}, mn = BIGI, mi = -1; for (int oi = 0; oi < no; oi++) { if (FJo[oi] < 64) hist[FJo[oi]]++; if (FJo[oi] < mn) { mn = FJo[oi]; mi = oi; } }
    FILE *fo = fopen(outp, "w"); fprintf(fo, "{\"orders\": %d, \"min_FJ\": %d, \"argmin_order\": %d, \"argmin_F\": %d, \"argmin_junction_after\": %d, \"minFJ_hist\": {", no, mn, mi, Fo[mi], Jo[mi]);
    int fz = 1; for (int g = 0; g < 64; g++) if (hist[g]) { fprintf(fo, "%s\"%d\": %d", fz ? "" : ", ", g, hist[g]); fz = 0; } fprintf(fo, "}, \"per_order\": [");
    for (int oi = 0; oi < no; oi++) fprintf(fo, "%s[%d, %d, %d]", oi ? ", " : "", Fo[oi], FJo[oi], Jo[oi]); fprintf(fo, "]}\n"); fclose(fo);
    printf("{\"orders\": %d, \"min_FJ\": %d, \"argmin_F\": %d}\n", no, mn, Fo[mi]);
    return 0;
}
