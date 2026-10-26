// Round R -- generalized detour lemma L1G for jump chains WITHOUT wraps.
// In the virtual cover a jump chain of trail S is a sequence of cuts u_1 -> ... -> u_r (r >= 2) whose consecutive cover
// edges are jumps (the piece with exit option u_i is followed by the piece with entry u_{i+1}); it acts as a pseudo-option
// with entry cut a = u_1, exit cut b = u_r and internal cost kappa = sum E'(u_i -> u_{i+1}), E'(u -> u') = w(u - 1, u') - c(u')
// (u - 1 = exit run of option u).  Removing it from a detour position x -> [a ... b] -> y changes G by
//     e(x, y) - 1 - kappa - e(x, a) - e(b, y),
// so it is removable when  e(x, y) <= 1 + kappa + e(x, a) + e(b, y).
// This program computes, for every trail version, kstar(a, b) = least kappa over jump chains that use NO wrap edge
// (all E' >= 0 then, shortest walks are simple paths; dense Dijkstra) and
// checks the inequality for all a, b of S and all x, y of two further distinct trails.  Wrap edges (E' = -1, the w2 link
// C_6 -> C_0 of a full chain) are reported separately.
// usage: l1g DIR
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <omp.h>
#define NTR 30
static int mrun[NTR][2]; static uint8_t *runp[NTR][2];
static int NOPT, otr[16384], over_[16384], okk[16384], ocut[16384], tofs[NTR], tcnt[NTR]; static uint8_t oen[16384][8], oex[16384][8];
static int wgt(const uint8_t *x, const uint8_t *y) { for (int s = 1; s < 8; s++) { int ok = 1; for (int i = 0; s + i < 8; i++) if (x[s + i] != y[i]) { ok = 0; break; } if (ok) return s; } return 8; }
static inline void mp(uint8_t *dst, const uint8_t *src, uint8_t a, int n) { for (int i = 0; i < n; i++) { uint8_t v = (uint8_t)(a + src[i]); dst[i] = v < dst[i] ? v : dst[i]; } }
int main(int argc, char **argv) {
    char p[2048]; snprintf(p, sizeof p, "%s/runs.bin", argv[1]); FILE *f = fopen(p, "rb"); if (!f) return 2;
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) { int32_t m; if (fread(&m, 4, 1, f) != 1) return 2; mrun[t][v] = m; runp[t][v] = malloc(8 * m); if (fread(runp[t][v], 1, 8 * m, f) != (size_t)(8 * m)) return 2; }
    fclose(f);
    for (int t = 0; t < NTR; t++) { tofs[t] = NOPT; for (int v = 0; v < 2; v++) { int m = mrun[t][v];
        for (int k = 0; k < m; k++) { int o = NOPT++; otr[o] = t; over_[o] = v; okk[o] = k; memcpy(oen[o], runp[t][v] + 8 * k, 8); const uint8_t *pr = runp[t][v] + 8 * ((k + m - 1) % m);
            oex[o][0] = pr[7]; for (int i = 1; i < 8; i++) oex[o][i] = pr[i - 1]; ocut[o] = wgt(oex[o], oen[o]); } } tcnt[t] = NOPT - tofs[t]; }
    size_t N = NOPT; uint8_t *e = malloc(N * N);
    #pragma omp parallel for schedule(dynamic, 16)
    for (int a = 0; a < NOPT; a++) for (int b = 0; b < NOPT; b++) { int v = otr[a] == otr[b] ? 99 : wgt(oex[a], oen[b]) - ocut[b] - 1; e[(size_t)a * N + b] = (uint8_t)v; }
    int worst = -100; long viol = 0, tight = 0, nwrap = 0, nzero = 0; int wt = -1, wa = -1, wb = -1, wk = -1;
    long kh[8] = {0};
    for (int t = 0; t < NTR; t++) for (int v = 0; v < 2; v++) {
        int m = mrun[t][v], base = tofs[t] + v * mrun[t][0];
        // jump edge costs E'(u -> u') for options of this version (u' != u, u' != natural successor-merge)
        int *E = malloc(sizeof(int) * m * m);
        for (int i = 0; i < m; i++) for (int j = 0; j < m; j++) { int u = base + i, u2 = base + j;
            if (i == j) { E[i * m + j] = 999; continue; }
            int w = wgt(oex[u], oen[u2]); int Ep = w - ocut[u2];
            if (Ep < 0) { nwrap++; E[i * m + j] = 999; continue; }          // wrap: excluded
            if (Ep == 0) nzero++;
            E[i * m + j] = Ep; }
        // kstar: dense Dijkstra (non-negative small integer weights, dense graph: O(m^2) per source)
        uint8_t *K = malloc(m * m); for (int i = 0; i < m * m; i++) K[i] = 250;
        #pragma omp parallel for schedule(dynamic, 8)
        for (int s = 0; s < m; s++) { int *d = malloc(sizeof(int) * m); char *done = calloc(m, 1); for (int j = 0; j < m; j++) d[j] = 1000; d[s] = 0;
            for (;;) { int bi = -1; for (int j = 0; j < m; j++) if (!done[j] && d[j] < 1000 && (bi < 0 || d[j] < d[bi])) bi = j; if (bi < 0) break; done[bi] = 1;
                const int *row = E + (size_t)bi * m; for (int j = 0; j < m; j++) { int c = row[j]; if (c >= 999 || done[j]) continue; if (d[bi] + c < d[j]) d[j] = d[bi] + c; } }
            for (int j = 0; j < m; j++) K[s * m + j] = (j == s || d[j] >= 250) ? 250 : (uint8_t)d[j]; free(d); free(done); }
        for (int i = 0; i < m * m; i++) if (K[i] < 8) kh[K[i]]++;
        // check: for x, y of distinct trails other than t:  min_{a,b} [kstar(a,b) + e(x,a) + e(b,y)] + 1 >= e(x,y)
        // M1[a][y] = min_b K[a][b] + e(b, y)   (y over all options);  then per x: R[y] = min_a e(x, a) + M1[a][y]
        uint8_t *M1 = malloc((size_t)m * N); memset(M1, 250, (size_t)m * N);
        #pragma omp parallel for schedule(dynamic, 8)
        for (int a = 0; a < m; a++) for (int b = 0; b < m; b++) { if (K[a * m + b] >= 250) continue; mp(M1 + (size_t)a * N, e + (size_t)(base + b) * N, K[a * m + b], NOPT); }
        int lw = -100; long lv = 0, lt = 0; int la = -1, lb = -1;
        #pragma omp parallel for schedule(dynamic, 16) reduction(+:lv, lt)
        for (int x = 0; x < NOPT; x++) { if (otr[x] == t) continue; uint8_t R[16384]; memset(R, 250, NOPT);
            for (int a = 0; a < m; a++) mp(R, M1 + (size_t)a * N, e[(size_t)x * N + base + a], NOPT);
            int w = -100;
            for (int y = 0; y < NOPT; y++) { if (otr[y] == t || otr[y] == otr[x]) continue; int d = (int)e[(size_t)x * N + y] - 1 - (int)R[y]; if (d > 0) lv++; if (d == 0) lt++; if (d > w) w = d; }
            if (w > lw) {
                #pragma omp critical
                { if (w > lw) { lw = w; la = x; } } } }
        if (lw > worst) { worst = lw; wt = t; wk = v; wa = la; wb = lb; }
        viol += lv; tight += lt;
        free(E); free(K); free(M1);
        fprintf(stderr, "trail %d v %d: L1G max excess %d, violations %ld\n", t, v, lw, lv);
    }
    printf("{\"L1G_max_excess_over_bound\": %d, \"L1G_violations\": %ld, \"L1G_tight\": %ld, \"wrap_edges_excluded\": %ld, \"zero_cost_jump_edges\": %ld, \"kstar_hist_0_7\": [%ld, %ld, %ld, %ld, %ld, %ld, %ld, %ld], \"worst_trail_version_x\": [%d, %d, %d], \"L1G_holds\": %s}\n",
           worst, viol, tight, nwrap, nzero, kh[0], kh[1], kh[2], kh[3], kh[4], kh[5], kh[6], kh[7], wt, wk, wa, worst <= 0 ? "true" : "false");
    (void)wb;
    return 0;
}
