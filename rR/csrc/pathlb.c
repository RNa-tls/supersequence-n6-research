// Round S -- relaxed lower bounds for PARTIAL paths, read off the backward table H of Round P checker B (rP/csrc/ckB.c).
// H(S, t, c)[o] = relaxed (A identities free, consecutive A trails distinct) minimum of the rest of a single-opening
// path after phi trail t (option o) that visits the phi trails outside S and exactly c more A trails.
// A path (the path component of a bracket tree, or the mains of a cover cycle in their order) through a set Q of phi
// trails and n_A A trails therefore costs at least
//     min over t in Q, a <= n_A, o :  S_a[t][o] + H((complement of Q) + t, t, n_A - a)[o],
// S_a = start chain of a A trails into (t, o).  Two versions of the start chain:
//     F   : with the first-piece term [cut(first option) = 2]            (path component of a route)
//     F0  : without it                                                   (the mains z_1 .. z_k of a cover cycle)
// This program takes the minimum over ALL phi sets of each size:  F[n_phi][n_A], F0[n_phi][n_A]  (n_phi >= 1), and the
// A-only chains FA[n_A], FA0[n_A].  They are valid lower bounds for every phi set of that size.
// usage: pathlb DIR(runs.bin) HDIR(H%02d.key/.val, meta.bin) OUT.json
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#define NTR 30
#define NPH 24
#define NOP 84
#define NOR 42
#define NCN 7
#define BIG 200
#define VSZ (NCN * NOR)
static int mrun[NTR][2]; static uint8_t *runp[NTR][2];
static int NOPT, otr[16384], ocut[16384], tofs[NTR], tcnt[NTR], isA[NTR], Alist[6], nA; static uint8_t oen[16384][8], oex[16384][8]; static int8_t *e;
static int wgt(const uint8_t *x, const uint8_t *y) { for (int s = 1; s < 8; s++) { int ok = 1; for (int i = 0; s + i < 8; i++) if (x[s + i] != y[i]) { ok = 0; break; } if (ok) return s; } return 8; }
int main(int argc, char **argv) {
    if (argc < 4) { fprintf(stderr, "usage: pathlb DIR HDIR OUT.json\n"); return 1; }
    char p[2048]; snprintf(p, sizeof p, "%s/runs.bin", argv[1]); FILE *f = fopen(p, "rb"); if (!f) return 2;
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int32_t m; if (fread(&m, 4, 1, f) != 1) return 2; mrun[t][v] = m; runp[t][v] = malloc(8 * m); if (fread(runp[t][v], 1, 8 * m, f) != (size_t)(8 * m)) return 2; }
    fclose(f);
    NOPT = 0;
    for (int t = 0; t < NTR; t++) { tofs[t] = NOPT; for (int v = 0; v < 2; v++) { int m = mrun[t][v];
        for (int k = 0; k < m; k++) { int o = NOPT++; otr[o] = t; memcpy(oen[o], runp[t][v] + 8 * k, 8); const uint8_t *pr = runp[t][v] + 8 * ((k + m - 1) % m);
            oex[o][0] = pr[7]; for (int i = 1; i < 8; i++) oex[o][i] = pr[i - 1]; ocut[o] = wgt(oex[o], oen[o]); } } tcnt[t] = NOPT - tofs[t]; }
    nA = 0; for (int t = 0; t < NTR; t++) { isA[t] = mrun[t][0] > 100; if (isA[t]) Alist[nA++] = t; }
    e = malloc((size_t)NOPT * NOPT);
    #pragma omp parallel for schedule(dynamic, 16)
    for (int a = 0; a < NOPT; a++) for (int b = 0; b < NOPT; b++) e[(size_t)a * NOPT + b] = (int8_t)(wgt(oex[a], oen[b]) - ocut[b] - 1);
    int phl[NPH], ptrs[6][NPH], orep[NPH][NOR];
    snprintf(p, sizeof p, "%s/meta.bin", argv[2]); f = fopen(p, "rb"); if (!f) return 2;
    if (fread(phl, 4, NPH, f) != NPH || fread(ptrs, 4, 6 * NPH, f) != 6 * NPH || fread(orep, 4, NPH * NOR, f) != NPH * NOR) return 2; fclose(f);
    for (int i = 0; i < NPH; i++) if (isA[phl[i]] || tcnt[phl[i]] != NOP) return 3;
    // start chains: Sv[var][a][t][i], var 0 = with the first-piece term, var 1 = without;  A-only chains FA[var][a]
    int NAO = tcnt[Alist[0]]; static int Sv[2][NCN][NPH][NOR]; int FA[2][NCN];
    for (int var = 0; var < 2; var++) {
        int *cur = malloc(sizeof(int) * 6 * NAO), *nx = malloc(sizeof(int) * 6 * NAO);
        for (int t = 0; t < NPH; t++) for (int i = 0; i < NOR; i++) { int o = tofs[phl[t]] + orep[t][i]; Sv[var][0][t][i] = var ? 0 : (ocut[o] == 2); }
        for (int a = 0; a < 6; a++) for (int q = 0; q < NAO; q++) cur[a * NAO + q] = var ? 0 : (ocut[tofs[Alist[a]] + q] == 2);
        FA[var][0] = 0;
        for (int len = 1; len <= 6; len++) {
            int mn = BIG; for (int i = 0; i < 6 * NAO; i++) if (cur[i] < mn) mn = cur[i]; FA[var][len] = mn;
            for (int t = 0; t < NPH; t++) for (int i = 0; i < NOR; i++) { int o = tofs[phl[t]] + orep[t][i]; int best = BIG;
                for (int a = 0; a < 6; a++) for (int q = 0; q < NAO; q++) { int v = cur[a * NAO + q]; if (v >= BIG) continue; int w = v + e[(size_t)(tofs[Alist[a]] + q) * NOPT + o]; if (w < best) best = w; }
                Sv[var][len][t][i] = best; }
            if (len == 6) break;
            for (int i = 0; i < 6 * NAO; i++) nx[i] = BIG;
            #pragma omp parallel for schedule(dynamic, 1)
            for (int b = 0; b < 6; b++) for (int a = 0; a < 6; a++) { if (a == b) continue;
                for (int q = 0; q < NAO; q++) { int v = cur[a * NAO + q]; if (v >= BIG) continue; const int8_t *er = e + (size_t)(tofs[Alist[a]] + q) * NOPT + tofs[Alist[b]];
                    for (int r = 0; r < NAO; r++) { int w = v + er[r]; if (w < nx[b * NAO + r]) nx[b * NAO + r] = w; } } }
            int *tt = cur; cur = nx; nx = tt; }
        free(cur); free(nx); }
    static int F[2][NPH + 1][NCN]; for (int v = 0; v < 2; v++) for (int n = 0; n <= NPH; n++) for (int c = 0; c < NCN; c++) F[v][n][c] = BIG;
    long total_states = 0;
    for (int k = 1; k <= NPH; k++) {
        snprintf(p, sizeof p, "%s/H%02d.key", argv[2], k); FILE *fk = fopen(p, "rb"); snprintf(p, sizeof p, "%s/H%02d.val", argv[2], k); FILE *fv = fopen(p, "rb"); if (!fk || !fv) return 4;
        fseek(fk, 0, SEEK_END); long n = ftell(fk) / 8; fseek(fk, 0, SEEK_SET);
        uint64_t *keys = malloc(8 * (n + 1)); if (fread(keys, 8, n, fk) != (size_t)n) return 4; fclose(fk);
        long chunk = 1 << 16; uint8_t *buf = malloc(chunk * VSZ); int nphi = NPH - k + 1; long done = 0;
        while (done < n) { long m = n - done < chunk ? n - done : chunk; if (fread(buf, VSZ, m, fv) != (size_t)m) return 4;
            int loc[2][NCN]; for (int v = 0; v < 2; v++) for (int c = 0; c < NCN; c++) loc[v][c] = BIG;
            #pragma omp parallel
            { int l2[2][NCN]; for (int v = 0; v < 2; v++) for (int c = 0; c < NCN; c++) l2[v][c] = BIG;
              #pragma omp for schedule(static)
              for (long x = 0; x < m; x++) { int t = keys[done + x] & 31; const uint8_t *hv = buf + x * VSZ;
                  for (int var = 0; var < 2; var++) for (int c = 0; c < NCN; c++) { int best = l2[var][c];
                      for (int a = 0; a <= c; a++) { const uint8_t *h = hv + (c - a) * NOR; const int *s = Sv[var][a][t];
                          for (int i = 0; i < NOR; i++) { int w = s[i] + h[i]; if (w < best) best = w; } }
                      l2[var][c] = best; } }
              #pragma omp critical
              for (int v = 0; v < 2; v++) for (int c = 0; c < NCN; c++) if (l2[v][c] < loc[v][c]) loc[v][c] = l2[v][c]; }
            for (int v = 0; v < 2; v++) for (int c = 0; c < NCN; c++) if (loc[v][c] < F[v][nphi][c]) F[v][nphi][c] = loc[v][c];
            done += m; }
        fclose(fv); free(keys); free(buf); total_states += n;
        fprintf(stderr, "layer %d (%d phi trails on the path): %ld canonical states;  F = ", k, nphi, n); for (int c = 0; c < NCN; c++) fprintf(stderr, "%d ", F[0][nphi][c]); fprintf(stderr, "\n");
    }
    FILE *o = fopen(argv[3], "w");
    fprintf(o, "{\"source\": \"backward table H of rP/csrc/ckB.c (relaxed A identities), minimum over all phi sets of each size\", \"canonical_states_read\": %ld,\n", total_states);
    for (int var = 0; var < 2; var++) { fprintf(o, " \"%s\": {", var ? "F0_without_first_piece_term" : "F_with_first_piece_term");
        for (int n = 1; n <= NPH; n++) { fprintf(o, "%s\"%d\": [", n > 1 ? ", " : "", n); for (int c = 0; c < NCN; c++) fprintf(o, "%s%d", c ? ", " : "", F[var][n][c]); fprintf(o, "]"); }
        fprintf(o, "},\n \"%s\": [", var ? "FA0_A_only_chain_without_term" : "FA_A_only_chain_with_term"); for (int c = 0; c < NCN; c++) fprintf(o, "%s%d", c ? ", " : "", FA[var][c]); fprintf(o, "]%s\n", var ? "" : ","); }
    fprintf(o, "}\n"); fclose(o);
    printf("relaxed optimum of the full path F[24][6] = %d\n", F[0][NPH][6]);
    return 0;
}
