// Round Q, section 22 -- the rotated-chain ("wrap") excision neighbourhood around many single-opening orders.
// For every trail order (30 trail ids per line): optimal options by the fixed-order DP (one optimal assignment),
// the run route of that single-opening word, then for every trail T, every FULL chain C of T's version (7 runs,
// w2 wrap) and every rotation a of C:
//   move A: T's block := C rotated at a (a1..C_end, C_start..a1-1), the rest R = T minus C (version order) inserted
//           at the best gap of the route (any gap outside the rotated chain, both ends included);
//   move B: T's block := R, the rotated chain inserted at the best gap.
// Every move is a valid multi-opening word; the length change is exact (run weights).  Reports, per order, the
// best change and the number of moves with change <= 0; prints every move with change < 0.
// usage: order_excise DIR(runs.bin) ORDERS.txt OUT.json
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#define NTR 30
#define BIGI (1 << 28)
static int mrun[NTR][2]; static uint8_t *runp[NTR][2];
static int NOPT, otr[16384], over_[16384], okk[16384], ocut[16384], tofs[NTR], tcnt[NTR]; static uint8_t oen[16384][8], oex[16384][8]; static int8_t *e;
static int wgt(const uint8_t *x, const uint8_t *y) { for (int s = 1; s < 8; s++) { int ok = 1; for (int i = 0; s + i < 8; i++) if (x[s + i] != y[i]) { ok = 0; break; } if (ok) return s; } return 8; }
static inline void lastp(const uint8_t *s, uint8_t *x) { x[0] = s[7]; for (int i = 1; i < 8; i++) x[i] = s[i - 1]; }
static inline int wr(const uint8_t *a, const uint8_t *b) { uint8_t x[8]; lastp(a, x); return wgt(x, b); }   // join run a -> run b
typedef struct { long nle0, nlt0; int best; int bt, bc, ba, bkind, bv, verified; } Res;
int main(int argc, char **argv) {
    const char *dir = argv[1], *ordp = argv[2], *outp = argv[3]; char p[2048]; double T0 = omp_get_wtime();
    snprintf(p, sizeof p, "%s/runs.bin", dir); FILE *f = fopen(p, "rb");
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int32_t m; if (fread(&m, 4, 1, f) != 1) return 2; mrun[t][v] = m; runp[t][v] = malloc(8 * m); if (fread(runp[t][v], 1, 8 * m, f) != (size_t)(8 * m)) return 2; }
    fclose(f);
    NOPT = 0;
    for (int t = 0; t < NTR; t++) { tofs[t] = NOPT; for (int v = 0; v < 2; v++) { int m = mrun[t][v];
        for (int k = 0; k < m; k++) { int o = NOPT++; otr[o] = t; over_[o] = v; okk[o] = k; memcpy(oen[o], runp[t][v] + 8 * k, 8); lastp(runp[t][v] + 8 * ((k + m - 1) % m), oex[o]); ocut[o] = wgt(oex[o], oen[o]); } } tcnt[t] = NOPT - tofs[t]; }
    e = malloc((size_t)NOPT * NOPT);
    #pragma omp parallel for schedule(dynamic, 16)
    for (int a = 0; a < NOPT; a++) for (int b = 0; b < NOPT; b++) e[(size_t)a * NOPT + b] = otr[a] == otr[b] ? 99 : (int8_t)(wgt(oex[a], oen[b]) - ocut[b] - 1);
    f = fopen(ordp, "r"); int cap = 4096, no = 0; int (*ord)[NTR] = malloc(sizeof(int[NTR]) * cap);
    while (1) { int ok = 1; for (int k = 0; k < NTR; k++) if (fscanf(f, "%d%*[, ]", &ord[no][k]) != 1) { ok = 0; break; } if (!ok) break; no++; if (no == cap) { cap *= 2; ord = realloc(ord, sizeof(int[NTR]) * cap); } }
    fclose(f);
    fprintf(stderr, "orders %d, setup %.1fs\n", no, omp_get_wtime() - T0);
    Res *res = malloc(sizeof(Res) * no); int *Fo = malloc(sizeof(int) * no); long totmoves = 0;
    FILE *neg = fopen(outp, "w"); fprintf(neg, "{\"negative_moves\": [\n"); int nneg = 0;
    #pragma omp parallel for schedule(dynamic, 1) reduction(+:totmoves)
    for (int oi = 0; oi < no; oi++) {
        int *pi = ord[oi];
        // fixed-order DP with backtracking
        int *cur = malloc(4 * 1400), *nx = malloc(4 * 1400); int16_t *bk[NTR]; for (int i = 0; i < NTR; i++) bk[i] = malloc(2 * 1400);
        for (int q = 0; q < tcnt[pi[0]]; q++) cur[q] = ocut[tofs[pi[0]] + q] == 2;
        for (int i = 1; i < NTR; i++) { int a = pi[i - 1], b = pi[i];
            for (int q2 = 0; q2 < tcnt[b]; q2++) { nx[q2] = BIGI; bk[i][q2] = -1; }
            for (int q = 0; q < tcnt[a]; q++) { int v = cur[q]; const int8_t *er = e + (size_t)(tofs[a] + q) * NOPT + tofs[b];
                for (int q2 = 0; q2 < tcnt[b]; q2++) { int c = v + er[q2]; if (c < nx[q2]) { nx[q2] = c; bk[i][q2] = q; } } }
            int *tt = cur; cur = nx; nx = tt; }
        int F = BIGI, qb = -1; for (int q = 0; q < tcnt[pi[NTR - 1]]; q++) if (cur[q] < F) { F = cur[q]; qb = q; }
        int opt[NTR]; opt[NTR - 1] = qb; for (int i = NTR - 1; i >= 1; i--) opt[i - 1] = bk[i][opt[i]];
        Fo[oi] = F;
        // route
        const uint8_t **rt = malloc(sizeof(uint8_t *) * 5040); int bst[NTR], ben[NTR]; int n = 0;
        for (int i = 0; i < NTR; i++) { int t = pi[i], o = tofs[t] + opt[i], v = over_[o], k = okk[o], m = mrun[t][v]; bst[i] = n;
            for (int u = 0; u < m; u++) rt[n++] = runp[t][v] + 8 * ((k + u) % m); ben[i] = n - 1; }
        int *jw = malloc(4 * n); long base = 0; for (int i = 0; i + 1 < n; i++) { jw[i] = wr(rt[i], rt[i + 1]); base += jw[i]; }
        Res R0 = {0, 0, BIGI, -1, -1, -1, -1, -1, -1}; long nm = 0;
        int *gin = malloc(4 * (n + 2)), *gout = malloc(4 * (n + 2));
        for (int i = 0; i < NTR; i++) {
            int t = pi[i], o = tofs[t] + opt[i], v = over_[o], m = mrun[t][v]; const uint8_t *V = runp[t][v];
            int i0 = bst[i], j0 = ben[i]; const uint8_t *P = i0 > 0 ? rt[i0 - 1] : NULL, *Nn = j0 + 1 < n ? rt[j0 + 1] : NULL;
            long oldc = 0; for (int u = i0; u < j0; u++) oldc += jw[u]; if (P) oldc += jw[i0 - 1]; if (Nn) oldc += jw[j0]; if (P && Nn) oldc -= wr(P, Nn);
            // full chains of the version cycle
            for (int s = 0; s < m; s++) {
                if (wr(V + 8 * ((s + m - 1) % m), V + 8 * s) != 3) continue;        // chain start
                int L = 1; while (L < m && wr(V + 8 * ((s + L - 1) % m), V + 8 * ((s + L) % m)) == 2) L++;
                if (L != 7 || wr(V + 8 * ((s + 6) % m), V + 8 * s) != 2) continue;     // full chain with wrap
                // R = runs s+7 .. s-1 (cyclic), internal cost
                const uint8_t *R0p = V + 8 * ((s + 7) % m), *R1p = V + 8 * ((s + m - 1) % m); long cR = 0; for (int u = 7; u < m - 1; u++) cR += wr(V + 8 * ((s + u) % m), V + 8 * ((s + u + 1) % m));
                // insertion costs of R into the gaps of the route outside T's block: gaps (rt[g], rt[g+1]) for g < i0-1 or g > j0,
                // plus both ends; best value over those (the gaps next to the new block are handled per move)
                int bestR = BIGI;
                { if (i0 > 0) { int c0 = wr(R1p, rt[0]); if (c0 < bestR) bestR = c0; } if (j0 < n - 1) { int c0 = wr(rt[n - 1], R0p); if (c0 < bestR) bestR = c0; }
                  for (int g = 0; g + 1 < n; g++) { if (g >= i0 - 1 && g <= j0) continue; int c0 = wr(rt[g], R0p) + wr(R1p, rt[g + 1]) - jw[g]; if (c0 < bestR) bestR = c0; } }
                for (int a = 0; a < 7; a++) {
                    const uint8_t *X0 = V + 8 * ((s + a) % m), *X1 = V + 8 * ((s + (a + 6) % 7) % m);    // rotated chain: first, last run
                    long cX = 0; for (int u = 0; u < 6; u++) cX += wr(V + 8 * ((s + (a + u) % 7) % m), V + 8 * ((s + (a + u + 1) % 7) % m));
                    // move A: X at T's place, R at the best gap (including the two gaps next to X)
                    { long here = cX + (P ? wr(P, X0) : 0) + (Nn ? wr(X1, Nn) : 0) - ((P && Nn) ? wr(P, Nn) : 0);
                      int b2 = bestR;
                      { int c0 = (P ? wr(P, R0p) : 0) + wr(R1p, X0) - (P ? wr(P, X0) : 0); if (c0 < b2) b2 = c0; }
                      { int c0 = wr(X1, R0p) + (Nn ? wr(R1p, Nn) : 0) - (Nn ? wr(X1, Nn) : 0); if (c0 < b2) b2 = c0; }
                      if (i0 == 0 && P == NULL) { } // start handled by the gap before X above
                      long d = here + cR + b2 - oldc; nm++;
                      if (d <= 0) R0.nle0++; if (d < 0) R0.nlt0++;
                      if (d < R0.best) { R0.best = d; R0.bt = t; R0.bc = s; R0.ba = a; R0.bkind = 0; R0.bv = v; } }
                    // move B: R at T's place, X at the best gap
                    { long here = cR + (P ? wr(P, R0p) : 0) + (Nn ? wr(R1p, Nn) : 0) - ((P && Nn) ? wr(P, Nn) : 0);
                      int bX = BIGI;
                      if (i0 > 0) { int c0 = wr(X1, rt[0]); if (c0 < bX) bX = c0; } if (j0 < n - 1) { int c0 = wr(rt[n - 1], X0); if (c0 < bX) bX = c0; }
                      for (int g = 0; g + 1 < n; g++) { if (g >= i0 - 1 && g <= j0) continue; int c0 = wr(rt[g], X0) + wr(X1, rt[g + 1]) - jw[g]; if (c0 < bX) bX = c0; }
                      { int c0 = (P ? wr(P, X0) : 0) + wr(X1, R0p) - (P ? wr(P, R0p) : 0); if (c0 < bX) bX = c0; }
                      { int c0 = wr(R1p, X0) + (Nn ? wr(X1, Nn) : 0) - (Nn ? wr(R1p, Nn) : 0); if (c0 < bX) bX = c0; }
                      long d = here + cX + bX - oldc; nm++;
                      if (d <= 0) R0.nle0++; if (d < 0) R0.nlt0++;
                      if (d < R0.best) { R0.best = d; R0.bt = t; R0.bc = s; R0.ba = a; R0.bkind = 1; R0.bv = v; } }
                } } }

        if (R0.best < 0) {   // exact re-evaluation of the best move: rebuild and scan every gap from scratch
            int t = R0.bt, v = R0.bv, s = R0.bc, a = R0.ba, m = mrun[t][v]; const uint8_t *V = runp[t][v]; int ii = -1; for (int i = 0; i < NTR; i++) if (pi[i] == t) ii = i;
            const uint8_t **here = malloc(sizeof(uint8_t *) * m), **oth = malloc(sizeof(uint8_t *) * m); int nh = 0, no2 = 0;
            const uint8_t *Xr[7]; for (int u = 0; u < 7; u++) Xr[u] = V + 8 * ((s + (a + u) % 7) % m);
            if (R0.bkind == 0) { for (int u = 0; u < 7; u++) here[nh++] = Xr[u]; for (int u = 7; u < m; u++) oth[no2++] = V + 8 * ((s + u) % m); }
            else { for (int u = 7; u < m; u++) here[nh++] = V + 8 * ((s + u) % m); for (int u = 0; u < 7; u++) oth[no2++] = Xr[u]; }
            const uint8_t **rest = malloc(sizeof(uint8_t *) * 5040); int nr = 0; for (int u = 0; u < bst[ii]; u++) rest[nr++] = rt[u]; int h0 = nr; for (int u = 0; u < nh; u++) rest[nr++] = here[u]; int h1 = nr; for (int u = ben[ii] + 1; u < n; u++) rest[nr++] = rt[u];
            long restc = 0; for (int u = 0; u + 1 < nr; u++) restc += wr(rest[u], rest[u + 1]); long oc = 0; for (int u = 0; u + 1 < no2; u++) oc += wr(oth[u], oth[u + 1]);
            long bestc = BIGI;
            for (int g = 0; g <= nr; g++) { if (g > h0 && g < h1) continue; long c = restc + oc;
                if (g > 0) c += wr(rest[g - 1], oth[0]); if (g < nr) c += wr(oth[no2 - 1], rest[g]); if (g > 0 && g < nr) c -= wr(rest[g - 1], rest[g]); if (c < bestc) bestc = c; }
            R0.verified = (int)(bestc - base);
            free(here); free(oth); free(rest); }
        res[oi] = R0; totmoves += nm;
        if (R0.best < 0) {
            #pragma omp critical
            { fprintf(neg, "%s{\"order_index\": %d, \"F\": %d, \"delta\": %d, \"delta_verified_from_scratch\": %d, \"trail\": %d, \"version\": %d, \"chain_start\": %d, \"a\": %d, \"kind\": %d}\n", nneg ? "," : "", oi, F, R0.best, R0.verified, R0.bt, R0.bv, R0.bc, R0.ba, R0.bkind); fflush(neg); nneg++; } }
        free(cur); free(nx); for (int k = 0; k < NTR; k++) free(bk[k]); free(rt); free(jw); free(gin); free(gout);
    }
    int best = BIGI, bo = -1; long nle0 = 0, nlt0 = 0; int bestF = BIGI; long hist[64] = {0};
    for (int oi = 0; oi < no; oi++) { int L = Fo[oi] + res[oi].best; if (L < best) { best = L; bo = oi; } nle0 += res[oi].nle0; nlt0 += res[oi].nlt0; if (Fo[oi] < bestF) bestF = Fo[oi];
        int dd = res[oi].best + 10; if (dd >= 0 && dd < 64) hist[dd]++; }
    fprintf(neg, "],\n \"orders\": %d, \"moves\": %ld, \"min_order_F\": %d, \"best_F_plus_delta\": %d, \"best_order\": %d, \"moves_le0\": %ld, \"moves_lt0\": %ld, \"best_delta_hist_offset10\": [", no, totmoves, bestF, best, bo, nle0, nlt0);
    for (int k = 0; k < 64; k++) fprintf(neg, "%s%ld", k ? ", " : "", hist[k]); fprintf(neg, "],\n \"sec\": %.1f}\n", omp_get_wtime() - T0); fclose(neg);
    printf("{\"orders\": %d, \"moves\": %ld, \"best_F_plus_delta\": %d, \"moves_le0\": %ld, \"moves_lt0\": %ld}\n", no, totmoves, best, nle0, nlt0);
    return 0;
}
